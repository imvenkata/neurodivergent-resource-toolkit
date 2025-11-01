#!/usr/bin/env python3
"""
Helper script to view and manage content cache files.
Shows all cached website and web search content.
"""

import json
import sys
from pathlib import Path
from typing import Optional

def list_content_cache_files(cache_dir: str = ".cache/content") -> list:
    """List all content cache files."""
    cache_path = Path(cache_dir)
    if not cache_path.exists():
        return []
    return sorted(cache_path.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)

def show_content_cache(center_name: Optional[str] = None, cache_dir: str = ".cache/content"):
    """Show content cache files and their contents."""
    files = list_content_cache_files(cache_dir)
    
    if not files:
        print("No content cache files found.")
        return
    
    print(f"Found {len(files)} content cache file(s):\n")
    
    for cache_file in files:
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            cache_center = data.get("center_name", "Unknown")
            cache_url = data.get("website_url", "Unknown")
            website_text_len = len(data.get("website_text", ""))
            web_search_len = len(data.get("web_search_text", ""))
            website_pages = len(data.get("website_pages", []))
            web_search_sources = len(data.get("web_search_sources", []))
            
            # Filter by center name if provided
            if center_name and center_name.lower() not in cache_center.lower():
                continue
            
            print(f"📄 {cache_file.name}")
            print(f"   Center: {cache_center}")
            print(f"   URL: {cache_url}")
            print(f"   Website text: {website_text_len:,} chars ({website_pages} pages)")
            print(f"   Web search text: {web_search_len:,} chars ({web_search_sources} sources)")
            
            # Show preview
            website_text = data.get("website_text", "")
            if website_text:
                preview = website_text[:200].replace('\n', ' ').strip()
                print(f"   Preview: {preview}...")
            
            print()
        except Exception as e:
            print(f"⚠️  Error reading {cache_file.name}: {e}\n")

if __name__ == "__main__":
    center_filter = sys.argv[1] if len(sys.argv) > 1 else None
    show_content_cache(center_filter)

