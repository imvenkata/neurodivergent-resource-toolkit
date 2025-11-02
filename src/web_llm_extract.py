import argparse
import gzip
import hashlib
import html
import json
import os
import random
import re
import ssl
import sys
import time
from pathlib import Path
# dataclass reserved for future structuring; avoid unused import for now
from typing import Dict, List, Optional, Set, Tuple
from urllib import request, parse
from urllib.error import HTTPError, URLError

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load .env from project root (parent of src directory)
    project_root = Path(__file__).parent.parent
    env_path = project_root / '.env'
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass  # python-dotenv not installed, will use system env vars

# Load cache directory from config if available
project_root = Path(__file__).parent.parent
try:
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    import config
    DEFAULT_CACHE_DIR = config.CACHE_DIR if hasattr(config, 'CACHE_DIR') else project_root / ".cache"
except ImportError:
    # Fallback if config.py not available
    DEFAULT_CACHE_DIR = project_root / ".cache"
    config = None


# Multiple User-Agent strings to rotate (avoid bot detection)
USER_AGENTS = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Chrome on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Safari on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]

def get_browser_headers(url: str = None) -> dict:
    """
    Generate realistic browser headers to avoid bot detection.
    Rotates User-Agent and includes common browser headers.
    """
    user_agent = random.choice(USER_AGENTS)
    
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.9,en-US;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }
    
    # Add Referer for non-initial requests (looks more natural)
    if url:
        parsed = parse.urlparse(url)
        if parsed.netloc:
            headers["Referer"] = f"{parsed.scheme}://{parsed.netloc}/"
    
    return headers


def get_root_url(url: str) -> str:
    """Extract root domain from URL (e.g., https://example.com/path -> https://example.com/)"""
    parsed = parse.urlparse(url)
    # Ensure www. is included if present, or add it if missing
    netloc = parsed.netloc
    if not netloc.startswith('www.'):
        # Try adding www. for fallback
        netloc_with_www = f"www.{netloc}"
    else:
        netloc_with_www = netloc
    
    root_url = f"{parsed.scheme}://{parsed.netloc}/"
    root_url_with_www = f"{parsed.scheme}://{netloc_with_www}/" if netloc_with_www != netloc else None
    
    return root_url, root_url_with_www


def decompress_response(resp) -> str:
    """Read and decompress HTTP response content, handling gzip/deflate/br encoding."""
    charset = resp.headers.get_content_charset() or "utf-8"
    raw_content = resp.read()
    
    # Decompress based on Content-Encoding header
    content_encoding = resp.headers.get('Content-Encoding', '').lower()
    
    if content_encoding == 'br':
        # Brotli compression
        try:
            import brotli
            content = brotli.decompress(raw_content).decode(charset, errors="ignore")
        except ImportError:
            # If brotli library not available, try to decode anyway (may fail)
            print("⚠️  Warning: Brotli compression detected but 'brotli' library not installed. Install with: pip install brotli", file=sys.stderr)
            content = raw_content.decode(charset, errors="ignore")
        except Exception:
            # If decompression fails, try decoding directly
            content = raw_content.decode(charset, errors="ignore")
    elif content_encoding == 'gzip':
        try:
            content = gzip.decompress(raw_content).decode(charset, errors="ignore")
        except Exception:
            # If decompression fails, try decoding directly
            content = raw_content.decode(charset, errors="ignore")
    elif content_encoding == 'deflate':
        try:
            import zlib
            content = zlib.decompress(raw_content).decode(charset, errors="ignore")
        except Exception:
            content = raw_content.decode(charset, errors="ignore")
    else:
        # Try to auto-detect compression by magic bytes
        if len(raw_content) >= 2:
            if raw_content[:2] == b'\x1f\x8b':
                # Gzip magic bytes
                try:
                    content = gzip.decompress(raw_content).decode(charset, errors="ignore")
                except Exception:
                    content = raw_content.decode(charset, errors="ignore")
            elif raw_content[:4] == b'\xce\xb2\xcf\x81' or content_encoding == '':
                # Try Brotli (no reliable magic bytes, but worth trying if Content-Encoding is missing)
                try:
                    import brotli
                    content = brotli.decompress(raw_content).decode(charset, errors="ignore")
                except (ImportError, Exception):
                    content = raw_content.decode(charset, errors="ignore")
            else:
                content = raw_content.decode(charset, errors="ignore")
        else:
            content = raw_content.decode(charset, errors="ignore")
    
    return content


# Content text caching functions (replaces HTML cache)
def get_content_cache_path(center_name: str, website_url: str, cache_dir: Optional[str] = None) -> Path:
    """Get cache file path for cleaned text content (one file per service center)."""
    # Use config CACHE_DIR if available, otherwise default
    if cache_dir is None:
        cache_dir = DEFAULT_CACHE_DIR / "content"
    else:
        # If relative path provided, resolve from cache directory
        cache_path = Path(cache_dir)
        if not cache_path.is_absolute():
            # If relative, resolve from CACHE_DIR
            cache_dir = DEFAULT_CACHE_DIR / cache_dir
    
    cache_base = Path(cache_dir)
    cache_base.mkdir(parents=True, exist_ok=True)
    
    # Create a safe filename from center name and URL hash
    cache_key = f"{center_name}_{website_url}".encode('utf-8')
    cache_hash = hashlib.md5(cache_key).hexdigest()
    name_safe = re.sub(r'[^\w\-_.]', '_', center_name)[:100]
    cache_file = cache_base / f"{name_safe}_{cache_hash}.json"
    
    return cache_file


def load_content_from_cache(center_name: str, website_url: str, cache_dir: Optional[str] = None, max_age_days: int = 30) -> Optional[Dict[str, str]]:
    """
    Load cleaned text content from cache if it exists and is not expired.
    
    Returns:
        Dict with 'website_text' and 'web_search_text' if cached and fresh, None otherwise
    """
    if cache_dir is False:  # Explicitly disabled
        return None
        
    cache_file = get_content_cache_path(center_name, website_url, cache_dir)
    
    if not cache_file.exists():
        return None
    
    # Check if cache is expired
    if max_age_days > 0:
        file_age = time.time() - cache_file.stat().st_mtime
        if file_age > (max_age_days * 24 * 60 * 60):
            return None  # Cache expired
    
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            cached_data = json.load(f)
            # Verify it's for the same center and URL
            if (cached_data.get("center_name") == center_name and 
                cached_data.get("website_url") == website_url):
                return {
                    "website_text": cached_data.get("website_text", ""),
                    "web_search_text": cached_data.get("web_search_text", ""),
                    "website_pages": cached_data.get("website_pages", []),
                    "web_search_sources": cached_data.get("web_search_sources", [])
                }
    except (OSError, json.JSONDecodeError, KeyError):
        # Cache file corrupted, ignore it
        pass
    
    return None


