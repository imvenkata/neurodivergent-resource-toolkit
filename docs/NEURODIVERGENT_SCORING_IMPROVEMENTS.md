# Neurodivergent Relevance Scoring Improvements

## Problem Identified

The original scoring mechanism was too lenient, allowing general recreational/educational services to be scored as "Medium" relevance when they should be "Low" or "None". 

**Example Case: Vauxhall City Farm**
- **Original Score**: Medium (incorrect)
- **Original Reasoning**: Mentioned "therapeutic offerings" which LLM inferred as ND-relevant
- **Correct Score**: Low (correct)
- **Issue**: Empty `conditions_supported`, no explicit ND keywords, no SEND/autism-friendly programs

## Root Causes

1. **Inference Over Evidence**: LLM was inferring relevance from vague terms like "therapeutic benefits" without requiring explicit ND mentions
2. **Missing Strict Rules**: No requirement that `conditions_supported` must be populated OR explicit ND keywords exist
3. **Incomplete Examples**: Missing examples of generic farms/parks that should be Low/None
4. **No Post-Processing**: No validation layer to catch false positives automatically

## Solutions Implemented

### 1. Strengthened LLM Prompt (`web_llm_extract.py`)

#### Added Explicit Requirements
- **MEDIUM score now REQUIRES**:
  - Explicit mention of SEND/SEN in services OR
  - Explicit "autism-friendly" / "sensory-friendly" statements OR
  - Professional therapeutic services (OT, speech therapy) - NOT general "therapeutic benefits"
  - Explicit disability/SEND programs

#### Added Strict Validation Checklist
New 5-step validation process:
1. **STEP 1**: Check for EXPLICIT neurodivergent mentions
2. **STEP 2**: Verify `conditions_supported` is populated
3. **STEP 3**: Determine score level based on explicit evidence
4. **STEP 4**: Validate against false positives
5. **STEP 5**: Final scoring for generic services

#### Added Key Rules
- **STRICT RULE**: If `conditions_supported` is EMPTY and no explicit ND keywords exist, service MUST be Low or None
- Clarified distinction between professional therapeutic services vs. general activities with therapeutic benefits
- Added explicit Low/None examples for generic farms, parks, recreational facilities

#### New Examples Added
- Example 10b: "City Farm (General Educational Farm)" → LOW
- Clarified that generic farms mentioning "therapeutic" without explicit ND programs should be LOW

### 2. Enhanced Validation Script (`validate_neurodivergent.py`)

#### Expanded Generic Service Detection
Added patterns for:
- City farms (without explicit ND programs)
- Farms (generic, excluding RDA/disability farms)
- Country parks (without SEND facilities)
- Youth centers (without SEND programs)
- Community/recreation centers (without special needs provision)

#### Stricter Validation Logic
- **Step 2**: New strict rule checking `conditions_supported` emptiness + missing ND keywords
- Validates that services explicitly mention SEND/SEN/autism-friendly
- Catches false positives where vague "therapeutic" language was misinterpreted

### 3. Integrated Auto-Validation (`batch_enrich_pipeline_parallel.py`)

#### Automatic False Positive Correction
- Pipeline now auto-validates each extracted resource
- Compares LLM output with validation rules
- Automatically corrects scores when validation differs
- Updates `neurodivergent_focus` with validation reason

#### Features
- Non-blocking: Validation failures don't break the pipeline
- Automatic: No manual intervention needed
- Transparent: Tracks changes via `changes` list

## Scoring Criteria (Updated)

### HIGH
- Name contains explicit ND keywords (autism, ADHD, dyslexia, etc.)
- Primary purpose is ND diagnosis, therapy, or education
- Specialist ND schools, clinics, assessment centers

### MEDIUM (Now Requires Explicit Evidence)
✅ **REQUIRED**: One of the following must be EXPLICITLY stated:
- SEND/SEN services explicitly mentioned in services/programs
- "Autism-friendly", "Sensory-friendly", or "Neurodivergent-friendly" explicitly stated
- Professional therapeutic services (OT, speech therapy, physio) - NOT general activities
- Mental health counseling/therapy services
- Crisis support services (helplines, emergency mental health)
- Parent/carer support groups EXPLICITLY for SEND/disabled families
- Disability charities EXPLICITLY serving disabled/SEND individuals
- Social skills/life skills groups EXPLICITLY mentioned
- Disability employment services EXPLICITLY mentioned

### LOW
- General services that ND people might use (but so does everyone)
- Educational/recreational facilities without SEND/autism-friendly programs
- Mentions vague "therapeutic benefits" but no explicit ND programs
- Has accessibility features but not ND-specific

### NONE
- General public services (transport, councils, hospitals)
- Commercial businesses
- Tourist attractions
- Generic recreational facilities

## Validation Results

### Test Case: Vauxhall City Farm
```
Original:
  is_neurodivergent_related: true
  neurodivergent_relevance_score: Medium

After Validation:
  is_neurodivergent_related: false
  neurodivergent_relevance_score: Low
  reason: No clear neurodivergent focus
```

**Why Corrected:**
- `conditions_supported`: [] (empty)
- No explicit ND keywords in name or services
- No "autism-friendly", "SEND", "SEN", or "special needs" mentioned
- Generic educational farm with vague "therapeutic" mention (not professional therapeutic service)

## Usage

### Automatic (Recommended)
The pipeline now automatically validates during enrichment:
```bash
python src/batch_enrich_pipeline_parallel.py --input data/input/file.csv
```

### Manual Validation
Re-validate existing cache files:
```bash
# Single file
python src/validate_neurodivergent.py --file .cache/llm_extractions/Vauxhall_City_Farm.json

# All cache files
python src/validate_neurodivergent.py --cache-dir .cache/llm_extractions
```

## Key Improvements Summary

1. ✅ **Stricter LLM Prompt**: Requires explicit evidence, not inference
2. ✅ **Validation Checklist**: Step-by-step process prevents false positives
3. ✅ **Enhanced Generic Detection**: Catches farms, parks, recreational facilities
4. ✅ **Auto-Correction**: Pipeline automatically fixes false positives
5. ✅ **Better Examples**: Clear Low/None examples for edge cases

## Future Considerations

- Monitor validation correction rates to fine-tune rules
- Consider adding more generic service patterns as they're discovered
- May want to add user override mechanism for edge cases
- Consider confidence scores for validation corrections

