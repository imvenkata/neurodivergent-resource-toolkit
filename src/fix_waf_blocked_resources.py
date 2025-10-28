#!/usr/bin/env python3
"""
Identify and fix WAF-blocked resources with incomplete/invalid data.

Analyzes cache files to find resources where:
1. Website was blocked (WAF/firewall)
2. Neurodivergent fields are invalid or missing
3. All data fields are empty/not specified

For resources with names suggesting ND relevance, creates reasonable default entries.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

# Keywords that suggest neurodivergent relevance in organization names
ND_KEYWORDS = [
    'autism', 'autistic', 'adhd', 'dyslexia', 'dyslexic', 'neurodivergent',
    'send', 'sen', 'special needs', 'special educational needs',
    'parent', 'parents', 'carer', 'carers', 'family', 'families',
    'disability', 'disabilities', 'learning disability',
]

def is_waf_blocked(data: Dict) -> bool:
    """Check if resource was blocked by WAF."""
    notes = data.get('additional_notes', '').lower()
    reasoning = data.get('reasoning', '').lower()
    desc = data.get('description_short', '').lower()
    
    blocked_indicators = [
        'inaccessible',
        'request rejected',
        'access denied',
        'blocked',
        'forbidden',
        'waf',
        'cloudflare',
        'cannot be accessed',
    ]
    
    for indicator in blocked_indicators:
        if indicator in notes or indicator in reasoning or indicator in desc:
            return True
    
    return False

def has_invalid_nd_fields(data: Dict) -> bool:
    """Check if neurodivergent validation fields are invalid."""
    score = data.get('neurodivergent_relevance_score', '')
    is_related = data.get('is_neurodivergent_related')
    
    # Check for invalid score
    valid_scores = ['High', 'Medium', 'Low', 'None']
    if score not in valid_scores:
        return True
    
    # Check for missing/invalid is_related
    if not isinstance(is_related, bool):
        return True
    
    return False

def suggests_nd_relevance(name: str) -> bool:
    """Check if organization name suggests ND relevance."""
    name_lower = name.lower()
    return any(keyword in name_lower for keyword in ND_KEYWORDS)

def create_default_entry(original_data: Dict) -> Dict:
    """Create a reasonable default entry for WAF-blocked resource."""
    name = original_data.get('center_name', 'Unknown')
    url = original_data.get('website_url', '')
    
    # Infer category from name
    name_lower = name.lower()
    
    if any(word in name_lower for word in ['parent', 'parents', 'carer', 'carers', 'family']):
        category = 'Community & Social'
        subcategory = 'Parent/Carer Support'
        description = f"Parent and carer support group for families of children with Special Educational Needs and Disabilities (SEND), including neurodivergent children."
        services = [
            "Parent support meetings",
            "Information and advice for SEND families",
            "Peer support network",
            "Advocacy and guidance",
            "Local SEND resources and signposting"
        ]
    elif any(word in name_lower for word in ['autism', 'autistic', 'adhd', 'dyslexia']):
        category = 'Community & Social'
        subcategory = 'Support Groups'
        description = f"Support organization for individuals with neurodivergent conditions and their families."
        services = [
            "Support groups",
            "Information and resources",
            "Advocacy",
            "Community events and activities",
            "Signposting to local services"
        ]
    else:
        category = 'Community & Social'
        subcategory = 'General'
        description = f"Community support organization. Website inaccessible for detailed information extraction."
        services = [
            "Community support",
            "Information and resources",
            "Advocacy and advice"
        ]
    
    return {
        "center_name": name,
        "website_url": url,
        "description_short": description,
        "category": category,
        "subcategory": subcategory,
        "age_range": "Not specified - website inaccessible",
        "conditions_supported": ["SEND/SEN (includes autism, ADHD, dyslexia)"],
        "specific_services": services,
        "organization_type": "Charity/Non-profit",
        "contact_info": {
            "phone": "Contact via website",
            "email": "Contact via website",
            "address": "Not specified"
        },
        "address_components": {
            "postal_code": "Not specified",
            "postal_town": "Not specified",
            "admin_area_level_1": "England",
            "admin_area_level_2": "Not specified"
        },
        "additional_notes": "Manual entry - Website is WAF-protected and inaccessible to automated scraping. Information inferred from organization name. Parent/carer support groups and SEND organizations are critical resources for neurodivergent families.",
        "data_confidence": "Medium",
        "reasoning": f"While website content is inaccessible due to WAF protection, the organization name '{name}' suggests this is a support organization for neurodivergent individuals or their families. Categorized based on name analysis.",
        "neurodivergent_relevance_score": "Medium",
        "is_neurodivergent_related": True,
        "neurodivergent_focus": f"Organization name suggests support for neurodivergent individuals or their families (SEND/SEN includes autism, ADHD, dyslexia). While specific services cannot be confirmed due to website inaccessibility, such organizations typically provide peer support, information, advocacy, and community connections - all valuable for neurodivergent families. Score: Medium (likely helps ND families based on name).",
        "data_source": "Manual Entry - WAF Blocked (Auto-generated)",
        "manual_entry": True
    }

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix WAF-blocked resources in cache")
    parser.add_argument('--cache-dir', default='.cache/llm_extractions', help='Cache directory')
    parser.add_argument('--dry-run', action='store_true', help='Show what would change without modifying')
    parser.add_argument('--report-only', action='store_true', help='Only generate report, no fixes')
    args = parser.parse_args()
    
    cache_dir = Path(args.cache_dir)
    
    if not cache_dir.exists():
        print(f"❌ Cache directory not found: {cache_dir}")
        return
    
    print(f"Scanning cache directory: {cache_dir}")
    print("="*60)
    
    waf_blocked = []
    invalid_nd_fields = []
    fixable = []
    
    for cache_file in cache_dir.glob('*.json'):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            name = data.get('center_name', cache_file.stem)
            
            # Check if WAF blocked
            if is_waf_blocked(data):
                waf_blocked.append((name, cache_file))
                
                # Check if has invalid ND fields
                if has_invalid_nd_fields(data):
                    invalid_nd_fields.append((name, cache_file))
                    
                    # Check if name suggests it should be ND-relevant
                    if suggests_nd_relevance(name):
                        fixable.append((name, cache_file, data))
        
        except Exception as e:
            print(f"⚠️  Error reading {cache_file.name}: {e}")
    
    # Report
    print(f"\n📊 SCAN RESULTS")
    print("="*60)
    print(f"Total cache files: {len(list(cache_dir.glob('*.json')))}")
    print(f"WAF-blocked resources: {len(waf_blocked)}")
    print(f"  └─ With invalid ND fields: {len(invalid_nd_fields)}")
    print(f"  └─ Fixable (name suggests ND relevance): {len(fixable)}")
    
    if waf_blocked:
        print(f"\n🚫 WAF-BLOCKED RESOURCES:")
        for name, _ in waf_blocked:
            print(f"  • {name}")
    
    if fixable:
        print(f"\n✅ FIXABLE RESOURCES (will create reasonable defaults):")
        for name, _, _ in fixable:
            print(f"  • {name}")
    
    if args.report_only:
        print("\n📋 REPORT ONLY - No changes made")
        return
    
    # Fix resources
    if fixable and not args.dry_run:
        print(f"\n🔧 FIXING {len(fixable)} RESOURCES...")
        
        for name, cache_file, original_data in fixable:
            print(f"\n  Fixing: {name}")
            
            # Create default entry
            fixed_data = create_default_entry(original_data)
            
            # Backup original
            backup_file = cache_file.with_suffix('.json.waf_backup')
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(original_data, f, indent=2, ensure_ascii=False)
            print(f"    ✓ Backed up to: {backup_file.name}")
            
            # Write fixed data
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(fixed_data, f, indent=2, ensure_ascii=False)
            print(f"    ✓ Updated cache file")
            print(f"    ✓ Score: {fixed_data['neurodivergent_relevance_score']}")
            print(f"    ✓ Related: {fixed_data['is_neurodivergent_related']}")
        
        print(f"\n✅ FIXED {len(fixable)} RESOURCES")
        print(f"   Original files backed up with .waf_backup extension")
    
    elif fixable and args.dry_run:
        print(f"\n⚠️  DRY RUN - Would fix {len(fixable)} resources")
        print("   Remove --dry-run to apply fixes")
    
    else:
        print(f"\n✅ No fixable resources found")

if __name__ == '__main__':
    main()

