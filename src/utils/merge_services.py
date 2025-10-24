"""
Merge two neurodivergent services CSV sources into a canonical schema.

Inputs (defaults point to repo paths):
 - to_be_normalised/autism_services_*.csv (LAG map scrape)
 - to_be_normalised/london_neurodivergent_resources_complete.csv (compiled dataset)

Output:
 - to_be_normalised/merged_neurodivergent_services.csv
"""

from __future__ import annotations

import argparse
import csv
import os
import re
from typing import Dict, Iterable, List
from urllib.parse import urlparse


CANONICAL_HEADERS: List[str] = [
    "source",
    "source_id",
    "name",
    "category",
    "subcategory",
    "description_short",
    "description_full",
    "website",
    "phone",
    "email",
    "facebook",
    "other_contact",
    "full_address",
    "postcode",
    "city",
    "region",
    "local_authority",
    "service_area",
    "days_open",
    "opening_hours",
    "appointment_needed",
    "response_time",
    "cost_type",
    "specific_cost",
    "insurance_accepted",
    "financial_assistance",
    "age_range",
    "conditions_supported",
    "referral_required",
    "diagnosis_required",
    "specific_services",
    "physical_access",
    "communication_access",
    "sensory_friendly",
    "organization_type",
    "neurodivergent_led",
    "cqc_rating",
    "status",
    "last_verified",
    "verified_by",
    "data_source",
    "internal_notes",
    "latitude",
    "longitude",
    "coordinates",
    "content",
]


def read_csv(path: str) -> Iterable[Dict[str, str]]:
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield {k: (v if v is not None else "") for k, v in row.items()}


POSTCODE_RE = re.compile(r"\b([A-Z]{1,2}\d{1,2}[A-Z]?)\s?(\d[A-Z]{2})\b", re.I)


def normalize_uk_postcode(raw: str) -> str:
    if not raw:
        return ""
    m = POSTCODE_RE.search(raw.upper())
    if not m:
        return ""
    outward, inward = m.group(1), m.group(2)
    return f"{outward} {inward}"


LONDON_OUTWARD_CODES = {
    # Core London postal areas
    "E", "EC", "N", "NW", "SE", "SW", "W", "WC",
    # Greater London fringe areas commonly used for London addresses
    "BR", "CR", "DA", "EN", "HA", "IG", "KT", "RM", "SM", "TW", "UB", "WD",
}


def infer_city_region(address: str, postcode: str) -> tuple[str, str]:
    addr_upper = (address or "").upper()
    if "LONDON" in addr_upper:
        return "London", "England - London"

    outward = (postcode.split(" ")[0] if postcode else "").upper()
    if outward in LONDON_OUTWARD_CODES:
        return "London", "England - London"

    # Heuristic city guess from comma-separated parts
    parts = [p.strip() for p in (address or "").split(",") if p.strip()]
    if parts:
        candidate = parts[-1]
        # If last part is actually the postcode, try previous part
        if normalize_uk_postcode(candidate):
            if len(parts) >= 2:
                candidate = parts[-2]
        # Remove any trailing postcode from candidate
        candidate = POSTCODE_RE.sub("", candidate).strip(", -")
        # Keep alphabetic-rich tokens as city
        if any(ch.isalpha() for ch in candidate):
            return candidate, ""

    return "", ""


