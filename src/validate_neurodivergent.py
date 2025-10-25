#!/usr/bin/env python3
"""
Post-process LLM validation to catch false positives
Apply stricter rules to ensure only genuine ND services are included
"""

import json
import re
from pathlib import Path
from typing import Dict, Tuple

# Services that are NEVER neurodivergent-specific (even if they have accessibility)
GENERIC_SERVICE_KEYWORDS = [
    # Transport
    r'\btransport for\b', r'\btfl\b', r'\bbus service\b', r'\btrain service\b',
    r'\bunderground\b', r'\btube service\b', r'\bpublic transport\b',
    
    # Government
    r'\bcouncil\b', r'\bborough\b', r'\btown hall\b', r'\blocal authority\b',
    r'\bgovernment\b', r'\bmunicipality\b',
    
    # Healthcare (general)
    r'\bgp surgery\b', r'\bgeneral practice\b', r'\bpharmacy\b', r'\bdentist\b',
    r'\boptician\b', r'\bhospital\b' + r'(?!.*autism|adhd|neurodiv)',
    
    # Education (general)
    r'\buniversity\b' + r'(?!.*autism|adhd|neurodiv)',
    r'\bcollege\b' + r'(?!.*autism|adhd|neurodiv)',
    r'\blibrary\b' + r'(?!.*autism|adhd|neurodiv)',
    
    # Entertainment (general)
    r'\bmuseum\b' + r'(?!.*autism|adhd|neurodiv)',
    r'\btheatre\b' + r'(?!.*autism|adhd|neurodiv)',
    r'\bcinema\b' + r'(?!.*autism|adhd|neurodiv)',
    r'\bsports club\b' + r'(?!.*autism|adhd|neurodiv)',
    r'\bgym\b' + r'(?!.*autism|adhd|neurodiv)',
]

# Keywords that indicate TRUE neurodivergent focus
TRUE_ND_KEYWORDS = [
    r'\bautis[mt]\b', r'\bASD\b', r'\bASC\b',
    r'\bADHD\b', r'\bADD\b', r'\battention deficit\b',
    r'\bdyslex\w*\b', r'\bdysprax\w*\b', r'\bDCD\b',
    r'\bneurodiverg\w*\b', r'\bneurodivers\w*\b',
    r'\bSEN\b', r'\bSEND\b', r'\bspecial educational needs\b',
    r'\blearning disabilit\w*\b', r'\blearning difficult\w*\b',
    r'\bAsperger\b', r'\bTourette\b',
    r'\bautism spectrum\b', r'\bautistic spectrum\b',
]

def is_generic_service(name: str, description: str, focus: str) -> bool:
    """
    Check if this is a GENERIC service (not ND-specific)
    Returns True if it's a false positive
    """
    text = f"{name} {description} {focus}".lower()
    
    # Check for generic service keywords
    for pattern in GENERIC_SERVICE_KEYWORDS:
        if re.search(pattern, text, re.IGNORECASE):
            # It's a generic service UNLESS it has explicit ND keywords
            has_nd_keywords = any(
                re.search(nd_pattern, text, re.IGNORECASE) 
                for nd_pattern in TRUE_ND_KEYWORDS
            )
            if not has_nd_keywords:
                return True  # False positive!
    
    return False

def has_true_nd_focus(name: str, description: str, conditions: list, services: list) -> bool:
    """
    Check if service has GENUINE neurodivergent focus
    """
    text = f"{name} {description} {' '.join(conditions)} {' '.join(services)}".lower()
    
    # Must have at least 2 ND keywords OR 1 ND keyword in name
    nd_keyword_count = sum(
        1 for pattern in TRUE_ND_KEYWORDS 
        if re.search(pattern, text, re.IGNORECASE)
    )
    
    has_nd_in_name = any(
        re.search(pattern, name, re.IGNORECASE)
        for pattern in TRUE_ND_KEYWORDS
    )
    
    return has_nd_in_name or nd_keyword_count >= 2

