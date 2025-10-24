#!/bin/bash
# Quick setup script to create .env file

echo "========================================="
echo "  .env File Setup"
echo "========================================="
echo ""

if [ -f .env ]; then
    echo "⚠️  .env file already exists!"
    echo ""
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled. Edit .env manually."
        exit 0
    fi
fi

# Copy example file
cp env.example .env
echo "✓ Created .env file from template"
echo ""

# Prompt for Gemini API key
echo "Get your Gemini API key from:"
echo "https://aistudio.google.com/app/apikey"
echo ""
read -p "Enter your Gemini API key (or press Enter to skip): " api_key
echo ""

if [ -n "$api_key" ]; then
    # Replace the placeholder in .env
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/GEMINI_API_KEY=.*/GEMINI_API_KEY=$api_key/" .env
    else
        # Linux
        sed -i "s/GEMINI_API_KEY=.*/GEMINI_API_KEY=$api_key/" .env
    fi
    echo "✓ API key added to .env file"
else
    echo "⚠️  No API key entered. Edit .env file manually:"
    echo "   nano .env"
fi

echo ""
echo "========================================="
echo "  Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Make sure python-dotenv is installed:"
echo "   pip install python-dotenv"
echo ""
echo "2. Run the test:"
echo "   bash test_pipeline.sh"
echo ""
echo "Your API key is stored in .env and will be"
echo "automatically loaded by the scripts."
echo ""

