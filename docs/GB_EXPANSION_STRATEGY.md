# Great Britain Expansion Strategy
## Neurodivergent Resource Toolkit - National Rollout Plan

**Date:** October 24, 2025  
**Current Coverage:** London & surrounding areas (641 resources = 61.4%)  
**Target:** Full GB coverage (England, Scotland, Wales, Northern Ireland)

---

## 📊 CURRENT STATE ANALYSIS

### Geographic Distribution (After Location Fix)
```
✅ Phase 1 Ready - London Core:           481 resources (46.1%)
✅ Phase 2 Ready - London Adjacent:       160 resources (15.3%)
   ├─ South East (Surrey, Kent, etc.):     87 resources
   └─ East of England (Essex, Herts):      73 resources

🟡 Phase 3 - Extended GB:                   1 resource  (0.1%)   ← NEEDS EXPANSION
🇬🇧 National Services:                     12 resources (1.2%)
❌ Unknown Location (need more data):     389 resources (37.3%)
```

### Coverage Gaps
```
STRONG COVERAGE:
✅ London/Greater London:        481 (46.1%)
✅ South East England:            87 (8.3%)
✅ East of England:               73 (7.0%)

WEAK/NO COVERAGE:
❌ West Midlands:                 <1%
❌ North West:                    <1%
❌ Yorkshire:                     <1%
❌ North East:                    <1%
❌ South West:                    <1%
❌ Scotland:                      0
❌ Wales:                         0
❌ Northern Ireland:              0
```

**Priority:** Systematically collect resources from underrepresented regions

---

## 🎯 THREE-PHASE ROLLOUT PLAN

### **Phase 1: LONDON CORE** (Current - Weeks 1-4)
**Goal:** Perfect the London dataset as proof-of-concept

**Actions:**
1. ✅ Validate all 481 London resources for ND-relevance
2. ✅ Fix encoding issues (44.5% affected)
3. ✅ Remove false positives
4. ✅ Add rich metadata (age ranges, costs, referrals)
5. ✅ Implement confidence scoring
6. ✅ Set up user feedback mechanism

**Target Quality Metrics:**
- 85%+ ND-relevance validation rate
- 90%+ with complete contact info
- 95%+ with clean, readable text
- 80%+ with rich metadata (age, cost, etc.)

**Expected Outcome:** ~400 high-quality validated London resources

---

### **Phase 2: LONDON ADJACENT** (Weeks 5-8)
**Goal:** Expand to surrounding South East & East of England

**Current Resources:** 160 (South East: 87, East of England: 73)

**Actions:**
1. Apply Phase 1 quality process to 160 existing resources
2. **Targeted collection in major population centers:**
   - **South East:** Brighton, Reading, Oxford, Slough, Guildford
   - **East of England:** Cambridge, Norwich, Ipswich, Luton, Southend
3. Focus on major cities/towns (50k+ population)
4. Cross-reference with local authority SEND directories

**New Data Sources for Phase 2:**
- Local Authority SEND Local Offers (mandatory for each LA)
- CQC (Care Quality Commission) register - filter by region
- Charity Commission - filter by area of benefit
- NHS Service Directory - regional filtering

**Target:** 300-400 resources in London Adjacent region

---

### **Phase 3: NATIONAL ROLLOUT** (Months 3-12)
**Goal:** Systematic GB-wide coverage

#### **3A: Major Cities First** (Months 3-6)
Focus on 20 largest UK cities outside London/SE:

**Priority Tier 1 Cities (500k+ population):**
1. Birmingham (West Midlands) - 1.1M
2. Manchester (North West) - 550k
3. Glasgow (Scotland) - 635k
4. Leeds (Yorkshire) - 800k
5. Liverpool (North West) - 500k
6. Edinburgh (Scotland) - 525k
7. Bristol (South West) - 465k
8. Sheffield (Yorkshire) - 585k

**Expected:** 50-100 resources per major city = 400-800 resources

**Priority Tier 2 Cities (250k-500k population):**
- Nottingham, Leicester, Newcastle, Cardiff, Bradford, Belfast, Southampton, Portsmouth, Oxford, Cambridge

**Expected:** 30-50 resources per city = 300-500 resources

#### **3B: Regional Coverage** (Months 7-12)
Systematic sweep of all UK regions:

**Target Coverage Per Region:**
- **North West** (Lancashire, Merseyside, Greater Manchester): 200-300 resources
- **Yorkshire and Humber**: 150-200 resources
- **West Midlands**: 150-200 resources
- **East Midlands**: 100-150 resources
- **South West** (Devon, Cornwall, Bristol, Somerset): 150-200 resources
- **North East** (Durham, Northumberland, Tyne and Wear): 100-150 resources
- **Scotland**: 200-300 resources
- **Wales**: 100-150 resources
- **Northern Ireland**: 50-100 resources

