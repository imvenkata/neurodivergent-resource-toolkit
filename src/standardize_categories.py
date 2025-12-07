#!/usr/bin/env python3
"""
Script to standardize categories and subcategories in existing data files.

This script reads a CSV/Excel file, standardizes all category and subcategory values,
and writes the standardized data to a new file.
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, List

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from openpyxl import load_workbook, Workbook
    from openpyxl.styles import Font, PatternFill
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    print("Warning: openpyxl not available. Excel files will be skipped.", file=sys.stderr)

# Import standardization functions
try:
    from src.utils.category_standardization import (
        standardize_resource_categories,
        STANDARD_CATEGORIES,
        STANDARD_SUBCATEGORIES,
    )
except ImportError as e:
    print(f"Error: category_standardization module not found: {e}", file=sys.stderr)
    print(f"Project root: {project_root}", file=sys.stderr)
    print(f"Python path: {sys.path[:3]}", file=sys.stderr)
    sys.exit(1)


def read_csv(input_path: str) -> List[Dict[str, str]]:
    """Read CSV file with multiple encoding attempts."""
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
    
    for encoding in encodings:
        try:
            with open(input_path, 'r', encoding=encoding, errors='replace') as f:
                reader = csv.DictReader(f)
                return list(reader)
        except UnicodeDecodeError:
            continue
    
    raise Exception(f"Could not read {input_path} with any encoding")


def read_excel(input_path: str, sheet_name: str = None) -> List[Dict[str, str]]:
    """Read Excel file."""
    if not OPENPYXL_AVAILABLE:
        raise Exception("openpyxl not available for Excel files")
    
    wb = load_workbook(input_path, data_only=True)
    ws = wb.active if sheet_name is None else wb[sheet_name]
    
    # Get headers from first row
    headers = [cell.value for cell in ws[1]]
    
    # Read data rows
    rows = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        row_dict = {}
        for i, value in enumerate(row):
            if i < len(headers):
                row_dict[headers[i]] = str(value) if value is not None else ""
        rows.append(row_dict)
    
    return rows


def write_csv(output_path: str, rows: List[Dict[str, str]], headers: List[str] = None):
    """Write CSV file."""
    if not rows:
        return
    
    if headers is None:
        headers = list(rows[0].keys())
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def write_excel(output_path: str, rows: List[Dict[str, str]], headers: List[str] = None):
    """Write Excel file with formatting."""
    if not OPENPYXL_AVAILABLE:
        raise Exception("openpyxl not available for Excel files")
    
    if not rows:
        wb = Workbook()
        wb.save(output_path)
        return
    
    if headers is None:
        headers = list(rows[0].keys())
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Standardized Resources"
    
    # Write headers
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="CCE5FF", end_color="CCE5FF", fill_type="solid")
    
    # Write data
    for row_idx, row_data in enumerate(rows, 2):
        for col_idx, header in enumerate(headers, 1):
            value = row_data.get(header, "")
            ws.cell(row=row_idx, column=col_idx, value=value)
    
    # Auto-size columns
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            except (TypeError, AttributeError):
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    wb.save(output_path)


def standardize_data(rows: List[Dict[str, str]]) -> tuple[List[Dict[str, str]], Dict[str, int]]:
    """
    Standardize categories and subcategories in data rows.
    
    Returns:
        Tuple of (standardized_rows, statistics_dict)
    """
    stats = {
        "total_rows": len(rows),
        "categories_standardized": 0,
        "subcategories_standardized": 0,
        "category_changes": {},
        "subcategory_changes": {},
    }
    
    standardized_rows = []
    
    for row in rows:
        new_row = row.copy()
        
        # Get current values
        category = row.get("category", "").strip()
        subcategory = row.get("subcategory", "").strip()
        
        # Standardize
        std_category, std_subcategory = standardize_resource_categories(
            category if category else None,
            subcategory if subcategory else None
        )
        
        # Track changes
        if category and category != std_category:
            stats["categories_standardized"] += 1
            change_key = f"{category} → {std_category}"
            stats["category_changes"][change_key] = stats["category_changes"].get(change_key, 0) + 1
        
        if subcategory and subcategory != std_subcategory:
            stats["subcategories_standardized"] += 1
            change_key = f"{subcategory} → {std_subcategory}"
            stats["subcategory_changes"][change_key] = stats["subcategory_changes"].get(change_key, 0) + 1
        
        # Update row
        new_row["category"] = std_category
        new_row["subcategory"] = std_subcategory
        
        standardized_rows.append(new_row)
    
    return standardized_rows, stats


def main():
    parser = argparse.ArgumentParser(
        description="Standardize categories and subcategories in resource data files"
    )
    parser.add_argument("--input", required=True, help="Input CSV or Excel file")
    parser.add_argument("--output", required=True, help="Output CSV or Excel file")
    parser.add_argument("--sheet", default=None, help="Excel sheet name (if reading Excel)")
    parser.add_argument("--stats", action="store_true", help="Print statistics about changes")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    
    # Read input file
    print(f"Reading {input_path}...")
    try:
        if input_path.suffix.lower() == '.csv':
            rows = read_csv(str(input_path))
        elif input_path.suffix.lower() in ['.xlsx', '.xls']:
            rows = read_excel(str(input_path), args.sheet)
        else:
            print(f"Error: Unsupported file format: {input_path.suffix}", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Error reading input file: {e}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Loaded {len(rows)} rows")
    
    # Standardize data
    print("Standardizing categories and subcategories...")
    standardized_rows, stats = standardize_data(rows)
    
    # Write output file
    print(f"Writing standardized data to {output_path}...")
    try:
        if output_path.suffix.lower() == '.csv':
            write_csv(str(output_path), standardized_rows)
        elif output_path.suffix.lower() in ['.xlsx', '.xls']:
            write_excel(str(output_path), standardized_rows)
        else:
            print(f"Error: Unsupported output format: {output_path.suffix}", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)
    
    print(f"✅ Standardization complete! Saved to {output_path}")
    
    # Print statistics
    if args.stats:
        print("\n" + "="*60)
        print("STANDARDIZATION STATISTICS")
        print("="*60)
        print(f"Total rows processed:        {stats['total_rows']}")
        print(f"Categories standardized:     {stats['categories_standardized']}")
        print(f"Subcategories standardized:  {stats['subcategories_standardized']}")
        
        if stats['category_changes']:
            print("\nCategory Changes:")
            for change, count in sorted(stats['category_changes'].items(), key=lambda x: -x[1]):
                print(f"  {change}: {count}")
        
        if stats['subcategory_changes']:
            print("\nSubcategory Changes (top 20):")
            for change, count in sorted(stats['subcategory_changes'].items(), key=lambda x: -x[1])[:20]:
                print(f"  {change}: {count}")
        
        print("\nStandard Categories:")
        for cat in STANDARD_CATEGORIES:
            subcat_count = len(STANDARD_SUBCATEGORIES.get(cat, []))
            print(f"  {cat}: {subcat_count} subcategories")
        print("="*60)


if __name__ == "__main__":
    main()

