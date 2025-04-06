from flask import Flask, request, jsonify, render_template
import asyncio
import nest_asyncio

from scraper import crawl_domain

nest_asyncio.apply()
# Supported domains remain the same
SUPPORTED_DOMAINS = [
    "https://www.rotanastar.ae/",
    # "https://phantomrentcar.com/",
    # "https://mkrentacar.com/",
    # "https://superiorrental.ae/",
    # "https://octane.rent/",
    # "https://www.uptowndxb.com/",
    # "https://www.bevip.ae/",
    # "https://xcarrental.com/",
    # "https://ferrorental.com/",
    # "https://mtn-rentacar.com/",
    # "https://www.selyarentacar.com/",
    # "https://firstsupercarrental.com/"
]

app = Flask(__name__)

@app.route('/')
def index():
    """
    Serve the frontend UI at the root path `/`.
    Loads `templates/index.html`, which includes links to static JS and CSS.
    """
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.get_json()
    if not data or 'cars' not in data:
        return jsonify({"error": "Missing 'cars' list"}), 400

    car_queries = data['cars']
    if not isinstance(car_queries, list):
        return jsonify({"error": "'cars' must be a list"}), 400

    for query in car_queries:
        if not isinstance(query, dict) or 'make' not in query or 'model' not in query:
            return jsonify({"error": "Each car query must have 'make' and 'model' fields"}), 400

    print(f"[REQUEST] Received request to scrape for cars: {car_queries}")
    all_results = {}

    loop = asyncio.get_event_loop()
    for domain in SUPPORTED_DOMAINS:
        print(f"[CRAWL] Starting crawl for domain: {domain}")
        result = loop.run_until_complete(crawl_domain(domain, car_queries))
        all_results.update(result)

    print(f"[DONE] Scraping complete. Found results for {len(all_results)} domains.")
    return jsonify(all_results)

@app.route('/mock-scrape', methods=['POST'])
def mock_scrape():
    """
    Returns mock pricing results for testing the frontend.
    Accepts the same payload as /scrape: {"cars": [{make, model}, ...]}
    """

    data = request.get_json()
    if not data or 'cars' not in data:
        return jsonify({"error": "Missing 'cars' list"}), 400

    car_queries = data['cars']
    mock_response = {}

    for car in car_queries:
        make = car.get('make', '').strip()
        model = car.get('model', '').strip()
        key = f"{make}-{model}".lower().replace(" ", "-")

        mock_response.setdefault("rotanastar.ae", []).append({
            "make": make,
            "model": model,
            "url": f"https://www.rotanastar.ae/car/{key}/",
            "prices": ["3200", "3400", "3000"]
        })

        mock_response.setdefault("phantomrentcar.com", []).append({
            "make": make,
            "model": model,
            "url": f"https://phantomrentcar.com/car/{key}/",
            "prices": ["3100", "3150"]
        })

    return jsonify(mock_response)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
