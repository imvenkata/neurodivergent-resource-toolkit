# Immediate Action Plan: Improve Data Accuracy

**Based on:** ACCURACY_REVIEW.md analysis  
**Current State:** 1,043 resources, 0% validated, 44.5% have encoding issues, 68.8% not enriched

---

## 🚨 CRITICAL STATISTICS FROM YOUR DATA

```
Total Resources:              1,043
├─ With Website:               781 (74.9%)
├─ Without Website:            262 (25.1%) ← CANNOT BE ENRICHED with current method
│
├─ Enriched:                   325 (31.2%)
├─ Not Enriched:               718 (68.8%)
│
├─ Validated ND-Related:         0 (0.0%)   ← CRITICAL ISSUE
├─ Validated NOT ND:             0 (0.0%)
└─ Unvalidated:              1,043 (100%)
│
├─ Encoding Issues:            464 (44.5%) ← USER EXPERIENCE ISSUE
└─ Potential False Positives:   79 (7.6%)  ← ACCURACY ISSUE
```

**Geographic Scope Issue:**
- London (Greater London): 444 (42.6%)
- Unknown/No County: 434 (41.6%) ← DATA QUALITY ISSUE
- Outside London: 165 (15.8%) - includes Hertfordshire, Surrey, Essex, Kent, etc.

---

## 📋 WEEK 1 ACTION PLAN

### Day 1: VALIDATE EXISTING DATA

**Goal:** Identify which resources are actually neurodivergent-related

#### Step 1.1: Run enrichment with validation on all resources
```bash
cd /Users/venkata/startup/neurodivergent-resource-toolkit

# Run enrichment on resources that have websites but aren't enriched yet
python src/batch_enrich_pipeline_parallel.py \
  --input data/enriched_resources.csv \
  --output data/output/validated_resources.xlsx \
  --backend gemini \
  --workers 5 \
  --rate-limit 15 \
  --categorize
```

**Expected time:** ~700 resources × 10 seconds = ~2 hours  
**API cost:** ~$0.50 (Gemini Flash is very cheap)

#### Step 1.2: Analyze validation results
```bash
python src/filter_neurodivergent.py \
  --input data/output/validated_resources.xlsx \
  --analyze
```

This will show you:
- How many are actually neurodivergent-related
- Relevance score distribution (High/Medium/Low/None)
- Which resources should be removed

#### Step 1.3: Create filtered high-quality dataset
```bash
# Keep only Medium+ relevance (recommended)
python src/filter_neurodivergent.py \
  --input data/output/validated_resources.xlsx \
  --filter \
  --min-score Medium \
  --output data/output/neurodivergent_verified.xlsx
```

**Expected outcome:** ~600-700 genuine neurodivergent resources (down from 1,043)

---

### Day 2: FIX ENCODING ISSUES

**Goal:** Clean up the 464 resources (44.5%) with corrupted text

#### Step 2.1: Create encoding fix script

Create new file: `src/fix_encoding.py`

```python
#!/usr/bin/env python3
"""Fix encoding issues in existing data"""
import csv
import re
from pathlib import Path

def clean_text(text: str) -> str:
    """Clean text to handle encoding issues."""
    if not isinstance(text, str):
        return text
    
    # Pattern: "9:00?AM?�?5:00?PM" -> "9:00 AM - 5:00 PM"
    text = re.sub(r'(\d{1,2}:\d{2})\?([AP]M)\?[�\ufffd]?\?(\d{1,2}:\d{2})\?([AP]M)', 
                  r'\1 \2 - \3 \4', text)
    
    # Replace common problematic characters
    replacements = {
        '\u2013': '-',  '\u2014': '-',  # dashes
        '\u2018': "'",  '\u2019': "'",  # quotes
        '\u201c': '"',  '\u201d': '"',
        '\u2026': '...',
        '\xa0': ' ',  '\u00a0': ' ',
        '\ufffd': '',  '�': '',
        '\x00': '',
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Remove standalone ? not in URLs
    if 'http' not in text.lower():
        text = re.sub(r'\?+', ' ', text)
    else:
        text = re.sub(r'\?([AP]M)', r' \1', text)
        text = re.sub(r'(\d)\?([A-Z][a-z])', r'\1 \2', text)
    
    # Clean up multiple spaces
    text = re.sub(r' +', ' ', text)
    
    # Remove non-printable except newlines/tabs
    text = ''.join(char if char.isprintable() or char in '\n\r\t' else ' ' for char in text)
    
    return text.strip()

def fix_encoding_in_csv(input_file: Path, output_file: Path):
    """Fix encoding issues in CSV file"""
    with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames
    
    # Clean all text fields
    for row in rows:
        for key in row:
            if isinstance(row[key], str):
                row[key] = clean_text(row[key])
    
    # Write cleaned data
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"✅ Fixed encoding in {len(rows)} rows")
    print(f"   Output: {output_file}")

if __name__ == "__main__":
    input_path = Path("data/enriched_resources.csv")
    output_path = Path("data/enriched_resources_cleaned.csv")
    fix_encoding_in_csv(input_path, output_path)
```

