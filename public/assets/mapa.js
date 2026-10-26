// Mapa territorial (MapLibre GL): coropletas por distrito, circunscripciones, malla H3 y activos puntuales.
import { fmt, fmtCorto, PALETA, ROJO } from "./graficos.js";

const ESTILO = "https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json";
const RAMPA = ["#e3eef0", "#b3d1d6", "#78aab4", "#3f7d8c", "#1d5262"]; // secuencial de un solo tono: rojo de la bandera, claro→oscuro
const RAMPA_HEX = ["#dde9f7", "#a9c7ec", "#6fa1de", "#2a78d6", "#184f95"]; // segundo contexto secuencial: azul
const TIPOS = {
  "Centro financiero de ingreso alto": PALETA[3],
  "Núcleo denso de vivienda pública e ingreso bajo": PALETA[1],
  "Núcleo urbano denso de clase media": PALETA[0],
  "Suburbano de baja densidad": PALETA[2],
};
const LENTES = [
  { id: "ingreso_mediano_hogar_hkd_2025", nombre: "Ingreso", unidad: "HK$/mes · 2025", f: (v) => "HK$ " + fmtCorto(v) },
  { id: "densidad_hab_km2", nombre: "Densidad", unidad: "hab/km² · 2021", f: fmtCorto },
  { id: "pct_65_mas", nombre: "65+ años", unidad: "% de la población · 2021", f: (v) => fmt(v, 1) + " %" },
  { id: "pct_vivienda_publica_alquiler", nombre: "Vivienda pública", unidad: "% en vivienda pública de alquiler", f: (v) => fmt(v, 1) + " %" },
  { id: "paradas_por_10k_hab", nombre: "Transporte", unidad: "paradas por 10.000 hab", f: (v) => fmt(v, 1) },
  { id: "tipologia", nombre: "Tipología", unidad: "k-means sobre 6 variables", cat: true },
];

