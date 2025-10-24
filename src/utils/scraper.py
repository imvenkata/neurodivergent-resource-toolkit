"""
London Autism Group Services Map Scraper
Extracts all service center information from the interactive map
"""

import asyncio
import json
import csv
from playwright.async_api import async_playwright
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import html
import re
import xml.etree.ElementTree as ET


def clean_html(raw_text):
    """Decode HTML entities, replace line-break tags with newlines, and strip remaining tags."""
    if not raw_text:
        return ""
    text = html.unescape(raw_text)
    # Normalize common line break tags to newlines
    text = re.sub(r"(?i)<\s*br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</\s*p\s*>", "\n", text)
    text = re.sub(r"(?i)<\s*p\b[^>]*>", "", text)
    # Strip all remaining tags
    text = re.sub(r"<[^>]+>", "", text)
    # Collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_first_url(text: str) -> str:
    """Return the first URL found in text, else empty string."""
    if not text:
        return ""
    match = re.search(r"https?://\S+", text)
    return match.group(0).rstrip('.,);]"\'') if match else ""


def split_description_and_address(text: str) -> tuple[str, str]:
    """Heuristically split text into description and address (UK-biased).

    - Address chosen as the first line that looks address-like (postcode or common tokens).
    - Everything else is description.
    """
    if not text:
        return "", ""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    postcode_re = re.compile(r"\b[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}\b", re.I)
    address_tokens = ("road", "rd", "street", "st ", "st.", "avenue", "ave", "lane", "ln", "close", "cl", "square", "sq", "london", "uk")

    address_line = ""
    for ln in lines:
        if postcode_re.search(ln):
            address_line = ln
            break
        low = ln.lower()
        if any(tok in low for tok in address_tokens):
            address_line = ln
            break

    if address_line:
        remaining = [ln for ln in lines if ln != address_line]
        description = "\n".join(remaining).strip()
        return description, address_line
    else:
        return "\n".join(lines).strip(), ""


def parse_kml_coordinates(coord: str) -> tuple[str, str]:
    """Parse KML coordinates string "lng,lat[,alt]" into (lat, lng) strings."""
    if not coord:
        return "", ""
    # KML uses "longitude,latitude[,altitude]"
    parts = [p.strip() for p in coord.split(",")]
    if len(parts) >= 2:
        lng, lat = parts[0], parts[1]
        return lat, lng
    return "", ""


def normalize_service_fields(title: str, content: str, coordinates: str = "", link: str | None = None) -> dict:
    """Return a normalized service record with split columns and preserved raw content."""
    cleaned_title = clean_html(title or "").strip()
    cleaned_content = clean_html(content or "").strip()
    url = (extract_first_url(cleaned_content) or (link or ""))
    description, address = split_description_and_address(cleaned_content)
    lat, lng = parse_kml_coordinates(coordinates)
    return {
        "title": cleaned_title or "Untitled",
        "description": description,
        "address": address,
        "url": url,
        "latitude": lat,
        "longitude": lng,
        "content": cleaned_content,  # keep full cleaned text for reference
    }


async def extract_services_via_kml(page):
    """Try to extract services directly from the Google My Maps KML feed."""
    try:
        frames = page.frames
        frame_url = None
        for frame in frames:
            url = frame.url or ""
            if "google.com/maps" in url and ("/d/" in url or "mid=" in url):
                frame_url = url
                break

        if not frame_url:
            return []

        parsed = urlparse(frame_url)
        params = parse_qs(parsed.query)
        mid = (params.get("mid") or [None])[0]
        if not mid:
            # Sometimes the mid is embedded in the path as /d/embed?mid=...
            return []

        kml_url = f"https://www.google.com/maps/d/kml?mid={mid}&forcekml=1"
        response = await page.context.request.get(kml_url)
        if response.status != 200:
            return []

        kml_text = await response.text()
        if not kml_text:
            return []

        # Parse KML
        # Common KML namespace
        ns = {"kml": "http://www.opengis.net/kml/2.2"}
        try:
            root = ET.fromstring(kml_text)
        except ET.ParseError:
            return []

        services = []
        for placemark in root.findall(".//kml:Placemark", ns):
            name_el = placemark.find("kml:name", ns)
            desc_el = placemark.find("kml:description", ns)
            point_el = placemark.find("kml:Point/kml:coordinates", ns)

            title = (name_el.text or "").strip() if name_el is not None else ""
            description = (desc_el.text or "").strip() if desc_el is not None else ""
            coordinates = (point_el.text or "").strip() if point_el is not None else ""

            normalized = normalize_service_fields(title, description, coordinates)
            service = {
                **normalized,
                "coordinates": coordinates,
                "category": extract_category((normalized.get("title") or "") or (normalized.get("description") or "")),
            }
            services.append(service)

        return services
    except Exception:
        # If anything goes wrong, just fall back to UI scraping
        return []

