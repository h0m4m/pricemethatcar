from flask import Flask, request, jsonify
from scraper import crawl_domain

app = Flask(__name__)

# Supported domains
SUPPORTED_DOMAINS = [
    # "https://www.rotanastar.ae/",
    "https://phantomrentcar.com/",
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

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.get_json()
    if not data or 'cars' not in data:
        return jsonify({"error": "Missing 'cars' list"}), 400

    car_queries = data['cars']
    if not isinstance(car_queries, list):
        return jsonify({"error": "'cars' must be a list"}), 400

    # Validate car queries
    for query in car_queries:
        if not isinstance(query, dict):
            return jsonify({"error": "Each car query must be an object"}), 400
        if 'make' not in query or 'model' not in query:
            return jsonify({"error": "Each car query must have 'make' and 'model' fields"}), 400

    print(f"[REQUEST] Received request to scrape for cars: {car_queries}")
    all_results = {}

    for domain in SUPPORTED_DOMAINS:
        print(f"[CRAWL] Starting crawl for domain: {domain}")
        result = crawl_domain(domain, car_queries)
        all_results.update(result)

    print(f"[DONE] Scraping complete. Found results for {len(all_results)} domains.")
    return jsonify(all_results)

if __name__ == '__main__':
    app.run(debug=True, port=5000)