def save_content_to_cache(
    center_name: str,
    website_url: str,
    website_text: str,
    website_pages: List[str],
    web_search_text: str = "",
    web_search_sources: List[str] = None,
    cache_dir: Optional[str] = None
) -> None:
    """Save cleaned text content to cache (replaces HTML cache)."""
    if cache_dir is False:  # Explicitly disabled
        return
        
    cache_file = get_content_cache_path(center_name, website_url, cache_dir)
    
    try:
        cache_data = {
            "center_name": center_name,
            "website_url": website_url,
            "website_text": website_text,
            "website_pages": website_pages,
            "web_search_text": web_search_text,
            "web_search_sources": web_search_sources or [],
            "cached_at": time.time(),
            "cached_at_readable": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
    except OSError:
        # Ignore cache write errors (disk full, permissions, etc.)
        pass


# HTML caching functions (DISABLED - HTML cache saving removed)
# Functions kept for backward compatibility with existing HTML cache files (read-only)
# We now only save processed/cleaned text to content cache, not raw HTML
def get_html_cache_path(url: str, cache_dir: Optional[str] = None) -> Path:
    """Get cache file path for a URL (DISABLED - no longer saving HTML cache)."""
    if cache_dir is None:
        cache_dir = DEFAULT_CACHE_DIR / "html_content"
    else:
        cache_path = Path(cache_dir)
        if not cache_path.is_absolute():
            cache_dir = DEFAULT_CACHE_DIR / cache_dir
    
    cache_base = Path(cache_dir)
    cache_base.mkdir(parents=True, exist_ok=True)
    
    # Create a safe filename from URL using hash
    url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
    # Also include first part of domain for easier debugging
    parsed = parse.urlparse(url)
    domain_safe = re.sub(r'[^\w\-_.]', '_', parsed.netloc or 'unknown')[:50]
    cache_file = cache_base / f"{domain_safe}_{url_hash}.html"
    
    return cache_file


def load_html_from_cache(url: str, cache_dir: Optional[str] = None, max_age_days: int = 30) -> Optional[str]:
    """
    Load HTML content from cache if it exists and is not expired.
    
    Returns:
        HTML content if cached and fresh, None otherwise
    """
    if cache_dir is False:  # Explicitly disabled
        return None
        
    cache_file = get_html_cache_path(url, cache_dir)
    
    if not cache_file.exists():
        return None
    
    # Check if cache is expired
    if max_age_days > 0:
        file_age = time.time() - cache_file.stat().st_mtime
        if file_age > (max_age_days * 24 * 60 * 60):
            return None  # Cache expired
    
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            cached_data = json.load(f)
            # Verify it's for the same URL (in case of hash collision)
            if cached_data.get("url") == url:
                return cached_data.get("content")
    except (OSError, json.JSONDecodeError, KeyError):
        # Cache file corrupted, ignore it
        pass
    
    return None


def save_html_to_cache(url: str, content: str, cache_dir: Optional[str] = None) -> None:
    """Save HTML content to cache (DISABLED - we now only save processed text)."""
    # HTML caching is disabled - we only save processed/cleaned text to content cache
    # This function is kept for backward compatibility but does nothing
    pass


def fetch_url(url: str, timeout: int = 20, html_cache_dir: Optional[str] = None, refresh_html_cache: bool = False) -> Optional[Tuple[str, str]]:
    """
    Fetch URL with comprehensive error handling and fallback strategies.
    
    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        html_cache_dir: Directory to cache HTML content (None to disable, False to explicitly disable)
        refresh_html_cache: If True, skip cache and fetch fresh content
    
    Returns:
        Tuple of (content, working_url) if successful, None if all strategies fail
        The working_url is the URL that actually worked (may differ from input)
    
    Fallback strategy:
    1. Add protocol if missing (https://)
    2. Try HTTPS with SSL verification
    3. If SSL error → Try HTTPS without verification
    4. If still fails → Try HTTP
    5. If still fails → Try root domain
    6. If still fails → Try root domain with www.
    """
    # Fix URLs missing protocol (e.g., "www.example.com" → "https://www.example.com")
    if url and not url.startswith(('http://', 'https://')):
        url = f'https://{url}'
    
    # HTML cache loading disabled - we only use processed text cache now
    # Keeping this commented out for backward compatibility with existing HTML cache
    # if not refresh_html_cache and html_cache_dir is not False:
    #     cached_content = load_html_from_cache(url, html_cache_dir)
    #     if cached_content:
    #         return (cached_content, url)
    
    # Add small random delay to avoid rate limiting (0.1-0.5 seconds)
    time.sleep(random.uniform(0.1, 0.5))
    
    # Strategy 1: Try HTTPS with normal SSL verification
    headers = get_browser_headers(url)
    req = request.Request(url, headers=headers)
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            content = decompress_response(resp)
            # HTML cache removed - we only save processed text to content cache
            return (content, url)
    except ssl.SSLError:
        # Strategy 2: Try HTTPS without SSL verification (many small charity sites have SSL issues)
        try:
            context = ssl._create_unverified_context()
            with request.urlopen(req, timeout=timeout, context=context) as resp:
                content = decompress_response(resp)
                # HTML cache removed - we only save processed text to content cache
                return (content, url)
        except Exception:
            pass
    except (request.URLError, TimeoutError, ValueError):
        pass
    
    # Strategy 3: Try HTTP instead of HTTPS
    if url.startswith('https://'):
        http_url = url.replace('https://', 'http://')
        try:
            req_http = request.Request(http_url, headers=get_browser_headers(http_url))
            with request.urlopen(req_http, timeout=timeout) as resp:
                content = decompress_response(resp)
                # HTML cache removed - we only save processed text to content cache
                return (content, http_url)
        except Exception:
            pass
    
    # Strategy 4: Try root domain as fallback
    root_url, root_url_with_www = get_root_url(url)
    
    # Don't retry root if we're already at root
    if url.rstrip('/') != root_url.rstrip('/'):
        # Try root URL with HTTPS
        try:
            req_root = request.Request(root_url, headers=get_browser_headers(root_url))
            try:
                with request.urlopen(req_root, timeout=timeout) as resp:
                    content = decompress_response(resp)
                    # HTML cache removed - we only save processed text to content cache
                    return (content, root_url)
            except ssl.SSLError:
                # Try root without SSL verification
                context = ssl._create_unverified_context()
                with request.urlopen(req_root, timeout=timeout, context=context) as resp:
                    content = decompress_response(resp)
                    # HTML cache removed - we only save processed text to content cache
                    return (content, root_url)
        except Exception:
            pass
        
        # Try root URL with HTTP
        if root_url.startswith('https://'):
            http_root = root_url.replace('https://', 'http://')
            try:
                req_http_root = request.Request(http_root, headers=get_browser_headers(http_root))
                with request.urlopen(req_http_root, timeout=timeout) as resp:
                    content = decompress_response(resp)
                    # HTML cache removed - we only save processed text to content cache
                    return (content, http_root)
            except Exception:
                pass
        
        # Strategy 5: Try with www. prefix if different
        if root_url_with_www and root_url_with_www != root_url:
            try:
                req_www = request.Request(root_url_with_www, headers=get_browser_headers(root_url_with_www))
                try:
                    with request.urlopen(req_www, timeout=timeout) as resp:
                        content = decompress_response(resp)
                        # HTML cache removed - we only save processed text to content cache
                        return (content, root_url_with_www)
                except ssl.SSLError:
                    # Try www without SSL verification
                    context = ssl._create_unverified_context()
                    with request.urlopen(req_www, timeout=timeout, context=context) as resp:
                        content = decompress_response(resp)
                        # HTML cache removed - we only save processed text to content cache
                        return (content, root_url_with_www)
            except Exception:
                pass
            
            # Try www with HTTP
            if root_url_with_www.startswith('https://'):
                http_www = root_url_with_www.replace('https://', 'http://')
                try:
                    req_http_www = request.Request(http_www, headers=get_browser_headers(http_www))
                    with request.urlopen(req_http_www, timeout=timeout) as resp:
                        content = decompress_response(resp)
                        # HTML cache removed - we only save processed text to content cache
                        return (content, http_www)
                except Exception:
                    pass
    
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


def crawl_site(
    start_url: str, 
    max_pages: int = 6, 
    html_cache_dir: Optional[str] = None, 
    refresh_html_cache: bool = False,
    center_name: Optional[str] = None,
    content_cache_dir: Optional[str] = None,
    refresh_content_cache: bool = False
) -> Tuple[List[Tuple[str, str]], str]:
    """
    Crawl website starting from start_url.
    If start_url fails, automatically falls back to root domain (handled by fetch_url).
    
    Args:
        start_url: Starting URL to crawl
        max_pages: Maximum number of pages to crawl
        html_cache_dir: Directory to cache HTML content (None to disable)
        refresh_html_cache: If True, skip cache and fetch fresh content
    
    Returns:
        Tuple of (collected_pages, working_url)
        - collected_pages: List of (url, html_content) tuples
        - working_url: The URL that actually worked (may differ from start_url)
    """
    visited: Set[str] = set()
    queue: List[str] = [start_url]
    collected: List[Tuple[str, str]] = []
    working_url = start_url  # Track the URL that actually works
    
    # Try to fetch the starting URL (fetch_url will handle fallback to root)
    result = fetch_url(start_url, html_cache_dir=html_cache_dir, refresh_html_cache=refresh_html_cache)
    if not result:
        # If even root domain fails, try explicit root URL fallback
        root_url, root_url_with_www = get_root_url(start_url)
        result = fetch_url(root_url, html_cache_dir=html_cache_dir, refresh_html_cache=refresh_html_cache)
        if result:
            # Use root URL as starting point instead
            start_url = root_url
            print(f"⚠️  Original URL failed, using root domain: {root_url}")
        elif root_url_with_www:
            result = fetch_url(root_url_with_www, html_cache_dir=html_cache_dir, refresh_html_cache=refresh_html_cache)
            if result:
                start_url = root_url_with_www
                print(f"⚠️  Original URL failed, using www domain: {root_url_with_www}")
    
    if result:
        initial_html, actual_working_url = result
        working_url = actual_working_url  # Save the URL that actually worked
        visited.add(start_url)
        collected.append((start_url, initial_html))
        # Extract and queue links from the starting page
        links = [lnk for lnk in extract_links(start_url, initial_html) if same_site(lnk, start_url)]
        links = sorted(set(links), key=lambda u: -rank_link(u))
        queue.extend([l for l in links if l not in visited])
    
    # Continue crawling additional pages
    while queue and len(collected) < max_pages:
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)
        if not same_site(url, start_url):
            continue
        result = fetch_url(url, html_cache_dir=html_cache_dir, refresh_html_cache=refresh_html_cache)
        if not result:
            continue
        html_doc, _ = result  # Unpack tuple
        collected.append((url, html_doc))
        links = [lnk for lnk in extract_links(url, html_doc) if same_site(lnk, start_url)]
        links = sorted(set(links), key=lambda u: -rank_link(u))
        for l in links:
            if l not in visited and l not in queue:
                queue.append(l)
    
    # Save cleaned text to content cache (replaces HTML cache)
    if center_name and content_cache_dir is not False and not refresh_content_cache:
        # Check if we should use cached content
        cached_content = load_content_from_cache(center_name, working_url, content_cache_dir)
        if cached_content and cached_content.get("website_text"):
            # Return cached pages structure (we still need to return pages for build_prompt)
            # But we'll use the cached text later in build_prompt
            pass
    
    # Process and save website text
    if center_name and content_cache_dir is not False:
        website_text_parts = []
        website_pages_list = []
        for url, html_content in collected:
            cleaned_text = html_to_text(html_content)
            if cleaned_text.strip():
                # Format: URL marker before text (so we know which page we're reading)
                website_text_parts.append(f"\n\n=== PAGE: {url} ===\n\n{cleaned_text}")
                website_pages_list.append(url)
        
        combined_website_text = "\n".join(website_text_parts)
        
        # Load existing web_search_text if any (to preserve it when updating website text only)
        existing_content = load_content_from_cache(center_name, working_url, content_cache_dir)
        web_search_text = existing_content.get("web_search_text", "") if existing_content else ""
        web_search_sources = existing_content.get("web_search_sources", []) if existing_content else []
        
        # Always save content cache (even if empty) so we know the crawl happened
        # This helps debug when websites can't be fetched
        try:
            save_content_to_cache(
                center_name=center_name,
                website_url=working_url,
                website_text=combined_website_text,
                website_pages=website_pages_list,
                web_search_text=web_search_text,
                web_search_sources=web_search_sources,
                cache_dir=content_cache_dir
            )
        except Exception as e:
            # Log cache errors but don't fail the extraction
            print(f"⚠️  Failed to save content cache for {center_name}: {str(e)[:100]}", file=sys.stderr)
    
    return (collected, working_url)