def as_canonical_from_lag(row: Dict[str, str]) -> Dict[str, str]:
    # LAG map scrape columns: title, description, address, url, latitude, longitude, content, coordinates, category
    address = row.get("address", "") or ""
    description_text = row.get("description", "") or ""
    content_text = row.get("content", "") or ""
    postcode = normalize_uk_postcode(" ".join([address, description_text, content_text]))
    city, region = infer_city_region(address, postcode)

    fb_from_content = extract_first_facebook_url(" ".join([content_text, description_text]))
    return {
        "source": "lag_map",
        "source_id": "",
        "name": row.get("title", "") or "",
        "category": row.get("category", "") or "",
        "subcategory": "",
        "description_short": "",
        "description_full": description_text,
        "website": canonicalize_website(row.get("url", "") or ""),
        "phone": "",
        "email": "",
        "facebook": canonicalize_facebook(fb_from_content),
        "other_contact": "",
        "full_address": address,
        "postcode": postcode,
        "city": city,
        "region": region,
        "local_authority": "",
        "service_area": "",
        "days_open": "",
        "opening_hours": "",
        "appointment_needed": "",
        "response_time": "",
        "cost_type": "",
        "specific_cost": "",
        "insurance_accepted": "",
        "financial_assistance": "",
        "age_range": "",
        "conditions_supported": "",
        "referral_required": "",
        "diagnosis_required": "",
        "specific_services": "",
        "physical_access": "",
        "communication_access": "",
        "sensory_friendly": "",
        "organization_type": "",
        "neurodivergent_led": "",
        "cqc_rating": "",
        "status": "",
        "last_verified": "",
        "verified_by": "",
        "data_source": "",
        "internal_notes": "",
        "latitude": row.get("latitude", "") or "",
        "longitude": row.get("longitude", "") or "",
        "coordinates": row.get("coordinates", "") or "",
        "content": row.get("content", "") or "",
    }


def as_canonical_from_compiled(row: Dict[str, str]) -> Dict[str, str]:
    # Compiled dataset columns include: Resource ID, Resource Name, Category, Subcategory, Short Description, Full Description, Website, Phone, Email, Facebook, Other Contact, Full Address, Postcode, City, Region, Local Authority, Service Area, Days Open, Opening Hours, Appointment Needed, Response Time, Cost Type, Specific Cost, Insurance Accepted, Financial Assistance, Age Range, Conditions Supported, Referral Required, Diagnosis Required, Specific Services, Physical Access, Communication Access, Sensory Friendly, Organization Type, Neurodivergent-Led, CQC Rating, Status, Last Verified, Verified By, Data Source, Internal Notes
    get = lambda k: (row.get(k, "") or "").strip()
    fb_direct = get("Facebook")
    if not fb_direct:
        fb_direct = extract_first_facebook_url(" ".join([get("Other Contact"), get("Full Description")]))
    return {
        "source": "compiled_resources",
        "source_id": get("Resource ID"),
        "name": get("Resource Name"),
        "category": get("Category"),
        "subcategory": get("Subcategory"),
        "description_short": get("Short Description"),
        "description_full": get("Full Description"),
        "website": canonicalize_website(get("Website")),
        "phone": normalize_uk_phone(get("Phone")),
        "email": normalize_email(get("Email")),
        "facebook": canonicalize_facebook(fb_direct),
        "other_contact": get("Other Contact"),
        "full_address": get("Full Address"),
        "postcode": get("Postcode"),
        "city": get("City"),
        "region": get("Region"),
        "local_authority": get("Local Authority"),
        "service_area": get("Service Area"),
        "days_open": get("Days Open"),
        "opening_hours": normalize_opening_hours(get("Opening Hours")),
        "appointment_needed": get("Appointment Needed"),
        "response_time": get("Response Time"),
        "cost_type": get("Cost Type"),
        "specific_cost": get("Specific Cost"),
        "insurance_accepted": get("Insurance Accepted"),
        "financial_assistance": get("Financial Assistance"),
        "age_range": get("Age Range"),
        "conditions_supported": get("Conditions Supported"),
        "referral_required": get("Referral Required"),
        "diagnosis_required": get("Diagnosis Required"),
        "specific_services": get("Specific Services"),
        "physical_access": get("Physical Access"),
        "communication_access": get("Communication Access"),
        "sensory_friendly": get("Sensory Friendly"),
        "organization_type": get("Organization Type"),
        "neurodivergent_led": get("Neurodivergent-Led"),
        "cqc_rating": get("CQC Rating"),
        "status": get("Status"),
        "last_verified": get("Last Verified"),
        "verified_by": get("Verified By"),
        "data_source": get("Data Source"),
        "internal_notes": get("Internal Notes"),
        "latitude": "",
        "longitude": "",
        "coordinates": "",
        "content": "",
    }


