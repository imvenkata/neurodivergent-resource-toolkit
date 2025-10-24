# Data Scraper

Tools for scraping and enriching neurodivergent service center information.

## Table of Contents

1. [web_llm_extract.py](#web_llm_extractpy) - Single service center extraction
2. [batch_enrich_pipeline.py](#batch_enrich_pipelinepy) - Batch processing pipeline

---

## web_llm_extract.py

Extract structured information from service center websites using LLMs.

### Features

- **Website Crawling**: Automatically crawls multiple pages from a website
- **LLM Extraction**: Uses Ollama, OpenAI, or Gemini to extract structured data
- **Smart Categorization**: Categorizes services into 9 predefined categories
- **Web Search Enhancement**: Optionally searches the web for missing contact information from reliable sources

### Usage

Basic usage:
```bash
python web_llm_extract.py \
  --center-name "Example Center" \
  --url "https://example.com" \
  --backend gemini
```

With web search enhancement:
```bash
python web_llm_extract.py \
  --center-name "Example Center" \
  --url "https://example.com" \
  --backend gemini \
  --enhance-with-websearch
```

### Arguments

- `--center-name`: Name of the service center (required)
- `--url`: Website URL to analyze (required)
- `--backend`: LLM backend to use: `ollama`, `openai`, or `gemini` (default: ollama)
- `--model`: Model name (optional, uses sensible defaults)
- `--max-pages`: Maximum pages to crawl (default: 6)
- `--enhance-with-websearch`: Enable web search for missing contact info
- `--out`: Output JSON file path (optional)

### Backend-Specific Arguments

**Ollama:**
- `--ollama-url`: Ollama server URL (default: http://localhost:11434)
- `--ollama-auth`: Authentication header or token

**OpenAI:**
- `--openai-key`: API key (or set OPENAI_API_KEY env var)

**Gemini:**
- `--gemini-key`: API key (or set GEMINI_API_KEY or GOOGLE_API_KEY env var)

### Web Search Enhancement

When `--enhance-with-websearch` is enabled:
- Searches for missing phone, email, and address information
- Only searches reliable sources: NHS, gov.uk, charity websites, Google Maps, etc.
- Adds `_metadata` field to track enhanced fields and sources
- Outputs progress to stderr

Example output with enhancement:
```json
{
  "center_name": "Example Center",
  "website_url": "https://example.com",
  "description_short": "A specialist center providing ADHD assessments and support.",
  "category": "Assessment & Diagnosis",
  "subcategory": "Diagnostic Centers",
  "age_range": "Adults (18+)",
  "conditions_supported": ["ADHD", "Autism/ASC"],
  "specific_services": ["ADHD Assessment", "Medication Management", "Ongoing care"],
  "organization_type": "NHS Service",
  "contact_info": {
    "phone": "020 1234 5678",
    "email": "info@example.com",
    "address": "123 Main St, London, SW1A 1AA"
  },
  "address_components": {
    "postal_code": "SW1A 1AA",
    "postal_town": "London",
    "admin_area_level_1": "England",
    "admin_area_level_2": "Greater London"
  },
  "additional_notes": "NHS referral required",
  "data_confidence": "High",
  "reasoning": "Clear service description and explicit ADHD assessment focus",
  "_metadata": {
    "enhanced_fields": ["phone", "email", "address_components"],
    "enhancement_sources": [
      "https://www.nhs.uk/example",
      "https://www.google.com/maps/example"
    ],
    "enhancement_note": "Contact information enhanced via web search from reliable sources"
  }
}
```

### Categories

1. **Assessment & Diagnosis** - Diagnostic Centers, Assessment Clinics, Psychoeducational Evaluation
2. **Crisis & Emergency** - Crisis Helplines, Emergency Intervention, Mental Health Crisis Teams
3. **Education & Learning** - SEN Schools, Mainstream Resources, Training, Skills Development, Tutoring
4. **Employment** - Job Coaching, Workplace Accommodations, Vocational Training, Supported Employment
5. **Housing & Benefits** - Housing Assistance, Benefits Advice, Independent Living, Welfare Navigation
6. **Transport & Accessibility** - Accessible Transport, Travel Training, Mobility Services, Subsidies
7. **Community & Social** - Local Groups, Organization Branches, Peer Networks, Meetups, Parent/Carer Groups
8. **Recreation & Activities** - Sports & Fitness, Arts & Entertainment, Play Centers, Hobby Clubs
9. **Unknown/Uncategorized** - Only when no other category fits

### Output Schema

```json
{
  "center_name": "string",
  "website_url": "string",
  "description_short": "string (1-2 sentences)",
  "category": "string (from categories above)",
  "subcategory": "string",
  "age_range": "string (e.g., 'Adults (18+)', 'Ages 4½ to 22', 'All ages')",
  "conditions_supported": ["array of strings (ADHD, Autism/ASC, Dyslexia, etc.)"],
  "specific_services": ["array of strings (specific services offered)"],
  "organization_type": "string (NHS Service, Charity/Non-profit, etc.)",
  "contact_info": {
    "phone": "string",
    "email": "string",
    "address": "string (full address)"
  },
  "address_components": {
    "postal_code": "string (e.g., 'E1 8DE')",
    "postal_town": "string (e.g., 'London')",
    "admin_area_level_1": "string (e.g., 'England')",
    "admin_area_level_2": "string (e.g., 'Greater London', 'Hertfordshire')"
  },
  "additional_notes": "string",
  "data_confidence": "string (High/Medium/Low)",
  "reasoning": "string"
}
```

### Address Components

The system automatically parses UK addresses into structured components:
- **postal_code**: UK postcode (e.g., "E1 8DE", "SG2 7AH")
- **postal_town**: City/town name (e.g., "London", "Stevenage", "Basildon")
- **admin_area_level_1**: Country/region (e.g., "England", "Scotland", "Wales")
- **admin_area_level_2**: County/area (e.g., "Greater London", "Hertfordshire", "Essex")

Address parsing happens automatically when:
1. The LLM provides a full address but no components
2. Web search enhancement finds an address

The parser supports major UK counties and cities.

### Environment Variables

- `OPENAI_API_KEY`: OpenAI API key
- `GEMINI_API_KEY` or `GOOGLE_API_KEY`: Gemini API key
- `OLLAMA_URL`: Ollama server URL

### Examples

Using Gemini with web enhancement:
```bash
export GEMINI_API_KEY="your-key-here"
python web_llm_extract.py \
  --center-name "London Autism Center" \
  --url "https://example-autism-center.org.uk" \
  --backend gemini \
  --enhance-with-websearch \
  --out results.json
```

Using local Ollama:
```bash
python web_llm_extract.py \
  --center-name "Local Support Group" \
  --url "https://localsupport.org" \
  --backend ollama \
  --model llama3.1:8b-instruct
```

### Notes

- Web search enhancement requires internet access
- Web search uses DuckDuckGo (no API key required)
- Only reliable sources are used for enhancement (NHS, gov.uk, charity sites, etc.)
- Enhancement is optional and fails gracefully if issues occur
- Phone number patterns are optimized for UK formats

---

## batch_enrich_pipeline.py

Batch processing pipeline to enrich multiple service centers from a CSV file.

### Features

- **Batch Processing**: Process hundreds or thousands of service centers automatically
- **Smart Detection**: Only processes rows with missing information
- **Caching**: Caches LLM results to avoid duplicate API calls
- **Resume Support**: Can resume from any row number
- **Excel Export**: Exports to XLSX with highlighted changes
- **Progress Tracking**: Real-time progress updates and statistics
- **Intelligent Merging**: Only fills in missing fields, preserves existing data

### Column Mapping

The pipeline automatically maps extracted data to CSV columns:

| Extracted Field | CSV Column |
|----------------|------------|
| center_name | gmaps_name |
| website_url | gmaps_website |
| description_short | description_short |
| age_range | age_range |
| conditions_supported | conditions_supported |
| specific_services | specific_services |
| organization_type | organization_type |
| contact_info.phone | gmaps_phone |
| contact_info.address | gmaps_formatted_address |
| address_components.postal_code | gmaps_addr_postal_code |
| address_components.postal_town | gmaps_addr_postal_town |
| address_components.admin_area_level_1 | gmaps_addr_admin_area_level_1 |
| address_components.admin_area_level_2 | gmaps_addr_admin_area_level_2 |

### Usage

Basic usage (process first 10 rows with missing data):
```bash
python batch_enrich_pipeline.py \
  --input to_be_normalised/enriched_resources.csv \
  --output enriched_output.xlsx \
  --backend gemini \
  --max-rows 10
```

Full pipeline with web search enhancement:
```bash
export GEMINI_API_KEY="your-key-here"

python batch_enrich_pipeline.py \
  --input to_be_normalised/enriched_resources.csv \
  --output enriched_resources_updated.xlsx \
  --backend gemini \
  --enhance-with-websearch \
  --skip-no-website \
  --delay 2.0
```

Resume processing from row 500:
```bash
python batch_enrich_pipeline.py \
  --input to_be_normalised/enriched_resources.csv \
  --start-row 500 \
  --backend gemini
```

Test on a small sample:
```bash
bash test_pipeline.sh
```

### Arguments

**Input/Output:**
- `--input`: Input CSV file path (default: `to_be_normalised/enriched_resources.csv`)
- `--output`: Output XLSX file path (default: auto-generated with timestamp)
- `--cache-dir`: Directory to cache LLM results (default: `.cache/llm_extractions`)

**Processing Control:**
- `--max-rows`: Maximum number of rows to process (for testing)
- `--start-row`: Row number to start from (0-indexed, for resuming)
- `--delay`: Delay between API calls in seconds (default: 1.0)
- `--skip-no-website`: Skip rows without a website URL

**Enrichment Control:**
- `--fields-to-check`: Comma-separated list of fields to check for missing data  
  (default: `description_short,age_range,organization_type`)
- `--enhance-with-websearch`: Enable web search for missing contact info

**LLM Backend:**
- `--backend`: Choose `ollama`, `openai`, or `gemini` (default: `gemini`)
- `--model`: Model name (optional, uses sensible defaults)

**Backend-Specific:**
- `--ollama-url`: Ollama server URL
- `--ollama-auth`: Ollama authentication
- `--openai-key`: OpenAI API key
- `--gemini-key`: Gemini API key

### How It Works

1. **Load CSV**: Reads the input CSV file with service center data
2. **Filter Rows**: Identifies rows with missing information in specified fields
3. **Extract Data**: Calls `web_llm_extract.py` for each service center
4. **Merge Data**: Intelligently merges extracted data, only filling empty fields
5. **Cache Results**: Caches LLM responses to avoid duplicate API calls
6. **Export**: Exports to Excel with changed cells highlighted in yellow
7. **Statistics**: Displays summary of processed, enriched, failed, and skipped rows

### Output Format

The pipeline generates an Excel file (.xlsx) with:
- **All original columns** preserved
- **Updated fields** highlighted in yellow
- **Auto-sized columns** for readability
- **Header row** with blue background

### Caching

The pipeline automatically caches LLM extraction results in `.cache/llm_extractions/`:
- Avoids duplicate API calls for the same service center
- Enables quick re-runs without re-processing
- Can be manually cleared by deleting the cache directory

### Error Handling

- Gracefully handles timeouts (180s per extraction)
- Continues processing on individual failures
- Provides detailed error messages
- Tracks failed rows in statistics

### Performance Tips

1. **Start Small**: Test with `--max-rows 5` first
2. **Use Caching**: Re-run uses cached results automatically
3. **Resume Support**: Use `--start-row` to resume after interruption
4. **Rate Limiting**: Adjust `--delay` to avoid API rate limits
5. **Skip Empties**: Use `--skip-no-website` to skip rows without URLs

### Example Output

```
Reading to_be_normalised/enriched_resources.csv...
Loaded 1925 rows
Found 847 rows that need enrichment

[1/847] Processing: East London NHS Foundation Trust
  Website: http://www.elft.nhs.uk/
  ✓ Using cached data
  ✓ Updated fields: description_short, age_range, organization_type

[2/847] Processing: C N W L Mental Health Clinic
  Website: http://www.cnwl.nhs.uk/
  ✓ Updated fields: description_short, specific_services

...

============================================================
SUMMARY
============================================================
Total rows in input:     1925
Rows needing enrichment: 847
Successfully processed:  820
Successfully enriched:   803
Failed:                  17
Skipped:                 10

Output saved to: enriched_resources_updated_20251012_143022.xlsx
Changed cells are highlighted in yellow
============================================================
```

### Best Practices

1. **Test First**: Always test with `--max-rows` before full run
2. **Monitor Progress**: Watch for patterns in failures
3. **Check Output**: Review highlighted changes in Excel
4. **Backup Original**: Keep a copy of your original CSV
5. **Use Appropriate Backend**: Gemini is fast and affordable for batch processing
6. **Enable Web Search**: Use `--enhance-with-websearch` for maximum data completeness

### Troubleshooting

**"No rows need enrichment"**
- Check `--fields-to-check` - adjust fields to check
- Verify your CSV has empty fields

**"Timeout after 180s"**
- Some websites are slow or blocked
- These rows will be marked as failed and you can continue

**"Module 'openpyxl' not found"**
```bash
pip install openpyxl
# or with uv
uv pip install openpyxl
```

**API rate limits**
- Increase `--delay` value
- Use caching to avoid re-processing
- Consider processing in smaller batches

### Requirements

- Python 3.12+
- openpyxl (for Excel export)
- Valid API key for chosen backend (Gemini, OpenAI, or Ollama)
- Internet connection for web scraping and API calls

