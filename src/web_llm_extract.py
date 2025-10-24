import argparse
import html
import json
import os
import re
import sys
from pathlib import Path
# dataclass reserved for future structuring; avoid unused import for now
from typing import Dict, List, Optional, Set, Tuple
from urllib import request, parse
from urllib.error import HTTPError, URLError

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load .env from current directory or parent directories
    env_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass  # python-dotenv not installed, will use system env vars


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
)


def fetch_url(url: str, timeout: int = 20) -> Optional[str]:
    req = request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="ignore")
    except (request.URLError, TimeoutError, ValueError):
        return None


TAG_RE = re.compile(r"<[^>]+>")
SCRIPT_STYLE_RE = re.compile(r"<(script|style)[\s\S]*?</\1>", re.I)


def html_to_text(html_str: str) -> str:
    if not html_str:
        return ""
    cleaned = SCRIPT_STYLE_RE.sub("\n", html_str)
    cleaned = html.unescape(cleaned)
    cleaned = re.sub(r"(?i)<\s*br\s*/?>", "\n", cleaned)
    cleaned = re.sub(r"(?i)</\s*p\s*>", "\n", cleaned)
    cleaned = re.sub(r"(?i)<\s*p\b[^>]*>", "", cleaned)
    cleaned = TAG_RE.sub(" ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    text = cleaned.strip()
    # Recreate some line breaks for headings and list items
    text = re.sub(r"\s*([.!?])\s+", r"\1\n", text)
    return text


LINK_RE = re.compile(r"<a\b[^>]*href=\"([^\"]+)\"[^>]*>(.*?)</a>", re.I)


def extract_links(base_url: str, html_str: str) -> List[str]:
    out: List[str] = []
    if not html_str:
        return out
    for m in LINK_RE.finditer(html_str):
        href = m.group(1).strip()
        if not href or href.startswith("mailto:") or href.startswith("tel:"):
            continue
        abs_url = parse.urljoin(base_url, href)
        out.append(abs_url)
    return out


def same_site(url: str, root: str) -> bool:
    a = parse.urlparse(url)
    b = parse.urlparse(root)
    return (a.scheme, a.netloc) == (b.scheme, b.netloc)


KEYWORDS = (
    "about",
    "service",
    "services",
    "contact",
    "what-we-do",
    "who-we-are",
    "support",
    "program",
    "programme",
    "offer",
)


def rank_link(url: str) -> int:
    low = url.lower()
    score = 0
    for kw in KEYWORDS:
        if kw in low:
            score += 2
    if low.endswith(".pdf"):
        score -= 3
    if any(ext in low for ext in (".jpg", ".png", ".gif", ".webp")):
        score -= 3
    return score


def crawl_site(start_url: str, max_pages: int = 6) -> List[Tuple[str, str]]:
    visited: Set[str] = set()
    queue: List[str] = [start_url]
    collected: List[Tuple[str, str]] = []
    while queue and len(collected) < max_pages:
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)
        if not same_site(url, start_url):
            continue
        html_doc = fetch_url(url)
        if not html_doc:
            continue
        collected.append((url, html_doc))
        links = [lnk for lnk in extract_links(url, html_doc) if same_site(lnk, start_url)]
        links = sorted(set(links), key=lambda u: -rank_link(u))
        for l in links:
            if l not in visited and l not in queue:
                queue.append(l)
    return collected


