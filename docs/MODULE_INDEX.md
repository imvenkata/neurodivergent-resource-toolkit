# Module Index

Quick navigation to all Python modules and their documentation.

## 📚 Core Modules

### Enrichment & Processing

| Module | File | CLI Command | Documentation |
|--------|------|-------------|---------------|
| **Parallel Enrichment Pipeline** | `src/batch_enrich_pipeline_parallel.py` | `python run.py enrich` | [MODULE_GUIDE.md](../MODULE_GUIDE.md#1-parallel-enrichment-pipeline) |
| **Sequential Enrichment Pipeline** | `src/batch_enrich_pipeline.py` | `python run.py enrich-single` | [MODULE_GUIDE.md](../MODULE_GUIDE.md#2-sequential-enrichment-pipeline) |
| **Web Data Extractor** | `src/web_llm_extract.py` | `python run.py extract` | [MODULE_GUIDE.md](../MODULE_GUIDE.md#3-web-extractor) |

### Data Analysis & Filtering

| Module | File | CLI Command | Documentation |
|--------|------|-------------|---------------|
| **Resource Categorization** | `src/categorize_resources.py` | `python run.py categorize` | [MODULE_GUIDE.md](../MODULE_GUIDE.md#4-categorization-engine) |
| **URL Population** | `src/populate_gmaps_url.py` | `python run.py populate-urls` | [MODULE_GUIDE.md](../MODULE_GUIDE.md#5-url-population) |
| **Relevance Filter** | `src/filter_neurodivergent.py` | `python run.py filter` | [MODULE_GUIDE.md](../MODULE_GUIDE.md#6-relevance-filter) |

### Utilities

| Module | File | Purpose |
|--------|------|---------|
| **Google Places Enrichment** | `src/utils/enrich_with_google.py` | Legacy Google Places integration |
| **LLM Description Enrichment** | `src/utils/llm_enrich_description.py` | Legacy LLM enrichment |
| **Service Merger** | `src/utils/merge_services.py` | Merge multiple datasets |
| **Web Scraper** | `src/utils/scraper.py` | Basic web scraping utilities |

## 🧪 Test Modules

| Module | File | Purpose |
|--------|------|---------|
| **Normalization Tests** | `tests/test_normalization.py` | Test data normalization |
| **Match Verification** | `tests/verify_matches.py` | Verify data matching |

## 📖 Complete Documentation

### Getting Started
1. [README.md](../README.md) - Project overview and quick start
2. [START_HERE.md](START_HERE.md) - Installation and first steps
3. [SETUP.md](SETUP.md) - Detailed setup instructions
4. [QUICK_REFERENCE.md](../QUICK_REFERENCE.md) - Command cheat sheet

### Module Documentation
5. [MODULE_GUIDE.md](../MODULE_GUIDE.md) - **Detailed module reference** ⭐
6. [PROJECT_OVERVIEW.md](../PROJECT_OVERVIEW.md) - Architecture and design

### Guides
7. [PARALLEL_GUIDE.md](PARALLEL_GUIDE.md) - Parallel pipeline optimization
8. [RATE_LIMIT_FIX.md](RATE_LIMIT_FIX.md) - API rate limit troubleshooting
9. [README_ENV.md](README_ENV.md) - Environment variable configuration
10. [NEURODIVERGENT_VALIDATION.md](NEURODIVERGENT_VALIDATION.md) - Validation system

### Migration & Changes
11. [MIGRATION_GUIDE.md](../MIGRATION_GUIDE.md) - Directory restructure guide
12. [CHANGES.md](CHANGES.md) - Change log

## 🔍 Finding What You Need

### "I want to..."

| Goal | See |
|------|-----|
| **Get started quickly** | [QUICK_REFERENCE.md](../QUICK_REFERENCE.md) |
| **Understand a specific module** | [MODULE_GUIDE.md](../MODULE_GUIDE.md) |
| **Fix API rate limit errors** | [RATE_LIMIT_FIX.md](RATE_LIMIT_FIX.md) |
| **Set up environment variables** | [README_ENV.md](README_ENV.md) |
| **Understand the architecture** | [PROJECT_OVERVIEW.md](../PROJECT_OVERVIEW.md) |
| **Migrate to new structure** | [MIGRATION_GUIDE.md](../MIGRATION_GUIDE.md) |
| **Install and configure** | [SETUP.md](SETUP.md) |
| **Optimize performance** | [PARALLEL_GUIDE.md](PARALLEL_GUIDE.md) |

## 🎯 By Use Case

### Data Enrichment
- [Parallel Pipeline Guide](../MODULE_GUIDE.md#1-parallel-enrichment-pipeline)
- [Web Extractor Guide](../MODULE_GUIDE.md#3-web-extractor)
- [Performance Tips](PARALLEL_GUIDE.md)

### Data Organization
- [Categorization Guide](../MODULE_GUIDE.md#4-categorization-engine)
- [URL Population Guide](../MODULE_GUIDE.md#5-url-population)
- [Filtering Guide](../MODULE_GUIDE.md#6-relevance-filter)

### Troubleshooting
- [Rate Limit Issues](RATE_LIMIT_FIX.md)
- [Environment Setup](README_ENV.md)
- [Quick Fixes](../QUICK_REFERENCE.md#-quick-fixes)

---

**Last Updated**: October 2024
