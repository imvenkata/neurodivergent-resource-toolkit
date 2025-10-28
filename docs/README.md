# Data Scraper - Neurodivergent Resource Enrichment Toolkit

A comprehensive toolkit for enriching, categorizing, and managing neurodivergent support resources using AI-powered data extraction and categorization.

## 🚀 Quick Start

```bash
# 1. Install dependencies
uv sync

# 2. Set up environment variables
cp .env.example .env
# Edit .env and add your API keys

# 3. Run the enrichment pipeline
python run.py enrich --workers 5 --rate-limit 15

# 4. Categorize the results
python run.py categorize --input data/output/enriched_resources_*.xlsx
```

## 📁 Project Structure

```
data_scraper/
├── src/                          # Source code
│   ├── batch_enrich_pipeline_parallel.py  # Main enrichment pipeline (FAST)
│   ├── web_llm_extract.py                 # Single website extractor
│   ├── populate_gmaps_url.py              # URL population
│   ├── filter_neurodivergent.py           # Relevance filtering
│   └── utils/                    # Utility scripts
│       ├── enrich_with_google.py
│       ├── llm_enrich_description.py
│       ├── merge_services.py
│       └── scraper.py
├── data/                         # Data files
│   ├── input/                    # Input data
│   │   └── to_be_normalised/     # Raw input files
│   ├── output/                   # Generated output files
│   └── archive/                  # Archived data
├── tests/                        # Test files
├── docs/                         # Documentation
├── config/                       # Configuration scripts
├── .cache/                       # LLM response cache
├── run.py                        # Main CLI entry point
└── pyproject.toml                # Project dependencies

```

## 🛠️ Available Commands

### 1. **Enrich Resources** (Recommended - Fast & Parallel)

#### **Complete Command with All Arguments:**
```bash
python run.py enrich \
  --input "data/input/enriched_resources.csv" \
  --output "data/output/enriched_resources_complete.xlsx" \
  --backend "gemini" \
  --model "gemini-1.5-flash" \
  --enhance-with-websearch \
  --max-rows 10 \
  --start-row 0 \
  --cache-dir ".cache/llm_extractions" \
  --fields-to-check "description_short,age_range,organization_type,specific_services" \
  --skip-no-website \
  --workers 10 \
  --rate-limit 15 \
  --populate-urls \
  --categorize \
  --ollama-url "http://localhost:11434" \
  --ollama-auth "Bearer your-token" \
  --openai-key "sk-your-openai-key" \
  --gemini-key "your-gemini-key"
```

#### **Common Use Cases:**

**Basic Enrichment (Default Settings):**
```bash
python run.py enrich --input data/input/resources.csv
```

**High-Performance Parallel Processing:**
```bash
python run.py enrich \
  --input data/input/resources.csv \
  --workers 20 \
  --rate-limit 30 \
  --categorize
```

**Testing with Limited Data:**
```bash
python run.py enrich \
  --input data/input/resources.csv \
  --max-rows 10 \
  --workers 2 \
  --backend gemini
```

**Full Pipeline with URL Population:**
```bash
python run.py enrich \
  --input data/input/resources.csv \
  --output data/output/enriched_complete.xlsx \
  --populate-urls \
  --categorize \
  --enhance-with-websearch \
  --workers 15
```

**Ollama Local Processing:**
```bash
python run.py enrich \
  --input data/input/resources.csv \
  --backend ollama \
  --model "llama3.1:8b-instruct" \
  --ollama-url "http://localhost:11434" \
  --workers 5
```

**OpenAI Processing:**
```bash
python run.py enrich \
  --input data/input/resources.csv \
  --backend openai \
  --model "gpt-4o-mini" \
  --openai-key "sk-your-key-here" \
  --workers 8
```