def build_prompt(center_name: str, website_url: str, docs: List[Tuple[str, str]]) -> str:
    parts = []
    for url, html_doc in docs:
        text = html_to_text(html_doc)
        if not text:
            continue
        # limit per page to avoid overlong prompts
        parts.append(f"\n\n=== PAGE: {url} ===\n{text[:8000]}")
        if len(parts) >= 8:
            break
    body = "".join(parts)

    instructions = (
        f"TASK: Extract structured information about {center_name} from their website content.\n"
        f"Website: {website_url}\n\n"
        "RULES:\n"
        "• Extract factual information only - do not infer or assume\n"
        "• Use \"Not specified\" for missing text fields, [] for missing arrays\n"
        "• Choose the most appropriate category from the list below\n\n"
        "CATEGORIES (choose one):\n"
        "1. Assessment & Diagnosis - Diagnostic Centers, Assessment Clinics, Psychoeducational Evaluation\n"
        "2. Crisis & Emergency - Crisis Helplines, Emergency Intervention, Mental Health Crisis Teams\n"
        "3. Education & Learning - SEN Schools, Mainstream Resources, Training, Skills Development, Tutoring\n"
        "4. Employment - Job Coaching, Workplace Accommodations, Vocational Training, Supported Employment\n"
        "5. Housing & Benefits - Housing Assistance, Benefits Advice, Independent Living, Welfare Navigation\n"
        "6. Transport & Accessibility - Accessible Transport, Travel Training, Mobility Services, Subsidies\n"
        "7. Community & Social - Local Groups, Organization Branches, Peer Networks, Meetups, Parent/Carer Groups\n"
        "8. Recreation & Activities - Sports & Fitness, Arts & Entertainment, Play Centers, Hobby Clubs\n"
        "9. Unknown/Uncategorized - Only when no other category fits\n\n"
        "EXTRACTION REQUIREMENTS:\n"
        "• description_short: 1-2 sentences summarizing main purpose and key services\n"
        "• category: Choose from list above (e.g., \"Education & Learning\")\n"
        "• subcategory: Select relevant subcategory or use \"General\"\n"
        "• age_range: Extract age ranges (e.g., \"Adults (18+)\", \"Ages 4½ to 22\", \"All ages\")\n"
        "• conditions_supported: List neurodivergent conditions (ADHD, Autism/ASC, Dyslexia, etc.)\n"
        "• specific_services: List concrete services (assessment, support groups, therapy, etc.)\n"
        "• organization_type: NHS Service, Charity/Non-profit, Local Authority, Private School, Private Provider, Social Enterprise, or Unknown\n"
        "• contact_info: Extract phone, email, full address if available\n"
        "• address_components: Break down address into postal_code, postal_town, admin_area_level_1 (country/region), admin_area_level_2 (county/area)\n"
        "• additional_notes: Note any funding, accessibility, referral requirements, payment plans\n"
        "• data_confidence: High (clear info), Medium (some ambiguity), or Low (limited info)\n"
        "• reasoning: Brief explanation of your categorization choice\n\n"
        "NEURODIVERGENT RELEVANCE CHECK (IMPORTANT):\n"
        "• is_neurodivergent_related: true/false - Does this service specifically support neurodivergent individuals?\n"
        "• neurodivergent_relevance_score: High/Medium/Low/None\n"
        "  - High: Explicitly specializes in ADHD, Autism, Dyslexia, or other neurodivergent conditions\n"
        "  - Medium: Offers some neurodivergent support but not primary focus\n"
        "  - Low: May help neurodivergent people but not specifically designed for them\n"
        "  - None: Not relevant to neurodivergent support\n"
        "• neurodivergent_focus: Brief note on what neurodivergent conditions/needs are addressed\n\n"
        "OUTPUT: Return ONLY valid JSON in this exact structure:\n"
        "{\n"
        "  \"center_name\": \"" + center_name + "\",\n"
        "  \"website_url\": \"" + website_url + "\",\n"
        "  \"description_short\": \"\",\n"
        "  \"category\": \"\",\n"
        "  \"subcategory\": \"\",\n"
        "  \"age_range\": \"\",\n"
        "  \"conditions_supported\": [],\n"
        "  \"specific_services\": [],\n"
        "  \"organization_type\": \"\",\n"
        "  \"contact_info\": {\"phone\": \"\", \"email\": \"\", \"address\": \"\"},\n"
        "  \"address_components\": {\n"
        "    \"postal_code\": \"\",\n"
        "    \"postal_town\": \"\",\n"
        "    \"admin_area_level_1\": \"\",\n"
        "    \"admin_area_level_2\": \"\"\n"
        "  },\n"
        "  \"additional_notes\": \"\",\n"
        "  \"data_confidence\": \"\",\n"
        "  \"reasoning\": \"\",\n"
        "  \"is_neurodivergent_related\": true,\n"
        "  \"neurodivergent_relevance_score\": \"High\",\n"
        "  \"neurodivergent_focus\": \"\"\n"
        "}\n"
    )
    prompt = f"{instructions}\nWEBSITE CONTENT (excerpted):\n{body}\n"
    return prompt


def _post_json(url: str, payload: Dict, headers: Dict[str, str], timeout: int) -> Dict:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, headers=headers)
    with request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8", errors="ignore")
        return json.loads(body)