async def scrape_autism_services():
    """
    Scrapes all service centers from the London Autism Group map
    """
    
    all_services = []
    
    async with async_playwright() as p:
        # Launch browser (set headless=False to see the browser in action)
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        print("Loading the map page...")
        await page.goto('https://www.londonautismgroupcharity.org/london-map-of-services', 
                       wait_until='networkidle')
        
        # Wait for the map to load
        await asyncio.sleep(5)
        
        print("Waiting for map markers to load...")
        
        # First attempt: use KML feed from Google My Maps (more reliable)
        kml_services = await extract_services_via_kml(page)
        if kml_services:
            print(f"\nExtracted {len(kml_services)} services via KML feed")
            all_services.extend(kml_services)
            print(f"\n\nTotal services extracted: {len(all_services)}")
            await browser.close()
            return all_services
        
        # Try to find the map container and markers
        # Google Maps markers are usually in an iframe or specific containers
        
        # Look for all possible marker elements
        # This may need adjustment based on actual map implementation
        marker_selectors = [
            'area[shape="poly"]',  # Image map areas
            'img[usemap]',  # Image maps
            'div[role="button"]',  # Google Maps markers
            'button[aria-label*="marker"]',
            '.gm-style button',  # Google Maps style buttons
        ]
        
        markers_found = []
        
        for selector in marker_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"Found {len(elements)} elements with selector: {selector}")
                    markers_found.extend(elements)
            except Exception as e:
                print(f"Error with selector {selector}: {e}")
        
        # If it's an image map, try to get the areas
        try:
            # Check for image map
            image_map = await page.query_selector('img[usemap]')
            if image_map:
                usemap_value = await image_map.get_attribute('usemap')
                map_name = usemap_value.replace('#', '')
                
                areas = await page.query_selector_all(f'map[name="{map_name}"] area')
                print(f"\nFound {len(areas)} clickable areas in image map")
                
                for idx, area in enumerate(areas, 1):
                    try:
                        title = await area.get_attribute('title')
                        alt = await area.get_attribute('alt')
                        href = await area.get_attribute('href')
                        
                        print(f"\nProcessing area {idx}/{len(areas)}")
                        print(f"Title: {title}")
                        
                        # Click the area
                        await area.click()
                        await asyncio.sleep(2)
                        
                        # Try to capture any popup or modal that appears
                        # Look for common popup/modal selectors
                        popup_selectors = [
                            '.popup-content',
                            '.modal-body',
                            '.info-window',
                            '[role="dialog"]',
                            '.gm-style-iw',  # Google Maps info window
                        ]
                        
                        popup_content = ""
                        for popup_sel in popup_selectors:
                            popup = await page.query_selector(popup_sel)
                            if popup:
                                popup_content = await popup.inner_text()
                                break
                        
                        # If no popup found, try to get content from the page
                        if not popup_content:
                            popup_content = await page.inner_text('body')
                        
                        normalized = normalize_service_fields(title or alt or f"Service {idx}", popup_content, link=href)
                        service_data = {
                            **normalized,
                            'index': idx,
                            'category': extract_category((normalized.get('title') or '') or (normalized.get('description') or '')),
                        }
                        all_services.append(service_data)
                        
                        # Try to close popup if there's a close button
                        close_button = await page.query_selector('button[aria-label*="Close"], .close, [class*="close"]')
                        if close_button:
                            await close_button.click()
                            await asyncio.sleep(1)
                        
                    except Exception as e:
                        print(f"Error processing area {idx}: {e}")
                        continue
        
        except Exception as e:
            print(f"Error with image map approach: {e}")
        
        # Alternative: Try to find Google Maps iframe
        try:
            frames = page.frames
            print(f"\nFound {len(frames)} frames on page")
            
            for frame_idx, frame in enumerate(frames):
                try:
                    frame_url = frame.url
                    if 'google.com/maps' in frame_url or 'gm-' in frame_url:
                        print(f"Found potential Google Maps frame: {frame_url}")
                        
                        # Try to interact with markers in the iframe
                        markers = await frame.query_selector_all('[role="button"]')
                        print(f"Found {len(markers)} buttons in frame")
                        
                        for marker_idx, marker in enumerate(markers[:50], 1):  # Limit to first 50
                            try:
                                aria_label = await marker.get_attribute('aria-label')
                                print(f"\nClicking marker {marker_idx}: {aria_label}")
                                
                                await marker.click()
                                await asyncio.sleep(2)
                                
                                # Get info window content
                                info_window = await frame.query_selector('.gm-style-iw')
                                if info_window:
                                    content = await info_window.inner_text()
                                    
                                    normalized = normalize_service_fields(aria_label or f"Service {marker_idx}", content)
                                    service_data = {
                                        **normalized,
                                        'index': marker_idx,
                                        'category': extract_category((normalized.get('title') or '') or (normalized.get('description') or '')),
                                    }
                                    all_services.append(service_data)
                                
                            except Exception as e:
                                print(f"Error with marker {marker_idx}: {e}")
                                continue
                
                except Exception as e:
                    print(f"Error with frame {frame_idx}: {e}")
                    continue
        
        except Exception as e:
            print(f"Error with iframe approach: {e}")
        
        print(f"\n\nTotal services extracted: {len(all_services)}")
        
        await browser.close()
    
    return all_services