#### **All Available Arguments:**

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--input` | str | `data/input/to_be_normalised/enriched_resources.csv` | Input CSV file path |
| `--output` | str | `None` (auto-generated) | Output file path |
| `--backend` | choice | `gemini` | LLM backend: `ollama`, `openai`, `gemini` |
| `--model` | str | `None` | Specific model name |
| `--enhance-with-websearch` | flag | `False` | Enable web search enhancement |
| `--max-rows` | int | `None` | Maximum rows to process |
| `--start-row` | int | `0` | Starting row index |
| `--cache-dir` | str | `.cache/llm_extractions` | Cache directory |
| `--fields-to-check` | str | `description_short,age_range,organization_type` | Fields to check for enrichment |
| `--skip-no-website` | flag | `False` | Skip rows without websites |
| `--workers` | int | `10` | Number of parallel workers |
| `--rate-limit` | int | `15` | API requests per minute |
| `--populate-urls` | flag | `False` | Populate missing Google Maps URLs |
| `--categorize` | flag | `False` | Auto-categorize resources |
| `--ollama-url` | str | `None` | Ollama server URL |
| `--ollama-auth` | str | `None` | Ollama authentication |
| `--openai-key` | str | `None` | OpenAI API key |
| `--gemini-key` | str | `None` | Gemini API key |

**Features:**
- Parallel processing (5-10x faster)
- LLM-powered data extraction
- Web search enhancement
- Automatic URL population
- Built-in categorization
- Rate limiting for API compliance
- Intelligent caching

### 2. **Populate Missing URLs**

#### **Complete Command with All Arguments:**
```bash
python run.py populate-urls \
  --input "data/input/resources.csv" \
  --output "data/output/with_urls.xlsx" \
  --use-directions \
  --no-api \
  --max-rows 100 \
  --rate-limit 0.1
```

#### **Common Use Cases:**

**Basic URL Population:**
```bash
python run.py populate-urls --input data/input/resources.csv
```

**With API Calls:**
```bash
python run.py populate-urls \
  --input data/input/resources.csv \
  --output data/output/with_urls.xlsx
```

**No API (Construct URLs Only):**
```bash
python run.py populate-urls \
  --input data/input/resources.csv \
  --no-api
```

#### **All Available Arguments:**

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--input` | str | **Required** | Input Excel or CSV file |
| `--output` | str | `None` (auto-generated) | Output file (adds _with_urls suffix) |
| `--use-directions` | flag | `False` | Use directions URL format instead of place URL format |
| `--no-api` | flag | `False` | Don't call API, only construct URLs from existing data |
| `--max-rows` | int | `None` | Maximum rows to process (for testing) |
| `--rate-limit` | float | `0.1` | Delay between API calls in seconds |

### 3. **Filter by Neurodivergent Relevance**

#### **Complete Command with All Arguments:**
```bash
python run.py filter \
  --input "data/output/enriched_resources.xlsx" \
  --analyze \
  --filter \
  --output "data/output/neurodivergent_only.xlsx" \
  --min-score "High" \
  --show-non-nd \
  --include-unknown
```

#### **Common Use Cases:**

**Filter High-Quality Resources Only:**
```bash
python run.py filter \
  --input data/output/enriched_resources.xlsx \
  --filter \
  --min-score High \
  --output data/output/high_quality_resources.xlsx
```

**Analyze Relevance Distribution:**
```bash
python run.py filter \
  --input data/output/enriched_resources.xlsx \
  --analyze
```

**Show All Resources (Including Non-Neurodivergent):**
```bash
python run.py filter \
  --input data/output/enriched_resources.xlsx \
  --filter \
  --show-non-nd \
  --include-unknown
```

#### **All Available Arguments:**

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--input` | str | **Required** | Input Excel file |
| `--analyze` | flag | `False` | Analyze relevance distribution |
| `--filter` | flag | `False` | Filter neurodivergent-related only |
| `--output` | str | `None` | Output file for filtered results |
| `--min-score` | choice | `None` | Minimum relevance score: `High`, `Medium`, `Low` |
| `--show-non-nd` | flag | `False` | Show non-neurodivergent resources |
| `--include-unknown` | flag | `False` | Include resources with unknown validation |

### 4. **Extract from Single Website**

#### **Complete Command with All Arguments:**
```bash
python run.py extract \
  --center-name "Resource Name" \
  --url "https://example.com" \
  --backend "gemini" \
  --model "gemini-1.5-flash" \
  --max-pages 5 \
  --out "output.json" \
  --enhance-with-websearch \
  --ollama-url "http://localhost:11434" \
  --ollama-auth "Bearer your-token" \
  --openai-key "sk-your-openai-key" \
  --gemini-key "your-gemini-key"
