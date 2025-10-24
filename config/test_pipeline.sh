#!/bin/bash
# Test script for batch_enrich_pipeline.py

echo "================================================"
echo "Batch Enrichment Pipeline - Test Run"
echo "================================================"
echo ""

# Load .env file if it exists
if [ -f .env ]; then
    echo "✓ Loading .env file..."
    export $(grep -v '^#' .env | xargs)
    echo ""
fi

# Check if API key is set (after loading .env)
if [ -z "$GEMINI_API_KEY" ] && [ -z "$GOOGLE_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ ERROR: No API key found!"
    echo ""
    
    if [ -f .env ]; then
        echo "Found .env file but no valid API key inside."
        echo "Please edit .env and add your API key:"
        echo ""
        echo "  nano .env"
        echo "  # Add: GEMINI_API_KEY=your-actual-key-here"
    else
        echo "No .env file found. Create one:"
        echo ""
        echo "  bash setup_env.sh"
        echo "  # OR"
        echo "  cp env.example .env"
        echo "  nano .env"
    fi
    echo ""
    echo "Alternatively, export manually:"
    echo "  export GEMINI_API_KEY='your-api-key-here'"
    echo ""
    echo "For local Ollama (free, no API key needed):"
    echo "  ollama serve"
    echo "  # Then edit this script to use --backend ollama"
    echo ""
    exit 1
fi

if [ -n "$GEMINI_API_KEY" ] || [ -n "$GOOGLE_API_KEY" ]; then
    BACKEND="gemini"
    echo "✓ Using Gemini backend"
elif [ -n "$OPENAI_API_KEY" ]; then
    BACKEND="openai"
    echo "✓ Using OpenAI backend"
else
    BACKEND="ollama"
    echo "✓ Using Ollama backend (make sure Ollama is running)"
fi

echo ""
echo "Testing batch enrichment pipeline on first 3 rows..."
echo ""

python batch_enrich_pipeline.py \
  --input to_be_normalised/enriched_resources.csv \
  --output test_enriched_sample.xlsx \
  --backend $BACKEND \
  --enhance-with-websearch \
  --max-rows 3 \
  --skip-no-website \
  --delay 2.0

if [ $? -eq 0 ]; then
    echo ""
    echo "================================================"
    echo "✅ Test complete! Check test_enriched_sample.xlsx"
    echo "================================================"
else
    echo ""
    echo "================================================"
    echo "❌ Test failed - see errors above"
    echo "================================================"
    exit 1
fi

