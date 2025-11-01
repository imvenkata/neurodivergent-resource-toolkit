# How `conditions_supported` and `specific_services` Are Extracted

## Overview

Both fields are extracted by an LLM (Gemini/OpenAI/Ollama) that reads the website content and identifies relevant information. The extraction is **factual only** - the LLM extracts what's explicitly stated on the website, not what it infers.

## Extraction Process

### Step 1: Website Content Collection

1. **Crawl website**: `crawl_site()` fetches multiple pages from the website
2. **Clean HTML**: Raw HTML is converted to clean text using `html_to_text()`
3. **Combine pages**: Multiple pages are combined with markers (`=== PAGE: URL ===`)
4. **Cache**: Cleaned text is saved to content cache for reuse
5. **Limit size**: Content is truncated to ~50,000 chars (first 8 pages, 8,000 chars per page)

### Step 2: LLM Prompt Construction

The prompt includes:

```python
instructions = (
    "TASK: Extract structured information about {center_name} from their website content.\n"
    "RULES:\n"
    "• Extract factual information only - do not infer or assume\n"
    "• Use \"Not specified\" for missing text fields, [] for missing arrays\n"
    
    "EXTRACTION REQUIREMENTS:\n"
    "• conditions_supported: List neurodivergent conditions (ADHD, Autism/ASC, Dyslexia, etc.)\n"
    "• specific_services: List concrete services (assessment, support groups, therapy, etc.)\n"
    
    "WEBSITE CONTENT (excerpted):\n{cleaned_website_text}"
)
```

### Step 3: LLM Extraction

The LLM receives:
- **Instructions**: What to extract and how
- **Website content**: Cleaned text from crawled pages
- **Output format**: Exact JSON structure with empty arrays as placeholders

The LLM analyzes the website text and populates the arrays.

## `conditions_supported` Logic

### What It Contains

**Primary purpose**: Lists neurodivergent conditions the service explicitly supports or treats.

**Examples from Priory Roehampton:**
- ✅ `"Autism/ASC"` - Explicitly mentioned in services
- ✅ `"ADHD"` - Explicitly mentioned in services  
- ✅ `"Learning disability"` - Explicitly mentioned
- ✅ `"Depression"`, `"Anxiety"` - Mental health conditions often co-occurring with ND
- ✅ `"Tourette's syndrome"` - Neurodivergent condition
- ✅ `"Eating disorders"` - Often co-occurring with ND conditions

### Extraction Rules

