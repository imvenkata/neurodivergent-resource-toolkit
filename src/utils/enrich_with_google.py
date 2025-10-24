"""
Enrich services with Google Places data (address, hours, reviews, lat/lng, contacts).

Usage (dry run):
  python3 enrich_with_google.py --help

Usage (real):
  export GOOGLE_MAPS_API_KEY=...  # or pass --api-key
  python3 enrich_with_google.py \
    --input /Users/venkata/startup/data_scraper/to_be_normalised/merged_neurodivergent_services.csv \
    --output /Users/venkata/startup/data_scraper/to_be_normalised/merged_with_google.csv \
    --output-xlsx /Users/venkata/startup/data_scraper/to_be_normalised/merged_with_google.xlsx \
    --cache /Users/venkata/startup/data_scraper/to_be_normalised/google_places_cache.json \
    --region gb --sleep 0.25
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from typing import Dict, Iterable, List, Optional, Tuple


DEFAULT_FIELDS = (
    "place_id,name,formatted_address,geometry,opening_hours,current_opening_hours,website,"
    "formatted_phone_number,international_phone_number,rating,user_ratings_total,reviews,types,"
    "business_status,editorial_summary,url,address_components,plus_code,photos"
)


def read_csv(path: str) -> List[Dict[str, str]]:
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [{k: (v if v is not None else "") for k, v in row.items()} for row in reader]


GMAPS_COLUMNS = [
    "gmaps_place_id",
    "gmaps_name",
    "gmaps_formatted_address",
    "gmaps_latitude",
    "gmaps_longitude",
    "gmaps_open_now",
    "gmaps_opening_hours_weekday_text",
    "gmaps_current_opening_hours_weekday_text",
    "gmaps_website",
    "gmaps_phone",
    "gmaps_rating",
    "gmaps_user_ratings_total",
    "gmaps_types",
    "gmaps_reviews_top3",
    "gmaps_business_status",
    "gmaps_editorial_summary",
    "gmaps_url",
    "gmaps_directions_url",
    "gmaps_plus_code_global",
    "gmaps_plus_code_compound",
    "gmaps_utc_offset_minutes",
    "gmaps_photo_reference_1",
    "gmaps_addr_country",
    "gmaps_addr_postal_code",
    "gmaps_addr_postal_town",
    "gmaps_addr_locality",
    "gmaps_addr_admin_area_level_1",
    "gmaps_addr_admin_area_level_2",
    # debug/trace
    "gmaps_query",
    "gmaps_text_status",
    "gmaps_details_status",
    "gmaps_details_error",
]


def write_csv(path: str, rows: List[Dict[str, str]]) -> None:
    if not rows:
        return
    # Build header as union of all keys, preserving the order of first row, then new keys, then expected gmaps columns
    ordered = list(rows[0].keys())
    seen = set(ordered)
    for r in rows[1:]:
        for k in r.keys():
            if k not in seen:
                ordered.append(k)
                seen.add(k)
    for gk in GMAPS_COLUMNS:
        if gk not in seen:
            ordered.append(gk)
            seen.add(gk)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ordered)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def write_excel(path: str, rows: List[Dict[str, str]]) -> None:
    try:
        import pandas as pd
    except Exception:
        print("pandas not installed; skipping Excel export:", path)
        return
    if not rows:
        df = pd.DataFrame()
    else:
        # Build header union like CSV and ensure GMAPS columns are present
        ordered = list(rows[0].keys())
        seen = set(ordered)
        for r in rows[1:]:
            for k in r.keys():
                if k not in seen:
                    ordered.append(k)
                    seen.add(k)
        for gk in GMAPS_COLUMNS:
            if gk not in seen:
                ordered.append(gk)
                seen.add(gk)
        # Ensure all rows have all GMAPS columns
        norm_rows = []
        for r in rows:
            rr = dict(r)
            for gk in GMAPS_COLUMNS:
                rr.setdefault(gk, "")
            norm_rows.append(rr)
        df = pd.DataFrame(norm_rows)
        # Reorder columns
        df = df.reindex(columns=ordered)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        df.to_excel(path, index=False, engine="openpyxl")
    except Exception:
        print("openpyxl not installed; skipping Excel export:", path)


def load_cache(path: str) -> Dict:
    if not path or not os.path.exists(path):
        return {"text_search": {}, "details": {}}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"text_search": {}, "details": {}}


def save_cache(path: str, data: Dict) -> None:
    if not path:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, path)


def http_get_json(url: str, headers: Optional[Dict[str, str]] = None) -> Dict:
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read().decode("utf-8")
        return json.loads(data)


def build_text_search_query(name: str, postcode: str, city: str) -> str:
    parts = [name.strip()]
    if postcode:
        parts.append(postcode.strip())
    elif city:
        parts.append(city.strip())
    return ", ".join([p for p in parts if p])


def gmaps_text_search(
    api_key: str,
    query: str,
    region: str,
    cache: Dict,
    sleep: float,
    location: Optional[Tuple[str, str]] = None,
    radius_m: int = 4000,
) -> Optional[Dict]:
    if not query:
        return None
    cached = cache.get("text_search", {}).get(query)
    if cached:
        return cached
    params = {"query": query, "key": api_key, "region": region}
    if location and location[0] and location[1]:
        params["location"] = f"{location[0]},{location[1]}"
        params["radius"] = str(radius_m)
    qs = urllib.parse.urlencode(params)
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?{qs}"
    data = http_get_json(url)
    status = data.get("status")
    if status == "OVER_QUERY_LIMIT":
        raise RuntimeError("Google Places OVER_QUERY_LIMIT")
    if status == "REQUEST_DENIED":
        raise RuntimeError(f"Google Places REQUEST_DENIED: {data}")
    if status not in ("OK", "ZERO_RESULTS"):
        # Store anyway to avoid refetching broken responses
        cache.setdefault("text_search", {})[query] = data
        return data
    cache.setdefault("text_search", {})[query] = data
    if sleep > 0:
        time.sleep(sleep)
    return data


def gmaps_place_details(api_key: str, place_id: str, fields: str, cache: Dict, sleep: float) -> Optional[Dict]:
    if not place_id:
        return None
    cache_key = f"{place_id}|{fields}"
    cached = cache.get("details", {}).get(cache_key)
    if cached:
        return cached
    qs = urllib.parse.urlencode({"place_id": place_id, "fields": fields, "key": api_key})
    url = f"https://maps.googleapis.com/maps/api/place/details/json?{qs}"
    data = http_get_json(url)
    status = data.get("status")
    if status == "OVER_QUERY_LIMIT":
        raise RuntimeError("Google Place Details OVER_QUERY_LIMIT")
    if status == "REQUEST_DENIED":
        raise RuntimeError(f"Google Place Details REQUEST_DENIED: {data}")
    cache.setdefault("details", {})[cache_key] = data
    if sleep > 0:
        time.sleep(sleep)
    return data


def extract_from_details(details: Dict) -> Dict[str, str]:
    result = (details or {}).get("result") or {}
    geom = (result.get("geometry") or {}).get("location") or {}
    opening = result.get("opening_hours") or {}
    reviews = result.get("reviews") or []
    weekday_text = opening.get("weekday_text") or []
    current_opening = result.get("current_opening_hours") or {}
    current_weekday_text = current_opening.get("weekday_text") or []
    plus_code = result.get("plus_code") or {}
    address_components = result.get("address_components") or []
    photos = result.get("photos") or []
    # Keep top 3 reviews as a compact string
    top_reviews = []
    for rv in reviews[:3]:
        author = rv.get("author_name") or ""
        rating = rv.get("rating")
        text = (rv.get("text") or "").strip().replace("\n", " ")
        top_reviews.append(f"{author}({rating}): {text}".strip())

    types = ",".join(result.get("types") or [])

    def addr_comp(type_name: str) -> str:
        for comp in address_components:
            types_list = comp.get("types") or []
            if type_name in types_list:
                return (comp.get("long_name") or comp.get("short_name") or "").strip()
        return ""

    place_id = result.get("place_id", "")
    lat_str = str(geom.get("lat", ""))
    lng_str = str(geom.get("lng", ""))
    maps_url = result.get("url", "")
    if place_id and not maps_url:
        maps_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
    if place_id:
        directions_url = f"https://www.google.com/maps/dir/?api=1&destination_place_id={place_id}"
    elif lat_str and lng_str:
        directions_url = f"https://www.google.com/maps/dir/?api=1&destination={lat_str}%2C{lng_str}"
    else:
        directions_url = ""

    photo_ref_1 = photos[0].get("photo_reference", "") if photos else ""

    return {
        "gmaps_place_id": place_id,
        "gmaps_name": result.get("name", ""),
        "gmaps_formatted_address": result.get("formatted_address", ""),
        "gmaps_latitude": lat_str,
        "gmaps_longitude": lng_str,
        "gmaps_open_now": str(opening.get("open_now", "")),
        "gmaps_opening_hours_weekday_text": "; ".join(weekday_text),
        "gmaps_current_opening_hours_weekday_text": "; ".join(current_weekday_text),
        "gmaps_website": result.get("website", ""),
        "gmaps_phone": result.get("international_phone_number") or result.get("formatted_phone_number", ""),
        "gmaps_rating": str(result.get("rating", "")),
        "gmaps_user_ratings_total": str(result.get("user_ratings_total", "")),
        "gmaps_types": types,
        "gmaps_reviews_top3": " | ".join(top_reviews),
        "gmaps_business_status": result.get("business_status", ""),
        "gmaps_editorial_summary": (result.get("editorial_summary") or {}).get("overview", ""),
        "gmaps_url": maps_url,
        "gmaps_directions_url": directions_url,
        "gmaps_plus_code_global": plus_code.get("global_code", ""),
        "gmaps_plus_code_compound": plus_code.get("compound_code", ""),
        "gmaps_utc_offset_minutes": str(result.get("utc_offset_minutes", "")),
        "gmaps_photo_reference_1": photo_ref_1,
        "gmaps_addr_country": addr_comp("country"),
        "gmaps_addr_postal_code": addr_comp("postal_code"),
        "gmaps_addr_postal_town": addr_comp("postal_town"),
        "gmaps_addr_locality": addr_comp("locality"),
        "gmaps_addr_admin_area_level_1": addr_comp("administrative_area_level_1"),
        "gmaps_addr_admin_area_level_2": addr_comp("administrative_area_level_2"),
    }


def enrich_records(
    rows: List[Dict[str, str]],
    api_key: str,
    cache: Dict,
    region: str,
    sleep: float,
    limit: Optional[int] = None,
    progress_interval: int = 50,
) -> List[Dict[str, str]]:
    out_rows: List[Dict[str, str]] = []
    processed = 0
    match_count = 0
    zero_count = 0
    error_count = 0
    total = min(len(rows), limit) if limit is not None else len(rows)

    for row in rows:
        if limit is not None and processed >= limit:
            break
        try:
            name = (row.get("name") or "").strip()
            postcode = (row.get("postcode") or "").strip()
            city = (row.get("city") or "").strip()
            base_lat = (row.get("latitude") or "").strip()
            base_lng = (row.get("longitude") or "").strip()
            if not name:
                out_rows.append(row)
                processed += 1
                if progress_interval and processed % progress_interval == 0:
                    print(f"[{processed}/{total}] matches:{match_count} zero:{zero_count} errors:{error_count}")
                continue

            query = build_text_search_query(name, postcode, city)
            ts = gmaps_text_search(api_key, query, region, cache, sleep, location=(base_lat, base_lng) if base_lat and base_lng else None)
            place_id = ""
            text_status = (ts or {}).get("status", "") if ts is not None else "NO_QUERY"
            if ts and (ts.get("results") or []):
                place_id = ts["results"][0].get("place_id", "")
                match_count += 1
            else:
                zero_count += 1

            details = gmaps_place_details(api_key, place_id, DEFAULT_FIELDS, cache, sleep) if place_id else None
            details_status = (details or {}).get("status", "") if details is not None else "NO_DETAILS"
            details_error = (details or {}).get("error_message", "") if details is not None else ""
            extra = extract_from_details(details or {}) if details else {}
            # Ensure all GMAPS columns exist even if empty
            for gk in GMAPS_COLUMNS:
                extra.setdefault(gk, "")
            # add debug trace
            extra["gmaps_query"] = query
            extra["gmaps_text_status"] = text_status
            extra["gmaps_details_status"] = details_status
            extra["gmaps_details_error"] = details_error
            enriched = {**row, **extra}
            out_rows.append(enriched)
        except Exception:
            error_count += 1
            # Still ensure blank GMAPS columns to keep headers consistent
            rr = dict(row)
            for gk in GMAPS_COLUMNS:
                rr.setdefault(gk, "")
            out_rows.append(rr)
        finally:
            processed += 1
            if progress_interval and processed % progress_interval == 0:
                print(f"[{processed}/{total}] matches:{match_count} zero:{zero_count} errors:{error_count}")

    # Final summary
    print(f"[done {processed}/{total}] matches:{match_count} zero:{zero_count} errors:{error_count}")
    return out_rows


def parse_args() -> argparse.Namespace:
    default_root = "/Users/venkata/startup/data_scraper"
    default_input = os.path.join(default_root, "to_be_normalised", "merged_neurodivergent_services.csv")
    default_output = os.path.join(default_root, "to_be_normalised", "merged_with_google.csv")
    default_output_xlsx = os.path.join(default_root, "to_be_normalised", "merged_with_google.xlsx")
    default_cache = os.path.join(default_root, "to_be_normalised", "google_places_cache.json")

    p = argparse.ArgumentParser(description="Enrich merged services with Google Places data")
    p.add_argument("--input", default=default_input, help="Path to merged services CSV")
    p.add_argument("--output", default=default_output, help="Path to write enriched CSV")
    p.add_argument("--output-xlsx", default=default_output_xlsx, help="Path to write enriched Excel (.xlsx)")
    p.add_argument("--cache", default=default_cache, help="Path to JSON cache file")
    p.add_argument("--api-key", default=os.getenv("GOOGLE_MAPS_API_KEY", ""), help="Google Maps API key")
    p.add_argument("--region", default="gb", help="Region bias (e.g., gb)")
    p.add_argument("--sleep", type=float, default=0.25, help="Sleep seconds between API calls")
    p.add_argument("--limit", type=int, default=None, help="Limit number of records to process")
    p.add_argument("--progress-interval", type=int, default=50, help="Print progress every N records (0 to disable)")
    p.add_argument("--dry-run", action="store_true", help="Do not call APIs; just show planned queries")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    rows = read_csv(args.input)
    cache = load_cache(args.cache)

    if args.dry_run:
        for row in rows[: min(len(rows), args.limit or 10)]:
            q = build_text_search_query(row.get("name", ""), row.get("postcode", ""), row.get("city", ""))
            print(q)
        print("Dry run complete.")
        return

    if not args.api_key:
        # Proceed without API calls: write inputs with blank GMAPS columns so headers are present
        print("Warning: Missing API key; writing outputs with blank Google columns.")
        base_rows = rows
        # Ensure blank GMAPS columns
        enriched = []
        for r in base_rows:
            rr = dict(r)
            for gk in GMAPS_COLUMNS:
                rr.setdefault(gk, "")
            enriched.append(rr)
        write_csv(args.output, enriched)
        write_excel(args.output_xlsx, enriched)
        print(f"Enriched {len(enriched)} records -> {args.output}")
        print(f"Excel -> {args.output_xlsx}")
        return

    try:
        enriched = enrich_records(
            rows=rows,
            api_key=args.api_key,
            cache=cache,
            region=args.region,
            sleep=args.sleep,
            limit=args.limit,
            progress_interval=args.progress_interval,
        )
    except RuntimeError as e:
        print("Error during enrichment:", e)
        save_cache(args.cache, cache)
        raise

    save_cache(args.cache, cache)
    write_csv(args.output, enriched)
    write_excel(args.output_xlsx, enriched)
    print(f"Enriched {len(enriched)} records -> {args.output}")
    print(f"Excel -> {args.output_xlsx}")


if __name__ == "__main__":
    main()


