/**
 * mapa.js — Leaflet map initialization with geolocation for health units.
 *
 * Loads units from the data injected by the server into window.UNIDADES.
 * Detects user position via Geolocation API and highlights the nearest unit.
 * "Como Chegar" button opens Google Maps with directions from user's position.
 */

(function () {
    "use strict";

    // Icon colors per unit type
    const ICON_COLORS = {
        ubs:          { bg: "#16a34a", border: "#14532d", emoji: "🏥" },
        upa:          { bg: "#d97706", border: "#92400e", emoji: "🚑" },
        hospital:     { bg: "#1d4ed8", border: "#1e3a8a", emoji: "🏨" },
        especializado:{ bg: "#7c3aed", border: "#4c1d95", emoji: "🔬" },
    };

    const TYPE_LABELS = {
        ubs:          "UBS — Posto de Saúde",
        upa:          "UPA 24h",
        hospital:     "Hospital de Urgência",
        especializado:"Centro Especializado",
    };

    /**
     * Builds a custom Leaflet DivIcon for a given unit type and optional highlight.
     * @param {string} tipo - Unit type key
     * @param {boolean} highlight - Whether to apply a highlight ring
     */
    function buildIcon(tipo, highlight) {
        const cfg = ICON_COLORS[tipo] || ICON_COLORS.ubs;
        const size = highlight ? 44 : 36;
        const ring = highlight ? `box-shadow:0 0 0 4px ${cfg.bg}55,0 0 0 8px ${cfg.bg}22;` : "";
        return L.divIcon({
            className: "",
            html: `<div style="width:${size}px;height:${size}px;background:${cfg.bg};border:3px solid ${cfg.border};border-radius:50% 50% 50% 0;transform:rotate(-45deg);display:flex;align-items:center;justify-content:center;${ring}">
                       <span style="transform:rotate(45deg);font-size:${highlight ? 18 : 14}px;">${cfg.emoji}</span>
                   </div>`,
            iconSize: [size, size],
            iconAnchor: [size / 2, size],
            popupAnchor: [0, -size],
        });
    }

    /**
     * Calculates the Haversine distance between two lat/lng pairs in km.
     * @param {number} lat1
     * @param {number} lon1
     * @param {number} lat2
     * @param {number} lon2
     * @returns {number}
     */
    function haversine(lat1, lon1, lat2, lon2) {
        const R = 6371;
        const dLat = ((lat2 - lat1) * Math.PI) / 180;
        const dLon = ((lon2 - lon1) * Math.PI) / 180;
        const a =
            Math.sin(dLat / 2) ** 2 +
            Math.cos((lat1 * Math.PI) / 180) *
                Math.cos((lat2 * Math.PI) / 180) *
                Math.sin(dLon / 2) ** 2;
        return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    }

    /**
     * Builds the popup HTML for a given unit with an optional "Como Chegar" URL.
     * @param {Object} u - Unit object
     * @param {string|null} routeUrl - Google Maps directions URL
     * @param {number|null} distKm - Distance in km (null if unknown)
     */
    function buildPopup(u, routeUrl, distKm) {
        const cfg = ICON_COLORS[u.tipo] || ICON_COLORS.ubs;
        const distLabel = distKm !== null ? `<p style="margin:4px 0;font-size:0.85rem;color:#64748b;">📍 ~${distKm.toFixed(1)} km de você</p>` : "";
        const btnHtml = routeUrl
            ? `<a href="${routeUrl}" target="_blank" rel="noopener"
                  style="display:inline-flex;align-items:center;gap:6px;margin-top:10px;padding:10px 16px;
                         background:${cfg.bg};color:#fff;border-radius:10px;font-weight:700;font-size:0.9rem;
                         text-decoration:none;box-shadow:0 2px 8px rgba(0,0,0,0.2);">
                  🗺️ Como Chegar
               </a>`
            : `<a href="https://www.google.com/maps/search/${encodeURIComponent(u.nome + ' ' + u.endereco)}" target="_blank" rel="noopener"
                  style="display:inline-flex;align-items:center;gap:6px;margin-top:10px;padding:10px 16px;
                         background:${cfg.bg};color:#fff;border-radius:10px;font-weight:700;font-size:0.9rem;
                         text-decoration:none;box-shadow:0 2px 8px rgba(0,0,0,0.2);">
                  🔍 Ver no Google Maps
               </a>`;

        return `<div style="font-family:'Nunito',sans-serif;min-width:220px;">
                    <p style="margin:0 0 4px;font-size:0.7rem;font-weight:700;text-transform:uppercase;color:${cfg.bg};">${TYPE_LABELS[u.tipo] || u.tipo}</p>
                    <h3 style="margin:0 0 6px;font-size:1rem;font-weight:900;color:#1e293b;">${u.nome}</h3>
                    <p style="margin:0 0 2px;font-size:0.85rem;color:#475569;">📍 ${u.endereco}</p>
                    <p style="margin:0;font-size:0.85rem;color:#475569;">📞 <a href="tel:${u.telefone}" style="color:#1d4ed8;">${u.telefone}</a></p>
                    <p style="margin:4px 0 0;font-size:0.85rem;color:#475569;">🕐 ${u.horario}</p>
                    ${distLabel}
                    ${btnHtml}
                </div>`;
    }

    window.addEventListener("DOMContentLoaded", function () {
        const unidades = window.UNIDADES || [];
        if (!unidades.length) return;

        // Center on Teresina by default
        const map = L.map("map", { zoomControl: true }).setView([-5.0921, -42.8032], 13);

        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution:
                '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
            maxZoom: 19,
        }).addTo(map);

        // Add markers for all units (no user location yet)
        const markers = unidades.map((u) => {
            const marker = L.marker([u.lat, u.lng], { icon: buildIcon(u.tipo, false) }).addTo(map);
            marker.bindPopup(buildPopup(u, null, null));
            return { unit: u, marker };
        });

        // Status bar
        const statusEl = document.getElementById("mapa-status");

        // Filter buttons
        document.querySelectorAll(".filtro-btn").forEach((btn) => {
            btn.addEventListener("click", function () {
                const tipo = this.dataset.tipo;
                document.querySelectorAll(".filtro-btn").forEach((b) => b.classList.remove("ativo"));
                this.classList.add("ativo");
                markers.forEach(({ unit, marker }) => {
                    if (tipo === "todos" || unit.tipo === tipo) {
                        marker.addTo(map);
                    } else {
                        map.removeLayer(marker);
                    }
                });
            });
        });

        // Geolocation
        if (!navigator.geolocation) {
            if (statusEl) statusEl.textContent = "Geolocalização não disponível no seu navegador.";
            return;
        }

        if (statusEl) {
            statusEl.innerHTML = '<span class="spinner"></span> Obtendo sua localização...';
        }

        navigator.geolocation.getCurrentPosition(
            function (pos) {
                const userLat = pos.coords.latitude;
                const userLng = pos.coords.longitude;

                // User marker
                const userIcon = L.divIcon({
                    className: "",
                    html: `<div style="width:16px;height:16px;background:#ef4444;border:3px solid #fff;border-radius:50%;box-shadow:0 0 0 4px rgba(239,68,68,0.3);"></div>`,
                    iconSize: [16, 16],
                    iconAnchor: [8, 8],
                });
                L.marker([userLat, userLng], { icon: userIcon })
                    .addTo(map)
                    .bindPopup("<b>Você está aqui!</b>")
                    .openPopup();

                map.setView([userLat, userLng], 14);

                // Find nearest unit
                let nearest = null;
                let nearestDist = Infinity;
                unidades.forEach((u) => {
                    const d = haversine(userLat, userLng, u.lat, u.lng);
                    if (d < nearestDist) {
                        nearestDist = d;
                        nearest = u;
                    }
                });

                // Update all markers with distances and route links
                markers.forEach(({ unit, marker }) => {
                    const dist = haversine(userLat, userLng, unit.lat, unit.lng);
                    const routeUrl = `https://www.google.com/maps/dir/${userLat},${userLng}/${unit.lat},${unit.lng}`;
                    const isNearest = nearest && unit.id === nearest.id;

                    marker.setIcon(buildIcon(unit.tipo, isNearest));
                    marker.setPopupContent(buildPopup(unit, routeUrl, dist));

                    if (isNearest) {
                        marker.openPopup();
                    }
                });

                if (statusEl && nearest) {
                    statusEl.innerHTML = `✅ Unidade mais próxima: <strong>${nearest.nome}</strong> (~${nearestDist.toFixed(1)} km)`;
                }
            },
            function (err) {
                console.warn("Geolocation error:", err.message);
                if (statusEl) {
                    statusEl.textContent = "Não foi possível obter sua localização. Use os filtros para encontrar uma unidade.";
                }
            },
            { timeout: 10000, maximumAge: 60000 }
        );
    });
})();
