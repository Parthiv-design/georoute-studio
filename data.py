import base64
import csv
import io
import itertools
import json
import math


def get_first_valid(mapping, keys):
  for key in keys:
    if key in mapping and mapping[key] not in (None, ""):
      return mapping[key]
  return None


def calculate_route_km(records):
  if len(records) < 2:
    return 0.0

  total_km = 0.0
  earth_radius_km = 6371.0

  for i in range(len(records) - 1):
    lat1 = math.radians(float(records[i]["latitude"]))
    lon1 = math.radians(float(records[i]["longitude"]))
    lat2 = math.radians(float(records[i + 1]["latitude"]))
    lon2 = math.radians(float(records[i + 1]["longitude"]))

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    total_km += earth_radius_km * c

  return round(total_km, 2)


def compute_route_stats(records):
  north = sum(1 for r in records if float(r["latitude"]) >= 0)
  south = len(records) - north
  east = sum(1 for r in records if float(r["longitude"]) >= 0)
  west = len(records) - east

  return {
      "count": len(records),
      "route_km": calculate_route_km(records),
      "north": north,
      "south": south,
      "east": east,
      "west": west,
  }


def decode_shared_route(encoded_str):
  """Decode a URL-safe Base64 ?route=... string directly on the server."""
  if not encoded_str:
    return []
  try:
    padded = encoded_str + "=" * (-len(encoded_str) % 4)
    raw_bytes = base64.urlsafe_b64decode(padded.encode("ascii"))
    compact = json.loads(raw_bytes.decode("utf-8"))

    records = []
    for idx, entry in enumerate(compact):
      lat, lon = float(entry[0]), float(entry[1])
      label = (
          str(entry[2])
          if len(entry) > 2 and entry[2]
          else f"Stop #{idx + 1}"
      )
      records.append({
          "point": idx + 1,
          "label": label,
          "latitude": lat,
          "longitude": lon,
      })
    return records
  except Exception:
    return []


def parse_uploaded_text(raw_text, file_type):
  latitude_list = []
  longitude_list = []
  labels_list = []

  if file_type == "csv":
    reader = csv.DictReader(io.StringIO(raw_text))
    for row in reader:
      lat_val = get_first_valid(row, ["latitude", "lat", "Latitude", "LAT"])
      lon_val = get_first_valid(
          row, ["longitude", "long", "lon", "lng", "Longitude", "LON", "LNG"]
      )
      label_val = get_first_valid(
          row, ["name", "label", "stop_name", "city", "title", "Name"]
      )
      latitude_list.append(float(lat_val) if lat_val is not None else None)
      longitude_list.append(float(lon_val) if lon_val is not None else None)
      labels_list.append(str(label_val) if label_val is not None else "")

  elif file_type == "json":
    raw = json.loads(raw_text)
    items = (
        raw
        if isinstance(raw, list)
        else (raw.get("records") or raw.get("locations") or [])
    )
    for item in items:
      lat_val = get_first_valid(item, ["latitude", "lat", "Latitude", "LAT"])
      lon_val = get_first_valid(
          item, ["longitude", "long", "lon", "lng", "Longitude", "LON", "LNG"]
      )
      label_val = get_first_valid(
          item, ["name", "label", "stop_name", "city", "title", "Name"]
      )
      latitude_list.append(float(lat_val) if lat_val is not None else None)
      longitude_list.append(float(lon_val) if lon_val is not None else None)
      labels_list.append(str(label_val) if label_val is not None else "")

  records = []
  for lat, lon, label in itertools.zip_longest(
      latitude_list, longitude_list, labels_list, fillvalue=None
  ):
    if lat is None or lon is None:
      continue
    idx = len(records) + 1
    records.append({
        "point": idx,
        "label": label if label else f"Stop #{idx}",
        "latitude": lat,
        "longitude": lon,
    })

  return records, compute_route_stats(records)


def serialize_records(records, file_type):
  if file_type == "json":
    clean = [
        {
            "stop": r.get("point", i + 1),
            "label": r.get("label") or f"Stop #{i + 1}",
            "latitude": r["latitude"],
            "longitude": r["longitude"],
        }
        for i, r in enumerate(records)
    ]
    return json.dumps(clean, indent=2)

  output = io.StringIO()
  writer = csv.writer(output)
  writer.writerow(["stop", "label", "latitude", "longitude"])
  for i, r in enumerate(records):
    writer.writerow([
        r.get("point", i + 1),
        r.get("label") or f"Stop #{i + 1}",
        r["latitude"],
        r["longitude"],
    ])
  return output.getvalue()