def build_prompt(
    center_name: str, 
    website_url: str, 
    docs: List[Tuple[str, str]],
    content_cache_dir: Optional[str] = None,
    use_content_cache: bool = True
) -> str:
    # Try to use cached cleaned text first
    body = None
    if use_content_cache and content_cache_dir is not False:
        cached_content = load_content_from_cache(center_name, website_url, content_cache_dir)
        if cached_content and cached_content.get("website_text"):
            # Use cached cleaned text (already has page separators)
            body = cached_content["website_text"]
            # Limit length if needed
            if len(body) > 50000:  # Limit total length
                # Split by page markers and take first N pages
                pages = body.split("\n=== PAGE:")
                body = "\n=== PAGE:".join(pages[:8])
    
    # Fallback: process HTML on the fly (if cache not available)
    if body is None:
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
        "• Use empty string \"\" for missing text fields (NOT \"Not specified\"), [] for missing arrays, null for missing values\n"
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
        "• conditions_supported: List ONLY PRIMARY neurodivergent conditions (max 10-12)\n"
        "  - Include: Autism/ASC, ADHD, Dyslexia, Dyspraxia, Tourette's, Learning disabilities, Intellectual disabilities\n"
        "  - Include: Co-occurring mental health ONLY if explicitly ND-related (e.g., \"Anxiety in autism\")\n"
        "  - EXCLUDE: Generic conditions like \"Stress\", \"Anger management\", \"Bereavement\" (not ND-specific)\n"
        "  - EXCLUDE: Common mental health conditions unless ND-specific (e.g., \"Depression\" alone → exclude)\n"
        "  - EXCLUDE: Substance abuse/addictions unless specified for ND population\n"
        "  - EXCLUDE: General terms like \"Mental health\" or \"Emotional support\" (too broad)\n"
        "  - EXCLUDE: Symptoms (e.g., \"Panic attacks\", \"Self-harm\") - not conditions\n"
        "  - EXCLUDE: Rare conditions unless this is a specialist service for that condition\n"
        "  - PRIORITIZE: Conditions explicitly stated in service descriptions or primary focus areas\n"
        "• specific_services: List ONLY high-importance service categories (max 10-12), GROUP similar services\n"
        "  - GROUP similar therapies: \"Therapy (individual, group, couples, family)\" NOT separate items\n"
        "  - GROUP assessment types: \"Diagnostic assessments (autism, ADHD)\" NOT separate items\n"
        "  - GROUP treatment delivery: \"Treatment (inpatient, outpatient, day care)\" NOT separate items\n"
        "  - INCLUDE: Core services only (assessments, therapy types, support programs)\n"
        "  - INCLUDE: Specialized services unique to this provider\n"
        "  - EXCLUDE: Generic activities (e.g., \"Yoga\", \"Gym facilities\", \"Movie nights\") unless ND-specific\n"
        "  - EXCLUDE: Administrative services (e.g., \"Referral services\", \"Payment plans\")\n"
        "  - EXCLUDE: Supportive activities unless explicitly ND-focused (e.g., \"Recreational activities\")\n"
        "  - PRIORITIZE: Services explicitly mentioned as primary offerings\n"
        "• organization_type: NHS Service, Charity/Non-profit, Local Authority, Private School, Private Provider, Social Enterprise, or Unknown\n"
        "• contact_info: Extract phone, email, full address if available. Use empty string \"\" if not found (NOT \"Not specified\")\n"
        "• address_components: Break down address into postal_code, postal_town, admin_area_level_1 (country/region), admin_area_level_2 (county/area)\n"
        "• additional_notes: Note any funding, accessibility, referral requirements, payment plans\n"
        "• data_confidence: High (clear info), Medium (some ambiguity), or Low (limited info)\n"
        "• reasoning: Brief explanation of your categorization choice\n\n"
        "NEURODIVERGENT RELEVANCE CHECK (CRITICAL - READ CAREFULLY):\n\n"
        "GOAL: This directory helps neurodivergent people and their families find support.\n"
        "ASK YOURSELF: Would a neurodivergent person or their family find this resource valuable?\n\n"
        "• neurodivergent_relevance_score: High/Medium/Low/None\n\n"
        "  HIGH = PRIMARY neurodivergent service (people seek this OUT for ND support)\n"
        "    ✓ Name contains ND keywords: autism, ADHD, dyslexia, neurodivergent\n"
        "    ✓ Primary purpose: ND diagnosis, ND-specific therapy, ND education\n"
        "    ✓ Specialist ND schools, clinics, assessment centers\n"
        "    ✓ ND advocacy organizations (NAS, ADHD Foundation)\n"
        "    Examples: \"ADHD Assessment Clinic\", \"Autism Specialist School\", \"Dyslexia Tutoring\", \"National Autistic Society\"\n\n"
        "  MEDIUM = SIGNIFICANTLY HELPS neurodivergent people (valuable in ND directory)\n"
        "    ✓ SEND/SEN services (Special Educational Needs includes autism, ADHD, dyslexia)\n"
        "      REQUIRED: Must PROVIDE DIRECT SEND/SEN services or programs, not just INFORMATION\n"
        "      ✗ Administrative/informational services (school search, admissions info) → LOW, not MEDIUM\n"
        "      ✗ General websites that list schools (including special schools) → LOW\n"
        "      ✓ Actual SEND schools, SEND support programs, SEND therapy → MEDIUM\n"
        "    ✓ Autism-friendly or sensory-friendly activities\n"
        "      REQUIRED: Must EXPLICITLY state \"autism-friendly\", \"sensory-friendly\", or \"neurodivergent-friendly\"\n"
        "    ✓ Mental health services (70% of autistic people have mental health conditions)\n"
        "      REQUIRED: Must be mental health counseling, therapy, or crisis services (not just general wellness)\n"
        "      ✓ Crisis helplines (Samaritans, etc.) → MEDIUM (critical for ND mental health)\n"
        "    ✓ Crisis support services (ND people have higher rates of mental health crisis)\n"
        "      REQUIRED: Must be dedicated crisis helplines or emergency mental health support\n"
        "    ✓ Parent/carer support groups (for families of ND children)\n"
        "      REQUIRED: Must EXPLICITLY mention SEND, disability, or neurodivergent families\n"
        "    ✓ Therapeutic services: OT, speech therapy, music therapy, art therapy\n"
        "      REQUIRED: Must be PROFESSIONAL therapeutic services (OT, speech therapy, physio), not general activities\n"
        "      ⚠️  Generic farms, parks, or recreational facilities that mention \"therapeutic\" are NOT therapeutic services\n"
        "    ✓ Disability charities: RDA, special needs playgrounds, adaptive sports\n"
        "      REQUIRED: Must EXPLICITLY serve disabled/SEND individuals or have dedicated facilities\n"
        "    ✓ Social skills groups, life skills training\n"
        "      REQUIRED: Must EXPLICITLY mention social skills, life skills, or independence programs\n"
        "    ✓ Employment support for people with disabilities\n"
        "      REQUIRED: Must EXPLICITLY mention disability employment or supported employment\n"
        "    ✓ Benefits advice, housing support for disabled/SEND\n"
        "      REQUIRED: Must PROVIDE direct support services, not just information/links\n"
        "      ✗ Administrative offices providing general information → LOW\n"
        "    Examples: \"SEND swimming\", \"Mental health counseling\", \"Samaritans crisis line\", \n"
        "              \"Parent Carer Forum\", \"RDA riding center\", \"Autism-friendly cinema\", \n"
        "              \"Occupational therapy\", \"Social skills group\"\n\n"
        "  LOW = Generic service, not ND-specific\n"
        "    ✗ General services that ND people might use (but so does everyone)\n"
        "    ✗ Has accessibility features but not ND-specific\n"
        "    ✗ No dedicated ND programs or staff\n"
        "    ✗ Mentions vague \"therapeutic benefits\" but no explicit ND programs\n"
        "    ✗ Educational/recreational facilities without SEND/autism-friendly programs\n"
        "    ✗ Administrative/informational services that mention SEND but don't provide direct support\n"
        "      ⚠️  School search tools, admissions info, general SEND information pages → LOW\n"
        "      ⚠️  Council services that list/link to SEND resources but don't provide them → LOW\n"
        "    Examples: \"Council SEND office\", \"Schools Office (information/admissions)\", \n"
        "              \"General hospital\", \"Library with quiet space\",\n"
        "              \"City farm (general)\", \"Community park\", \"General youth center\"\n\n"
        "  NONE = Completely irrelevant to ND needs\n"
        "    ✗ No connection to neurodivergent conditions\n"
        "    ✗ Not a service ND individuals specifically need\n"
        "    ✗ General public services or commercial businesses\n"
        "    Examples: \"Transport for London\", \"Generic sports club\", \"Museum\", \"Pharmacy\",\n"
        "              \"General city farm\", \"Tourist attraction\", \"Restaurant\"\n\n"
        "• is_neurodivergent_related: true/false\n"
        "  - true ONLY IF: High or Medium score\n"
        "  - false IF: Low or None score\n\n"
        "• neurodivergent_focus: Brief explanation\n"
        "  - If true: What specific ND conditions/services?\n"
        "  - If false: Why is it not ND-specific?\n\n"
        "IMPORTANT DISTINCTIONS:\n"
        "❌ WRONG: \"Has wheelchair access\" → ND-relevant (NO! That's general accessibility)\n"
        "✓ RIGHT: \"Has autism-trained staff\" → ND-relevant (YES! That's ND-specific)\n\n"
        "❌ WRONG: \"Offers mental health support\" → ND-relevant (Too broad - everyone needs mental health)\n"
        "✓ RIGHT: \"Offers ADHD-specific therapy\" → ND-relevant (YES! That's ND-specific)\n\n"
        "CONCRETE EXAMPLES:\n\n"
        "Example 1: \"National Autistic Society\"\n"
        "  ✓ Name has 'Autistic' → HIGH\n"
        "  ✓ is_neurodivergent_related: true\n"
        "  ✓ conditions_supported: [\"Autism/ASC\"]\n"
        "  ✓ neurodivergent_focus: \"Charity specializing in autism support, education, and advocacy\"\n\n"
        "Example 2: \"London ADHD Clinic\"\n"
        "  ✓ Name has 'ADHD' → HIGH\n"
        "  ✓ is_neurodivergent_related: true\n"
        "  ✓ conditions_supported: [\"ADHD\"]\n"
        "  ✓ neurodivergent_focus: \"Specialist clinic for ADHD assessment and treatment\"\n\n"
        "Example 3: \"Mental Health Counseling Service (anxiety, depression, trauma)\"\n"
        "  ✓ Mental health services help ND people significantly → MEDIUM\n"
        "  ✓ is_neurodivergent_related: true\n"
        "  ✓ conditions_supported: [\"Co-occurring mental health (anxiety, depression common in ND)\"]\n"
        "  ✓ neurodivergent_focus: \"Mental health counseling for anxiety and depression. Highly relevant as 70% of autistic people and 50% of ADHD adults have co-occurring mental health conditions.\"\n\n"
        "Example 3b: \"Samaritans Crisis Helpline\"\n"
        "  ✓ Crisis support critical for ND community → MEDIUM\n"
        "  ✓ is_neurodivergent_related: true\n"
        "  ✓ conditions_supported: [\"Mental health crisis (ND people have 9x higher suicide risk)\"]\n"
        "  ✓ neurodivergent_focus: \"24/7 emotional support and crisis intervention. Critical resource as autistic people have 9x higher suicide rates and ADHD 5x higher suicide attempts.\"\n\n"
        "Example 3c: \"Parent Carer Forum for SEND Families\"\n"
        "  ✓ Supports families of ND children → MEDIUM\n"
        "  ✓ is_neurodivergent_related: true\n"
        "  ✓ conditions_supported: [\"SEND (includes autism, ADHD, dyslexia)\"]\n"
        "  ✓ neurodivergent_focus: \"Support network for parents and carers of children with Special Educational Needs, which includes neurodivergent conditions.\"\n\n"
        "Example 4: \"Transport for London (TfL)\"\n"
        "  ✗ General public transport → NONE\n"
        "  ✗ is_neurodivergent_related: false\n"
        "  ✗ conditions_supported: []\n"
        "  ✗ neurodivergent_focus: \"General transport service. Has accessibility features but not ND-specific.\"\n\n"
        "Example 5: \"Southwark Council\" or \"Hammersmith and Fulham Council\"\n"
        "  ✗ General local authority → NONE (not LOW!)\n"
        "  ✗ is_neurodivergent_related: false\n"
        "  ✗ conditions_supported: [] (even if mentions 'Disabilities' or 'Learning Disabilities' - too generic)\n"
        "  ✗ neurodivergent_focus: \"General council providing public services. Even if mentions disability support, \n"
        "      this is a general public service used by everyone, not a neurodivergent-specific resource. \n"
        "      Generic terms like 'disabilities' or 'learning disabilities' do not qualify as ND-specific.\"\n\n"
        "Example 5b: \"Tower Hamlets Schools Office\" or similar administrative/informational services\n"
        "  ✗ Provides INFORMATION about schools (including special schools) → LOW (not MEDIUM!)\n"
        "  ✗ Administrative service (school search, admissions, term dates) → LOW\n"
        "  ✗ Mentions SEND but only provides links/information, not direct services → LOW\n"
        "  ✗ is_neurodivergent_related: false (or true if has search for SEND schools, but still LOW score)\n"
        "  ✗ conditions_supported: [\"SEND\"] (information service, not direct support)\n"
        "  ✗ neurodivergent_focus: \"Administrative office providing school information and search tools. \n"
        "      While it includes special schools in search results, this is an informational service, \n"
        "      not a direct neurodivergent support resource. Families use it to find schools, \n"
        "      but it doesn't provide therapy, support groups, or ND-specific services.\"\n\n"
        "Example 5c: \"Actual SEND School\" or \"SEND Support Service\"\n"
        "  ✓ Provides DIRECT SEND education or support → MEDIUM\n"
        "  ✓ is_neurodivergent_related: true\n"
        "  ✓ conditions_supported: [\"SEND\", \"Autism\", \"ADHD\"]\n"
        "  ✓ neurodivergent_focus: \"Specialist school providing education for children with SEND needs.\"\n\n"
        "Example 6: \"General Hospital\"\n"
        "  ✗ No ND specialty → NONE\n"
        "  ✗ is_neurodivergent_related: false\n"
        "  ✗ conditions_supported: []\n"
        "  ✗ neurodivergent_focus: \"General healthcare. Not neurodivergent-specific unless has ND clinic.\"\n\n"
        "Example 7: \"SEND Swimming Lessons / Hydrotherapy for Disabled Children\"\n"
        "  ✓ Explicitly serves SEND/SEN population → MEDIUM\n"
        "  ✓ is_neurodivergent_related: true\n"
        "  ✓ conditions_supported: [\"SEND/SEN (includes autism, ADHD)\"]\n"
        "  ✓ neurodivergent_focus: \"Swimming lessons specifically for children with Special Educational Needs (SEND), which includes neurodivergent conditions.\"\n\n"
        "Example 8: \"Country Park with SEND Pavilion / Special Needs Playground\"\n"
        "  ✓ Has dedicated SEND facilities → MEDIUM\n"
        "  ✓ is_neurodivergent_related: true\n"
        "  ✓ conditions_supported: [\"SEND/SEN (includes autism, ADHD)\"]\n"
        "  ✓ neurodivergent_focus: \"Recreation facility with specialist playground and pavilion designed for children with special educational needs.\"\n\n"
        "Example 9: \"RDA Riding Center / Therapeutic Horse Riding for Disabled\"\n"
        "  ✓ Disability charity serving ND individuals → MEDIUM\n"
        "  ✓ is_neurodivergent_related: true\n"
        "  ✓ conditions_supported: [\"Autism\", \"ADHD\", \"Learning disabilities\"]\n"
        "  ✓ neurodivergent_focus: \"Riding for the Disabled Association center providing therapeutic equine activities for disabled individuals, including those with autism and ADHD.\"\n\n"
        "Example 10: \"Farm with Autism-Friendly Sessions\"\n"
        "  ✓ Offers autism-friendly programs → MEDIUM\n"
        "  ✓ is_neurodivergent_related: true\n"
        "  ✓ conditions_supported: [\"Autism/ASC\"]\n"
        "  ✓ neurodivergent_focus: \"Farm offering sensory-friendly and autism-friendly visiting sessions specifically designed for neurodivergent children.\"\n\n"
        "Example 10b: \"City Farm (General Educational Farm)\"\n"
        "  ✗ General educational farm, mentions \"therapeutic\" but no explicit ND programs → LOW\n"
        "  ✗ is_neurodivergent_related: false\n"
        "  ✗ conditions_supported: []\n"
        "  ✗ neurodivergent_focus: \"General city farm offering educational workshops and animal experiences. While activities may have therapeutic benefits, there are no explicit programs for neurodivergent individuals, no autism-friendly sessions, and no mention of SEND/SEN support.\"\n\n"
        "Example 11: \"Occupational Therapy Service (pediatric, general)\"\n"
        "  ✓ Therapeutic service commonly used by ND individuals → MEDIUM\n"
        "  ✓ is_neurodivergent_related: true\n"
        "  ✓ conditions_supported: [\"Commonly used by autistic children for sensory processing, motor skills\"]\n"
        "  ✓ neurodivergent_focus: \"Occupational therapy services. Frequently used by autistic and ADHD individuals for sensory processing, motor skills, and daily living skills development.\"\n\n"
        "Example 12: \"Speech and Language Therapy Clinic\"\n"
        "  ✓ Therapeutic service commonly used by ND individuals → MEDIUM\n"
        "  ✓ is_neurodivergent_related: true\n"
        "  ✓ conditions_supported: [\"Commonly used by autistic children for communication development\"]\n"
        "  ✓ neurodivergent_focus: \"Speech and language therapy. Frequently accessed by autistic children and those with developmental language disorders.\"\n\n"
        "Example 13: \"General Museum with occasional 'quiet hours'\"\n"
        "  ✗ Primary purpose is museum, not ND support → LOW\n"
        "  ✗ is_neurodivergent_related: false\n"
        "  ✗ conditions_supported: []\n"
        "  ✗ neurodivergent_focus: \"Museum with occasional quiet sessions, but not ND-specific organization. Primary purpose is general tourism.\"\n\n"
        "Example 14: \"Southwark Council (General)\"\n"
        "  ✗ General local authority → NONE\n"
        "  ✗ is_neurodivergent_related: false\n"
        "  ✗ conditions_supported: []\n"
        "  ✗ neurodivergent_focus: \"General council services. May have SEND department but not an ND-specific resource.\"\n\n"
        "IMPORTANT RECOGNITION PATTERNS (Services That HELP Neurodivergent People):\n\n"
        "ALWAYS MEDIUM (or Higher):\n"
        "• SEND/SEN services (Special Educational Needs = includes autism, ADHD, dyslexia)\n"
        "• \"Autism-friendly\", \"Sensory-friendly\", \"Neurodivergent-friendly\" sessions/venues\n"
        "• Mental health services (anxiety, depression, trauma counseling)\n"
        "• Crisis support (helplines, suicide prevention, emotional support)\n"
        "• Parent/carer support groups (for families of disabled/SEND children)\n"
        "• Therapeutic services: OT, speech therapy, hydrotherapy, music/art therapy\n"
        "• RDA (Riding for Disabled) and similar disability charities\n"
        "• Social skills groups, life skills training, independence programs\n"
        "• Disability employment services (job coaching, supported employment)\n"
        "• Special needs playgrounds, sensory rooms, adaptive sports facilities\n"
        "• Benefits advice, housing support for disabled/SEND individuals\n"
        "• Respite care, short breaks for disabled children\n\n"
        "ALWAYS LOW or NONE:\n"
        "• General public services everyone uses: Transport (TfL), councils, general hospitals\n"
        "  ⚠️  CRITICAL: Local councils/authorities are ALWAYS NONE even if they mention:\n"
        "     - \"Disabilities\" or \"Learning Disabilities\" (too generic)\n"
        "     - General disability support (everyone uses this)\n"
        "     - Benefits advice for disabled (general service, not ND-specific)\n"
        "     - Only exception: Council-run autism/ADHD assessment centers with specific ND name\n"
        "• Pharmacies, dentists, opticians (unless ND-specialist)\n"
        "• Museums, theatres with only passive \"quiet hours\" (not active ND programs)\n"
        "• Generic gyms, sports clubs (no adaptive programs)\n"
        "• Schools without SEN provision\n"
        "• Administrative offices (council SEND offices that don't provide direct support)\n"
        "• General farms, city farms, parks without explicit SEND/autism-friendly programs\n"
        "• Educational centers/farms that mention \"therapeutic\" but have no ND-specific services\n"
        "• Youth centers, community centers without SEND programs\n"
        "• General recreational facilities (swimming pools, play centers) without special needs provision\n\n"
        "CRITICAL VALIDATION CHECKLIST (MUST FOLLOW IN ORDER):\n\n"
        "STEP 1: Check for EXPLICIT neurodivergent mentions\n"
        "  ✓ Does the name contain: autism, ADHD, dyslexia, neurodivergent, SEND, SEN?\n"
        "  ✓ Do services EXPLICITLY mention: \"SEND\", \"autism-friendly\", \"sensory-friendly\", \"for disabled\", \"special needs\"?\n"
        "  ✓ Are there EXPLICIT programs like \"autism-friendly sessions\", \"SEND swimming\", \"disability riding\"?\n"
        "  → If YES to any → Continue to Step 2\n"
        "  → If NO to all → SKIP to Step 5 (likely LOW/NONE)\n\n"
        "STEP 2: Check conditions_supported\n"
        "  ✓ Is conditions_supported populated with specific conditions?\n"
        "  → If EMPTY and no explicit ND keywords found → MUST be LOW or NONE\n"
        "  → If populated → Continue to Step 3\n\n"
        "STEP 3: Determine score level\n"
        "  • Name has ND keywords → HIGH\n"
        "  • Explicit SEND/SEN programs → MEDIUM (but check if it's direct service or just info)\n"
        "    ⚠️  SEND school search/information → LOW (administrative, not direct service)\n"
        "    ✓ Actual SEND schools, SEND therapy, SEND support groups → MEDIUM\n"
        "  • Explicit autism-friendly/sensory-friendly → MEDIUM\n"
        "  • Professional therapeutic services (OT, speech) → MEDIUM\n"
        "  • Mental health/crisis services → MEDIUM\n"
        "  • Parent/carer support for SEND families → MEDIUM\n\n"
        "STEP 4: Validate against false positives\n"
        "  ✗ Vague \"therapeutic benefits\" without explicit ND programs → LOW\n"
        "  ✗ General farms/parks/recreation without SEND programs → LOW/NONE\n"
        "  ✗ Educational services without SEN provision → LOW\n"
        "  ✗ Generic accessibility features (wheelchair access) → NOT enough for Medium\n"
        "  ✗ Administrative/informational services (school search, admissions info) → LOW\n"
        "  ✗ Services that only PROVIDE INFORMATION about SEND but not direct support → LOW\n\n"
        "STEP 5: Final scoring for generic services\n"
        "  • Generic public services (transport, councils, hospitals) → NONE\n"
        "    ⚠️  Councils are ALWAYS NONE even if they mention generic 'disabilities' support\n"
        "  • General recreational/educational (farms, parks, museums) → LOW\n"
        "  • Commercial businesses → NONE\n\n"
        "STRICT RULES:\n"
        "1. If conditions_supported is EMPTY and no explicit ND keywords exist → MUST be LOW or NONE\n"
        "2. Generic terms like 'Disabilities' or 'Learning Disabilities' do NOT count as explicit ND keywords\n"
        "3. Councils/local authorities are ALWAYS NONE unless name has specific ND terms (e.g., 'Autism Centre')\n"
        "4. Services with only generic disability support (no autism/ADHD/dyslexia/SEND) → NONE\n"
        "5. Administrative/informational services (school search, admissions, general info) → LOW\n"
        "   Even if they mention SEND/special schools, if they only provide INFORMATION not direct services → LOW\n"
        "6. DISTINCTION: Information service vs Direct service\n"
        "   • Information service (lists schools, provides links, search tools) → LOW\n"
        "   • Direct service (provides therapy, education, support groups) → MEDIUM\n\n"
        "EXAMPLES OF GOOD EXTRACTION:\n\n"
        "Example 1: Mental Health Hospital with ND Services\n"
        "  conditions_supported: [\"Autism/ASC\", \"ADHD\", \"Learning disabilities\", \"Intellectual disabilities\", \"Tourette's syndrome\"]\n"
        "    ✅ Includes primary ND conditions\n"
        "    ❌ Excludes: \"Depression\", \"Anxiety\", \"Stress\" (not ND-specific conditions)\n"
        "  specific_services: [\"Diagnostic assessments (autism, ADHD)\", \"Therapy (individual, group, family)\", \"Inpatient treatment\", \"Outpatient treatment\", \"Day care programs\", \"Specialist ND clinics\"]\n"
        "    ✅ Groups similar services\n"
        "    ✅ Focuses on core services\n"
        "    ❌ Excludes: \"Yoga\", \"Gym facilities\", \"Recreational activities\" (not core services)\n\n"
        "Example 2: ADHD Assessment Clinic\n"
        "  conditions_supported: [\"ADHD\"]\n"
        "    ✅ Single primary condition\n"
        "  specific_services: [\"ADHD assessment\", \"ADHD treatment planning\", \"Prescription management\", \"Follow-up support\"]\n"
        "    ✅ Focused on primary service\n\n"
        "Example 3: Autism School\n"
        "  conditions_supported: [\"Autism/ASC\", \"Learning disabilities\"]\n"
        "    ✅ Primary conditions served\n"
        "  specific_services: [\"Specialist education (SEN)\", \"Speech and language therapy\", \"Occupational therapy\", \"Sensory support programs\", \"Social skills training\"]\n"
        "    ✅ Educational and therapeutic services\n\n"
        "IMPORTANT: Keep arrays focused and meaningful. If a service offers many things, prioritize the 10-12 most important/relevant for neurodivergent individuals.\n\n"
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
        "  \"neurodivergent_relevance_score\": \"High\",\n"
        "  \"is_neurodivergent_related\": true,\n"
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


