# Google Places Scraping Optimization Guide

## Overview

This guide explains the optimization strategies available for scraping Google Places data more efficiently.

## Optimization Strategies

### 1. **Keyword Grouping** ⭐ RECOMMENDED

Groups similar keywords together to reduce redundant API calls.

**How it works:**
- Groups `["autism support center", "autism spectrum services", "ASD support"]` → searches only `"autism support"`
- Reduces 45 keywords → 13 keyword groups (71% fewer searches!)
- Results cover all variants due to Google's semantic search

**Configuration:**
```python
# config.py
GOOGLE_PLACES_CONFIG = {
    "use_keyword_grouping": True,  # Enable grouping
}
```

**Command line:**
```bash
# Enabled by default with --parallel
python src/expand_uk_coverage.py --regions-filter "Kent" --parallel

# Disable if needed
python src/expand_uk_coverage.py --regions-filter "Kent" --parallel --no-keyword-grouping
```

**Keyword Groups:**
1. **autism assessment** - diagnosis and assessment services
2. **autism support** - general support services  
3. **autism therapy** - therapy services
4. **autism community** - social groups and support
5. **autism employment** - employment services
6. **autism charities** - charities and organizations
7. **ADHD assessment** - ADHD diagnosis
8. **ADHD support** - ADHD support and therapy
9. **learning disability support** - dyslexia, dyspraxia
10. **special educational needs** - SEN schools and support
11. **special needs center** - neurodivergent centers
12. **child development** - pediatric development
13. **behavioral therapy** - behavioral and sensory therapy

### 2. **Parallel Processing** ⚡ FAST

Runs multiple searches simultaneously using ThreadPoolExecutor.

**Benefits:**
- 3-5x faster execution time
- Better resource utilization
- Thread-safe rate limiting

**Configuration:**
```python
# config.py
GOOGLE_PLACES_CONFIG = {
    "use_parallel": True,
    "max_workers": 5,  # Number of concurrent threads
}
```

**Command line:**
```bash
# Use 5 workers (default)
python src/expand_uk_coverage.py --regions-filter "Kent" --parallel

# Use 3 workers (more conservative)
python src/expand_uk_coverage.py --regions-filter "Kent" --parallel --workers 3

# Use 10 workers (aggressive, watch rate limits!)
python src/expand_uk_coverage.py --regions-filter "Kent" --parallel --workers 10
```

**⚠️ Caution:**
- More workers = more concurrent API calls
- Respect rate limits (100 requests/minute default)
- Start with 3-5 workers, increase gradually

### 3. **Pagination**

Fetches multiple pages of results per search (default: up to 60 results).

**How it works:**
- Google Places API returns max 20 results per request
- Pagination fetches additional pages using `nextPageToken`
- Default: fetch 3 pages (60 results total)

**Configuration:**
```python
# config.py
GOOGLE_PLACES_CONFIG = {
    "max_results_per_search": 60,  # 3 pages (default)
}
```

**Options:**
```python
"max_results_per_search": 20,   # 1 page (faster, less data)
"max_results_per_search": 40,   # 2 pages (balanced)
"max_results_per_search": 60,   # 3 pages (default, recommended)
"max_results_per_search": 100,  # 5 pages (thorough but slower)
```

## Performance Comparison

### Sequential (No Optimizations)
```bash
python src/expand_uk_coverage.py --regions-filter "Kent"
```
- **Searches**: 45 keywords × 1 region = 45 searches
- **Time**: ~5-7 minutes
- **API Calls**: ~135-180 (with pagination)

### Parallel + Keyword Grouping (RECOMMENDED)
```bash
python src/expand_uk_coverage.py --regions-filter "Kent" --parallel --workers 5
```
- **Searches**: 13 groups × 1 region = 13 searches  
- **Time**: ~2-3 minutes
- **API Calls**: ~39-52 (with pagination)
- **Speed-up**: 2-3x faster
- **Cost savings**: 71% fewer API calls

## Best Practices

### 1. **Testing** (Small Region)
```bash
# Test with small search count
python src/expand_uk_coverage.py \
  --regions-filter "Hertfordshire" \
  --max-searches 10 \
  --parallel --workers 3
```

### 2. **Single Region** (Production)
```bash
# Full region scan with optimizations
python src/expand_uk_coverage.py \
  --regions-filter "Kent" \
  --parallel --workers 5
```

### 3. **Multiple Regions** (Large Scale)
```bash
# Multiple regions with conservative workers
python src/expand_uk_coverage.py \
  --regions-filter "Kent,Surrey,Essex" \
  --parallel --workers 3
```

### 4. **Full UK Scan** (⚠️ Many API Calls!)
```bash
# All regions - will take hours and many API calls
python src/expand_uk_coverage.py \
  --parallel --workers 5 \
  --rate-limit 60  # Be more conservative
```

## Rate Limiting

**Default**: 100 requests/minute

**Adjust based on your needs:**
```bash
# Conservative (safer for large scans)
python src/expand_uk_coverage.py --rate-limit 60 --parallel

# Aggressive (if you have high quota)
python src/expand_uk_coverage.py --rate-limit 200 --parallel --workers 10
```

## Cost Optimization

### API Pricing (Google Places API New)
- **Text Search**: SKU limited, check current pricing
- **Place Details**: Contact Data (2 fields) + Basic Data (free)
- **Geocoding**: Usually included in free tier

### Tips to Reduce Costs:
1. ✅ **Use keyword grouping** - 71% fewer searches
2. ✅ **Set max_results_per_search** wisely - don't fetch 100 if 60 is enough
3. ✅ **Use --no-details** for initial scans - only basic data
4. ✅ **Filter regions** - don't scan all UK at once
5. ✅ **Use cache** - won't repeat searches (automatic)

### Example: Cost-Optimized Scan
```bash
# Quick scan without details (cheapest)
python src/expand_uk_coverage.py \
  --regions-filter "Kent" \
  --parallel --workers 5 \
  --no-details

# Then enrich details later if needed
python src/batch_enrich_pipeline_parallel.py \
  --input data/db/enriched_resources_latest.csv
```

## Monitoring Progress

The pipeline shows real-time progress:
```
📦 Grouped 45 keywords into 13 groups
Starting parallel scrape: 13 keyword groups × 1 regions = 13 searches
Workers: 5
Rate limit: 100 requests/minute

[1/13] 'autism support' in Kent... found 58 results, 54 new (total: 54)
[2/13] 'autism assessment' in Kent... found 57 results, 31 new (total: 85)
...
```

## Troubleshooting

### "Too many requests" errors
- Reduce `--workers` (try 3 instead of 5)
- Reduce `--rate-limit` (try 60 instead of 100)

### Parallel mode not working
- Check that `src/scrape_google_places_parallel.py` exists
- Python 3.7+ required for ThreadPoolExecutor

### Duplicate results
- Normal! The pipeline automatically deduplicates by:
  - `gmaps_place_id`
  - Website URL
- Statistics show duplicates found vs new added

## Summary

**Recommended Setup for Most Users:**
```bash
python src/expand_uk_coverage.py \
  --regions-filter "YourRegion" \
  --parallel \
  --workers 5
```

This gives you:
- ✅ 71% fewer API calls (keyword grouping)
- ✅ 2-3x faster execution (parallel processing)
- ✅ Up to 60 results per keyword (pagination)
- ✅ Thread-safe rate limiting
- ✅ Automatic caching and deduplication