def revalidate_resource(data: Dict) -> Tuple[bool, str, str]:
    """
    Apply stricter validation rules
    Returns: (is_nd_related, relevance_score, reason)
    """
    name = data.get("center_name", "")
    description = data.get("description_short", "")
    focus = data.get("neurodivergent_focus", "")
    conditions = data.get("conditions_supported", [])
    services = data.get("specific_services", [])
    
    # Step 1: Check if it's a generic service (false positive)
    if is_generic_service(name, description, focus):
        return False, "None", "Generic service (not ND-specific) - false positive"
    
    # Step 2: Check if it has genuine ND focus
    if not has_true_nd_focus(name, description, conditions, services):
        return False, "Low", "No clear neurodivergent focus"
    
    # Step 3: Check conditions_supported
    if not conditions or len(conditions) == 0:
        # No conditions specified - likely not ND-focused
        return False, "Low", "No neurodivergent conditions specified"
    
    # Step 4: If passed all checks, determine relevance level
    nd_keywords_in_name = any(
        re.search(pattern, name, re.IGNORECASE)
        for pattern in TRUE_ND_KEYWORDS
    )
    
    if nd_keywords_in_name:
        return True, "High", "Explicitly neurodivergent-focused (in name)"
    elif len(conditions) >= 2:
        return True, "High", "Multiple ND conditions supported"
    elif len(conditions) == 1:
        return True, "Medium", "Single ND condition supported"
    else:
        return True, "Medium", "Some ND support offered"

def validate_cache_file(cache_path: Path) -> Dict:
    """
    Re-validate a cached LLM extraction
    """
    with open(cache_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Get original validation
    original_related = data.get("is_neurodivergent_related", False)
    original_score = data.get("neurodivergent_relevance_score", "Unknown")
    
    # Apply strict rules
    is_related, score, reason = revalidate_resource(data)
    
    # Update if different
    if is_related != original_related or score != original_score:
        data["is_neurodivergent_related"] = is_related
        data["neurodivergent_relevance_score"] = score
        data["validation_override"] = reason
        data["original_validation"] = {
            "is_neurodivergent_related": original_related,
            "neurodivergent_relevance_score": original_score
        }
        
        # Save updated cache
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return {
            "changed": True,
            "name": data.get("center_name"),
            "old_score": original_score,
            "new_score": score,
            "reason": reason
        }
    
    return {"changed": False}

def validate_all_cache_files(cache_dir: Path = Path(".cache/llm_extractions")):
    """
    Re-validate all cached extractions
    """
    if not cache_dir.exists():
        print(f"Cache directory not found: {cache_dir}")
        return
    
    cache_files = list(cache_dir.glob("*.json"))
    print(f"\n🔍 Re-validating {len(cache_files)} cached resources...")
    print("="*70)
    
    changes = []
    for cache_file in cache_files:
        result = validate_cache_file(cache_file)
        if result.get("changed"):
            changes.append(result)
    
    print(f"\n✅ Validation complete!")
    print(f"   Total files checked: {len(cache_files)}")
    print(f"   Changed: {len(changes)}")
    print(f"   Unchanged: {len(cache_files) - len(changes)}")
    
    if changes:
        print(f"\n📊 VALIDATION CHANGES:")
        print("="*70)
        
        # Group by reason
        from collections import Counter
        reasons = Counter(c['reason'] for c in changes)
        
        print(f"\nChange reasons:")
        for reason, count in reasons.most_common():
            print(f"  • {reason}: {count}")
        
        print(f"\nDetailed changes:")
        for change in changes[:20]:  # Show first 20
            print(f"\n  {change['name']}")
            print(f"    {change['old_score']} → {change['new_score']}")
            print(f"    Reason: {change['reason']}")
        
        if len(changes) > 20:
            print(f"\n  ... and {len(changes) - 20} more changes")
    
    print("="*70)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Re-validate cached ND resources")
    parser.add_argument("--cache-dir", default=".cache/llm_extractions",
                       help="Path to cache directory")
    parser.add_argument("--file", help="Validate single file")
    
    args = parser.parse_args()
    
    if args.file:
        result = validate_cache_file(Path(args.file))
        if result.get("changed"):
            print(f"✅ Updated: {result['name']}")
            print(f"   {result['old_score']} → {result['new_score']}")
            print(f"   Reason: {result['reason']}")
        else:
            print("No changes needed")
    else:
        validate_all_cache_files(Path(args.cache_dir))

