#!/usr/bin/env python3
"""
Category and Subcategory Standardization Module

This module provides functions to standardize resource categories and subcategories,
ensuring consistency across the dataset and mapping subcategories to correct categories.
"""

from typing import Dict, List, Optional, Tuple


# ============================================================================
# STANDARDIZED CATEGORIES (10 categories)
# ============================================================================

STANDARD_CATEGORIES = [
    "Assessment & Diagnosis",
    "Crisis & Emergency",
    "Education & Learning",
    "Employment",
    "Housing & Benefits",
    "Transport & Accessibility",
    "Community & Social",
    "Recreation & Activities",
    "Mental Health & Wellbeing",
    "Unknown/Uncategorized",
]

# Note: "Therapeutic Services" is merged into "Mental Health & Wellbeing" 
# and "Assessment & Diagnosis" depending on context


# ============================================================================
# CATEGORY MAPPING (old -> standard)
# ============================================================================

CATEGORY_MAPPING: Dict[str, str] = {
    # Direct matches (keep as-is)
    "Assessment & Diagnosis": "Assessment & Diagnosis",
    "Crisis & Emergency": "Crisis & Emergency",
    "Education & Learning": "Education & Learning",
    "Employment": "Employment",
    "Housing & Benefits": "Housing & Benefits",
    "Transport & Accessibility": "Transport & Accessibility",
    "Community & Social": "Community & Social",
    "Recreation & Activities": "Recreation & Activities",
    "Unknown/Uncategorized": "Unknown/Uncategorized",
    
    # Mental Health variants -> Mental Health & Wellbeing
    "Mental health support": "Mental Health & Wellbeing",
    "Mental Health & Wellbeing": "Mental Health & Wellbeing",
    "Mental Health & Therapy": "Mental Health & Wellbeing",
    "Mental Health": "Mental Health & Wellbeing",
    
    # Therapeutic Services -> Mental Health & Wellbeing (most cases)
    "Therapeutic Services": "Mental Health & Wellbeing",
    
    # Health -> Mental Health & Wellbeing (if mental health related) or Unknown
    "Health": "Mental Health & Wellbeing",  # Default assumption, can be refined
    
    # Legacy categories (from old system)
    "Community Support": "Community & Social",
    "Education Support": "Education & Learning",
    "Employment Support": "Employment",
    "Housing Support": "Housing & Benefits",
    "Benefits Support": "Housing & Benefits",
    "Transport Support": "Transport & Accessibility",
    "Autism Friendly Entertainment": "Recreation & Activities",
    "Local Support Services and Groups": "Community & Social",
    "Employment and Skills Services": "Employment",
    "National Autistic Society Branches": "Community & Social",
    "Autism Friendly Sports Activities": "Recreation & Activities",
    "Special Needs Play Centres": "Recreation & Activities",
    "Special Interests and Hobbies": "Recreation & Activities",
    "Unknown Category": "Unknown/Uncategorized",
}


# ============================================================================
# STANDARDIZED SUBCATEGORIES BY CATEGORY
# ============================================================================

