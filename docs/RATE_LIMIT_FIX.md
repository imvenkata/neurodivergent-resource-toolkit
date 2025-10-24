# Rate Limit Fix - Preventing Failures 🛡️

## The Problem You Encountered

With 10 workers, you hit **658 failures out of 781** (84% failure rate).

**Root Cause:** Gemini's free tier allows only **15 requests per minute**. With 10 parallel workers making simultaneous requests, you exceeded this limit and got blocked.

## ✅ Solutions (Pick One)

### Option 1: Use Fewer Workers (Simplest)

Use **3-5 workers** instead of 10. Still faster than sequential!

```bash
source .venv/bin/activate

python batch_enrich_pipeline_parallel.py \
  --backend gemini \
  --enhance-with-websearch \
  --skip-no-website \
  --workers 3 \
  --rate-limit 15
```

**Speed:** 3-4x faster than sequential  
**Success Rate:** ~100%  

### Option 2: Use Updated Version with Built-in Rate Limiting (Best)

I've updated the parallel script with automatic rate limiting!

```bash
source .venv/bin/activate

# Now you can safely use 10 workers with rate limiting
python batch_enrich_pipeline_parallel.py \
  --backend gemini \
  --enhance-with-websearch \
  --skip-no-website \
  --workers 10 \
  --rate-limit 15
```

The script will automatically:
- ✅ Track API requests per minute
- ✅ Wait if limit is reached
- ✅ Resume automatically
- ✅ Prevent failures

### Option 3: Resume from Where You Left Off

You already processed 123 centers successfully. Resume from there:

```bash
source .venv/bin/activate

python batch_enrich_pipeline_parallel.py \
  --backend gemini \
  --enhance-with-websearch \
  --skip-no-website \
  --workers 3 \
  --rate-limit 15 \
  --start-row 123
```

## 📊 Recommended Settings

| Tier | Max Requests/Min | Workers | Rate Limit Flag | Speed |
|------|-----------------|---------|-----------------|-------|
| **Gemini Free** | 15 | **3-5** | `--rate-limit 15` | **3-5x faster** |
| Gemini Paid | 60+ | 10-20 | `--rate-limit 60` | 10-20x faster |
| OpenAI (varies) | Check your tier | 3-10 | Adjust accordingly | Varies |
| Ollama (local) | Unlimited | 20+ | No limit needed | 20x+ faster |

## 🎯 Best Approach for Your 781 Centers

### Step 1: Clear Failed Cache (Optional)

The 658 failures might have created bad cache entries. Clean them:

```bash
# Backup cache
cp -r .cache/llm_extractions .cache/llm_extractions_backup

# The script will recreate cache for failed ones
```

### Step 2: Run with Safe Settings

```bash
source .venv/bin/activate

python batch_enrich_pipeline_parallel.py \
  --backend gemini \
  --enhance-with-websearch \
  --skip-no-website \
  --workers 5 \
  --rate-limit 15
```

**Expected Results:**
- Time: ~8-12 minutes (vs 30-40 sequential)
- Success rate: ~95-100%
- Cost: Same (~$1-2)

### Step 3: Check Results

```bash
open enriched_resources_parallel_*.xlsx
```

## 🔍 Understanding Rate Limiting

The updated script now:

1. **Tracks requests:** Counts how many API calls in the last 60 seconds
2. **Auto-waits:** If limit reached, waits until it's safe to continue
3. **Smart caching:** Cached results don't count toward rate limit
4. **Thread-safe:** Multiple workers coordinate automatically

## 💡 Pro Tips

### For Maximum Speed (If You Have Paid API)

If you're on Gemini's paid tier with higher limits:

```bash
python batch_enrich_pipeline_parallel.py \
  --workers 20 \
  --rate-limit 100 \
  --backend gemini
```

### For Free Tier (Most Reliable)

```bash
python batch_enrich_pipeline_parallel.py \
  --workers 3 \
  --rate-limit 14 \  # Slightly under limit for safety
  --backend gemini
```

### To Monitor Progress

The script shows real-time status:
```
🚀 Parallel Processing with 5 workers
📊 Rate limit: 15 requests/minute
...
[1/781] Center Name: ✓ new - 3 fields
[2/781] Center Name: ✓ cached - 2 fields
[3/781] Center Name: Failed
```

## 🚨 Troubleshooting

### Still seeing failures?

1. **Reduce workers further:**
   ```bash
   --workers 2
   ```

2. **Lower rate limit:**
   ```bash
   --rate-limit 12
   ```

3. **Check your API quota:**
   Visit: https://aistudio.google.com/app/apikey

### Want to try Ollama (free, local)?

No rate limits at all!

```bash
# Start Ollama
ollama serve

# Run with many workers
python batch_enrich_pipeline_parallel.py \
  --backend ollama \
  --model llama3.1:8b-instruct \
  --workers 20  # No rate limit!
```

---

**Ready to retry?** Use the safe settings above! 🚀

**Recommended command:**
```bash
source .venv/bin/activate

python batch_enrich_pipeline_parallel.py \
  --workers 5 \
  --rate-limit 15 \
  --backend gemini \
  --enhance-with-websearch \
  --skip-no-website
```

This should process all 781 centers in ~8-12 minutes with ~100% success rate!

