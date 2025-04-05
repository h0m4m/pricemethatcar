from flask import Flask, request, jsonify
from scraper import crawl_domain

app = Flask(__name__)

# Hardcoded domains
SUPPORTED_DOMAINS = [
    "https://www.vipcarrental.ae/"
]

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.get_json()
    if not data or 'cars' not in data:
        return jsonify({"error": "Missing 'cars' list"}), 400

    car_names = data['cars']
    print(f"[REQUEST] Received request to scrape for cars: {car_names}")
    all_results = []

    for domain in SUPPORTED_DOMAINS:
        print(f"[CRAWL] Starting crawl for domain: {domain}")
        result = crawl_domain(domain, car_names)
        all_results.extend(result)

    print(f"[DONE] Scraping complete. Total results: {len(all_results)}")
    return jsonify(all_results)

if __name__ == '__main__':
    app.run(debug=True, port=5000)