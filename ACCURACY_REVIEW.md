# Accuracy Review: Neurodivergent Resource Collection

**Date:** October 24, 2025  
**Focus:** Data Accuracy & Collection Method Improvements  
**Reviewer:** Code & Data Analysis

## Executive Summary

After reviewing the batch enrichment pipeline and sample data from ~1,926 resources, I've identified **10 critical accuracy issues** and **8 collection method improvements** that will significantly enhance the quality and reliability of your neurodivergent resource database.

---

## 🔴 CRITICAL ACCURACY ISSUES

### 1. **FALSE POSITIVES: Non-Neurodivergent Services**

**Problem:** The dataset includes many services that are NOT neurodivergent-specific:
- General GP surgeries (e.g., "Temple Hill Surgery")
- Generic community centers (e.g., "Ashford Community Centre")
- General schools without SEN specialization (e.g., "Bancroft's School")
- Standard youth theaters and entertainment venues
- General carer services (not specifically for neurodivergent conditions)

**Evidence from data:**
```csv
Row 308: Temple Hill Surgery - General GP surgery
Row 302: Ashford Community Centre - Generic community center
Row 322: Bush Hill Park Bowls Tennis & Social Club - General sports club
Row 326: Bancroft's School - Standard independent school
```

**Impact:** ~40-50% of resources may not be relevant to neurodivergent individuals

**Root Cause:** 
- Initial data source likely included all "family services" or "disability services"
- No filtering by neurodivergent-specific keywords during data collection
- The validation (`is_neurodivergent_related`) is only added AFTER enrichment, not during collection

### 2. **MISSING VALIDATION: 59.9% Unvalidated Resources**

**Problem:** From your own docs (MODULE_GUIDE.md):
```
❓ Unknown/Not validated:   625 (59.9%)
```

**Current Issue:**
- Old cached data has placeholder values: `"is_neurodivergent_related": true` (line 169 in batch_enrich_pipeline_parallel.py)
- Many resources never run through validation
- The system assumes neurodivergent if cached before validation feature existed

**Impact:** Cannot trust majority of dataset for actual neurodivergent relevance

### 3. **WEBSITE-DEPENDENT EXTRACTION: Missing Critical Data**

**Problem:** The enrichment process REQUIRES a website (line 280-281):
```python
if not website:
    return original_idx, None, [], f"{status_msg}: No website"
```

**Evidence from data:** Many high-quality resources have no website:
```csv
Row 10: Tower Hamlets Schools Office - No website field
Row 375: Supporting Asperger Families In Essex - No website
Row 329: Multiple resources with empty website fields
```

**Impact:** 
- Legitimate neurodivergent services without websites are ignored
- Phone-only or community-based services excluded
- Grassroots autism support groups often lack websites

**Solution Needed:** Alternative enrichment via:
- Phone number lookup + Google search
- Address-based search for organization info
- Manual verification pathway for no-website resources

### 4. **ENCODING CORRUPTION IN DATA**

**Problem:** Character encoding issues throughout dataset:
```csv
Opening hours: "9:00?AM?�?5:00?PM"  (should be "9:00 AM - 5:00 PM")
Names: "Wandsworth Carers� Centre" (should be "Wandsworth Carers' Centre")
Special characters replaced with ? and �
```

**Root Cause:** 
- Google Maps data uses UTF-8 with special characters (em-dash, curly quotes)
- CSV export/import chain loses encoding
- `clean_text_for_excel()` function (line 308-356) tries to fix but applied ONLY during Excel export, not at data ingestion

**Impact:**
- Data looks unprofessional
- Search and matching may fail on corrupted names
- User experience degraded

**Solution:** Apply cleaning at data INGESTION, not just export

### 5. **OVER-RELIANCE ON LLM CATEGORIZATION**

**Problem:** The `categorize_resource()` function (line 388-428) uses LLM for every categorization

**Issues:**
- LLM categorization is inconsistent (same resource may get different categories)
- Expensive (API costs for 2000+ resources)
- No validation or confidence scoring
- Categories may not match user's mental model
- Line 426-427: Falls back to "Unknown Category" on ANY error (masks problems)

