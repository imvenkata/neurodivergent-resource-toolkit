# Project Overview

## 🎯 Purpose

Automated toolkit for enriching, categorizing, and managing neurodivergent support resources using AI-powered data extraction.

## 📊 Key Statistics

- **Total Resources**: 1000+ neurodivergent support services
- **Enrichment Speed**: 0.5-2 seconds per resource (parallel)
- **Categorization**: 15 predefined categories
- **Supported LLMs**: Gemini, OpenAI, Ollama
- **Output Format**: Excel (.xlsx) with clean data

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLI Entry Point (run.py)                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            ▼                ▼                ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │   Enrichment │  │Categorization│  │   Filtering  │
    │   Pipeline   │  │    Engine    │  │   & Export   │
    └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
           │                 │                  │
           ▼                 ▼                  ▼
    ┌──────────────────────────────────────────────────┐
    │              LLM Integration Layer                │
    │  (Gemini / OpenAI / Ollama)                      │
    └──────────────────────────────────────────────────┘
           │                 │                  │
           ▼                 ▼                  ▼
    ┌──────────────────────────────────────────────────┐
    │           Data Storage & Caching                  │
    │  (.cache/ + data/output/)                        │
    └──────────────────────────────────────────────────┘
```

## 🔧 Core Components

### 1. **Enrichment Pipeline** (`src/batch_enrich_pipeline_parallel.py`)
- **Purpose**: Extract structured data from websites using LLMs
- **Features**:
  - Parallel processing (5-10x faster)
  - Web scraping with intelligent parsing
  - Intelligent caching
  - Rate limiting
  - Error recovery
- **Input**: CSV/Excel with basic info (name, website)
- **Output**: Enriched Excel with 30+ fields

### 2. **Categorization Engine** (`src/categorize_resources.py`)
- **Purpose**: Classify resources into predefined categories
- **Method**: Keyword-based classification
- **Speed**: 1000+ resources/second
- **Accuracy**: ~95% for well-described resources
- **Categories**: 15 specialized categories

### 3. **URL Population** (`src/populate_gmaps_url.py`)
- **Purpose**: Generate Google Maps URLs from place IDs or coordinates
- **Validation**: Rejects fake place IDs (like "1", "2", "3")
- **Fallback**: Uses coordinates when place ID unavailable
- **Success Rate**: ~75% for missing URLs

### 4. **Relevance Filter** (`src/filter_neurodivergent.py`)
- **Purpose**: Filter resources by neurodivergent relevance
- **Criteria**:
  - Relevance score (High/Medium/Low/None)
  - Explicit neurodivergent focus
  - Service type validation
- **Output**: Filtered Excel with only relevant resources

### 5. **Web Extractor** (`src/web_llm_extract.py`)
- **Purpose**: Extract data from a single website
- **Features**:
  - Multi-page crawling
  - Contact info extraction
  - Address parsing
  - Web search fallback
- **LLM Backends**: Gemini, OpenAI, Ollama

## 📁 Directory Structure

```
data_scraper/
├── src/                    # All source code
│   ├── *.py               # Main scripts
│   └── utils/             # Helper utilities
├── data/
│   ├── input/             # Raw input data
│   ├── output/            # Generated results
│   └── archive/           # Historical data
├── tests/                 # Test suite
├── docs/                  # Documentation
├── config/                # Configuration scripts
├── .cache/                # LLM response cache
└── run.py                 # CLI entry point
```

## 🔄 Data Flow

```
1. Input Data (CSV/Excel)
   ↓
2. URL Population (optional)
   - Validates place IDs
   - Generates Maps URLs
   ↓
3. Enrichment (LLM Processing)
   - Web scraping
   - LLM extraction
   - Address parsing
   - Contact info extraction
   ↓
4. Validation
   - Neurodivergent relevance check
   - Data quality validation
   ↓
5. Categorization
   - Keyword-based classification
   - 15 predefined categories
   ↓
6. Output (Excel)
   - Clean data
   - Highlighted changes
   - Validation flags
   - Category assignments
```

## 🚀 Performance Optimizations

### Parallel Processing
- ThreadPoolExecutor for concurrent LLM calls
- Configurable worker count (default: 10)
- Rate limiting to prevent API throttling

### Caching System
- Thread-safe cache for LLM responses
- Instant loading for previously processed resources
- JSON-based storage in `.cache/llm_extractions/`

### Text Cleaning
- Removes encoding issues (`?`, `�`)
- Preserves URLs and query strings
- Normalizes special characters
- Clean Excel output

### Smart Categorization
- Keyword-based (no LLM needed)
- Weights services higher than descriptions
- Hierarchical category matching
- Fallback to "Unknown Category"

## 📊 Supported Data Fields

### Input Requirements (Minimum)
- `gmaps_name` - Resource name
- `gmaps_website` - Website URL (optional with `--skip-no-website`)

### Enriched Output (30+ fields)
- **Basic**: name, description, category
- **Contact**: phone, email, address
- **Location**: postal code, town, county
- **Services**: age range, conditions, specific services
- **Validation**: neurodivergent relevance, confidence score
- **Metadata**: organization type, data confidence

## 🔐 Security & Privacy

- API keys stored in `.env` (gitignored)
- No data sent to external services except chosen LLM
- Local caching for reduced API calls
- Data files excluded from version control

## 🎓 Learning Resources

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Main documentation |
| [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) | New structure guide |
| [docs/START_HERE.md](docs/START_HERE.md) | Quick start |
| [docs/SETUP.md](docs/SETUP.md) | Installation |
| [docs/PARALLEL_GUIDE.md](docs/PARALLEL_GUIDE.md) | Parallel pipeline |
| [docs/RATE_LIMIT_FIX.md](docs/RATE_LIMIT_FIX.md) | API troubleshooting |

## 🔮 Future Enhancements

- [ ] Multi-language support
- [ ] Advanced LLM categorization option
- [ ] API endpoint for real-time enrichment
- [ ] Database integration
- [ ] Automated quality scoring
- [ ] Duplicate detection
- [ ] Geographic clustering
- [ ] Automated report generation

## 📈 Metrics

### Processing Speed
- **Sequential**: ~5-10 seconds/resource
- **Parallel (5 workers)**: ~1-2 seconds/resource
- **Parallel (10 workers)**: ~0.5-1 second/resource

### Cache Hit Rate
- First run: 0%
- Subsequent runs: ~75-90%
- Full cache: 100% (instant)

### API Usage
- Average: 1-2 LLM calls per resource
- Cached: 0 LLM calls
- With web search: 2-3 calls per resource

## 🎯 Success Criteria

✅ **Data Quality**
- 95%+ valid contact information
- 90%+ accurate categorization
- 100% clean text (no encoding issues)

✅ **Performance**
- < 2 seconds per resource (parallel)
- < 5 minutes for 300 resources
- < 15 minutes for 1000 resources (Gemini free tier)

✅ **Reliability**
- Automatic retry on failures
- Graceful degradation
- Comprehensive error logging

---

**Built for the neurodivergent community with care and attention to detail** ❤️

