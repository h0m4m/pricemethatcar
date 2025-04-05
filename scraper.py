import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, urljoin
from domain_rules import DOMAIN_RULES

def extract_price_via_rule(soup, rule):
    selector = rule.get("price_selector")
    cleaning = rule.get("price_cleaning", lambda x: x.strip())
    matches = soup.select(selector) if selector else []
    prices = set()

    for tag in matches:
        text = tag.get_text()
        price = cleaning(text)
        if price:
            prices.add(price)
    return list(prices)

def scrape_car_page(domain_rule, domain, url, car_names):
    found = []
    try:
        print(f"[SCRAPE] Visiting {url}")
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, 'html.parser')
        page_text = soup.get_text().lower()

        for car in car_names:
            if car.lower() in page_text or all(part in url.lower() for part in car.lower().split()):
                prices = extract_price_via_rule(soup, domain_rule)
                result = {
                    "car_name": car,
                    "domain": domain,
                    "url": url,
                    "prices": prices if prices else ["N/A"]
                }
                print(f"[MATCH] Found {car} with prices {result['prices']} at {url}")
                found.append(result)
        return found
    except Exception as e:
        print(f"[ERROR] scrape_car_page: {e} @ {url}")
        return []

def is_valid_prefix(path, prefixes):
    for prefix in prefixes:
        if path.startswith(prefix):
            print(f"[VALID] Found valid URL prefix: {path}")
            return True
    return False

def crawl_domain(domain, car_names, max_depth=3, max_workers=15):
    parsed = urlparse(domain)
    domain_host = parsed.netloc
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    if domain_host not in DOMAIN_RULES:
        print(f"[SKIP] No rules for {domain_host}")
        return []

    rule = DOMAIN_RULES[domain_host]
    prefixes = rule.get("url_prefixes", [])
    visited = set()
    to_visit = [domain]  # Start with the main domain
    discovered_car_pages = set()
    depth = 0

    print(f"[CRAWL] Starting crawl from {domain}")
    print(f"[INFO] Looking for URLs with prefixes: {prefixes}")

    while to_visit and depth < max_depth:
        print(f"[DEPTH {depth}] Crawling {len(to_visit)} pages...")
        next_to_visit = set()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(requests.get, url, timeout=10): url for url in to_visit}
            for future in as_completed(futures):
                url = futures[future]
                visited.add(url)
                try:
                    resp = future.result()
                    if resp.status_code != 200:
                        print(f"[ERROR] Failed to fetch {url}: Status code {resp.status_code}")
                        continue

                    content_type = resp.headers.get('Content-Type', '')
                    if 'text/html' not in content_type:
                        print(f"[SKIP] Non-HTML content at {url}")
                        continue

                    soup = BeautifulSoup(resp.text, 'html.parser')
                    
                    # Look for car links in navigation menus
                    nav_links = soup.find_all('a', href=True)
                    for link in nav_links:
                        href = link['href'].strip()
                        if href.startswith("javascript:") or href.startswith("#"):
                            continue

                        full_url = urljoin(url, href)
                        full_url_parsed = urlparse(full_url)

                        if full_url_parsed.netloc != domain_host:
                            continue

                        norm_url = full_url.split("#")[0]
                        if norm_url not in visited:
                            path = full_url_parsed.path
                            if is_valid_prefix(path, prefixes):
                                print(f"[DISCOVERED] Found car page: {norm_url}")
                                discovered_car_pages.add(norm_url)
                            next_to_visit.add(norm_url)

                    # Also look for car links in the main content
                    car_links = soup.find_all('a', class_=lambda x: x and ('car' in x.lower() or 'vehicle' in x.lower()))
                    for link in car_links:
                        href = link.get('href', '').strip()
                        if href and not href.startswith(("javascript:", "#")):
                            full_url = urljoin(url, href)
                            full_url_parsed = urlparse(full_url)
                            if full_url_parsed.netloc == domain_host:
                                norm_url = full_url.split("#")[0]
                                if norm_url not in visited:
                                    print(f"[DISCOVERED] Found car link: {norm_url}")
                                    discovered_car_pages.add(norm_url)
                                    next_to_visit.add(norm_url)

                except Exception as e:
                    print(f"[ERROR] Failed crawling {url}: {e}")

        to_visit = list(next_to_visit - visited)
        depth += 1

    print(f"[INFO] Total car pages discovered: {len(discovered_car_pages)}")
    print(f"[INFO] Car pages to scrape: {discovered_car_pages}")

    # Scrape car pages
    found = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(scrape_car_page, rule, domain, url, car_names): url
            for url in discovered_car_pages
        }
        for future in as_completed(futures):
            try:
                result = future.result()
                found.extend(result)
            except Exception as e:
                print(f"[ERROR] scraping car page: {e}")

    # Deduplication
    seen = set()
    final = []
    for entry in found:
        for price in entry['prices']:
            key = (entry['car_name'], entry['url'], price)
            if key not in seen:
                seen.add(key)
                final.append({
                    "car_name": entry['car_name'],
                    "domain": entry['domain'],
                    "price": price,
                    "url": entry['url']
                })

    print(f"[DONE] {len(final)} unique car listings found.\n")
    return final