# Neurodivergent Relevance Validation

## Overview

The pipeline now automatically validates whether each resource is truly neurodivergent-related. This helps filter out irrelevant services that may have been picked up during scraping.

## New Validation Fields

### 1. `is_neurodivergent_related` (boolean)
- **true**: Service specifically supports neurodivergent individuals
- **false**: Service is NOT neurodivergent-related
- Used for filtering

### 2. `neurodivergent_relevance_score` (text)
- **High**: Explicitly specializes in ADHD, Autism, Dyslexia, or other neurodivergent conditions
- **Medium**: Offers some neurodivergent support but not primary focus
- **Low**: May help neurodivergent people but not specifically designed for them
- **None**: Not relevant to neurodivergent support

### 3. `neurodivergent_focus` (text)
- Brief explanation of what neurodivergent conditions/needs are addressed
- Examples: "ADHD assessment and support", "General mental health, not ND-specific"

## How It Works

### During Extraction

The LLM analyzes each service's website and determines:

1. **Is it neurodivergent-related?**
   - Checks for mention of ADHD, Autism, Dyslexia, etc.
   - Looks for neurodivergent-specific services
   - Identifies if it's a general service vs. specialized

2. **Relevance Score**
   - Rates how specifically neurodivergent the service is
   - Helps prioritize highly relevant services

3. **Focus Area**
   - Notes which neurodivergent conditions are supported
   - Explains why it's classified as it is

### Example Output

**Highly Relevant Service:**
```json
{
  "center_name": "London ADHD Clinic",
  "is_neurodivergent_related": true,
  "neurodivergent_relevance_score": "High",
  "neurodivergent_focus": "Specializes in ADHD assessment and treatment for adults"
}
```

**Not Relevant:**
```json
{
  "center_name": "General Medical Center",
  "is_neurodivergent_related": false,
  "neurodivergent_relevance_score": "None",
  "neurodivergent_focus": "General healthcare, no neurodivergent specialization"
}
```

## Using the Filter Tool

### 1. Analyze Your Data

```bash
python filter_neurodivergent.py --input enriched_resources_parallel.xlsx --analyze
```

**Output:**
```
📊 SUMMARY:
  Total resources:           781
  ✅ Neurodivergent-related:  650 (83.2%)
  ❌ Not related:             100 (12.8%)
  ❓ Unknown/Not validated:   31 (4.0%)

📈 RELEVANCE SCORE BREAKDOWN:
  High            :  450 (69.2%)
  Medium          :  150 (23.1%)
  Low             :   50 (7.7%)
```

### 2. View Non-Neurodivergent Resources

```bash
python filter_neurodivergent.py --input enriched_resources_parallel.xlsx --show-non-nd
```

This shows resources that should potentially be removed.

### 3. Filter to Keep Only Neurodivergent Resources

```bash
# Keep only High relevance
python filter_neurodivergent.py \
  --input enriched_resources_parallel.xlsx \
  --filter \
  --min-score High \
  --output neurodivergent_only.xlsx
```

```bash
# Keep High and Medium relevance
python filter_neurodivergent.py \
  --input enriched_resources_parallel.xlsx \
  --filter \
  --min-score Medium \
  --output neurodivergent_only.xlsx
```

```bash
# Keep all neurodivergent-related (High, Medium, Low)
python filter_neurodivergent.py \
  --input enriched_resources_parallel.xlsx \
  --filter \
  --min-score Low \
  --output neurodivergent_only.xlsx
```

## Complete Workflow

### Step 1: Run Pipeline with Validation

```bash
source .venv/bin/activate

python batch_enrich_pipeline_parallel.py \
  --backend gemini \
  --enhance-with-websearch \
  --skip-no-website \
  --workers 5 \
  --rate-limit 15
```

This automatically adds validation fields to all resources.

### Step 2: Analyze Results

```bash
python filter_neurodivergent.py \
  --input enriched_resources_parallel_*.xlsx \
  --analyze
```

### Step 3: Review Non-Neurodivergent Resources

```bash
python filter_neurodivergent.py \
  --input enriched_resources_parallel_*.xlsx \
  --show-non-nd
```

Review the list and decide if they should be removed.

### Step 4: Create Filtered Dataset

```bash
python filter_neurodivergent.py \
  --input enriched_resources_parallel_*.xlsx \
  --filter \
  --min-score Medium \
  --output neurodivergent_resources_final.xlsx
```

## Use Cases

### Use Case 1: Remove All Non-Neurodivergent Services

```bash
# Filter to High + Medium only (most strict)
python filter_neurodivergent.py \
  --input enriched_resources.xlsx \
  --filter \
  --min-score Medium
```

### Use Case 2: Keep Everything Neurodivergent-Related

```bash
# Include Low relevance too
python filter_neurodivergent.py \
  --input enriched_resources.xlsx \
  --filter \
  --min-score Low
```

### Use Case 3: Keep Only Highly Specialized Services

```bash
# High relevance only
python filter_neurodivergent.py \
  --input enriched_resources.xlsx \
  --filter \
  --min-score High
```

### Use Case 4: Quality Check

```bash
# See what's being marked as non-neurodivergent
python filter_neurodivergent.py \
  --input enriched_resources.xlsx \
  --show-non-nd
```

## Validation Accuracy

The LLM-based validation is generally accurate for:
- ✅ Explicitly neurodivergent services (High score)
- ✅ Clearly non-related services (false)
- ⚠️ Edge cases may need manual review

### Manual Review Recommended For:
- Services with "Low" relevance score
- Resources with "Unknown" validation
- Services that seem borderline

## Excel Columns

The output Excel will have these additional columns:

| Column | Values | Purpose |
|--------|--------|---------|
| `is_neurodivergent_related` | true/false | Filter flag |
| `neurodivergent_relevance_score` | High/Medium/Low/None | Quality indicator |
| `neurodivergent_focus` | Text description | Explains the assessment |

## Tips

1. **Start with analysis** to understand your data distribution
2. **Review non-ND resources** before removing them
3. **Use appropriate threshold**:
   - High only → Most strict, highest quality
   - High + Medium → Balanced approach (recommended)
   - All (High/Medium/Low) → Inclusive, keep more resources
4. **Manual spot check** some Low-scored resources

## Command Reference

```bash
# Analyze distribution
python filter_neurodivergent.py --input file.xlsx --analyze

# Show non-neurodivergent
python filter_neurodivergent.py --input file.xlsx --show-non-nd

# Filter (High only)
python filter_neurodivergent.py --input file.xlsx --filter --min-score High

# Filter (High + Medium)
python filter_neurodivergent.py --input file.xlsx --filter --min-score Medium

# Filter (All neurodivergent)
python filter_neurodivergent.py --input file.xlsx --filter --min-score Low

# Custom output file
python filter_neurodivergent.py --input file.xlsx --filter --output custom.xlsx
```

## Benefits

✅ **Automatic validation** - No manual review needed for most cases  
✅ **Quality scores** - Prioritize highly relevant services  
✅ **Easy filtering** - Remove irrelevant resources in one command  
✅ **Transparency** - See why each resource was classified  
✅ **Flexible** - Choose your own relevance threshold  

---

**Next Steps:**
1. Run pipeline (validation happens automatically)
2. Analyze results: `python filter_neurodivergent.py --input file.xlsx --analyze`
3. Filter: `python filter_neurodivergent.py --input file.xlsx --filter --min-score Medium`

