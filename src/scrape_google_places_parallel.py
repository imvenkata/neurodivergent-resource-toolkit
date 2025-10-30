#!/usr/bin/env python3
"""
Parallel/optimized version of Google Places scraper with keyword grouping.
"""

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from config import GOOGLE_PLACES_CONFIG
from src.scrape_google_places import (
    RateLimiter,
    load_cache,
    save_cache,
    geocode_location,
    search_places_by_keyword,
    get_place_details,
    extract_place_data,
)


class ThreadSafeRateLimiter:
    """Thread-safe rate limiter for parallel API calls."""
    
    def __init__(self, requests_per_minute: int):
        import threading
        self.requests_per_minute = requests_per_minute
        self.min_interval = 60.0 / requests_per_minute if requests_per_minute > 0 else 0
        self.last_request_time = 0
        self.lock = threading.Lock()
    
    def wait_if_needed(self):
        """Thread-safe wait to respect rate limit."""
        if self.min_interval <= 0:
            return
        
        with self.lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                time.sleep(sleep_time)
            
            self.last_request_time = time.time()


def optimize_keywords(keywords: List[str]) -> List[Dict[str, any]]:
    """
    Group similar keywords to reduce redundant searches.
    
    Returns list of keyword groups with metadata:
    [{"primary": "autism", "variants": ["autism support", "ASD support"], ...}]
    """
    # Define keyword groups (primary term + variants)
    groups = [
        {
            "primary": "autism assessment",
            "variants": ["autism assessment clinic", "autism diagnostic center", "autism diagnosis"],
            "description": "Autism diagnosis and assessment services"
        },
        {
            "primary": "autism support",
            "variants": ["autism support center", "autism spectrum services", "ASD support", "autistic services"],
            "description": "General autism support services"
        },
        {
            "primary": "autism therapy",
            "variants": ["autism therapy", "speech therapy autism", "occupational therapy autism"],
            "description": "Autism therapy services"
        },
        {
            "primary": "autism community",
            "variants": ["autism social group", "autism community center", "autism support group", 
                        "autism parent support", "autism family support"],
            "description": "Autism community and social support"
        },
        {
            "primary": "autism employment",
            "variants": ["autism employment support", "autism job coaching", "supported employment neurodivergent"],
            "description": "Autism employment services"
        },
        {
            "primary": "autism charities",
            "variants": ["autism charities", "National Autistic Society", "Ambitious about Autism", "autism angels"],
            "description": "Autism charities and organizations"
        },
        {
            "primary": "ADHD assessment",
            "variants": ["ADHD assessment", "ADHD diagnosis", "ADHD clinic"],
            "description": "ADHD assessment and diagnosis"
        },
        {
            "primary": "ADHD support",
            "variants": ["ADHD support", "ADHD therapy", "attention deficit services"],
            "description": "ADHD support and therapy"
        },
        {
            "primary": "learning disability support",
            "variants": ["learning disability support", "dyslexia support", "dyspraxia services"],
            "description": "Learning disability support"
        },
        {
            "primary": "special educational needs",
            "variants": ["special educational needs", "SEN support", "special needs school", "special education"],
            "description": "Special educational needs"
        },
        {
            "primary": "special needs center",
            "variants": ["special needs center", "neurodivergent support", "neurodevelopmental services"],
            "description": "General neurodivergent support centers"
        },
        {
            "primary": "child development",
            "variants": ["child development center", "developmental pediatrician", "developmental disorders clinic",
                        "neurodevelopmental assessment"],
            "description": "Child development and assessment"
        },
        {
            "primary": "behavioral therapy",
            "variants": ["behavioral therapy", "sensory processing support", "life skills training autism"],
            "description": "Behavioral and sensory therapy"
        },
    ]
    
    # Filter groups to only include keywords that are in the input list
    filtered_groups = []
    for group in groups:
        matching_variants = [kw for kw in group["variants"] if kw in keywords]
        if matching_variants:
            filtered_groups.append({
                "primary": group["primary"],
                "variants": matching_variants,
                "description": group["description"]
            })
    
    return filtered_groups


