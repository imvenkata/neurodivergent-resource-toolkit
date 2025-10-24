# Batch Enrichment Pipeline - Quick Start Guide

## What It Does

Automatically enriches service center data from `enriched_resources.csv` by:
1. Reading center names and websites from the CSV
2. Extracting structured information using LLMs
3. Filling in missing fields (description, age range, services, etc.)
4. Exporting to Excel with highlighted changes

## Quick Start

### 1. Install Dependencies

```bash
pip install openpyxl
# or with uv
uv pip install openpyxl
```

### 2. Set Your API Key

```bash
export GEMINI_API_KEY="your-key-here"
# or for OpenAI
export OPENAI_API_KEY="your-key-here"
```

### 3. Test with Sample Data

```bash
bash test_pipeline.sh
```

This will process 3 service centers and create `test_enriched_sample.xlsx`

### 4. Run Full Pipeline

```bash
python batch_enrich_pipeline.py \
  --input to_be_normalised/enriched_resources.csv \
  --output enriched_resources_updated.xlsx \
  --backend gemini \
  --enhance-with-websearch \
  --skip-no-website \
  --delay 2.0
```

## Common Use Cases

### Process First 50 Rows (Testing)
```bash
python batch_enrich_pipeline.py \
  --max-rows 50 \
  --backend gemini
```

### Resume from Row 500
```bash
python batch_enrich_pipeline.py \
  --start-row 500 \
  --backend gemini
```

### Process Only Centers with Missing Descriptions
```bash
python batch_enrich_pipeline.py \
  --fields-to-check description_short \
  --backend gemini
```

### Use Local Ollama (Free)
```bash
python batch_enrich_pipeline.py \
  --backend ollama \
  --model llama3.1:8b-instruct
```

## Expected Output

```
Reading to_be_normalised/enriched_resources.csv...
Loaded 1925 rows
Found 847 rows that need enrichment

[1/847] Processing: East London NHS Foundation Trust
  Website: http://www.elft.nhs.uk/
  ✓ Updated fields: description_short, age_range, organization_type

[2/847] Processing: C N W L Mental Health Clinic
  Website: http://www.cnwl.nhs.uk/
  ✓ Using cached data
  ✓ Updated fields: description_short, specific_services

============================================================
SUMMARY
============================================================
Total rows in input:     1925
Rows needing enrichment: 847
Successfully processed:  820
Successfully enriched:   803
Failed:                  17
Skipped:                 10

Output saved to: enriched_resources_updated.xlsx
Changed cells are highlighted in yellow
============================================================
```

## Excel Output

The output Excel file will have:
- ✅ All original data preserved
- 🟡 Changed cells highlighted in yellow
- 📊 Proper column widths
- 🎨 Formatted headers

## Column Mapping

| CSV Column | What Gets Filled |
|-----------|------------------|
| description_short | Brief service description |
| age_range | Age groups served (e.g., "Adults (18+)") |
| conditions_supported | ADHD, Autism/ASC, Dyslexia, etc. |
| specific_services | Concrete services offered |
| organization_type | NHS, Charity, Private, etc. |
| gmaps_addr_postal_code | UK postcode |
| gmaps_addr_postal_town | City/town name |
| gmaps_addr_admin_area_level_1 | England/Scotland/Wales |
| gmaps_addr_admin_area_level_2 | County name |

## Performance Tips

1. **Start Small**: Always test with `--max-rows 5` first
2. **Use Caching**: Re-runs are instant for processed centers
3. **Gemini is Fast**: Recommended for batch processing
4. **Watch Rate Limits**: Increase `--delay` if hitting limits
5. **Resume Support**: Use `--start-row` if interrupted

## Troubleshooting

### "No rows need enrichment"
- Your CSV already has the data
- Adjust `--fields-to-check` to check different columns

### "Timeout after 180s"
- Some websites are slow/blocked
- These will be marked as failed
- You can resume and process others

### "Module 'openpyxl' not found"
```bash
pip install openpyxl
```

### API Rate Limits
- Increase `--delay` to 3-5 seconds
- Process in smaller batches with `--max-rows`
- Use caching to avoid reprocessing

## Files Created

- `.cache/llm_extractions/*.json` - Cached extraction results
- `enriched_resources_updated_YYYYMMDD_HHMMSS.xlsx` - Output Excel file

## Cost Estimates (Gemini)

- Per center: ~$0.001-0.003 (Flash model)
- 1000 centers: ~$1-3
- 1925 centers: ~$2-6

OpenAI is more expensive (~10x), Ollama is free but slower.

## Need Help?

See the full documentation in [README.md](README.md)

## Example: Complete Workflow

```bash
# 1. Test with 5 centers
python batch_enrich_pipeline.py --max-rows 5 --backend gemini

# 2. Check the output Excel file
open test_enriched_sample.xlsx

# 3. If looks good, run on more data
python batch_enrich_pipeline.py --max-rows 100 --backend gemini

# 4. Finally, run full pipeline
python batch_enrich_pipeline.py \
  --backend gemini \
  --enhance-with-websearch \
  --delay 2.0
```

That's it! 🚀

