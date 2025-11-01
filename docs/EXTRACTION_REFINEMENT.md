# Extraction Refinement - Focused Categories

## Problem Identified

The LLM was extracting too many items, including:
- **`conditions_supported`**: 29 items including non-ND conditions like "Stress", "Bereavement", "Anger management"
- **`specific_services`**: 41 items with many duplicates/groupings (e.g., separate entries for "Group therapy", "Couples therapy", "One-to-one therapy")

## Solution: Focused Extraction (Max 10-12 Items)

### Updated Rules for `conditions_supported`

**INCLUDE (Primary ND Conditions):**
- ✅ Autism/ASC
- ✅ ADHD
- ✅ Dyslexia
- ✅ Dyspraxia
- ✅ Tourette's syndrome
- ✅ Learning disabilities
- ✅ Intellectual disabilities
- ✅ Co-occurring mental health ONLY if explicitly ND-related

**EXCLUDE:**
- ❌ Generic conditions: "Stress", "Anger management", "Bereavement"
- ❌ Common mental health unless ND-specific: "Depression", "Anxiety" (alone)
- ❌ Symptoms: "Panic attacks", "Self-harm" (not conditions)
- ❌ General terms: "Mental health", "Emotional support"
- ❌ Substance abuse/addictions unless ND-specific
- ❌ Rare conditions unless this is a specialist service

### Updated Rules for `specific_services`

**GROUP Similar Services:**
- ✅ `"Therapy (individual, group, couples, family)"` instead of 4 separate items
- ✅ `"Diagnostic assessments (autism, ADHD)"` instead of separate items
- ✅ `"Treatment (inpatient, outpatient, day care)"` instead of separate items

**INCLUDE:**
- ✅ Core services: Assessments, therapy types, support programs
- ✅ Specialized services unique to provider

**EXCLUDE:**
- ❌ Generic activities: "Yoga", "Gym facilities", "Movie nights" (unless ND-specific)
- ❌ Administrative: "Referral services", "Payment plans"
- ❌ Supportive activities: "Recreational activities" (unless ND-focused)

## Expected Improvements

### Before (Priory Roehampton):
```json
{
  "conditions_supported": [
    "Autism/ASC", "ADHD", "Tourette's syndrome", "Learning disability",
    "Brain injury", "Depression", "Anxiety", "OCD", "PTSD",
    "Bipolar disorder", "Stress", "Personality disorders",
    "Bereavement", "Anger management", "Panic attacks", "Self-harm",
    "Psychosis", "School phobia", "Eating disorders",
    "Addictions (Alcohol, Drugs, Gambling, Internet, Shopping, Sex and love)",
    "Prader-Willi syndrome", "Gender dysphoria", "Conduct disorder",
    "Oppositional defiant disorder (ODD)", "Medically unexplained symptoms (MUS)",
    "Somatic symptom disorder (SSD)", "Treatment-resistant depression",
    "Seasonal affective disorder (SAD)", "Selective mutism"
  ],
  "specific_services": [
    "Mental health assessments", "Autism assessment (children and adults)",
    "ADHD assessment", "Eating disorder assessment", "Private CAMHS assessment",
    "Free addiction assessment", "Inpatient (residential) treatment",
    "Outpatient treatment", "Day care", "Online therapy",
    "One-to-one therapy", "Group therapy", "Couples therapy",
    "Family counselling", "Cognitive behavioural therapy (CBT)",
    "Dialectical behaviour therapy (DBT)", ... (41 items total)
  ]
}
```

### After (Expected):
```json
{
  "conditions_supported": [
    "Autism/ASC",
    "ADHD",
    "Tourette's syndrome",
    "Learning disabilities",
    "Intellectual disabilities",
    "Brain injury"
  ],
  "specific_services": [
    "Diagnostic assessments (autism, ADHD)",
    "Therapy (individual, group, couples, family)",
    "Treatment (inpatient, outpatient, day care)",
    "Cognitive behavioural therapy (CBT)",
    "Dialectical behaviour therapy (DBT)",
    "Specialist ND clinics",
    "Addiction treatment programs",
    "Young people's mental health services (12-17 years)",
    "On-site school provision",
    "Positive behaviour support (PBS)"
  ]
}
```

## Benefits

1. **More Focused**: Only includes what's truly relevant for ND directory
2. **Easier to Read**: Fewer items, grouped logically
3. **Better Prioritization**: Focuses on core services, not supporting activities
4. **More Accurate**: Excludes non-ND conditions that were incorrectly included

## Example Extraction Patterns

### Example 1: Mental Health Hospital with ND Services
```json
{
  "conditions_supported": [
    "Autism/ASC",
    "ADHD",
    "Learning disabilities",
    "Intellectual disabilities",
    "Tourette's syndrome"
  ],
  "specific_services": [
    "Diagnostic assessments (autism, ADHD)",
    "Therapy (individual, group, family)",
    "Inpatient treatment",
    "Outpatient treatment",
    "Day care programs",
    "Specialist ND clinics"
  ]
}
```
✅ Includes primary ND conditions
❌ Excludes: "Depression", "Anxiety", "Stress" (not ND-specific conditions)

### Example 2: ADHD Assessment Clinic
```json
{
  "conditions_supported": ["ADHD"],
  "specific_services": [
    "ADHD assessment",
    "ADHD treatment planning",
    "Prescription management",
    "Follow-up support"
  ]
}
```
✅ Focused on single primary condition

### Example 3: Autism School
```json
{
  "conditions_supported": [
    "Autism/ASC",
    "Learning disabilities"
  ],
  "specific_services": [
    "Specialist education (SEN)",
    "Speech and language therapy",
    "Occupational therapy",
    "Sensory support programs",
    "Social skills training"
  ]
}
```
✅ Educational and therapeutic services focused on ND needs

## Implementation

The changes are in the LLM prompt in `src/web_llm_extract.py`:
- Lines 705-714: Updated `conditions_supported` rules
- Lines 715-724: Updated `specific_services` rules  
- Lines 975-994: Added examples of good extraction

The LLM will now:
1. Filter out non-ND conditions
2. Group similar services together
3. Limit to 10-12 most important items per array
4. Focus on core services for neurodivergent individuals