**Total Phase 3 Target:** 1,200-1,800 resources across GB

---

## 📚 DATA SOURCES FOR GB EXPANSION

### **Priority 1: Official Registries** (High Quality, Structured)
1. **Care Quality Commission (CQC)** - https://www.cqc.org.uk/
   - All registered care providers
   - Filter by: service type, region, rating
   - API available: https://api.cqc.org.uk/
   - **Coverage:** England only (Scotland/Wales/NI have separate registers)

2. **Charity Commission Register** - https://register-of-charities.charitycommission.gov.uk/
   - All UK registered charities
   - Filter by: area of benefit, activities
   - Bulk data download available
   - **Coverage:** England & Wales (Scotland has separate register)

3. **NHS Service Directory** - https://www.nhs.uk/service-search
   - Mental health services, CAMHS, specialist clinics
   - Regional filtering available
   - **Coverage:** England (Scotland/Wales/NI have separate systems)

4. **Local Authority SEND Local Offers** (Mandatory since 2014)
   - Every LA must publish directory of SEND services
   - 152 Local Authorities in England
   - Direct URLs: `https://[council-name].local-offer.org/`
   - **Coverage:** England (Scotland/Wales/NI have different systems)

### **Priority 2: Neurodivergent-Specific Organizations**
5. **National Autistic Society (NAS)** - https://www.autism.org.uk/
   - Branch finder
   - Service directory
   - Comprehensive autism-specific listings

6. **ADHD Foundation** - https://adhdfoundation.org.uk/
   - Service directory
   - Support groups

7. **British Dyslexia Association** - https://www.bdadyslexia.org.uk/
   - Accredited assessors directory
   - Local dyslexia associations

8. **Contact (for families with disabled children)** - https://contact.org.uk/
   - Helpline database
   - Local support groups

9. **IPSEA (SEN education law)** - https://www.ipsea.org.uk/
   - SEND tribunal representatives
   - Education advice services

### **Priority 3: Regional Registers** (Scotland, Wales, NI)
10. **Care Inspectorate Scotland** - https://www.careinspectorate.com/
11. **Care Inspectorate Wales** - https://careinspectorate.wales/
12. **RQIA Northern Ireland** - https://www.rqia.org.uk/
13. **OSCR (Scottish Charity Register)** - https://www.oscr.org.uk/

### **Priority 4: Community Sources** (Lower quality, needs validation)
14. **Google Maps Places API** (current method)
15. **Facebook Groups** - Local autism/ADHD parent groups
16. **Mumsnet/Netmums** - Parent recommendations
17. **Special Needs Jungle** - User-submitted directory

---

## 🤖 AUTOMATED COLLECTION SCRIPTS

### **Script 1: CQC API Integration**
Create: `src/collect_cqc_services.py`

```python
#!/usr/bin/env python3
"""
Collect neurodivergent services from CQC register
CQC API: https://api.cqc.org.uk/
"""

import requests
from typing import List, Dict

CQC_API_BASE = "https://api.cqc.org.uk/public/v1"

# Service types relevant to neurodivergent support
RELEVANT_SERVICE_TYPES = [
    "Community based services for people with learning disabilities",
    "Community based services for people with mental health needs",
    "Domiciliary care agency",
    "Supported living service",
    "Residential special school",
]

# Care activities relevant to ND
RELEVANT_CARE_ACTIVITIES = [
    "Learning disabilities",
    "Autism",
    "Mental health",
]

def search_cqc_services(region: str = None) -> List[Dict]:
    """Search CQC for relevant services"""
    
    # CQC regions: London, South East, East of England, etc.
    params = {
        "careHome": "Y",  # Include care homes
        "perPage": 500,
    }
    
    if region:
        params["region"] = region
    
    response = requests.get(f"{CQC_API_BASE}/locations", params=params)
    
    if response.status_code == 200:
        data = response.json()
        return data.get("locations", [])
    else:
        return []

def filter_neurodivergent_services(services: List[Dict]) -> List[Dict]:
    """Filter CQC services for neurodivergent relevance"""
    
    nd_services = []
    
    for service in services:
        # Check service type
        service_types = service.get("serviceTypes", [])
        for st in service_types:
            if any(relevant in st.get("name", "") for relevant in RELEVANT_SERVICE_TYPES):
                nd_services.append(service)
                break
        
        # Check care activities
        specialisms = service.get("specialisms", [])
        for spec in specialisms:
            if any(relevant in spec.get("name", "") for relevant in RELEVANT_CARE_ACTIVITIES):
                if service not in nd_services:
                    nd_services.append(service)
                break
    
    return nd_services

# Usage:
# services = search_cqc_services(region="London")
# nd_services = filter_neurodivergent_services(services)
```

