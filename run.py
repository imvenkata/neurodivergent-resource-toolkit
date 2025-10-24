#!/usr/bin/env python3
"""
Main CLI entry point for the Data Scraper toolkit.

Usage:
    python run.py enrich --help
    python run.py categorize --help
    python run.py populate-urls --help
    python run.py filter --help
"""

import sys
import subprocess
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print("""
Data Scraper - Neurodivergent Resource Enrichment Toolkit
==========================================================

Available commands:
  enrich          - Enrich resources with LLM data (parallel pipeline)
  enrich-single   - Enrich a single resource (sequential pipeline)
  categorize      - Categorize resources into predefined categories
  populate-urls   - Populate missing Google Maps URLs
  filter          - Filter resources by neurodivergent relevance
  extract         - Extract data from a single website

Usage:
  python run.py <command> [options]

Examples:
  python run.py enrich --input data/input/resources.csv --workers 5
  python run.py categorize --input data/output/enriched.xlsx
  python run.py filter --input data/output/enriched.xlsx --min-score High

For detailed help on a command:
  python run.py <command> --help
""")
        sys.exit(1)
    
    command = sys.argv[1]
    args = sys.argv[2:]
    
    # Map commands to scripts
    commands = {
        "enrich": "src/batch_enrich_pipeline_parallel.py",
        "enrich-single": "src/batch_enrich_pipeline.py",
        "categorize": "src/categorize_resources.py",
        "populate-urls": "src/populate_gmaps_url.py",
        "filter": "src/filter_neurodivergent.py",
        "extract": "src/web_llm_extract.py",
    }
    
    if command not in commands:
        print(f"Error: Unknown command '{command}'")
        print(f"Available commands: {', '.join(commands.keys())}")
        sys.exit(1)
    
    script_path = Path(__file__).parent / commands[command]
    
    # Run the script
    try:
        result = subprocess.run([sys.executable, str(script_path)] + args)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Error running command: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

