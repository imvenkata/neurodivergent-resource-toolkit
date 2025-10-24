"""
Enrich Description text using a local Ollama LLM.

For each row, extracts:
 - description_short
 - gmaps_formatted_address
 - gmaps_phone
 - gmaps_website

If a value is not present, return null (empty string in CSV).

Supports CSV and Excel input/output. Uses pandas if available for Excel; falls back to CSV.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from typing import Dict, List, Optional, Tuple
from urllib import request


def _read_csv_with_encoding(path: str, encoding_hint: Optional[str] = None) -> Tuple[List[Dict[str, str]], List[str]]:
    encodings_to_try = []
    if encoding_hint:
        encodings_to_try.append(encoding_hint)
    encodings_to_try.extend(["utf-8", "utf-8-sig", "cp1252", "latin-1"])
    last_error: Optional[Exception] = None
    for enc in encodings_to_try:
        try:
            with open(path, "r", encoding=enc, errors="strict") as f:
                reader = csv.DictReader(f)
                rows = [{k: (v if v is not None else "") for k, v in row.items()} for row in reader]
                return rows, (reader.fieldnames or [])
        except Exception as e:
            last_error = e
            continue
    raise RuntimeError(f"Failed to read CSV with tried encodings {encodings_to_try}: {last_error}")


def read_rows(input_path: str, sheet: Optional[str] = None, encoding: Optional[str] = None) -> Tuple[List[Dict[str, str]], List[str]]:
    ext = os.path.splitext(input_path)[1].lower()
    if ext in (".xlsx", ".xls"):  # Excel
        try:
            import pandas as pd
        except Exception:
            raise RuntimeError("pandas is required to read Excel files. Install pandas and openpyxl.")
        df = pd.read_excel(input_path, sheet_name=sheet or 0, dtype=str).fillna("")
        rows = df.to_dict(orient="records")
        columns = list(df.columns)
        return rows, [str(c) for c in columns]
    else:  # CSV
        return _read_csv_with_encoding(input_path, encoding_hint=encoding)


def write_rows(output_path: str, rows: List[Dict[str, str]], columns: Optional[List[str]] = None) -> None:
    ext = os.path.splitext(output_path)[1].lower()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if ext in (".xlsx", ".xls"):
        try:
            import pandas as pd
        except Exception:
            print("pandas not installed; falling back to CSV export.")
            csv_path = os.path.splitext(output_path)[0] + ".csv"
            write_rows(csv_path, rows, columns)
            return
        import pandas as pd
        df = pd.DataFrame(rows)
        # Reorder columns if provided
        if columns:
            extra = [c for c in df.columns if c not in columns]
            df = df[[c for c in columns if c in df.columns] + extra]
        df.to_excel(output_path, index=False, engine="openpyxl")
    else:
        # CSV
        if not rows:
            return
        # Build column union
        ordered = list(columns or rows[0].keys())
        seen = set(ordered)
        for r in rows:
            for k in r.keys():
                if k not in seen:
                    ordered.append(k)
                    seen.add(k)
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=ordered)
            writer.writeheader()
            writer.writerows(rows)


OLLAMA_URL_DEFAULT = "http://localhost:11434/api/generate"


def load_env_file(path: Optional[str]) -> Dict[str, str]:
    env: Dict[str, str] = {}
    if not path:
        return env
    if not os.path.exists(path):
        return env
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:
        pass
    return env


def call_ollama_generate(
    model: str,
    prompt: str,
    base_url: str = OLLAMA_URL_DEFAULT,
    json_mode: bool = True,
    timeout: int = 120,
    extra_headers: Optional[Dict[str, str]] = None,
) -> Dict:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    if json_mode:
        payload["format"] = "json"
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if extra_headers:
        headers.update(extra_headers)
    req = request.Request(base_url, data=data, headers=headers)
    with request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
        obj = json.loads(body)
        return obj


def clean_description_via_llm(
    text: str,
    model: str,
    base_url: str,
    auth_header: Optional[str],
    timeout: int = 120,
) -> str:
    """Ask the LLM to strictly remove addresses/contacts/URLs from a short blurb."""
    if not text:
        return ""
    instruction = (
        "Clean the following description. Remove any lines containing postal addresses, venue names, postcodes, phone numbers, emails, or URLs. "
        "Keep only sentences describing the service/activity, audience, frequency, cost or referral info. "
        "Return ONLY the cleaned text, no JSON, no quotes.\n\n"
        f"Text:\n{text}"
    )
    extra_headers = None
    if auth_header:
        if ":" in auth_header:
            name, val = auth_header.split(":", 1)
            extra_headers = {name.strip(): val.strip()}
        else:
            extra_headers = {"Authorization": f"Bearer {auth_header.strip()}"}
    try:
        resp = call_ollama_generate(
            model=model,
            prompt=instruction,
            base_url=base_url,
            json_mode=False,
            timeout=timeout,
            extra_headers=extra_headers,
        )
        return (resp.get("response") or "").strip()
    except Exception:
        return text


EXTRACTION_INSTRUCTIONS = (
    "You are an information extraction assistant. Given a free-text Description, extract the following fields as JSON.\n"
    "Rules:\n"
    "- Return ONLY valid JSON object, no extra commentary.\n"
    "- If a field is not present, set it to null.\n"
    "- description_short: A concise summary of the activity/service in <= 4 bullet-like lines.\n"
    "  STRICT: Do NOT include any postal address lines, postcodes, venue names/lines, phone numbers, emails, or URLs.\n"
    "  Keep only what the service does, who it's for, frequency, cost, or referral info.\n"
    "- gmaps_formatted_address: Multi-line postal address if present; otherwise null.\n"
    "- gmaps_phone: Digits-only UK phone (keep leading 0 or +44 if present); else null.\n"
    "- gmaps_website: First website URL if present; else null.\n"
    "- gmaps_addr_postal_code: UK postcode if present; else null.\n"
)


def build_prompt(description_text: str) -> str:
    example_desc = (
        "Weekly group called Connect set up by Natasha of Dream Box Education. Natasha is an SEN teacher who now works directly with families in their homes.\n"
        "-Specially designed play for children with additional needs.\n"
        "-Advice about how to engage your child and encourage communication.\n"
        "-For people in NE London, West Essex and Herts borders...\n"
        "-£3 per family including refreshments.\n"
        "All welcome with or without your child.\n"
        "No diagnosis necessary.\n"
        "Call ahead with any questions.\n"
        "tel: 07947730797\n"
        "email: Tasha@dreamboxeducation.co.uk\n"
        "Trinity Church,\n"
        "Mannock Drive,\n"
        "Loughton IG10 2JD,, -Share your concerns, chat and learn from others. Or just take time to relax and socialise."
    )
    example_json = {
        "description_short": "Weekly group called Connect set up by Natasha of Dream Box Education. Natasha is an SEN teacher who now works directly with families in their homes.\n-Specially designed play for children with additional needs.\n-Advice about how to engage your child and encourage communication.\n-For people in NE London, West Essex and Herts borders...",
        "gmaps_formatted_address": "Trinity Church,\nMannock Drive,\nLoughton IG10 2JD",
        "gmaps_phone": "07947730797",
        "gmaps_website": None,
        "gmaps_addr_postal_code": "IG10 2JD",
    }
    prompt = (
        f"{EXTRACTION_INSTRUCTIONS}\n\n"
        f"Example Input Description:\n{example_desc}\n\n"
        f"Example JSON Output:\n{json.dumps(example_json, ensure_ascii=False)}\n\n"
        f"Now extract from this Description:\n{description_text}\n"
    )
    return prompt


PHONE_RE = re.compile(r"(?:(?:\+?44\s?\d{3,}|0\s?\d{3,})[\s\d-]{5,}\d)")
URL_RE = re.compile(r"https?://\S+", re.I)
EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)


def fallback_extract(description_text: str) -> Dict[str, Optional[str]]:
    phone = None
    m = PHONE_RE.search(description_text)
    if m:
        phone = re.sub(r"[^+\d]", "", m.group(0))
    url = None
    u = URL_RE.search(description_text)
    if u:
        url = u.group(0).rstrip('.,);]"\'')
    # UK postcode
    pc = None
    mpc = re.search(r"\b([A-Z]{1,2}\d{1,2}[A-Z]?)\s?(\d[A-Z]{2})\b", description_text, flags=re.I)
    if mpc:
        pc = f"{mpc.group(1).upper()} {mpc.group(2).upper()}"
    return {
        "description_short": None,
        "gmaps_formatted_address": None,
        "gmaps_phone": phone,
        "gmaps_website": url,
        "gmaps_addr_postal_code": pc,
    }


def _clean_line(line: str) -> str:
    return line.strip().strip(",; ")


def dedupe_description_text(text: str) -> str:
    if not text:
        return ""
    # First remove duplicate lines (case-insensitive), preserving order
    raw_lines = [ln for ln in text.splitlines() if ln.strip()]
    seen_lines = set()
    unique_lines = []
    for ln in raw_lines:
        key = ln.strip().lower()
        if key not in seen_lines:
            seen_lines.add(key)
            unique_lines.append(ln.strip())

    # Then remove duplicate sentences across the text, preserving order
    seen_sent = set()
    cleaned_lines = []
    for ln in unique_lines:
        parts = re.split(r"(?<=[.!?])\s+", ln)
        dedup_parts = []
        for p in parts:
            p_clean = p.strip()
            if not p_clean:
                continue
            key = p_clean.lower()
            if key not in seen_sent:
                seen_sent.add(key)
                dedup_parts.append(p_clean)
        if dedup_parts:
            cleaned_lines.append(" ".join(dedup_parts))

    return "\n".join(cleaned_lines).strip()


def rule_extract(description_text: str) -> Dict[str, Optional[str]]:
    if not description_text:
        return {
            "description_short": None,
            "gmaps_formatted_address": None,
            "gmaps_phone": None,
            "gmaps_website": None,
            "gmaps_addr_postal_code": None,
        }

    text = description_text.strip()
    # Locate cut index at first contact/postcode occurrence
    cut_positions = []
    m_phone = PHONE_RE.search(text)
    if m_phone:
        cut_positions.append(m_phone.start())
    m_email = EMAIL_RE.search(text)
    if m_email:
        cut_positions.append(m_email.start())
    m_pc = re.search(r"\b([A-Z]{1,2}\d{1,2}[A-Z]?)\s?(\d[A-Z]{2})\b", text, flags=re.I)
    if m_pc:
        cut_positions.append(m_pc.start())
    cut_at = min(cut_positions) if cut_positions else None

    description_short = text if cut_at is None else text[:cut_at]
    # Keep up to 4 non-empty lines, remove lines with contact/address tokens
    lines = [ln for ln in description_short.splitlines()]
    filtered: List[str] = []
    for ln in lines:
        raw = ln.strip()
        if not raw:
            continue
        low = raw.lower()
        if ("http://" in low or "https://" in low or "www." in low
            or "tel:" in low or "phone" in low or "email" in low or EMAIL_RE.search(raw)
            or re.search(r"\b([A-Z]{1,2}\d{1,2}[A-Z]?)\s?(\d[A-Z]{2})\b", raw, flags=re.I)):
            continue
        filtered.append(raw)
        if len(filtered) >= 4:
            break
    description_short = "\n".join(filtered).strip() if filtered else ""

    # Address block: from postcode line and up to 2 previous address-like lines
    address = None
    if m_pc:
        # Work line-wise to find the line containing the postcode
        text_lines = [ln for ln in description_text.splitlines()]
        pc_line_idx = None
        for idx, ln in enumerate(text_lines):
            if re.search(r"\b([A-Z]{1,2}\d{1,2}[A-Z]?)\s?(\d[A-Z]{2})\b", ln, flags=re.I):
                pc_line_idx = idx
                break
        if pc_line_idx is not None:
            parts = []
            # include up to 2 previous plausible address lines
            for j in range(max(0, pc_line_idx - 2), pc_line_idx):
                cand = _clean_line(text_lines[j])
                if not cand:
                    continue
                low = cand.lower()
                if ("http://" in low or "https://" in low or "www." in low or EMAIL_RE.search(cand)
                    or "tel:" in low or "phone" in low):
                    continue
                parts.append(cand)
            parts.append(_clean_line(text_lines[pc_line_idx]))
            # Dedup adjacent duplicates and empty
            final_parts = []
            for p in parts:
                if p and (not final_parts or final_parts[-1] != p):
                    final_parts.append(p)
            address = "\n".join(final_parts).strip() if final_parts else None

    # Phone and website (first URL only)
    phone = m_phone.group(0) if m_phone else None
    if phone:
        phone = re.sub(r"[^+\d]", "", phone)
    url = None
    mu = URL_RE.search(text)
    if mu:
        url = mu.group(0).rstrip('.,);]"\'')

    pc_val = (m_pc.group(0).upper().replace(" ", "")) if m_pc else None
    if pc_val:
        pc_val = f"{m_pc.group(1).upper()} {m_pc.group(2).upper()}"

    return {
        "description_short": description_short or None,
        "gmaps_formatted_address": address,
        "gmaps_phone": phone,
        "gmaps_website": url,
        "gmaps_addr_postal_code": pc_val,
    }


def parse_llm_json(response_text: str) -> Dict[str, Optional[str]]:
    try:
        obj = json.loads(response_text)
        result = {
            "description_short": obj.get("description_short"),
            "gmaps_formatted_address": obj.get("gmaps_formatted_address"),
            "gmaps_phone": obj.get("gmaps_phone"),
            "gmaps_website": obj.get("gmaps_website"),
            "gmaps_addr_postal_code": obj.get("gmaps_addr_postal_code"),
        }
        # Normalize null-like values
        for k, v in list(result.items()):
            if isinstance(v, str):
                v = v.strip()
                if v == "":
                    result[k] = None
                else:
                    result[k] = v
        return result
    except Exception:
        return {
            "description_short": None,
            "gmaps_formatted_address": None,
            "gmaps_phone": None,
            "gmaps_website": None,
            "gmaps_addr_postal_code": None,
        }

def resolve_description_column(columns: List[str], preferred: Optional[str]) -> Optional[str]:
    if not columns:
        return None
    # 1) Exact match
    if preferred and preferred in columns:
        return preferred
    # 2) Case-insensitive direct match
    lower_map = {c.lower(): c for c in columns}
    if preferred and preferred.lower() in lower_map:
        return lower_map[preferred.lower()]
    # 3) Heuristic candidates
    candidates = [
        "description",
        "desc",
        "full description",
        "full_description",
        "content",
        "details",
        "notes",
    ]
    for cand in candidates:
        if cand in lower_map:
            return lower_map[cand]
    # 4) Fallback: first column that contains 'descr' substring
    for c in columns:
        if 'descr' in c.lower():
            return c
    return None


def enrich_rows(
    rows: List[Dict[str, str]],
    description_col: str,
    model: str,
    base_url: str,
    auth_header: Optional[str],
    retries: int,
    sleep: float,
    progress_interval: int,
    limit: Optional[int] = None,
    llm_only: bool = False,
) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    total = min(len(rows), limit) if limit is not None else len(rows)
    for i, r in enumerate(rows, start=1):
        if limit is not None and i > limit:
            break
        desc = (r.get(description_col) or "").strip()
        result: Dict[str, Optional[str]] = {"description_short": None, "gmaps_formatted_address": None, "gmaps_phone": None, "gmaps_website": None, "gmaps_addr_postal_code": None}
        error_msg = ""
        if desc:
            if llm_only:
                # LLM-only mode: do not use rule-based or regex fallback
                prompt = build_prompt(desc)
                for attempt in range(retries + 1):
                    try:
                        extra_headers = None
                        if auth_header:
                            # Support either full header line or bare token
                            if ":" in auth_header:
                                # e.g., "Authorization: Bearer TOKEN"
                                name, val = auth_header.split(":", 1)
                                extra_headers = {name.strip(): val.strip()}
                            else:
                                extra_headers = {"Authorization": f"Bearer {auth_header.strip()}"}
                        resp = call_ollama_generate(
                            model=model,
                            prompt=prompt,
                            base_url=base_url,
                            json_mode=True,
                            extra_headers=extra_headers,
                        )
                        text = resp.get("response") or ""
                        parsed = parse_llm_json(text)
                        # Use parsed values only (no rule or regex fallback)
                        result = parsed
                        # Additional LLM cleanup pass for description_short to exclude addresses/URLs
                        if result.get("description_short"):
                            result["description_short"] = clean_description_via_llm(
                                text=result.get("description_short") or "",
                                model=model,
                                base_url=base_url,
                                auth_header=auth_header,
                            )
                        break
                    except Exception as e:
                        error_msg = str(e)
                        time.sleep(sleep)
            else:
                # First pass: deterministic rule extraction
                result = rule_extract(desc)
                # If any field still missing, call LLM to try to fill gaps
                if any(result.get(k) in (None, "") for k in ("description_short", "gmaps_formatted_address", "gmaps_phone", "gmaps_website", "gmaps_addr_postal_code")):
                    prompt = build_prompt(desc)
                    for attempt in range(retries + 1):
                        try:
                            extra_headers = None
                            if auth_header:
                                # Support either full header line or bare token
                                if ":" in auth_header:
                                    # e.g., "Authorization: Bearer TOKEN"
                                    name, val = auth_header.split(":", 1)
                                    extra_headers = {name.strip(): val.strip()}
                                else:
                                    extra_headers = {"Authorization": f"Bearer {auth_header.strip()}"}
                            resp = call_ollama_generate(
                                model=model,
                                prompt=prompt,
                                base_url=base_url,
                                json_mode=True,
                                extra_headers=extra_headers,
                            )
                            text = resp.get("response") or ""
                            parsed = parse_llm_json(text)
                            # Merge LLM outputs only where we still lack data
                            for k, v in parsed.items():
                                if (result.get(k) in (None, "")) and v:
                                    result[k] = v
                            # If still nothing parsed, use minimal regex fallback to fill phone/url/pc
                            if all(result.get(k) in (None, "") for k in ("gmaps_phone", "gmaps_website", "gmaps_addr_postal_code")):
                                fb = fallback_extract(desc)
                                for k, v in fb.items():
                                    if (result.get(k) in (None, "")) and v:
                                        result[k] = v
                            break
                        except Exception as e:
                            error_msg = str(e)
                            time.sleep(sleep)
        else:
            error_msg = "empty_description"

        # Create output row with new fields appended
        out_row = dict(r)
        # Impute only if missing in original row
        # Overwrite behavior controlled at call site by a flag; read from env var passthrough
        overwrite_description_short = bool(os.getenv("OVERWRITE_DESCRIPTION_SHORT", "").strip())
        if overwrite_description_short or not (out_row.get("description_short") or "").strip():
            ds = result.get("description_short") or ""
            # Only apply post-filter when NOT in LLM-only mode
            if ds and not llm_only:
                lines = [ln for ln in ds.splitlines() if ln.strip()]
                filtered = []
                for ln in lines:
                    low = ln.lower()
                    if re.search(r"\b\d{3,}\b", ln):
                        if any(tok in low for tok in ["per week", "weekly", "monthly", "free", "cost", "£", "referral"]):
                            filtered.append(ln)
                        continue
                    if any(tok in low for tok in ["tel:", "phone", "email", "@", "http://", "https://", "www."]):
                        continue
                    if re.search(r"\b[A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2}\b", ln):
                        continue
                    if any(tok in low for tok in ["road", "rd", "street", "st ", "st.", "avenue", "ave", "lane", "ln", "close", "cl", "square", "sq", "church", "centre", "center", "hall", "drive", "dr", "park"]):
                        continue
                    filtered.append(ln)
                ds = "\n".join(filtered).strip()
            out_row["description_short"] = ds
        if not (out_row.get("gmaps_formatted_address") or "").strip():
            out_row["gmaps_formatted_address"] = result.get("gmaps_formatted_address") or ""
        if not (out_row.get("gmaps_phone") or "").strip():
            out_row["gmaps_phone"] = result.get("gmaps_phone") or ""
        if not (out_row.get("gmaps_website") or "").strip():
            out_row["gmaps_website"] = result.get("gmaps_website") or ""
        if not (out_row.get("gmaps_addr_postal_code") or "").strip():
            out_row["gmaps_addr_postal_code"] = result.get("gmaps_addr_postal_code") or ""
        out_row["llm_error"] = error_msg
        out.append(out_row)

        if progress_interval and i % progress_interval == 0:
            print(f"[{i}/{total}] enriched; last_error={bool(error_msg)}")

    print(f"[done {min(i, total)}/{total}]")
    return out


def parse_args() -> argparse.Namespace:
    default_root = "/Users/venkata/startup/data_scraper"
    default_input = os.path.join(default_root, "to_be_normalised", "resources_data.csv")
    default_output = os.path.join(default_root, "to_be_normalised", "resources_data_enriched.csv")
    default_output_xlsx = os.path.join(default_root, "to_be_normalised", "resources_data_enriched.xlsx")

    p = argparse.ArgumentParser(description="Enrich Description via local Ollama LLM")
    p.add_argument("--input", default=default_input, help="Path to input CSV/XLSX")
    p.add_argument("--sheet", default=None, help="Excel sheet name or index (e.g., 0)")
    p.add_argument("--description-col", default="description", help="Column name containing Description text (case-insensitive; auto-detect if missing)")
    p.add_argument("--output", default=default_output, help="Path to output CSV")
    p.add_argument("--output-xlsx", default=default_output_xlsx, help="Path to output Excel")
    p.add_argument("--model", default="llama3.1:8b-instruct", help="Ollama model name/tag")
    p.add_argument("--env-file", default=".env", help="Path to .env file with OLLAMA_URL / OLLAMA_AUTH_HEADER / OLLAMA_API_KEY")
    p.add_argument("--ollama-url", default=None, help="Ollama generate endpoint URL (overrides env)")
    p.add_argument("--auth-header", default=None, help="Authorization header or bare token (overrides env)")
    p.add_argument("--retries", type=int, default=2, help="Retries on API failure")
    p.add_argument("--sleep", type=float, default=0.25, help="Sleep seconds between retries")
    p.add_argument("--progress-interval", type=int, default=25, help="Print progress every N rows (0 to disable)")
    p.add_argument("--limit", type=int, default=None, help="Limit number of rows for a quick run")
    p.add_argument("--encoding", default=None, help="Override CSV file encoding (e.g., cp1252)")
    p.add_argument("--llm-only", action="store_true", help="Use only LLM (no rule/regex fallback, no post-filter)")
    p.add_argument("--overwrite-description-short", action="store_true", help="Overwrite description_short even if it already has a value")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    env_from_file = load_env_file(args.env_file)
    # Resolve base URL
    base_url = (
        args.ollama_url
        or env_from_file.get("OLLAMA_URL")
        or os.getenv("OLLAMA_URL")
        or OLLAMA_URL_DEFAULT
    )
    # Resolve auth header
    auth_header = (
        args.auth_header
        or env_from_file.get("OLLAMA_AUTH_HEADER")
        or os.getenv("OLLAMA_AUTH_HEADER")
    )
    if not auth_header:
        token = env_from_file.get("OLLAMA_API_KEY") or os.getenv("OLLAMA_API_KEY")
        if token:
            auth_header = token
    # Interpret sheet as int if it's a numeric string
    sheet_param = None
    if args.sheet is None:
        sheet_param = None
    else:
        try:
            # try to parse numeric index
            sheet_param = int(args.sheet)
        except (TypeError, ValueError):
            sheet_param = args.sheet

    try:
        rows, columns = read_rows(args.input, sheet=sheet_param, encoding=args.encoding)
    except Exception as e:
        print("Failed to read input:", e)
        sys.exit(2)

    # Resolve description column robustly
    desc_col = resolve_description_column(columns, args.description_col)
    if not desc_col:
        print("Failed to find a Description column. Available columns:", ", ".join(columns))
        sys.exit(2)

    enriched = enrich_rows(
        rows=rows,
        description_col=desc_col,
        model=args.model,
        base_url=base_url,
        auth_header=auth_header,
        retries=args.retries,
        sleep=args.sleep,
        progress_interval=args.progress_interval,
        limit=args.limit,
        llm_only=args.llm_only,
        # pass via closure by adding parameter to function signature? We'll set a local var and capture below
    )

    # Write CSV and Excel
    write_rows(args.output, enriched, columns=None)
    write_rows(args.output_xlsx, enriched, columns=None)
    print(f"Wrote -> {args.output}")
    print(f"Wrote -> {args.output_xlsx}")


if __name__ == "__main__":
    main()


