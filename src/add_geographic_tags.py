#!/usr/bin/env python3
"""
Add geographic tags to resources for GB-wide scalability
"""
import csv
from pathlib import Path
from typing import Dict, Optional

# UK Region mapping based on county
UK_REGIONS = {
    # London
    "Greater London": "London",
    "London": "London",
    
    # South East England
    "Surrey": "South East",
    "Kent": "South East", 
    "East Sussex": "South East",
    "West Sussex": "South East",
    "Berkshire": "South East",
    "Buckinghamshire": "South East",
    "Oxfordshire": "South East",
    "Hampshire": "South East",
    
    # East of England
    "Essex": "East of England",
    "Hertfordshire": "East of England",
    "Bedfordshire": "East of England",
    "Cambridgeshire": "East of England",
    "Norfolk": "East of England",
    "Suffolk": "East of England",
    
    # South West
    "Bristol": "South West",
    "Cornwall": "South West",
    "Devon": "South West",
    "Dorset": "South West",
    "Gloucestershire": "South West",
    "Somerset": "South West",
    "Wiltshire": "South West",
    
    # Midlands
    "West Midlands": "West Midlands",
    "Warwickshire": "West Midlands",
    "Staffordshire": "West Midlands",
    "Worcestershire": "West Midlands",
    "Derbyshire": "East Midlands",
    "Leicestershire": "East Midlands",
    "Nottinghamshire": "East Midlands",
    "Lincolnshire": "East Midlands",
    "Northamptonshire": "East Midlands",
    
    # North
    "Greater Manchester": "North West",
    "Lancashire": "North West",
    "Merseyside": "North West",
    "Cheshire": "North West",
    "Cumbria": "North West",
    "South Yorkshire": "Yorkshire and the Humber",
    "West Yorkshire": "Yorkshire and the Humber",
    "North Yorkshire": "Yorkshire and the Humber",
    "East Riding of Yorkshire": "Yorkshire and the Humber",
    "Durham": "North East",
    "Northumberland": "North East",
    "Tyne and Wear": "North East",
    
    # Wales
    "Cardiff": "Wales",
    "Swansea": "Wales",
    "Newport": "Wales",
    "Pembrokeshire": "Wales",
    "Carmarthenshire": "Wales",
    "Ceredigion": "Wales",
    "Powys": "Wales",
    "Gwynedd": "Wales",
    "Anglesey": "Wales",
    "Conwy": "Wales",
    "Denbighshire": "Wales",
    "Flintshire": "Wales",
    "Wrexham": "Wales",
    
    # Scotland
    "Edinburgh": "Scotland",
    "Glasgow": "Scotland",
    "Aberdeen": "Scotland",
    "Dundee": "Scotland",
    "Highland": "Scotland",
    "Fife": "Scotland",
    
    # Northern Ireland
    "Belfast": "Northern Ireland",
    "Antrim": "Northern Ireland",
    "Down": "Northern Ireland",
    "Armagh": "Northern Ireland",
    "Londonderry": "Northern Ireland",
    "Tyrone": "Northern Ireland",
    "Fermanagh": "Northern Ireland",
}

# Distance bands from London (for prioritization during initial rollout)
LONDON_PROXIMITY = {
    "London": "London Core",
    "South East": "London Adjacent",  # Surrey, Kent, Berkshire, etc.
    "East of England": "London Adjacent",  # Essex, Hertfordshire
    "South West": "Extended",
    "West Midlands": "Extended",
    "East Midlands": "Extended",
    "North West": "Extended",
    "Yorkshire and the Humber": "Extended",
    "North East": "Extended",
    "Wales": "Extended",
    "Scotland": "Extended",
    "Northern Ireland": "Extended",
}

def get_region(county: str) -> Optional[str]:
    """Get UK region from county name"""
    county = county.strip()
    return UK_REGIONS.get(county, None)

def get_proximity_band(region: str) -> str:
    """Get proximity to London for rollout prioritization"""
    return LONDON_PROXIMITY.get(region, "Unknown")

def add_geographic_tags(input_file: Path, output_file: Path):
    """Add geographic metadata to resources"""
    
    with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = list(reader.fieldnames)
    
    # Add new fields if not present
    new_fields = ['uk_region', 'london_proximity', 'geographic_scope']
    for field in new_fields:
        if field not in fieldnames:
            fieldnames.append(field)
    
    # Tag each resource
    london_core = 0
    london_adjacent = 0
    extended = 0
    unknown_location = 0
    national_services = 0
    
    for row in rows:
        county = row.get('gmaps_addr_admin_area_level_2', '').strip()
        name = row.get('gmaps_name', '').lower()
        
        # Check if national service (no specific location)
        is_national = any(keyword in name for keyword in [
            'national', 'uk wide', 'britain', 'helpline', 'online'
        ])
        
        if is_national:
            row['uk_region'] = 'National'
            row['london_proximity'] = 'National Service'
            row['geographic_scope'] = 'National'
            national_services += 1
        elif county:
            region = get_region(county)
            if region:
                row['uk_region'] = region
                row['london_proximity'] = get_proximity_band(region)
                row['geographic_scope'] = 'Regional'
                
                # Count proximity bands
                if row['london_proximity'] == 'London Core':
                    london_core += 1
                elif row['london_proximity'] == 'London Adjacent':
                    london_adjacent += 1
                elif row['london_proximity'] == 'Extended':
                    extended += 1
            else:
                row['uk_region'] = county  # Keep original county name
                row['london_proximity'] = 'Unknown'
                row['geographic_scope'] = 'Regional'
                unknown_location += 1
        else:
            row['uk_region'] = 'Unknown'
            row['london_proximity'] = 'Unknown'
            row['geographic_scope'] = 'Unknown'
            unknown_location += 1
    
    # Write updated data
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    # Report
    print("\n" + "="*70)
    print("GEOGRAPHIC TAGGING COMPLETE")
    print("="*70)
    print(f"\nTotal resources: {len(rows)}")
    print(f"\nGeographic Distribution:")
    print(f"  🏙️  London Core:           {london_core:4} ({london_core/len(rows)*100:5.1f}%)")
    print(f"  🌆  London Adjacent:       {london_adjacent:4} ({london_adjacent/len(rows)*100:5.1f}%)")
    print(f"  🌍  Extended GB:           {extended:4} ({extended/len(rows)*100:5.1f}%)")
    print(f"  🇬🇧  National Services:     {national_services:4} ({national_services/len(rows)*100:5.1f}%)")
    print(f"  ❓  Unknown Location:      {unknown_location:4} ({unknown_location/len(rows)*100:5.1f}%)")
    
    print(f"\n✅ Output written to: {output_file}")
    print(f"\nNew fields added:")
    print(f"  - uk_region: Geographic region (London, South East, etc.)")
    print(f"  - london_proximity: Distance band (London Core/Adjacent/Extended)")
    print(f"  - geographic_scope: National vs Regional service")
    
    print(f"\n💡 Usage: Filter by 'london_proximity' for phased rollout:")
    print(f"   Phase 1: London Core")
    print(f"   Phase 2: London Core + Adjacent")
    print(f"   Phase 3: All of GB")
    print("="*70)
    
    # Show region breakdown
    from collections import Counter
    regions = Counter(row.get('uk_region', 'Unknown') for row in rows)
    print(f"\nTop 15 Regions:")
    for region, count in regions.most_common(15):
        print(f"  {region:30} {count:4}")
    print("="*70)

if __name__ == "__main__":
    input_path = Path("data/enriched_resources.csv")
    output_path = Path("data/enriched_resources_tagged.csv")
    
    add_geographic_tags(input_path, output_path)