#### Step 2.2: Run encoding fix
```bash
python src/fix_encoding.py
```

#### Step 2.3: Replace original with cleaned version
```bash
# Backup original
cp data/enriched_resources.csv data/enriched_resources_backup.csv

# Use cleaned version
mv data/enriched_resources_cleaned.csv data/enriched_resources.csv
```

**Expected outcome:** All resources have clean, readable text

---

### Day 3: ADD KEYWORD-BASED FILTERING

**Goal:** Prevent false positives from entering the dataset

#### Step 3.1: Create pre-filtering script

Create new file: `src/filter_input_data.py`

```python
#!/usr/bin/env python3
"""Pre-filter resources by neurodivergent keywords"""
import csv
import re
from pathlib import Path
from typing import List, Tuple

# Neurodivergent-related keywords (INCLUDE if present)
ND_KEYWORDS = [
    r'\bautis[mt]\b', r'\bASD\b', r'\bASC\b',
    r'\bADHD\b', r'\bADD\b', r'\battention deficit\b',
    r'\bdyslex\w*\b', r'\bdysprax\w*\b', r'\bDCD\b',
    r'\bneurodiverg\w*\b',
    r'\bSEN\b', r'\bSEND\b', r'\bspecial educational needs\b',
    r'\blearning disabilit\w*\b', r'\blearning difficult\w*\b',
    r'\bAsperger\b',
    r'\bTourette\b',
    r'\bsensory processing\b',
    r'\bautism friendly\b',
]

# Generic service keywords (EXCLUDE if present WITHOUT ND keywords)
GENERIC_KEYWORDS = [
    r'\bGP surgery\b', r'\bgeneral practice\b',
    r'\bpharmacy\b', r'\bdentist\b', r'\boptician\b',
]

# Combine name and description for checking
def get_searchable_text(row: dict) -> str:
    """Combine searchable fields"""
    fields = [
        row.get('gmaps_name', ''),
        row.get('description_short', ''),
        row.get('gmaps_editorial_summary', ''),
        row.get('conditions_supported', ''),
        row.get('specific_services', ''),
    ]
    return ' '.join(str(f) for f in fields if f).lower()

def is_neurodivergent_related(row: dict) -> Tuple[bool, str]:
    """Check if resource is likely neurodivergent-related"""
    text = get_searchable_text(row)
    
    # Check for ND keywords
    nd_matches = [kw for kw in ND_KEYWORDS if re.search(kw, text, re.IGNORECASE)]
    
    if nd_matches:
        return True, f"Matched: {', '.join(nd_matches[:3])}"
    
    # Check for generic services (without ND keywords)
    generic_matches = [kw for kw in GENERIC_KEYWORDS if re.search(kw, text, re.IGNORECASE)]
    
    if generic_matches and not nd_matches:
        return False, f"Generic service: {generic_matches[0]}"
    
    # If enriched data exists, check validation fields
    if row.get('is_neurodivergent_related'):
        is_related = str(row.get('is_neurodivergent_related')).lower() in ['true', 'yes', '1']
        return is_related, "From validation field"
    
    # Default: keep for manual review
    return True, "No clear indicators (needs validation)"

def filter_resources(input_file: Path, output_file: Path, rejected_file: Path):
    """Filter resources by neurodivergent relevance"""
    with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames
    
    kept = []
    rejected = []
    reasons = []
    
    for row in rows:
        is_nd, reason = is_neurodivergent_related(row)
        if is_nd:
            kept.append(row)
        else:
            rejected.append(row)
            reasons.append({'name': row.get('gmaps_name'), 'reason': reason})
    
    # Write kept resources
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(kept)
    
    # Write rejected resources with reasons
    with open(rejected_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(fieldnames) + ['rejection_reason'])
        writer.writeheader()
        for row, reason_data in zip(rejected, reasons):
            row['rejection_reason'] = reason_data['reason']
            writer.writerow(row)
    
    print(f"\n✅ FILTERING COMPLETE")
    print(f"   Total input:     {len(rows)}")
    print(f"   Kept (ND-related): {len(kept)} ({len(kept)/len(rows)*100:.1f}%)")
    print(f"   Rejected:        {len(rejected)} ({len(rejected)/len(rows)*100:.1f}%)")
    print(f"\n   Output files:")
    print(f"   - Kept: {output_file}")
    print(f"   - Rejected: {rejected_file}")
    
    # Show sample rejections
    print(f"\n   Sample rejected resources:")
    for r in reasons[:10]:
        print(f"   - {r['name']}: {r['reason']}")

if __name__ == "__main__":
    input_path = Path("data/enriched_resources.csv")
    output_path = Path("data/neurodivergent_filtered.csv")
    rejected_path = Path("data/rejected_resources.csv")
    
    filter_resources(input_path, output_path, rejected_path)
```

