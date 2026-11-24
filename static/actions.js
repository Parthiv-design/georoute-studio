const UI_CONTEXT = window.GEOROUTE_CONFIG;
let COORDS_DATA = [];
let loadedFileName = null;
let activeMarkersLayer = null;
let markerMap = {};
let routePolyline = null;
let showRouteLine = true;
let addPinMode = false;
let isDarkMode = false;
let customTileLayer = null;

function showToast(msg) {
    const toast = document.getElementById('toastBanner');
    toast.textContent = msg;
    toast.style.opacity = '1';
    clearTimeout(window._toastTimer);
    window._toastTimer = setTimeout(() => { toast.style.opacity = '0'; }, 2400);
}

async function updateStatusAndStats() {
    if (COORDS_DATA.length === 0) {
        document.getElementById('statusBadge').textContent = '0 stops • 0 km';
        document.getElementById('drawerTitle').textContent = 'Route Manifest (0 stops)';
        document.getElementById('geoStatsBar').innerHTML = '<span>Est. Path: 0 km</span><span>N:0 S:0 E:0 W:0</span>';
        return;
    }

    try {
        const res = await fetch('/api/stats', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ records: COORDS_DATA })
        });
        const stats = await res.json();
        document.getElementById('statusBadge').textContent = `${stats.count} stops • ${stats.route_km} km`;
        document.getElementById('drawerTitle').textContent = `Route Manifest (${stats.count} stops)`;
        document.getElementById('geoStatsBar').innerHTML = `
            <span>Est. Path: ${stats.route_km} km</span>
            <span>N:${stats.north} S:${stats.south} E:${stats.east} W:${stats.west}</span>
        `;
    } catch (err) {
        console.error('Stats sync error:', err);
    }
}

function rebuildAllMarkers() {
    const mapObj = window[UI_CONTEXT.mapVarName];
    if (!mapObj) return;

    if (activeMarkersLayer) {
        mapObj.removeLayer(activeMarkersLayer);
    }
    markerMap = {};

    const useCluster = COORDS_DATA.length >= 50 && typeof L.markerClusterGroup === 'function';
    activeMarkersLayer = useCluster ? L.markerClusterGroup() : L.layerGroup();

    COORDS_DATA.forEach(item => {
        const marker = L.marker([item.latitude, item.longitude])
            .bindPopup(`
                <div style="font-family: system-ui, sans-serif; min-width: 145px;">
                    <div style="font-size: 11px; font-weight: 700; color: #2563eb; text-transform: uppercase;">Stop #${item.point}</div>
                    <div style="font-weight: 700; color: #0f172a; margin-bottom: 4px;">${item.label}</div>
                    <div style="font-size: 12px; color: #475569;"><strong>Lat:</strong> ${item.latitude}<br><strong>Lon:</strong> ${item.longitude}</div>
                </div>
            `)
            .bindTooltip(`#${item.point} — ${item.label}`);

        activeMarkersLayer.addLayer(marker);
        markerMap[item.point] = marker;
    });

    activeMarkersLayer.addTo(mapObj);
}

function handleFileUpload(event, fileType) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (e) => {
        try {
            const res = await fetch('/api/parse', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    content: e.target.result,
                    file_type: fileType
                })
            });
            const data = await res.json();

            if (!res.ok) {
                showToast(`Error: ${data.error || 'Could not parse file'}`);
                return;
            }
            if (!data.records || data.records.length === 0) {
                showToast(`No valid coordinates found in ${file.name}`);
                return;
            }

            loadedFileName = file.name;
            COORDS_DATA = data.records;
            rebuildAllMarkers();
            await updateStatusAndStats();
            redrawRoutePolyline();
            renderTable();
            fitAllPins();
            showToast(`Loaded ${COORDS_DATA.length} stops from ${file.name}`);
        } catch (err) {
            showToast(`Failed to load ${file.name}`);
        } finally {
            event.target.value = '';
        }
    };
    reader.readAsText(file);
}

function deletePin(pointNum) {
    const idx = COORDS_DATA.findIndex(r => r.point === pointNum);
    if (idx === -1) return;

    COORDS_DATA.splice(idx, 1);
    COORDS_DATA.forEach((item, i) => {
        item.point = i + 1;
    });

    rebuildAllMarkers();
    updateStatusAndStats();
    redrawRoutePolyline();
    renderTable();
    showToast(`Removed stop #${pointNum}`);
}

function clearAllPins() {
    COORDS_DATA = [];
    loadedFileName = null;
    rebuildAllMarkers();
    updateStatusAndStats();
    redrawRoutePolyline();
    renderTable();
    showToast('Cleared all stops');
}

function toggleTheme() {
    isDarkMode = !isDarkMode;
    document.body.classList.toggle('dark-theme', isDarkMode);

    const theme = isDarkMode ? UI_CONTEXT.themes.dark : UI_CONTEXT.themes.light;
    const btn = document.getElementById('themeToggleBtn');
    btn.innerHTML = `${theme.icon} ${theme.label}`;

    const mapObj = window[UI_CONTEXT.mapVarName];
    if (!mapObj) return;

    if (customTileLayer) mapObj.removeLayer(customTileLayer);
    customTileLayer = L.tileLayer(theme.tileUrl, {
        attribution: theme.attribution,
        maxZoom: 19
    }).addTo(mapObj);
    customTileLayer.bringToBack();
}

function toggleCoordsDrawer() {
    const drawer = document.getElementById('coordsDrawer');
    const btn = document.getElementById('drawerToggleBtn');
    const isOpen = drawer.style.display === 'flex';
    drawer.style.display = isOpen ? 'none' : 'flex';
    btn.classList.toggle('btn-active', !isOpen);
}

