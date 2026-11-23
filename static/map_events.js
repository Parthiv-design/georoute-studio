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

function fitAllPins() {
    const mapObj = window[UI_CONTEXT.mapVarName];
    if (!mapObj || COORDS_DATA.length === 0) return;
    const bounds = COORDS_DATA.map(r => [r.latitude, r.longitude]);
    mapObj.fitBounds(bounds, { padding: [40, 40] });
}

function toggleAddPinMode(forceState = null) {
    addPinMode = forceState !== null ? forceState : !addPinMode;
    const btn = document.getElementById('addPinModeBtn');
    const mapObj = window[UI_CONTEXT.mapVarName];
    if (addPinMode) {
        btn.classList.add('btn-active');
        if (mapObj) mapObj.getContainer().style.cursor = 'crosshair';
        showToast('Click anywhere on the map to place a stop');
    } else {
        btn.classList.remove('btn-active');
        if (mapObj) mapObj.getContainer().style.cursor = '';
    }
}

function zoomToPin(item, rowEl) {
    document.querySelectorAll('.coord-row').forEach(r => r.classList.remove('active-row'));
    rowEl.classList.add('active-row');

    const mapObj = window[UI_CONTEXT.mapVarName];
    const markerObj = markerMap[item.point];
    if (!mapObj || !markerObj) return;

    if (activeMarkersLayer && typeof activeMarkersLayer.zoomToShowLayer === 'function') {
        activeMarkersLayer.zoomToShowLayer(markerObj, () => markerObj.openPopup());
    } else {
        mapObj.flyTo([item.latitude, item.longitude], 12, { animate: true, duration: 1.0 });
        setTimeout(() => markerObj.openPopup(), 1050);
    }
}

window.addEventListener('load', () => {
    const saveBtn = document.getElementById('saveDiskBtn');
    if (saveBtn) saveBtn.title = `Save route manifest to ${UI_CONTEXT.defaultSaveName}`;

    updateStatusAndStats();
    renderTable();
    redrawRoutePolyline();

    const mapObj = window[UI_CONTEXT.mapVarName];
    if (mapObj) {
        // Start directly in Place Stop mode on a clean canvas
        toggleAddPinMode(true);

        mapObj.on('click', (e) => {
            if (!addPinMode) return;

            const lat = Number(e.latlng.lat.toFixed(4));
            const lon = Number(e.latlng.lng.toFixed(4));
            const nextNum = COORDS_DATA.length + 1;

            COORDS_DATA.push({
                point: nextNum,
                label: `Stop #${nextNum}`,
                latitude: lat,
                longitude: lon
            });

            rebuildAllMarkers();
            if (markerMap[nextNum]) {
                markerMap[nextNum].openPopup();
            }
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
        if (addPinMode) toggleAddPinMode(false);
    }
});