#### Step 3.2: Run keyword filter
```bash
python src/filter_input_data.py
```

This will:
- Keep resources with ND keywords
- Reject generic services (GP surgeries, councils, etc.)
- Create separate file of rejected resources for manual review

**Expected outcome:** ~800-900 resources (removing ~150-250 obvious false positives)

---

### Day 4: REMOVE OUT-OF-SCOPE LOCATIONS

**Goal:** Focus on actual London/Greater London area

#### Step 4.1: Define geographic scope

Create new file: `src/filter_geography.py`

```python
#!/usr/bin/env python3
"""Filter resources by geographic scope"""
import csv
from pathlib import Path

# London boroughs + Greater London
LONDON_AREAS = {
    "Greater London",
    "London",
    "",  # Keep empty (will manual review)
}

# Nearby counties that might be included
NEARBY_COUNTIES = {
    "Hertfordshire", "Surrey", "Essex", "Kent", 
    "Berkshire", "Buckinghamshire"
}

def filter_by_geography(input_file: Path, london_only: bool = False):
    """Filter resources by location"""
    with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames
    
    london_resources = []
    nearby_resources = []
    far_resources = []
    
    for row in rows:
        county = row.get('gmaps_addr_admin_area_level_2', '').strip()
        
        if county in LONDON_AREAS:
            london_resources.append(row)
        elif county in NEARBY_COUNTIES:
            nearby_resources.append(row)
        else:
            far_resources.append(row)
    
    print(f"\n📍 GEOGRAPHIC ANALYSIS")
    print(f"   London/Greater London: {len(london_resources)} ({len(london_resources)/len(rows)*100:.1f}%)")
    print(f"   Nearby counties:       {len(nearby_resources)} ({len(nearby_resources)/len(rows)*100:.1f}%)")
    print(f"   Far/Unknown:           {len(far_resources)} ({len(far_resources)/len(rows)*100:.1f}%)")
    
    # Write London-only dataset
    london_file = input_file.parent / "london_only_resources.csv"
    with open(london_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(london_resources)
    
    print(f"\n   Created: {london_file}")
    print(f"   Contains {len(london_resources)} London resources")
    
    # Optionally include nearby if needed
    if not london_only:
        extended_file = input_file.parent / "london_extended_resources.csv"
        with open(extended_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(london_resources + nearby_resources)
        
        print(f"   Created: {extended_file}")
        print(f"   Contains {len(london_resources + nearby_resources)} resources (London + nearby)")

if __name__ == "__main__":
    input_path = Path("data/neurodivergent_filtered.csv")
    filter_by_geography(input_path, london_only=False)
```

#### Step 4.2: Run geographic filter
```bash
python src/filter_geography.py
```

**Decision point:** Do you want:
- **london_only_resources.csv** (~450 resources) - Strict London/Greater London only
- **london_extended_resources.csv** (~650 resources) - Include nearby counties

---

### Day 5: IDENTIFY & MERGE DUPLICATES

**Goal:** Merge duplicate entries for same organizations

#### Step 5.1: Create deduplication script

Create new file: `src/deduplicate.py`

