from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os

app = Flask(__name__)
CORS(app)

@app.route("/scrape", methods=["POST"])
def scrape():
    data = request.get_json()
    q = data.get("query","").strip()
    if not q:
        return jsonify(error="Missing query"), 400

    # run scraper
    # note: require python on PATH; adjust to 'python3' if needed
    cmd = ["python", "map_scrape.py", q, "--headless"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        return jsonify(error=e.stderr or "Scraper failed"), 500

    # last line of stdout is the filename
    fname = result.stdout.strip().splitlines()[-1]
    if not os.path.exists(fname):
        return jsonify(error="Dump file missing"), 500

    with open(fname, encoding="utf-8") as f:
        content = f.read()
    # optional: delete the file after reading
    os.remove(fname)
    return jsonify(results=content)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
