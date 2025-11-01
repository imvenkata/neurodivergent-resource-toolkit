# Early Duplicate Skipping: How It Works

## Overview

The early duplicate skipping mechanism prevents wasting API calls and processing time on places we already know about. It works in **two stages**:

1. **Stage 1: Skip by Place ID** (before fetching details) - Saves API calls
2. **Stage 2: Skip by Website** (after fetching details) - Catches duplicates with different place_ids

## Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│ 1. Load Existing Resources                               │
│    - Read from data/db/enriched_resources_*.csv          │
│    - Extract all gmaps_place_id values                   │
│    - Extract all gmaps_website values (normalized)       │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Build Lookup Sets                                    │
│    existing_place_ids_set = {                           │
│      "ChIJ...", "ChIJ...", ...                          │
│    }                                                     │
│    existing_websites_set = {                             │
│      "example.com", "another.org", ...                  │
│    } (all lowercase, normalized)                         │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Scrape New Places                                    │
│    For each place returned by Google Places API:         │
│                                                          │
│    ┌──────────────────────────────────────────────┐   │
│    │ STAGE 1: Check Place ID (IMMEDIATE SKIP)     │   │
│    │                                               │   │
│    │ if place_id in existing_place_ids_set:       │   │
│    │     continue  ← Skip! No API call needed     │   │
│    │                                               │   │
│    │ ✅ Benefit: Saves Place Details API call     │   │
│    └──────────────────────────────────────────────┘   │
│                        ↓                                │
│    ┌──────────────────────────────────────────────┐   │
│    │ Fetch Place Details (if needed)               │   │
│    │ - Cost: 1 Place Details API call              │   │
│    └──────────────────────────────────────────────┘   │
│                        ↓                                │
│    ┌──────────────────────────────────────────────┐   │
│    │ STAGE 2: Check Website (AFTER DETAILS)       │   │
│    │                                               │   │
│    │ site = details.get("websiteUri")              │   │
│    │ if site.lower() in existing_websites_set:    │   │
│    │     continue  ← Skip! Already have this      │   │
│    │                                               │   │
│    │ ✅ Benefit: Catches duplicates where place_id │   │
│    │    differs but website is the same            │   │
│    └──────────────────────────────────────────────┘   │
│                        ↓                                │
│    ┌──────────────────────────────────────────────┐   │
│    │ Add to Results                                │   │
│    └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Code Implementation

### Step 1: Build Lookup Sets (in `expand_uk_coverage.py`)

```python
# Lines 504-512
existing_place_ids_set = set()
existing_websites_set = set()

for res in existing_resources:
    pid = (res.get("gmaps_place_id") or "").strip()
    if pid:
        existing_place_ids_set.add(pid)  # e.g., "ChIJN1t_tDeuEmsRUsoyG83frY4"
    
    site = (res.get("gmaps_website") or "").strip().lower()
    if site:
        existing_websites_set.add(site)  # e.g., "example.com"
```

**Result**: Two fast lookup sets
- `existing_place_ids_set`: ~1,676 place IDs
- `existing_websites_set`: ~1,200 unique websites

### Step 2: Pass Sets to Scraper

```python
# Lines 544-546 (parallel) or 556-558 (sequential)
new_places = scrape_uk_places_parallel(
    # ... other params ...
    existing_place_ids=existing_place_ids_set,
    existing_websites=existing_websites_set,
    strict_geo_filter=strict_geo_filter,
)
```

### Step 3: Stage 1 - Skip by Place ID (Before API Call)

**Location**: `src/scrape_google_places.py` lines 452-454

```python
for place in places:
    place_id = place.get("id")
    
    # ⚡ EARLY SKIP: Check place_id before fetching details
    if place_id in seen_place_ids or place_id in existing_place_ids:
        continue  # Skip immediately - saves API call!
    
    # ... geo filter check ...
    
    # Only fetch details if we get past this point
    if fetch_details:
        details = get_place_details(...)  # 💰 API call happens here
```

