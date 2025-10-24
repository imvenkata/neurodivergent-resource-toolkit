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
│   ├── batch_enrich_pipeline.py           # Sequential pipeline
│   ├── web_llm_extract.py                 # Single website extractor
│   ├── categorize_resources.py            # Resource categorization
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
```bash
python run.py enrich \
  --workers 5 \
  --rate-limit 15 \
  --enhance-with-websearch \
  --populate-urls \
  --categorize
```

**Features:**
- Parallel processing (5-10x faster)
- LLM-powered data extraction
- Web search enhancement
- Automatic URL population
- Built-in categorization
- Rate limiting for API compliance
- Intelligent caching

### 2. **Categorize Resources**
```bash
python run.py categorize \
  --input data/output/enriched_resources_*.xlsx \
  --output data/output/categorized_resources.xlsx
```

**Categories:**
- Assessment & Diagnosis
- Crisis & Emergency
- Community Support
- Education Support
- Employment Support
- Housing Support
- Benefits Support
- Transport Support
- Autism Friendly Entertainment
- Local Support Services and Groups
- Employment and Skills Services
- National Autistic Society Branches
- Autism Friendly Sports Activities
- Special Needs Play Centres
- Special Interests and Hobbies

### 3. **Populate Missing URLs**
```bash
python run.py populate-urls \
  --input data/input/resources.csv \
  --output data/output/with_urls.xlsx
```

### 4. **Filter by Neurodivergent Relevance**
```bash
python run.py filter \
  --input data/output/enriched_resources.xlsx \
  --filter \
  --min-score High \
  --output data/output/neurodivergent_only.xlsx
```

### 5. **Extract from Single Website**
```bash
python run.py extract \
  --center-name "Resource Name" \
  --url "https://example.com" \
  --backend gemini
```

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

## 📜 License

[Your License Here]

## 🆘 Support

For issues or questions:
1. Check [docs/QUICKFIX.md](docs/QUICKFIX.md)
2. Review [docs/TROUBLESHOOTING.md](docs/SETUP.md)
3. Open an issue on GitHub

---

**Built with ❤️ for the neurodivergent community**

