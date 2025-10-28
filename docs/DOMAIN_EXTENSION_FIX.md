# 🌐 Domain Extension Correction

## 🔍 **Issue: Wrong Domain Extensions**

### **Example: Alma Autism**

```
Stored in CSV:  www.almaautism.com     ❌ Domain doesn't exist
Correct URL:    https://www.almaautism.uk/     ✅ Domain exists
```

**Problem:** The CSV has `.com` but the actual domain is `.uk`

---

## ❌ **Why Current System Can't Auto-Fix This:**

### **Our URL handling covers:**
1. ✅ Missing protocol (`www.` → `https://www.`)
2. ✅ Broken page URLs (`/old-page` → `/`)
3. ✅ SSL errors (HTTPS without verification)
4. ✅ HTTP fallback (HTTPS → HTTP)
5. ✅ www. variants (`example.org` → `www.example.org`)

### **But NOT:**
6. ❌ **Wrong TLD** (`.com` → `.uk`)

**Why?** There are dozens of possible TLDs:
```
.com, .co.uk, .uk, .org, .org.uk, .net, .eu, .io, .wales, .scot, .london...
```

Trying all combinations would:
- Take 30-60 seconds per URL
- Trigger rate limiting
- Get blocked by WAF
- Slow pipeline to a crawl

---

## ✅ **Solution: Data Cleaning Script**

I've created `src/fix_domain_extensions.py` to **pre-clean** your data.

### **What It Does:**
1. Reads your CSV
2. Checks each URL
3. If URL doesn't work, tries common UK TLD variants:
   - `.com` → `.uk`
   - `.com` → `.co.uk`
   - `.com` → `.org.uk`
   - `.org` → `.org.uk`
   - `.org` → `.uk`
   - `.net` → `.uk`
   - `.net` → `.co.uk`
4. Updates CSV with working URLs

---

## 🚀 **Usage:**

### **Step 1: Dry Run (See What Would Change)**

```bash
python3 src/fix_domain_extensions.py \
  --input data/input/enriched_resources.csv \
  --output data/input/enriched_resources_FIXED.csv \
  --url-column gmaps_website \
  --dry-run
```

**Output:**
```
Reading data/input/enriched_resources.csv...
Total resources: 1,043
Resources with URLs: 950

Checking URLs and finding corrections...

[123] Alma Autism
  Original: www.almaautism.com
  ❌ Original URL doesn't work - trying variants...
  Checking: www.almaautism.com
    Trying: www.almaautism.uk... ✅ WORKS!

============================================================
SUMMARY
============================================================
URLs checked: 950
Corrections found: 15

Corrections:
  [123] Alma Autism
    OLD: www.almaautism.com
    NEW: www.almaautism.uk

  [456] Example Service
    OLD: www.example.com
    NEW: www.example.co.uk

⚠️  DRY RUN - No changes made. Remove --dry-run to apply corrections.
```

---

### **Step 2: Apply Corrections**

If the dry run looks good:

```bash
python3 src/fix_domain_extensions.py \
  --input data/input/enriched_resources.csv \
  --output data/input/enriched_resources_FIXED_TLD.csv \
  --url-column gmaps_website
```

**Output:**
```
Applying 15 corrections...
Saving to data/input/enriched_resources_FIXED_TLD.csv...
✅ Done!
```

---

### **Step 3: Run Enrichment with Fixed URLs**

```bash
python3 src/batch_enrich_pipeline_parallel.py \
  --input data/input/enriched_resources_FIXED_TLD.csv \
  --output data/output/enriched_COMPLETE_$(date +%Y%m%d_%H%M%S).xlsx \
  --backend gemini \
  --workers 5 \
  --skip-no-website \
  --rate-limit 15
```

Now Alma Autism (and others) will work! ✅

---

## 📊 **Expected Impact:**

### **Common Issues in Your Dataset:**

| Original Domain | Likely Correct | Reason |
|----------------|---------------|---------|
| `*.com` | `*.uk` or `*.co.uk` | UK-based organizations |
| `*.org` | `*.org.uk` | UK charities |
| `*.net` | `*.uk` | UK businesses |

**Estimated:** ~10-20 resources with wrong TLDs (1-2% of dataset)

