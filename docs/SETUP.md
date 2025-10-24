# Setup Guide - Getting Started

## Prerequisites

1. **Python 3.12+** ✅ (You have this)
2. **Install Dependencies**
3. **Get an API Key**

## Step 1: Install Dependencies

```bash
# Install required packages
pip install openpyxl python-dotenv

# Or with uv (if you're using it)
uv pip install openpyxl python-dotenv
```

## Step 2: Get an API Key

You have **3 options**:

### Option 1: Gemini (Recommended) 🌟

**Why Gemini?**
- Fast and affordable
- $0.001-0.003 per center
- Easy to get started
- Free tier available

**Get your key:**
1. Go to: https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy your key

**Set the key (choose one method):**

**Method 1: .env file (Recommended - Permanent)**
```bash
# Copy the example file
cp env.example .env

# Edit .env and add your key
# GEMINI_API_KEY=your-actual-key-here
```

**Method 2: Export (Temporary - current session only)**
```bash
export GEMINI_API_KEY='your-key-here'
```

### Option 2: OpenAI

**Get your key:**
1. Go to: https://platform.openai.com/api-keys
2. Create a new key
3. Copy your key

**Set the key:**

Add to your `.env` file:
```bash
OPENAI_API_KEY=your-key-here
```

Or export temporarily:
```bash
export OPENAI_API_KEY='your-key-here'
```

**Note:** OpenAI is ~10x more expensive than Gemini

### Option 3: Ollama (Free, Local)

**Install Ollama:**
```bash
# macOS
brew install ollama

# Or download from: https://ollama.ai
```

**Start Ollama:**
```bash
ollama serve

# In another terminal, pull a model
ollama pull llama3.1:8b-instruct
```

**No API key needed!** Just use `--backend ollama`

## Step 3: Test the Setup

```bash
# Test with the test script
bash test_pipeline.sh

# Or test manually with 1 center
export GEMINI_API_KEY='your-key-here'

python batch_enrich_pipeline.py \
  --max-rows 1 \
  --backend gemini
```

## Step 4: Run the Full Pipeline

Once the test works, run the full pipeline:

```bash
export GEMINI_API_KEY='your-key-here'

python batch_enrich_pipeline.py \
  --input to_be_normalised/enriched_resources.csv \
  --output enriched_resources_updated.xlsx \
  --backend gemini \
  --enhance-with-websearch \
  --skip-no-website \
  --delay 2.0
```

## Troubleshooting

### "GEMINI_API_KEY not set"

Make sure you've exported the variable in the same terminal session:

```bash
# Check if it's set
echo $GEMINI_API_KEY

# Set it again if needed
export GEMINI_API_KEY='your-actual-key-here'
```

### "Module 'openpyxl' not found"

```bash
pip install openpyxl
```

### "Connection timeout" or rate limits

Increase the delay:
```bash
python batch_enrich_pipeline.py --delay 5.0 ...
```

## Quick Reference

### Test with Gemini
```bash
export GEMINI_API_KEY='sk-...'
bash test_pipeline.sh
```

### Test with OpenAI
```bash
export OPENAI_API_KEY='sk-...'
bash test_pipeline.sh
```

### Test with Ollama (free)
```bash
ollama serve  # In one terminal
bash test_pipeline.sh  # Will auto-detect Ollama
```

## Next Steps

1. ✅ Set your API key
2. ✅ Run `bash test_pipeline.sh`
3. ✅ Check `test_enriched_sample.xlsx`
4. ✅ Run full pipeline with all centers

## Cost Estimates

**For ~780 centers with websites:**

| Backend | Cost | Time |
|---------|------|------|
| Gemini Flash | $1-2 | 30-40 min |
| OpenAI GPT-4o-mini | $10-20 | 30-40 min |
| Ollama (local) | $0 | 60-90 min |

## Support

If you have issues:
1. Check the error message
2. See [README.md](README.md) for detailed docs
3. See [PIPELINE_QUICKSTART.md](PIPELINE_QUICKSTART.md) for examples

---

**Ready to start?** → Set your API key and run `bash test_pipeline.sh`! 🚀

