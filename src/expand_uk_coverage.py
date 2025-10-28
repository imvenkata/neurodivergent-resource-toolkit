#!/usr/bin/env python3
"""
Pipeline to expand UK coverage by scraping new places and combining with existing data.

This script:
1. Scrapes new places from Google Places API using keywords and regions
2. Loads existing enriched resources
3. Deduplicates based on gmaps_place_id
4. Combines datasets with smart merging
5. Outputs combined dataset

Usage:
    # Test run (only 5 searches)
    python src/expand_uk_coverage.py --test --output data/output/expanded_resources_test.xlsx
    
    # Production run with specific keywords/regions
    python src/expand_uk_coverage.py --keywords-filter "autism,ADHD" --regions-filter "Manchester,Birmingham" --output data/output/expanded_resources.xlsx
    
    # Full UK expansion (WARNING: This will make many API calls!)
    python src/expand_uk_coverage.py --output data/output/expanded_resources_uk.xlsx
"""

import argparse
import csv
import os
import sys
from pathlib import Path
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from config import GOOGLE_PLACES_CONFIG, SEARCH_KEYWORDS, UK_REGIONS, DATA_DIR

# Import the scraper
from src.scrape_google_places import scrape_uk_places, RateLimiter


def read_csv(path: str) -> List[Dict[str, str]]:
    """Read CSV file and return list of dictionaries."""
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert None to empty string
            rows.append({k: (v if v is not None else "") for k, v in row.items()})
    return rows


def read_excel(path: str) -> List[Dict[str, str]]:
    """Read Excel file and return list of dictionaries."""
    try:
        import pandas as pd
    except ImportError:
        print("Error: pandas is required to read Excel files. Install with: pip install pandas openpyxl")
        sys.exit(1)
    
    df = pd.read_excel(path, engine="openpyxl")
    # Replace NaN with empty string
    df = df.fillna("")
    # Convert to list of dicts
    return df.to_dict("records")


def load_existing_resources(input_path: str) -> List[Dict[str, str]]:
    """Load existing enriched resources from CSV or Excel."""
    if not os.path.exists(input_path):
        print(f"Warning: Input file not found: {input_path}")
        return []
    
    print(f"Loading existing resources from {input_path}...")
    
    if input_path.endswith(".xlsx"):
        rows = read_excel(input_path)
    else:
        rows = read_csv(input_path)
    
    print(f"✅ Loaded {len(rows)} existing resources")
    return rows


def merge_place_data(existing: Dict[str, str], new: Dict[str, str], prefer_existing: bool = True) -> Dict[str, str]:
    """
    Merge two place records intelligently.
    
    Args:
        existing: Existing place data
        new: New place data from scraping
        prefer_existing: If True, prefer existing data when both have values
    
    Returns:
        Merged dictionary
    """
    merged = existing.copy()
    
    for key, new_value in new.items():
        if key not in merged or not merged[key]:
            # Field doesn't exist or is empty in existing data, add it
            merged[key] = new_value
        elif new_value and not prefer_existing:
            # New value exists and we prefer new data
            merged[key] = new_value
        # else: keep existing value
    
    return merged


