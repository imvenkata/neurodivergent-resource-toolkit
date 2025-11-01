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
    
    # Recreational/Educational (generic)
    r'\bcity farm\b' + r'(?!.*autism|adhd|send|sen|special needs|neurodiv)',
    r'\bfarm\b' + r'(?!.*autism|adhd|send|sen|special needs|neurodiv|rda|disabled)',
    r'\bcountry park\b' + r'(?!.*send|sen|special needs|autism|adhd|neurodiv)',
    r'\bpark\b' + r'(?!.*send|sen|special needs|autism|adhd|neurodiv)',
    r'\byouth center\b' + r'(?!.*send|sen|special needs|autism|adhd|neurodiv)',
    r'\byouth centre\b' + r'(?!.*send|sen|special needs|autism|adhd|neurodiv)',
    r'\bcommunity center\b' + r'(?!.*send|sen|special needs|autism|adhd|neurodiv)',
    r'\bcommunity centre\b' + r'(?!.*send|sen|special needs|autism|adhd|neurodiv)',
    r'\brecreation center\b' + r'(?!.*send|sen|special needs|autism|adhd|neurodiv)',
    r'\brecreation centre\b' + r'(?!.*send|sen|special needs|autism|adhd|neurodiv)',
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
    
    Generic services (councils, transport, etc.) are ALWAYS generic unless
    they have VERY specific ND services in the name itself (e.g., "Autism Assessment Centre")
    """
    text = f"{name} {description} {focus}".lower()
    
    # STRICT: Councils and government services are ALWAYS generic unless name has specific ND keywords
    # (e.g., "Hammersmith Autism Support" would be OK, but "Hammersmith Council" is not)
    council_patterns = [r'\bcouncil\b', r'\bborough\b', r'\blocal authority\b', r'\bgovernment\b']
    is_council = any(re.search(pattern, text, re.IGNORECASE) for pattern in council_patterns)
    
    if is_council:
        # Only allow if the NAME itself contains specific ND keywords (not just description)
        # This catches things like "Hammersmith Autism Assessment Centre" but rejects "Hammersmith Council"
        specific_nd_keywords = [r'\bautis[mt]\b', r'\bASD\b', r'\bASC\b', r'\bADHD\b', r'\bADD\b', 
                               r'\bdyslex\w*\b', r'\bdysprax\w*\b', r'\bSEN\b', r'\bSEND\b']
        name_has_specific_nd = any(
            re.search(pattern, name, re.IGNORECASE) 
            for pattern in specific_nd_keywords
        )
        if not name_has_specific_nd:
            return True  # Council without specific ND in name = always generic
    
    # Check for other generic service keywords
    for pattern in GENERIC_SERVICE_KEYWORDS:
        if re.search(pattern, text, re.IGNORECASE):
            # For non-council generic services, check if it has explicit ND keywords
            # But be stricter - exclude generic terms like "disabilities" or "learning disabilities"
            specific_nd_keywords = [r'\bautis[mt]\b', r'\bASD\b', r'\bASC\b', r'\bADHD\b', r'\bADD\b',
                                   r'\bdyslex\w*\b', r'\bdysprax\w*\b', r'\bDCD\b',
                                   r'\bneurodiverg\w*\b', r'\bneurodivers\w*\b',
                                   r'\bSEN\b', r'\bSEND\b', r'\bspecial educational needs\b',
                                   r'\bAsperger\b', r'\bTourette\b']
            has_specific_nd = any(
                re.search(nd_pattern, text, re.IGNORECASE) 
                for nd_pattern in specific_nd_keywords
            )
            # Exclude generic terms - "disabilities" or "learning disabilities" alone don't count
            has_generic_only = re.search(r'\bdisabilit\w*\b', text, re.IGNORECASE) and not has_specific_nd
            
            if not has_specific_nd or has_generic_only:
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
    
    # Convert services to string for searching
    services_text = " ".join(services) if isinstance(services, list) else str(services)
    
    # Step 1: Check if it's a generic service (false positive)
    if is_generic_service(name, description, focus):
        return False, "None", "Generic service (not ND-specific) - false positive"
    
    # Step 2: STRICT RULE - Check conditions_supported - filter out generic terms
    # Generic terms like "Disabilities" or "Learning Disabilities" don't count as explicit ND
    all_text = f"{name} {description} {focus} {services_text}".lower()
    
    # Specific ND keywords (exclude generic terms)
    specific_nd_patterns = [
        r'\bautis[mt]\b', r'\bASD\b', r'\bASC\b',
        r'\bADHD\b', r'\bADD\b', r'\battention deficit\b',
        r'\bdyslex\w*\b', r'\bdysprax\w*\b', r'\bDCD\b',
        r'\bneurodiverg\w*\b', r'\bneurodivers\w*\b',
        r'\bSEN\b', r'\bSEND\b', r'\bspecial educational needs\b',
        r'\bAsperger\b', r'\bTourette\b',
        r'\bautism spectrum\b', r'\bautistic spectrum\b',
    ]
    
    has_explicit_nd = any(
        re.search(pattern, all_text, re.IGNORECASE)
        for pattern in specific_nd_patterns
    )
    
    # Check if conditions contain only generic terms
    if conditions and len(conditions) > 0:
        conditions_text = " ".join(conditions) if isinstance(conditions, list) else str(conditions)
        # Filter out generic conditions - only count specific ND conditions
        has_specific_conditions = any(
            re.search(pattern, conditions_text, re.IGNORECASE)
            for pattern in specific_nd_patterns
        )
        # If conditions only have generic terms (disabilities, learning disabilities), treat as empty
        if not has_specific_conditions and re.search(r'\bdisabilit\w*\b', conditions_text, re.IGNORECASE):
            conditions = []  # Treat as empty - generic terms don't count
    
    # Also check for explicit SEND/SEN/autism-friendly mentions in services
    has_explicit_programs = any(
        keyword in services_text.lower()
        for keyword in ["send", "sen", "autism-friendly", "sensory-friendly", 
                       "special needs", "for disabled", "neurodivergent-friendly"]
    )
    
    if (not conditions or len(conditions) == 0):
        if not has_explicit_nd and not has_explicit_programs:
            # Empty conditions AND no explicit ND keywords = must be Low or None
            return False, "Low", "Empty conditions_supported and no explicit ND keywords/programs found"
    
    # Step 3: Check if it has genuine ND focus (requires explicit keywords or populated conditions)
    if not has_true_nd_focus(name, description, conditions, services):
        # Double-check: maybe it has conditions but no keywords (edge case)
        if conditions and len(conditions) > 0:
            # Has conditions but no keywords - might be legit, but be cautious
            # Check if conditions actually mention ND conditions
            conditions_text = " ".join(conditions) if isinstance(conditions, list) else str(conditions)
            has_nd_in_conditions = any(
                re.search(pattern, conditions_text, re.IGNORECASE)
                for pattern in TRUE_ND_KEYWORDS
            )
            if has_nd_in_conditions:
                # Conditions mention ND - allow Medium score
                pass
            else:
                return False, "Low", "No clear neurodivergent focus despite conditions list"
        else:
            return False, "Low", "No clear neurodivergent focus"
    
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
        # Has some ND keywords but no conditions - be cautious, might be Medium if explicit programs exist
        if has_explicit_nd or has_explicit_programs:
            return True, "Medium", "Explicit ND programs/services mentioned"
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

