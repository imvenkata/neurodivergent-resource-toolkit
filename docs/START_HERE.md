# 🚀 Start Here - Quick Setup (2 minutes)

## What You Need

1. ✅ Python 3.12+ (you have this)
2. ⬜ API Key (get it free)
3. ⬜ Dependencies installed

## Quick Setup

### 1. Install Dependencies

```bash
pip install openpyxl python-dotenv
```

### 2. Set Up Your API Key

**Easy way (run the setup script):**
```bash
bash setup_env.sh
```

**Manual way:**
```bash
# 1. Copy the example file
cp env.example .env

# 2. Get your FREE Gemini API key
open https://aistudio.google.com/app/apikey

# 3. Edit .env and paste your key
nano .env
# Change: GEMINI_API_KEY=your-gemini-api-key-here
# To:     GEMINI_API_KEY=AIzaSyD... (your actual key)
```

### 3. Test It!

```bash
bash test_pipeline.sh
```

That's it! The pipeline will automatically read your API key from `.env`

## Expected Output

```
✓ Using Gemini backend

Testing batch enrichment pipeline on first 3 rows...

[1/3] Processing: East London NHS Foundation Trust
  Website: http://www.elft.nhs.uk/
  ✓ Updated fields: description_short, age_range, organization_type

✅ Test complete! Check test_enriched_sample.xlsx
```

## Run Full Pipeline

Once the test works:

```bash
python batch_enrich_pipeline.py \
  --backend gemini \
  --enhance-with-websearch \
  --skip-no-website \
  --delay 2.0
```

## Your .env File

The `.env` file stores your API keys securely:

```bash
# .env (this file is gitignored - your keys are safe)
GEMINI_API_KEY=AIzaSyDxxxxxxxxxxxxxxxxxxxxxxxxx
```

Benefits:
- ✅ No need to export variables each time
- ✅ Keys are automatically loaded
- ✅ .env is gitignored (safe from git commits)
- ✅ Works across all scripts

## Troubleshooting

### "python-dotenv not found"
```bash
pip install python-dotenv
```

### "API key not set"
Make sure your `.env` file exists and has the correct format:
```bash
cat .env  # Should show: GEMINI_API_KEY=AIza...
```

### Still having issues?
See [QUICKFIX.md](QUICKFIX.md) for detailed troubleshooting

## Next Steps

1. ✅ Run `bash setup_env.sh` or create `.env` manually
2. ✅ Run `bash test_pipeline.sh`
3. ✅ Check the output Excel file
4. ✅ Run full pipeline on all data

---

**Ready?** → Run `bash setup_env.sh` now! 🎯

