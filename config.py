#!/usr/bin/env python3
"""
Configuration file for the Neurodivergent Resource Enrichment Toolkit.
All non-secret settings are defined here for easy management.
"""

from pathlib import Path
from typing import Dict, Any

# Base paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = PROJECT_ROOT / ".cache"
OUTPUT_DIR = DATA_DIR / "output"

# Default input/output files
DEFAULT_INPUT = DATA_DIR / "enriched" / "enriched_resources_20251101_080009.csv"
DEFAULT_OUTPUT = OUTPUT_DIR / "enriched_resources_complete.xlsx"

# LLM Configuration
LLM_CONFIG = {
    "backend": "gemini",  # Options: gemini, openai, ollama
    "model": None,  # Model name (None for default: gemini-1.5-flash)
    "enhance_with_websearch": True,  # Enable web search for missing contact info
    "cache_dir": ".cache/llm_extractions",
    "rate_limit": 15,  # requests per minute
}

# Processing Configuration
PROCESSING_CONFIG = {
    "workers": 10,  # Number of parallel workers
    "max_rows": 10,  # None for all rows, or specify number (default: 1 for testing)
    "start_row": 1,  # Starting row index (default: 150 for testing)
    "fields_to_check": "description_short,age_range,organization_type,neurodivergent_relevance,is_neurodivergent_related,category,conditions_supported,neurodivergent_focus",  # Fields to check for enrichment
    "skip_no_website": True,
    "populate_urls": True,
    "categorize": False,
    "input_file": "data/enriched/enriched_resources_20251101_080009.csv",  # Default input file
}

# Ollama Configuration (for local LLM)
OLLAMA_CONFIG = {
    "url": "http://localhost:11434",
    "auth": None,  # Set in .env if needed
}

# File Processing Configuration
FILE_CONFIG = {
    "input_encoding": "utf-8",  # Fallback encodings: utf-8-sig, latin-1, cp1252
    "output_format": "xlsx",  # Options: xlsx, csv
    "highlight_changes": True,
}

# Resource Categories (Simplified 9-Category System)
RESOURCE_CATEGORIES = [
    "Assessment & Diagnosis",
    "Crisis & Emergency", 
    "Education & Learning",
    "Employment",
    "Housing & Benefits",
    "Transport & Accessibility",
    "Community & Social",
    "Recreation & Activities",
    "Unknown/Uncategorized",
]

# Category Descriptions for LLM Understanding
CATEGORY_DESCRIPTIONS = {
    "Assessment & Diagnosis": "Diagnostic Centers, Assessment Clinics, Psychoeducational Evaluation",
    "Crisis & Emergency": "Crisis Helplines, Emergency Intervention, Mental Health Crisis Teams",
    "Education & Learning": "SEN Schools, Mainstream School Resources, Training Programs, Skills Development, Tutoring Services",
    "Employment": "Job Coaching, Workplace Accommodations, Vocational Training, Supported Employment",
    "Housing & Benefits": "Housing Assistance, Benefits Advice, Independent Living Programs, Welfare Navigation",
    "Transport & Accessibility": "Accessible Transport, Travel Training, Mobility Services, Transport Subsidies",
    "Community & Social": "Local Groups, National Organization Branches, Peer Networks, Social Meetups, Parent/Carer Groups",
    "Recreation & Activities": "Sports & Fitness, Arts & Entertainment, Play Centers, Hobby Clubs, Social Activities",
    "Unknown/Uncategorized": "Use only when the description doesn't clearly fit any category"
}

# Preset configurations for common use cases
PRESETS = {
    "quick_test": {
        "max_rows": 200,
        "workers": 20,
        "rate_limit": 10,
        "enhance_with_websearch": True,
    },
    "production": {
        "workers": 20,
        "rate_limit": 30,
        "enhance_with_websearch": True,
    },
    "conservative": {
        "workers": 3,
        "rate_limit": 10,
        "enhance_with_websearch": False,
    },
    "local_ollama": {
        "backend": "ollama",
        "model": "llama3.1:8b-instruct",
        "workers": 5,
        "rate_limit": 0,  # No rate limit for local
    }
}

