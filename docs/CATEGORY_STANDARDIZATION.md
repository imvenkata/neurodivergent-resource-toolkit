# Category and Subcategory Standardization

## Overview

This document describes the category and subcategory standardization system implemented to ensure consistency across the neurodivergent resource dataset.

## Standard Categories (10 Categories)

The system uses **10 standardized categories**:

1. **Assessment & Diagnosis** - Diagnostic centers, assessment clinics, psychoeducational evaluation
2. **Crisis & Emergency** - Crisis helplines, emergency intervention, mental health crisis teams
3. **Education & Learning** - SEN schools, mainstream resources, training, skills development, tutoring
4. **Employment** - Job coaching, workplace accommodations, vocational training, supported employment
5. **Housing & Benefits** - Housing assistance, benefits advice, independent living, welfare navigation
6. **Transport & Accessibility** - Accessible transport, travel training, mobility services, transport subsidies
7. **Community & Social** - Local groups, organization branches, peer networks, meetups, parent/carer groups
8. **Recreation & Activities** - Sports & fitness, arts & entertainment, play centers, hobby clubs
9. **Mental Health & Wellbeing** - Mental health services, therapy, counselling, therapeutic services, rehabilitation, wellbeing support
10. **Unknown/Uncategorized** - Use only when no other category fits

## Key Changes

### Category Consolidation

The following category variants have been consolidated:

- **Mental Health variants** → `Mental Health & Wellbeing`
  - "Mental health support"
  - "Mental Health & Wellbeing"
  - "Mental Health & Therapy"
  - "Mental Health"
  - "Therapeutic Services" (most cases)

- **Legacy categories** → Standard categories
  - "Community Support" → "Community & Social"
  - "Education Support" → "Education & Learning"
  - "Employment Support" → "Employment"
  - "Housing Support" → "Housing & Benefits"
  - "Benefits Support" → "Housing & Benefits"
  - "Transport Support" → "Transport & Accessibility"

### Subcategory Standardization

Subcategories are standardized to ensure:
1. **Consistency** - Same service type always uses the same subcategory name
2. **Category Mapping** - Subcategories are mapped to the correct parent category
3. **Completeness** - All variations map to a standard subcategory

## Implementation

### Module: `src/utils/category_standardization.py`

This module provides:

- `standardize_category(category)` - Standardizes a category value
- `standardize_subcategory(subcategory, category)` - Standardizes a subcategory and ensures correct category mapping
- `standardize_resource_categories(category, subcategory)` - Standardizes both together

### Integration

The standardization is automatically applied in:

1. **`src/batch_enrich_pipeline_parallel.py`** - During data enrichment, categories and subcategories are automatically standardized
2. **`src/standardize_categories.py`** - Standalone script to standardize existing data files

## Usage

### Automatic Standardization (During Enrichment)

Categories and subcategories are automatically standardized when running the enrichment pipeline:

```bash
python src/batch_enrich_pipeline_parallel.py --input data.csv --output output.xlsx
```

### Manual Standardization (Existing Data)

To standardize categories in an existing file:

```bash
python src/standardize_categories.py \
  --input data/enriched/enriched_resources.csv \
  --output data/enriched/enriched_resources_standardized.xlsx \
  --stats
```

The `--stats` flag shows statistics about what was changed.

### Programmatic Usage

```python
from src.utils.category_standardization import standardize_resource_categories

# Standardize both category and subcategory
category = "Mental health support"
subcategory = "Therapy/Counselling"

std_category, std_subcategory = standardize_resource_categories(category, subcategory)
# Returns: ("Mental Health & Wellbeing", "Therapy")
```

## Standard Subcategories by Category

### Assessment & Diagnosis
- Diagnostic Assessment, Diagnostic Clinics, Diagnostic Centers
- Assessment Clinics, Assessment & Screening
- Psychoeducational Evaluation
- Neurodevelopmental Assessment
- ADHD Assessment, Autism Assessment, Dyslexia Assessment
- Developmental Assessment, Psychological Assessment, Psychiatric Assessment
- Occupational Therapy Assessment, Speech & Language Assessment
- General Assessment

### Crisis & Emergency
- Crisis Helplines, Crisis Intervention, Emergency Intervention
- Mental Health Crisis Teams, Crisis Support Services
- Crisis Counselling, Suicide Prevention
- Emergency Mental Health, General Crisis Support

### Education & Learning
- SEN Schools, Special Educational Needs (SEN/SEND)
- Alternative Provision, Alternative Education
- Mainstream Resources, Tutoring, Skills Development, Training
- Educational Support Services, Early Years Education
- Further Education, Higher Education
- Educational Psychology, Learning Support
- Literacy Support, Dyslexia Support
- General Education Support

### Employment
- Job Coaching, Workplace Accommodations
- Vocational Training, Supported Employment
- Employment Support Services
- Workplace Training & Consultancy
- Career Guidance, Employment Rights & Advice
- Recruitment Services
- General Employment Support

### Housing & Benefits
- Housing Assistance, Benefits Advice, Welfare Navigation
- Independent Living, Residential Care, Supported Living
- Respite Care, Short Breaks
- Financial Assistance
- General Housing & Benefits Support

### Transport & Accessibility
- Accessible Transport, Travel Training
- Mobility Services, Mobility Equipment
- Accessibility Services, Accessibility Information
- Accessibility Consulting
- General Transport Support

### Community & Social
- Local Groups, Organization Branches, Peer Networks
- Support Groups, Parent/Carer Groups
- Social Clubs, Social Activities, Meetups
- Advocacy, Advocacy Groups, Self-Advocacy
- Community Support Services
- Family Support, Carer Support
- General Community Support

### Recreation & Activities
- Sports & Fitness, Arts & Entertainment
- Play Centers, Hobby Clubs
- Outdoor Activities, Adventure Sports
- Adaptive Sports, Accessible Recreation
- Therapeutic Activities, Social Activities
- General Recreation

### Mental Health & Wellbeing
- Mental Health Support, Mental Health Therapy
- Mental Health Counselling, Mental Health Assessment
- Mental Health Services
- CBT (Cognitive Behavioural Therapy)
- Psychotherapy, Counselling, Therapy, Therapy Services
- Occupational Therapy, Speech & Language Therapy
- Physiotherapy, Play Therapy, Art Therapy, Music Therapy
- Creative Therapy, Trauma Therapy, Trauma Support
- Eating Disorder Therapy, Addiction Therapy
- Child & Adolescent Mental Health, Adult Mental Health
- Inpatient Mental Health, Outpatient Mental Health
- Day Services, Rehabilitation, Wellbeing Support
- General Mental Health Support

### Unknown/Uncategorized
- General, Uncategorized

## Benefits

1. **Data Consistency** - All resources use the same category/subcategory names
2. **Better Filtering** - Users can reliably filter by standardized categories
3. **Analytics** - Category distribution analysis is accurate
4. **Maintenance** - Easier to maintain and update categories
5. **Mapping** - Subcategories are correctly mapped to parent categories

## Migration Notes

When migrating existing data:

1. Run `standardize_categories.py` on existing files
2. Review the statistics output to see what changed
3. Verify the standardized output looks correct
4. Update any downstream systems that depend on category names

## Future Enhancements

Potential improvements:

1. Add more granular subcategories as needed
2. Support category hierarchies (e.g., sub-subcategories)
3. Add validation rules (e.g., certain subcategories only valid for certain categories)
4. Add category descriptions for better LLM understanding