**Better Approach:**
- Use rule-based categorization for obvious cases (e.g., if name contains "diagnosis", category = Assessment & Diagnosis)
- Use LLM only for ambiguous cases
- Implement category confidence scoring
- Allow multiple categories per resource (many services span multiple areas)

### 6. **WEAK NEURODIVERGENT CONDITION DETECTION**

**Problem:** No explicit validation that conditions are neurodivergent-related

**Evidence from LLM prompt (web_llm_extract.py, line 165):**
```
• conditions_supported: List neurodivergent conditions (ADHD, Autism/ASC, Dyslexia, etc.)
```

**Missing Conditions:**
- Tourette's Syndrome (often omitted)
- Dyscalculia (rarely mentioned)
- Sensory Processing Disorder
- Developmental Coordination Disorder (DCD/Dyspraxia)
- Fetal Alcohol Spectrum Disorder (FASD)

**Issue:** LLM may extract "mental health" or "anxiety" as conditions, which are NOT neurodivergent conditions (though they may co-occur)

**Solution:** 
- Explicit whitelist of neurodivergent conditions
- Post-processing to filter out non-ND conditions
- Tag co-occurring conditions separately

### 7. **AGE RANGE INCONSISTENCY**

**Problem:** Age ranges are stored as free text with inconsistent formats:

**Examples from data:**
```
"Adults (18+)"
"All ages"
"Ages 4½ to 22"  (uses special character)
"Children (0-11), Young People (12-17), up to 25 for SEND"
```

**Impact:**
- Cannot filter by age range programmatically
- Cannot find services for specific age groups
- Searching for "adult services" requires complex text matching

**Solution:**
- Structured age range fields: `age_min`, `age_max`, `age_category`
- Standardized categories: Child (0-11), Teen (12-17), Young Adult (18-25), Adult (25+), All Ages
- Allow multiple age ranges per service

### 8. **DUPLICATE DETECTION MISSING**

**Problem:** No deduplication logic in the pipeline

**Potential Issues in Data:**
```csv
Row 8: "National Autistic Society" (Weston House)
Row 132: "National Autistic Society" (6 St Edwards Cl)
Row 18: "The National Autistic Society Centre, Greater London,Croydon"
Row 20: "The National Autistic Society Centre, Greater London (Ladbroke Grove)"
```

**These may be:**
- Same organization, multiple locations (should be linked)
- Duplicate entries (should be merged)
- Different branches (should have parent-child relationship)

**Impact:** Inflated resource counts, confused users

**Solution Needed:**
- Fuzzy name matching with Levenshtein distance
- Address-based proximity detection
- Place ID comparison (many entries share place IDs)
- Organization hierarchy (national org → local branches)

### 9. **LOCATION ACCURACY: Geographic Scope Issues**

**Problem:** Dataset claims to be "London neurodivergent resources" but includes:

**Non-London locations:**
```csv
Row 23: Stevenage (Hertfordshire) - "Church Farm Ardeley"
Row 25: Basildon (Essex) - "Papworth Trust"
Row 101: Stevenage again - "TRACKS autism"
Row 123: Chelmsford (Essex) - "Museum of Chelmsford"
Row 126: Colchester (Essex) - "Consensus Support"
Row 323: Uckfield (East Sussex) - "Bellbrook Centre"
Row 378: Eastleigh (Hampshire) - "Reach Out Caring"
Row 386: Farnham (Surrey) - "Challengers Playscheme"
```

**Issue:** 
- No clear geographic boundary
- "Greater London" includes areas 50+ miles from London
- Users expect London services, get results from different counties

**Solution:**
- Define explicit geographic scope (London boroughs only? 30-mile radius?)
- Add `geographic_scope` field: Local, Regional, National, Online
- Allow filtering by actual user location
- Tag national organizations separately

### 10. **MISSING CRITICAL METADATA**

**Problem:** Essential filtering fields are absent or inconsistent:

**Missing Fields:**
- **Referral Requirements:** Self-referral, GP referral, professional referral only?
- **Cost:** Free, NHS funded, paid, insurance accepted?
- **Wait Times:** Immediate, weeks, months?
- **Service Availability:** Currently accepting new clients? Waitlist status?
- **Accessibility:** Physical accessibility, sensory accommodations, communication support?
- **Languages Supported:** English only? Other languages?
- **Online Services:** In-person only, online available, hybrid?

