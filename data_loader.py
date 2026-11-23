import csv
import itertools
import json
import math
import os


def get_first_valid(mapping, keys):
  """Safely retrieve a value without treating 0 or 0.0 as missing."""
  for key in keys:
    if key in mapping and mapping[key] not in (None, ""):
      return mapping[key]
  return None


def calculate_route_km(records):
  """Compute total sequential Haversine distance in kilometers across all stops."""
  if len(records) < 2:
    return 0.0

  total_km = 0.0
  earth_radius_km = 6371.0

  for i in range(len(records) - 1):
    lat1 = math.radians(records[i]["latitude"])
    lon1 = math.radians(records[i]["longitude"])
    lat2 = math.radians(records[i + 1]["latitude"])
    lon2 = math.radians(records[i + 1]["longitude"])

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    total_km += earth_radius_km * c

  return round(total_km, 2)


def load_coordinates(target_file=None):
  """Load stops from a CSV/JSON manifest, or return an empty canvas for manual placement."""
  if not target_file:
    return [], "Blank Route"

  latitude_list = []
  longitude_list = []
  labels_list = []

  if target_file.lower().endswith(".csv"):
    status_text = f"Manifest: {os.path.basename(target_file)}"
    with open(target_file, mode="r", newline="", encoding="utf-8") as f:
      reader = csv.DictReader(f)
      for row in reader:
        lat_val = get_first_valid(row, ["latitude", "lat", "Latitude", "LAT"])
        lon_val = get_first_valid(
            row, ["longitude", "long", "lon", "lng", "Longitude", "LON", "LNG"]
        )
        label_val = get_first_valid(
            row, ["name", "label", "stop", "city", "title", "Name"]
        )
        latitude_list.append(float(lat_val) if lat_val is not None else None)
        longitude_list.append(float(lon_val) if lon_val is not None else None)
        labels_list.append(str(label_val) if label_val is not None else "")

  elif target_file.lower().endswith(".json"):
    status_text = f"Manifest: {os.path.basename(target_file)}"
    with open(target_file, mode="r", encoding="utf-8") as f:
      data = json.load(f)
      for item in data:
        lat_val = get_first_valid(item, ["latitude", "lat", "Latitude", "LAT"])
        lon_val = get_first_valid(
            item, ["longitude", "long", "lon", "lng", "Longitude", "LON", "LNG"]
        )
        label_val = get_first_valid(
            item, ["name", "label", "stop", "city", "title", "Name"]
        )
        latitude_list.append(float(lat_val) if lat_val is not None else None)
        longitude_list.append(float(lon_val) if lon_val is not None else None)
        labels_list.append(str(label_val) if label_val is not None else "")
  else:
    return [], "Blank Route"

  records = []
  for i, (lat, long, label) in enumerate(
      itertools.zip_longest(
          latitude_list, longitude_list, labels_list, fillvalue=None
      )
  ):
    if lat is None or long is None:
      continue
    records.append({
        "point": i + 1,
        "label": label if label else f"Stop #{i + 1}",
        "latitude": lat,
        "longitude": long,
    })

  return records, status_text
