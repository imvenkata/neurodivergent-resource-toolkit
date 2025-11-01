Use the regions filter with the exact region name “Hertfordshire”.

Quick test (1 search, snapshot written to data/db):

```bash
python src/expand_uk_coverage.py \
  --regions-filter "Hertfordshire" \
  --max-searches 1
```

Targeted keywords (cheaper/faster):

```bash
python src/expand_uk_coverage.py \
  --regions-filter "Hertfordshire" \
  --keywords-filter "autism,ADHD" \
  --max-searches 25
```

Full run for Hertfordshire:

```bash
python src/expand_uk_coverage.py \
  --regions-filter "Hertfordshire"
```

Notes:

- Region name must match config exactly: Hertfordshire.
- Output is auto-snapshotted to data/db/enriched_resources_YYYYMMDD_HHMMSS.{xlsx|csv}.
- Coverage is recorded in data/db/coverage_status.csv after the run.
