def get_ui_map_events_js():
  """Return JS handling Leaflet route polylines, layer refreshes, flyTo, map clicks, and heartbeat."""
  return """
        function redrawRoutePolyline() {
            const mapObj = window[UI_CONTEXT.mapVarName];
            if (!mapObj) return;

            if (routePolyline) {
                mapObj.removeLayer(routePolyline);
                routePolyline = null;
            }
            if (!showRouteLine || COORDS_DATA.length < 2) return;

            const latlngs = COORDS_DATA.map(r => [r.latitude, r.longitude]);
            routePolyline = L.polyline(latlngs, {
                color: '#2563eb',
                weight: 3,
                opacity: 0.75,
                dashArray: '6, 6'
            }).addTo(mapObj);
        }

        function toggleRouteLine() {
            showRouteLine = !showRouteLine;
            document.getElementById('routeLineBtn').classList.toggle('btn-active', showRouteLine);
            redrawRoutePolyline();
        }

        async function refreshMapLayer() {
            const countInput = document.getElementById('pointCountInput');
            const customCount = countInput && countInput.value ? `?count=${encodeURIComponent(countInput.value)}` : '';

            const res = await fetch(`/api/refresh${customCount}`, { cache: 'no-store' });
            const data = await res.json();
            const mapObj = window[UI_CONTEXT.mapVarName];

            if (window[currentLayerVar]) mapObj.removeLayer(window[currentLayerVar]);
            if (customUserLayer) {
                mapObj.removeLayer(customUserLayer);
                customUserLayer = null;
                customMarkers = {};
            }

            window[data.temp_map_var] = mapObj;
            new Function(data.layer_script)();

            COORDS_DATA = data.records;
            currentLayerVar = data.layer_var;
            currentIsClustered = data.is_clustered;

            updateStatusAndStats();
            redrawRoutePolyline();
            renderTable();
            fitAllPins();
            showToast(`Loaded ${COORDS_DATA.length} stops`);
        }

        function fitAllPins() {
            const mapObj = window[UI_CONTEXT.mapVarName];
            if (!mapObj || COORDS_DATA.length === 0) return;
            const bounds = COORDS_DATA.map(r => [r.latitude, r.longitude]);
            mapObj.fitBounds(bounds, { padding: [40, 40] });
        }

        function toggleAddPinMode() {
            addPinMode = !addPinMode;
            const btn = document.getElementById('addPinModeBtn');
            const mapObj = window[UI_CONTEXT.mapVarName];
            if (addPinMode) {
                btn.classList.add('btn-active');
                mapObj.getContainer().style.cursor = 'crosshair';
                showToast('Click anywhere on the map to append a stop');
            } else {
                btn.classList.remove('btn-active');
                mapObj.getContainer().style.cursor = '';
            }
        }

        function zoomToPin(item, rowEl) {
            document.querySelectorAll('.coord-row').forEach(r => r.classList.remove('active-row'));
            rowEl.classList.add('active-row');

            const mapObj = window[UI_CONTEXT.mapVarName];
            if (!mapObj) return;

            if (item.custom && customMarkers[item.point]) {
                const m = customMarkers[item.point];
                mapObj.flyTo([item.latitude, item.longitude], 12, { animate: true, duration: 1.0 });
                setTimeout(() => m.openPopup(), 1050);
                return;
            }

            const layerObj = window[currentLayerVar];
            const markerObj = window[item.marker_var];
            if (!markerObj) return;

            if (currentIsClustered && layerObj && typeof layerObj.zoomToShowLayer === 'function') {
                layerObj.zoomToShowLayer(markerObj, () => markerObj.openPopup());
            } else {
                mapObj.flyTo([item.latitude, item.longitude], 12, { animate: true, duration: 1.0 });
                setTimeout(() => markerObj.openPopup(), 1050);
            }
        }

        window.addEventListener('load', () => {
            renderTable();
            redrawRoutePolyline();

            const mapObj = window[UI_CONTEXT.mapVarName];
            if (mapObj) {
                mapObj.on('click', (e) => {
                    if (!addPinMode) return;
                    if (!customUserLayer) customUserLayer = L.layerGroup().addTo(mapObj);

                    const lat = Number(e.latlng.lat.toFixed(4));
                    const lon = Number(e.latlng.lng.toFixed(4));
                    const nextNum = COORDS_DATA.length + 1;
                    const label = `Waypoint #${nextNum}`;

                    const marker = L.marker([lat, lon])
                        .bindPopup(`<strong>${label}</strong><br>Lat: ${lat}<br>Lon: ${lon}`)
                        .addTo(customUserLayer)
                        .openPopup();

                    customMarkers[nextNum] = marker;
                    COORDS_DATA.push({
                        point: nextNum,
                        label: label,
                        latitude: lat,
                        longitude: lon,
                        custom: true
                    });
                    updateStatusAndStats();
                    redrawRoutePolyline();
                    renderTable();
                });
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                document.getElementById('coordsDrawer').style.display = 'none';
                document.getElementById('drawerToggleBtn').classList.remove('btn-active');
                if (addPinMode) toggleAddPinMode();
            }
        });

        setInterval(() => {
            fetch('/heartbeat', { cache: 'no-store' })
                .then(res => { if (!res.ok) throw new Error(); })
                .catch(() => {
                    window.open('', '_self', '');
                    window.close();
                    document.body.innerHTML = `<div style="display:flex;height:100vh;align-items:center;justify-content:center;font-family:system-ui;"><h2>GeoRoute Studio Server Stopped</h2></div>`;
                });
        }, 1500);
    """