def ensure_all_fields(record: Dict[str, str]) -> Dict[str, str]:
    return {key: (record.get(key, "") or "") for key in CANONICAL_HEADERS}


def write_csv(path: str, rows: Iterable[Dict[str, str]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CANONICAL_HEADERS)
        writer.writeheader()
        for row in rows:
            writer.writerow(ensure_all_fields(row))


def normalize_website(url: str) -> str:
    if not url:
        return ""
    try:
        parsed = urlparse(url.strip())
        netloc = (parsed.netloc or parsed.path or "").lower()
        # strip common www.
        if netloc.startswith("www."):
            netloc = netloc[4:]
        path = parsed.path.rstrip("/")
        return f"{netloc}{path}"
    except Exception:
        return url.strip().lower()


def canonicalize_website(url: str) -> str:
    if not url:
        return ""
    try:
        parsed = urlparse(url.strip())
        netloc = (parsed.netloc or parsed.path or "").lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        path = (parsed.path or "").rstrip("/")
        # drop query and fragment
        if not netloc:
            return ""
        return f"https://{netloc}{path}"
    except Exception:
        return url.strip()


EMAIL_RE = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.I)


def normalize_email(email: str) -> str:
    if not email:
        return ""
    e = email.strip().lower()
    return e if EMAIL_RE.match(e) else ""


def _first_number_like(text: str) -> str:
    # split by common separators and pick the first candidate
    for part in re.split(r"[,/;]|\bor\b|\band\b", text, flags=re.I):
        s = part.strip()
        if re.search(r"\d", s):
            return s
    return text


def normalize_uk_phone(phone: str) -> str:
    if not phone:
        return ""
    p = _first_number_like(phone)
    # remove extensions
    p = re.sub(r"(ext\.?|x)\s*\d+$", "", p, flags=re.I)
    # keep leading +, remove other non-digits
    p = re.sub(r"[^+\d]", "", p)
    # 00 prefix -> +
    if p.startswith("00"):
        p = "+" + p[2:]
    if p.startswith("+"):
        # already international; ensure only digits after +
        p = "+" + re.sub(r"\D", "", p[1:])
        return p
    # local formats
    digits = re.sub(r"\D", "", p)
    if not digits:
        return ""
    if digits.startswith("0"):
        digits = "44" + digits[1:]
    elif len(digits) in (9, 10, 11):
        digits = "44" + digits
    return "+" + digits


