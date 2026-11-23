import logging
import os
import threading
import webbrowser
from data import compute_route_stats, parse_uploaded_text, serialize_records
from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from map_builder import build_initial_page

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app)
logging.getLogger("werkzeug").setLevel(logging.ERROR)


@app.route("/")
def index():
  return build_initial_page()


@app.route("/api/parse", methods=["POST"])
def api_parse():
  data = request.get_json(silent=True) or {}
  raw_text = data.get("content", "")
  file_type = data.get("file_type", "csv").lower()

  try:
    records, stats = parse_uploaded_text(raw_text, file_type)
    return jsonify({"records": records, "stats": stats}), 200
  except Exception as e:
    return jsonify({"error": str(e)}), 400


@app.route("/api/stats", methods=["POST"])
def api_stats():
  data = request.get_json(silent=True) or {}
  records = data.get("records", [])
  return jsonify(compute_route_stats(records)), 200


@app.route("/api/export", methods=["POST"])
def api_export():
  data = request.get_json(silent=True) or {}
  records = data.get("records", [])
  file_type = data.get("file_type", "csv").lower()
  formatted_text = serialize_records(records, file_type)
  return Response(formatted_text, mimetype="text/plain; charset=utf-8")


@app.route("/api/save", methods=["POST"])
def api_save():
  data = request.get_json(silent=True) or {}
  records = data.get("records", [])
  save_path = os.path.basename(data.get("filename") or "dispatch_route.csv")
  file_type = "json" if save_path.lower().endswith(".json") else "csv"

  try:
    formatted_text = serialize_records(records, file_type)
    with open(save_path, mode="w", newline="", encoding="utf-8") as f:
      f.write(formatted_text)

    return jsonify({"saved_path": save_path, "count": len(records)}), 200
  except Exception as e:
    return jsonify({"error": str(e)}), 500


@app.route("/heartbeat")
def heartbeat():
  return "ok", 200


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 8000))
  is_render = "RENDER" in os.environ

  if not is_render:
    url = f"http://localhost:{port}/"
    print(f"GeoRoute Studio running locally at {url} (Press Ctrl+C to stop)")
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()

  try:
    app.run(
        host="0.0.0.0" if is_render else "127.0.0.1",
        port=port,
        debug=False,
        use_reloader=False,
    )
  except KeyboardInterrupt:
    print("\nShutting down GeoRoute Studio... Goodbye!")