def get_websearch_cache_path(center_name: str, website_url: str, cache_dir: Optional[str] = None) -> Path:
    """Get cache file path for web search results."""
    if cache_dir is None:
        cache_dir = DEFAULT_CACHE_DIR / "web_search"
    else:
        cache_path = Path(cache_dir)
        if not cache_path.is_absolute():
            cache_dir = DEFAULT_CACHE_DIR / cache_dir
    
    cache_base = Path(cache_dir)
    cache_base.mkdir(parents=True, exist_ok=True)
    
    # Create a safe filename from center name and URL
    cache_key = f"{center_name}_{website_url}".encode('utf-8')
    cache_hash = hashlib.md5(cache_key).hexdigest()
    name_safe = re.sub(r'[^\w\-_.]', '_', center_name)[:50]
    cache_file = cache_base / f"{name_safe}_{cache_hash}.json"
    
    return cache_file


def load_websearch_from_cache(center_name: str, website_url: str, cache_dir: Optional[str] = None, max_age_days: int = 30) -> Optional[Dict[str, any]]:
    """Load web search results from cache if they exist and are not expired."""
    if cache_dir is False:  # Explicitly disabled
        return None
        
    cache_file = get_websearch_cache_path(center_name, website_url, cache_dir)
    
    if not cache_file.exists():
        return None
    
    # Check if cache is expired
    if max_age_days > 0:
        file_age = time.time() - cache_file.stat().st_mtime
        if file_age > (max_age_days * 24 * 60 * 60):
            return None  # Cache expired
    
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            cached_data = json.load(f)
            # Verify it's for the same center and URL
            if (cached_data.get("center_name") == center_name and 
                cached_data.get("website_url") == website_url):
                return cached_data.get("contact_info")
    except (OSError, json.JSONDecodeError, KeyError):
        # Cache file corrupted, ignore it
        pass
    
    return None


