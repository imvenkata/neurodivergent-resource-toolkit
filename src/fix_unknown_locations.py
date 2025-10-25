#!/usr/bin/env python3
"""
Fix resources with Unknown location by extracting county from address
"""
import csv
import re
from pathlib import Path
from typing import Optional

# Common UK counties/areas to extract from addresses
UK_LOCATIONS = [
    # London boroughs (might be in address but not in county field)
    "Westminster", "Camden", "Islington", "Hackney", "Tower Hamlets",
    "Greenwich", "Lewisham", "Southwark", "Lambeth", "Wandsworth",
    "Hammersmith", "Fulham", "Kensington", "Chelsea", "Brent",
    "Ealing", "Hounslow", "Richmond", "Kingston", "Merton",
    "Sutton", "Croydon", "Bromley", "Bexley", "Havering",
    "Barking", "Dagenham", "Redbridge", "Newham", "Waltham Forest",
    "Haringey", "Enfield", "Barnet", "Harrow", "Hillingdon",
    
    # Counties
    "Greater London", "Hertfordshire", "Surrey", "Kent", "Essex",
    "Berkshire", "Buckinghamshire", "Oxfordshire", "Hampshire",
    "East Sussex", "West Sussex", "Bedfordshire", "Cambridgeshire",
    "Norfolk", "Suffolk", "Lincolnshire", "Nottinghamshire",
    "Derbyshire", "Leicestershire", "Northamptonshire", "Warwickshire",
    "Staffordshire", "Worcestershire", "Gloucestershire", "Somerset",
    "Devon", "Cornwall", "Dorset", "Wiltshire", "Bristol",
    "Greater Manchester", "Lancashire", "Merseyside", "Cheshire",
    "South Yorkshire", "West Yorkshire", "North Yorkshire",
    "East Riding of Yorkshire", "Durham", "Northumberland",
    "Tyne and Wear", "Cumbria",
    
    # Unitary authorities
    "Thurrock", "Southend-on-Sea", "Medway", "Luton", "Milton Keynes",
    "Peterborough", "Brighton and Hove", "Portsmouth", "Southampton",
    "Reading", "Slough", "Bracknell", "Windsor", "Maidenhead",
]

def extract_county_from_address(address: str, postal_town: str = "") -> Optional[str]:
    """
    Extract county/region from full address string
    """
    if not address:
        return None
    
    address_lower = address.lower()
    
    # Try to find county in address
    for location in UK_LOCATIONS:
        location_lower = location.lower()
        # Look for exact word match (not substring)
        pattern = r'\b' + re.escape(location_lower) + r'\b'
        if re.search(pattern, address_lower):
            return location
    
    # If postal town is a London borough, it's Greater London
    if postal_town:
        for location in UK_LOCATIONS[:35]:  # First 35 are London boroughs
            if location.lower() in postal_town.lower():
                return "Greater London"
    
    # Check if "London" is in address
    if re.search(r'\blondon\b', address_lower):
        return "Greater London"
    
    return None

def fix_unknown_locations(input_file: Path, output_file: Path):
    """Fix resources with Unknown location"""
    
    with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = list(reader.fieldnames)
    
    fixed_count = 0
    still_unknown = 0
    
    for row in rows:
        # Skip if already has valid county
        county = row.get('gmaps_addr_admin_area_level_2', '').strip()
        if county and county not in ['', 'Unknown']:
            continue
        
        # Try to extract from address
        address = row.get('gmaps_formatted_address', '')
        postal_town = row.get('gmaps_addr_postal_town', '')
        
        extracted_county = extract_county_from_address(address, postal_town)
        
        if extracted_county:
            row['gmaps_addr_admin_area_level_2'] = extracted_county
            fixed_count += 1
        else:
            row['gmaps_addr_admin_area_level_2'] = 'Unknown'
            still_unknown += 1
    
    # Write updated data
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print("\n" + "="*70)
    print("LOCATION FIX COMPLETE")
    print("="*70)
    print(f"\nTotal resources: {len(rows)}")
    print(f"  ✅ Fixed locations:     {fixed_count:4}")
    print(f"  ❌ Still unknown:       {still_unknown:4}")
    print(f"\nImprovement: {(fixed_count/(fixed_count+still_unknown))*100:.1f}% of unknowns resolved")
    print(f"\n✅ Output written to: {output_file}")
    print("="*70)
    
    # Show sample of still unknown (for debugging)
    if still_unknown > 0:
        print("\nSample of still-unknown locations (first 10):")
        unknown_samples = [
            (row.get('gmaps_name'), row.get('gmaps_formatted_address'))
            for row in rows 
            if row.get('gmaps_addr_admin_area_level_2') == 'Unknown'
        ][:10]
        for name, address in unknown_samples:
            print(f"  - {name}")
            print(f"    Address: {address[:70]}...")
    print("="*70)

if __name__ == "__main__":
    input_path = Path("data/enriched_resources_tagged.csv")
    output_path = Path("data/enriched_resources_tagged_fixed.csv")
    
    fix_unknown_locations(input_path, output_path)

