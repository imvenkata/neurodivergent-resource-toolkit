# Content Cache System

## Overview

The system uses two separate cache layers:

1. **LLM Extraction Cache** (`.cache/llm_extractions/`): Caches the final structured JSON output from LLM extraction
2. **Content Cache** (`.cache/content/`): Caches the cleaned text content scraped from websites

## Why Two Caches?

- **Content Cache**: Stores raw website text, allowing fast prompt building without re-scraping
- **LLM Cache**: Stores final extraction results, allowing fast retrieval without re-running expensive LLM calls

## Current Behavior

When the batch pipeline runs:
- If **LLM cache exists**: Returns cached data immediately (fast)
- If **LLM cache missing**: Runs `web_llm_extract.py` which:
  1. Crawls website → populates **content cache**
  2. Builds prompt from content cache
  3. Calls LLM → populates **LLM cache**

## Known Issue

**Problem**: If LLM extraction was cached from BEFORE the content cache system was implemented, the content cache will be empty even though LLM cache exists.

**Solution**: The pipeline now checks if content cache exists. If missing but LLM cache exists, it will still run `web_llm_extract.py` to populate the content cache. This will:
- ✅ Crawl the website (to populate content cache)
- ✅ Use cached content for prompt building (if available)
- ⚠️ May still call LLM if prompt needs fresh data

## Populating Content Cache for Existing LLM Extractions

To populate content cache for resources that already have LLM cache:

### Option 1: Re-run pipeline (with refresh)
```bash
# This will re-crawl and populate content cache, but will still use LLM cache for extraction
python src/batch_enrich_pipeline_parallel.py \
  --refresh-html-cache \
  --input data/input/file.csv \
  --max-rows 10  # Test with small batch first
```

### Option 2: Use content cache population script (future)
A dedicated script could crawl existing LLM cached resources to populate content cache without calling LLM.

## File Naming

- **LLM Cache**: `Center_Name.json` (sanitized)
- **Content Cache**: `Center_Name_HASH.json` (includes URL hash for uniqueness)

## Benefits of Content Cache

1. **Faster Prompt Building**: No need to re-scrape websites
2. **Web Search Enhancement**: Web search results stored in content cache
3. **Debugging**: Can review scraped content without re-running extraction
4. **Consistency**: Same content used for prompt building across runs