**Impact:** Users can't filter for actually accessible services

**Evidence:** The current schema (lines 62-83 in batch_enrich_pipeline_parallel.py) has fields like:
```python
"conditions_supported"
"specific_services"
"organization_type"
```

But missing the above critical filters.

---

## 🟡 COLLECTION METHOD IMPROVEMENTS

### Improvement 1: **MULTI-SOURCE DATA COLLECTION**

**Current:** Single source → Google Maps Places API

**Problem:** 
- Google Maps is incomplete for small organizations
- Many autism support groups don't have GMaps listings
- Community-based services often not on Google

**Recommendation:**
```
PRIMARY SOURCES:
1. Google Maps Places API (current)
2. Charity Commission register (for UK registered charities)
3. Care Quality Commission (CQC) register (for regulated care providers)
4. Local Authority SEND directories (each London borough publishes)
5. NHS Service Directory
6. National Autistic Society directory
7. ADHD Foundation directory

SECONDARY SOURCES:
- Autism.org.uk listings
- Contact (for families with disabled children) directory
- IPSEA (SEN education) database
```

### Improvement 2: **KEYWORD-BASED INITIAL FILTERING**

**Current:** Scrape all "health services" then validate later

**Better Approach:** Filter during collection
```python
NEURODIVERGENT_KEYWORDS = [
    "autism", "autistic", "ASD", "ASC",
    "ADHD", "ADD", "attention deficit",
    "dyslexia", "dyspraxia", "DCD",
    "neurodivergent", "neurodiversity",
    "SEN", "SEND", "special educational needs",
    "learning disabilities", "learning difficulties",
    "developmental disabilities",
    "sensory processing",
    "Asperger", "Aspergers"  # legacy term still used
]

EXCLUSION_KEYWORDS = [
    "general practitioner", "GP surgery",
    "hospital" (unless + autism keyword),
    "pharmacy",
    "dentist",
    "optician"
]
```

**Implementation:** Add keyword filter in initial Google Places search query

### Improvement 3: **STRUCTURED DATA VALIDATION**

**Current:** LLM extracts free text, minimal validation

**Recommendation:** Add validation layer after LLM extraction

```python
def validate_extracted_data(data: Dict) -> Tuple[bool, List[str]]:
    """Validate LLM output for data quality"""
    errors = []
    
    # Validate conditions are actually neurodivergent
    valid_conditions = {"ADHD", "Autism", "ASC", "Dyslexia", "Dyspraxia", "Tourette", ...}
    for condition in data.get("conditions_supported", []):
        if not any(vc in condition for vc in valid_conditions):
            errors.append(f"Invalid condition: {condition}")
    
    # Validate age range format
    age_range = data.get("age_range", "")
    if age_range and not re.match(r"\d+|\ball ages\b|adult|child", age_range.lower()):
        errors.append(f"Invalid age range format: {age_range}")
    
    # Validate organization type is from allowed list
    valid_org_types = {"NHS Service", "Charity/Non-profit", "Local Authority", ...}
    if data.get("organization_type") not in valid_org_types:
        errors.append(f"Invalid org type: {data.get('organization_type')}")
    
    # Validate neurodivergent relevance is actually justified
    if data.get("is_neurodivergent_related") == True:
        if not data.get("neurodivergent_focus") or len(data.get("neurodivergent_focus")) < 10:
            errors.append("Claimed ND-related but no focus description")
    
    return len(errors) == 0, errors
```

### Improvement 4: **CONFIDENCE SCORING**

**Current:** Binary validation (true/false for neurodivergent-related)

**Better:** Multi-factor confidence score