def save_websearch_to_cache(center_name: str, website_url: str, contact_info: Dict[str, any], cache_dir: Optional[str] = None) -> None:
    """Save web search results to cache."""
    if cache_dir is False:  # Explicitly disabled
        return
        
    cache_file = get_websearch_cache_path(center_name, website_url, cache_dir)
    
    try:
        cache_data = {
            "center_name": center_name,
            "website_url": website_url,
            "contact_info": contact_info,
            "cached_at": time.time(),
            "cached_at_readable": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
    except OSError:
        # Ignore cache write errors (disk full, permissions, etc.)
        pass


def search_web_for_contact(center_name: str, website_url: str, timeout: int = 10, websearch_cache_dir: Optional[str] = None, refresh_websearch_cache: bool = False) -> Dict[str, any]:
    """Search web for missing contact information from reliable sources."""
    # Check cache first (unless refresh is requested)
    if not refresh_websearch_cache and websearch_cache_dir is not False:
        cached_result = load_websearch_from_cache(center_name, website_url, websearch_cache_dir)
        if cached_result is not None:
            return cached_result
    
    contact_info = {
        "phone": None,
        "email": None, 
        "address": None,
        "address_components": None,
        "sources": []
    }
    
    # Track web search text for content cache
    web_search_text_parts = []
    web_search_sources_list = []
    
    # Build search query
    domain = parse.urlparse(website_url).netloc if website_url else ""
    search_query = parse.quote(f"{center_name} contact phone email {domain}")
    
    # Use DuckDuckGo HTML search (doesn't require API key)
    search_url = f"https://html.duckduckgo.com/html/?q={search_query}"
    
    try:
        # Fetch DuckDuckGo search results page (this also uses HTML cache)
        fetch_result = fetch_url(search_url, timeout=timeout, html_cache_dir=str(DEFAULT_CACHE_DIR / "html_content"))
        if not fetch_result:
            return contact_info
        
        html_content, _ = fetch_result
            
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
            fetch_result = fetch_url(actual_url, timeout=timeout, html_cache_dir=str(DEFAULT_CACHE_DIR / "html_content"))
            if not fetch_result:
                continue
            
            page_html, _ = fetch_result
            page_text = html_to_text(page_html)
            
            # Collect web search text for content cache
            if page_text.strip():
                # Format: URL marker before text (so we know which source we're reading)
                web_search_text_parts.append(f"\n\n=== SOURCE: {actual_url} ===\n\n{page_text}")
                web_search_sources_list.append(actual_url)
            
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
    
    # Save contact info to web search cache
    save_websearch_to_cache(center_name, website_url, contact_info, websearch_cache_dir)
    
    # Also save web search text to content cache (unified cache)
    if web_search_text_parts:
        combined_web_search_text = "\n".join(web_search_text_parts)
        
        # Load existing website_text to preserve it
        content_cache_file = get_content_cache_path(center_name, website_url, str(DEFAULT_CACHE_DIR / "content"))
        existing_website_text = ""
        existing_website_pages = []
        if content_cache_file.exists():
            try:
                with open(content_cache_file, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                    existing_website_text = existing.get("website_text", "")
                    existing_website_pages = existing.get("website_pages", [])
            except Exception:
                pass
        
        save_content_to_cache(
            center_name=center_name,
            website_url=website_url,
            website_text=existing_website_text,
            website_pages=existing_website_pages,
            web_search_text=combined_web_search_text,
            web_search_sources=web_search_sources_list,
            cache_dir=str(DEFAULT_CACHE_DIR / "content")
        )
    
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
    parser.add_argument("--html-cache-dir", default=str(DEFAULT_CACHE_DIR / "html_content"), help=f"Directory to cache HTML content (set to 'false' to disable, default: {DEFAULT_CACHE_DIR / 'html_content'})")
    parser.add_argument("--no-html-cache", action="store_true", help="Disable HTML caching")
    parser.add_argument("--refresh-html-cache", action="store_true", help="Skip HTML cache and fetch fresh content")
    parser.add_argument("--websearch-cache-dir", default=str(DEFAULT_CACHE_DIR / "web_search"), help=f"Directory to cache web search results (set to 'false' to disable, default: {DEFAULT_CACHE_DIR / 'web_search'})")
    parser.add_argument("--no-websearch-cache", action="store_true", help="Disable web search caching")
    parser.add_argument("--refresh-websearch-cache", action="store_true", help="Skip web search cache and perform fresh search")
    args = parser.parse_args()

    # Determine HTML cache settings
    html_cache_dir = None if args.no_html_cache else (False if args.html_cache_dir.lower() == "false" else args.html_cache_dir)
    
    # Determine web search cache settings
    websearch_cache_dir = None if args.no_websearch_cache else (False if args.websearch_cache_dir.lower() == "false" else args.websearch_cache_dir)
    
    # Determine content cache settings - use config CACHE_DIR
    content_cache_dir = str(DEFAULT_CACHE_DIR / "content")
    refresh_content_cache = args.refresh_html_cache  # Use same flag for now
    
    start = args.url
    docs, working_url = crawl_site(
        start, 
        max_pages=args.max_pages, 
        html_cache_dir=html_cache_dir, 
        refresh_html_cache=args.refresh_html_cache,
        center_name=args.center_name,
        content_cache_dir=content_cache_dir,
        refresh_content_cache=refresh_content_cache
    )
    if not docs:
        # Still try to save content cache (empty) to record that crawl was attempted
        if args.center_name and content_cache_dir is not False:
            try:
                save_content_to_cache(
                    center_name=args.center_name,
                    website_url=start,
                    website_text="",  # Empty - fetch failed
                    website_pages=[],
                    web_search_text="",
                    web_search_sources=[],
                    cache_dir=content_cache_dir
                )
            except Exception:
                pass  # Ignore cache save errors
        print("Failed to fetch website content.", file=sys.stderr)
        sys.exit(2)

    prompt = build_prompt(args.center_name, args.url, docs, content_cache_dir=content_cache_dir)

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

    # Clean up "Not specified" values - convert to empty strings
    def clean_not_specified(value):
        """Recursively clean 'Not specified' values to empty strings."""
        if isinstance(value, str):
            if value.strip().lower() in ("not specified", "n/a", "none", "nan", "null", "unknown"):
                return ""
            return value
        elif isinstance(value, dict):
            return {k: clean_not_specified(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [clean_not_specified(item) for item in value]
        return value
    
    obj = clean_not_specified(obj)

    # Ensure center_name and website_url presence
    obj.setdefault("center_name", args.center_name)
    obj.setdefault("website_url", args.url)
    
    # Add the working URL (the one that actually worked)
    if working_url != args.url:
        obj["website_url_corrected"] = working_url
        obj["website_url_original"] = args.url

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
        # Check if phone is missing (empty, None, or placeholder values)
        phone = contact.get("phone", "")
        if not phone or (isinstance(phone, str) and phone.strip().lower() in ("not specified", "n/a", "none", "nan", "unknown", "")):
            missing_fields.append("phone")
        # Check if email is missing
        email = contact.get("email", "")
        if not email or (isinstance(email, str) and email.strip().lower() in ("not specified", "n/a", "none", "nan", "unknown", "")):
            missing_fields.append("email")
        # Check if address is missing
        address = contact.get("address", "")
        if not address or (isinstance(address, str) and address.strip().lower() in ("not specified", "n/a", "none", "nan", "unknown", "")):
            missing_fields.append("address")
        
        if missing_fields:
            print(f"Searching web for missing contact info: {', '.join(missing_fields)}...", file=sys.stderr)
            web_contact = search_web_for_contact(
                args.center_name, 
                args.url,
                websearch_cache_dir=websearch_cache_dir,
                refresh_websearch_cache=args.refresh_websearch_cache
            )
            
            # Track what was enhanced
            enhanced_fields = []
            
            # Update phone if missing or placeholder
            phone = contact.get("phone", "")
            if (not phone or (isinstance(phone, str) and phone.strip().lower() in ("not specified", "n/a", "none", "nan", "unknown", ""))) and web_contact.get("phone"):
                contact["phone"] = web_contact["phone"]
                enhanced_fields.append("phone")
            
            # Update email if missing or placeholder
            email = contact.get("email", "")
            if (not email or (isinstance(email, str) and email.strip().lower() in ("not specified", "n/a", "none", "nan", "unknown", ""))) and web_contact.get("email"):
                contact["email"] = web_contact["email"]
                enhanced_fields.append("email")
            
            # Update address if missing or placeholder
            address = contact.get("address", "")
            if (not address or (isinstance(address, str) and address.strip().lower() in ("not specified", "n/a", "none", "nan", "unknown", ""))) and web_contact.get("address"):
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