1. **Factual extraction only**: LLM extracts conditions **explicitly mentioned** on the website
2. **Neurodivergent focus**: Should include ND conditions (autism, ADHD, dyslexia, Tourette's, etc.)
3. **Co-occurring conditions**: May include mental health conditions (depression, anxiety) that commonly co-occur
4. **No inference**: If website doesn't mention a condition, it's not listed
5. **Empty array allowed**: If no ND conditions mentioned, array is `[]`

### Real Example from Priory Roehampton

**Why these conditions are listed:**

1. **Website explicitly states**: "autism and ADHD assessments for children and adults"
   → Extracted: `"Autism/ASC"`, `"ADHD"`

2. **Website mentions**: "learning disabilities and brain injuries"
   → Extracted: `"Learning disability"`, `"Brain injury"`

3. **Website lists**: Various mental health conditions in their treatment programs
   → Extracted: `"Depression"`, `"Anxiety"`, `"OCD"`, etc.

4. **Website mentions**: Specific conditions in service descriptions
   → Extracted: `"Tourette's syndrome"`, `"Prader-Willi syndrome"`, etc.

## `specific_services` Logic

### What It Contains

**Primary purpose**: Lists concrete, actionable services the organization provides.

**Examples from Priory Roehampton:**
- ✅ `"Autism assessment (children and adults)"` - Specific service type
- ✅ `"ADHD assessment"` - Specific service type
- ✅ `"Inpatient (residential) treatment"` - Service delivery method
- ✅ `"Cognitive behavioural therapy (CBT)"` - Specific therapy type
- ✅ `"Online therapy"` - Service delivery method

### Extraction Rules

1. **Concrete services only**: Lists actual services offered, not general descriptions
2. **Specificity**: Prefers specific service names over generic descriptions
3. **Action-oriented**: Services should be things users can access/use
4. **No inference**: Only lists services explicitly mentioned on website
5. **Empty array allowed**: If no services clearly described, array is `[]`

### Real Example from Priory Roehampton

**Why these services are listed:**

1. **Website explicitly states**: "autism assessment", "ADHD assessment"
   → Extracted: `"Autism assessment (children and adults)"`, `"ADHD assessment"`

2. **Website lists**: Various therapy types
   → Extracted: `"CBT"`, `"DBT"`, `"EMDR"`, `"ACT"`, etc.

3. **Website describes**: Treatment programs
   → Extracted: `"Inpatient (residential) treatment"`, `"Outpatient treatment"`, `"Day care"`

4. **Website mentions**: Support services
   → Extracted: `"Family counselling"`, `"Crisis support (signposting)"`, etc.

## Key Principles

### 1. Factual Extraction Only

❌ **WRONG**: LLM infers "They probably support autism because they're a mental health service"
✅ **RIGHT**: LLM extracts "autism" only if website explicitly mentions it

### 2. No Assumptions

❌ **WRONG**: LLM assumes all mental health services support ND conditions
✅ **RIGHT**: LLM only lists ND conditions explicitly stated in website content

### 3. Explicit Over Implicit

❌ **WRONG**: "Offers therapy" → assumes ND-relevant therapy
✅ **RIGHT**: "Offers autism-specific therapy" → extracts as ND service

### 4. Empty Arrays Are Valid

- If website doesn't mention any ND conditions → `conditions_supported: []`
- If website doesn't list specific services → `specific_services: []`
- This is correct behavior, not an error

## Relationship to Neurodivergent Relevance Scoring

These fields are used to determine `neurodivergent_relevance_score`:

### HIGH Score Requirements:
- `conditions_supported` includes ND conditions
- OR name contains ND keywords (autism, ADHD, etc.)

### MEDIUM Score Requirements:
- `conditions_supported` includes at least one ND condition
- OR `specific_services` includes ND-specific services (SEND programs, autism-friendly activities, etc.)

### LOW/NONE Score:
- `conditions_supported` is empty
- AND no explicit ND keywords in name/description
- AND no ND-specific services in `specific_services`

## Example: Priory Roehampton Analysis

Looking at the extraction:

**`conditions_supported`**: 29 conditions listed
- ✅ Includes ND conditions: Autism/ASC, ADHD, Tourette's, Learning disability
- ✅ Includes co-occurring: Depression, Anxiety, OCD, etc.
- ✅ Includes related: Brain injury, Eating disorders, etc.

**`specific_services`**: 41 services listed
- ✅ ND-specific: "Autism assessment", "ADHD assessment"
- ✅ Therapeutic: Multiple therapy types (CBT, DBT, etc.)
- ✅ Service types: Inpatient, outpatient, day care

**Result**: 
- `neurodivergent_relevance_score`: **"High"** ✅
- `is_neurodivergent_related`: **true** ✅
- Reasoning: Explicitly provides autism and ADHD assessments, which are primary ND services

## Quality Checks

### Good Extraction Indicators:
✅ Specific conditions listed (not just "mental health")
✅ Specific service types (not just "support" or "help")
✅ Multiple related services indicate comprehensive extraction
✅ Conditions match what's in `description_short`

### Potential Issues:
⚠️ Empty arrays when website clearly mentions services (LLM missed them)
⚠️ Too generic conditions ("Mental health" instead of specific conditions)
⚠️ Services not actually mentioned on website (LLM inferred)
⚠️ Missing key services that are clearly stated on website

## Improving Extraction Quality

If extraction is poor, check:

1. **Website content quality**: Was website content successfully crawled?
2. **Content length**: Is content truncated too early?
3. **LLM model**: Different models (Gemini vs GPT-4) may extract differently
4. **Prompt clarity**: Instructions should be clear (they are)
5. **Content cache**: Check `.cache/content/` files to see what LLM actually read

## Technical Flow Summary

```
Website URL
  ↓
crawl_site() → Fetches HTML pages
  ↓
html_to_text() → Cleans HTML to text
  ↓
build_prompt() → Creates LLM prompt with:
  - Instructions
  - Cleaned website text
  - Output JSON template
  ↓
LLM (Gemini/OpenAI/Ollama) → Analyzes text
  ↓
Extracts conditions_supported & specific_services
  ↓
Returns JSON with populated arrays
```