```python
def calculate_confidence_score(data: Dict, extraction_metadata: Dict) -> float:
    """Calculate confidence in data quality (0-100)"""
    score = 100.0
    
    # Deduct for missing fields
    critical_fields = ["description_short", "conditions_supported", "specific_services"]
    for field in critical_fields:
        if not data.get(field) or data.get(field) == "Not specified":
            score -= 15
    
    # Deduct for low LLM confidence
    if extraction_metadata.get("data_confidence") == "Low":
        score -= 20
    elif extraction_metadata.get("data_confidence") == "Medium":
        score -= 10
    
    # Boost for explicit neurodivergent keywords in description
    description = (data.get("description_short", "") or "").lower()
    nd_keywords = ["autism", "adhd", "dyslexia", "neurodivergent"]
    keyword_count = sum(1 for kw in nd_keywords if kw in description)
    score += min(keyword_count * 5, 20)
    
    # Deduct for vague categorization
    if data.get("category") == "Unknown/Uncategorized":
        score -= 25
    
    # Boost for official registration (NHS, CQC, Charity Commission)
    if "NHS" in (data.get("organization_type") or ""):
        score += 10
    
    return max(0.0, min(100.0, score))
```

**Usage:** Filter resources by confidence threshold (e.g., only show 70+ confidence)

### Improvement 5: **HUMAN VALIDATION WORKFLOW**

**Current:** Fully automated, no human review

**Recommendation:** Hybrid approach

```
AUTOMATED TIER (High Confidence):
- Clear neurodivergent keywords in name
- Official registration (CQC, Charity Commission)
- Detailed website with explicit ND focus
→ Auto-approve, no human review needed

REVIEW TIER (Medium Confidence):
- Generic names but ND services listed
- Limited website content
- New/unknown organizations
→ Flag for quick human review (5 min per resource)

MANUAL TIER (Low Confidence):
- No website
- Ambiguous services
- Potential false positives
→ Detailed human verification required
```

**Implementation:** Add `validation_status` field:
- `auto_validated` (high confidence)
- `pending_review` (needs human check)
- `manually_verified` (human confirmed)
- `rejected` (not neurodivergent-related)

### Improvement 6: **REAL-TIME DATA FRESHNESS**

**Current:** Static snapshot, no update mechanism

**Problem visible in data:**
```csv
"status,last_verified"
"Active & Verified,03/10/2025"
"Active - Needs Verification,03/10/2025"
```

**Recommendations:**

```python
# Add freshness tracking
FRESHNESS_RULES = {
    "website_content": 90,  # Re-scrape every 90 days
    "contact_info": 180,    # Re-verify every 6 months
    "service_availability": 30,  # Check monthly if still accepting clients
    "opening_hours": 90,    # Re-check quarterly
}

def needs_refresh(resource: Dict) -> bool:
    """Check if resource data is stale"""
    last_updated = resource.get("last_verified")
    if not last_updated:
        return True
    
    days_old = (datetime.now() - parse_date(last_updated)).days
    
    # Different fields have different freshness requirements
    if resource.get("status") == "Active - Needs Verification":
        return days_old > 30  # Verify sooner if uncertain
    
    return days_old > 180  # General refresh every 6 months
```

**Implement:**
- Background job to re-scrape stale data
- User feedback mechanism ("Is this info still accurate?")
- Automatic flagging of resources with bounced emails/disconnected phones

### Improvement 7: **USER FEEDBACK INTEGRATION**

**Current:** One-way data flow (scrape → enrich → publish)

**Recommendation:** Feedback loop

```python
# Add user feedback fields
FEEDBACK_SCHEMA = {
    "user_reports": {
        "helpful_count": int,
        "not_helpful_count": int,
        "comments": [
            {
                "date": datetime,
                "user_id": str,
                "feedback_type": "incorrect_info|outdated|not_neurodivergent|helpful",
                "details": str
            }
        ]
    },
    "accuracy_score": float,  # Calculated from user feedback
    "last_user_verification": datetime
}
```

**Benefits:**
- Crowd-sourced accuracy improvement
- Identify outdated listings faster
- Build trust with users

### Improvement 8: **LINKED DATA & RELATIONSHIPS**

**Current:** Flat list of independent resources

**Better:** Graph of relationships

