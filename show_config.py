#!/usr/bin/env python3
"""
Show available configurations and generate example commands.
"""

from config import get_config, PRESETS, LLM_CONFIG, PROCESSING_CONFIG
import json

def show_configs():
    print("🔧 Available Configuration Presets:")
    print("=" * 50)
    
    for name, preset in PRESETS.items():
        print(f"\n📋 {name.upper()}:")
        for key, value in preset.items():
            print(f"  {key}: {value}")
    
    print(f"\n🔧 Default LLM Configuration:")
    for key, value in LLM_CONFIG.items():
        print(f"  {key}: {value}")
    
    print(f"\n⚙️  Default Processing Configuration:")
    for key, value in PROCESSING_CONFIG.items():
        print(f"  {key}: {value}")

def show_examples():
    print("\n" + "=" * 50)
    print("📝 Example Commands:")
    print("=" * 50)
    
    examples = [
        ("Quick Test (5 resources)", "python enrich.py --preset quick_test"),
        ("Production Run", "python enrich.py --preset production"),
        ("Conservative (slow but safe)", "python enrich.py --preset conservative"),
        ("Local Ollama", "python enrich.py --preset local_ollama"),
        ("Custom Input", "python enrich.py --input my_data.csv --max-rows 10"),
        ("Custom Workers", "python enrich.py --workers 5 --max-rows 20"),
    ]
    
    for desc, cmd in examples:
        print(f"\n{desc}:")
        print(f"  {cmd}")

if __name__ == "__main__":
    show_configs()
    show_examples()