```

#### **Common Use Cases:**

**Basic Extraction:**
```bash
python run.py extract \
  --center-name "Autism Support Center" \
  --url "https://example.com" \
  --backend gemini
```

**With Web Search Enhancement:**
```bash
python run.py extract \
  --center-name "Autism Support Center" \
  --url "https://example.com" \
  --backend gemini \
  --enhance-with-websearch
```

**Ollama Local Processing:**
```bash
python run.py extract \
  --center-name "Autism Support Center" \
  --url "https://example.com" \
  --backend ollama \
  --model "llama3.1:8b-instruct" \
  --ollama-url "http://localhost:11434"
```

#### **All Available Arguments:**

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--center-name` | str | **Required** | Name of the center/organization |
| `--url` | str | **Required** | Website URL to extract from |
| `--backend` | choice | `gemini` | LLM backend: `ollama`, `openai`, `gemini` |
| `--model` | str | `None` | Model name (ollama: llama3.1:8b-instruct; openai: gpt-4o-mini; gemini: gemini-1.5-flash) |
| `--max-pages` | int | `None` | Maximum pages to crawl |
| `--out` | str | `None` | Optional path to write JSON output |
| `--enhance-with-websearch` | flag | `False` | Search web for missing contact info from reliable sources |
| `--ollama-url` | str | `None` | Ollama server URL |
| `--ollama-auth` | str | `None` | Ollama authentication (Header line or bare token) |
| `--openai-key` | str | `None` | OpenAI API key |
| `--gemini-key` | str | `None` | Gemini API key |

### 5. **Resource Categories (Simplified 9-Category System)**

The system automatically categorizes resources into these simplified categories:

1. **Assessment & Diagnosis** - Diagnostic Centers, Assessment Clinics, Psychoeducational Evaluation
2. **Crisis & Emergency** - Crisis Helplines, Emergency Intervention, Mental Health Crisis Teams  
3. **Education & Learning** - SEN Schools, Mainstream School Resources, Training Programs, Skills Development, Tutoring Services
4. **Employment** - Job Coaching, Workplace Accommodations, Vocational Training, Supported Employment
5. **Housing & Benefits** - Housing Assistance, Benefits Advice, Independent Living Programs, Welfare Navigation
6. **Transport & Accessibility** - Accessible Transport, Travel Training, Mobility Services, Transport Subsidies
7. **Community & Social** - Local Groups, National Organization Branches, Peer Networks, Social Meetups, Parent/Carer Groups
8. **Recreation & Activities** - Sports & Fitness, Arts & Entertainment, Play Centers, Hobby Clubs, Social Activities
9. **Unknown/Uncategorized** - Use only when the description doesn't clearly fit any category

## 📊 Pipeline Workflow

```
1. Input Data
   ↓
2. Populate Missing URLs (optional)
   ↓
3. Enrich with LLM
   - Extract descriptions
   - Identify services
   - Parse addresses
   - Validate neurodivergent relevance
   ↓
4. Categorize Resources
   - Keyword-based categorization
   - Fast & accurate
   ↓
5. Filter & Export
   - Filter by relevance
   - Export to Excel
```

## ⚙️ Configuration

### Environment Variables (.env)
```bash
# Required: At least one LLM API key
GEMINI_API_KEY=your_gemini_key_here
GOOGLE_API_KEY=your_google_key_here  # Alternative for Gemini
OPENAI_API_KEY=your_openai_key_here  # Optional

# Optional: Ollama configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_AUTH=your_auth_token
```

### API Rate Limits
- **Gemini Free Tier**: 15 requests/minute (use `--rate-limit 15`)
- **OpenAI**: 60 requests/minute (use `--rate-limit 60`)
- **Ollama**: No limit (local)

## 🎯 Common Use Cases

### Full Pipeline with All Features
```bash
python run.py enrich \
  --input data/input/to_be_normalised/enriched_resources.csv \
  --backend gemini \
  --enhance-with-websearch \
  --populate-urls \
  --categorize \
  --workers 5 \
  --rate-limit 15
```

### Quick Test Run (First 10 Rows)
```bash
python run.py enrich \
  --max-rows 10 \
  --workers 2 \
  --backend gemini
```