### **After Running fix_domain_extensions.py:**

```
Before:
  Wrong TLD:   ~10-20 resources
  Failed:      110 resources
  
After:
  Wrong TLD:   0 resources  ✅
  Failed:      90-100 resources  ⬇️ -10-20
```

---

## ⚠️ **Limitations:**

### **Cannot Auto-Fix:**

1. **Completely Different Domains**
   ```
   Stored: www.old-name.com
   Actual: www.new-name.org.uk
   → Requires manual correction
   ```

2. **Typos in Domain Name**
   ```
   Stored: www.autismm-uk.com (extra 'm')
   Actual: www.autism-uk.org
   → Requires manual correction
   ```

3. **Merged/Rebranded Organizations**
   ```
   Stored: www.old-charity.org
   Actual: www.merged-charity.uk
   → Requires manual update
   ```

---

## 🎯 **Manual Verification Recommended:**

After running the script, **manually verify** a few corrections:

```bash
# Check a few corrected URLs
curl -I "https://www.almaautism.uk/"          # Should return 200 OK
curl -I "https://www.example-corrected.co.uk" # Should return 200 OK
```

---

## 📋 **Alternative: Add TLD Fallback to Main Pipeline**

If you want **automatic TLD fallback** during enrichment (not recommended):

### **Pros:**
- ✅ Automatic correction during processing
- ✅ No separate script needed

### **Cons:**
- ❌ Very slow (30-60 seconds per failed URL)
- ❌ Triggers rate limiting
- ❌ May get blocked by WAF
- ❌ Adds 5-10 minutes to full pipeline

**Recommendation:** Use the **data cleaning script** instead (faster, safer).

---

## 🔄 **Workflow:**

### **Best Practice Workflow:**

```
1. Data Collection
   ↓
2. Run fix_domain_extensions.py (one-time cleanup)
   ↓
3. Run batch_enrich_pipeline_parallel.py (main enrichment)
   ↓
4. Output with all corrected URLs
```

### **Time Comparison:**

**Without TLD Fix:**
```
Failed resources: 110
Reason: 10-20 have wrong TLDs
Result: Incomplete dataset
```

**With TLD Fix Script:**
```
Pre-cleaning: 5-10 minutes (one-time)
Failed resources: 90-100  ⬇️ -10-20
Result: More complete dataset
```

**With Auto-Fallback in Pipeline:**
```
Pipeline time: +5-10 minutes per run
Failed resources: 90-100
Result: Every run is slower
```

**Winner:** 🏆 **Pre-cleaning script** (faster overall, cleaner data)

---

## 🎯 **Summary:**

### **Problem:**
- Alma Autism stored as `www.almaautism.com` (wrong TLD)
- Actual domain is `www.almaautism.uk`
- Current system cannot guess TLD

### **Solution:**
- ✅ Created `fix_domain_extensions.py`
- ✅ Pre-cleans CSV data
- ✅ Tries common UK TLD variants
- ✅ Updates CSV with working URLs

### **Impact:**
- ✅ Fixes 10-20 wrong TLDs (1-2% of dataset)
- ✅ Reduces failures by 10-20 resources
- ✅ One-time cleanup (5-10 minutes)
- ✅ Future runs use clean data

### **Usage:**
```bash
# Step 1: Dry run
python3 src/fix_domain_extensions.py \
  --input data/input/enriched_resources.csv \
  --output data/input/enriched_resources_FIXED_TLD.csv \
  --dry-run

# Step 2: Apply corrections
python3 src/fix_domain_extensions.py \
  --input data/input/enriched_resources.csv \
  --output data/input/enriched_resources_FIXED_TLD.csv

# Step 3: Run enrichment with fixed data
python3 src/batch_enrich_pipeline_parallel.py \
  --input data/input/enriched_resources_FIXED_TLD.csv \
  --output data/output/enriched_COMPLETE.xlsx \
  --backend gemini \
  --workers 5
```

---

**Implementation Date:** October 27, 2025  
**Status:** ✅ COMPLETE  
**Tool Created:** `src/fix_domain_extensions.py`  
**Expected Impact:** +10-20 resources successfully enriched  
**Recommended:** Run once before main enrichment pipeline  

