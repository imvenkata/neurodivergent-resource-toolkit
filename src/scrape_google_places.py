#!/usr/bin/env python3
"""
Scrape Google Places data systematically across UK regions using keywords.
This script searches for neurodivergent resources using predefined keywords and regions.

Usage:
    python src/scrape_google_places.py --output data/output/scraped_places.csv --test
    python src/scrape_google_places.py --output data/output/scraped_places.csv --keywords-filter "autism,ADHD"
    python src/scrape_google_places.py --output data/output/scraped_places.csv --regions-filter "London,Manchester"
"""

import argparse
import csv
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from config import GOOGLE_PLACES_CONFIG, SEARCH_KEYWORDS, UK_REGIONS


class RateLimiter:
    """Simple rate limiter for API calls."""
    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.min_interval = 60.0 / requests_per_minute
        self.last_request_time = 0
    
    def wait_if_needed(self):
        """Wait if necessary to respect rate limit."""
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            time.sleep(sleep_time)
        self.last_request_time = time.time()


def load_cache(cache_path: str) -> Dict:
    """Load cache from JSON file."""
    if not cache_path or not os.path.exists(cache_path):
        return {"text_search": {}, "details": {}}
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load cache: {e}")
        return {"text_search": {}, "details": {}}


def save_cache(cache_path: str, cache: Dict) -> None:
    """Save cache to JSON file."""
    if not cache_path:
        return
    try:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        tmp_path = cache_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, cache_path)
    except Exception as e:
        print(f"Warning: Could not save cache: {e}")


def http_get_json(url: str, headers: Optional[Dict[str, str]] = None) -> Dict:
    """Make HTTP GET request and return JSON response."""
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read().decode("utf-8")
        return json.loads(data)


