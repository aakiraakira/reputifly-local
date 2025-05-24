from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import subprocess

app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.get_json() or {}
    q = data.get('query','').strip()
    if not q:
        return jsonify(error="No query provided"), 400

    # call your map_scrape.py as a subprocess and capture its stdout
    try:
        result = subprocess.run(
            ['python','map_scrape.py', q, '--headless'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, timeout=120
        )
    except Exception as e:
        return jsonify(error=str(e)), 500

    if result.returncode != 0:
        return jsonify(error=result.stderr.splitlines()[-1]), 500

    # map_scrape.py prints the filename of the dump
    dump_file = result.stdout.strip()
    try:
        with open(dump_file, encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        return jsonify(error="Could not find output file"), 500

    return jsonify(results=text)
