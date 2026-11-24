import folium
from folium.plugins import MarkerCluster
from ui import build_overlay_html


def build_initial_page(initial_records=None):
  initial_records = initial_records or []
  m = folium.Map(location=[51.0447, -114.0719], zoom_start=11)

  # Pre-load Leaflet.markercluster assets
  MarkerCluster().add_to(m)

  if initial_records:
    lats = [r["latitude"] for r in initial_records]
    lons = [r["longitude"] for r in initial_records]
    m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])

  overlay_html = build_overlay_html(
      map_var_name=m.get_name(),
      initial_records=initial_records,
  )
  m.get_root().html.add_child(folium.Element(overlay_html))
  return m.get_root().render()
