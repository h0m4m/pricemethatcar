from flask import Flask, request, jsonify, render_template
import uuid
import asyncio
import nest_asyncio
import threading

from scraper import crawl_domain

nest_asyncio.apply()

SUPPORTED_DOMAINS = [
    "https://www.rotanastar.ae/",
    "https://phantomrentcar.com/",
    "https://mkrentacar.com/",
    "https://superiorrental.ae/",
    # "https://octane.rent/",
    "https://www.uptowndxb.com/",
    "https://www.bevip.ae/",
    "https://xcarrental.com/",
    "https://ferrorental.com/",
    "https://mtn-rentacar.com/",
    "https://www.selyarentacar.com/",
    "https://firstsupercarrental.com/"
]

app = Flask(__name__)
TASKS = {}  # job_id -> {"status": "pending"|"done"|"error", "result": dict}

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/scrape', methods=['POST'])
def create_scrape_job():
    data = request.get_json()
    car_queries = data.get('cars', [])
    job_id = str(uuid.uuid4())
    TASKS[job_id] = {"status": "pending", "result": None}

    threading.Thread(target=lambda: asyncio.run(run_scrape_job(job_id, car_queries))).start()

    return jsonify({"job_id": job_id}), 202


@app.route('/scrape-status/<job_id>', methods=['GET'])
def check_scrape_status(job_id):
    task = TASKS.get(job_id)
    if not task:
        return jsonify({"error": "Invalid job ID"}), 404

    return jsonify({
        "status": task["status"],
        "result": task["result"] if task["status"] == "done" else None
    })


async def run_scrape_job(job_id, car_queries):
    try:
        async def scrape_all():
            tasks = [crawl_domain(domain, car_queries) for domain in SUPPORTED_DOMAINS]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            merged = {}
            for result in results:
                if isinstance(result, dict):
                    merged.update(result)
            return merged

        results = await scrape_all()
        TASKS[job_id] = {"status": "done", "result": results}
    except Exception as e:
        print(f"[ERROR] Scrape job failed: {e}")
        TASKS[job_id] = {"status": "error", "result": str(e)}


if __name__ == '__main__':
    app.run(debug=True, port=5000)