def get_config(preset: str = None) -> Dict[str, Any]:
    """
    Get configuration with optional preset override.
    
    Args:
        preset: Name of preset to apply (quick_test, production, conservative, local_ollama)
    
    Returns:
        Combined configuration dictionary
    """
    config = {
        "llm": LLM_CONFIG.copy(),
        "processing": PROCESSING_CONFIG.copy(),
        "ollama": OLLAMA_CONFIG.copy(),
        "file": FILE_CONFIG.copy(),
    }
    
    if preset and preset in PRESETS:
        preset_config = PRESETS[preset]
        
        # Apply preset overrides
        for key, value in preset_config.items():
            if key in config["llm"]:
                config["llm"][key] = value
            elif key in config["processing"]:
                config["processing"][key] = value
            elif key in config["ollama"]:
                config["ollama"][key] = value
    
    return config

# Google Places Scraping Configuration
GOOGLE_PLACES_CONFIG = {
    "api_key_env": "GOOGLE_MAPS_API_KEY",
    "region": "gb",  # UK region bias
    "sleep_between_calls": 0.5,  # Rate limiting: seconds between API calls
    "cache_file": ".cache/google_places_scraping_cache.json",
    "requests_per_minute": 100,  # Conservative limit for Google Places API
    "max_searches": None,  # Maximum number of searches to perform (None = unlimited)
    "fetch_details": True,  # Whether to fetch detailed place information
    "max_results_per_search": 30,  # Lowered to limit spillover and duplicates
    
    # Parallel processing options
    "use_parallel": True,  # Enable parallel processing for faster scraping
    "max_workers": 5,  # Number of concurrent workers (be careful with rate limits!)
    "use_keyword_grouping": False,  # Group similar keywords to reduce API calls
    
    # Dedup/geo options
    "strict_geo_filter": True,  # Drop results outside radius
}
 
# Comprehensive list of keywords for neurodivergent resource discovery
SEARCH_KEYWORDS = [
    # Autism-specific
    "autism support center",
    "autism assessment clinic",
    "autism therapy",
    "autism diagnosis",
    "autism spectrum services",
    "ASD support",
    "autistic services",
    "autism charities",
    
    # ADHD-specific
    "ADHD assessment",
    "ADHD clinic",
    "ADHD support",
    "ADHD diagnosis",
    "ADHD therapy",
    "attention deficit services",
    
    # Learning disabilities and difficulties
    "learning disability support",
    "dyslexia support",
    "dyspraxia services",
    "special educational needs",
    "SEN support",
    "special needs center",
    
    # General neurodivergent
    "neurodivergent support",
    "neurodevelopmental services",
    "developmental disorders clinic",
    
    # Service types
    "special needs school",
    # "special education",
    "occupational therapy autism",
    "speech therapy autism",
    "behavioral therapy",
    "sensory processing support",
    
    # Employment and life skills
    "autism employment support",
    "supported employment neurodivergent",
    "autism job coaching",
    # "life skills training autism",
    
    # Social and community
    "autism social group",
    "autism community center",
    "autism support group",
    "autism parent support",
    "autism family support",
    
    # Diagnosis and assessment
    "autism diagnostic center",
    "neurodevelopmental assessment",
    
    # Specific organizations (common UK providers)
    "National Autistic Society",
    "Ambitious about Autism",
    "autism angels",
]

