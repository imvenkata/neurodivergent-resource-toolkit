# UK Expansion Pipeline Guide

## Overview

This guide explains how to expand your neurodivergent resource database from London/Hertfordshire to cover the entire UK using the Google Places scraping pipeline.

## Pipeline Architecture

The expansion pipeline consists of three main components:

1. **Configuration (`config.py`)**: Defines search keywords and UK regions
2. **Scraper (`src/scrape_google_places.py`)**: Searches Google Places API systematically
3. **Pipeline (`src/expand_uk_coverage.py`)**: Combines scraped data with existing resources

## Quick Start

### Prerequisites

1. **Google Maps API Key**: Ensure `GOOGLE_MAPS_API_KEY` is set in your `.env` file
2. **Python Dependencies**: Install required packages (already in your environment)

### Test Run (Recommended First Step)

Run a small test to verify everything works:

```bash
python src/expand_uk_coverage.py \
  --test \
  --output data/output/test_expansion.xlsx
```

This performs only 5 searches and shows you how the pipeline works.

### Targeted Expansion

Search specific regions or keywords:

```bash
# Expand to Manchester and Birmingham only
python src/expand_uk_coverage.py \
  --regions-filter "Manchester,Birmingham" \
  --output data/output/expanded_manchester_birmingham.xlsx

# Focus on autism-specific keywords
python src/expand_uk_coverage.py \
  --keywords-filter "autism" \
  --regions-filter "Manchester,Leeds,Liverpool" \
  --output data/output/expanded_autism_northwest.xlsx

# Limit number of searches
python src/expand_uk_coverage.py \
  --keywords-filter "autism,ADHD" \
  --max-searches 50 \
  --output data/output/expanded_partial.xlsx
```

### Full UK Expansion

**⚠️ WARNING**: This will perform approximately **3,200+ API calls** (47 keywords × 70 regions)!

- **Cost**: ~$32-64 depending on your Google Places pricing
- **Time**: 30-60 minutes with rate limiting
- **API Quota**: Ensure you have sufficient quota

```bash
python src/expand_uk_coverage.py \
  --output data/output/expanded_resources_uk_full.xlsx
```

## Configuration

### Keywords (`config.py`)

The pipeline uses 47 comprehensive keywords covering:

- **Autism**: "autism support center", "autism assessment clinic", "autism therapy", etc.
- **ADHD**: "ADHD assessment", "ADHD clinic", "ADHD support", etc.
- **Learning Disabilities**: "dyslexia support", "special educational needs", etc.
- **Service Types**: "occupational therapy autism", "autism employment support", etc.
- **Organizations**: "National Autistic Society", "Ambitious about Autism", etc.

You can modify `SEARCH_KEYWORDS` in `config.py` to add or remove keywords.

### UK Regions (`config.py`)

70 regions covering:

- **England**: All major counties and cities
- **Wales**: Cardiff, Swansea, Newport, regional areas
- **Scotland**: Glasgow, Edinburgh, Aberdeen, Highlands, etc.
- **Northern Ireland**: Belfast, Derry, etc.

Each region has a center point and search radius (15-40km based on area size).

### Rate Limiting

Default: **100 requests/minute** (conservative)

- Adjust in `config.py`: `GOOGLE_PLACES_CONFIG["requests_per_minute"]`
- Or use command-line: `--rate-limit 150`

Google Places API standard limits:
- Free tier: Varies by endpoint
- Paid tier: Can go higher with increased costs

## Command-Line Options

### `expand_uk_coverage.py` (Main Pipeline)

#### Input/Output
- `--input PATH`: Existing resources file (default: `data/input/enriched_resources_28Oct25.xlsx`)
- `--output PATH`: Output file path (required, .csv or .xlsx)
- `--scraped-cache PATH`: Save/load scraped data to avoid re-scraping

#### Scraping Control
- `--test`: Test mode (only 5 searches)
- `--skip-scraping`: Use cached scraped data only
- `--keywords-filter "keyword1,keyword2"`: Filter keywords
- `--regions-filter "region1,region2"`: Filter regions
- `--max-searches N`: Limit total number of searches
- `--no-details`: Skip place details (faster, less data)

#### API Configuration
- `--api-key KEY`: Google Maps API key (or use env var)
- `--rate-limit N`: Requests per minute

#### Merging
- `--prefer-new`: Prefer new data over existing when merging duplicates (default: prefer existing)

### `scrape_google_places.py` (Standalone Scraper)

Can be used independently:

```bash
python src/scrape_google_places.py \
  --output data/output/scraped_places.csv \
  --keywords-filter "autism" \
  --regions-filter "Manchester"
```

## Usage Examples

### Example 1: Incremental Expansion by Region

Expand coverage gradually to manage costs:

```bash
# Week 1: North West England
python src/expand_uk_coverage.py \
  --regions-filter "Manchester,Liverpool,Lancashire,Cheshire" \
  --scraped-cache data/output/scraped_northwest.csv \
  --output data/output/expanded_week1.xlsx

# Week 2: Midlands
python src/expand_uk_coverage.py \
  --regions-filter "Birmingham,Nottingham,Leicester,Derby" \
  --scraped-cache data/output/scraped_midlands.csv \
  --output data/output/expanded_week2.xlsx

# Week 3: Scotland
python src/expand_uk_coverage.py \
  --regions-filter "Glasgow,Edinburgh,Aberdeen,Dundee" \
  --scraped-cache data/output/scraped_scotland.csv \
  --output data/output/expanded_week3.xlsx
```

### Example 2: Focus on Specific Services

Search only for assessment and diagnosis centers:

```bash
python src/expand_uk_coverage.py \
  --keywords-filter "assessment,diagnosis,clinic" \
  --output data/output/expanded_assessment_centers.xlsx
```