STANDARD_SUBCATEGORIES: Dict[str, List[str]] = {
    "Assessment & Diagnosis": [
        "Diagnostic Assessment",
        "Diagnostic Clinics",
        "Diagnostic Centers",
        "Assessment Clinics",
        "Assessment & Screening",
        "Psychoeducational Evaluation",
        "Neurodevelopmental Assessment",
        "ADHD Assessment",
        "Autism Assessment",
        "Dyslexia Assessment",
        "Developmental Assessment",
        "Psychological Assessment",
        "Psychiatric Assessment",
        "Occupational Therapy Assessment",
        "Speech & Language Assessment",
        "General Assessment",
    ],
    
    "Crisis & Emergency": [
        "Crisis Helplines",
        "Crisis Intervention",
        "Emergency Intervention",
        "Mental Health Crisis Teams",
        "Crisis Support Services",
        "Crisis Counselling",
        "Suicide Prevention",
        "Emergency Mental Health",
        "General Crisis Support",
    ],
    
    "Education & Learning": [
        "SEN Schools",
        "Special Educational Needs (SEN)",
        "Special Educational Needs (SEND)",
        "Alternative Provision",
        "Alternative Education",
        "Mainstream Resources",
        "Tutoring",
        "Skills Development",
        "Training",
        "Educational Support Services",
        "Early Years Education",
        "Further Education",
        "Higher Education",
        "Educational Psychology",
        "Learning Support",
        "Literacy Support",
        "Dyslexia Support",
        "General Education Support",
    ],
    
    "Employment": [
        "Job Coaching",
        "Workplace Accommodations",
        "Vocational Training",
        "Supported Employment",
        "Employment Support Services",
        "Workplace Training & Consultancy",
        "Career Guidance",
        "Employment Rights & Advice",
        "Recruitment Services",
        "General Employment Support",
    ],
    
    "Housing & Benefits": [
        "Housing Assistance",
        "Benefits Advice",
        "Welfare Navigation",
        "Independent Living",
        "Residential Care",
        "Supported Living",
        "Respite Care",
        "Short Breaks",
        "Financial Assistance",
        "General Housing & Benefits Support",
    ],
    
    "Transport & Accessibility": [
        "Accessible Transport",
        "Travel Training",
        "Mobility Services",
        "Mobility Equipment",
        "Accessibility Services",
        "Accessibility Information",
        "Accessibility Consulting",
        "General Transport Support",
    ],
    
    "Community & Social": [
        "Local Groups",
        "Organization Branches",
        "Peer Networks",
        "Support Groups",
        "Parent/Carer Groups",
        "Social Clubs",
        "Social Activities",
        "Meetups",
        "Advocacy",
        "Advocacy Groups",
        "Self-Advocacy",
        "Community Support Services",
        "Family Support",
        "Carer Support",
        "General Community Support",
    ],
    
    "Recreation & Activities": [
        "Sports & Fitness",
        "Arts & Entertainment",
        "Play Centers",
        "Hobby Clubs",
        "Outdoor Activities",
        "Adventure Sports",
        "Adaptive Sports",
        "Accessible Recreation",
        "Therapeutic Activities",
        "Social Activities",
        "General Recreation",
    ],
    
    "Mental Health & Wellbeing": [
        "Mental Health Support",
        "Mental Health Therapy",
        "Mental Health Counselling",
        "Mental Health Assessment",
        "Mental Health Services",
        "CBT (Cognitive Behavioural Therapy)",
        "Psychotherapy",
        "Counselling",
        "Therapy",
        "Therapy Services",
        "Occupational Therapy",
        "Speech & Language Therapy",
        "Physiotherapy",
        "Play Therapy",
        "Art Therapy",
        "Music Therapy",
        "Creative Therapy",
        "Trauma Therapy",
        "Trauma Support",
        "Eating Disorder Therapy",
        "Addiction Therapy",
        "Child & Adolescent Mental Health",
        "Adult Mental Health",
        "Inpatient Mental Health",
        "Outpatient Mental Health",
        "Day Services",
        "Rehabilitation",
        "Wellbeing Support",
        "General Mental Health Support",
    ],
    
    "Unknown/Uncategorized": [
        "General",
        "Uncategorized",
    ],
}


# ============================================================================
# SUBCATEGORY MAPPING (old -> standard)
# ============================================================================

