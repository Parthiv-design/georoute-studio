import json
import os


def build_overlay_html(map_var_name, initial_records=None):
  theme_config = {
      "light": {
          "label": "Dark",
          "icon": "&#9790;",
          "tileUrl": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
          "attribution": "&copy; OpenStreetMap contributors",
      },
      "dark": {
          "label": "Light",
          "icon": "&#9728;",
          "tileUrl": (
              "https://{s}://{z}/{x}/{y}{r}.png"
          ),
          "attribution": "&copy; OpenStreetMap &copy; CARTO",
      },
  }

  ui_context = {
      "mapVarName": map_var_name,
      "initialRecords": initial_records or [],
      "defaultSaveName": "dispatch_route.csv",
      "themes": theme_config,
  }

  overlay_path = os.path.join(
      os.path.dirname(__file__), "static", "overlay.html"
  )
  with open(overlay_path, mode="r", encoding="utf-8") as f:
    markup = f.read()

  return f"""
    <link rel="stylesheet" href="/static/style.css">
    {markup}
    <script>
        window.GEOROUTE_CONFIG = {json.dumps(ui_context)};
    </script>
    <script src="/static/actions.js"></script>
    <script src="/static/map_events.js"></script>
    """
