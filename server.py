# server.py
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import subprocess, os

app = Flask(__name__, static_folder="frontend", static_url_path="")
CORS(app)

# serve your React-style static site
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

# POST /scrape  → runs your map_scrape.py & returns its dump
@app.route("/scrape", methods=["POST"])
def scrape():
    q = request.json.get("query", "").strip()
    if not q:
        return jsonify(error="Missing query"), 400

    # call your existing scraper
    # note: we capture stdout so we can find the dump filename
    cmd = ["python", "map_scrape.py", q, "--headless"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        return jsonify(error=proc.stderr.strip()), 500

    # map_scrape.py prints the dump filename when it finishes:
    fname = proc.stdout.strip()
    if not os.path.exists(fname):
        return jsonify(error="Dump file missing"), 500

    with open(fname, encoding="utf-8") as f:
        data = f.read()

    # (optional) clean up that dump file
    try:
        os.remove(fname)
    except:
        pass

    return jsonify(results=data)
    

if __name__ == "__main__":
    # pick up the port Render hands us
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