def _build_subcategory_mapping() -> Dict[str, Tuple[str, str]]:
    """
    Build a mapping from old subcategory values to (standard_subcategory, category) tuples.
    Returns a dictionary mapping old_subcategory -> (standard_subcategory, category).
    """
    mapping: Dict[str, Tuple[str, str]] = {}
    
    # Build reverse mapping from standard subcategories
    for category, subcats in STANDARD_SUBCATEGORIES.items():
        for subcat in subcats:
            # Map exact match
            mapping[subcat] = (subcat, category)
            # Map lowercase version
            mapping[subcat.lower()] = (subcat, category)
    
    # Add specific mappings for common variations
    # Assessment & Diagnosis
    mapping.update({
        "Assessment & Diagnosis": ("Diagnostic Assessment", "Assessment & Diagnosis"),
        "Assessment & Screening": ("Assessment & Screening", "Assessment & Diagnosis"),
        "Diagnostic Assessments": ("Diagnostic Assessment", "Assessment & Diagnosis"),
        "Diagnostic Centers": ("Diagnostic Centers", "Assessment & Diagnosis"),
        "Diagnostic Clinics": ("Diagnostic Clinics", "Assessment & Diagnosis"),
        "Assessment Clinics": ("Assessment Clinics", "Assessment & Diagnosis"),
        "Assessment Clinic": ("Assessment Clinics", "Assessment & Diagnosis"),
        "Psychoeducational Evaluation": ("Psychoeducational Evaluation", "Assessment & Diagnosis"),
        "Neurodevelopmental Assessment": ("Neurodevelopmental Assessment", "Assessment & Diagnosis"),
        "Neurodevelopmental Assessments": ("Neurodevelopmental Assessment", "Assessment & Diagnosis"),
        "ADHD Assessment": ("ADHD Assessment", "Assessment & Diagnosis"),
        "ADHD Assessment/Support": ("ADHD Assessment", "Assessment & Diagnosis"),
        "ADHD Assessment & Treatment": ("ADHD Assessment", "Assessment & Diagnosis"),
        "Autism Assessment": ("Autism Assessment", "Assessment & Diagnosis"),
        "Dyslexia Assessment": ("Dyslexia Assessment", "Assessment & Diagnosis"),
        "Dyslexia Assessment & Support": ("Dyslexia Assessment", "Assessment & Diagnosis"),
        "Developmental Assessment": ("Developmental Assessment", "Assessment & Diagnosis"),
        "Psychological Assessment": ("Psychological Assessment", "Assessment & Diagnosis"),
        "Psychiatric Assessment": ("Psychiatric Assessment", "Assessment & Diagnosis"),
        "Occupational Therapy Assessment": ("Occupational Therapy Assessment", "Assessment & Diagnosis"),
        "Occupational Therapy Assessments": ("Occupational Therapy Assessment", "Assessment & Diagnosis"),
        "Occupational Therapy Assessment": ("Occupational Therapy Assessment", "Assessment & Diagnosis"),
        "Speech & Language Assessment": ("Speech & Language Assessment", "Assessment & Diagnosis"),
        "Speech and Language Therapy, Diagnostic Assessments": ("Speech & Language Assessment", "Assessment & Diagnosis"),
    })
    
    # Crisis & Emergency
    mapping.update({
        "Crisis & Emergency": ("Crisis Helplines", "Crisis & Emergency"),
        "Crisis Helplines": ("Crisis Helplines", "Crisis & Emergency"),
        "Crisis Helplines & Intervention": ("Crisis Intervention", "Crisis & Emergency"),
        "Crisis Intervention": ("Crisis Intervention", "Crisis & Emergency"),
        "Crisis Intervention & Support": ("Crisis Intervention", "Crisis & Emergency"),
        "Emergency Intervention": ("Emergency Intervention", "Crisis & Emergency"),
        "Mental Health Crisis Teams": ("Mental Health Crisis Teams", "Crisis & Emergency"),
        "Mental Health Crisis Support": ("Mental Health Crisis Teams", "Crisis & Emergency"),
        "Mental Health Crisis Services": ("Mental Health Crisis Teams", "Crisis & Emergency"),
        "Crisis Support Services": ("Crisis Support Services", "Crisis & Emergency"),
        "Crisis Counselling": ("Crisis Counselling", "Crisis & Emergency"),
    })
    
    # Education & Learning
    mapping.update({
        "Education & Learning": ("General Education Support", "Education & Learning"),
        "SEN Schools": ("SEN Schools", "Education & Learning"),
        "SEN Support": ("Special Educational Needs (SEN)", "Education & Learning"),
        "SEND Support": ("Special Educational Needs (SEND)", "Education & Learning"),
        "Special Educational Needs": ("Special Educational Needs (SEN)", "Education & Learning"),
        "Special Educational Needs (SEN)": ("Special Educational Needs (SEN)", "Education & Learning"),
        "Special Educational Needs (SEND)": ("Special Educational Needs (SEND)", "Education & Learning"),
        "Alternative Provision": ("Alternative Provision", "Education & Learning"),
        "Alternative Education": ("Alternative Education", "Education & Learning"),
        "Tutoring": ("Tutoring", "Education & Learning"),
        "Tutoring & Skills Development": ("Tutoring", "Education & Learning"),
        "Skills Development": ("Skills Development", "Education & Learning"),
        "Training": ("Training", "Education & Learning"),
        "Training & Skills Development": ("Training", "Education & Learning"),
        "Educational Support Services": ("Educational Support Services", "Education & Learning"),
        "Early Years Education": ("Early Years Education", "Education & Learning"),
        "Further Education": ("Further Education", "Education & Learning"),
        "Higher Education": ("Higher Education", "Education & Learning"),
        "Educational Psychology": ("Educational Psychology", "Education & Learning"),
        "Learning Support": ("Learning Support", "Education & Learning"),
        "Literacy Support": ("Literacy Support", "Education & Learning"),
        "Dyslexia Support": ("Dyslexia Support", "Education & Learning"),
    })
    
    # Employment
    mapping.update({
        "Employment": ("General Employment Support", "Employment"),
        "Job Coaching": ("Job Coaching", "Employment"),
        "Workplace Accommodations": ("Workplace Accommodations", "Employment"),
        "Vocational Training": ("Vocational Training", "Employment"),
        "Supported Employment": ("Supported Employment", "Employment"),
        "Employment Support Services": ("Employment Support Services", "Employment"),
        "Workplace Training & Consultancy": ("Workplace Training & Consultancy", "Employment"),
        "Career Guidance": ("Career Guidance", "Employment"),
        "Employment Rights & Advice": ("Employment Rights & Advice", "Employment"),
        "Recruitment Services": ("Recruitment Services", "Employment"),
    })
    
    # Housing & Benefits
    mapping.update({
        "Housing & Benefits": ("General Housing & Benefits Support", "Housing & Benefits"),
        "Housing Assistance": ("Housing Assistance", "Housing & Benefits"),
        "Benefits Advice": ("Benefits Advice", "Housing & Benefits"),
        "Welfare Navigation": ("Welfare Navigation", "Housing & Benefits"),
        "Independent Living": ("Independent Living", "Housing & Benefits"),
        "Residential Care": ("Residential Care", "Housing & Benefits"),
        "Supported Living": ("Supported Living", "Housing & Benefits"),
        "Respite Care": ("Respite Care", "Housing & Benefits"),
        "Short Breaks": ("Short Breaks", "Housing & Benefits"),
        "Financial Assistance": ("Financial Assistance", "Housing & Benefits"),
    })
    
    # Transport & Accessibility
    mapping.update({
        "Transport & Accessibility": ("General Transport Support", "Transport & Accessibility"),
        "Accessible Transport": ("Accessible Transport", "Transport & Accessibility"),
        "Travel Training": ("Travel Training", "Transport & Accessibility"),
        "Mobility Services": ("Mobility Services", "Transport & Accessibility"),
        "Mobility Equipment": ("Mobility Equipment", "Transport & Accessibility"),
        "Accessibility Services": ("Accessibility Services", "Transport & Accessibility"),
    })
    
    # Community & Social
    mapping.update({
        "Community & Social": ("General Community Support", "Community & Social"),
        "Local Groups": ("Local Groups", "Community & Social"),
        "Organization Branches": ("Organization Branches", "Community & Social"),
        "Peer Networks": ("Peer Networks", "Community & Social"),
        "Support Groups": ("Support Groups", "Community & Social"),
        "Parent/Carer Groups": ("Parent/Carer Groups", "Community & Social"),
        "Social Clubs": ("Social Clubs", "Community & Social"),
        "Social Activities": ("Social Activities", "Community & Social"),
        "Meetups": ("Meetups", "Community & Social"),
        "Advocacy": ("Advocacy", "Community & Social"),
        "Advocacy Groups": ("Advocacy Groups", "Community & Social"),
        "Family Support": ("Family Support", "Community & Social"),
        "Carer Support": ("Carer Support", "Community & Social"),
    })
    
    # Recreation & Activities
    mapping.update({
        "Recreation & Activities": ("General Recreation", "Recreation & Activities"),
        "Sports & Fitness": ("Sports & Fitness", "Recreation & Activities"),
        "Arts & Entertainment": ("Arts & Entertainment", "Recreation & Activities"),
        "Play Centers": ("Play Centers", "Recreation & Activities"),
        "Hobby Clubs": ("Hobby Clubs", "Recreation & Activities"),
        "Outdoor Activities": ("Outdoor Activities", "Recreation & Activities"),
        "Adaptive Sports": ("Adaptive Sports", "Recreation & Activities"),
    })
    
    # Mental Health & Wellbeing
    mapping.update({
        "Mental Health & Wellbeing": ("General Mental Health Support", "Mental Health & Wellbeing"),
        "Mental Health Support": ("Mental Health Support", "Mental Health & Wellbeing"),
        "Mental Health Therapy": ("Mental Health Therapy", "Mental Health & Wellbeing"),
        "Mental Health Counselling": ("Mental Health Counselling", "Mental Health & Wellbeing"),
        "Mental Health Assessment": ("Mental Health Assessment", "Mental Health & Wellbeing"),
        "Mental Health Services": ("Mental Health Services", "Mental Health & Wellbeing"),
        "Therapeutic Services": ("Therapy Services", "Mental Health & Wellbeing"),
        "Therapy": ("Therapy", "Mental Health & Wellbeing"),
        "Therapy Services": ("Therapy Services", "Mental Health & Wellbeing"),
        "Counselling": ("Counselling", "Mental Health & Wellbeing"),
        "Counselling & Therapy": ("Counselling", "Mental Health & Wellbeing"),
        "Psychotherapy": ("Psychotherapy", "Mental Health & Wellbeing"),
        "Occupational Therapy": ("Occupational Therapy", "Mental Health & Wellbeing"),
        "Speech & Language Therapy": ("Speech & Language Therapy", "Mental Health & Wellbeing"),
        "Speech and Language Therapy": ("Speech & Language Therapy", "Mental Health & Wellbeing"),
        "Physiotherapy": ("Physiotherapy", "Mental Health & Wellbeing"),
        "Play Therapy": ("Play Therapy", "Mental Health & Wellbeing"),
        "Art Therapy": ("Art Therapy", "Mental Health & Wellbeing"),
        "Music Therapy": ("Music Therapy", "Mental Health & Wellbeing"),
        "Trauma Therapy": ("Trauma Therapy", "Mental Health & Wellbeing"),
        "Trauma Support": ("Trauma Support", "Mental Health & Wellbeing"),
        "Eating Disorder Therapy": ("Eating Disorder Therapy", "Mental Health & Wellbeing"),
        "Addiction Therapy": ("Addiction Therapy", "Mental Health & Wellbeing"),
        "Child & Adolescent Mental Health": ("Child & Adolescent Mental Health", "Mental Health & Wellbeing"),
        "Adult Mental Health": ("Adult Mental Health", "Mental Health & Wellbeing"),
        "Inpatient Mental Health": ("Inpatient Mental Health", "Mental Health & Wellbeing"),
        "Outpatient Mental Health": ("Outpatient Mental Health", "Mental Health & Wellbeing"),
        "Day Services": ("Day Services", "Mental Health & Wellbeing"),
        "Rehabilitation": ("Rehabilitation", "Mental Health & Wellbeing"),
        "Wellbeing Support": ("Wellbeing Support", "Mental Health & Wellbeing"),
    })
    
    return mapping


