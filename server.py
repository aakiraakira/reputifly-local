from flask             import Flask, request, jsonify, send_from_directory
from flask_cors        import CORS
import subprocess, os

app = Flask(
  __name__,
  static_folder="frontend",      # <- your frontend dir
  static_url_path=""             # <- serve at root
)
CORS(app)

# 1) Serve your front end:
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def frontend(path):
    file_path = os.path.join(app.static_folder, path)
    if path and os.path.exists(file_path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")

# 2) Your existing /scrape API:
@app.route("/scrape", methods=["POST"])
def scrape():
    q = request.json.get("query", "").strip()
    if not q:
        return jsonify(error="Missing query"), 400

    # run your map_scrape.py
    cmd = ["python", "map_scrape.py", q, "--headless"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        return jsonify(error=proc.stderr), 500

    # read the dump file
    fname = "".join(c if c.isalnum() else "_" for c in q.lower()) + "_dump.txt"
    if not os.path.exists(fname):
        return jsonify(error="Dump not found"), 500

    return jsonify(results=open(fname,encoding="utf8").read())

if __name__=="__main__":
    app.run(host="0.0.0.0", port=3000)
