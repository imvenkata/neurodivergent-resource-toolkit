# Using .env Files for API Keys

## Why Use .env Files?

✅ **Convenient** - Set once, use everywhere  
✅ **Secure** - Automatically gitignored  
✅ **No exports needed** - Works across terminal sessions  
✅ **Easy sharing** - Team members can use env.example as template

## Setup Instructions

### Method 1: Automated Setup (Recommended)

```bash
bash setup_env.sh
```

This will:
1. Create `.env` file from template
2. Prompt you for your API key
3. Save it securely

### Method 2: Manual Setup

```bash
# 1. Copy the example file
cp env.example .env

# 2. Edit the file
nano .env

# 3. Add your API key
GEMINI_API_KEY=AIzaSyD_your_actual_key_here
```

## How It Works

Both `web_llm_extract.py` and `batch_enrich_pipeline.py` automatically load `.env` at startup:

```python
# This code is already in the scripts
from dotenv import load_dotenv
load_dotenv()
```

The scripts will:
1. Look for `.env` file in the project directory
2. Load all variables into the environment
3. Fall back to system environment variables if no `.env` exists

## Supported Variables

All of these can be set in your `.env` file:

```bash
# Gemini (recommended)
GEMINI_API_KEY=your-key-here
GOOGLE_API_KEY=your-key-here  # Alternative for Gemini

# OpenAI
OPENAI_API_KEY=your-key-here

# Ollama (local LLM)
OLLAMA_URL=http://localhost:11434
OLLAMA_AUTH=optional-auth-token
```

## Getting API Keys

### Gemini (Free, Recommended)
1. Visit: https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key (starts with `AIza`)

### OpenAI
1. Visit: https://platform.openai.com/api-keys
2. Create new key
3. Copy the key (starts with `sk-`)

## Security

✅ `.env` is in `.gitignore` - won't be committed to git  
✅ Keys stay on your machine  
✅ Each team member has their own `.env`  
✅ `env.example` shows the format without exposing keys

## Testing

After creating your `.env` file:

```bash
# Test that it's loaded
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('API key loaded:', 'Yes' if os.getenv('GEMINI_API_KEY') else 'No')"

# Run the test pipeline
bash test_pipeline.sh
```

## Troubleshooting

### "python-dotenv not found"

Install it:
```bash
pip install python-dotenv
```

### "API key not set"

Check your `.env` file:
```bash
cat .env
```

Should show:
```
GEMINI_API_KEY=AIzaSyD...
```

Make sure:
- No spaces around `=`
- No quotes needed (unless key contains spaces)
- File is named exactly `.env` (not `.env.txt`)

### .env not loading

Make sure you're running scripts from the project directory:
```bash
cd /Users/venkata/startup/data_scraper
bash test_pipeline.sh
```

### Still using exports?

If you previously exported API keys, they might override `.env` values. Either:
- Unset them: `unset GEMINI_API_KEY`
- Close terminal and open a new one
- Let `.env` handle it going forward

## Migration from Exports

If you were using `export` commands:

**Before:**
```bash
export GEMINI_API_KEY='AIzaSyD...'
python batch_enrich_pipeline.py ...
```

**After (with .env):**
```bash
# Just run directly, .env is loaded automatically
python batch_enrich_pipeline.py ...
```

Much cleaner! 🎉

## Example .env File

```bash
# My API keys (this file is gitignored)

# Gemini - for batch processing
GEMINI_API_KEY=AIzaSyDxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional: OpenAI for testing
# OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx

# Optional: Local Ollama
# OLLAMA_URL=http://localhost:11434
```

---

**Next Step:** Run `bash setup_env.sh` to get started! 🚀