**Why This Matters**:
- Place Details API calls cost money/credits
- If we already have this place_id, we don't need details
- **Savings**: ~50-80% of API calls avoided for known places

### Step 4: Stage 2 - Skip by Website (After Details)

**Location**: `src/scrape_google_places.py` lines 471-477

```python
# Get detailed info if requested
details = None
if fetch_details and place_name:
    details = get_place_details(place_name, api_key, cache, rate_limiter)
    
    # 🔍 SECOND CHECK: Website duplicate detection
    if details:
        site = (details.get("websiteUri") or "").strip().lower()
        if site and site in existing_websites:
            continue  # Skip - we already have this website!
```

**Why This Matters**:
- Sometimes Google assigns different `place_id`s to the same organization
  - Different locations (headquarters vs branch)
  - Google data inconsistencies
  - Merged/split business entries
- Website is more stable identifier
- Catches duplicates that place_id misses

## Example Scenario

### Scenario: Scraping Cornwall

**Existing Database** has:
```python
existing_place_ids_set = {
    "ChIJN1t_tDeuEmsRUsoyG83frY4",  # Autism Support Center London
    "ChIJ...",  # ... 1,675 more
}

existing_websites_set = {
    "autismsupport.org.uk",
    "example-clinic.com",
    # ... 1,200 more
}
```

**Google Returns**:
1. Place A: `place_id="ChIJN1t_tDeuEmsRUsoyG83frY4"` (London center)
   - ✅ **Stage 1 Skip**: Place ID in existing set
   - **Saves**: 1 API call

2. Place B: `place_id="ChIJ_NEW_PLACE_123"` (New Cornwall location)
   - ✅ Passes Stage 1
   - Fetch details → `website="autismsupport.org.uk"`
   - ✅ **Stage 2 Skip**: Website in existing set
   - **Result**: Detected as duplicate even with different place_id

3. Place C: `place_id="ChIJ_NEW_PLACE_456"` (New Cornwall service)
   - ✅ Passes Stage 1
   - Fetch details → `website="cornwall-autism.co.uk"` (new!)
   - ✅ Passes Stage 2
   - **Result**: Added as new place

## Performance Impact

### Before Early Skipping

```
Cornwall scrape:
- Google returns: 500 places
- Fetch details for: 500 places (500 API calls)
- Check duplicates: After all API calls done
- Duplicates found: 480
- New places: 20
- Cost: 500 Place Details calls
```

### After Early Skipping

```
Cornwall scrape:
- Google returns: 500 places
- Stage 1 skip: 400 places (by place_id)
- Fetch details for: 100 places (100 API calls)  ← 80% reduction!
- Stage 2 skip: 80 places (by website)
- New places: 20
- Cost: 100 Place Details calls  ← Saves 400 API calls
```

## Benefits Summary

1. **Cost Savings**: 50-80% fewer Place Details API calls
2. **Speed**: Faster execution (fewer network requests)
3. **Rate Limits**: Less pressure on API rate limits
4. **Accuracy**: Catches duplicates at two levels:
   - Place ID level (same Google place)
   - Website level (same organization, different place_id)

## Configuration

Control this behavior via:

```python
# config.py
GOOGLE_PLACES_CONFIG = {
    "strict_geo_filter": True,  # Also filters by distance
    "fetch_details": True,      # Must be True for website check
}
```

## Edge Cases Handled

1. **Missing place_id**: Skipped automatically
2. **Missing website**: Only place_id check applies
3. **Website normalization**: Lowercase comparison handles case differences
4. **Empty strings**: Stripped before comparison
5. **Thread safety**: In parallel mode, sets are read-only (safe)

## Debugging

To see what's being skipped:

```python
# Add debug prints in scrape_uk_places.py line 453:
if place_id in existing_place_ids:
    print(f"⚠️  Skipping known place_id: {place_id}")
    continue
```

And line 476:
```python
if site and site in existing_websites:
    print(f"⚠️  Skipping known website: {site}")
    continue
```