def _normalize_ollama_base(base_url: Optional[str]) -> Tuple[str, List[str]]:
    base = base_url or os.getenv("OLLAMA_URL") or "http://localhost:11434"
    # If user passed full endpoint, accept as-is and infer sibling
    if base.endswith("/api/generate"):
        return base, [base, base.rsplit("/", 1)[0] + "/chat"]
    if base.endswith("/api/chat"):
        return base, [base.rsplit("/", 1)[0] + "/generate", base]
    # If user passed /api, append generate/chat
    if base.endswith("/api"):
        return base, [base + "/generate", base + "/chat"]
    # Otherwise treat as host root
    api = base.rstrip("/") + "/api"
    return api, [api + "/generate", api + "/chat"]


def call_ollama(model: str, prompt: str, base_url: Optional[str] = None, auth_header: Optional[str] = None, timeout: int = 120) -> str:
    _, endpoints = _normalize_ollama_base(base_url)
    headers = {"Content-Type": "application/json"}
    if auth_header:
        if ":" in auth_header:
            k, v = auth_header.split(":", 1)
            headers[k.strip()] = v.strip()
        else:
            headers["Authorization"] = f"Bearer {auth_header.strip()}"

    last_error: Optional[str] = None
    for url in endpoints:
        try:
            if url.endswith("/generate"):
                obj = _post_json(url, {"model": model, "prompt": prompt, "stream": False}, headers, timeout)
                return obj.get("response") or obj.get("message", {}).get("content", "")
            else:  # /chat
                obj = _post_json(url, {"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False}, headers, timeout)
                return obj.get("message", {}).get("content", "") or obj.get("response", "")
        except HTTPError as e:
            # Try next endpoint on 404; otherwise propagate
            detail = f"HTTP {e.code}: {e.reason}"
            try:
                detail_body = e.read().decode("utf-8", errors="ignore")
                if detail_body:
                    detail += f" | {detail_body[:200]}"
            except Exception:
                pass
            last_error = detail
            if e.code == 404:
                continue
            raise
        except URLError as e:
            last_error = str(e)
            continue
        except TimeoutError as e:
            last_error = str(e)
            continue
        except Exception as e:
            last_error = str(e)
            continue

    raise RuntimeError(f"Failed to call Ollama endpoints ({', '.join(endpoints)}): {last_error}")


def call_openai_chat(model: str, prompt: str, api_key: Optional[str] = None, timeout: int = 120) -> str:
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY not set")
    url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You extract structured JSON from website content."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
    }
    req = request.Request(url, data=data, headers=headers)
    with request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8", errors="ignore")
        obj = json.loads(body)
        return obj["choices"][0]["message"]["content"]


def call_gemini(model: str, prompt: str, api_key: Optional[str] = None, timeout: int = 120) -> str:
    key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY (or GOOGLE_API_KEY) not set")

    mdl = model or "gemini-1.5-flash"
    # Prefer v1beta; list available models via GET
    def list_models(ver: str) -> List[str]:
        url = f"https://generativelanguage.googleapis.com/{ver}/models?key={key}"
        req = request.Request(url, headers={"Content-Type": "application/json"})
        try:
            with request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
                obj = json.loads(body)
                return [m.get("name", "") for m in (obj.get("models") or [])]
        except Exception:
            return []

    models_v1beta = list_models("v1beta")

    # Build candidates from discovery with graceful fallback when '-latest' not present
    model_ids_beta = [m.split("/", 1)[1] for m in models_v1beta]

    def pick_candidates(requested: str) -> List[str]:
        candidates: List[str] = []
        # Exact match
        if requested in model_ids_beta:
            candidates.append(requested)
        # Base prefix (handle '-latest' by stripping)
        base = requested[:-7] if requested.endswith("-latest") else requested
        base = base.rstrip("-")
        prefix_matches = [mid for mid in model_ids_beta if mid.startswith(base)]
        for mid in prefix_matches:
            if mid not in candidates:
                candidates.append(mid)
        # If still empty, prefer any 'flash' models, then 'pro'
        if not candidates:
            flash_models = [mid for mid in model_ids_beta if "flash" in mid]
            pro_models = [mid for mid in model_ids_beta if "pro" in mid]
            for mid in flash_models + pro_models:
                if mid not in candidates:
                    candidates.append(mid)
        # Always append safe fallbacks at the end to try
        for mid in [requested, "gemini-1.5-flash", "gemini-1.5-pro"]:
            if mid not in candidates:
                candidates.append(mid)
        return candidates

    model_candidates = pick_candidates(mdl)

    versions = ["v1beta"]
    headers = {"Content-Type": "application/json"}

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
        }
    }

    last_error: Optional[str] = None
    for ver in versions:
        for m in model_candidates:
            url = f"https://generativelanguage.googleapis.com/{ver}/models/{m}:generateContent?key={key}"
            try:
                obj = _post_json(url, payload, headers, timeout)
                # Typical shape
                candidates = obj.get("candidates") or []
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and isinstance(parts[0], dict) and "text" in parts[0]:
                        return parts[0]["text"]
                # Some responses may include text directly (fallback)
                if "text" in obj:
                    return obj["text"]
                # As a last resort, return raw JSON string
                return json.dumps(obj)
            except HTTPError as e:
                detail = f"HTTP {e.code}: {e.reason}"
                try:
                    body = e.read().decode("utf-8", errors="ignore")
                    if body:
                        detail += f" | {body[:200]}"
                except Exception:
                    pass
                last_error = detail
                # Try next combo on 404/400
                if e.code in (400, 404):
                    continue
                raise
            except URLError as e:
                last_error = str(e)
                continue
            except TimeoutError as e:
                last_error = str(e)
                continue
            except Exception as e:
                last_error = str(e)
                continue

    raise RuntimeError(f"Gemini request failed for models {model_candidates} and versions {versions}: {last_error}")


