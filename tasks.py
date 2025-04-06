from celery_app import celery
from scraper import crawl_domain
import asyncio

SUPPORTED_DOMAINS = [
    "https://www.rotanastar.ae/",
    "https://phantomrentcar.com/",
    "https://mkrentacar.com/",
    "https://superiorrental.ae/",
    "https://www.uptowndxb.com/",
    "https://www.bevip.ae/",
    "https://xcarrental.com/",
    "https://ferrorental.com/",
    "https://mtn-rentacar.com/",
    "https://www.selyarentacar.com/",
    "https://firstsupercarrental.com/"
]

async def scrape_all_domains(car_queries):
    tasks = [crawl_domain(domain, car_queries) for domain in SUPPORTED_DOMAINS]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    aggregated = {}
    for result in results:
        if isinstance(result, dict):
            aggregated.update(result)
    return aggregated

@celery.task(bind=True)
def run_scrape_job(self, car_queries):
    return asyncio.run(scrape_all_domains(car_queries))