export async function iniciarMapa(G, estado, elegirDistrito) {
  const caja = document.getElementById("mapaLienzo");
  const aviso = document.getElementById("mapaAviso");
  if (!window.maplibregl) { aviso.style.display = "flex"; aviso.textContent = "No se pudo cargar la librería del mapa (MapLibre). Revisa tu conexión."; return null; }

  const [geo, dcca, hex] = await Promise.all(["geo", "geo_circunscripciones", "hex_h3_res8"].map((a) => fetch(`data/${a}.json`.replace("hex_h3_res8.json", "hex_h3_res8.geojson")).then((r) => r.json())));
  const distritos = geo.distritos;
  for (const f of distritos.features) Object.assign(f.properties, G.porCod[f.properties.codigo]);

  let estilo = ESTILO;
  try { const r = await fetch(ESTILO); if (!r.ok) throw 0; estilo = await r.json(); }
  catch { estilo = { version: 8, sources: {}, layers: [{ id: "fondo", type: "background", paint: { "background-color": "#eef0f2" } }] }; }

  const map = new maplibregl.Map({ container: caja, style: estilo, center: [114.14, 22.36], zoom: 9.6, pitch: 0, attributionControl: { compact: true }, cooperativeGestures: true });
  map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "bottom-right");
  await new Promise((ok) => map.on("load", ok));

  map.addSource("distritos", { type: "geojson", data: distritos, promoteId: "codigo" });
  map.addSource("dcca", { type: "geojson", data: dcca });
  map.addSource("hex", { type: "geojson", data: hex });
  const pts = (lista, lat = "lat", lon = "lon") => ({ type: "FeatureCollection", features: lista.map((p) => ({ type: "Feature", properties: p, geometry: { type: "Point", coordinates: [p[lon], p[lat]] } })) });
  map.addSource("mtr", { type: "geojson", data: pts(G.infraestructura.estaciones_mtr) });
  map.addSource("hosp", { type: "geojson", data: pts(G.infraestructura.hospitales) });
  map.addSource("hko", { type: "geojson", data: pts(G.sensores.estaciones_meteorologicas) });
  map.addSource("paradas", { type: "geojson", data: { type: "FeatureCollection", features: [] } });

  map.addLayer({ id: "dist-fill", type: "fill", source: "distritos", paint: { "fill-color": RAMPA[2], "fill-opacity": 0.78 } });
  map.addLayer({ id: "dist-3d", type: "fill-extrusion", source: "distritos", layout: { visibility: "none" }, paint: { "fill-extrusion-color": RAMPA[2], "fill-extrusion-height": 0, "fill-extrusion-opacity": 0.85 } });
  map.addLayer({ id: "hex", type: "fill", source: "hex", layout: { visibility: "none" }, paint: { "fill-color": ["interpolate", ["linear"], ["get", "parada_transporte"], 1, RAMPA_HEX[0], 3, RAMPA_HEX[1], 8, RAMPA_HEX[2], 15, RAMPA_HEX[3], 30, RAMPA_HEX[4]], "fill-opacity": 0.8, "fill-outline-color": "rgba(255,255,255,.7)" } });
  map.addLayer({ id: "dcca-line", type: "line", source: "dcca", layout: { visibility: "none" }, paint: { "line-color": "rgba(17,24,39,.25)", "line-width": 0.6 } });
  map.addLayer({ id: "dist-line", type: "line", source: "distritos", paint: { "line-color": "#ffffff", "line-width": 1.4 } });
  map.addLayer({ id: "dist-sel", type: "line", source: "distritos", filter: ["==", ["get", "codigo"], ""], paint: { "line-color": "#1f2933", "line-width": 3.2 } });
  map.addLayer({ id: "paradas", type: "circle", source: "paradas", layout: { visibility: "none" }, paint: { "circle-radius": ["interpolate", ["linear"], ["zoom"], 10, 1.2, 15, 3.5], "circle-color": "#4b5563", "circle-opacity": 0.65 } });
  map.addLayer({ id: "hko", type: "circle", source: "hko", layout: { visibility: "none" }, paint: { "circle-radius": 4.5, "circle-color": PALETA[2], "circle-stroke-color": "#ffffff", "circle-stroke-width": 1.5 } });
  map.addLayer({ id: "mtr", type: "circle", source: "mtr", paint: { "circle-radius": ["interpolate", ["linear"], ["zoom"], 9, 2.5, 14, 6], "circle-color": PALETA[0], "circle-stroke-color": "#ffffff", "circle-stroke-width": 1.8 } });
  map.addLayer({ id: "hosp", type: "circle", source: "hosp", paint: { "circle-radius": 6.5, "circle-color": "#1f2933", "circle-stroke-color": "#ffffff", "circle-stroke-width": 2.2 } });

  // etiquetas de distrito como marcadores HTML (no dependen de glifos del estilo base)
  const etiquetas = distritos.features.map((f) => {
    const e = document.createElement("div");
    e.style.cssText = "font:600 10.5px var(--sans);color:#1f2933;text-shadow:0 0 3px #fff,0 0 6px #fff,0 0 10px #fff;pointer-events:none;white-space:nowrap";
    e.textContent = f.properties.distrito_es;
    e.dataset.chico = f.properties.area_km2_oficial < 25 ? "1" : "";
    return new maplibregl.Marker({ element: e }).setLngLat([f.properties.centro_lon, f.properties.centro_lat]).addTo(map);
  });
  // los distritos urbanos pequeños solo muestran su nombre al acercarse (evita que se encimen)
  const ajustarEtiquetas = () => { const z = map.getZoom(); etiquetas.forEach((m) => { const e = m.getElement(); e.style.display = e.dataset.chico && z < 11.2 ? "none" : ""; }); };
  map.on("zoomend", ajustarEtiquetas); ajustarEtiquetas();

  // ---- lentes ----
  let lente = LENTES[0], tresD = false;
  const lentesEl = document.getElementById("lentes");
  lentesEl.innerHTML = LENTES.map((l, i) => `<button data-i="${i}" class="${i ? "" : "on"}">${l.nombre}</button>`).join("") + `<button data-3d="1">◭ 3D</button><button data-capas="1" class="solo-movil" style="display:none">☰ Capas</button>`;
  if (matchMedia("(max-width:860px)").matches) lentesEl.querySelector("[data-capas]").style.display = "";
  function aplicarLente() {
    let color;
    if (lente.cat) color = ["match", ["get", "tipologia"], ...Object.entries(TIPOS).flat(), "#cfd4da"];
    else {
      const vals = G.D.map((d) => d[lente.id]), mn = Math.min(...vals), mx = Math.max(...vals);
      color = ["interpolate", ["linear"], ["get", lente.id], ...RAMPA.flatMap((c, i) => [mn + (mx - mn) * i / (RAMPA.length - 1), c])];
      const alto = ["*", ["/", ["-", ["get", lente.id], mn], (mx - mn) || 1], 9000];
      map.setPaintProperty("dist-3d", "fill-extrusion-height", ["+", 300, alto]);
    }
    if (lente.cat) map.setPaintProperty("dist-3d", "fill-extrusion-height", 1500);
    map.setPaintProperty("dist-fill", "fill-color", color);
    map.setPaintProperty("dist-3d", "fill-extrusion-color", color);
    leyenda();
  }
  function leyenda() {
    const el = document.getElementById("leyendaMapa");
    if (lente.cat) {
      el.innerHTML = `<div style="color:#1f2933;margin-bottom:6px">Tipología de distrito</div>` + Object.entries(TIPOS).map(([t, c]) => `<div style="display:flex;gap:6px;align-items:center;margin-top:3px"><i style="width:10px;height:10px;border-radius:3px;background:${c}"></i>${t}</div>`).join("");
    } else {
      const vals = G.D.map((d) => d[lente.id]);
      el.innerHTML = `<div style="color:#1f2933">${lente.nombre}</div><div class="muted">${lente.unidad}</div><div class="rampa" style="background:linear-gradient(90deg,${RAMPA.join(",")})"></div><div class="ext"><span>${lente.f(Math.min(...vals))}</span><span>${lente.f(Math.max(...vals))}</span></div>`;
    }
    if (map.getLayoutProperty("hex", "visibility") === "visible") el.innerHTML += `<div style="margin-top:10px;color:#1f2933">Hexágonos H3</div><div class="muted">paradas por celda (~0,74 km²)</div><div class="rampa" style="background:linear-gradient(90deg,${RAMPA_HEX.join(",")})"></div><div class="ext"><span>1</span><span>30+</span></div>`;
  }
  lentesEl.addEventListener("click", (e) => {
    const b = e.target.closest("button"); if (!b) return;
    if (b.dataset.capas) { document.getElementById("mapaPanel").classList.toggle("oculto-movil"); return; }
    if (b.dataset["3d"]) {
      tresD = !tresD; b.classList.toggle("on", tresD);
      map.setLayoutProperty("dist-3d", "visibility", tresD ? "visible" : "none");
      map.setLayoutProperty("dist-fill", "visibility", tresD ? "none" : "visible");
      map.easeTo({ pitch: tresD ? 55 : 0, bearing: tresD ? -18 : 0, duration: 900 });
      return;
    }
    lente = LENTES[+b.dataset.i];
    lentesEl.querySelectorAll("[data-i]").forEach((x) => x.classList.toggle("on", x === b));
    aplicarLente(); ficha();
  });

  // ---- capas ----
  const CAPAS = [
    { id: "dist-fill", nombre: "Distritos (coropleta)", color: RAMPA[3], on: true, n: 18 },
    { id: "dcca-line", nombre: "Circunscripciones DCCA", color: "#cfd4da", on: false, n: 452 },
    { id: "hex", nombre: "Malla hexagonal H3", color: RAMPA_HEX[3], on: false, n: hex.features.length },
    { id: "mtr", nombre: "Estaciones MTR", color: PALETA[0], on: true, n: G.infraestructura.estaciones_mtr.length },
    { id: "hosp", nombre: "Hospitales con urgencias", color: "#1f2933", on: true, n: G.infraestructura.hospitales.length },
    { id: "hko", nombre: "Estaciones del Observatorio", color: PALETA[2], on: false, n: G.sensores.estaciones_meteorologicas.length },
    { id: "paradas", nombre: "Paradas de transporte", color: "#4b5563", on: false, n: G.panorama.kpis.paradas_transporte_publico },
  ];
  document.getElementById("capas").innerHTML = CAPAS.map((c) => `<label class="capa"><input type="checkbox" data-id="${c.id}" ${c.on ? "checked" : ""}><i style="background:${c.color}"></i>${c.nombre}<small>${fmt(c.n, 0)}</small></label>`).join("") +
    `<p class="mono muted" style="font-size:10px;margin:10px 0 0;line-height:1.4">Archivos: <b>geo.json</b> (F19, F22) · <b>geo_circunscripciones.json</b> (F19) · <b>hex_h3_res8.geojson</b> (F23–F25) · <b>infraestructura.json</b> (F23, F24) · <b>sensores.json</b> (F25) · <b>infraestructura_paradas.json</b> (F23). Mapa base © CARTO / OpenStreetMap.</p>`;
  let paradasCargadas = false;
  document.getElementById("capas").addEventListener("change", async (e) => {
    const id = e.target.dataset.id, on = e.target.checked;
    if (id === "paradas" && on && !paradasCargadas) {
      const p = await fetch("data/infraestructura_paradas.json").then((r) => r.json());
      const i = Object.fromEntries(p.columnas.map((c, k) => [c, k]));
      map.getSource("paradas").setData({ type: "FeatureCollection", features: p.filas.map((r) => ({ type: "Feature", properties: { nombre: r[i.nombre], modos: r[i.modos], n_rutas: r[i.n_rutas] }, geometry: { type: "Point", coordinates: [r[i.lon], r[i.lat]] } })) });
      paradasCargadas = true;
    }
    const capas = id === "dist-fill" ? ["dist-fill", ...(tresD ? ["dist-3d"] : [])] : [id];
    capas.forEach((c) => map.setLayoutProperty(c, "visibility", on ? "visible" : "none"));
    if (id === "hex") { map.setPaintProperty("dist-fill", "fill-opacity", on ? 0.18 : 0.72); leyenda(); }
  });

  // ---- ficha ----
  const fichaEl = document.getElementById("ficha");
  function ficha() {
    const d = G.porCod[estado.a];
    const fila = (v, l) => `<div><b>${v}</b><small>${l}</small></div>`;
    fichaEl.innerHTML = `<p class="ceja" style="margin:0">Ficha · ${lente.nombre.toLowerCase()}</p><h4 style="margin:2px 0 0;font-family:var(--titulo);font-size:18px">${d.distrito_es} <span class="muted" style="font-size:13px">${d.distrito_zh}</span></h4><span class="tipo-pill">${d.tipologia}</span>
      <div class="g">${fila(fmtCorto(d.poblacion_2025), "habitantes 2025")}${fila("HK$ " + fmtCorto(d.ingreso_mediano_hogar_hkd_2025), "ingreso mediano del hogar")}
      ${fila(fmtCorto(d.densidad_hab_km2), "hab/km²")}${fila(fmt(d.pct_65_mas, 1) + " %", "65 años o más")}
      ${fila(fmt(d.pct_vivienda_publica_alquiler, 1) + " %", "vivienda pública")}${fila(fmt(d.paradas_por_10k_hab, 1), "paradas/10k hab")}
      ${fila(d.paradas_metro_mtr, "estaciones MTR")}${fila(fmt(d.dist_media_hospital_km, 1) + " km", "dist. media urgencias")}</div>
      <p class="mono muted" style="font-size:10px;margin:8px 0 0">${d.n_circunscripciones} circunscripciones · ${fmt(d.area_km2_oficial, 1)} km² de tierra</p>`;
    map.setFilter("dist-sel", ["==", ["get", "codigo"], estado.a]);
  }

  // ---- interacción ----
  const popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 10 });
  const hover = (capa, html) => {
    map.on("mousemove", capa, (e) => { map.getCanvas().style.cursor = "pointer"; popup.setLngLat(e.lngLat).setHTML(html(e.features[0].properties)).addTo(map); });
    map.on("mouseleave", capa, () => { map.getCanvas().style.cursor = ""; popup.remove(); });
  };
  hover("dist-fill", (p) => `<b>${p.distrito_es}</b><br><span class="muted">${lente.nombre}: ${lente.cat ? p.tipologia : lente.f(p[lente.id])}</span>`);
  hover("dist-3d", (p) => `<b>${p.distrito_es}</b><br><span class="muted">${lente.nombre}: ${lente.cat ? p.tipologia : lente.f(p[lente.id])}</span>`);
  hover("mtr", (p) => `<b>MTR · ${p.nombre_en}</b><br><span class="muted">${p.nombre_zh} · ${p.n_rutas} líneas/servicios</span>`);
  hover("hosp", (p) => `<b>${p.hospital_en}</b><br><span class="muted">${p.hospital_zh} · urgencias</span>`);
  hover("hko", (p) => `<b>${p.estacion}</b><br><span class="muted">HKO · ${p.tipo}${p.elevacion_m != null ? " · " + p.elevacion_m + " m" : ""}</span>`);
  hover("hex", (p) => `<b>Celda H3</b><br><span class="muted">${p.parada_transporte} paradas · ${p.rutas_servidas} rutas-parada · cobertura ${p.nivel_cobertura}</span>`);
  hover("paradas", (p) => `<b>${p.nombre}</b><br><span class="muted">${String(p.modos).replace(/\|/g, ", ")} · ${p.n_rutas} rutas</span>`);
  const clic = (e) => elegirDistrito(e.features[0].properties.codigo, "mapa");
  map.on("click", "dist-fill", clic); map.on("click", "dist-3d", clic);

  function enfocar(cod) {
    const f = distritos.features.find((x) => x.properties.codigo === cod); if (!f) return;
    const c = f.geometry.type === "Polygon" ? f.geometry.coordinates.flat() : f.geometry.coordinates.flat(2);
    const xs = c.map((p) => p[0]), ys = c.map((p) => p[1]);
    map.fitBounds([[Math.min(...xs), Math.min(...ys)], [Math.max(...xs), Math.max(...ys)]], { padding: { top: 70, bottom: 40, left: innerWidth > 860 ? 290 : 30, right: innerWidth > 860 ? 300 : 30 }, duration: 900, maxZoom: 13 });
  }
  estado.oyentes.push((origen) => { ficha(); if (origen === "mapa") return; });
  aplicarLente(); ficha();
  void etiquetas;
  return { map, enfocar };
}