def try_parse_json(text: str) -> Dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
        raise


RELIABLE_DOMAINS = (
    "nhs.uk", "gov.uk", "charity", "org.uk", 
    "google.com/maps", "yell.com", "192.com",
    "facebook.com", "linkedin.com"
)


# UK county/area mappings for admin_area_level_2
UK_COUNTIES = {
    "greater london": "Greater London",
    "london": "Greater London",
    "hertfordshire": "Hertfordshire",
    "essex": "Essex",
    "kent": "Kent",
    "surrey": "Surrey",
    "berkshire": "Berkshire",
    "buckinghamshire": "Buckinghamshire",
    "oxfordshire": "Oxfordshire",
    "cambridgeshire": "Cambridgeshire",
    "suffolk": "Suffolk",
    "norfolk": "Norfolk",
    "bedfordshire": "Bedfordshire",
    "northamptonshire": "Northamptonshire",
    "warwickshire": "Warwickshire",
    "west midlands": "West Midlands",
    "staffordshire": "Staffordshire",
    "derbyshire": "Derbyshire",
    "nottinghamshire": "Nottinghamshire",
    "leicestershire": "Leicestershire",
    "lincolnshire": "Lincolnshire",
    "yorkshire": "Yorkshire",
    "lancashire": "Lancashire",
    "merseyside": "Merseyside",
    "cheshire": "Cheshire",
    "manchester": "Greater Manchester",
    "greater manchester": "Greater Manchester",
}


def is_reliable_source(url: str) -> bool:
    """Check if URL is from a reliable source."""
    url_lower = url.lower()
    return any(domain in url_lower for domain in RELIABLE_DOMAINS)


def parse_uk_address(address: str) -> Dict[str, str]:
    """Parse UK address into components."""
    components = {
        "postal_code": "",
        "postal_town": "",
        "admin_area_level_1": "",
        "admin_area_level_2": ""
    }
    
    if not address:
        return components
    
    # Extract postcode (UK format)
    postcode_pattern = r'\b([A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2})\b'
    postcode_match = re.search(postcode_pattern, address, re.I)
    if postcode_match:
        components["postal_code"] = postcode_match.group(1).upper()
    
    # Default admin_area_level_1 for UK addresses
    if any(word in address.lower() for word in ["uk", "united kingdom", "england", "scotland", "wales"]):
        if "scotland" in address.lower():
            components["admin_area_level_1"] = "Scotland"
        elif "wales" in address.lower():
            components["admin_area_level_1"] = "Wales"
        elif "northern ireland" in address.lower():
            components["admin_area_level_1"] = "Northern Ireland"
        else:
            components["admin_area_level_1"] = "England"
    
    # Extract county/area (admin_area_level_2)
    address_lower = address.lower()
    for key, value in UK_COUNTIES.items():
        if key in address_lower:
            components["admin_area_level_2"] = value
            break
    
    # Extract town/city (postal_town)
    # Common UK cities and towns
    uk_towns = [
        "london", "birmingham", "manchester", "liverpool", "leeds", "sheffield", 
        "bristol", "edinburgh", "glasgow", "cardiff", "belfast", "nottingham",
        "leicester", "coventry", "bradford", "cambridge", "oxford", "brighton",
        "stevenage", "basildon", "berkhamsted", "hertford", "watford", "luton",
        "romford", "ilford", "barking", "enfield", "croydon", "bromley"
    ]
    
    for town in uk_towns:
        if town in address_lower:
            components["postal_town"] = town.title()
            break
    
    # If London is in admin_area_level_2 but not explicitly stated
    if components["admin_area_level_2"] == "Greater London" and not components["postal_town"]:
        components["postal_town"] = "London"
    
    return components


