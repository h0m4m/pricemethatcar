import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, urljoin
from domain_rules import DOMAIN_RULES
import re
import time

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

def normalize_car_name(make, model):
    """Convert car make and model to URL-friendly format"""
    if not make:  # If only model is provided
        return re.sub(r'[^a-z0-9-]', '', model.lower())
    combined = f"{make}-{model}".lower()
    return re.sub(r'[^a-z0-9-]', '', combined)

def construct_car_urls(domain, prefixes, make, model):
    """Try to construct possible car URLs based on make and model"""
    base_url = domain.rstrip('/')
    normalized = normalize_car_name(make, model)
    urls = []
    
    # Try make-model combination
    for prefix in prefixes:
        urls.append(f"{base_url}{prefix}{normalized}/")
    
    # Try just the model
    model_only = normalize_car_name("", model)
    for prefix in prefixes:
        urls.append(f"{base_url}{prefix}{model_only}/")
    
    return urls

def fetch_url_with_retry(url, max_retries=3, timeout=20):
    """Fetch URL with retry logic and increased timeout"""
    for attempt in range(max_retries):
        try:
            # Add a small delay between retries
            if attempt > 0:
                time.sleep(1)
                
            # Use a longer timeout for problematic domains
            if "uptowndxb.com" in url:
                timeout = 30  # 30 seconds for Uptown Dubai
                
            resp = requests.get(url, timeout=timeout)
            if resp.status_code == 200:
                return resp
            print(f"[WARN] Attempt {attempt+1}: Status code {resp.status_code} for {url}")
        except Exception as e:
            print(f"[WARN] Attempt {attempt+1} failed for {url}: {e}")
            
    print(f"[ERROR] All {max_retries} attempts failed for {url}")
    return None

def scrape_car_page(domain_rule, domain, url, car_queries):
    found = []
    try:
        print(f"[SCRAPE] Visiting {url}")
        resp = fetch_url_with_retry(url)
        if not resp:
            return []

        soup = BeautifulSoup(resp.text, 'html.parser')
        url_path = urlparse(url).path.lower()

        for query in car_queries:
            make = query.get('make', '').strip()
            model = query.get('model', '').strip()
            
            if not make or not model:
                continue
                
            # Check if URL contains either make-model combination or just model
            normalized = normalize_car_name(make, model)
            model_only = normalize_car_name("", model)
            
            if normalized in url_path or model_only in url_path:
                prices = extract_price_via_rule(soup, domain_rule)
                result = {
                    "make": make,
                    "model": model,
                    "domain": domain,
                    "url": url,
                    "prices": prices if prices else ["N/A"]
                }
                print(f"[MATCH] Found {make} {model} with prices {result['prices']} at {url}")
                found.append(result)
        return found
    except Exception as e:
        print(f"[ERROR] scrape_car_page: {e} @ {url}")
        return []

def crawl_domain(domain, car_queries, max_depth=3, max_workers=15):
    parsed = urlparse(domain)
    domain_host = parsed.netloc
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    if domain_host not in DOMAIN_RULES:
        print(f"[SKIP] No rules for {domain_host}")
        return {}

    rule = DOMAIN_RULES[domain_host]
    prefixes = rule.get("url_prefixes", [])
    found = []
    found_with_prices = False

    # First try direct URL construction for each car
    for query in car_queries:
        make = query.get('make', '').strip()
        model = query.get('model', '').strip()
        
        if not make or not model:
            continue
            
        possible_urls = construct_car_urls(base_url, prefixes, make, model)
        print(f"[TRY] Attempting direct URLs for {make} {model}: {possible_urls}")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(scrape_car_page, rule, domain, url, [query]): url
                for url in possible_urls
            }
            for future in as_completed(futures):
                try:
                    result = future.result()
                    found.extend(result)
                    # Check if we found any results with actual prices
                    if result and any(price != "N/A" for r in result for price in r['prices']):
                        found_with_prices = True
                except Exception as e:
                    print(f"[ERROR] scraping car page: {e}")

    # If we found results with actual prices through direct URLs, return them
    if found_with_prices:
        results_by_domain = {domain: found}
        print(f"[DONE] Found results with prices through direct URLs for {domain}")
        return results_by_domain

    # If no results found with prices through direct URLs, fall back to crawling
    print(f"[FALLBACK] No prices found through direct URLs, falling back to crawling {domain}")
    visited = set()
    to_visit = [domain]
    discovered_car_pages = set()
    depth = 0

    while to_visit and depth < max_depth:
        print(f"[DEPTH {depth}] Crawling {len(to_visit)} pages...")
        next_to_visit = set()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(fetch_url_with_retry, url): url for url in to_visit}
            for future in as_completed(futures):
                url = futures[future]
                visited.add(url)
                try:
                    resp = future.result()
                    if not resp:
                        continue

                    content_type = resp.headers.get('Content-Type', '')
                    if 'text/html' not in content_type:
                        continue

                    soup = BeautifulSoup(resp.text, 'html.parser')
                    
                    # Look for car links
                    all_links = soup.find_all('a', href=True)
                    for link in all_links:
                        href = link['href'].strip()
                        if href.startswith(("javascript:", "#")):
                            continue

                        full_url = urljoin(url, href)
                        full_url_parsed = urlparse(full_url)

                        if full_url_parsed.netloc != domain_host:
                            continue

                        norm_url = full_url.split("#")[0]
                        if norm_url not in visited:
                            path = full_url_parsed.path
                            if any(path.startswith(prefix) for prefix in prefixes):
                                discovered_car_pages.add(norm_url)
                            next_to_visit.add(norm_url)

                except Exception as e:
                    print(f"[ERROR] Failed crawling {url}: {e}")

        to_visit = list(next_to_visit - visited)
        depth += 1

    # Scrape discovered car pages
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(scrape_car_page, rule, domain, url, car_queries): url
            for url in discovered_car_pages
        }
        for future in as_completed(futures):
            try:
                result = future.result()
                found.extend(result)
            except Exception as e:
                print(f"[ERROR] scraping car page: {e}")

    # Group results by domain
    results_by_domain = {domain: found} if found else {}
    print(f"[DONE] Found results for {domain}")
    return results_by_domain