```python
#!/usr/bin/env python3
"""Identify and merge duplicate resources"""
import csv
from pathlib import Path
from collections import defaultdict
from difflib import SequenceMatcher

def name_similarity(name1: str, name2: str) -> float:
    """Calculate name similarity (0-1)"""
    return SequenceMatcher(None, name1.lower(), name2.lower()).ratio()

def find_duplicates(rows: list, similarity_threshold: float = 0.85) -> list:
    """Find potential duplicates by name similarity"""
    duplicates = []
    
    for i, row1 in enumerate(rows):
        for j, row2 in enumerate(rows[i+1:], start=i+1):
            name1 = row1.get('gmaps_name', '')
            name2 = row2.get('gmaps_name', '')
            
            if not name1 or not name2:
                continue
            
            # Check name similarity
            sim = name_similarity(name1, name2)
            
            if sim >= similarity_threshold:
                duplicates.append({
                    'idx1': i,
                    'idx2': j,
                    'name1': name1,
                    'name2': name2,
                    'similarity': sim,
                    'place_id1': row1.get('gmaps_place_id'),
                    'place_id2': row2.get('gmaps_place_id'),
                })
    
    return duplicates

def analyze_duplicates(input_file: Path):
    """Analyze potential duplicates"""
    with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    duplicates = find_duplicates(rows)
    
    print(f"\n🔍 DUPLICATE ANALYSIS")
    print(f"   Total resources:      {len(rows)}")
    print(f"   Potential duplicates: {len(duplicates)} pairs")
    
    if duplicates:
        print(f"\n   Top 20 potential duplicates:")
        for i, dup in enumerate(sorted(duplicates, key=lambda x: -x['similarity'])[:20], 1):
            print(f"\n   {i}. Similarity: {dup['similarity']:.2f}")
            print(f"      - {dup['name1']}")
            print(f"      - {dup['name2']}")
            if dup['place_id1'] == dup['place_id2']:
                print(f"      ⚠️  SAME PLACE ID - Definite duplicate!")
    
    # Group by organization (e.g., all "National Autistic Society" locations)
    org_groups = defaultdict(list)
    for i, row in enumerate(rows):
        name = row.get('gmaps_name', '')
        # Extract base organization name
        base_name = name.split('-')[0].split('(')[0].strip()
        org_groups[base_name].append((i, name))
    
    # Show organizations with multiple locations
    multi_location_orgs = {k: v for k, v in org_groups.items() if len(v) > 1}
    
    print(f"\n   Organizations with multiple locations: {len(multi_location_orgs)}")
    print(f"\n   Top 10 multi-location organizations:")
    for org, locations in sorted(multi_location_orgs.items(), key=lambda x: -len(x[1]))[:10]:
        print(f"      - {org}: {len(locations)} locations")

if __name__ == "__main__":
    input_path = Path("data/london_extended_resources.csv")
    analyze_duplicates(input_path)
```

#### Step 5.2: Run duplicate analysis
```bash
python src/deduplicate.py
```

**Review output** - manually decide which duplicates to merge

**For now:** Just be aware of duplicates. Full deduplication is Week 2 task.

---

## 📊 WEEK 1 EXPECTED OUTCOMES

### Before Week 1
```
Total:           1,043 resources
Validated:           0 (0%)
Clean text:        579 (55.5%)
False positives: ~150-250 (est.)
```

### After Week 1
```
Total:             ~650 resources (cleaned dataset)
├─ Validated:       650 (100%) ✅
├─ ND-Relevant:    ~550 (85%)
├─ Clean text:      650 (100%) ✅
├─ In scope:        650 (100% London/nearby) ✅
└─ Duplicates:     ~50 pairs (flagged for Week 2)

Removed:
├─ False positives: ~150
├─ Out of scope:   ~150
├─ Not ND-related: ~100
```

---

## 🎯 WEEK 2+ ROADMAP

### Week 2: ENHANCE DATA QUALITY
- [ ] Merge identified duplicates
- [ ] Handle 262 resources without websites (alternative enrichment)
- [ ] Add structured age range fields
- [ ] Add referral requirements field
- [ ] Add cost/funding information

### Week 3: MULTI-SOURCE COLLECTION
- [ ] Scrape Charity Commission for registered charities
- [ ] Add CQC (Care Quality Commission) providers
- [ ] Cross-reference with NHS Service Directory
- [ ] Add National Autistic Society branch listings

### Week 4: USER-FACING IMPROVEMENTS
- [ ] Implement confidence scoring
- [ ] Add freshness tracking (last verified dates)
- [ ] Set up user feedback mechanism
- [ ] Create relationship mapping (parent orgs → branches)

---

## 💡 QUICK WINS (Can do TODAY)

1. **Run validation on enriched data:**
   ```bash
   python src/filter_neurodivergent.py \
     --input data/output/enriched_resources_parallel_20251024_201302.xlsx \
     --analyze
   ```

2. **Check how many are already validated** in your latest output files

3. **Review sample false positives** to understand data quality

4. **Decide geographic scope** - London only or include nearby counties?

---

## ❓ QUESTIONS FOR YOU

1. **Geographic Scope:** 
   - Strict London only (~450 resources)?
   - Include nearby counties (~650 resources)?
   - National services also (~850 resources)?

2. **Quality vs. Quantity:**
   - High precision (Medium+ relevance only) → ~550 resources
   - High recall (Low+ relevance) → ~700 resources
   - Maximum coverage (include unvalidated) → ~900 resources

3. **Resources without websites (262):**
   - Remove them entirely?
   - Manual verification?
   - Alternative enrichment method?

4. **Duplicate handling:**
   - Merge duplicates (single entry per org) → fewer resources
   - Keep separate locations (each branch separate) → more resources
   - Hybrid (parent org + branch relationship) → best UX

---

## 📞 NEED HELP?

If you want me to:
- ✅ Create any of the scripts above
- ✅ Run the analysis commands
- ✅ Review specific data samples
- ✅ Prioritize which improvements to tackle first

Just let me know!