def search_web_for_contact(center_name: str, website_url: str, timeout: int = 10) -> Dict[str, any]:
    """Search web for missing contact information from reliable sources."""
    contact_info = {
        "phone": None,
        "email": None, 
        "address": None,
        "address_components": None,
        "sources": []
    }
    
    # Build search query
    domain = parse.urlparse(website_url).netloc if website_url else ""
    search_query = parse.quote(f"{center_name} contact phone email {domain}")
    
    # Use DuckDuckGo HTML search (doesn't require API key)
    search_url = f"https://html.duckduckgo.com/html/?q={search_query}"
    
    try:
        html_content = fetch_url(search_url, timeout=timeout)
        if not html_content:
            return contact_info
            
        # Extract search results
        # Pattern to find result links
        result_pattern = re.compile(r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="([^"]+)"', re.I)
        results = result_pattern.findall(html_content)
        
        # Check first few results from reliable sources
        for result_url in results[:10]:
            # Decode DDG redirect URL
            if "uddg=" in result_url:
                try:
                    actual_url = parse.unquote(result_url.split("uddg=")[1].split("&")[0])
                except Exception:
                    continue
            else:
                actual_url = result_url
                
            if not is_reliable_source(actual_url):
                continue
                
            # Fetch the page
            page_html = fetch_url(actual_url, timeout=timeout)
            if not page_html:
                continue
                
            page_text = html_to_text(page_html)
            
            # Extract phone numbers (UK and international formats)
            if not contact_info["phone"]:
                phone_patterns = [
                    r'\b0\d{3}[\s-]?\d{3}[\s-]?\d{4}\b',  # UK landline
                    r'\b0\d{4}[\s-]?\d{6}\b',  # UK alternative
                    r'\b07\d{3}[\s-]?\d{6}\b',  # UK mobile
                    r'\+44[\s-]?\d{3}[\s-]?\d{3}[\s-]?\d{4}\b',  # International UK
                ]
                for pattern in phone_patterns:
                    match = re.search(pattern, page_text)
                    if match:
                        contact_info["phone"] = match.group(0).strip()
                        break
            
            # Extract email addresses
            if not contact_info["email"]:
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                match = re.search(email_pattern, page_text)
                if match:
                    email = match.group(0).strip()
                    # Filter out common false positives
                    if not any(x in email.lower() for x in ["example.com", "test@", "noreply@"]):
                        contact_info["email"] = email
            
            # Extract address (basic pattern for UK addresses)
            if not contact_info["address"]:
                # Look for UK postcodes
                postcode_pattern = r'\b[A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2}\b'
                match = re.search(postcode_pattern, page_text)
                if match:
                    # Get surrounding context (up to 150 chars before postcode)
                    pos = match.start()
                    start = max(0, pos - 150)
                    address_candidate = page_text[start:match.end()].strip()
                    # Clean up and take last few lines
                    lines = [l.strip() for l in address_candidate.split('\n') if l.strip()]
                    if lines:
                        full_address = ' '.join(lines[-3:])
                        contact_info["address"] = full_address
                        # Parse address into components
                        contact_info["address_components"] = parse_uk_address(full_address)
            
            # Record source
            if contact_info["phone"] or contact_info["email"] or contact_info["address"]:
                contact_info["sources"].append(actual_url)
            
            # Stop if we have all information
            if contact_info["phone"] and contact_info["email"] and contact_info["address"]:
                break
                
    except Exception:
        # Silently fail - web search is optional enhancement
        pass
    
    return contact_info


