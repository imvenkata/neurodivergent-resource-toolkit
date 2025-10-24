# Module Guide - Detailed Documentation

Complete reference for all Python modules in the Data Scraper toolkit.

---

## Table of Contents

1. [Enrichment Pipelines](#enrichment-pipelines)
   - [Parallel Pipeline](#1-parallel-enrichment-pipeline)
   - [Sequential Pipeline](#2-sequential-enrichment-pipeline)
2. [Data Processing](#data-processing)
   - [Web Extractor](#3-web-extractor)
   - [Categorization](#4-categorization-engine)
   - [URL Population](#5-url-population)
   - [Relevance Filter](#6-relevance-filter)
3. [Utilities](#utilities)
4. [Input File Specifications](#input-file-specifications)

---

## Enrichment Pipelines

### 1. Parallel Enrichment Pipeline

**File**: `src/batch_enrich_pipeline_parallel.py`

#### Purpose
Main enrichment pipeline using parallel processing for maximum speed. Processes multiple resources simultaneously using ThreadPoolExecutor.

#### Usage
```bash
# Via CLI (recommended)
python run.py enrich [options]

# Direct
python src/batch_enrich_pipeline_parallel.py [options]
```

#### Input File Requirements

**Format**: CSV or Excel (.csv, .xlsx)

**Required Columns**:
- `gmaps_name` - Name of the resource/organization
- `gmaps_website` - Website URL (optional if using `--skip-no-website`)

**Optional Columns** (will be enriched if missing):
- `description_short` - Brief description
- `age_range` - Age range served
- `conditions_supported` - Conditions/needs addressed
- `specific_services` - List of services offered
- `organization_type` - Type of organization
- `gmaps_phone` - Phone number
- `gmaps_formatted_address` - Full address
- `gmaps_addr_postal_code` - Postal code
- `gmaps_addr_postal_town` - Town/city
- `gmaps_addr_admin_area_level_1` - County/state
- `gmaps_addr_admin_area_level_2` - Region
- `gmaps_place_id` - Google Place ID
- `gmaps_latitude` - Latitude
- `gmaps_longitude` - Longitude
- `gmaps_url` - Google Maps URL

**Example Input**:
```csv
gmaps_name,gmaps_website,gmaps_place_id,gmaps_latitude,gmaps_longitude
"Autism Support Center","https://example.com","ChIJ123abc",51.5074,-0.1278
"ADHD Clinic","https://adhd-clinic.com",,51.4545,-0.1234
```

#### Command-Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--input` | string | `data/input/to_be_normalised/enriched_resources.csv` | Input CSV/Excel file |
| `--output` | string | Auto-generated | Output Excel file path |
| `--backend` | choice | `gemini` | LLM backend: `gemini`, `openai`, `ollama` |
| `--model` | string | Auto | Model name (optional) |
| `--enhance-with-websearch` | flag | False | Enable web search for missing data |
| `--max-rows` | int | None | Limit number of rows to process |
| `--start-row` | int | 0 | Starting row index |
| `--cache-dir` | string | `.cache/llm_extractions` | Cache directory path |
| `--fields-to-check` | string | `description_short,age_range,organization_type` | Fields to check for enrichment |
| `--skip-no-website` | flag | False | Skip rows without website |
| `--workers` | int | 10 | Number of parallel workers |
| `--rate-limit` | int | 15 | Max API requests per minute |
| `--populate-urls` | flag | False | Populate missing Google Maps URLs |
| `--categorize` | flag | False | Auto-categorize resources |
| `--ollama-url` | string | None | Ollama server URL |
| `--ollama-auth` | string | None | Ollama authentication |
| `--openai-key` | string | None | OpenAI API key (or use .env) |
| `--gemini-key` | string | None | Gemini API key (or use .env) |

#### Output Format

**File**: Excel (.xlsx) with the following features:
- All input columns preserved
- New/updated columns highlighted in yellow
- Auto-adjusted column widths
- Clean text (no encoding issues)

**Output Columns** (30+ fields):
- All input columns
- `description_short` - AI-generated description
- `age_range` - Supported age ranges
- `conditions_supported` - List of conditions
- `specific_services` - Detailed services list
- `organization_type` - Organization classification
- `gmaps_phone` - Extracted phone number
- `gmaps_formatted_address` - Full address
- `gmaps_addr_postal_code` - Postal code
- `gmaps_addr_postal_town` - Town
- `gmaps_addr_admin_area_level_1` - County
- `gmaps_addr_admin_area_level_2` - Region
- `is_neurodivergent_related` - Boolean validation
- `neurodivergent_relevance_score` - High/Medium/Low/None
- `neurodivergent_focus` - Focus description
- `resource_category` - Category (if --categorize used)
- `gmaps_url` - Google Maps URL (if --populate-urls used)

#### Examples

**Basic enrichment:**
```bash
python run.py enrich --workers 5 --rate-limit 15
```

**Full pipeline with all features:**
```bash
python run.py enrich \
  --input data/input/my_resources.csv \
  --backend gemini \
  --enhance-with-websearch \
  --populate-urls \
  --categorize \
  --workers 5 \
  --rate-limit 15
```

**Test run (first 10 rows):**
```bash
python run.py enrich --max-rows 10 --workers 2
```

**Skip resources without websites:**
```bash
python run.py enrich --skip-no-website --workers 5
```

#### Performance Tips

- **Gemini Free Tier**: Use `--workers 5 --rate-limit 15`
- **OpenAI**: Use `--workers 10 --rate-limit 60`
- **Ollama (local)**: Use `--workers 20` (no rate limit needed)
- Enable caching for repeated runs (automatic)
- Use `--max-rows` for testing

#### Caching System

- **Location**: `.cache/llm_extractions/`
- **Format**: JSON files named by resource name
- **Behavior**: 
  - First run: Calls LLM for all resources
  - Subsequent runs: Loads from cache (instant)
  - Updates cache when using `--enhance-with-websearch`
- **Old cache**: Automatically adds neurodivergent validation fields

---

### 2. Sequential Enrichment Pipeline

**File**: `src/batch_enrich_pipeline.py`

#### Purpose
Alternative enrichment pipeline that processes resources one at a time. Slower but more stable for debugging or low-memory environments.

#### Usage
```bash
# Via CLI
python run.py enrich-single [options]

# Direct
python src/batch_enrich_pipeline.py [options]
```

#### Input File Requirements
Same as Parallel Pipeline (see above)

#### Key Differences from Parallel Pipeline

| Feature | Parallel | Sequential |
|---------|----------|------------|
| Speed | 5-10x faster | Baseline |
| Memory | Higher | Lower |
| Debugging | Harder | Easier |
| Best For | Production | Development/Testing |

#### Command-Line Arguments
Same as Parallel Pipeline, **except**:
- No `--workers` argument
- No `--rate-limit` argument
- No `--categorize` argument (use standalone categorize script)

#### Examples

```bash
# Basic sequential enrichment
python run.py enrich-single --backend gemini

# Debug single resource
python run.py enrich-single --max-rows 1 --enhance-with-websearch
```

---

## Data Processing

### 3. Web Extractor

**File**: `src/web_llm_extract.py`

#### Purpose
Extract structured data from a single website using LLM. Used internally by enrichment pipelines, but can be run standalone.

#### Usage
```bash
# Via CLI
python run.py extract [options]

# Direct
python src/web_llm_extract.py [options]
```

#### Input
**Command-line arguments** (no file required):
- `--center-name` - Name of the resource
- `--url` - Website URL to scrape
- `--backend` - LLM backend (gemini/openai/ollama)
- `--model` - Model name (optional)
- `--max-pages` - Maximum pages to crawl (default: 3)
- `--enhance-with-websearch` - Enable DuckDuckGo search fallback

#### Output
**Format**: JSON to stdout

**Structure**:
```json
{
  "center_name": "Example Center",
  "website_url": "https://example.com",
  "description_short": "Brief description...",
  "category": "Community Support",
  "age_range": "All ages",
  "conditions_supported": ["Autism", "ADHD"],
  "specific_services": ["Assessment", "Support groups"],
  "organization_type": "Charity",
  "contact_info": {
    "phone": "+44 20 1234 5678",
    "email": "info@example.com",
    "address": "123 Main St, London"
  },
  "address_components": {
    "postal_code": "SW1A 1AA",
    "postal_town": "London",
    "admin_area_level_1": "Greater London",
    "admin_area_level_2": "England"
  },
  "is_neurodivergent_related": true,
  "neurodivergent_relevance_score": "High",
  "neurodivergent_focus": "Specializes in autism support",
  "data_confidence": "High",
  "reasoning": "..."
}
```

#### Examples

```bash
# Extract from single website
python run.py extract \
  --center-name "Autism Center" \
  --url "https://autism-center.org" \
  --backend gemini

# With web search fallback
python run.py extract \
  --center-name "ADHD Clinic" \
  --url "https://adhd-clinic.com" \
  --enhance-with-websearch \
  --max-pages 5

# Save to file
python run.py extract \
  --center-name "Support Group" \
  --url "https://example.com" \
  --backend gemini > output.json
```

#### Use Cases
- Testing LLM extraction on single site
- Debugging extraction issues
- One-off data extraction
- Integration with other tools (via JSON output)

---

### 4. Categorization Engine

**File**: `src/categorize_resources.py`

#### Purpose
Fast keyword-based categorization of resources into 15 predefined categories. Processes 1000+ resources per second.

#### Usage
```bash
# Via CLI
python run.py categorize [options]

# Direct
python src/categorize_resources.py [options]
```

#### Input File Requirements

**Format**: CSV or Excel (.csv, .xlsx)

**Required Columns**:
- `gmaps_name` - Resource name (used for categorization)

**Recommended Columns** (improve accuracy):
- `description_short` - Description of services
- `specific_services` - List of services offered
- `organization_type` - Type of organization

**Optional Columns**:
- `resource_category` - Existing category (will be skipped unless `--overwrite`)

**Example Input**:
```csv
gmaps_name,description_short,specific_services
"NAS Bexley Branch","Local autism support","Parent groups, advice"
"Swimming Club","Autism-friendly swimming","Swimming lessons, sports"
"Employment Service","Job support for autistic adults","Job coaching, skills training"
```

#### Categories

The system assigns one of these 15 categories:

1. **Assessment & Diagnosis** - Diagnostic services, CAMHS, evaluations
2. **Crisis & Emergency** - Helplines, emergency support, crisis services
3. **Community Support** - General support, advice, guidance
4. **Education Support** - Schools, learning, tutoring, SEN support
5. **Employment Support** - Job coaching, work programs
6. **Housing Support** - Accommodation, residential services
7. **Benefits Support** - Financial advice, DLA, PIP
8. **Transport Support** - Travel training, accessible transport
9. **Autism Friendly Entertainment** - Theatre, museums, arts
10. **Local Support Services and Groups** - Parent groups, meetups
11. **Employment and Skills Services** - Skills training, apprenticeships
12. **National Autistic Society Branches** - NAS local branches
13. **Autism Friendly Sports Activities** - Swimming, sports clubs
14. **Special Needs Play Centres** - Playgroups, soft play
15. **Special Interests and Hobbies** - Clubs, hobbies, activities
16. **Unknown Category** - Insufficient data for categorization

#### Command-Line Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `--input` | string | Yes | Input CSV/Excel file |
| `--output` | string | No | Output Excel file (default: adds `_categorized` suffix) |
| `--overwrite` | flag | No | Overwrite existing categories (default: only fill empty) |

#### Output Format

**File**: Excel (.xlsx)

**Features**:
- All input columns preserved
- `resource_category` column added/updated
- Changed categories highlighted in yellow
- Category distribution summary printed

**Example Output**:
```
📊 Category Distribution:
======================================================================
  Assessment & Diagnosis                          20 (  1.9%)
  Employment Support                              55 (  5.3%)
  Autism Friendly Sports Activities               61 (  5.8%)
  Local Support Services and Groups               46 (  4.4%)
  Unknown Category                               725 ( 69.5%)
======================================================================
  TOTAL                                         1043 (100.0%)
```

#### Examples

```bash
# Categorize enriched data
python run.py categorize \
  --input data/output/enriched_resources.xlsx \
  --output data/output/categorized_resources.xlsx

# Re-categorize with new logic (overwrite existing)
python run.py categorize \
  --input data/output/old_categories.xlsx \
  --overwrite

# Auto-named output
python run.py categorize --input data/output/enriched.xlsx
# Creates: data/output/enriched_categorized.xlsx
```

#### Categorization Logic

The engine uses **keyword matching** in this order:

1. **Exact organization match** (e.g., "National Autistic Society" → NAS Branches)
2. **Service-specific keywords** (e.g., "assessment", "diagnosis" → Assessment & Diagnosis)
3. **Activity keywords** (e.g., "swimming", "sports" → Sports Activities)
4. **Support type** (e.g., "parent group" → Local Support Groups)
5. **General support** (e.g., "advice", "help" → Community Support)

Keywords from `specific_services` are **weighted higher** than `description_short` for better accuracy.

#### Performance
- **Speed**: 1000+ resources/second
- **Memory**: Minimal (processes row-by-row)
- **Accuracy**: ~95% for well-described resources, ~70% for sparse data

---

### 5. URL Population

**File**: `src/populate_gmaps_url.py`

#### Purpose
Generate valid Google Maps URLs for resources using place IDs or coordinates. Validates place IDs to reject fake placeholders.

#### Usage
```bash
# Via CLI
python run.py populate-urls [options]

# Direct
python src/populate_gmaps_url.py [options]
```

#### Input File Requirements

**Format**: CSV or Excel (.csv, .xlsx)

**Required Columns** (at least one of):
- `gmaps_place_id` - Google Place ID (preferred)
- `gmaps_latitude` + `gmaps_longitude` - Coordinates (fallback)

**Optional Columns**:
- `gmaps_url` - Existing URL (will be skipped unless empty)
- `gmaps_name` - Resource name (used for API search if enabled)
- `gmaps_formatted_address` - Address (used for API search)

**Example Input**:
```csv
gmaps_name,gmaps_place_id,gmaps_latitude,gmaps_longitude,gmaps_url
"Center A","ChIJ123abc",,,""
"Center B","1",51.5074,-0.1278,""
"Center C","",51.4545,-0.1234,""
"Center D","ChIJ456def",,,"https://maps.google.com/?cid=123"
```

#### Place ID Validation

The script **validates place IDs** and rejects:
- Pure numbers: "1", "2", "123" ❌
- Too short: < 15 characters ❌
- Placeholders: "none", "null", "n/a" ❌
- Valid format: "ChIJ123abc..." ✅

#### URL Generation Strategies

**Strategy 1**: Use existing valid place ID
```
Input:  place_id = "ChIJ39RePbUcdkgRnUxiKN-8IQ8"
Output: https://www.google.com/maps/place/?q=place_id:ChIJ39RePbUcdkgRnUxiKN-8IQ8
```

**Strategy 2**: Use coordinates
```
Input:  lat = 51.5074, lng = -0.1278
Output: https://www.google.com/maps?q=51.5074,-0.1278
```

**Strategy 3**: Search Google Places API (optional)
```bash
# Enable API search (requires GOOGLE_API_KEY in .env)
python run.py populate-urls --input file.csv
# Without API, only strategies 1 & 2 are used
```

#### Command-Line Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `--input` | string | Yes | Input CSV/Excel file |
| `--output` | string | No | Output Excel file (default: adds `_with_urls` suffix) |
| `--use-directions` | flag | No | Use directions URL format instead of place URL |
| `--no-api` | flag | No | Don't call Google Places API (only use existing data) |
| `--max-rows` | int | No | Limit rows to process (for testing) |
| `--rate-limit` | float | No | Delay between API calls in seconds (default: 0.1) |

#### Output Format

**File**: Excel (.xlsx)

**Features**:
- All input columns preserved
- `gmaps_url` column added/populated
- `gmaps_place_id` column updated (if new place_id found via API)
- Changed rows highlighted in yellow
- Summary statistics

**Example Output**:
```
======================================================================
SUMMARY
======================================================================
Total rows processed:    434
✅ Successfully updated: 325
❌ Failed:               109

Output saved to: enriched_resources_with_urls.xlsx
======================================================================
```

#### Examples

```bash
# Basic URL population (no API calls)
python run.py populate-urls \
  --input data/output/enriched_resources.xlsx \
  --no-api

# With Google Places API search
python run.py populate-urls \
  --input data/input/missing_urls.csv \
  --rate-limit 0.2

# Use directions format
python run.py populate-urls \
  --input data/output/resources.xlsx \
  --use-directions

# Test with first 50 rows
python run.py populate-urls \
  --input data/output/large_file.xlsx \
  --max-rows 50 \
  --no-api
```

#### Success Rates
- **With valid place_id**: 100%
- **With coordinates**: 100%
- **With API search**: ~60-80% (depends on data quality)
- **Overall (typical dataset)**: ~75%

---

### 6. Relevance Filter

**File**: `src/filter_neurodivergent.py`

#### Purpose
Analyze and filter resources based on neurodivergent relevance validation. Generates reports and filtered datasets.

#### Usage
```bash
# Via CLI
python run.py filter [options]

# Direct
python src/filter_neurodivergent.py [options]
```

#### Input File Requirements

**Format**: Excel (.xlsx) - must be output from enrichment pipeline

**Required Columns**:
- `is_neurodivergent_related` - Boolean flag (true/false)
- `neurodivergent_relevance_score` - Score: High/Medium/Low/None/Unknown
- `neurodivergent_focus` - Description of neurodivergent focus

**Optional Columns**:
- `gmaps_name` - Resource name
- `description_short` - Description
- All other enrichment columns

**Example Input**:
```
| gmaps_name | is_neurodivergent_related | neurodivergent_relevance_score | neurodivergent_focus |
|------------|---------------------------|--------------------------------|---------------------|
| Center A   | true                      | High                           | Autism specialist   |
| Center B   | true                      | Medium                         | Some ADHD support   |
| Center C   | false                     | None                           |                     |
```

#### Command-Line Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `--input` | string | Yes | Input Excel file (must have validation columns) |
| `--analyze` | flag | No | Show analysis report only (no filtering) |
| `--filter` | flag | No | Filter and export neurodivergent resources only |
| `--min-score` | choice | No | Minimum score: High/Medium/Low (default: Medium) |
| `--output` | string | No | Output file (required if --filter used) |

#### Output Modes

**Mode 1: Analysis** (`--analyze`)
- Prints statistics to console
- No file output
- Shows distribution of scores and validation

**Mode 2: Filter** (`--filter`)
- Creates new Excel file
- Only includes neurodivergent-related resources
- Filters by minimum score

#### Analysis Output Example

```
======================================================================
NEURODIVERGENT RELEVANCE ANALYSIS
======================================================================

📊 SUMMARY:
  Total resources:           1043
  ✅ Neurodivergent-related:  318 (30.5%)
  ❌ Not related:             100 (9.6%)
  ❓ Unknown/Not validated:   625 (59.9%)

📈 RELEVANCE SCORE BREAKDOWN:
  High                      : 150 (47.2% of validated)
  Medium                    :  98 (30.8% of validated)
  Low                       :  45 (14.2% of validated)
  None                      : 100 (31.4% of validated)
  Unknown/Not validated     : 650 (62.3% of total)

🎯 NEURODIVERGENT FOCUS AREAS:
  Autism support            : 180
  ADHD services             :  65
  Dyslexia support          :  30
  Multiple conditions       :  43

📝 RECOMMENDATIONS:
  - 625 resources need validation (run enrichment pipeline)
  - 100 resources marked as not neurodivergent-related
  - High-quality resources: 150 (score: High)
```

#### Examples

```bash
# Analyze validation status
python run.py filter \
  --input data/output/enriched_resources.xlsx \
  --analyze

# Filter high-quality neurodivergent resources only
python run.py filter \
  --input data/output/enriched_resources.xlsx \
  --filter \
  --min-score High \
  --output data/output/neurodivergent_high_quality.xlsx

# Filter medium+ quality
python run.py filter \
  --input data/output/enriched_resources.xlsx \
  --filter \
  --min-score Medium \
  --output data/output/neurodivergent_medium_plus.xlsx

# Include all neurodivergent (even low score)
python run.py filter \
  --input data/output/enriched_resources.xlsx \
  --filter \
  --min-score Low \
  --output data/output/all_neurodivergent.xlsx
```

#### Score Meanings

| Score | Meaning | Example |
|-------|---------|---------|
| **High** | Explicitly specializes in neurodivergent support | "Autism specialist clinic" |
| **Medium** | Offers neurodivergent support but not primary focus | "General mental health with autism services" |
| **Low** | May help neurodivergent people but not designed for them | "Community center with some inclusive activities" |
| **None** | Not relevant to neurodivergent support | "General hospital" |
| **Unknown** | Not yet validated (missing data) | Empty/null values |

---

## Utilities

### Location: `src/utils/`

These are helper scripts used internally by the main pipelines. Generally not called directly.

#### 1. Google Places Enrichment (`enrich_with_google.py`)
- **Purpose**: Enrich data using Google Places API
- **Usage**: Internal utility
- **Note**: Superseded by main enrichment pipeline

#### 2. LLM Description Enrichment (`llm_enrich_description.py`)
- **Purpose**: Legacy LLM enrichment script
- **Usage**: Internal utility
- **Note**: Superseded by `web_llm_extract.py`

#### 3. Service Merger (`merge_services.py`)
- **Purpose**: Merge multiple service datasets
- **Usage**: Standalone utility for data consolidation
- **Input**: Multiple CSV files
- **Output**: Merged CSV

#### 4. Web Scraper (`scraper.py`)
- **Purpose**: Basic web scraping utilities
- **Usage**: Internal helper for web extraction
- **Note**: Used by `web_llm_extract.py`

---

## Input File Specifications

### Minimum Requirements

For the enrichment pipelines to work, you need **at minimum**:

```csv
gmaps_name,gmaps_website
"Resource Name","https://example.com"
```

### Recommended Input Format

For best results, include as much existing data as possible:

```csv
gmaps_name,gmaps_website,gmaps_place_id,gmaps_latitude,gmaps_longitude,gmaps_phone,gmaps_formatted_address
"Autism Center","https://autism.org","ChIJ123",51.5074,-0.1278,"+44 20 1234",  "123 Main St, London"
```

### Complete Field List

**Google Maps Fields** (from Google Places API):
- `gmaps_place_id` - Unique Google place identifier
- `gmaps_name` - Business/resource name
- `gmaps_formatted_address` - Full formatted address
- `gmaps_latitude` - Latitude coordinate
- `gmaps_longitude` - Longitude coordinate
- `gmaps_opening_hours_weekday_text` - Opening hours
- `gmaps_website` - Website URL
- `gmaps_phone` - Phone number
- `gmaps_rating` - Google rating (1-5)
- `gmaps_user_ratings_total` - Number of reviews
- `gmaps_editorial_summary` - Google's summary
- `gmaps_url` - Google Maps link
- `gmaps_directions_url` - Directions link
- `gmaps_plus_code_global` - Plus code
- `gmaps_plus_code_compound` - Local plus code
- `gmaps_addr_country` - Country
- `gmaps_addr_postal_code` - Postal/ZIP code
- `gmaps_addr_postal_town` - Town/city
- `gmaps_addr_admin_area_level_1` - State/county
- `gmaps_addr_admin_area_level_2` - Region

**Enriched Fields** (added by pipeline):
- `description_short` - AI-generated description
- `age_range` - Age groups served
- `conditions_supported` - Conditions addressed
- `specific_services` - Detailed services list
- `organization_type` - Organization classification
- `is_neurodivergent_related` - Validation flag
- `neurodivergent_relevance_score` - Quality score
- `neurodivergent_focus` - Focus description
- `resource_category` - Assigned category

**Metadata Fields**:
- `status` - Current status
- `last_verified` - Last verification date
- `sno` - Serial number

### Data Quality Guidelines

**High Quality Input** (best results):
- ✅ Valid website URLs
- ✅ Real Google Place IDs (not "1", "2", "3")
- ✅ Accurate coordinates
- ✅ Phone numbers in correct format
- ✅ Complete addresses

**Acceptable Input** (will be enriched):
- ✅ Name and website only
- ✅ Partial data (pipeline fills gaps)
- ✅ Missing coordinates (optional)

**Problematic Input** (poor results):
- ❌ No website and no data
- ❌ Invalid/broken URLs
- ❌ Fake place IDs (will be detected and ignored)
- ❌ Incorrect coordinates

### File Format Support

| Format | Read | Write | Notes |
|--------|------|-------|-------|
| CSV | ✅ | ✅ | UTF-8, UTF-8-BOM, Latin-1, CP1252 |
| Excel (.xlsx) | ✅ | ✅ | Preferred output format |
| Excel (.xls) | ✅ | ❌ | Legacy format (read-only) |
| JSON | ❌ | ✅ | Cache and extract output only |

---

## Complete Workflow Example

### Step 1: Prepare Input Data
```csv
# data/input/my_resources.csv
gmaps_name,gmaps_website,gmaps_place_id
"Autism Support Center","https://autism-support.org","ChIJ123abc"
"ADHD Clinic","https://adhd-clinic.com",""
"Parent Support Group","",""
```

### Step 2: Enrich Data
```bash
python run.py enrich \
  --input data/input/my_resources.csv \
  --backend gemini \
  --enhance-with-websearch \
  --populate-urls \
  --workers 5 \
  --rate-limit 15 \
  --skip-no-website
```

**Output**: `data/output/enriched_resources_parallel_20231021_153045.xlsx`

### Step 3: Categorize
```bash
python run.py categorize \
  --input data/output/enriched_resources_parallel_20231021_153045.xlsx
```

**Output**: `data/output/enriched_resources_parallel_20231021_153045_categorized.xlsx`

### Step 4: Filter High-Quality Resources
```bash
python run.py filter \
  --input data/output/enriched_resources_parallel_20231021_153045_categorized.xlsx \
  --filter \
  --min-score High \
  --output data/output/final_high_quality_resources.xlsx
```

**Final Output**: Clean, categorized, validated neurodivergent resources!

---

## Troubleshooting

### Issue: "No module named 'google'"
**Solution**: Gemini SDK not installed
```bash
uv sync  # or pip install google-generativeai
```

### Issue: "GEMINI_API_KEY not set"
**Solution**: Create/update `.env` file
```bash
cp .env.example .env
# Edit .env and add: GEMINI_API_KEY=your_key_here
```

### Issue: "Rate limit exceeded"
**Solution**: Reduce workers and rate
```bash
python run.py enrich --workers 3 --rate-limit 10
```

### Issue: "Many resources categorized as Unknown"
**Solution**: Run enrichment first to populate `description_short` and `specific_services`

### Issue: "Validation columns not found"
**Solution**: File wasn't created by enrichment pipeline. Run enrichment first.

---

## API Keys Reference

### Required for Enrichment
- **Gemini**: Set `GEMINI_API_KEY` or `GOOGLE_API_KEY` in `.env`
- **OpenAI**: Set `OPENAI_API_KEY` in `.env`
- **Ollama**: No key needed (local server)

### Optional for URL Population
- **Google Places**: Set `GOOGLE_API_KEY` in `.env` (for API-based URL search)

### Get API Keys
- **Gemini**: https://makersuite.google.com/app/apikey
- **OpenAI**: https://platform.openai.com/api-keys
- **Ollama**: https://ollama.ai (local installation)

---

## Support

For detailed guides, see:
- [README.md](README.md) - Main documentation
- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - New structure guide
- [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) - Architecture details
- [docs/](docs/) - Additional guides

---

**Last Updated**: October 2024