# UK Counties and Major Regions for systematic coverage
UK_REGIONS = [
    # England - Greater London (already covered, but keeping for completeness) - Completed
    {"name": "Greater London", "center": "London, UK", "radius_km": 25},
    
    # England - South East - Completed, some missing from this list
    {"name": "Kent", "center": "Maidstone, Kent, UK", "radius_km": 30},
    {"name": "Surrey", "center": "Guildford, Surrey, UK", "radius_km": 25},
    {"name": "East Sussex", "center": "Lewes, East Sussex, UK", "radius_km": 25},
    {"name": "West Sussex", "center": "Chichester, West Sussex, UK", "radius_km": 25},
    {"name": "Hampshire", "center": "Winchester, Hampshire, UK", "radius_km": 30},
    {"name": "Berkshire", "center": "Reading, Berkshire, UK", "radius_km": 25},
    {"name": "Buckinghamshire", "center": "Aylesbury, Buckinghamshire, UK", "radius_km": 25},
    {"name": "Oxfordshire", "center": "Oxford, Oxfordshire, UK", "radius_km": 25},
    {"name": "Hertfordshire", "center": "Hertford, Hertfordshire, UK", "radius_km": 25},
    {"name": "Essex", "center": "Chelmsford, Essex, UK", "radius_km": 30},
    
    # England - South West - Completed
    {"name": "Bristol", "center": "Bristol, UK", "radius_km": 20},
    {"name": "Somerset", "center": "Taunton, Somerset, UK", "radius_km": 30},
    {"name": "Devon", "center": "Exeter, Devon, UK", "radius_km": 35},
    {"name": "Cornwall", "center": "Truro, Cornwall, UK", "radius_km": 35},
    {"name": "Dorset", "center": "Dorchester, Dorset, UK", "radius_km": 25},
    {"name": "Wiltshire", "center": "Trowbridge, Wiltshire, UK", "radius_km": 25},
    {"name": "Gloucestershire", "center": "Gloucester, UK", "radius_km": 25},
    
    # England - Midlands
    {"name": "Birmingham", "center": "Birmingham, UK", "radius_km": 25},
    {"name": "West Midlands", "center": "Coventry, UK", "radius_km": 25},
    {"name": "Warwickshire", "center": "Warwick, UK", "radius_km": 25},
    {"name": "Staffordshire", "center": "Stafford, UK", "radius_km": 30},
    {"name": "Leicestershire", "center": "Leicester, UK", "radius_km": 25},
    {"name": "Nottinghamshire", "center": "Nottingham, UK", "radius_km": 25},
    {"name": "Derbyshire", "center": "Derby, UK", "radius_km": 25},
    {"name": "Northamptonshire", "center": "Northampton, UK", "radius_km": 25},
    {"name": "Worcestershire", "center": "Worcester, UK", "radius_km": 25},
    {"name": "Herefordshire", "center": "Hereford, UK", "radius_km": 20},
    {"name": "Shropshire", "center": "Shrewsbury, UK", "radius_km": 25},
    {"name": "Lincolnshire", "center": "Lincoln, UK", "radius_km": 30},
    
    # England - East
    {"name": "Cambridgeshire", "center": "Cambridge, UK", "radius_km": 25},
    {"name": "Norfolk", "center": "Norwich, UK", "radius_km": 30},
    {"name": "Suffolk", "center": "Ipswich, UK", "radius_km": 30},
    {"name": "Bedfordshire", "center": "Bedford, UK", "radius_km": 20},
    
    # England - North West
    {"name": "Greater Manchester", "center": "Manchester, UK", "radius_km": 25},
    {"name": "Liverpool", "center": "Liverpool, UK", "radius_km": 20},
    {"name": "Lancashire", "center": "Preston, UK", "radius_km": 30},
    {"name": "Cheshire", "center": "Chester, UK", "radius_km": 25},
    {"name": "Cumbria", "center": "Carlisle, UK", "radius_km": 35},
    {"name": "Merseyside", "center": "Liverpool, UK", "radius_km": 20},
    
    # England - North East
    {"name": "Newcastle", "center": "Newcastle upon Tyne, UK", "radius_km": 20},
    {"name": "Durham", "center": "Durham, UK", "radius_km": 25},
    {"name": "Northumberland", "center": "Morpeth, UK", "radius_km": 30},
    {"name": "Tyne and Wear", "center": "Newcastle upon Tyne, UK", "radius_km": 20},
    
    # England - Yorkshire
    {"name": "West Yorkshire", "center": "Leeds, UK", "radius_km": 25},
    {"name": "South Yorkshire", "center": "Sheffield, UK", "radius_km": 25},
    {"name": "North Yorkshire", "center": "York, UK", "radius_km": 30},
    {"name": "East Riding", "center": "Beverley, UK", "radius_km": 25},
    
    # Wales
    {"name": "Cardiff", "center": "Cardiff, Wales", "radius_km": 20},
    {"name": "Swansea", "center": "Swansea, Wales", "radius_km": 20},
    {"name": "Newport", "center": "Newport, Wales", "radius_km": 15},
    {"name": "North Wales", "center": "Bangor, Wales", "radius_km": 35},
    {"name": "Mid Wales", "center": "Aberystwyth, Wales", "radius_km": 35},
    {"name": "South Wales Valleys", "center": "Merthyr Tydfil, Wales", "radius_km": 25},
    
    # Scotland
    {"name": "Glasgow", "center": "Glasgow, Scotland", "radius_km": 20},
    {"name": "Edinburgh", "center": "Edinburgh, Scotland", "radius_km": 20},
    {"name": "Aberdeen", "center": "Aberdeen, Scotland", "radius_km": 20},
    {"name": "Dundee", "center": "Dundee, Scotland", "radius_km": 15},
    {"name": "Highlands", "center": "Inverness, Scotland", "radius_km": 40},
    {"name": "Fife", "center": "Glenrothes, Scotland", "radius_km": 25},
    {"name": "Ayrshire", "center": "Ayr, Scotland", "radius_km": 25},
    {"name": "Stirling", "center": "Stirling, Scotland", "radius_km": 20},
    
    # Northern Ireland
    {"name": "Belfast", "center": "Belfast, Northern Ireland", "radius_km": 20},
    {"name": "Derry", "center": "Derry, Northern Ireland", "radius_km": 15},
    {"name": "Antrim", "center": "Antrim, Northern Ireland", "radius_km": 20},
    {"name": "Down", "center": "Downpatrick, Northern Ireland", "radius_km": 20},
]

