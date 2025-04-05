"""
scraper.py
----------

An asynchronous, high-performance refactoring of the original scraper.
Maintains existing domain-specific rules and BFS logic but uses aiohttp
and asyncio to scrape multiple pages concurrently.

PEP 8 Conventions:
- Module-level constants in all caps if needed.
- Functions use snake_case.
- Classes use PascalCase.

Dependencies:
- aiohttp >= 3.8.4
- beautifulsoup4
- Python 3.8+ recommended

References:
- https://docs.aiohttp.org/en/stable/
- https://docs.python.org/3/library/asyncio.html
- https://peps.python.org/pep-0008/
"""

import asyncio
import re
from urllib.parse import urlparse, urljoin

import aiohttp
from bs4 import BeautifulSoup

from domain_rules import DOMAIN_RULES


def extract_price_via_rule(soup, rule):
    """
    Extract price strings from a BeautifulSoup document using the domain-specific rule.

    :param soup: BeautifulSoup instance of the parsed HTML.
    :param rule: Dict containing 'price_selector' for CSS selection and 'price_cleaning' callable.
    :return: List of price strings (potentially cleaned/normalized).
    :complexity: O(n) where n is the number of matching elements selected.
    """
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
    """
    Convert a car make/model into a URL-friendly format:
    - Lowercase
    - Replace spaces and non-alphanumeric characters with a hyphen
    - Collapse multiple hyphens
    - Remove leading/trailing hyphens

    :param make: Car make (e.g., 'BMW')
    :param model: Car model (e.g., 'X5')
    :return: A normalized, hyphenated string (e.g., 'bmw-x5')
    :complexity: O(m), where m is the combined length of make and model
    """
    combined = f"{make}-{model}" if make else model
    combined = combined.lower()

    # Replace non-alphanumeric chars with hyphen
    slug = re.sub(r'[^a-z0-9]+', '-', combined)

    # Strip leading/trailing hyphens
    slug = slug.strip('-')

    return slug


def should_process_url(url, prefixes):
    """
    Decide whether a given URL path should be processed based on domain-specific prefixes.

    :param url: The full URL to evaluate.
    :param prefixes: List of path prefixes that indicate potential car pages.
    :return: True if the path starts with any known prefix and meets minimal segment count.
    :complexity: O(p) where p is the number of prefixes.
    """
    path = urlparse(url).path
    segments = [s for s in path.split('/') if s]

    for prefix in prefixes:
        if path.startswith(prefix):
            # If prefix == "/" or there are at least 2 segments
            if prefix == "/" or len(segments) >= 2:
                return True
    return False


async def fetch_url_with_retry(
    session, url, max_retries=3, base_timeout=20
):
    """
    Perform an asynchronous GET request with built-in retries.

    :param session: aiohttp.ClientSession object.
    :param url: URL to fetch.
    :param max_retries: Number of retry attempts for network failures or non-200 responses.
    :param base_timeout: Base timeout for the request; adjusted for known slow domains.
    :return: The HTML text if successful, None otherwise.
    :complexity: O(r) where r = max_retries, each attempt is an async HTTP request.
    """
    for attempt in range(max_retries):
        try:
            timeout_val = base_timeout
            if "uptowndxb.com" in url:
                timeout_val = 30
            if "ferrorental.com" in url:
                timeout_val = 40

            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=timeout_val)
            ) as resp:
                if resp.status == 200:
                    return await resp.text()

                print(f"[WARN] Attempt {attempt+1}: Status code {resp.status} for {url}")

        except Exception as e:
            print(f"[WARN] Attempt {attempt+1} failed for {url}: {e}")

        # Short delay before retrying
        await asyncio.sleep(1)

    print(f"[ERROR] All {max_retries} attempts failed for {url}")
    return None