def search_keyword_group_task(
    keyword_group: Dict,
    region: Dict,
    api_key: str,
    cache: Dict,
    rate_limiter: ThreadSafeRateLimiter,
    max_results_per_search: int,
    fetch_details: bool,
) -> Tuple[str, str, List[Dict]]:
    """
    Search for a keyword group in a region.
    Returns (keyword, region_name, list of place data dicts)
    """
    primary_keyword = keyword_group["primary"]
    region_name = region["name"]
    region_center = region["center"]
    radius_km = region.get("radius_km", 25)
    radius_meters = radius_km * 1000
    
    try:
        # Geocode location
        lat_lng = geocode_location(region_center, api_key, cache, rate_limiter)
        
        # Search with primary keyword
        places = search_places_by_keyword(
            keyword=primary_keyword,
            location=region_center,
            lat_lng=lat_lng,
            radius_meters=radius_meters,
            api_key=api_key,
            region=GOOGLE_PLACES_CONFIG["region"],
            cache=cache,
            rate_limiter=rate_limiter,
            max_results=max_results_per_search,
        )
        
        # Process places
        place_data_list = []
        for place in places:
            place_name = place.get("name", "")
            place_id = place.get("id") or (place_name.split("/")[-1] if place_name else None)
            
            if not place_id:
                continue
            
            # Get details if requested
            details = None
            if fetch_details and place_name:
                details = get_place_details(place_name, api_key, cache, rate_limiter)
            
            # Extract place data
            place_data = extract_place_data(place, details, primary_keyword, region_name)
            place_data_list.append(place_data)
        
        return (primary_keyword, region_name, place_data_list)
    
    except Exception as e:
        print(f"\n❌ Error in task '{primary_keyword}' @ {region_name}: {e}")
        return (primary_keyword, region_name, [])


def scrape_uk_places_parallel(
    api_key: str,
    keywords: List[str],
    regions: List[Dict],
    cache_path: str,
    rate_limiter: ThreadSafeRateLimiter,
    fetch_details: bool = True,
    max_searches: Optional[int] = None,
    max_results_per_search: int = 60,
    max_workers: int = 5,
    use_keyword_grouping: bool = True,
) -> List[Dict[str, str]]:
    """
    Parallel version of scrape_uk_places with optional keyword grouping.
    
    Args:
        max_workers: Number of parallel threads (default: 5, be careful with rate limits!)
        use_keyword_grouping: If True, group similar keywords to reduce searches
    """
    cache = load_cache(cache_path)
    all_places: Dict[str, Dict[str, str]] = {}  # place_id -> place_data
    seen_websites: Set[str] = set()  # Track websites to prevent duplicates
    
    # Optimize keywords if requested
    if use_keyword_grouping:
        keyword_groups = optimize_keywords(keywords)
        print(f"📦 Grouped {len(keywords)} keywords into {len(keyword_groups)} groups")
    else:
        # Create simple groups (one keyword per group)
        keyword_groups = [{"primary": kw, "variants": [kw], "description": ""} for kw in keywords]
    
    # Create task list
    tasks = []
    for keyword_group in keyword_groups:
        for region in regions:
            tasks.append((keyword_group, region))
    
    if max_searches:
        tasks = tasks[:max_searches]
    
    total_searches = len(tasks)
    print(f"\nStarting parallel scrape: {len(keyword_groups)} keyword groups × {len(regions)} regions = {total_searches} searches")
    print(f"Workers: {max_workers}")
    print(f"Rate limit: {rate_limiter.requests_per_minute} requests/minute")
    print(f"Fetch details: {fetch_details}")
    print(f"Keyword grouping: {'ON' if use_keyword_grouping else 'OFF'}\n")
    
    completed = 0
    places_found = 0
    
    # Execute searches in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_task = {}
        for keyword_group, region in tasks:
            future = executor.submit(
                search_keyword_group_task,
                keyword_group=keyword_group,
                region=region,
                api_key=api_key,
                cache=cache,
                rate_limiter=rate_limiter,
                max_results_per_search=max_results_per_search,
                fetch_details=fetch_details,
            )
            future_to_task[future] = (keyword_group["primary"], region["name"])
        
        # Process completed tasks
        for future in as_completed(future_to_task):
            keyword, region_name = future_to_task[future]
            completed += 1
            
            try:
                keyword, region_name, place_data_list = future.result()
                
                # Deduplicate by place_id and website
                new_count = 0
                for place_data in place_data_list:
                    place_id = place_data.get("gmaps_place_id", "")
                    website = place_data.get("gmaps_website", "").strip().lower()
                    
                    if not place_id:
                        continue
                    
                    # Skip if we've already seen this place_id
                    if place_id in all_places:
                        continue
                    
                    # Skip if we've already seen this website (and it's not empty)
                    if website and website in seen_websites:
                        continue
                    
                    all_places[place_id] = place_data
                    if website:
                        seen_websites.add(website)
                    new_count += 1
                    places_found += 1
                
                print(f"[{completed}/{total_searches}] '{keyword}' in {region_name}... "
                      f"found {len(place_data_list)} results, {new_count} new (total: {places_found})")
                
            except Exception as e:
                print(f"[{completed}/{total_searches}] '{keyword}' in {region_name}... ERROR: {e}")
    
    # Save cache
    save_cache(cache_path, cache)
    
    print(f"\n✅ Scraping complete!")
    print(f"   Total searches: {total_searches}")
    print(f"   Unique places found: {len(all_places)}")
    
    return list(all_places.values())