def main() -> None:
    parser = argparse.ArgumentParser(description="Crawl a site, build LLM prompt, return structured JSON.")
    parser.add_argument("--center-name", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--backend", choices=["ollama", "openai", "gemini"], default="ollama")
    parser.add_argument("--model", default=None, help="Model name (ollama: llama3.1:8b-instruct; openai: gpt-4o-mini; gemini: gemini-1.5-flash)")
    parser.add_argument("--max-pages", type=int, default=6)
    parser.add_argument("--out", default=None, help="Optional path to write JSON output")
    parser.add_argument("--enhance-with-websearch", action="store_true", help="Search web for missing contact info from reliable sources")
    parser.add_argument("--ollama-url", default=None)
    parser.add_argument("--ollama-auth", default=None, help="Header line or bare token")
    parser.add_argument("--openai-key", default=None)
    parser.add_argument("--gemini-key", default=None)
    args = parser.parse_args()

    start = args.url
    docs = crawl_site(start, max_pages=args.max_pages)
    if not docs:
        print("Failed to fetch website content.")
        sys.exit(2)

    prompt = build_prompt(args.center_name, args.url, docs)

    if args.backend == "ollama":
        model = args.model or "llama3.1:8b-instruct"
        resp_text = call_ollama(model=model, prompt=prompt, base_url=args.ollama_url, auth_header=args.ollama_auth)
    elif args.backend == "openai":
        model = args.model or "gpt-4o-mini"
        resp_text = call_openai_chat(model=model, prompt=prompt, api_key=args.openai_key)
    else:  # gemini
        model = args.model or "gemini-1.5-flash"
        key = args.gemini_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        resp_text = call_gemini(model=model, prompt=prompt, api_key=key)

    try:
        obj = try_parse_json(resp_text)
    except Exception:
        obj = {
            "center_name": args.center_name,
            "website_url": args.url,
            "error": "Model did not return valid JSON.",
            "raw": resp_text[:4000],
        }

    # Ensure center_name and website_url presence
    obj.setdefault("center_name", args.center_name)
    obj.setdefault("website_url", args.url)

    # Parse address components if address exists but components are missing
    if "error" not in obj:
        contact = obj.get("contact_info", {})
        address_components = obj.get("address_components", {})
        
        # If we have an address but no components, parse it
        if contact and contact.get("address") and not any(address_components.get(k) for k in ["postal_code", "postal_town", "admin_area_level_1", "admin_area_level_2"]):
            parsed = parse_uk_address(contact["address"])
            obj["address_components"] = parsed

    # Enhance with web search if enabled and contact info is missing
    if args.enhance_with_websearch and "error" not in obj:
        contact = obj.get("contact_info", {})
        if not contact:
            contact = {}
            obj["contact_info"] = contact
            
        missing_fields = []
        if not contact.get("phone"):
            missing_fields.append("phone")
        if not contact.get("email"):
            missing_fields.append("email")
        if not contact.get("address"):
            missing_fields.append("address")
        
        if missing_fields:
            print(f"Searching web for missing contact info: {', '.join(missing_fields)}...", file=sys.stderr)
            web_contact = search_web_for_contact(args.center_name, args.url)
            
            # Track what was enhanced
            enhanced_fields = []
            
            if not contact.get("phone") and web_contact.get("phone"):
                contact["phone"] = web_contact["phone"]
                enhanced_fields.append("phone")
            
            if not contact.get("email") and web_contact.get("email"):
                contact["email"] = web_contact["email"]
                enhanced_fields.append("email")
            
            if not contact.get("address") and web_contact.get("address"):
                contact["address"] = web_contact["address"]
                enhanced_fields.append("address")
                
                # Also add address components if available
                if web_contact.get("address_components"):
                    obj["address_components"] = web_contact["address_components"]
                    enhanced_fields.append("address_components")
            
            # Add metadata about enhancement
            if enhanced_fields:
                obj["_metadata"] = {
                    "enhanced_fields": enhanced_fields,
                    "enhancement_sources": web_contact.get("sources", []),
                    "enhancement_note": "Contact information enhanced via web search from reliable sources"
                }
                print(f"Enhanced fields: {', '.join(enhanced_fields)}", file=sys.stderr)
            else:
                print("No additional contact information found via web search.", file=sys.stderr)

    print(json.dumps(obj, indent=2, ensure_ascii=False))
    if args.out:
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()