async def scrape_car_page(session, domain_rule, domain, url, car_queries):
    """
    Scrape a single car page to find matching makes/models and price info.

    :param session: aiohttp.ClientSession for requests.
    :param domain_rule: Dictionary with domain-specific 'price_selector' and 'price_cleaning'.
    :param domain: The domain (e.g., 'https://phantomrentcar.com').
    :param url: The page URL to scrape.
    :param car_queries: A list of dicts, each with 'make' and 'model'.
    :return: A list of result dicts (make, model, domain, url, prices).
    :complexity: O(q + n) where q = number of car_queries, n = number of matched price tags.
    """
    found = []
    try:
        print(f"[SCRAPE] Visiting {url}")
        html_content = await fetch_url_with_retry(session, url)
        if not html_content:
            return found

        soup = BeautifulSoup(html_content, 'html.parser')
        url_path = urlparse(url).path

        for query in car_queries:
            make = query.get('make', '').strip()
            model = query.get('model', '').strip()
            if not make or not model:
                continue

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

    except Exception as e:
        print(f"[ERROR] scrape_car_page: {e} @ {url}")
    return found


async def crawl_domain(domain, car_queries, max_depth=3, max_workers=50):
    """
    Asynchronously crawl a domain to discover relevant car pages and extract pricing info.

    :param domain: The domain to crawl (e.g., 'https://mkrentacar.com/').
    :param car_queries: A list of car query dicts with 'make' and 'model'.
    :param max_depth: BFS depth limit to avoid infinite or extensive crawling.
    :param max_workers: Number of concurrent tasks to allow.
    :return: A dict { domain: [ list_of_found_results ] } or {} if none found.
    :complexity:
       - BFS is O(N) where N is the total pages visited up to max_depth.
       - Each page fetch is done concurrently, up to max_workers.
    """
    parsed = urlparse(domain)
    domain_host = parsed.netloc
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    # If domain is not in the domain_rules, skip
    if domain_host not in DOMAIN_RULES:
        print(f"[SKIP] No rules for {domain_host}")
        return {}

    rule = DOMAIN_RULES[domain_host]
    prefixes = rule.get("url_prefixes", [])

    visited = set()
    to_visit = set([base_url])
    discovered_car_pages = set()
    found = []
    depth = 0

    async with aiohttp.ClientSession() as session:
        # Semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_workers)

        # BFS-like approach
        while to_visit and depth < max_depth:
            print(f"[DEPTH {depth}] Processing {len(to_visit)} URLs...")
            current_batch = list(to_visit)
            to_visit.clear()
            depth += 1

            fetch_tasks = []

            for url in current_batch:
                if url in visited:
                    continue
                visited.add(url)

                async def fetch_and_extract(u):
                    async with semaphore:
                        html = await fetch_url_with_retry(session, u)
                        if not html:
                            return

                        soup = BeautifulSoup(html, "html.parser")
                        # Extract all links
                        for link in soup.find_all('a', href=True):
                            href = link['href'].strip()
                            if href.startswith(("javascript:", "#")):
                                continue

                            full_url = urljoin(u, href)
                            full_url_parsed = urlparse(full_url)

                            # Only stay within the same domain
                            if full_url_parsed.netloc != domain_host:
                                continue

                            norm_url = full_url.split("#")[0]
                            if norm_url not in visited:
                                # If domain == ferrorental.com, skip /ru/ prefix
                                if domain_host == "ferrorental.com" and urlparse(norm_url).path.startswith("/ru/"):
                                    continue

                                # If should_process_url, it's likely a car page
                                if should_process_url(norm_url, prefixes):
                                    discovered_car_pages.add(norm_url)
                                else:
                                    to_visit.add(norm_url)

                task = asyncio.create_task(fetch_and_extract(url))
                fetch_tasks.append(task)

            await asyncio.gather(*fetch_tasks)

        # Now scrape all discovered car pages in parallel
        print(f"[SCRAPE] Processing {len(discovered_car_pages)} discovered car pages...")
        scrape_tasks = []
        for url in discovered_car_pages:
            scrape_tasks.append(asyncio.create_task(
                scrape_car_page(session, rule, domain, url, car_queries)
            ))

        scrape_results = await asyncio.gather(*scrape_tasks, return_exceptions=True)
        for result in scrape_results:
            if isinstance(result, list):
                found.extend(result)
            else:
                print(f"[ERROR] Exception in scrape results: {result}")

    return {domain: found} if found else {}