function renderTable() {
    const query = (document.getElementById('coordSearchInput').value || '').trim().toLowerCase();
    const tbody = document.getElementById('coordsTableBody');
    tbody.innerHTML = '';

    if (COORDS_DATA.length === 0) {
        tbody.innerHTML = `<tr><td colspan="3" style="text-align:center;color:var(--ui-muted);padding:16px;">Click on the map to place stops, or use <strong>Load CSV / JSON</strong>.</td></tr>`;
        return;
    }

    const filtered = COORDS_DATA.filter(item =>
        String(item.point).includes(query) ||
        (item.label && item.label.toLowerCase().includes(query)) ||
        String(item.latitude).includes(query) ||
        String(item.longitude).includes(query)
    );

    filtered.forEach(item => {
        const tr = document.createElement('tr');
        tr.className = 'coord-row';
        const labelText = item.label ? `<div style="font-weight:600;">${item.label}</div>` : '';
        tr.innerHTML = `
            <td style="font-weight:700; color:#2563eb;">#${item.point}</td>
            <td>
                ${labelText}
                <div style="color:var(--ui-muted); font-size:11.5px;">${item.latitude}, ${item.longitude}</div>
            </td>
            <td>
                <div class="action-cell">
                    <button class="mini-btn copy-btn" title="Copy coordinates">Copy</button>
                    <button class="mini-btn mini-btn-del del-btn" title="Delete stop">&times;</button>
                </div>
            </td>
        `;
        tr.querySelector('.copy-btn').onclick = (e) => {
            e.stopPropagation();
            navigator.clipboard.writeText(`${item.latitude}, ${item.longitude}`);
            showToast(`Copied: ${item.latitude}, ${item.longitude}`);
        };
        tr.querySelector('.del-btn').onclick = (e) => {
            e.stopPropagation();
            deletePin(item.point);
        };
        tr.onclick = () => zoomToPin(item, tr);
        tbody.appendChild(tr);
    });
}

async function saveToDisk() {
    if (COORDS_DATA.length === 0) {
        showToast('Nothing to save — place or load stops first');
        return;
    }
    try {
        const res = await fetch('/api/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filename: loadedFileName || UI_CONTEXT.defaultSaveName,
                records: COORDS_DATA
            })
        });
        const result = await res.json();
        if (res.ok) {
            showToast(`Saved ${result.count} stops to ${result.saved_path}`);
        } else {
            showToast(`Save failed: ${result.error || 'Unknown error'}`);
        }
    } catch (err) {
        showToast('Failed to reach server to save manifest');
    }
}

async function exportFile(fileType) {
    if (COORDS_DATA.length === 0) {
        showToast('Nothing to export — place or load stops first');
        return;
    }
    try {
        const res = await fetch('/api/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file_type: fileType, records: COORDS_DATA })
        });
        const textContent = await res.text();
        const filename = fileType === 'json' ? 'dispatch_route.json' : 'dispatch_route.csv';
        const mimeType = fileType === 'json' ? 'application/json' : 'text/csv;charset=utf-8;';

        const blob = new Blob([textContent], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast(`Exported ${filename}`);
    } catch (err) {
        showToast(`Failed to export ${fileType.toUpperCase()}`);
    }
}

function downloadCSV() { exportFile('csv'); }
function downloadJSON() { exportFile('json'); }

function copyShareableLink() {
    if (COORDS_DATA.length === 0) {
        showToast('Place or load stops first to share a route');
        return;
    }

    // Compact format: [[lat, lon, label], ...] to keep URLs short
    const compact = COORDS_DATA.map(r => [
        Number(r.latitude),
        Number(r.longitude),
        r.label || `Stop #${r.point}`
    ]);

    // UTF-8 safe Base64 URL encoding
    const jsonStr = JSON.stringify(compact);
    const base64 = btoa(encodeURIComponent(jsonStr).replace(/%([0-9A-F]{2})/g,
        (_, p1) => String.fromCharCode('0x' + p1)
    )).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');

    const shareUrl = `${window.location.origin}${window.location.pathname}#route=${base64}`;
    window.history.replaceState(null, '', `#route=${base64}`);

    navigator.clipboard.writeText(shareUrl)
        .then(() => showToast('Shareable route link copied to clipboard!'))
        .catch(() => showToast('Route encoded in address bar — copy URL to share'));
}

function loadRouteFromUrl() {
    const hash = window.location.hash || '';
    if (!hash.startsWith('#route=')) return false;

    try {
        let base64 = hash.slice(7).replace(/-/g, '+').replace(/_/g, '/');
        while (base64.length % 4) base64 += '=';

        const binary = atob(base64);
        const percentEncoded = Array.from(binary)
            .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
            .join('');
        const compact = JSON.parse(decodeURIComponent(percentEncoded));

        if (!Array.isArray(compact) || compact.length === 0) return false;

        COORDS_DATA = compact.map((item, idx) => ({
            point: idx + 1,
            latitude: Number(item),
            longitude: Number(item),
            label: item ? String(item) : `Stop #${idx + 1}`
        }));

        rebuildAllMarkers();
        updateStatusAndStats();
        redrawRoutePolyline();
        renderTable();
        fitAllPins();
        showToast(`Loaded shared route (${COORDS_DATA.length} stops)`);
        return true;
    } catch (err) {
        console.error('Invalid share link:', err);
        showToast('Could not read shared route from URL');
        return false;
    }
}
