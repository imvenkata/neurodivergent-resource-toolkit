# Category & Subcategory Standardization - Summary & Recommendations

## Executive Summary

I've implemented a comprehensive category and subcategory standardization system for your neurodivergent resource toolkit. The system consolidates **15 inconsistent categories** into **10 standardized categories** and maps **hundreds of subcategory variations** to consistent, well-organized subcategories.

## What Was Done

### 1. Created Standardization Module (`src/utils/category_standardization.py`)

- **10 Standard Categories** (consolidated from 15+ variants)
- **Comprehensive Subcategory Lists** organized by category
- **Mapping Functions** to convert old values to standard values
- **Validation Functions** to ensure data quality

### 2. Updated Core Pipeline (`src/batch_enrich_pipeline_parallel.py`)

- Automatic standardization during data enrichment
- Categories and subcategories are standardized when merging extracted data
- Ensures consistency between category and subcategory

### 3. Created Standalone Script (`src/standardize_categories.py`)

- Can standardize existing data files (CSV/Excel)
- Provides statistics on what changed
- Useful for migrating existing datasets

### 4. Updated Configuration (`config.py`)

- Added "Mental Health & Wellbeing" as 10th category
- Updated category descriptions for LLM understanding

### 5. Updated LLM Prompt (`src/web_llm_extract.py`)

- Added "Mental Health & Wellbeing" to category list
- Ensures LLM assigns standardized categories from the start

## Standard Categories (10)

1. **Assessment & Diagnosis**
2. **Crisis & Emergency**
3. **Education & Learning**
4. **Employment**
5. **Housing & Benefits**
6. **Transport & Accessibility**
7. **Community & Social**
8. **Recreation & Activities**
9. **Mental Health & Wellbeing** ⭐ (NEW - consolidates Mental Health variants)
10. **Unknown/Uncategorized**

## Key Consolidations

### Category Consolidations

| Old Variants | → | Standard Category |
|-------------|---|------------------|
| Mental health support<br>Mental Health & Wellbeing<br>Mental Health & Therapy<br>Mental Health<br>Therapeutic Services | → | **Mental Health & Wellbeing** |
| Community Support | → | **Community & Social** |
| Education Support | → | **Education & Learning** |
| Employment Support | → | **Employment** |
| Housing Support<br>Benefits Support | → | **Housing & Benefits** |
| Transport Support | → | **Transport & Accessibility** |
| Unknown Category | → | **Unknown/Uncategorized** |

### Subcategory Standardization

All subcategories are now:
- **Consistent** - Same service type always uses same name
- **Mapped to Correct Category** - Subcategories automatically map to parent category
- **Organized** - Clear hierarchy and structure

Examples:
- "Therapy/Counselling" → "Therapy" (Mental Health & Wellbeing)
- "SEN Support" → "Special Educational Needs (SEN)" (Education & Learning)
- "Job Coaching, Workplace Accommodations" → "Job Coaching" (Employment)

## How to Use

### 1. Automatic Standardization (Recommended)

Categories are automatically standardized during enrichment:

```bash
python src/batch_enrich_pipeline_parallel.py \
  --input data/enriched/enriched_resources.csv \
  --output data/output/enriched_resources_standardized.xlsx
```

### 2. Standardize Existing Data

To standardize categories in existing files:

```bash
python src/standardize_categories.py \
  --input data/enriched/enriched_resources.csv \
  --output data/enriched/enriched_resources_standardized.xlsx \
  --stats
```

The `--stats` flag shows what changed:
- How many categories were standardized
- How many subcategories were standardized
- List of all changes made

### 3. Programmatic Usage

```python
from src.utils.category_standardization import standardize_resource_categories

category = "Mental health support"
subcategory = "Therapy/Counselling"

std_category, std_subcategory = standardize_resource_categories(category, subcategory)
# Returns: ("Mental Health & Wellbeing", "Therapy")
```

## Recommendations

### Immediate Actions

1. **Run Standardization on Existing Data**
   ```bash
   python src/standardize_categories.py \
     --input data/enriched/enriched_resources_20251101_080009.csv \
     --output data/enriched/enriched_resources_standardized.xlsx \
     --stats
   ```

2. **Review Statistics**
   - Check what categories/subcategories changed
   - Verify the mappings look correct
   - Update any downstream systems if needed

3. **Update LLM Prompts** (Already done)
   - The LLM prompt now includes "Mental Health & Wellbeing"
   - Future extractions will use standardized categories

### Future Enhancements

1. **Add More Subcategory Mappings**
   - The current mapping covers common variations
   - You can add more specific mappings as needed in `category_standardization.py`

2. **Category Validation Rules**
   - Add rules like "ADHD Assessment" must be in "Assessment & Diagnosis"
   - Currently handled by mapping, but explicit rules could be added

3. **Category Hierarchies**
   - Consider adding sub-subcategories if needed
   - Current system supports 2 levels (category → subcategory)

4. **Analytics Dashboard**
   - Track category distribution over time
   - Monitor standardization effectiveness

## Files Created/Modified

### New Files
- `src/utils/category_standardization.py` - Core standardization module
- `src/standardize_categories.py` - Standalone standardization script
- `docs/CATEGORY_STANDARDIZATION.md` - Detailed documentation
- `docs/CATEGORY_STANDARDIZATION_SUMMARY.md` - This file

### Modified Files
- `src/batch_enrich_pipeline_parallel.py` - Added automatic standardization
- `config.py` - Added "Mental Health & Wellbeing" category
- `src/web_llm_extract.py` - Updated LLM prompt with new category

## Testing

To test the standardization:

```python
from src.utils.category_standardization import standardize_resource_categories

# Test category consolidation
assert standardize_resource_categories("Mental health support", "")[0] == "Mental Health & Wellbeing"
assert standardize_resource_categories("Therapeutic Services", "")[0] == "Mental Health & Wellbeing"

# Test subcategory mapping
assert standardize_resource_categories("", "Therapy/Counselling")[1] == "Therapy"
assert standardize_resource_categories("Education & Learning", "SEN Support")[1] == "Special Educational Needs (SEN)"

# Test category correction from subcategory
category, subcategory = standardize_resource_categories("Unknown/Uncategorized", "ADHD Assessment")
assert category == "Assessment & Diagnosis"
assert subcategory == "ADHD Assessment"
```

## Next Steps

1. ✅ **Standardization system implemented**
2. ✅ **Automatic standardization in pipeline**
3. ✅ **Standalone script for existing data**
4. ⏭️ **Run on existing data** (you should do this)
5. ⏭️ **Review and refine mappings** (as needed)
6. ⏭️ **Update any downstream systems** (if they depend on old category names)

## Questions or Issues?

If you find:
- Subcategories that don't map correctly
- Categories that should be consolidated differently
- Missing subcategory mappings

You can:
1. Add mappings to `_build_subcategory_mapping()` in `category_standardization.py`
2. Add new standard subcategories to `STANDARD_SUBCATEGORIES`
3. Update category mappings in `CATEGORY_MAPPING`

The system is designed to be easily extensible!

