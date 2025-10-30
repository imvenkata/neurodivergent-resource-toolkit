#!/usr/bin/env python3
"""
Test script to validate keyword grouping doesn't miss significant results.
Compares grouped vs ungrouped searches.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.scrape_google_places import (
    load_cache,
    save_cache,
    geocode_location,
    search_places_by_keyword,
    RateLimiter,
)
from config import GOOGLE_PLACES_CONFIG


def test_keyword_group(api_key: str, test_groups: list, region: dict):
    """
    Test if grouped keywords find similar results to individual searches.
    """
    cache = load_cache(".cache/test_keyword_grouping.json")
    rate_limiter = RateLimiter(100)
    
    print("\n" + "="*80)
    print("🧪 KEYWORD GROUPING VALIDATION TEST")
    print("="*80)
    print(f"\nRegion: {region['name']}")
    print(f"Cache: .cache/test_keyword_grouping.json")
    
    lat_lng = geocode_location(region["center"], api_key, cache, rate_limiter)
    radius_meters = region.get("radius_km", 25) * 1000
    
    results = []
    
    for group in test_groups:
        primary = group["primary"]
        variants = group["variants"]
        
        print(f"\n{'─'*80}")
        print(f"📦 Testing group: '{primary}'")
        print(f"   Variants: {variants}")
        print(f"{'─'*80}")
        
        # Search with primary keyword
        primary_places = search_places_by_keyword(
            keyword=primary,
            location=region["center"],
            lat_lng=lat_lng,
            radius_meters=radius_meters,
            api_key=api_key,
            region=GOOGLE_PLACES_CONFIG["region"],
            cache=cache,
            rate_limiter=rate_limiter,
            max_results=60,
        )
        
        primary_ids = {p.get("id") for p in primary_places if p.get("id")}
        print(f"\n✓ Primary '{primary}': {len(primary_places)} results ({len(primary_ids)} unique IDs)")
        
        # Search with each variant
        all_variant_ids = set()
        variant_results = {}
        
        for variant in variants:
            variant_places = search_places_by_keyword(
                keyword=variant,
                location=region["center"],
                lat_lng=lat_lng,
                radius_meters=radius_meters,
                api_key=api_key,
                region=GOOGLE_PLACES_CONFIG["region"],
                cache=cache,
                rate_limiter=rate_limiter,
                max_results=60,
            )
            
            variant_ids = {p.get("id") for p in variant_places if p.get("id")}
            all_variant_ids.update(variant_ids)
            variant_results[variant] = variant_ids
            
            # Check overlap
            overlap = primary_ids & variant_ids
            unique_to_variant = variant_ids - primary_ids
            
            overlap_pct = (len(overlap) / len(variant_ids) * 100) if variant_ids else 0
            
            print(f"  - Variant '{variant}': {len(variant_places)} results ({len(variant_ids)} unique)")
            print(f"    ├─ Overlap with primary: {len(overlap)} ({overlap_pct:.1f}%)")
            print(f"    └─ Unique to variant: {len(unique_to_variant)}")
            
            if unique_to_variant:
                print(f"       ⚠️  Would MISS {len(unique_to_variant)} places with grouping!")
        
        # Overall analysis
        missed_ids = all_variant_ids - primary_ids
        total_unique = len(primary_ids | all_variant_ids)
        coverage = len(primary_ids) / total_unique * 100 if total_unique else 0
        
        print(f"\n📊 Group Summary:")
        print(f"   Total unique places (all keywords): {total_unique}")
        print(f"   Found by primary only: {len(primary_ids)}")
        print(f"   Missed by grouping: {len(missed_ids)} ({100-coverage:.1f}%)")
        
        if coverage >= 90:
            print(f"   ✅ GOOD: Primary covers {coverage:.1f}% of results")
        elif coverage >= 75:
            print(f"   ⚠️  MODERATE: Primary covers {coverage:.1f}% of results")
        else:
            print(f"   ❌ POOR: Primary only covers {coverage:.1f}% of results")
        
        results.append({
            "group": primary,
            "variants": variants,
            "total_unique": total_unique,
            "primary_count": len(primary_ids),
            "missed_count": len(missed_ids),
            "coverage_pct": coverage,
        })
    
    # Save cache
    save_cache(".cache/test_keyword_grouping.json", cache)
    
    # Overall summary
    print(f"\n{'='*80}")
    print("📊 OVERALL SUMMARY")
    print(f"{'='*80}")
    
    for result in results:
        status = "✅" if result["coverage_pct"] >= 90 else "⚠️ " if result["coverage_pct"] >= 75 else "❌"
        print(f"{status} '{result['group']}':")
        print(f"   Coverage: {result['coverage_pct']:.1f}% | Would miss: {result['missed_count']} places")
    
    avg_coverage = sum(r["coverage_pct"] for r in results) / len(results)
    total_missed = sum(r["missed_count"] for r in results)
    
    print(f"\n{'─'*80}")
    print(f"Average Coverage: {avg_coverage:.1f}%")
    print(f"Total Places Missed: {total_missed}")
    
    if avg_coverage >= 90:
        print("\n✅ RECOMMENDATION: Keyword grouping is SAFE to use")
        print("   Minimal data loss (<10%) for significant performance gain")
    elif avg_coverage >= 75:
        print("\n⚠️  RECOMMENDATION: Use keyword grouping with CAUTION")
        print("   Moderate data loss (10-25%), consider testing more")
    else:
        print("\n❌ RECOMMENDATION: DO NOT use keyword grouping")
        print("   High data loss (>25%), search all keywords individually")
    
    return results


if __name__ == "__main__":
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        print("❌ Error: GOOGLE_MAPS_API_KEY not found in environment")
        sys.exit(1)
    
    # Test with a few critical groups
    test_groups = [
        {
            "primary": "autism support",
            "variants": ["autism support", "ASD support", "autism spectrum services"],
        },
        {
            "primary": "autism assessment",
            "variants": ["autism assessment", "autism assessment clinic", "autism diagnostic center"],
        },
        {
            "primary": "ADHD assessment",
            "variants": ["ADHD assessment", "ADHD clinic", "ADHD diagnosis"],
        },
    ]
    
    # Test region (small for quick testing)
    test_region = {"name": "Hertfordshire", "center": "Hertford, Hertfordshire, UK", "radius_km": 25}
    
    print("\n🧪 Running keyword grouping validation test...")
    print("This will make multiple API calls to compare grouped vs individual searches")
    
    results = test_keyword_group(api_key, test_groups, test_region)