def get_command_args(config: Dict[str, Any], input_file: str = None, output_file: str = None) -> list:
    """
    Generate command line arguments from configuration.
    
    Args:
        config: Configuration dictionary
        input_file: Override input file path
        output_file: Override output file path
    
    Returns:
        List of command line arguments
    """
    args = []
    
    # Input/Output
    if input_file:
        args.extend(["--input", str(input_file)])
    if output_file:
        args.extend(["--output", str(output_file)])
    
    # LLM settings
    llm = config["llm"]
    if llm["backend"]:
        args.extend(["--backend", llm["backend"]])
    if llm["model"]:
        args.extend(["--model", llm["model"]])
    if llm["enhance_with_websearch"]:
        args.append("--enhance-with-websearch")
    if llm["cache_dir"]:
        args.extend(["--cache-dir", llm["cache_dir"]])
    if llm["rate_limit"]:
        args.extend(["--rate-limit", str(llm["rate_limit"])])
    
    # Processing settings
    proc = config["processing"]
    if proc["max_rows"]:
        args.extend(["--max-rows", str(proc["max_rows"])])
    if proc["start_row"]:
        args.extend(["--start-row", str(proc["start_row"])])
    if proc["fields_to_check"]:
        args.extend(["--fields-to-check", proc["fields_to_check"]])
    if proc["skip_no_website"]:
        args.append("--skip-no-website")
    if proc["workers"]:
        args.extend(["--workers", str(proc["workers"])])
    if proc["populate_urls"]:
        args.append("--populate-urls")
    if proc["categorize"]:
        args.append("--categorize")
    
    # Ollama settings (only if using Ollama backend)
    if llm["backend"] == "ollama":
        ollama = config["ollama"]
        if ollama["url"]:
            args.extend(["--ollama-url", ollama["url"]])
        if ollama["auth"]:
            args.extend(["--ollama-auth", ollama["auth"]])
    
    return args

# Example usage presets for UK expansion
UK_EXPANSION_PRESETS = {
    "test_single_region": {
        "max_searches": 5,
        "fetch_details": True,
        "requests_per_minute": 100,
    },
    "production_full_scan": {
        "max_searches": None,  # Unlimited
        "fetch_details": True,
        "requests_per_minute": 60,  # More conservative for large scans
    },
    "quick_scan_no_details": {
        "max_searches": 50,
        "fetch_details": False,  # Faster but less data
        "requests_per_minute": 100,
    },
}
