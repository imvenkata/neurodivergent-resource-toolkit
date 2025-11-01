#!/usr/bin/env python3
"""
Remove duplicate entries from CSV file based on gmaps_place_id.
Keeps the first occurrence of each place_id.
"""

import csv
import sys
from pathlib import Path

def remove_duplicates_by_place_id(input_file: str, output_file: str = None):
    """
    Remove duplicate entries based on gmaps_place_id.
    
    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file (default: overwrite input)
    """
    if not Path(input_file).exists():
        print(f"❌ Error: File not found: {input_file}")
        sys.exit(1)
    
    # Default: overwrite input file
    if output_file is None:
        output_file = input_file
        backup_file = input_file + ".backup"
        print(f"📝 Creating backup: {backup_file}")
        
        # Create backup
        import shutil
        shutil.copy2(input_file, backup_file)
        print(f"✅ Backup created")
    
    # Read all rows
    rows = []
    seen_place_ids = set()
    duplicates_removed = 0
    empty_place_ids = []
    
    print(f"\n📖 Reading: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        
        for row in reader:
            place_id = row.get('gmaps_place_id', '').strip()
            
            if not place_id:
                # Keep rows with empty place_id (they'll be handled separately)
                empty_place_ids.append(row)
                rows.append(row)
                continue
            
            if place_id in seen_place_ids:
                # Duplicate found - skip it
                duplicates_removed += 1
                continue
            
            # First occurrence - keep it
            seen_place_ids.add(place_id)
            rows.append(row)
    
    print(f"   Total rows read: {len(rows) + duplicates_removed}")
    print(f"   Unique place_ids: {len(seen_place_ids)}")
    print(f"   Empty place_ids: {len(empty_place_ids)}")
    print(f"   Duplicates removed: {duplicates_removed}")
    print(f"   Rows to write: {len(rows)}")
    
    if duplicates_removed == 0:
        print(f"\n✅ No duplicates found. File is already clean!")
        if backup_file and Path(backup_file).exists():
            Path(backup_file).unlink()  # Remove backup since no changes needed
            print(f"   Backup removed (no changes needed)")
        return
    
    # Write cleaned data
    print(f"\n💾 Writing cleaned data to: {output_file}")
    
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"✅ Successfully removed {duplicates_removed} duplicate entries")
    print(f"   Saved to: {output_file}")
    
    if output_file == input_file:
        print(f"   Original backed up to: {backup_file}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Remove duplicate entries by gmaps_place_id"
    )
    parser.add_argument(
        "input_file",
        help="Path to input CSV file"
    )
    parser.add_argument(
        "--output",
        help="Output CSV file (default: overwrite input with backup)"
    )
    
    args = parser.parse_args()
    
    remove_duplicates_by_place_id(args.input_file, args.output)

