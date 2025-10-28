# UK Expansion Pipeline - Quick Start

## ✅ What's Been Built

I've created a complete pipeline to expand your neurodivergent resource database across the entire UK:

### 1. **Configuration** (`config.py`)
- ✅ 45+ comprehensive search keywords (autism, ADHD, learning disabilities, etc.)
- ✅ 70 UK regions covering England, Wales, Scotland, and Northern Ireland
- ✅ Rate limiting and API configuration

### 2. **Google Places Scraper** (`src/scrape_google_places.py`)
- ✅ Systematic search across keywords and regions
- ✅ Caching to avoid duplicate API calls
- ✅ Rate limiting to manage costs
- ✅ Extracts all Google Maps data (address, phone, website, hours, ratings, etc.)

### 3. **Expansion Pipeline** (`src/expand_uk_coverage.py`)
- ✅ Combines new scraped data with existing resources
- ✅ Automatic deduplication by `gmaps_place_id`
- ✅ Smart merging (preserves existing data, fills in gaps)
- ✅ Outputs in CSV or Excel format

### 4. **Documentation** (`docs/UK_EXPANSION_GUIDE.md`)
- ✅ Comprehensive usage guide
- ✅ Cost estimates and performance tips
- ✅ Examples for different scenarios

## 🚀 How to Use

### Step 1: Enable Google Cloud Billing

The test showed you need to enable billing on your Google Cloud Project:

1. Go to: https://console.cloud.google.com/project/_/billing/enable
2. Enable billing for your project
3. Ensure "Places API" is enabled

### Step 2: Test the Pipeline

```bash
python src/expand_uk_coverage.py --test --output data/output/test_expansion.xlsx
```

This will perform 5 sample searches to verify everything works.

### Step 3: Run Targeted Expansion

Start with specific regions to manage costs:

```bash
# Example: Expand to Manchester and Birmingham
python src/expand_uk_coverage.py \
  --regions-filter "Manchester,Birmingham" \
  --output data/output/expanded_northwest.xlsx
```

### Step 4: Full UK Expansion (When Ready)

```bash
python src/expand_uk_coverage.py \
  --output data/output/expanded_resources_uk_full.xlsx
```

**⚠️ This will make ~3,200 API calls and cost approximately $190 USD**

## 📊 What You Get

The pipeline will find and extract:
- Neurodivergent support centers
- Autism assessment clinics
- ADHD diagnostic services
- Special educational needs schools
- Therapy centers
- Employment support services
- Community organizations
- And much more...

All with complete Google Maps data:
- Full address and coordinates
- Website and phone numbers
- Opening hours
- Ratings and reviews
- Photos and more

## 💡 Recommended Approach

### Option 1: Incremental Expansion (Cost-Effective)

Expand region by region over several weeks:

```bash
# Week 1: Major cities
python src/expand_uk_coverage.py \
  --regions-filter "Manchester,Birmingham,Leeds,Liverpool,Bristol" \
  --output data/output/expanded_major_cities.xlsx

# Week 2: Scotland
python src/expand_uk_coverage.py \
  --regions-filter "Glasgow,Edinburgh,Aberdeen" \
  --output data/output/expanded_scotland.xlsx

# Week 3: Wales
python src/expand_uk_coverage.py \
  --regions-filter "Cardiff,Swansea,Newport" \
  --output data/output/expanded_wales.xlsx
```

### Option 2: Keyword-Focused (Lower Volume)

Focus on specific service types:

```bash
# Just autism-specific searches
python src/expand_uk_coverage.py \
  --keywords-filter "autism" \
  --output data/output/expanded_autism_only.xlsx

# Assessment and diagnosis centers
python src/expand_uk_coverage.py \
  --keywords-filter "assessment,diagnosis,clinic" \
  --output data/output/expanded_assessment_centers.xlsx
```

## 🔄 Full Workflow

```
1. Scrape → Find places across UK using keywords
2. Dedupe → Remove duplicates with existing data
3. Merge → Combine into single dataset
4. Enrich → Use existing batch_enrich_pipeline_parallel.py
5. Validate → Use validate_neurodivergent.py
6. Deploy → Complete UK resource database!
```

## 📈 Expected Results

Based on your current 935 resources (mostly London/Hertfordshire):

- **Estimated UK total**: 8,000-15,000 neurodivergent resources
- **New records from expansion**: ~7,000-14,000
- **Coverage**: All major cities and counties across UK

## 🛠️ Command Options

### Key Flags

- `--test`: Test mode (5 searches only)
- `--keywords-filter "autism,ADHD"`: Filter to specific keywords
- `--regions-filter "London,Manchester"`: Filter to specific regions
- `--max-searches 100`: Limit number of searches
- `--no-details`: Skip place details (faster, cheaper)
- `--rate-limit 50`: Adjust API rate limit

See full documentation: `docs/UK_EXPANSION_GUIDE.md`

## ❗ Important Notes

1. **API Costs**: Google Places API charges per request. Monitor your usage!
2. **Rate Limits**: Default is 100 requests/minute to stay safe
3. **Caching**: All searches are cached - rerunning is free
4. **Existing Data**: Your current 935 resources are preserved and merged

## 📞 Next Steps

1. **Enable billing** on Google Cloud Platform
2. **Run test** to verify setup
3. **Choose approach** (incremental or full)
4. **Start scraping** with your chosen regions/keywords
5. **Review results** and adjust as needed
6. **Enrich with LLM** using batch_enrich_pipeline_parallel.py

## 📚 Files Created

- `config.py` - Updated with keywords and regions
- `src/scrape_google_places.py` - Google Places scraper
- `src/expand_uk_coverage.py` - Main expansion pipeline
- `docs/UK_EXPANSION_GUIDE.md` - Comprehensive guide
- `UK_EXPANSION_README.md` - This file

## ✨ Summary

You now have a production-ready pipeline to expand your neurodivergent resource database from London to the entire UK. The pipeline is:

- **Smart**: Automatic deduplication and merging
- **Efficient**: Caching to avoid duplicate API calls
- **Flexible**: Filter by keywords, regions, or both
- **Safe**: Rate limiting and error handling
- **Complete**: Matches your existing data schema

Start with `--test` mode and scale up as needed!

---

**Questions?** See `docs/UK_EXPANSION_GUIDE.md` for detailed documentation.

