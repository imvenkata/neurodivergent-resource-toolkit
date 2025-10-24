# 🔧 Quick Fix - API Key Error

## The Error You Just Saw

```
RuntimeError: GEMINI_API_KEY (or GOOGLE_API_KEY) not set
```

## ✅ Solution (30 seconds)

### Step 1: Get a Gemini API Key (FREE)

1. Open: https://aistudio.google.com/app/apikey
2. Click **"Create API Key"** or **"Get API Key"**
3. Copy the key (starts with something like `AIza...`)

### Step 2: Set the API Key

**Option A: Use .env file (Recommended)**

1. Create a `.env` file in the project directory:
   ```bash
   cp env.example .env
   ```

2. Edit `.env` and add your key:
   ```bash
   GEMINI_API_KEY=AIzaSyDxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

3. Install python-dotenv if needed:
   ```bash
   pip install python-dotenv
   ```

**Option B: Export in terminal (temporary)**

```bash
export GEMINI_API_KEY='AIzaSyDxxxxxxxxxxxxxxxxxxxxxxxxxxx'
```

### Step 3: Run the Test Again

```bash
bash test_pipeline.sh
```

## ✅ Expected Output

You should now see:
```
✓ Using Gemini backend

Testing batch enrichment pipeline on first 3 rows...

[1/3] Processing: East London NHS Foundation Trust
  Website: http://www.elft.nhs.uk/
  ✓ Updated fields: description_short, age_range, organization_type

[2/3] Processing: C N W L Mental Health Clinic
  Website: http://www.cnwl.nhs.uk/
  ✓ Updated fields: description_short, specific_services

...
```

## 🎯 Alternative: Use Free Local LLM

Don't want to use an API key? Use **Ollama** (runs locally, free):

```bash
# Install Ollama
brew install ollama

# Start Ollama server
ollama serve

# Pull model (in another terminal)
ollama pull llama3.1:8b-instruct

# Update test script to use Ollama
# Edit test_pipeline.sh and change --backend to ollama
```

## Still Having Issues?

### Check if key is set:
```bash
echo $GEMINI_API_KEY
```

If it's empty, you need to export it again.

### Make sure you're using the same terminal:
The `export` command only works in the current terminal session.

### Permanent solution (add to ~/.zshrc or ~/.bashrc):
```bash
echo 'export GEMINI_API_KEY="your-key-here"' >> ~/.zshrc
source ~/.zshrc
```

---

**Ready?** → Get your key, export it, and run `bash test_pipeline.sh` again! 🚀