### **Script 2: Local Authority SEND Scraper**
Create: `src/collect_local_authority_send.py`

```python
#!/usr/bin/env python3
"""
Scrape Local Authority SEND Local Offer directories
Each LA has mandatory SEND local offer site
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict

# 152 Local Authorities in England - sample
LOCAL_AUTHORITIES = {
    # London
    "Barnet": "https://www.barnet.gov.uk/children-and-families/send-local-offer",
    "Camden": "https://www.camden.gov.uk/send-local-offer",
    "Hackney": "https://www.hackneylocaloffer.co.uk/",
    
    # South East
    "Brighton and Hove": "https://www.brighton-hove.gov.uk/send-local-offer",
    "Surrey": "https://www.surreylocaloffer.org.uk/",
    
    # Add all 152 LAs...
}

def scrape_send_directory(la_name: str, url: str) -> List[Dict]:
    """Scrape SEND directory from LA website"""
    
    # Each LA has different structure - need custom scrapers
    # But they all must have:
    # - Directory of services
    # - Contact information
    # - Service descriptions
    
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract service listings
        # (LA-specific parsing logic here)
        
        services = []
        return services
    
    except Exception as e:
        print(f"Error scraping {la_name}: {e}")
        return []
```

### **Script 3: Charity Commission Bulk Import**
Create: `src/collect_charity_commission.py`

```python
#!/usr/bin/env python3
"""
Import neurodivergent charities from Charity Commission register
Bulk data: https://register-of-charities.charitycommission.gov.uk/register/full-register-download
"""

import csv
from pathlib import Path

# Charity Commission classifications relevant to ND
RELEVANT_CLASSIFICATIONS = [
    "Education/training",
    "Disability",
    "Health",
    "People with disabilities",
]

# Keywords in charity purposes
ND_KEYWORDS = [
    "autism", "autistic", "ADHD", "dyslexia", "dyspraxia",
    "neurodivergent", "learning disability", "learning difficulties",
    "special educational needs", "SEN", "SEND"
]

def filter_nd_charities(charity_register_path: Path) -> List[Dict]:
    """Filter Charity Commission register for ND organizations"""
    
    nd_charities = []
    
    with open(charity_register_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            charity_name = row.get("charity_name", "").lower()
            activities = row.get("charity_activities", "").lower()
            purposes = row.get("charity_purposes", "").lower()
            
            # Check if mentions ND conditions
            text = f"{charity_name} {activities} {purposes}"
            
            if any(keyword in text for keyword in ND_KEYWORDS):
                nd_charities.append({
                    "name": row.get("charity_name"),
                    "number": row.get("charity_number"),
                    "postcode": row.get("charity_postcode"),
                    "activities": row.get("charity_activities"),
                    "income": row.get("latest_income"),
                })
    
    return nd_charities
```

---

## 📊 QUALITY METRICS BY PHASE

### **Success Criteria**

| Phase | Target Resources | ND-Relevant % | Complete Data % | User Confidence |
|-------|-----------------|---------------|----------------|-----------------|
| Phase 1 (London) | 400 | 90%+ | 85%+ | High |
| Phase 2 (Adjacent) | 300-400 | 85%+ | 80%+ | High |
| Phase 3 (National) | 1,200-1,800 | 80%+ | 75%+ | Medium-High |
| **TOTAL** | **2,000-2,600** | **85%+** | **80%+** | **High** |

### **Data Completeness Requirements**

**Essential Fields** (Must have for all resources):
- ✅ Name
- ✅ Location (at least region)
- ✅ ND-relevance validation
- ✅ Category
- ✅ Contact method (phone OR email OR website)

**Desirable Fields** (Target 80%+ coverage):
- 🎯 Full address
- 🎯 Website
- 🎯 Description
- 🎯 Conditions supported
- 🎯 Age range
- 🎯 Organization type

**Enhanced Fields** (Target 60%+ coverage):
- 💎 Referral requirements
- 💎 Cost/funding
- 💎 Wait times
- 💎 Accessibility features
- 💎 Languages supported

---

## 🛠️ TECHNICAL INFRASTRUCTURE NEEDS

### **For GB-Scale Operation:**

1. **Database Migration**
   - Current: CSV files
   - Needed: PostgreSQL/MySQL with PostGIS for geographic queries
   - Enable queries like "Find autism services within 10 miles of Manchester"

2. **API Development**
   - RESTful API for programmatic access
   - Endpoints:
     - `/api/services?region=London&condition=autism`
     - `/api/services/nearby?lat=51.5074&lon=0.1278&radius=10`
     - `/api/services/search?q=ADHD+assessment`

