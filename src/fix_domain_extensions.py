#!/usr/bin/env python3
"""
Fix incorrect domain extensions in URLs.

Tries common UK TLD variants for domains that fail to resolve.
"""

import pandas as pd
import urllib.request
import urllib.error
import ssl
from urllib.parse import urlparse
import time

# Common UK TLD alternatives
UK_TLD_VARIANTS = [
    ('.com', '.uk'),
    ('.com', '.co.uk'),
    ('.com', '.org.uk'),
    ('.org', '.org.uk'),
    ('.org', '.uk'),
    ('.net', '.uk'),
    ('.net', '.co.uk'),
]

def check_url_exists(url: str, timeout: int = 10) -> bool:
    """Check if a URL exists and returns 200 OK."""
    try:
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'
        
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
        })
        
        # Try with SSL verification
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status == 200
        except ssl.SSLError:
            # Try without SSL verification
            context = ssl._create_unverified_context()
            with urllib.request.urlopen(req, timeout=timeout, context=context) as resp:
                return resp.status == 200
    except Exception:
        return False

def find_correct_tld(original_url: str) -> str:
    """
    Try to find the correct TLD for a URL that doesn't work.
    
    Args:
        original_url: URL that doesn't resolve
        
    Returns:
        Corrected URL if found, otherwise original URL
    """
    # Add protocol if missing
    if not original_url.startswith(('http://', 'https://')):
        test_url = f'https://{original_url}'
    else:
        test_url = original_url
    
    parsed = urlparse(test_url)
    domain = parsed.netloc or parsed.path.split('/')[0]
    
    # Extract base domain and current TLD
    parts = domain.rsplit('.', 1)
    if len(parts) != 2:
        return original_url
    
    base_domain, current_tld = parts
    current_tld = f'.{current_tld}'
    
    print(f"  Checking: {domain}")
    
    # Try UK TLD variants
    for old_tld, new_tld in UK_TLD_VARIANTS:
        if current_tld == old_tld:
            # Try the variant
            new_domain = f"{base_domain}{new_tld}"
            new_url = test_url.replace(domain, new_domain)
            
            print(f"    Trying: {new_domain}...", end=' ')
            if check_url_exists(new_url):
                print("✅ WORKS!")
                return new_url.replace('https://', '').replace('http://', '')
            else:
                print("❌ Failed")
            
            # Small delay to avoid rate limiting
            time.sleep(0.5)
    
    print("    ⚠️  No working variant found")
    return original_url

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix incorrect domain extensions in CSV")
    parser.add_argument('--input', required=True, help='Input CSV file')
    parser.add_argument('--output', required=True, help='Output CSV file')
    parser.add_argument('--url-column', default='gmaps_website', help='Name of URL column')
    parser.add_argument('--dry-run', action='store_true', help='Show what would change without modifying')
    args = parser.parse_args()
    
    print(f"Reading {args.input}...")
    df = pd.read_csv(args.input, encoding='latin-1', low_memory=False)
    
    print(f"Total resources: {len(df)}")
    
    # Find resources with URLs
    df_with_urls = df[df[args.url_column].notna() & (df[args.url_column] != '')]
    print(f"Resources with URLs: {len(df_with_urls)}")
    
    # Check which URLs don't work
    print("\nChecking URLs and finding corrections...")
    corrections = []
    
    for idx, row in df_with_urls.iterrows():
        original_url = str(row[args.url_column]).strip()
        
        # Skip if already has correct protocol
        if original_url.startswith('http'):
            continue
        
        # Add protocol for testing
        test_url = original_url if original_url.startswith(('http://', 'https://')) else f'https://{original_url}'
        
        # Check if original URL works
        print(f"\n[{idx}] {row.get('gmaps_name', 'Unknown')}")
        print(f"  Original: {original_url}")
        
        if check_url_exists(test_url):
            print("  ✅ Original URL works - no change needed")
            continue
        
        # Try to find correct TLD
        print("  ❌ Original URL doesn't work - trying variants...")
        corrected_url = find_correct_tld(original_url)
        
        if corrected_url != original_url:
            corrections.append({
                'index': idx,
                'name': row.get('gmaps_name', 'Unknown'),
                'original': original_url,
                'corrected': corrected_url
            })
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"URLs checked: {len(df_with_urls)}")
    print(f"Corrections found: {len(corrections)}")
    
    if corrections:
        print("\nCorrections:")
        for c in corrections:
            print(f"  [{c['index']}] {c['name']}")
            print(f"    OLD: {c['original']}")
            print(f"    NEW: {c['corrected']}")
            print()
    
    # Apply corrections
    if not args.dry_run and corrections:
        print(f"Applying {len(corrections)} corrections...")
        for c in corrections:
            df.at[c['index'], args.url_column] = c['corrected']
        
        print(f"Saving to {args.output}...")
        df.to_csv(args.output, index=False, encoding='utf-8')
        print("✅ Done!")
    elif args.dry_run:
        print("\n⚠️  DRY RUN - No changes made. Remove --dry-run to apply corrections.")
    else:
        print("\n✅ No corrections needed!")

if __name__ == '__main__':
    main()

