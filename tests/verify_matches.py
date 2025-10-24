"""
Verify that each record's original fields match the enriched Google Places fields.

Checks:
 - Normalized name similarity (name vs gmaps_name)
 - Normalized website match (website vs gmaps_website)
 - UK postcode normalization and equality (postcode vs gmaps_addr_postal_code)
 - Coordinate distance (latitude/longitude vs gmaps_latitude/gmaps_longitude)

Outputs a CSV/XLSX report with flags and scores.
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import re
from typing import Dict, List


def read_csv(path: str) -> List[Dict[str, str]]:
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [{k: (v if v is not None else "") for k, v in row.items()} for row in reader]


def write_csv(path: str, rows: List[Dict[str, str]]) -> None:
    if not rows:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # Build union of headers in a stable order: first row keys, then any new keys encountered
    headers = list(rows[0].keys())
    seen = set(headers)
    for r in rows[1:]:
        for k in r.keys():
            if k not in seen:
                headers.append(k)
                seen.add(k)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def write_excel(path: str, rows: List[Dict[str, str]]) -> None:
    try:
        import pandas as pd
    except Exception:
        print("pandas not installed; skipping Excel export:", path)
        return
    df = (pd.DataFrame(rows) if rows else pd.DataFrame())
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        df.to_excel(path, index=False, engine="openpyxl")
    except Exception:
        print("openpyxl not installed; skipping Excel export:", path)


POSTCODE_RE = re.compile(r"\b([A-Z]{1,2}\d{1,2}[A-Z]?)\s?(\d[A-Z]{2})\b", re.I)


def normalize_postcode(raw: str) -> str:
    if not raw:
        return ""
    m = POSTCODE_RE.search(raw.upper())
    if not m:
        return ""
    return f"{m.group(1)} {m.group(2)}"


def normalize_name(name: str) -> str:
    if not name:
        return ""
    s = name.lower()
    s = re.sub(r"&amp;", "and", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\b(ltd|limited|nhs|trust|service|services|the|clinic|centre|center)\b", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def normalize_website(url: str) -> str:
    if not url:
        return ""
    url = url.strip().lower()
    url = re.sub(r"^https?://(www\.)?", "", url)
    url = url.split("?")[0].rstrip("/")
    return url


def extract_domain(url: str) -> str:
    if not url:
        return ""
    host = normalize_website(url).split("/")[0]
    if not host:
        return ""
    labels = host.split(".")
    if len(labels) < 2:
        return host
    public_suffix_3 = (
        host.endswith(".co.uk")
        or host.endswith(".org.uk")
        or host.endswith(".gov.uk")
        or host.endswith(".ac.uk")
        or host.endswith(".nhs.uk")
        or host.endswith(".police.uk")
        or host.endswith(".mod.uk")
        or host.endswith(".sch.uk")
    )
    if public_suffix_3 and len(labels) >= 3:
        return ".".join(labels[-3:])
    return ".".join(labels[-2:])


def jaccard_similarity(a: str, b: str) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    aset = set(a.split())
    bset = set(b.split())
    if not aset and not bset:
        return 1.0
    inter = len(aset & bset)
    union = len(aset | bset)
    return inter / union if union else 0.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dl/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


def to_float(s: str) -> float | None:
    try:
        return float(s)
    except Exception:
        return None


def verify(rows: List[Dict[str, str]], name_threshold: float, max_distance_km: float) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for idx, r in enumerate(rows, start=1):
        name = normalize_name(r.get("name", ""))
        gname = normalize_name(r.get("gmaps_name", ""))
        name_sim = jaccard_similarity(name, gname)

        web = normalize_website(r.get("website", ""))
        gweb = normalize_website(r.get("gmaps_website", ""))
        web_match = int(bool(web and gweb and web == gweb))
        dom = extract_domain(r.get("website", ""))
        gdom = extract_domain(r.get("gmaps_website", ""))
        domain_match = int(bool(dom and gdom and dom == gdom))

        pc = normalize_postcode(r.get("postcode", ""))
        gpc = normalize_postcode(r.get("gmaps_addr_postal_code", ""))
        pc_match = int(bool(pc and gpc and pc == gpc))

        lat = to_float(r.get("latitude", ""))
        lng = to_float(r.get("longitude", ""))
        glat = to_float(r.get("gmaps_latitude", ""))
        glng = to_float(r.get("gmaps_longitude", ""))
        distance_km = ""
        if lat is not None and lng is not None and glat is not None and glng is not None:
            distance_km = round(haversine_km(lat, lng, glat, glng), 3)

        likely_match = (
            (name_sim >= name_threshold)
            or web_match
            or domain_match
            or pc_match
            or (isinstance(distance_km, float) and distance_km <= max_distance_km)
        )

        # Start with all original columns
        row_out: Dict[str, str] = dict(r)
        # Append verification fields without overwriting original columns
        row_out.update({
            "row_index": idx,
            "name_similarity": f"{name_sim:.3f}",
            "website_norm": web,
            "gmaps_website_norm": gweb,
            "website_match": str(web_match),
            "website_domain": dom,
            "gmaps_website_domain": gdom,
            "domain_match": str(domain_match),
            "postcode_norm": pc,
            "gmaps_postcode_norm": gpc,
            "postcode_match": str(pc_match),
            "distance_km": distance_km,
            "likely_match": str(int(likely_match)),
        })
        out.append(row_out)
    return out


def parse_args() -> argparse.Namespace:
    default_root = "/Users/venkata/startup/data_scraper"
    default_input = os.path.join(default_root, "to_be_normalised", "merged_with_google.csv")
    default_report = os.path.join(default_root, "to_be_normalised", "match_report.csv")
    default_report_xlsx = os.path.join(default_root, "to_be_normalised", "match_report.xlsx")

    p = argparse.ArgumentParser(description="Verify enriched Google Places matches")
    p.add_argument("--input", default=default_input, help="Path to enriched CSV")
    p.add_argument("--output", default=default_report, help="Path to write match report CSV")
    p.add_argument("--output-xlsx", default=default_report_xlsx, help="Path to write match report Excel")
    p.add_argument("--name-threshold", type=float, default=0.5, help="Name similarity threshold (0-1)")
    p.add_argument("--max-distance-km", type=float, default=1.0, help="Max allowed distance in km")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    rows = read_csv(args.input)
    report = verify(rows, name_threshold=args.name_threshold, max_distance_km=args.max_distance_km)
    write_csv(args.output, report)
    write_excel(args.output_xlsx, report)
    print(f"Match report -> {args.output}")
    print(f"Match report Excel -> {args.output_xlsx}")


if __name__ == "__main__":
    main()


