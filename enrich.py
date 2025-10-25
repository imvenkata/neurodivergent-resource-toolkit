#!/usr/bin/env python3
"""
Simple CLI wrapper for the enrichment pipeline using configuration files.
This replaces the long command line arguments with simple presets.
"""

import argparse
import subprocess
import sys
from pathlib import Path
from config import get_config, get_command_args, DEFAULT_INPUT

def main():
    parser = argparse.ArgumentParser(
        description="Neurodivergent Resource Enrichment Pipeline - Simple CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python enrich.py                                    # Use default settings
  python enrich.py --preset quick_test                # Test with 5 resources
  python enrich.py --preset production                # Full production run
  python enrich.py --preset conservative              # Conservative settings
  python enrich.py --preset local_ollama              # Use local Ollama
  python enrich.py --input my_data.csv --max-rows 10  # Custom settings
        """
    )
    
    # Preset selection
    parser.add_argument(
        "--preset", 
        choices=["quick_test", "production", "conservative", "local_ollama"],
        help="Use a predefined configuration preset"
    )
    
    # File overrides
    parser.add_argument("--input", help="Input CSV file path")
    parser.add_argument("--output", help="Output Excel file path")
    
    # Common overrides
    parser.add_argument("--max-rows", type=int, help="Maximum rows to process")
    parser.add_argument("--workers", type=int, help="Number of parallel workers")
    parser.add_argument("--backend", choices=["gemini", "openai", "ollama"], help="LLM backend")
    
    args = parser.parse_args()
    
    # Get base configuration
    config = get_config(args.preset)
    
    # Apply command line overrides
    if args.max_rows is not None:
        config["processing"]["max_rows"] = args.max_rows
    if args.workers is not None:
        config["processing"]["workers"] = args.workers
    if args.backend:
        config["llm"]["backend"] = args.backend
    
    # Use default input if none specified
    input_file = args.input or str(DEFAULT_INPUT)
    
    # Generate command arguments
    cmd_args = get_command_args(config, input_file, args.output)
    
    # Build the full command
    cmd = [sys.executable, "run.py", "enrich"] + cmd_args
    
    print("🚀 Running enrichment pipeline...")
    print(f"📋 Command: {' '.join(cmd)}")
    print()
    
    # Run the command
    try:
        result = subprocess.run(cmd, check=True)
        print("\n✅ Enrichment completed successfully!")
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Enrichment failed with exit code {e.returncode}")
        return e.returncode
    except KeyboardInterrupt:
        print("\n\n⏹️  Enrichment interrupted by user")
        return 130

if __name__ == "__main__":
    sys.exit(main())