### Re-categorize Existing Data
```bash
python run.py categorize \
  --input data/output/enriched_resources_20231021.xlsx \
  --overwrite
```

### Extract High-Quality Neurodivergent Resources Only
```bash
python run.py filter \
  --input data/output/enriched_resources.xlsx \
  --filter \
  --min-score High \
  --output data/output/high_quality_resources.xlsx
```

## 📈 Performance

- **Parallel Pipeline**: ~0.5-2 seconds per resource
- **Caching**: Instant for previously processed resources
- **Categorization**: ~1000 resources/second (keyword-based)
- **URL Population**: ~300-400 URLs/second

## 🔧 Troubleshooting

### API Rate Limit Errors
```bash
# Reduce workers and rate limit
python run.py enrich --workers 3 --rate-limit 10
```

### Memory Issues
```bash
# Process in batches
python run.py enrich --max-rows 500 --start-row 0
python run.py enrich --max-rows 500 --start-row 500
```

### Invalid URLs
```bash
# Re-populate URLs with validation
python run.py populate-urls --input data/output/bad_urls.xlsx
```

## 📚 Documentation

- [Quick Start Guide](docs/START_HERE.md)
- [Setup Instructions](docs/SETUP.md)
- [Parallel Pipeline Guide](docs/PARALLEL_GUIDE.md)
- [Rate Limit Fix](docs/RATE_LIMIT_FIX.md)
- [Environment Setup](docs/README_ENV.md)
- [Changes Log](docs/CHANGES.md)

## 🧪 Testing

```bash
# Run tests
python -m pytest tests/

# Verify data integrity
python tests/verify_matches.py
```

## 📝 Output Format

All output files are Excel (.xlsx) with:
- ✅ **Yellow highlighting** for modified cells
- ✅ **Auto-adjusted column widths**
- ✅ **Clean encoding** (no ? or � characters)
- ✅ **Validation columns** (neurodivergent relevance)
- ✅ **Category assignments**

## 🤝 Contributing

1. Add new features to `src/`
2. Update tests in `tests/`
3. Document in `docs/`
4. Test with sample data in `data/input/`

## 📋 Complete Command Reference

### **Quick Command Cheat Sheet:**

```bash
# Get help for any command
python run.py <command> --help

# Basic enrichment
python run.py enrich --input data/input/resources.csv

# Full pipeline with all features
python run.py enrich \
  --input data/input/resources.csv \
  --backend gemini \
  --enhance-with-websearch \
  --populate-urls \
  --categorize \
  --workers 10 \
  --rate-limit 15

# Test with limited data
python run.py enrich \
  --input data/input/resources.csv \
  --max-rows 10 \
  --workers 2

# Populate missing URLs
python run.py populate-urls --input data/input/resources.csv

# Filter high-quality resources
python run.py filter \
  --input data/output/enriched_resources.xlsx \
  --filter \
  --min-score High

# Extract from single website
python run.py extract \
  --center-name "Resource Name" \
  --url "https://example.com" \
  --backend gemini
```

### **Environment Variables (.env file):**
```bash
# Required: At least one LLM API key
GEMINI_API_KEY=your_gemini_key_here
GOOGLE_API_KEY=your_google_key_here  # Alternative for Gemini
OPENAI_API_KEY=your_openai_key_here  # Optional

# Optional: Ollama configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_AUTH=your_auth_token
```

### **Performance Tuning:**
```bash
# High performance (more workers, higher rate limit)
python run.py enrich --workers 20 --rate-limit 30

# Conservative (fewer workers, lower rate limit)
python run.py enrich --workers 3 --rate-limit 10

# Local processing (no API limits)
python run.py enrich --backend ollama --workers 5
```

### **Batch Processing:**
```bash
# Process in chunks
python run.py enrich --max-rows 500 --start-row 0
python run.py enrich --max-rows 500 --start-row 500
python run.py enrich --max-rows 500 --start-row 1000
```

## 📜 License

[Your License Here]

## 🆘 Support

For issues or questions:
1. Check [docs/QUICKFIX.md](docs/QUICKFIX.md)
2. Review [docs/TROUBLESHOOTING.md](docs/SETUP.md)
3. Open an issue on GitHub

---

**Built with ❤️ for the neurodivergent community**

