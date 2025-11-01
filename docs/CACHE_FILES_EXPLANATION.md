# Cache Files Creation Flow

## Overview

The system creates two types of cache files during resource enrichment:

1. **LLM Extraction Cache** (`.cache/llm_extractions/`) - Final structured JSON output
2. **Content Cache** (`.cache/content/`) - Cleaned website text content

## How Cache Files Are Created

### Flow Diagram

```
Batch Pipeline (batch_enrich_pipeline_parallel.py)
  ↓
  Calls web_llm_extract.py as subprocess
  ↓
web_llm_extract.py main()
  ↓
  ├─→ crawl_site() [STEP 1]
  │     ├─→ Fetches website pages
  │     ├─→ Saves to CONTENT CACHE ← This happens here
  │     └─→ Returns (pages, working_url)
  │
  ├─→ build_prompt() [STEP 2]
  │     └─→ Uses content cache if available
  │
  ├─→ LLM call (Gemini/OpenAI/Ollama) [STEP 3]
  │     └─→ Extracts structured data
  │
  └─→ Returns JSON to stdout
       ↓
Batch Pipeline receives JSON
  ↓
  Saves to LLM EXTRACTION CACHE ← This happens here
```

## Step-by-Step Details

### Step 1: Content Cache Creation (`crawl_site` function)

**Location:** `src/web_llm_extract.py`, lines 590-623

**When it happens:**
- Called at the START of `web_llm_extract.py` execution
- Before LLM extraction happens
- Saves cleaned text from website pages

**Code flow:**
```python
def crawl_site(..., center_name, content_cache_dir):
    # ... fetch website pages ...
    
    # Save cleaned text to content cache
    if center_name and content_cache_dir is not False:
        # Process HTML pages → cleaned text
        combined_website_text = "..."
        
        # Save to cache
        save_content_to_cache(
            center_name=center_name,
            website_url=working_url,
            website_text=combined_website_text,
            ...
        )
```

**Content Cache File:**
- **Location:** `.cache/content/`
- **Filename:** `{Center_Name}_{MD5_Hash}.json`
- **Hash:** MD5 of `"{center_name}_{website_url}"`
- **Contains:** `website_text`, `website_pages`, `web_search_text`, `web_search_sources`

**When content cache is NOT created:**
1. If `center_name` is None or empty
2. If `content_cache_dir` is False (disabled)
3. If website fetch fails (no pages collected) - **NOW FIXED**: saves empty cache to record failed attempt
4. If `save_content_to_cache()` throws an exception (silently caught, but now logged)

**IMPORTANT BUG FIX (Nov 1, 2025):**
- **Issue**: Subprocess runs with `cwd=src/`, so relative paths like `.cache/content` resolved to `src/.cache/content/`
- **Result**: Content cache files were saved in wrong location
- **Fix**: Cache path functions now resolve to absolute paths from project root
- **Note**: Existing cache files may be in `src/.cache/content/` (will be migrated automatically)

### Step 2: LLM Extraction Cache Creation

**Location:** `src/batch_enrich_pipeline_parallel.py`, lines 284-292

**When it happens:**
- After `web_llm_extract.py` subprocess completes successfully
- Only if subprocess returns JSON output
- After parsing the JSON response

**Code flow:**
```python
result = subprocess.run(cmd, ...)  # Calls web_llm_extract.py

if result.returncode == 0:
    data = json.loads(result.stdout)  # Parse JSON output
    
    # Save to LLM cache
    with open(cache_file, "w") as f:
        json.dump(data, f, ...)
```

**LLM Cache File:**
- **Location:** `.cache/llm_extractions/`
- **Filename:** `{Center_Name}.json` (sanitized, max 100 chars)
- **Contains:** Full LLM extraction result (all fields)

## Why Content Cache Might Be Missing

### Issue 1: Website Fetch Failed
If `crawl_site()` returns empty `docs` list:
- Code exits early: `sys.exit(2)` (line 1548-1550)
- Content cache never gets saved
- LLM extraction never happens
- **Result:** No cache files at all

### Issue 2: Empty Content
If website pages have no extractable text:
- `combined_website_text` is empty string
- Code now always saves (updated to save even if empty)
- **Previous behavior:** Would skip saving empty cache

### Issue 3: Exception During Save
If `save_content_to_cache()` throws exception:
- Exception is caught and logged (line 620-622)
- Cache save fails silently
- Extraction continues
- **Result:** LLM cache exists, content cache missing

### Issue 4: Center Name Not Passed
If `center_name` is None:
- Condition check fails: `if center_name and ...`
- Content cache not saved
- **Result:** LLM cache exists, content cache missing

## Debugging Missing Content Cache

### Check 1: Verify subprocess is called correctly
```python
# In batch_enrich_pipeline_parallel.py
cmd = [sys.executable, "web_llm_extract.py", "--center-name", center_name, ...]
# center_name should be passed correctly
```

### Check 2: Check if website fetch succeeded
Look for error messages:
- "Failed to fetch website content" → website fetch failed
- No error → fetch likely succeeded

### Check 3: Check content cache save location
```python
from src.web_llm_extract import get_content_cache_path
cache_path = get_content_cache_path(center_name, website_url, ".cache/content")
print(f"Expected cache: {cache_path}")
```

### Check 4: Verify center_name is not None
```python
# In crawl_site function
print(f"center_name: {center_name}")  # Should not be None
```

## Recent Fix

**Problem:** Content cache only saved if `combined_website_text.strip()` was not empty.

**Solution:** Updated to always save content cache (even if empty), with error logging:
```python
# Always save content cache (even if empty) so we know the crawl happened
try:
    save_content_to_cache(...)
except Exception as e:
    print(f"⚠️  Failed to save content cache: {e}", file=sys.stderr)
```

This ensures:
- Cache files are created for all processed resources
- Empty cache indicates failed crawl (no extractable content)
- Errors are logged but don't fail the extraction

## Verification Commands

```bash
# Count LLM cache files
ls -1 .cache/llm_extractions/*.json | wc -l

# Count content cache files
ls -1 .cache/content/*.json | wc -l

# Check specific resource
python -c "
from src.web_llm_extract import get_content_cache_path
cache = get_content_cache_path('Resource Name', 'https://url.com', '.cache/content')
print(f'Expected: {cache}')
print(f'Exists: {cache.exists()}')
"

# Find cache files created today
find .cache/content -name '*.json' -mtime -1
```