### Example 3: Using Scraped Cache

Scrape once, then reuse data:

```bash
# Step 1: Scrape and cache
python src/expand_uk_coverage.py \
  --regions-filter "Manchester,Leeds,Sheffield" \
  --scraped-cache data/output/scraped_yorkshire.csv \
  --output data/output/expanded_yorkshire_v1.xlsx

# Step 2: Re-merge with different existing data (no new API calls)
python src/expand_uk_coverage.py \
  --skip-scraping \
  --scraped-cache data/output/scraped_yorkshire.csv \
  --input data/input/alternative_source.csv \
  --output data/output/expanded_yorkshire_v2.xlsx
```

## Output Format

The pipeline produces files matching your existing `enriched_resources.csv` schema with these fields:

### Core Google Maps Fields
- `gmaps_place_id`: Unique Google Place ID
- `gmaps_name`: Business/organization name
- `gmaps_formatted_address`: Full address
- `gmaps_latitude`, `gmaps_longitude`: Coordinates
- `gmaps_website`: Website URL
- `gmaps_phone`: Phone number
- `gmaps_rating`, `gmaps_user_ratings_total`: Ratings
- `gmaps_opening_hours_weekday_text`: Opening hours
- And many more...

### Enrichment Fields
- `description_short`: (Empty for new records, fill via batch enrichment pipeline)
- `age_range`: (Empty initially)
- `conditions_supported`: (Empty initially)
- `specific_services`: (Empty initially)
- `organization_type`: (Empty initially)

### Search Metadata
- `search_keyword`: Keyword that found this place
- `search_region`: Region where found

### Next Step: Enrichment

After expanding coverage, run the LLM enrichment pipeline to fill in detailed information:

```bash
python src/batch_enrich_pipeline_parallel.py \
  --input data/output/expanded_resources_uk_full.xlsx \
  --output data/output/enriched_resources_uk_complete.xlsx \
  --workers 10
```

## Deduplication

The pipeline automatically deduplicates based on `gmaps_place_id`:

- **Duplicates Found**: Same place appears in existing data
- **Merge Strategy**: By default, keeps existing data and fills in missing fields from new data
- **Override**: Use `--prefer-new` to prefer newly scraped data

## Cost Estimation

### Google Places API Pricing (as of 2024)

- **Text Search**: $32 per 1000 requests
- **Place Details**: $17 per 1000 requests (if using `--no-details`, skip this)

### Full UK Expansion Cost

- Keywords: 47
- Regions: 70
- Total searches: ~3,290

**Without details** (`--no-details`):
- 3,290 text searches = ~$105

**With details** (default):
- 3,290 text searches = ~$105
- Assuming ~5000 unique places found
- 5,000 place details = ~$85
- **Total: ~$190**

**Tip**: Start with `--no-details` to get place IDs cheaply, then fetch details only for relevant places.

## Caching

The scraper uses aggressive caching to avoid duplicate API calls:

- Cache location: `.cache/google_places_scraping_cache.json`
- Caches both text searches and place details
- Rerun the same search = instant results from cache
- Clear cache to force fresh data: `rm -rf .cache/google_places_scraping_cache.json`

## Troubleshooting

### API Key Issues

```
Error: Google Maps API key required
```

**Solution**: Ensure `.env` file contains:
```
GOOGLE_MAPS_API_KEY=your_actual_api_key_here
```

### Rate Limiting

```
Google Places API: OVER_QUERY_LIMIT
```

**Solution**: Reduce rate limit:
```bash
--rate-limit 50
```

### No Results Found

If searches return zero results, verify:
1. API key has Places API enabled
2. Keywords are appropriate for UK market
3. Regions are correctly specified

### Import Errors

```
ModuleNotFoundError: No module named 'pandas'
```

**Solution**: Install dependencies:
```bash
pip install pandas openpyxl python-dotenv
```

## Performance Tips

1. **Use `--no-details` first**: Get all place IDs quickly and cheaply
2. **Filter smartly**: Use `--keywords-filter` and `--regions-filter` to focus on high-value searches
3. **Incremental approach**: Expand region by region to manage costs
4. **Monitor cache**: Check cache file size to see progress
5. **Batch processing**: Use `--scraped-cache` to separate scraping from merging

## Advanced Usage

### Custom Keyword List

Edit `config.py` and modify `SEARCH_KEYWORDS`:

```python
SEARCH_KEYWORDS = [
    "your custom keyword 1",
    "your custom keyword 2",
    # ... add more
]
```

### Custom Regions

Edit `config.py` and modify `UK_REGIONS`:

```python
UK_REGIONS = [
    {"name": "Custom Region", "center": "City Name, UK", "radius_km": 30},
    # ... add more
]
```

### Integration with Other Tools

The output CSV/XLSX can be used with:

1. **LLM Enrichment Pipeline**: `batch_enrich_pipeline_parallel.py`
2. **Validation**: `validate_neurodivergent.py`
3. **Geographic Tagging**: `add_geographic_tags.py`
4. **Domain Fixes**: `fix_domain_extensions.py`

## Support

For issues or questions:
1. Check this guide first
2. Review the script help: `python src/expand_uk_coverage.py --help`
3. Check cache and log files
4. Verify API key and permissions

## Summary Workflow

```
1. Test: python src/expand_uk_coverage.py --test --output test.xlsx
2. Review: Check test.xlsx to verify data quality
3. Expand: Run with your chosen regions/keywords
4. Enrich: Use batch_enrich_pipeline_parallel.py for detailed info
5. Validate: Use validate_neurodivergent.py to ensure relevance
6. Deploy: Your comprehensive UK resource database is ready!
```

---

**Note**: Always start with `--test` mode to verify your setup before running large-scale expansions.