TIME_RE = re.compile(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", re.I)


def _to_24h(match: re.Match) -> str:
    hour = int(match.group(1) or 0)
    minute = int(match.group(2) or 0)
    ampm = (match.group(3) or "").lower()
    if ampm == "pm" and hour < 12:
        hour += 12
    if ampm == "am" and hour == 12:
        hour = 0
    return f"{hour:02d}:{minute:02d}"


def normalize_opening_hours(raw: str) -> str:
    if not raw:
        return ""
    s = raw.strip()
    # unify dashes and remove bracketed hints
    s = s.replace("–", "-").replace("—", "-")
    s = re.sub(r"\((?:[^()]|\([^)]*\))*\)", "", s)
    # convert times to 24h
    s = TIME_RE.sub(_to_24h, s)
    # collapse spaces
    s = re.sub(r"\s+", " ", s).strip()
    return s


FACEBOOK_URL_RE = re.compile(r"https?://(?:www\.|m\.)?(?:facebook\.com|fb\.com)/[^\s)>'\"]+", re.I)


def extract_first_facebook_url(text: str) -> str:
    if not text:
        return ""
    m = FACEBOOK_URL_RE.search(text)
    return m.group(0) if m else ""


def canonicalize_facebook(url: str) -> str:
    if not url:
        return ""
    try:
        p = urlparse(url.strip())
        host = (p.netloc or p.path or "").lower()
        host = host.replace("m.facebook.com", "facebook.com").replace("fb.com", "facebook.com")
        if host.startswith("www."):
            host = host[4:]
        path = (p.path or "").rstrip("/")
        # keep profile.php?id=...; otherwise drop query
        if path.endswith("/profile.php") and p.query:
            q = p.query
            return f"https://{host}{path}?{q}"
        return f"https://{host}{path}"
    except Exception:
        return url.strip()


def normalize_name(name: str) -> str:
    if not name:
        return ""
    s = name.lower()
    s = re.sub(r"&amp;", "and", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\b(ltd|limited|nhs|trust|service|services|the)\b", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def dedupe_key(record: Dict[str, str]) -> tuple | None:
    website = normalize_website(record.get("website", ""))
    postcode = (record.get("postcode") or "").upper()
    city = (record.get("city") or "").lower().strip()
    name = normalize_name(record.get("name", ""))

    if website and postcode:
        return ("wp", website, postcode)
    if name and postcode:
        return ("np", name, postcode)
    if website and city:
        return ("wc", website, city)
    if name and city:
        return ("nc", name, city)
    return None


def merge_field(preferred: str, incoming: str) -> str:
    if preferred and not incoming:
        return preferred
    if incoming and not preferred:
        return incoming
    if not preferred and not incoming:
        return ""
    # both non-empty: choose the longer (more informative)
    return incoming if len(incoming) > len(preferred) else preferred


def merge_records(base: Dict[str, str], incoming: Dict[str, str]) -> Dict[str, str]:
    merged = dict(base)
    for field in CANONICAL_HEADERS:
        merged[field] = merge_field(base.get(field, ""), incoming.get(field, ""))
    return merged


def dedupe_records(records: List[Dict[str, str]]) -> List[Dict[str, str]]:
    # Process compiled first so it wins on conflicts; LAG fills gaps
    def priority(rec: Dict[str, str]) -> int:
        return 0 if rec.get("source") == "compiled_resources" else 1

    sorted_records = sorted(records, key=priority)
    key_to_record: Dict[tuple, Dict[str, str]] = {}
    deduped: List[Dict[str, str]] = []

    for rec in sorted_records:
        key = dedupe_key(rec)
        if not key:
            # no reliable key: append as-is
            deduped.append(rec)
            continue
        if key in key_to_record:
            merged = merge_records(key_to_record[key], rec)
            key_to_record[key] = merged
        else:
            key_to_record[key] = rec

    # Preserve insertion order: first the keyed merged ones in their first-seen order, then no-key ones
    seen = set()
    ordered: List[Dict[str, str]] = []
    for rec in sorted_records:
        key = dedupe_key(rec)
        if key and key not in seen:
            ordered.append(key_to_record[key])
            seen.add(key)
    # Append items that lacked a key (already in deduped)
    for rec in deduped:
        if dedupe_key(rec) is None:
            ordered.append(rec)
    return ordered


def merge_files(file_a: str, file_b: str) -> List[Dict[str, str]]:
    merged: List[Dict[str, str]] = []

    # File A: LAG map scrape
    for row in read_csv(file_a):
        merged.append(as_canonical_from_lag(row))

    # File B: Compiled resources
    for row in read_csv(file_b):
        merged.append(as_canonical_from_compiled(row))

    return dedupe_records(merged)


def compute_completeness(rec: Dict[str, str]) -> float:
    fields = [
        "name", "website", "postcode", "city", "category",
        "phone", "email", "opening_hours",
    ]
    present = sum(1 for f in fields if rec.get(f))
    return round(present / len(fields), 3)


def list_issues(rec: Dict[str, str]) -> List[str]:
    issues: List[str] = []
    # website
    w = rec.get("website", "")
    if w and "." not in (urlparse(w).netloc or ""):
        issues.append("website_suspect")
    if not w and not rec.get("phone") and not rec.get("email"):
        issues.append("no_contact")
    # email validity handled by normalization; but if original provided and blank here, we can't see. Basic recheck:
    e = rec.get("email", "")
    if e and not EMAIL_RE.match(e):
        issues.append("email_invalid")
    # phone basic length check
    p = rec.get("phone", "")
    if p and not re.match(r"^\+\d{7,15}$", p):
        issues.append("phone_suspect")
    # address / geo
    pc = rec.get("postcode", "")
    if pc and not POSTCODE_RE.match(pc):
        issues.append("postcode_invalid")
    if (rec.get("postcode") or rec.get("full_address")) and not (rec.get("latitude") and rec.get("longitude")):
        issues.append("missing_coordinates")
    return issues


def generate_qa_report(records: List[Dict[str, str]], output_path: str) -> None:
    headers = [
        "record_index", "name", "postcode", "city", "website", "phone", "email", "facebook",
        "source", "completeness", "key_used", "issues"
    ]
    rows = []
    for idx, rec in enumerate(records, start=1):
        key = dedupe_key(rec)
        rows.append({
            "record_index": str(idx),
            "name": rec.get("name", ""),
            "postcode": rec.get("postcode", ""),
            "city": rec.get("city", ""),
            "website": rec.get("website", ""),
            "phone": rec.get("phone", ""),
            "email": rec.get("email", ""),
            "facebook": rec.get("facebook", ""),
            "source": rec.get("source", ""),
            "completeness": str(compute_completeness(rec)),
            "key_used": key[0] if key else "",
            "issues": ";".join(list_issues(rec)),
        })
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    # also return rows so callers can export to Excel easily
    return rows


def write_excel(path: str, rows: List[Dict[str, str]], columns: List[str] | None = None) -> None:
    try:
        import pandas as pd
        if not rows:
            df = pd.DataFrame(columns=columns or [])
        else:
            df = pd.DataFrame(rows)
            if columns:
                extra_cols = [c for c in df.columns if c not in columns]
                df = df[[c for c in (columns or []) if c in df.columns] + extra_cols]
        os.makedirs(os.path.dirname(path), exist_ok=True)
        df.to_excel(path, index=False, engine="openpyxl")
    except ImportError:
        print("pandas/openpyxl not installed; skipping Excel export for", path)


def parse_args() -> argparse.Namespace:
    default_root = "/Users/venkata/startup/data_scraper"
    default_a = os.path.join(default_root, "to_be_normalised", "autism_services_20251008_185311.csv")
    default_b = os.path.join(default_root, "to_be_normalised", "london_neurodivergent_resources_complete.csv")
    default_out = os.path.join(default_root, "to_be_normalised", "merged_neurodivergent_services.csv")
    default_out_xlsx = os.path.join(default_root, "to_be_normalised", "merged_neurodivergent_services.xlsx")
    default_qa = os.path.join(default_root, "to_be_normalised", "qa_report.csv")
    default_qa_xlsx = os.path.join(default_root, "to_be_normalised", "qa_report.xlsx")

    parser = argparse.ArgumentParser(description="Merge neurodivergent service CSV sources into a canonical schema.")
    parser.add_argument("--file-a", default=default_a, help="Path to LAG map CSV (autism_services_*.csv)")
    parser.add_argument("--file-b", default=default_b, help="Path to compiled resources CSV")
    parser.add_argument("--output", default=default_out, help="Path to write merged CSV")
    parser.add_argument("--output-xlsx", default=default_out_xlsx, help="Path to write merged Excel (.xlsx)")
    parser.add_argument("--qa-report", default=default_qa, help="Path to write QA report CSV")
    parser.add_argument("--qa-report-xlsx", default=default_qa_xlsx, help="Path to write QA report Excel (.xlsx)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    records = merge_files(args.file_a, args.file_b)
    write_csv(args.output, records)
    qa_rows = generate_qa_report(records, args.qa_report)
    # Excel exports
    write_excel(args.output_xlsx, [ensure_all_fields(r) for r in records], CANONICAL_HEADERS)
    write_excel(args.qa_report_xlsx, qa_rows)

    print(f"Merged {len(records)} records -> {args.output}")
    print(f"QA report -> {args.qa_report}")
    print(f"Merged Excel -> {args.output_xlsx}")
    print(f"QA Excel -> {args.qa_report_xlsx}")


if __name__ == "__main__":
    main()