```python
RELATIONSHIP_TYPES = {
    "parent_organization": "This location is part of larger org",
    "partnership": "Works with another resource",
    "referral_pathway": "Refers clients to another service",
    "same_location": "Multiple services at same address",
    "successor": "Organization replaced previous one"
}

# Example: National Autistic Society
{
    "id": "nas_national",
    "name": "National Autistic Society",
    "type": "national_organization",
    "branches": [
        {"id": "nas_croydon", "name": "NAS Centre - Croydon"},
        {"id": "nas_ladbroke", "name": "NAS Centre - Ladbroke Grove"},
        {"id": "nas_enfield", "name": "Enfield National Autistic Society"}
    ]
}
```

**Benefits:**
- Reduce duplicate confusion
- Show users service ecosystem
- Enable "Similar Services" recommendations

---

## 📊 IMPACT ASSESSMENT

### Current State
- **Total Resources:** ~1,926
- **Validated ND-Related:** ~30.5% (318)
- **Unvalidated:** ~59.9% (625)
- **Not ND-Related:** ~9.6% (100)
- **Estimated False Positives:** 40-50% of total

### After Improvements
- **Expected Precision:** 85-90% (vs current ~50%)
- **Expected Coverage:** +200-300 genuine ND services found via multi-source
- **Data Freshness:** 95% of resources verified within 6 months
- **User Trust:** Confidence scoring shows data quality upfront

---

## 🎯 PRIORITY RECOMMENDATIONS

### IMMEDIATE (Week 1)
1. **Run validation on all existing resources** - Filter out false positives
   ```bash
   python batch_enrich_pipeline_parallel.py --input enriched_resources.csv --validate-only
   python filter_neurodivergent.py --filter --min-score Medium
   ```

2. **Fix encoding issues** - Apply `clean_text_for_excel()` at ingestion
3. **Add keyword filtering** - Filter Google Maps queries before scraping

### SHORT TERM (Month 1)
4. **Implement deduplication** - Merge duplicate organizations
5. **Add confidence scoring** - Show data quality to users
6. **Structured age ranges** - Enable filtering by age group
7. **Define geographic scope** - Remove out-of-scope resources

### MEDIUM TERM (Months 2-3)
8. **Multi-source collection** - Add Charity Commission, CQC, NHS directory
9. **Validation workflow** - Set up human review for medium-confidence resources
10. **Freshness tracking** - Implement automatic re-validation

### LONG TERM (Months 4-6)
11. **User feedback system** - Allow crowd-sourced accuracy improvements
12. **Relationship mapping** - Build organization hierarchy
13. **Enhanced metadata** - Add referral requirements, costs, wait times

---

## 🧪 TESTING RECOMMENDATIONS

### Data Quality Tests
```python
def test_neurodivergent_relevance():
    """Test that resources are actually ND-related"""
    resources = load_resources()
    for r in resources:
        if r.get("is_neurodivergent_related"):
            # Must have at least one ND condition
            assert len(r.get("conditions_supported", [])) > 0
            # Must have explanation
            assert len(r.get("neurodivergent_focus", "")) > 20

def test_no_generic_services():
    """Test that generic services are filtered out"""
    generic_keywords = ["general practice", "gp surgery", "pharmacy"]
    resources = load_resources()
    for r in resources:
        name_lower = r.get("gmaps_name", "").lower()
        for keyword in generic_keywords:
            assert keyword not in name_lower, f"Generic service found: {r['gmaps_name']}"

def test_geographic_scope():
    """Test resources are within defined area"""
    resources = load_resources()
    for r in resources:
        county = r.get("gmaps_addr_admin_area_level_2")
        assert county == "Greater London", f"Out of scope: {county}"
```

---

## 📝 CONCLUSION

Your pipeline architecture is solid for PROCESSING data, but the accuracy issues stem from:

1. **Input data quality** (collecting non-ND services)
2. **Lack of validation** during collection (only after enrichment)
3. **Missing structured metadata** (can't filter effectively)
4. **No deduplication** (inflated counts)
5. **No freshness tracking** (data goes stale)

**The good news:** These are fixable with the improvements above. Focus on:
- ✅ Filtering during collection (not just validation after)
- ✅ Structured validation rules (not just LLM confidence)
- ✅ Multi-source data collection (not just Google Maps)
- ✅ Human review workflow (hybrid automation)

**Expected Outcome:** A high-quality, trustworthy database of 800-1000 genuinely neurodivergent-focused resources in London, with clear quality indicators and up-to-date information.