def deduplicate_and_merge(
    existing_resources: List[Dict[str, str]],
    new_places: List[Dict[str, str]],
    prefer_existing: bool = True,
) -> tuple[List[Dict[str, str]], Dict[str, int]]:
    """
    Deduplicate and merge existing resources with newly scraped places.
    
    Args:
        existing_resources: List of existing resource dictionaries
        new_places: List of newly scraped place dictionaries
        prefer_existing: If True, prefer existing data in conflicts
    
    Returns:
        Tuple of (merged_list, statistics_dict)
    """
    # Build index of existing resources by place_id
    existing_by_id: Dict[str, Dict[str, str]] = {}
    for resource in existing_resources:
        place_id = resource.get("gmaps_place_id", "").strip()
        if place_id:
            existing_by_id[place_id] = resource
    
    # Track statistics
    stats = {
        "existing_count": len(existing_resources),
        "new_scraped_count": len(new_places),
        "duplicates_found": 0,
        "new_added": 0,
        "updated": 0,
    }
    
    # Process new places
    merged_resources = existing_resources.copy()
    new_places_to_add = []
    
    for new_place in new_places:
        place_id = new_place.get("gmaps_place_id", "").strip()
        if not place_id:
            continue
        
        if place_id in existing_by_id:
            # Duplicate found - merge data
            stats["duplicates_found"] += 1
            existing_idx = None
            for idx, res in enumerate(merged_resources):
                if res.get("gmaps_place_id") == place_id:
                    existing_idx = idx
                    break
            
            if existing_idx is not None:
                merged = merge_place_data(merged_resources[existing_idx], new_place, prefer_existing)
                merged_resources[existing_idx] = merged
                stats["updated"] += 1
        else:
            # New place not in existing data
            new_places_to_add.append(new_place)
            stats["new_added"] += 1
    
    # Add new places to the end
    merged_resources.extend(new_places_to_add)
    
    stats["total_count"] = len(merged_resources)
    
    return merged_resources, stats


def write_output(rows: List[Dict[str, str]], output_path: str) -> None:
    """Write merged data to CSV or Excel based on file extension."""
    if not rows:
        print("No data to write.")
        return
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    if output_path.endswith(".xlsx"):
        write_excel(output_path, rows)
    else:
        write_csv_simple(output_path, rows)


def write_csv_simple(output_path: str, rows: List[Dict[str, str]]) -> None:
    """Write data to CSV file."""
    if not rows:
        return
    
    # Get all column names
    all_columns = set()
    for row in rows:
        all_columns.update(row.keys())
    
    # Order columns sensibly
    priority_columns = [
        "sno", "gmaps_place_id", "gmaps_name", "gmaps_formatted_address", 
        "gmaps_latitude", "gmaps_longitude", "gmaps_opening_hours_weekday_text",
        "gmaps_website", "gmaps_phone", "gmaps_rating", "gmaps_user_ratings_total"
    ]
    
    ordered_columns = []
    for col in priority_columns:
        if col in all_columns:
            ordered_columns.append(col)
            all_columns.remove(col)
    ordered_columns.extend(sorted(all_columns))
    
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ordered_columns)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"📄 Saved to {output_path}")


def write_excel(output_path: str, rows: List[Dict[str, str]]) -> None:
    """Write data to Excel file."""
    try:
        import pandas as pd
    except ImportError:
        print("Warning: pandas not installed. Saving as CSV instead.")
        csv_path = output_path.replace(".xlsx", ".csv")
        write_csv_simple(csv_path, rows)
        return
    
    if not rows:
        df = pd.DataFrame()
    else:
        df = pd.DataFrame(rows)
    
    try:
        df.to_excel(output_path, index=False, engine="openpyxl")
        print(f"📄 Saved to {output_path}")
    except Exception as e:
        print(f"Error saving Excel: {e}")
        print("Saving as CSV instead...")
        csv_path = output_path.replace(".xlsx", ".csv")
        write_csv_simple(csv_path, rows)


