import argparse
import csv
import json
from pathlib import Path
# typing imports not needed currently


# Reuse normalization logic from scraper.py
try:
    from scraper import normalize_service_fields
except Exception as import_error:  # pragma: no cover
    raise SystemExit(
        f"Failed to import from scraper.py: {import_error}"
    ) from import_error


def read_text_file(file_path: Path) -> str:
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    return file_path.read_text(encoding="utf-8")


def write_csv(output_path: Path, record: dict) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(record.keys()))
        writer.writeheader()
        writer.writerow(record)


def main() -> None:
    parser = argparse.ArgumentParser(description="Test normalization of scraped content.")
    parser.add_argument(
        "--input-file",
        type=Path,
        default=Path("/Users/venkata/startup/data_scraper/to_be_normalised/test.text"),
        help="Path to a text file containing the raw description/content.",
    )
    parser.add_argument(
        "--title",
        type=str,
        default="Test Center",
        help="Title to associate with the content.",
    )
    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="Optional URL to include (used if not found in content).",
    )
    parser.add_argument(
        "--coordinates",
        type=str,
        default="",
        help=(
            "Optional coordinates to include. For KML-style, pass 'lng,lat' or 'lng,lat,alt'."
        ),
    )
    parser.add_argument(
        "--out-csv",
        type=Path,
        default=None,
        help="Optional path to write a one-row CSV of the normalized record.",
    )

    args = parser.parse_args()

    raw_text = read_text_file(args.input_file)

    normalized_record = normalize_service_fields(
        title=args.title,
        content=raw_text,
        coordinates=args.coordinates,
        link=args.url,
    )

    print(json.dumps(normalized_record, indent=2, ensure_ascii=False))

    if args.out_csv is not None:
        write_csv(args.out_csv, normalized_record)


if __name__ == "__main__":
    main()


