import folium
from folium.plugins import MarkerCluster
from ui import build_overlay_html


def build_initial_page():
  """Build a clean, empty GeoRoute Studio map canvas."""
  m = folium.Map(location=[51.0447, -114.0719], zoom_start=11)

  # Pre-load Leaflet.markercluster assets so large CSV/JSON uploads cluster smoothly
  MarkerCluster().add_to(m)

  overlay_html = build_overlay_html(map_var_name=m.get_name())
  m.get_root().html.add_child(folium.Element(overlay_html))

  print("Built clean GeoRoute Studio canvas (0 stops)")
  return m.get_root().render()