3. **Caching Strategy**
   - Cache enriched data for 6 months
   - Re-validate stale data quarterly
   - Priority re-validation for high-traffic resources

4. **Monitoring**
   - Data freshness dashboard
   - Coverage maps (choropleth by region)
   - User engagement metrics
   - Data quality scores by region

5. **Scalability**
   - Current: 1,043 resources, manual processing
   - Target: 2,500+ resources, automated pipeline
   - Need: Distributed processing, rate limiting, error recovery

---

## 💰 COST ESTIMATE

### **API Costs (Gemini Flash for enrichment)**

| Phase | Resources | API Calls | Cost (@ $0.000375/call) | Time (@ 10s/call) |
|-------|-----------|-----------|-------------------------|-------------------|
| Phase 1 | 400 | 400 | $0.15 | 1.1 hours |
| Phase 2 | 400 | 400 | $0.15 | 1.1 hours |
| Phase 3 | 1,800 | 1,800 | $0.68 | 5 hours |
| **TOTAL** | **2,600** | **2,600** | **~$1** | **~7 hours** |

**Budget:** Gemini API costs are negligible (~$1 for entire GB)

### **Development Time Estimate**

| Phase | Task | Effort | Priority |
|-------|------|--------|----------|
| Phase 1 | London validation & quality | 2 weeks | P0 |
| Phase 1 | Fix encoding, duplicates | 1 week | P0 |
| Phase 1 | Rich metadata, UI | 2 weeks | P1 |
| Phase 2 | Adjacent region collection | 1 week | P1 |
| Phase 2 | CQC/LA integration | 2 weeks | P1 |
| Phase 3 | National automation | 3 weeks | P2 |
| Phase 3 | Regional validation | 2 weeks | P2 |
| **TOTAL** | | **13 weeks** | |

---

## 🚀 IMMEDIATE NEXT STEPS (This Week)

### **Day 1-2: Validate Existing Data**
```bash
# Run validation on all 1,043 resources
python src/batch_enrich_pipeline_parallel.py \
  --input data/enriched_resources_final.csv \
  --output data/validated_gb_resources.xlsx \
  --workers 10

# Filter for quality
python src/filter_neurodivergent.py \
  --input data/validated_gb_resources.xlsx \
  --filter --min-score Medium \
  --output data/high_quality_gb_resources.xlsx
```

### **Day 3: Set Up Multi-Source Collection**
```bash
# Create CQC integration
python src/collect_cqc_services.py --region London --output data/cqc_london.csv

# Cross-reference with existing data to avoid duplicates
python src/deduplicate_multi_source.py \
  --existing data/high_quality_gb_resources.xlsx \
  --new data/cqc_london.csv \
  --output data/merged_london.csv
```

### **Day 4-5: Enhance Metadata**
- Add structured age ranges
- Add referral requirements
- Add cost/funding information
- Add confidence scores

---

## 📈 SUCCESS METRICS

### **Coverage Goals**

**By End of Phase 1 (Month 1):**
- ✅ 400 validated London resources
- ✅ 90%+ ND-relevance rate
- ✅ 85%+ complete contact info

**By End of Phase 2 (Month 2):**
- ✅ 700-800 validated South East + East resources
- ✅ Full CQC integration
- ✅ Local Authority SEND integration

**By End of Phase 3 (Month 12):**
- ✅ 2,000-2,500 validated GB resources
- ✅ Coverage in all major cities (100k+ pop)
- ✅ User feedback mechanism active
- ✅ Quarterly data refresh process

---

## ❓ QUESTIONS FOR YOU

1. **Priority Regions After London:**
   - Should we prioritize by population (major cities first)?
   - Or by specific request (e.g., "we need Scotland coverage next")?

2. **Data Quality vs. Quantity:**
   - High bar (Medium+ validation) = ~2,000 resources
   - Lower bar (Low+ validation) = ~3,000 resources
   - Which approach?

3. **Multi-Source Integration:**
   - Should we integrate CQC/Charity Commission now (Week 1)?
   - Or perfect London dataset first (Week 4)?

4. **User Feedback:**
   - When to launch public feedback mechanism?
   - Wait until Phase 2 (better data quality)?
   - Or launch now with Phase 1 (faster iteration)?

---

Would you like me to:
1. ✅ **Implement the CQC integration script** for automated collection?
2. ✅ **Create the Local Authority SEND scraper** for comprehensive coverage?
3. ✅ **Set up the database migration** (CSV → PostgreSQL + PostGIS)?
4. ✅ **Build the API layer** for programmatic access?

Let me know your priorities and I'll start implementing! 🚀