def extract_category(text):
    """Extract service category from text"""
    categories = [
        'LAG Charity Community Café Sites',
        'National Autistic Society Branches',
        'Employment and Skills Services',
        'Local Support Services and Groups',
        'Autism Friendly Entertainment',
        'Autism Friendly Sports Activities',
        'Special Interests and Hobbies',
        'Special Needs Play Centres'
    ]
    
    text_lower = text.lower()
    for category in categories:
        if any(word.lower() in text_lower for word in category.split() if len(word) > 3):
            return category
    
    return 'Unknown Category'


def save_to_json(data, filename='autism_services.json'):
    """Save data to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\nData saved to {filename}")


def save_to_csv(data, filename='autism_services.csv'):
    """Save data to CSV file"""
    if not data:
        print("No data to save")
        return
    
    keys = data[0].keys()
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)
    print(f"Data saved to {filename}")


def save_to_excel(data, filename='autism_services.xlsx'):
    """Save data to Excel file"""
    try:
        import pandas as pd
        df = pd.DataFrame(data)
        df.to_excel(filename, index=False, engine='openpyxl')
        print(f"Data saved to {filename}")
    except ImportError:
        print("pandas and openpyxl are required for Excel export")
        print("Install with: pip install pandas openpyxl")


async def main():
    """Main execution function"""
    print("=" * 60)
    print("London Autism Services Map Scraper")
    print("=" * 60)
    print()
    
    # Scrape the data
    services = await scrape_autism_services()
    
    if services:
        # Save in multiple formats
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        save_to_json(services, f'autism_services_{timestamp}.json')
        save_to_csv(services, f'autism_services_{timestamp}.csv')
        
        try:
            save_to_excel(services, f'autism_services_{timestamp}.xlsx')
        except Exception:
            pass
        
        print("\n" + "=" * 60)
        print("Scraping completed successfully!")
        print("=" * 60)
        
        # Print summary
        print(f"\nTotal services extracted: {len(services)}")
        
        # Group by category
        categories = {}
        for service in services:
            cat = service.get('category', 'Unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        print("\nServices by category:")
        for cat, count in categories.items():
            print(f"  - {cat}: {count}")
    else:
        print("\n⚠️  No services were extracted. The map structure may have changed.")
        print("Please check the browser window to see what happened.")


if __name__ == "__main__":
    asyncio.run(main())