def print_statistics(stats: Dict[str, int]) -> None:
    """Print merging statistics."""
    print("\n" + "="*60)
    print("📊 MERGE STATISTICS")
    print("="*60)
    print(f"  Existing resources:     {stats['existing_count']:>6}")
    print(f"  New places scraped:     {stats['new_scraped_count']:>6}")
    print(f"  Duplicates found:       {stats['duplicates_found']:>6}")
    print(f"  Records updated:        {stats['updated']:>6}")
    print(f"  New records added:      {stats['new_added']:>6}")
    print(f"  {'─'*58}")
    print(f"  Total records:          {stats['total_count']:>6}")
    print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Expand UK coverage by scraping and merging with existing data"
    )
    
    # I/O arguments
    parser.add_argument(
        "--input",
        default=str(DATA_DIR / "input" / "enriched_resources_28Oct25.xlsx"),
        help="Path to existing enriched resources (CSV or Excel)",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output path for combined dataset (CSV or Excel)",
    )
    parser.add_argument(
        "--scraped-cache",
        help="Path to save/load scraped data (CSV) to avoid re-scraping",
    )
    
    # Scraping arguments
    parser.add_argument(
        "--skip-scraping",
        action="store_true",
        help="Skip scraping and only use scraped-cache file",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode: only perform 5 searches",
    )
    parser.add_argument(
        "--keywords-filter",
        help="Comma-separated keywords to use (e.g., 'autism,ADHD')",
    )
    parser.add_argument(
        "--regions-filter",
        help="Comma-separated region names to search (e.g., 'London,Manchester')",
    )
    parser.add_argument(
        "--max-searches",
        type=int,
        help="Maximum number of searches to perform",
    )
    parser.add_argument(
        "--no-details",
        action="store_true",
        help="Skip fetching place details (faster but less data)",
    )
    
    # API configuration
    parser.add_argument(
        "--api-key",
        help="Google Maps API key (or use GOOGLE_MAPS_API_KEY env var)",
    )
    parser.add_argument(
        "--rate-limit",
        type=int,
        help="Requests per minute (default from config)",
    )
    
    # Merging arguments
    parser.add_argument(
        "--prefer-new",
        action="store_true",
        help="Prefer new scraped data over existing when merging duplicates",
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("🚀 UK NEURODIVERGENT RESOURCE EXPANSION PIPELINE")
    print("="*60 + "\n")
    
    # Load existing resources
    existing_resources = load_existing_resources(args.input)
    
    # Scrape or load new places
    new_places = []
    
    if args.skip_scraping:
        if not args.scraped_cache or not os.path.exists(args.scraped_cache):
            print("Error: --skip-scraping requires --scraped-cache with existing file")
            sys.exit(1)
        print(f"Loading scraped data from {args.scraped_cache}...")
        new_places = read_csv(args.scraped_cache)
        print(f"✅ Loaded {len(new_places)} scraped places from cache")
    else:
        # Get API key
        api_key = args.api_key or os.getenv(GOOGLE_PLACES_CONFIG["api_key_env"])
        if not api_key:
            print("Error: Google Maps API key required.")
            print("Set {} env var or use --api-key".format(
                GOOGLE_PLACES_CONFIG['api_key_env']
            ))
            sys.exit(1)
        
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
        
        # Determine max searches
        max_searches = None
        if args.test:
            max_searches = 5
            print("🧪 TEST MODE: Limited to 5 searches\n")
        elif args.max_searches:
            max_searches = args.max_searches
        
        # Run scraper
        print("\n" + "─"*60)
        print("📡 SCRAPING GOOGLE PLACES")
        print("─"*60 + "\n")
        
        cache_path = GOOGLE_PLACES_CONFIG["cache_file"]
        
        new_places = scrape_uk_places(
            api_key=api_key,
            keywords=keywords,
            regions=regions,
            cache_path=cache_path,
            rate_limiter=rate_limiter,
            fetch_details=not args.no_details,
            max_searches=max_searches,
        )
        
        # Save scraped data if cache path provided
        if args.scraped_cache:
            write_csv_simple(args.scraped_cache, new_places)
            print(f"💾 Saved scraped data to {args.scraped_cache}")
    
    # Merge and deduplicate
    print("\n" + "─"*60)
    print("🔀 MERGING AND DEDUPLICATING")
    print("─"*60 + "\n")
    
    merged_resources, stats = deduplicate_and_merge(
        existing_resources=existing_resources,
        new_places=new_places,
        prefer_existing=not args.prefer_new,
    )
    
    # Print statistics
    print_statistics(stats)
    
    # Add sequential sno if not present
    for idx, resource in enumerate(merged_resources, start=1):
        if "sno" not in resource or not resource["sno"]:
            resource["sno"] = str(idx)
    
    # Write output
    write_output(merged_resources, args.output)
    
    print("✨ Pipeline complete!\n")


if __name__ == "__main__":
    main()

