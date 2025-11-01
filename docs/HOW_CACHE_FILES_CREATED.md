# How Cache Files Are Created - Simple Explanation

## The Problem You Found

You noticed that **LLM extraction cache files** (`.cache/llm_extractions/`) were created, but **content cache files** (`.cache/content/`) were missing for the same resources.

## Root Cause (FIXED)

The issue was a **working directory mismatch**:

1. **Batch pipeline** calls `web_llm_extract.py` as a subprocess
2. Subprocess runs with `cwd=src/` (the `src/` directory)
3. Content cache path is relative: `.cache/content`
4. Relative paths resolve from **current working directory**
5. Result: Cache saved to `src/.cache/content/` instead of project root `.cache/content/`

**Your cache files WERE created, just in the wrong place!**

Check: `ls -la src/.cache/content/` - you'll find them there!

## How Files Are Created (Step by Step)

### Step 1: Content Cache (During Subprocess)

```
Batch Pipeline
  → Calls: python src/web_llm_extract.py --center-name "X" --url "Y"
    (runs with cwd=src/)
    
web_llm_extract.py main()
  → crawl_site() called FIRST
    → Fetches website pages
    → Saves CONTENT CACHE
      Location: src/.cache/content/ (WRONG - before fix)
      Location: .cache/content/ (CORRECT - after fix)
```

**Content Cache Created:** During `crawl_site()` function execution (lines 590-623)

### Step 2: LLM Extraction Cache (After Subprocess)

```
web_llm_extract.py
  → build_prompt()
  → LLM call (Gemini/OpenAI)
  → Returns JSON to stdout
  
Batch Pipeline receives stdout
  → Parses JSON
  → Saves LLM EXTRACTION CACHE
    Location: .cache/llm_extractions/ (always project root)
```

**LLM Cache Created:** After subprocess completes, in batch pipeline (lines 288-292)

## Why You Saw LLM Cache But Not Content Cache

1. **LLM cache** saves to `.cache/llm_extractions/` (project root) ✅
2. **Content cache** was saving to `src/.cache/content/` (wrong location) ❌
3. You looked in project root `.cache/content/` → found nothing
4. But files existed in `src/.cache/content/`!

## The Fix

Updated cache path functions to **always resolve to absolute paths**:

```python
def get_content_cache_path(center_name, website_url, cache_dir):
    cache_base = Path(cache_dir)
    if not cache_base.is_absolute():
        # Always resolve from project root, not current working directory
        project_root = Path(__file__).parent.parent
        cache_base = project_root / cache_dir
    return cache_base / f"{name_safe}_{hash}.json"
```

Now cache files are **always saved to project root**, regardless of where code runs from.

## Verification

After the fix, run:
```bash
# Check project root cache
ls -la .cache/content/

# Should find cache files for all processed resources
# (they will be created in correct location on next run)
```

## Migration Note

If you have existing cache files in `src/.cache/content/`, you can either:
1. Leave them (they'll be used if needed)
2. Move them: `mv src/.cache/content/* .cache/content/`
3. Let new runs create fresh cache in correct location