# Build the mapping once at module load
SUBCATEGORY_MAPPING = _build_subcategory_mapping()


# ============================================================================
# STANDARDIZATION FUNCTIONS
# ============================================================================

def standardize_category(category: Optional[str]) -> str:
    """
    Standardize a category value to one of the standard categories.
    
    Args:
        category: The category value to standardize (can be None or empty)
    
    Returns:
        Standardized category string
    """
    if not category or not isinstance(category, str):
        return "Unknown/Uncategorized"
    
    category = category.strip()
    if not category:
        return "Unknown/Uncategorized"
    
    # Check exact match first
    if category in STANDARD_CATEGORIES:
        return category
    
    # Check mapping
    if category in CATEGORY_MAPPING:
        return CATEGORY_MAPPING[category]
    
    # Try case-insensitive match
    category_lower = category.lower()
    for old_cat, new_cat in CATEGORY_MAPPING.items():
        if old_cat.lower() == category_lower:
            return new_cat
    
    # Try partial match (contains)
    for old_cat, new_cat in CATEGORY_MAPPING.items():
        if old_cat.lower() in category_lower or category_lower in old_cat.lower():
            return new_cat
    
    # Default to unknown
    return "Unknown/Uncategorized"


def standardize_subcategory(
    subcategory: Optional[str], 
    category: Optional[str] = None
) -> Tuple[str, str]:
    """
    Standardize a subcategory value and ensure it maps to the correct category.
    
    Args:
        subcategory: The subcategory value to standardize (can be None or empty)
        category: The category (will be standardized first if provided)
    
    Returns:
        Tuple of (standardized_subcategory, standardized_category)
    """
    # Standardize category first if provided
    if category:
        category = standardize_category(category)
    else:
        category = "Unknown/Uncategorized"
    
    if not subcategory or not isinstance(subcategory, str):
        return ("General", category)
    
    subcategory = subcategory.strip()
    if not subcategory:
        return ("General", category)
    
    # Check exact match in mapping
    if subcategory in SUBCATEGORY_MAPPING:
        mapped_subcat, mapped_cat = SUBCATEGORY_MAPPING[subcategory]
        # Use the mapped category if it's more specific than the provided one
        if category == "Unknown/Uncategorized" or mapped_cat != "Unknown/Uncategorized":
            return (mapped_subcat, mapped_cat)
        return (mapped_subcat, category)
    
    # Try case-insensitive match
    subcat_lower = subcategory.lower()
    for old_subcat, (new_subcat, new_cat) in SUBCATEGORY_MAPPING.items():
        if old_subcat.lower() == subcat_lower:
            if category == "Unknown/Uncategorized" or new_cat != "Unknown/Uncategorized":
                return (new_subcat, new_cat)
            return (new_subcat, category)
    
    # Try partial match (contains)
    for old_subcat, (new_subcat, new_cat) in SUBCATEGORY_MAPPING.items():
        if old_subcat.lower() in subcat_lower or subcat_lower in old_subcat.lower():
            if category == "Unknown/Uncategorized" or new_cat != "Unknown/Uncategorized":
                return (new_subcat, new_cat)
            return (new_subcat, category)
    
    # Check if subcategory matches any standard subcategory for the given category
    if category in STANDARD_SUBCATEGORIES:
        for std_subcat in STANDARD_SUBCATEGORIES[category]:
            if std_subcat.lower() == subcat_lower or subcat_lower in std_subcat.lower():
                return (std_subcat, category)
    
    # Default: return "General" with the category
    if category in STANDARD_SUBCATEGORIES:
        return ("General", category)
    
    return ("General", "Unknown/Uncategorized")


def standardize_resource_categories(
    category: Optional[str],
    subcategory: Optional[str]
) -> Tuple[str, str]:
    """
    Standardize both category and subcategory, ensuring they're consistent.
    
    Args:
        category: The category value
        subcategory: The subcategory value
    
    Returns:
        Tuple of (standardized_category, standardized_subcategory)
    """
    # First standardize category
    std_category = standardize_category(category)
    
    # Then standardize subcategory (which may also correct the category)
    std_subcategory, final_category = standardize_subcategory(subcategory, std_category)
    
    return (final_category, std_subcategory)


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def is_valid_category(category: str) -> bool:
    """Check if a category is one of the standard categories."""
    return category in STANDARD_CATEGORIES


def is_valid_subcategory(subcategory: str, category: str) -> bool:
    """Check if a subcategory is valid for the given category."""
    if category not in STANDARD_SUBCATEGORIES:
        return False
    return subcategory in STANDARD_SUBCATEGORIES[category]


def get_subcategories_for_category(category: str) -> List[str]:
    """Get the list of standard subcategories for a given category."""
    return STANDARD_SUBCATEGORIES.get(category, [])