def http_post_json(url: str, body: Dict, headers: Optional[Dict[str, str]] = None) -> Dict:
    """Make HTTP POST request with JSON body and return JSON response."""
    payload = json.dumps(body).encode("utf-8")
    all_headers = {"Content-Type": "application/json; charset=utf-8"}
    if headers:
        all_headers.update(headers)
    req = urllib.request.Request(url, data=payload, headers=all_headers, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read().decode("utf-8")
        return json.loads(data)


def geocode_location(location_str: str, api_key: str, cache: Dict, rate_limiter: RateLimiter) -> Optional[Tuple[float, float]]:
    """
    Geocode a location string to lat/lng coordinates.
    Returns (lat, lng) tuple or None if geocoding fails.
    """
    cache_key = f"geocode:{location_str}"
    if cache_key in cache.get("text_search", {}):
        cached = cache["text_search"][cache_key]
        if cached and "location" in cached and cached["location"] is not None:
            return (cached["location"]["lat"], cached["location"]["lng"])
        return None
    
    rate_limiter.wait_if_needed()
    
    try:
        params = {"address": location_str, "key": api_key}
        qs = urllib.parse.urlencode(params)
        url = f"https://maps.googleapis.com/maps/api/geocode/json?{qs}"
        data = http_get_json(url)
        
        if data.get("status") == "OK" and data.get("results"):
            location = data["results"][0]["geometry"]["location"]
            cache.setdefault("text_search", {})[cache_key] = {"location": location}
            return (location["lat"], location["lng"])
        else:
            cache.setdefault("text_search", {})[cache_key] = {"location": None}
            return None
    except Exception as e:
        print(f"Warning: Geocoding failed for '{location_str}': {e}")
        return None


def search_places_by_keyword(
    keyword: str,
    location: str,
    lat_lng: Optional[Tuple[float, float]],
    radius_meters: int,
    api_key: str,
    region: str,
    cache: Dict,
    rate_limiter: RateLimiter,
) -> List[Dict]:
    """
    Search for places using Google Places API (New) Text Search.
    Returns list of place dictionaries.
    """
    # Build search query (use keyword only; location is provided via locationBias)
    query = keyword.strip()
    cache_key = f"search_v1:{query}:{location}:r{radius_meters}"
    
    # Check cache
    if cache_key in cache.get("text_search", {}):
        cached = cache["text_search"][cache_key]
        return cached.get("results", [])
    
    rate_limiter.wait_if_needed()
    
    try:
        url = "https://places.googleapis.com/v1/places:searchText"
        field_mask = (
            "places.id,places.name,places.displayName,places.formattedAddress,"
            "places.location,places.types,places.businessStatus,places.googleMapsUri"
        )
        headers = {
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": field_mask,
        }
        body: Dict[str, object] = {
            "textQuery": query,
            "regionCode": (region or "gb").upper(),
            "languageCode": "en",
            "maxResultCount": 20,
            "rankPreference": "RELEVANCE",
        }
        if lat_lng:
            body["locationBias"] = {
                "circle": {
                    "center": {"latitude": float(lat_lng[0]), "longitude": float(lat_lng[1])},
                    "radius": float(radius_meters),
                }
            }
        data = http_post_json(url, body=body, headers=headers)
        results = data.get("places", [])
        cache.setdefault("text_search", {})[cache_key] = {"results": results, "status": "OK"}
        return results
    except Exception as e:
        print(f"Error searching '{query}': {e}")
        cache.setdefault("text_search", {})[cache_key] = {"results": [], "error": str(e)}
        return []


def get_place_details(
    place_name: str,
    api_key: str,
    cache: Dict,
    rate_limiter: RateLimiter,
    fields: str = None,
) -> Optional[Dict]:
    """
    Get detailed information about a place using Places API (New).
    place_name should be the resource name like 'places/{id}' from search results.
    """
    if not fields:
        # Note: Places API (New) uses different field names
        # - nationalPhoneNumber instead of formattedPhoneNumber  
        # - displayName instead of name
        # - Don't include 'name' as field (it's the resource name)
        fields = (
            "id,displayName,formattedAddress,location,types,businessStatus,googleMapsUri,"
            "websiteUri,nationalPhoneNumber,addressComponents"
        )

    cache_key = f"details_v1:{place_name}:{fields}"
    
    # Check cache
    if cache_key in cache.get("details", {}):
        return cache["details"][cache_key]
    
    rate_limiter.wait_if_needed()

    try:
        # place_name is already in format 'places/{id}'
        url = f"https://places.googleapis.com/v1/{place_name}"
        headers = {
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": fields,
        }
        data = http_get_json(url, headers=headers)
        cache.setdefault("details", {})[cache_key] = data
        return data
    except Exception as e:
        print(f"Error getting details for place '{place_name}': {e}")
        cache.setdefault("details", {})[cache_key] = {"error": str(e)}
        return None


def extract_place_data(place_basic: Dict, place_details: Optional[Dict], keyword: str, region_name: str) -> Dict[str, str]:
    """
    Extract and normalize place data into CSV row format matching enriched_resources.csv schema.
    """
    # Start with basic data from search results (Places API New)
    place_id = place_basic.get("id") or (place_basic.get("name", "").split("/")[-1] if place_basic.get("name") else "")
    display_name = place_basic.get("displayName", {})
    name = display_name.get("text") or place_basic.get("name", "")
    formatted_address = place_basic.get("formattedAddress", "")
    loc = place_basic.get("location", {}) or {}
    lat = loc.get("latitude", "")
    lng = loc.get("longitude", "")
    
    # Initialize row with basic data
    row = {
        "gmaps_place_id": place_id,
        "gmaps_name": name,
        "gmaps_formatted_address": formatted_address,
        "gmaps_latitude": str(lat),
        "gmaps_longitude": str(lng),
        "gmaps_types": ",".join(place_basic.get("types", [])),
        "gmaps_business_status": place_basic.get("business_status", ""),
        "search_keyword": keyword,
        "search_region": region_name,
    }
    
    # If we have detailed data, extract it
    if place_details:
        # Places API New returns the place object directly
        result = place_details
        
        # Contact Data fields (website + phone)
        row["gmaps_website"] = result.get("websiteUri", "")
        row["gmaps_phone"] = result.get("nationalPhoneNumber", "") or result.get("internationalPhoneNumber", "")
        
        # Note: opening_hours NOT requested to save costs (Contact Data)
        
        # Note: rating, user_ratings_total, reviews, editorial_summary are NOT requested
        # to avoid expensive Atmosphere Data charges - these fields will be empty
        
        # URLs
        row["gmaps_url"] = result.get("googleMapsUri", "") or (f"https://www.google.com/maps/place/?q=place_id:{place_id}" if place_id else "")
        if lat and lng:
            row["gmaps_directions_url"] = f"https://www.google.com/maps/dir/?api=1&destination={lat}%2C{lng}"
        else:
            row["gmaps_directions_url"] = ""
        
        # Plus code
        plus_code = result.get("plusCode", {})
        row["gmaps_plus_code_global"] = plus_code.get("globalCode", "")
        row["gmaps_plus_code_compound"] = plus_code.get("compoundCode", "")
        
        # UTC offset
        row["gmaps_utc_offset_minutes"] = str(result.get("utc_offset_minutes", ""))
        
        # Photo reference
        photos = result.get("photos", [])
        row["gmaps_photo_reference_1"] = photos[0].get("name", "") if photos else ""
        
        # Address components (Places API New: addressComponents with types)
        addr_components = result.get("addressComponents", [])
        def addr_get(type_name: str) -> str:
            for comp in addr_components:
                types_list = comp.get("types", []) or []
                if type_name in types_list:
                    # v1 uses longText/shortText
                    return (comp.get("longText") or comp.get("shortText") or "").strip()
            return ""

        row["gmaps_addr_country"] = addr_get("country")
        row["gmaps_addr_postal_code"] = addr_get("postal_code")
        row["gmaps_addr_postal_town"] = addr_get("postal_town")
        row["gmaps_addr_locality"] = addr_get("locality")
        row["gmaps_addr_admin_area_level_1"] = addr_get("administrative_area_level_1")
        row["gmaps_addr_admin_area_level_2"] = addr_get("administrative_area_level_2")
    
    # Fill in any missing fields with empty strings
    all_fields = [
        "gmaps_place_id", "gmaps_name", "gmaps_formatted_address", "gmaps_latitude", "gmaps_longitude",
        "gmaps_open_now", "gmaps_opening_hours_weekday_text", "gmaps_current_opening_hours_weekday_text",
        "gmaps_website", "gmaps_phone", "gmaps_rating", "gmaps_user_ratings_total", "gmaps_types",
        "gmaps_reviews_top3", "gmaps_business_status", "gmaps_editorial_summary", "gmaps_url",
        "gmaps_directions_url", "gmaps_plus_code_global", "gmaps_plus_code_compound",
        "gmaps_utc_offset_minutes", "gmaps_photo_reference_1", "gmaps_addr_country",
        "gmaps_addr_postal_code", "gmaps_addr_postal_town", "gmaps_addr_locality",
        "gmaps_addr_admin_area_level_1", "gmaps_addr_admin_area_level_2",
        "search_keyword", "search_region"
    ]
    
    for field in all_fields:
        row.setdefault(field, "")
    
    return row


def scrape_uk_places(
    api_key: str,
    keywords: List[str],
    regions: List[Dict],
    cache_path: str,
    rate_limiter: RateLimiter,
    fetch_details: bool = True,
    max_searches: Optional[int] = None,
) -> List[Dict[str, str]]:
    """
    Main scraping function that searches across keywords and regions.
    Returns list of place data dictionaries.
    """
    cache = load_cache(cache_path)
    all_places: Dict[str, Dict[str, str]] = {}  # place_id -> place_data
    seen_place_ids: Set[str] = set()
    
    total_searches = len(keywords) * len(regions)
    if max_searches:
        total_searches = min(total_searches, max_searches)
    
    search_count = 0
    places_found = 0
    
    print(f"Starting scrape: {len(keywords)} keywords × {len(regions)} regions = {total_searches} searches")
    print(f"Rate limit: {rate_limiter.requests_per_minute} requests/minute")
    print(f"Fetch details: {fetch_details}\n")
    
    for keyword in keywords:
        for region in regions:
            if max_searches and search_count >= max_searches:
                print(f"\nReached max_searches limit ({max_searches}). Stopping.")
                break
            
            search_count += 1
            region_name = region["name"]
            region_center = region["center"]
            radius_km = region.get("radius_km", 25)
            radius_meters = radius_km * 1000
            
            print(f"[{search_count}/{total_searches}] '{keyword}' in {region_name}...", end=" ", flush=True)
            
            # Geocode the region center if not cached
            lat_lng = geocode_location(region_center, api_key, cache, rate_limiter)
            
            # Search for places
            places = search_places_by_keyword(
                keyword=keyword,
                location=region_center,
                lat_lng=lat_lng,
                radius_meters=radius_meters,
                api_key=api_key,
                region=GOOGLE_PLACES_CONFIG["region"],
                cache=cache,
                rate_limiter=rate_limiter,
            )
            
            new_places = 0
            for place in places:
                place_name = place.get("name", "")  # Resource name like 'places/ChIJ...'
                place_id = place.get("id") or (place_name.split("/")[-1] if place_name else None)
                if not place_id or place_id in seen_place_ids:
                    continue
                
                seen_place_ids.add(place_id)
                new_places += 1
                places_found += 1
                
                # Get detailed info if requested
                details = None
                if fetch_details and place_name:
                    details = get_place_details(place_name, api_key, cache, rate_limiter)
                
                # Extract and store place data
                place_data = extract_place_data(place, details, keyword, region_name)
                all_places[place_id] = place_data
            
            print(f"found {len(places)} results, {new_places} new (total: {places_found})")
            
            # Save cache periodically
            if search_count % 10 == 0:
                save_cache(cache_path, cache)
        
        if max_searches and search_count >= max_searches:
            break
    
    # Final cache save
    save_cache(cache_path, cache)
    
    print(f"\n✅ Scraping complete!")
    print(f"   Total searches: {search_count}")
    print(f"   Unique places found: {len(all_places)}")
    
    return list(all_places.values())


def write_csv(output_path: str, rows: List[Dict[str, str]]) -> None:
    """Write places data to CSV file."""
    if not rows:
        print("No data to write.")
        return
    
    # Determine all columns
    all_columns = set()
    for row in rows:
        all_columns.update(row.keys())
    
    # Order columns sensibly
    priority_columns = [
        "gmaps_place_id", "gmaps_name", "gmaps_formatted_address", "gmaps_latitude", "gmaps_longitude",
        "gmaps_website", "gmaps_phone", "gmaps_rating", "gmaps_user_ratings_total",
        "search_keyword", "search_region"
    ]
    
    ordered_columns = []
    for col in priority_columns:
        if col in all_columns:
            ordered_columns.append(col)
            all_columns.remove(col)
    ordered_columns.extend(sorted(all_columns))
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ordered_columns)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"📄 Saved {len(rows)} places to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Scrape Google Places for neurodivergent resources across UK"
    )
    parser.add_argument("--output", required=True, help="Output CSV file path")
    parser.add_argument("--api-key", help="Google Maps API key (or use GOOGLE_MAPS_API_KEY env var)")
    parser.add_argument("--cache", help="Cache file path (default from config)")
    parser.add_argument("--test", action="store_true", help="Test mode: only 5 searches")
    parser.add_argument("--keywords-filter", help="Comma-separated keywords to use (default: all)")
    parser.add_argument("--regions-filter", help="Comma-separated region names to search (default: all)")
    parser.add_argument("--no-details", action="store_true", help="Skip fetching place details (faster but less data)")
    parser.add_argument("--rate-limit", type=int, help="Requests per minute (default from config)")
    parser.add_argument("--max-searches", type=int, help="Maximum number of searches to perform")
    
    args = parser.parse_args()
    
    # Get API key
    api_key = args.api_key or os.getenv(GOOGLE_PLACES_CONFIG["api_key_env"])
    if not api_key:
        print("Error: Google Maps API key required. Set {} env var or use --api-key".format(
            GOOGLE_PLACES_CONFIG['api_key_env']
        ))
        sys.exit(1)
    
    # Set up cache
    cache_path = args.cache or GOOGLE_PLACES_CONFIG["cache_file"]
    
    # Set up rate limiter
    rate_limit = args.rate_limit or GOOGLE_PLACES_CONFIG["requests_per_minute"]
    rate_limiter = RateLimiter(rate_limit)
    
    # Filter keywords if specified
    keywords = SEARCH_KEYWORDS
    if args.keywords_filter:
        filter_terms = [k.strip().lower() for k in args.keywords_filter.split(",")]
        keywords = [kw for kw in SEARCH_KEYWORDS if any(ft in kw.lower() for ft in filter_terms)]
        print(f"Filtered to {len(keywords)} keywords matching: {args.keywords_filter}")
    
    # Filter regions if specified
    regions = UK_REGIONS
    if args.regions_filter:
        filter_regions = [r.strip().lower() for r in args.regions_filter.split(",")]
        regions = [reg for reg in UK_REGIONS if any(fr in reg["name"].lower() for fr in filter_regions)]
        print(f"Filtered to {len(regions)} regions matching: {args.regions_filter}")
    
    # Test mode: limit searches
    max_searches = None
    if args.test:
        max_searches = 5
        print("🧪 TEST MODE: Limited to 5 searches")
    elif args.max_searches:
        max_searches = args.max_searches
    
    # Run the scraper
    places = scrape_uk_places(
        api_key=api_key,
        keywords=keywords,
        regions=regions,
        cache_path=cache_path,
        rate_limiter=rate_limiter,
        fetch_details=not args.no_details,
        max_searches=max_searches,
    )
    
    # Write output
    write_csv(args.output, places)
    
    print("\n✨ Done!")


if __name__ == "__main__":
    main()

