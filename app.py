# app.py
from flask import Flask, request, jsonify, render_template
from tasks import run_scrape_job

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def start_scrape():
    data = request.get_json()
    car_queries = data.get("cars", [])
    job = run_scrape_job.delay(car_queries)
    return jsonify({"job_id": job.id}), 202

@app.route('/scrape-status/<job_id>', methods=['GET'])
def check_scrape_status(job_id):
    job = run_scrape_job.AsyncResult(job_id)
    if job.state == "PENDING":
        return jsonify({"status": "pending"})
    elif job.state == "FAILURE":
        return jsonify({"status": "error", "result": str(job.result)})
    elif job.state == "SUCCESS":
        return jsonify({"status": "done", "result": job.result})
    else:
        return jsonify({"status": job.state})