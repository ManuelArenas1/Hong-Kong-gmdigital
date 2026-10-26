// Cerebro HK — orquesta datos del lago y secciones de la página.
import { lineas, barrasH, apiladaH, columnas, dispersion, pearson, spearman, fmt, fmtCorto, PALETA, CORAL, NEUTRO } from "./graficos.js";
import { iniciarMapa } from "./mapa.js";

const $ = (s) => document.querySelector(s);
const ARCHIVOS = ["panorama", "atlas_zonas", "demografia", "economia", "infraestructura", "sensores", "escucha",
  "correlaciones", "perfil_wiki", "fuentes", "conciliacion", "barrios"];
const G = {}; // datos globales

// ---------- utilidades ----------
const n0 = (v) => fmt(v, 0), n1 = (v) => fmt(v, 1);
const hk = (v) => "HK$ " + n0(v);
const pct = (v, d = 1) => fmt(v, d) + " %";
const mediana = (a) => { const s = [...a].sort((x, y) => x - y), m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; };
const norm = (vals, invertir) => { const mn = Math.min(...vals), mx = Math.max(...vals); return vals.map((v) => { const r = (v - mn) / (mx - mn || 1) * 100; return invertir ? 100 - r : r; }); };
const W = (tema, campo) => G.perfil_wiki.temas[tema][campo].valor;
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

function kpis(nodo, lista) {
  $(nodo).innerHTML = lista.map((k) => `<div class="kpi">${k.sello ? `<span class="sello ${k.sello}">${{ obs: "observado", dec: "declarado", der: "derivado" }[k.sello]}</span>` : ""}
    <div class="v">${k.v}${k.u ? `<small>${k.u}</small>` : ""}</div><div class="l">${k.l}</div><div class="f">${(k.f || "").replace(/^(F[\d–, F]+)/, "<b>$1</b>")}</div></div>`).join("");
}
function senales(nodo, lista) {
  $(nodo).innerHTML = lista.map((s) => `<div class="senal ${s.t || ""}"><b>${s.b}</b><span>${s.s}</span></div>`).join("");
}

// ---------- estado compartido ----------
const estado = { a: "J", b: "A", pesos: [1, 1, 1], oyentes: [] };
export function elegirDistrito(cod, origen) {
  if (!G.porCod[cod]) return;
  if (cod === estado.b) estado.b = estado.a;
  estado.a = cod;
  estado.oyentes.forEach((f) => f(origen));
}

// =====================================================================
async function cargar() {
  const res = await Promise.all(ARCHIVOS.map((a) => fetch(`data/${a}.json`).then((r) => { if (!r.ok) throw new Error(a); return r.json(); })));
  ARCHIVOS.forEach((a, i) => (G[a] = res[i]));
  G.D = G.atlas_zonas.distritos;
  // nombres que en una frase se confunden con palabras comunes («Este», «Sur», «Norte»)
  const AMBIGUOS = { C: "Distrito Este", D: "Distrito Sur", N: "Distrito Norte" };
  for (const d of G.D) if (AMBIGUOS[d.codigo]) d.distrito_es = AMBIGUOS[d.codigo];
  for (const f of G.correlaciones.dispersion) if (AMBIGUOS[f.codigo]) f.distrito_es = AMBIGUOS[f.codigo];
  for (const m of G.escucha.menciones_por_distrito) if (AMBIGUOS[m.codigo]) m.distrito_es = AMBIGUOS[m.codigo];
  G.porCod = Object.fromEntries(G.D.map((d) => [d.codigo, d]));
  G.nombre = (c) => G.porCod[c]?.distrito_es ?? c;
}

// =====================================================================
// PANORAMA
function panorama() {
  const k = G.panorama.kpis, D = G.D;
  const ing = D.map((d) => d.ingreso_mediano_hogar_hkd_2025);
  const dmin = D[ing.indexOf(Math.min(...ing))], dmax = D[ing.indexOf(Math.max(...ing))];
  $("#heroLead").innerHTML = `Hong Kong, <b>${n1(k.area_terrestre_km2)} km²</b> de tierra en 18 distritos: <b>${n0(k.poblacion_tierra_mitad_anio_2025)}</b> habitantes en 2025 (Censo 2021: ${n0(k.poblacion_censo_2021)}) · densidad media ${n0(k.densidad_media_hab_km2)} hab/km² · ingreso mediano del hogar entre <b>HK$ ${n0(dmin.ingreso_mediano_hogar_hkd_2025)}</b> (${dmin.distrito_es}) y <b>HK$ ${n0(dmax.ingreso_mediano_hogar_hkd_2025)}</b> (${dmax.distrito_es}) · PIB per cápita US$ ${n0(k.pib_per_capita_usd_2025)} · ${n0(k.paradas_transporte_publico)} paradas de transporte y ${k.estaciones_mtr} estaciones MTR. Un sistema territorial que reúne mapa, atlas distrital y correlaciones trazables: cada cifra conserva fuente, vigencia y método.`;
  const FU = G.fuentes.fuentes, integradas = FU.filter((f) => f.estado === "Integrada al lago").length;
  $("#heroPastillas").innerHTML = `<span class="pastilla"><span class="vivo"></span>licencias revisadas ${G.fuentes.fecha_licencias}</span><span class="pastilla">${FU.length} fuentes · F01–F${FU.length}</span>
    <span class="pastilla">${integradas} fuentes integradas</span><span class="pastilla">${Object.keys(G.correlaciones.variables).length} variables cruzables</span>
    <a class="pastilla acento" href="#fuentes">ver trazabilidad ↗</a>`;

  // selectores
  const opts = D.map((d) => `<option value="${d.codigo}">${d.distrito_es} · ${d.distrito_zh}</option>`).join("");
  $("#zonaA").innerHTML = opts; $("#zonaB").innerHTML = opts;
  $("#lugares").innerHTML = Object.keys(G.barrios).map((b) => `<option value="${b}">`).join("") + D.map((d) => `<option value="${d.distrito_en}">`).join("");

  // dimensiones del diagnóstico
  const dims = [
    { id: "pros", nombre: "Prosperidad", vars: [["ingreso_mediano_hogar_hkd_2025"], ["pct_titulo_universitario_15_mas"]], prim: "ingreso_mediano_hogar_hkd_2025", sello: "obs", unidad: "HK$/mes", fuente: "F21 · atlas_zonas.json", fmtv: n0 },
    { id: "con", nombre: "Conectividad", vars: [["paradas_por_10k_hab"], ["dist_media_hospital_km", true]], prim: "paradas_por_10k_hab", sello: "der", unidad: "paradas/10k hab", fuente: "F23, F24 · atlas_zonas.json", fmtv: n1 },
    { id: "pre", nombre: "Presión demográfica", vars: [["densidad_hab_km2"], ["pct_65_mas"]], prim: "densidad_hab_km2", sello: "obs", unidad: "hab/km²", fuente: "F20, F22 · atlas_zonas.json", fmtv: n0 },
  ];
  for (const dm of dims) {
    const partes = dm.vars.map(([c, inv]) => norm(D.map((d) => d[c]), inv));
    dm.punt = D.map((_, i) => partes.reduce((s, p) => s + p[i], 0) / partes.length);
    dm.normPrim = norm(D.map((d) => d[dm.prim]));
  }
  const presets = { Equilibrio: [1, 1, 1], Prosperidad: [3, 1, 1], Conectividad: [1, 3, 1], "Presión demográfica": [1, 1, 3] };
  $("#prioridades").insertAdjacentHTML("beforeend", Object.keys(presets).map((p, i) => `<button class="chip${i ? "" : " on"}" data-p="${p}">${p}</button>`).join(""));
  $("#pesos").innerHTML = dims.map((dm, i) => `<div class="peso"><div class="t">${dm.nombre}<span id="pp${i}">33 %</span></div><input type="range" min="0" max="5" step="1" value="1" data-i="${i}" aria-label="Peso de ${dm.nombre}"></div>`).join("");

  const indice = () => {
    const s = estado.pesos.reduce((a, b) => a + b, 0) || 1;
    return D.map((_, i) => dims.reduce((acc, dm, j) => acc + dm.punt[i] * estado.pesos[j], 0) / s);
  };
  function pintar() {
    $("#zonaA").value = estado.a; $("#zonaB").value = estado.b;
    const idx = indice(), orden = D.map((d, i) => [d, idx[i]]).sort((x, y) => y[1] - x[1]);
    const ia = D.findIndex((d) => d.codigo === estado.a), ib = D.findIndex((d) => d.codigo === estado.b);
    const da = D[ia], db = D[ib], pos = orden.findIndex((o) => o[0].codigo === estado.a) + 1, posb = orden.findIndex((o) => o[0].codigo === estado.b) + 1;
    const s = estado.pesos.reduce((a, b) => a + b, 0) || 1;
    estado.pesos.forEach((p, i) => ($("#pp" + i).textContent = Math.round((p / s) * 100) + " %"));
    $("#score").innerHTML = `${n1(idx[ia])}<small>/100</small>`;
    $("#lecturaCeja").textContent = `Lectura ejecutiva · ${da.distrito_es}`;
    const nivel = idx[ia] >= 66 ? "muy alta" : idx[ia] >= 50 ? "alta" : idx[ia] >= 33 ? "media" : "baja";
    const domin = dims.map((dm, j) => [dm, dm.punt[ia]]).sort((x, y) => y[1] - x[1]);
    const rel = (c) => { const m = mediana(D.map((d) => d[c])), v = da[c], r = (v / m - 1) * 100; return Math.abs(r) < 3 ? "en la mediana" : `${n0(Math.abs(r))} % ${r > 0 ? "sobre" : "bajo"} la mediana`; };
    $("#lectura").innerHTML = `<b>${da.distrito_es} presenta intensidad territorial ${nivel}</b> y ocupa el puesto ${pos} de 18 con las prioridades actuales. Su rasgo dominante es la ${domin[0][0].nombre.toLowerCase()}; el más débil, la ${domin[2][0].nombre.toLowerCase()}. Frente a la mediana de los distritos: ingreso del hogar ${rel("ingreso_mediano_hogar_hkd_2025")}, paradas por habitante ${rel("paradas_por_10k_hab")} y densidad ${rel("densidad_hab_km2")}. Es un distrito de tipo <b>${da.tipologia.toLowerCase()}</b>. <span class="muted">Esto orienta una revisión; no demuestra déficit ni causalidad.</span>`;
    $("#puesto").textContent = "#" + pos;
    $("#puestoNota").textContent = `de 18 distritos · ${n1(Math.abs(idx[ia] - idx[ib]))} puntos ${idx[ia] >= idx[ib] ? "sobre" : "bajo"} ${db.distrito_es}`;
    $("#dims").innerHTML = dims.map((dm) => `<div class="tarjeta dim" style="position:relative"><span class="sello ${dm.sello}">${dm.sello === "obs" ? "observado" : "derivado"}</span>
      <div class="muted" style="font-size:12.5px">${dm.nombre.toLowerCase()}</div><div class="v">${dm.fmtv(da[dm.prim])} <small>${dm.unidad}</small></div><p>${rel(dm.prim).replace(/^./, (c) => c.toUpperCase())} de los 18 distritos.</p><p class="mono muted" style="font-size:10px">${dm.fuente}</p></div>`).join("");
    $("#cmpTitulo").textContent = `${da.distrito_es} frente a ${db.distrito_es}`;
    $("#comparar").innerHTML = dims.map((dm) => `<div class="tarjeta" style="padding:12px 14px"><div style="display:flex;justify-content:space-between"><b style="font-size:13px">${dm.nombre}</b><span class="sello ${dm.sello} inline">${dm.sello === "obs" ? "observado" : "derivado"}</span></div>
      ${[[da, ia, CORAL], [db, ib, PALETA[0]]].map(([d, i, c]) => `<div class="barra-cmp"><span class="t">${d.distrito_es}</span><span class="pista"><i style="width:${Math.max(2, dm.punt[i])}%;background:${c}"></i></span><span class="n">${n0(dm.punt[i])}/100</span></div>`).join("")}
      <div class="mono muted" style="font-size:10px;margin-top:6px">${dm.prim.replace(/_/g, " ")}: ${dm.fmtv(da[dm.prim])} vs ${dm.fmtv(db[dm.prim])}</div></div>`).join("");
    $("#top5").innerHTML = orden.slice(0, 5).map(([d, v], i) => `<div>#${i + 1} ${d.distrito_es}<b>${n1(v)}</b><i style="width:${v}%"></i></div>`).join("");
    G.diagTexto = `${da.distrito_es}: índice ${n1(idx[ia])}/100, puesto ${pos} de 18 (prioridad ${estado.pesos.join("/")}). ${$("#lectura").innerText}`;
    void posb;
  }
  $("#prioridades").addEventListener("click", (e) => {
    const b = e.target.closest(".chip"); if (!b) return;
    document.querySelectorAll("#prioridades .chip").forEach((c) => c.classList.toggle("on", c === b));
    estado.pesos = [...presets[b.dataset.p]];
    document.querySelectorAll("#pesos input").forEach((r, i) => (r.value = estado.pesos[i]));
    pintar();
  });
  $("#pesos").addEventListener("input", (e) => {
    estado.pesos[+e.target.dataset.i] = +e.target.value;
    document.querySelectorAll("#prioridades .chip").forEach((c) => c.classList.remove("on"));
    pintar();
  });
  $("#zonaA").addEventListener("change", (e) => elegirDistrito(e.target.value, "diag"));
  $("#zonaB").addEventListener("change", (e) => { estado.b = e.target.value; if (estado.b === estado.a) estado.a = D.find((d) => d.codigo !== estado.b).codigo; pintar(); });
  $("#intercambiar").addEventListener("click", () => { [estado.a, estado.b] = [estado.b, estado.a]; estado.oyentes.forEach((f) => f("diag")); });
  const buscar = () => {
    const q = $("#lugar").value.trim().toLowerCase(); if (!q) return;
    const b = Object.entries(G.barrios).find(([k]) => k.toLowerCase() === q) || Object.entries(G.barrios).find(([k]) => k.toLowerCase().includes(q));
    const d = D.find((x) => x.distrito_en.toLowerCase().includes(q) || x.distrito_es.toLowerCase().includes(q) || x.distrito_zh.includes(q));
    const cod = b ? b[1].codigo : d?.codigo;
    if (cod) { elegirDistrito(cod, "diag"); $("#lugar").value = ""; $("#lugar").placeholder = `${b ? b[0] + " → " : ""}${G.nombre(cod)}`; }
    else { $("#lugar").value = ""; $("#lugar").placeholder = "No encontrado en el diccionario de barrios"; }
  };
  $("#buscarLugar").addEventListener("click", buscar);
  $("#lugar").addEventListener("keydown", (e) => e.key === "Enter" && buscar());
  $("#verEnMapa").addEventListener("click", () => { G.mapa?.enfocar(estado.a); document.getElementById("mapa").scrollIntoView(); });
  $("#copiarDiag").addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(G.diagTexto); $("#copiarDiag").textContent = "Copiado ✓"; } catch { $("#copiarDiag").textContent = "No se pudo copiar"; }
    setTimeout(() => ($("#copiarDiag").textContent = "Copiar diagnóstico"), 1800);
  });
  estado.oyentes.push(pintar);
  pintar();

  // señales
  const T = G.perfil_wiki.temas;
  senales("#senalesPanorama", [
    { t: "bueno", b: `Población: ${n0(W("poblacion", "poblacion_mitad_2026"))} a mediados de 2026 (+${n1(W("poblacion", "variacion_poblacion_anual_pct"))} %)`, s: `Crece solo por migración: ${n0(W("poblacion", "nacimientos_jul2025_jun2026"))} nacimientos contra ${n0(W("poblacion", "defunciones_jul2025_jun2026"))} defunciones en el último año. C&SD (F01).` },
    { t: "alerta", b: `Desigualdad: el hogar mediano de ${dmax.distrito_es} gana ${n1(dmax.ingreso_mediano_hogar_hkd_2025 / dmin.ingreso_mediano_hogar_hkd_2025)}× el de ${dmin.distrito_es}`, s: `HK$ ${n0(dmax.ingreso_mediano_hogar_hkd_2025)} frente a HK$ ${n0(dmin.ingreso_mediano_hogar_hkd_2025)} al mes en 2025. Encuesta General de Hogares (C&SD).` },
    { t: "critico", b: `Vivienda: ${n1(W("vivienda", "tiempo_espera_compuesto_anios_mar2026"))} años de espera por vivienda pública`, s: `${n0(W("vivienda", "solicitudes_prh_generales_mar2025"))} solicitudes generales; el ${n0(100 * D.reduce((a, d) => a + d.pob_vivienda_publica_alquiler + d.pob_vivienda_subsidiada_venta, 0) / k.poblacion_censo_2021)} % de la población vive en vivienda pública o subsidiada (Censo 2021, F20). Espera: Housing Bureau (F06).` },
    { t: "serio", b: `Envejecimiento: ${n1(k.pct_65_mas_2021)} % tiene 65+; la proyección oficial llega a ${n0(W("poblacion", "pct_65_mas_2046"))} % en 2046`, s: `Censo 2021 (F20, incluye empleadas domésticas). La proyección (F02) usa otra base, sin ellas. La natalidad bajó a ${n1(W("poblacion", "tasa_bruta_natalidad_2025"))} por mil (era ${n1(W("poblacion", "tasa_bruta_natalidad_1981"))} en 1981; CHP, F04).` },
    { t: "alerta", b: `Seguridad: ${n0(W("seguridad", "delitos_totales_2025"))} delitos en 2025 (${n1(W("seguridad", "var_delitos_totales_2025_pct"))} %)`, s: `El delito callejero baja, pero el fraude ya es el ${n1(W("seguridad", "pct_fraude_sobre_delitos_2025"))} % del total y costó HK$ ${n0(W("seguridad", "perdidas_fraude_2025"))} M. HKPF (F10).` },
    { t: "bueno", b: `Turismo: ${n1(W("turismo", "llegadas_visitantes_2025") / 1e6)} M de visitantes en 2025 (+${n0(W("turismo", "var_llegadas_2025_pct"))} %)`, s: `Aún bajo el pico de ${n1(W("turismo", "llegadas_visitantes_pico_2018") / 1e6)} M (2018); ${n0(100 * W("turismo", "llegadas_continentales_2025") / W("turismo", "llegadas_visitantes_2025"))} % llega de China continental. gov.hk (F12).` },
    { t: "bueno", b: `Finanzas: reservas de HK$ ${n0(W("finanzas_publicas", "reservas_fiscales_mar2026"))} M`, s: `Cubren unos ${W("finanzas_publicas", "reservas_meses_de_gasto")} meses de gasto; superávit consolidado estimado de HK$ ${n0(W("finanzas_publicas", "superavit_consolidado_2026_27"))} M en 2026-27. Budget 2026-27 (F08).` },
  ]);
  void T;
}

// =====================================================================
function gente() {
  const D = G.D, dem = G.demografia, k = G.panorama.kpis;
  const P = dem.piramide_hk_2021, tot = Object.values(P).reduce((a, b) => a + b, 0);
  const hog = D.reduce((a, d) => a + d.hogares_2021, 0);
  const tam = D.reduce((a, d) => a + d.tamano_medio_hogar * d.hogares_2021, 0) / hog;
  const nac = D.reduce((a, d) => a + d.pob_nacida_en_hk, 0) / k.poblacion_censo_2021 * 100;
  const sr = D.reduce((a, d) => a + d.razon_sexos_hombres_por_1000_mujeres * d.poblacion_2021, 0) / k.poblacion_censo_2021;
  const crec = [...D].sort((a, b) => b.var_pob_2016_2025_pct - a.var_pob_2016_2025_pct);
  const env = [...D].sort((a, b) => b.pct_65_mas - a.pct_65_mas);
  const den = [...D].sort((a, b) => b.densidad_hab_km2 - a.densidad_hab_km2);
  $("#genteLead").innerHTML = `Hong Kong tenía <b>${n0(k.poblacion_censo_2021)}</b> habitantes en el Censo 2021 y <b>${n0(k.poblacion_tierra_mitad_anio_2025)}</b> en 2025; la estimación de mediados de 2026 es <b>${n0(W("poblacion", "poblacion_mitad_2026"))}</b>. Es una de las ciudades más densas del mundo (${n0(k.densidad_media_hab_km2)} hab/km² de media, ${n0(den[0].densidad_hab_km2)} en ${den[0].distrito_es}), envejece rápido (${pct(k.pct_65_mas_2021)} con 65+) y crece solo por migración: la natalidad cayó a ${n1(W("poblacion", "tasa_bruta_natalidad_2025"))} por mil.`;
  kpis("#genteKpis", [
    { v: n0(k.poblacion_censo_2021), u: "personas", l: "Población Censo 2021", f: "F20 · demografia.json", sello: "obs" },
    { v: n0(k.poblacion_tierra_mitad_anio_2025), u: "personas", l: "Población terrestre 2025", f: "F21 · demografia.json", sello: "obs" },
    { v: n0(W("poblacion", "poblacion_mitad_2026")), u: "personas", l: "Estimación mediados de 2026", f: "F01 · perfil_wiki.json", sello: "dec" },
    { v: n0(k.densidad_media_hab_km2), u: "hab/km²", l: "Densidad media terrestre", f: "F20, F22 · panorama.json", sello: "der" },
    { v: n1(k.pct_65_mas_2021), u: "%", l: "Población de 65 años o más", f: "F20 · demografia.json", sello: "obs" },
    { v: n1(100 * P["0_14"] / tot), u: "%", l: "Población de 0 a 14", f: "F20 · demografia.json", sello: "obs" },
    { v: n0(sr), u: "hombres/1.000 mujeres", l: "Razón de sexos (incluye empleadas domésticas)", f: "F20 · atlas_zonas.json", sello: "obs" },
    { v: n0(hog), u: "hogares", l: "Hogares domésticos 2021", f: "F20 · atlas_zonas.json", sello: "obs" },
    { v: fmt(tam, 2), u: "personas/hogar", l: "Tamaño medio del hogar", f: "F20 · atlas_zonas.json", sello: "der" },
    { v: n1(nac), u: "%", l: "Nacida en Hong Kong", f: "F20 · atlas_zonas.json", sello: "obs" },
    { v: n1(W("poblacion", "pct_15mas_educacion_superior_2021")), u: "%", l: "15+ con educación superior (incluye no universitaria)", f: "F03 · perfil_wiki.json", sello: "dec" },
    { v: n1(W("poblacion", "tasa_bruta_natalidad_2025")), u: "‰", l: "Tasa bruta de natalidad 2025", f: "F04 · perfil_wiki.json", sello: "dec" },
    { v: fmt(W("poblacion", "poblacion_proyectada_2046_base") / 1e6, 2), u: "M personas", l: "Proyección 2046 (escenario base)", f: "F02 · perfil_wiki.json", sello: "dec" },
    { v: n0(W("poblacion", "pct_65_mas_2046")), u: "%", l: "65+ proyectado en 2046", f: "F02 · perfil_wiki.json", sello: "dec" },
  ]);
  senales("#genteSenales", [
    { t: "bueno", b: `${crec[0].distrito_es} es el que más crece: +${n1(crec[0].var_pob_2016_2025_pct)} % entre 2016 y 2025`, s: `${crec[crec.length - 1].distrito_es} es el que más pierde (${n1(crec[crec.length - 1].var_pob_2016_2025_pct)} %). Los distritos nuevos del oeste y Lantau absorben el crecimiento; la isla de Hong Kong se vacía.` },
    { t: "serio", b: `${env[0].distrito_es} es el distrito más envejecido: ${pct(env[0].pct_65_mas)} con 65+`, s: `Le siguen ${env[1].distrito_es} (${pct(env[1].pct_65_mas)}) y ${env[2].distrito_es} (${pct(env[2].pct_65_mas)}). El más joven es ${env[17].distrito_es} (${pct(env[17].pct_65_mas)}).` },
    { t: "alerta", b: `Déficit natural: ${n0(-W("poblacion", "crecimiento_natural_jul2025_jun2026"))} personas menos al año`, s: `Mueren más de las que nacen; la entrada neta proyectada a 2046 es de ${n1(W("poblacion", "entrada_neta_proyectada_2022_2046") / 1e6)} M (incluye ${n0(W("poblacion", "entrada_one_way_permit_2022_2046") / 1e3)} mil con One-way Permit).` },
    { t: "critico", b: `Densidad extrema: ${den[0].distrito_es} tiene ${n0(den[0].densidad_hab_km2)} hab/km²`, s: `Es ${n0(den[0].densidad_hab_km2 / den[17].densidad_hab_km2)} veces la de ${den[17].distrito_es}. Los 5 distritos de Kowloon superan los 40.000 hab/km².` },
  ]);
  const serie = Object.entries(dem.serie_poblacion.reduce((a, r) => ((a[r.anio] = (a[r.anio] || 0) + r.poblacion_mitad_anio), a), {})).map(([x, y]) => ({ x: +x, y }));
  lineas($("#gPobTotal"), { series: [{ nombre: "Hong Kong", color: CORAL, valores: serie }], alto: 230, etiquetas: false });
  barrasH($("#gEdad"), { filas: [["65 o más", "65_mas"], ["45–64", "45_64"], ["25–44", "25_44"], ["15–24", "15_24"], ["0–14", "0_14"]].map(([e, c]) => ({ etiqueta: e, valor: P[c] })), fmtV: fmtCorto, anchoEtiqueta: 70, tipExtra: (f) => `<div class="muted">${n1(100 * f.valor / tot)} % del total</div>` });
  const fila = (campo, f = (v) => v) => (d) => ({ etiqueta: d.distrito_es, valor: f(d[campo]), resaltar: d.codigo === estado.a, alClic: () => elegirDistrito(d.codigo, "graf") });
  const pintarDist = () => {
    barrasH($("#gPobDist"), { filas: [...D].sort((a, b) => b.poblacion_2025 - a.poblacion_2025).map(fila("poblacion_2025")), fmtV: fmtCorto });
    barrasH($("#gEnvej"), { filas: [...D].sort((a, b) => b.pct_65_mas - a.pct_65_mas).map(fila("pct_65_mas")), fmtV: n1, sufijo: " %" });
    barrasH($("#gCrec"), { filas: [...D].sort((a, b) => b.var_pob_2016_2025_pct - a.var_pob_2016_2025_pct).map(fila("var_pob_2016_2025_pct")), fmtV: n1, sufijo: " %" });
    barrasH($("#gEdu"), { filas: [...D].sort((a, b) => b.pct_titulo_universitario_15_mas - a.pct_titulo_universitario_15_mas).map(fila("pct_titulo_universitario_15_mas")), fmtV: n1, sufijo: " %" });
  };
  pintarDist(); estado.oyentes.push(pintarDist);
  columnas($("#gNatal"), { filas: [["1981", "tasa_bruta_natalidad_1981"], ["2011", "tasa_bruta_natalidad_2011"], ["2025", "tasa_bruta_natalidad_2025"]].map(([e, c]) => ({ etiqueta: e, valor: W("poblacion", c) })), alto: 230, fmtV: n1 });
}

// =====================================================================
function economia() {
  const D = G.D, e = G.economia, mac = e.macro, ult = mac[mac.length - 1];
  const pubsub = 100 * D.reduce((a, d) => a + d.pob_vivienda_publica_alquiler + d.pob_vivienda_subsidiada_venta, 0) / G.panorama.kpis.poblacion_censo_2021;
  $("#ecoLead").innerHTML = `Hong Kong tiene un PIB per cápita de <b>US$ ${n0(ult.pib_per_capita_usd_corrientes)}</b> (2025) e inflación de ${pct(ult.inflacion_ipc_pct)}, pero el mercado de vivienda más caro del mundo: un apartamento pequeño cuesta <b>HK$ ${n0(W("vivienda", "precio_m2_apto_menor_40m2_oct2025"))} por m²</b> y la espera por vivienda pública es de ${n1(W("vivienda", "tiempo_espera_compuesto_anios_mar2026"))} años. El ingreso mediano del hogar va de HK$ ${n0(Math.min(...D.map((d) => d.ingreso_mediano_hogar_hkd_2025)))} a HK$ ${n0(Math.max(...D.map((d) => d.ingreso_mediano_hogar_hkd_2025)))} al mes según el distrito.`;
  kpis("#ecoKpis", [
    { v: n0(ult.pib_per_capita_usd_corrientes), u: "US$", l: "PIB per cápita 2025", f: "F28 · economia.json", sello: "obs" },
    { v: n1(ult.crecimiento_real_pib_pc_pct), u: "%", l: "Crecimiento real del PIB per cápita", f: "F29 · economia.json", sello: "der" },
    { v: n1(ult.inflacion_ipc_pct), u: "%", l: "Inflación IPC 2025", f: "F30 · economia.json", sello: "obs" },
    { v: n1(W("finanzas_publicas", "pct_pib_cuatro_industrias_2024")), u: "% PIB", l: "Peso de las cuatro industrias clave", f: "F09 · perfil_wiki.json", sello: "dec" },
    { v: n0(mediana(D.map((d) => d.ingreso_mediano_hogar_hkd_2025))), u: "HK$/mes", l: "Ingreso mediano del hogar, distrito típico", f: "F21 · atlas_zonas.json", sello: "obs" },
    { v: n0(W("vivienda", "precio_m2_apto_menor_40m2_oct2025")), u: "HK$/m²", l: "Precio, apartamentos < 40 m²", f: "F05 · perfil_wiki.json", sello: "dec" },
    { v: "+" + n1(W("vivienda", "var_precio_h1_2026_pct")), u: "%", l: "Variación del precio, 1.er semestre 2026", f: "F05 · perfil_wiki.json", sello: "dec" },
    { v: n1(W("vivienda", "vacancia_residencial_pct_2025")), u: "%", l: `Vacancia residencial (${n0(W("vivienda", "viviendas_vacantes_2025"))} unidades)`, f: "F05 · perfil_wiki.json", sello: "dec" },
    { v: n1(W("vivienda", "tiempo_espera_compuesto_anios_mar2026")), u: "años", l: "Espera por vivienda pública (CWT)", f: "F06 · perfil_wiki.json", sello: "dec" },
    { v: n0(W("vivienda", "solicitudes_prh_generales_mar2025")), u: "solicitudes", l: "Lista de espera de vivienda pública", f: "F06 · perfil_wiki.json", sello: "dec" },
    { v: n1(pubsub), u: "%", l: "Población en vivienda pública o subsidiada", f: "F20 · atlas_zonas.json", sello: "obs" },
  ]);
  const ri = [...D].sort((a, b) => b.var_ingreso_2016_2025_pct - a.var_ingreso_2016_2025_pct);
  senales("#ecoSenales", [
    { t: "alerta", b: `Precio de vivienda: cayó ${n0(-W("vivienda", "caida_precio_desde_pico_sep2021_pct"))} % desde 2021 y ahora rebota +${n1(W("vivienda", "var_precio_h1_2026_pct"))} %`, s: `Las rentas subieron ${n1(W("vivienda", "var_indice_rentas_h1_2026_pct"))} % en el primer semestre de 2026 y se esperan ${W("vivienda", "prevision_rentas_2026")} % en el año. RVD (F05).` },
    { t: "bueno", b: `${ri[0].distrito_es} es donde más subió el ingreso: +${n1(ri[0].var_ingreso_2016_2025_pct)} % en 2016–2025`, s: `En ${ri[17].distrito_es} apenas ${n1(ri[17].var_ingreso_2016_2025_pct)} %. Valores nominales, sin ajustar por inflación.` },
    { t: "critico", b: `El problema es la asequibilidad, no solo la escasez`, s: `Hay ${n0(W("vivienda", "viviendas_vacantes_2025"))} viviendas privadas vacías (${n1(W("vivienda", "vacancia_residencial_pct_2025"))} %) mientras ${n0(W("vivienda", "solicitudes_prh_generales_mar2025"))} hogares esperan vivienda pública.` },
  ]);
  // ingreso por distrito: hasta 4 destacados, resto en gris
  const sel = ["A", "J", "F", "Q"];
  const colorDe = {}; sel.forEach((c, i) => (colorDe[c] = PALETA[i]));
  const pintarIng = () => {
    $("#ingresoSel").innerHTML = D.map((d) => `<button class="chip" data-c="${d.codigo}" style="${sel.includes(d.codigo) ? `border-color:${colorDe[d.codigo]};color:#2b0d09;box-shadow:inset 0 -3px 0 ${colorDe[d.codigo]}` : ""}">${d.distrito_es}</button>`).join("");
    const series = D.map((d) => ({ nombre: d.distrito_es, color: sel.includes(d.codigo) ? colorDe[d.codigo] : "#eadcd9", tenue: !sel.includes(d.codigo), grosor: sel.includes(d.codigo) ? 2.2 : 1.2,
      valores: e.serie_distritos.filter((r) => r.codigo === d.codigo).map((r) => ({ x: r.anio, y: r.ingreso_mediano_hogar_hkd })) }))
      .sort((a, b) => (a.tenue ? 0 : 1) - (b.tenue ? 0 : 1));
    lineas($("#gIngreso"), { series, alto: 300, yFmt: (v) => "HK$ " + fmtCorto(v) });
  };
  $("#ingresoSel").addEventListener("click", (ev) => {
    const b = ev.target.closest(".chip"); if (!b) return; const c = b.dataset.c;
    if (sel.includes(c)) { if (sel.length > 1) { sel.splice(sel.indexOf(c), 1); delete colorDe[c]; } }
    else { if (sel.length >= 4) { delete colorDe[sel.shift()]; } const libre = PALETA.slice(0, 4).find((p) => !Object.values(colorDe).includes(p)); colorDe[c] = libre; sel.push(c); }
    pintarIng();
  });
  pintarIng();
  const fila = (campo) => (d) => ({ etiqueta: d.distrito_es, valor: d[campo], resaltar: d.codigo === estado.a, alClic: () => elegirDistrito(d.codigo, "graf") });
  const pintarRank = () => barrasH($("#gRankIng"), { filas: [...D].sort((a, b) => b.ingreso_mediano_hogar_hkd_2025 - a.ingreso_mediano_hogar_hkd_2025).map(fila("ingreso_mediano_hogar_hkd_2025")), fmtV: (v) => fmtCorto(v) });
  pintarRank(); estado.oyentes.push(pintarRank);
  lineas($("#gPib"), { series: [{ nombre: "PIB per cápita", color: PALETA[0], valores: mac.map((r) => ({ x: r.anio, y: r.pib_per_capita_usd_corrientes })) }], alto: 260, etiquetas: false, yFmt: (v) => "US$ " + fmtCorto(v) });
  columnas($("#gInfl"), { filas: mac.filter((r) => r.anio >= 2010).map((r) => ({ etiqueta: String(r.anio).slice(2), valor: r.inflacion_ipc_pct, nota: `año ${r.anio}` })), alto: 260, fmtV: n1, etiquetasValor: false });
  const pintarTen = () => apiladaH($("#gTenencia"), {
    filas: [...D].sort((a, b) => b.pct_vivienda_publica_alquiler - a.pct_vivienda_publica_alquiler).map((d) => ({ etiqueta: d.distrito_es, resaltar: d.codigo === estado.a,
      valores: { pub: d.pct_vivienda_publica_alquiler, sub: d.pct_vivienda_subsidiada_venta, pri: d.pct_vivienda_privada, otr: Math.max(0, 100 - d.pct_vivienda_publica_alquiler - d.pct_vivienda_subsidiada_venta - d.pct_vivienda_privada) } })),
    partes: [{ clave: "pub", nombre: "Pública de alquiler", color: PALETA[0] }, { clave: "sub", nombre: "Subsidiada en propiedad", color: PALETA[1] }, { clave: "pri", nombre: "Privada", color: PALETA[2] }, { clave: "otr", nombre: "Temporal y no doméstica", color: "#d9c9c6" }],
  });
  pintarTen(); estado.oyentes.push(pintarTen);
  columnas($("#gOferta"), { filas: [{ etiqueta: "2024 terminadas", valor: W("vivienda", "viviendas_privadas_terminadas_2024") }, { etiqueta: "2026 previstas", valor: W("vivienda", "oferta_privada_prevista_2026") }, { etiqueta: "2027 previstas", valor: W("vivienda", "oferta_privada_prevista_2027") }], alto: 200, fmtV: fmtCorto });
  senales("#viviendaSenales", [
    { t: "serio", b: `${n0(W("vivienda", "oferta_publica_proyectada_5_anios"))} viviendas públicas en 5 años`, s: `Light Public Housing: ${n0(W("vivienda", "light_public_housing_unidades_1t2026"))} unidades de una meta de ${n0(W("vivienda", "light_public_housing_meta_2027_28"))} para 2027/28. Housing Bureau (F06).` },
  ]);
}

// =====================================================================
function turismo() {
  const t = (c) => W("turismo", c);
  $("#turLead").innerHTML = `Hong Kong recibió <b>${n1(t("llegadas_visitantes_2025") / 1e6)} millones</b> de visitantes en 2025 (+${n0(t("var_llegadas_2025_pct"))} %), aún bajo el pico de ${n1(t("llegadas_visitantes_pico_2018") / 1e6)} M de 2018. El primer trimestre de 2026 fue récord (${n1(t("llegadas_visitantes_1t2026") / 1e6)} M, +${n0(t("var_llegadas_1t2026_pct"))} %). El turismo pesa ${n1(t("pct_pib_turismo_2024"))} % del PIB en la medida oficial, pero mueve hoteles al ${n0(t("ocupacion_hotelera_2025_pct"))} % de ocupación y una oferta natural de ${W("suelo", "n_country_parks")} parques.`;
  kpis("#turKpis", [
    { v: n1(t("llegadas_visitantes_2025") / 1e6), u: "M", l: "Llegadas de visitantes 2025", f: "F12 · perfil_wiki.json", sello: "dec" },
    { v: "+" + n0(t("var_llegadas_2025_pct")), u: "%", l: "Variación frente a 2024", f: "F12 · perfil_wiki.json", sello: "dec" },
    { v: n1(t("llegadas_visitantes_1t2026") / 1e6), u: "M", l: "Llegadas 1.er trimestre 2026 (récord)", f: "F12 · perfil_wiki.json", sello: "dec" },
    { v: n0(100 * t("llegadas_continentales_2025") / t("llegadas_visitantes_2025")), u: "%", l: "Visitantes de China continental", f: "F12 · perfil_wiki.json (derivado)", sello: "der" },
    { v: n0(t("gasto_turistico_receptor_2024") / 1000), u: "mil M HK$", l: "Gasto de los visitantes 2024", f: "F12 · perfil_wiki.json", sello: "dec" },
    { v: n1(t("pct_pib_turismo_2024")), u: "% PIB", l: "Peso del turismo en el PIB", f: "F12 · perfil_wiki.json", sello: "dec" },
    { v: n0(t("empleos_turismo_2024")), u: "empleos", l: `Empleo turístico (${n1(t("pct_empleo_turismo_2024"))} % del total)`, f: "F12 · perfil_wiki.json", sello: "dec" },
    { v: n1(t("estancia_media_noches_2025")), u: "noches", l: "Estancia media", f: "F12 · perfil_wiki.json", sello: "dec" },
    { v: n0(t("ocupacion_hotelera_2025_pct")), u: "%", l: "Ocupación hotelera", f: "F12 · perfil_wiki.json", sello: "dec" },
  ]);
  barrasH($("#gLlegadas"), { filas: [
    { etiqueta: "2018 (pico)", valor: t("llegadas_visitantes_pico_2018") / 1e6, color: "#d9c9c6" },
    { etiqueta: "2025 total", valor: t("llegadas_visitantes_2025") / 1e6, color: PALETA[0] },
    { etiqueta: "2025 · China continental", valor: t("llegadas_continentales_2025") / 1e6, color: PALETA[1] },
    { etiqueta: "2025 · otros mercados", valor: t("llegadas_no_continentales_2025") / 1e6, color: PALETA[2] },
    { etiqueta: "1.er trim. 2026", valor: t("llegadas_visitantes_1t2026") / 1e6, color: PALETA[0] }], fmtV: n1, sufijo: " M", anchoEtiqueta: 160, alto: 170 });
  barrasH($("#gParques"), { filas: G.perfil_wiki.suelo_parques.map((p) => ({ etiqueta: p.nombre_parque, valor: p.area_ha })), fmtV: n0, sufijo: " ha", color: PALETA[1], anchoEtiqueta: 110 });
  $("#turNoticias").innerHTML = titularesHTML(G.escucha.noticias.filter((n) => n.tema === "turismo"));
}

// =====================================================================
function gobierno() {
  const f = (c) => W("finanzas_publicas", c);
  $("#finLead").innerHTML = `El presupuesto 2026-27 estima ingresos por <b>HK$ ${n0(f("ingreso_total_2026_27"))} M</b> y gastos por <b>HK$ ${n0(f("gasto_total_2026_27"))} M</b> (${n1(f("gasto_pct_pib_2026_27"))} % del PIB). Sin IVA ni impuesto a las ganancias de capital, la mayor fuente son los impuestos a las ganancias y los salarios. Las reservas fiscales cubren unos ${f("reservas_meses_de_gasto")} meses de gasto y la inversión del Northern Metropolis se financia con bonos.`;
  kpis("#finKpis", [
    { v: n0(f("ingreso_total_2026_27") / 1000), u: "mil M HK$", l: "Ingreso total estimado", f: "F08 · perfil_wiki.json", sello: "dec" },
    { v: n0(f("gasto_total_2026_27") / 1000), u: "mil M HK$", l: `Gasto total (+${n1(f("var_gasto_total_pct"))} %)`, f: "F08 · perfil_wiki.json", sello: "dec" },
    { v: n1(f("gasto_pct_pib_2026_27")), u: "% PIB", l: "Tamaño del gasto público", f: "F08 · perfil_wiki.json", sello: "dec" },
    { v: n0(f("gasto_salud_bienestar_educacion_2026_27") / 1000), u: "mil M HK$", l: "Salud, bienestar y educación (~60 % del recurrente)", f: "F08 · perfil_wiki.json", sello: "dec" },
    { v: n0(f("reservas_fiscales_mar2026") / 1000), u: "mil M HK$", l: `Reservas fiscales (~${f("reservas_meses_de_gasto")} meses de gasto)`, f: "F08 · perfil_wiki.json", sello: "dec" },
    { v: n0(f("superavit_consolidado_2026_27") / 1000), u: "mil M HK$", l: "Superávit consolidado estimado 2026-27", f: "F08 · perfil_wiki.json", sello: "dec" },
    { v: n0(f("techo_deuda_bonos") / 1000), u: "mil M HK$", l: "Techo de endeudamiento por bonos", f: "F08 · perfil_wiki.json", sello: "dec" },
    { v: n0(f("emision_bonos_2026_27") / 1000), u: "mil M HK$", l: "Emisión de bonos 2026-27", f: "F08 · perfil_wiki.json", sello: "dec" },
  ]);
  barrasH($("#gFin"), { filas: [
    { etiqueta: "Ingreso total", valor: f("ingreso_total_2026_27"), color: PALETA[2] },
    { etiqueta: "Ganancias y salarios", valor: f("impuestos_ganancias_y_salarios_2026_27"), color: PALETA[2] },
    { etiqueta: "Derechos de timbre", valor: f("derechos_timbre_2026_27"), color: PALETA[2] },
    { etiqueta: "Venta de suelo", valor: f("ingreso_suelo_2026_27"), color: PALETA[2] },
    { etiqueta: "Gasto total", valor: f("gasto_total_2026_27"), color: PALETA[1] },
    { etiqueta: "Gasto recurrente", valor: f("gasto_recurrente_2026_27"), color: PALETA[1] },
    { etiqueta: "Salud, bienestar, educación", valor: f("gasto_salud_bienestar_educacion_2026_27"), color: PALETA[2] }], fmtV: fmtCorto, anchoEtiqueta: 160 });
  $("#gFin").insertAdjacentHTML("beforeend", `<div class="leyenda"><span><i style="background:${PALETA[1]}"></i>Ingresos</span><span><i style="background:${PALETA[2]}"></i>Gastos</span></div>`);
  columnas($("#gBalance"), { filas: [
    { etiqueta: "Consolidado 2025-26", valor: f("superavit_consolidado_2025_26"), color: PALETA[2] },
    { etiqueta: "Consolidado 2026-27", valor: f("superavit_consolidado_2026_27"), color: PALETA[2] },
    { etiqueta: "Cuenta de capital 2026-27", valor: f("deficit_capital_2026_27"), color: PALETA[2] }], alto: 240, fmtV: fmtCorto });
}

// =====================================================================
function seguridad() {
  const s = (c) => W("seguridad", c);
  $("#segLead").innerHTML = `Ciudad muy segura en la calle: <b>${n0(s("delitos_totales_2025"))}</b> delitos en 2025 (${n1(s("var_delitos_totales_2025_pct"))} %), robos con violencia en mínimos y una tasa habitual de homicidios de ${n1(s("tasa_homicidios_habitual_100k"))} por 100.000. El problema que crece es el <b>fraude</b>: ya es el ${n1(s("pct_fraude_sobre_delitos_2025"))} % del total. La policía no publica las cifras por los 18 distritos, así que esta sección no tiene mapa.`;
  kpis("#segKpis", [
    { v: n0(s("delitos_totales_2025")), u: "casos", l: `Delitos 2025 (${n1(s("var_delitos_totales_2025_pct"))} %)`, f: "F10 · perfil_wiki.json", sello: "dec" },
    { v: n0(s("delitos_violentos_2025")), u: "casos", l: `Delitos violentos (${n1(s("var_delitos_violentos_2025_pct"))} %)`, f: "F10 · perfil_wiki.json", sello: "dec" },
    { v: n0(s("casos_fraude_2025")), u: "casos", l: `Fraude y estafa (${n1(s("pct_fraude_sobre_delitos_2025"))} % del delito)`, f: "F10 · perfil_wiki.json", sello: "dec" },
    { v: n0(s("perdidas_fraude_2025")), u: "M HK$", l: "Pérdidas por fraude", f: "F10 · perfil_wiki.json", sello: "dec" },
    { v: n0(s("casos_fraude_compras_online_2025")), u: "casos", l: "Fraude en compras online (el más común)", f: "F10 · perfil_wiki.json", sello: "dec" },
    { v: n1(s("tasa_homicidios_habitual_100k")), u: "por 100 mil", l: "Tasa habitual de homicidios", f: "F10 · perfil_wiki.json", sello: "dec" },
    { v: "#" + s("posicion_cpi_2025"), u: `de 180+ · ${s("puntaje_cpi_2025")} pts`, l: `Percepción de corrupción (era #${s("posicion_cpi_2024")})`, f: "F11 · perfil_wiki.json", sello: "dec" },
    { v: n0(s("delitos_triadas_2025")), u: "casos", l: `Delitos de tríadas (${n1(s("var_delitos_triadas_2025_pct"))} %)`, f: "F10 · perfil_wiki.json", sello: "dec" },
  ]);
  senales("#segSenales", [
    { t: "critico", b: "El fraude es casi la mitad del delito", s: `${n0(s("casos_fraude_2025"))} casos y HK$ ${n0(s("perdidas_fraude_2025"))} M en pérdidas. La población mayor (19,6 % con 65+, Censo 2021) es blanco frecuente: cruzar edad y pobreza por zona es delicado.` },
    { t: "alerta", b: "Homicidios 2025: no es una ola de criminalidad", s: "El salto de 2025 se explica casi entero por el incendio de Wang Fuk Court en Tai Po (168 muertes), reclasificado como homicidio involuntario." },
    { t: "bueno", b: `Robo con violencia ${n1(s("var_robo_con_violencia_2025_pct"))} % y allanamiento ${n1(s("var_hurto_con_allanamiento_2025_pct"))} %`, s: "Mínimos históricos del delito callejero y contra la propiedad." },
  ]);
  const dm = G.escucha.delitos_mensuales;
  lineas($("#gDelitos"), { series: [
    { nombre: "Totales", color: PALETA[0], valores: dm.map((r, i) => ({ x: i, y: r.delitos_totales })) },
    { nombre: "Violentos", color: PALETA[1], valores: dm.map((r, i) => ({ x: i, y: r.delitos_violentos })) }],
  alto: 260, desde0: true, xFmt: (i) => dm[i]?.periodo ?? "", yFmt: fmtCorto });
  barrasH($("#gVarDelitos"), { filas: [
    ["Delitos totales", "var_delitos_totales_2025_pct"], ["Violentos", "var_delitos_violentos_2025_pct"], ["Robo con violencia", "var_robo_con_violencia_2025_pct"],
    ["Allanamiento", "var_hurto_con_allanamiento_2025_pct"], ["Tríadas", "var_delitos_triadas_2025_pct"], ["Pérdidas por fraude", "var_perdidas_fraude_2025_pct"]]
    .map(([e, c]) => ({ etiqueta: e, valor: s(c) })), fmtV: n1, sufijo: " %", anchoEtiqueta: 130 });
}

// =====================================================================
function infraestructura() {
  const D = G.D, inf = G.infraestructura, k = G.panorama.kpis;
  const sinH = D.filter((d) => d.hospitales_urgencias === 0);
  const acc = inf.acceso_hospital_dcca, distMedia = acc.reduce((a, r) => a + r.distancia_hospital_m, 0) / acc.length / 1000;
  const lejos = [...acc].sort((a, b) => b.distancia_hospital_m - a.distancia_hospital_m)[0];
  const p10 = [...D].sort((a, b) => b.paradas_por_10k_hab - a.paradas_por_10k_hab);
  $("#infLead").innerHTML = `La red pública reúne <b>${n0(k.paradas_transporte_publico)} paradas</b> de bus, minibús, MTR, tren ligero y ferry, con <b>${k.estaciones_mtr} estaciones MTR</b>. ${p10[0].distrito_es} tiene la mayor oferta por habitante (${n1(p10[0].paradas_por_10k_hab)} paradas por 10.000) y ${p10[17].distrito_es} la menor (${n1(p10[17].paradas_por_10k_hab)}). Hay ${k.hospitales_urgencias} hospitales públicos con urgencias; ${sinH.length} distritos no tienen ninguno dentro (${sinH.map((d) => d.distrito_es).join(", ")}).`;
  kpis("#infKpis", [
    { v: n0(k.paradas_transporte_publico), u: "paradas", l: "Paradas de transporte con rutas activas", f: "F23 · panorama.json", sello: "obs" },
    { v: k.estaciones_mtr, u: "estaciones", l: "Estaciones del MTR", f: "F23 · panorama.json", sello: "obs" },
    { v: n0(D.reduce((a, d) => a + d.paradas_minibus, 0)), u: "paradas", l: "Paradas de minibús verde", f: "F23 · atlas_zonas.json", sello: "obs" },
    { v: k.hospitales_urgencias, u: "hospitales", l: "Hospitales públicos con urgencias", f: "F24 · panorama.json", sello: "obs" },
    { v: n1(distMedia), u: "km", l: "Distancia media a urgencias (452 circunscripciones)", f: "F24, F19 · infraestructura.json", sello: "der" },
    { v: n1(lejos.distancia_hospital_m / 1000), u: "km", l: `Circunscripción más lejana (${lejos.codigo_dcca}, ${G.nombre(lejos.codigo)})`, f: "F24, F19 · infraestructura.json", sello: "der" },
    { v: sinH.length, u: "distritos", l: "Sin hospital de urgencias propio", f: "F24 · atlas_zonas.json", sello: "der" },
  ]);
  const fila = (campo, f = (v) => v) => (d) => ({ etiqueta: d.distrito_es, valor: f(d[campo]), resaltar: d.codigo === estado.a, alClic: () => elegirDistrito(d.codigo, "graf") });
  const pintar = () => {
    barrasH($("#gParadas10k"), { filas: [...D].sort((a, b) => b.paradas_por_10k_hab - a.paradas_por_10k_hab).map(fila("paradas_por_10k_hab")), fmtV: n1 });
    barrasH($("#gDistHosp"), { filas: [...D].sort((a, b) => b.dist_media_hospital_km - a.dist_media_hospital_km).map(fila("dist_media_hospital_km")), fmtV: n1, sufijo: " km" });
    barrasH($("#gMtr"), { filas: [...D].sort((a, b) => b.paradas_metro_mtr - a.paradas_metro_mtr).map(fila("paradas_metro_mtr")), fmtV: n0, color: PALETA[0] });
    apiladaH($("#gModos"), { filas: [...D].sort((a, b) => b.paradas_transporte - a.paradas_transporte).map((d) => ({ etiqueta: d.distrito_es, resaltar: d.codigo === estado.a,
      valores: { bus: d.paradas_bus, mini: d.paradas_minibus, mtr: d.paradas_metro_mtr, lr: d.paradas_tren_ligero, fe: d.paradas_ferry } })),
    partes: [{ clave: "bus", nombre: "Bus", color: PALETA[0] }, { clave: "mini", nombre: "Minibús", color: PALETA[1] }, { clave: "mtr", nombre: "MTR", color: PALETA[2] }, { clave: "lr", nombre: "Tren ligero", color: PALETA[3] }, { clave: "fe", nombre: "Ferry", color: PALETA[4] }],
    fmtV: (v) => n0(v) + " paradas" });
  };
  pintar(); estado.oyentes.push(pintar);
}

// =====================================================================
function ambiente() {
  const s = G.sensores, su = (c) => W("suelo", c);
  const aq = s.calidad_aire, fecha = aq[0]?.publicado_hkt?.replace("T", " ").slice(0, 16);
  const maxA = Math.max(...aq.map((a) => a.aqhi));
  $("#ambLead").innerHTML = `Más del ${n0(su("pct_territorio_protegido"))} % del territorio está protegido (${su("area_protegida_km2")} km² en ${su("n_country_parks")} parques naturales y ${su("n_special_areas")} áreas especiales). El agua depende del río Dongjiang en China continental (${su("pct_suministro_dongjiang_min")}–${su("pct_suministro_dongjiang_max")} % del suministro). La red de monitoreo tiene ${s.estaciones_meteorologicas.length} estaciones del Observatorio y ${aq.length} de calidad del aire; en la última captura (${fecha} HKT) el AQHI máximo fue ${maxA}: riesgo bajo.`;
  kpis("#ambKpis", [
    { v: maxA, u: "AQHI", l: "Índice de calidad del aire más alto (última captura)", f: "F27 · sensores.json", sello: "obs" },
    { v: n0(su("pct_territorio_protegido")), u: "%", l: `Territorio protegido (${su("area_protegida_km2")} km²)`, f: "F13 · perfil_wiki.json", sello: "dec" },
    { v: `${su("pct_suministro_dongjiang_min")}–${su("pct_suministro_dongjiang_max")}`, u: "%", l: "Agua importada del Dongjiang", f: "F14 · perfil_wiki.json", sello: "dec" },
    { v: su("capacidad_embalses"), u: "M m³", l: "Capacidad de los embalses", f: "F14 · perfil_wiki.json", sello: "dec" },
    { v: su("pct_especies_en_riesgo"), u: "%", l: `Especies en riesgo (de ${su("especies_evaluadas")} evaluadas)`, f: "F15 · perfil_wiki.json", sello: "dec" },
    { v: su("especies_extintas_localmente"), u: "especies", l: "Extintas localmente", f: "F15 · perfil_wiki.json", sello: "dec" },
    { v: s.estaciones_meteorologicas.length, u: "estaciones", l: "Estaciones del Observatorio", f: "F25 · sensores.json", sello: "obs" },
  ]);
  $("#aqhiFecha").textContent = `AQHI · ${fecha} HKT`;
  barrasH($("#gAqhi"), { filas: [...aq].sort((a, b) => b.aqhi - a.aqhi).map((a) => ({ etiqueta: a.estacion + (a.tipo === "borde_de_via" ? " (vía)" : ""), valor: a.aqhi, color: a.aqhi <= 3 ? "#0ca30c" : a.aqhi <= 6 ? "#fab219" : "#d03b3b" })), max: 10, fmtV: n0, anchoEtiqueta: 140, tipExtra: (f) => `<div class="muted">riesgo ${f.valor <= 3 ? "bajo" : f.valor <= 6 ? "moderado" : "alto"}</div>` });
  barrasH($("#gAgua"), { filas: [["Río Dongjiang", "pct_consumo_dongjiang_2024"], ["Agua de mar (inodoros)", "pct_consumo_agua_mar_2024"], ["Lluvia local", "pct_consumo_lluvia_local_2024"], ["Desalación", "pct_consumo_desalacion_2024"]].map(([e, c]) => ({ etiqueta: e, valor: su(c), color: PALETA[0] })), fmtV: n0, sufijo: " %", max: 100, anchoEtiqueta: 150 });
  const tipos = s.estaciones_meteorologicas.reduce((a, e) => ((a[e.tipo] = (a[e.tipo] || 0) + 1), a), {});
  const nombres = { automatica: "Automática", pluviometro: "Pluviómetro", viento: "Viento", mareografo: "Mareógrafo", boya: "Boya", tripulada: "Tripulada" };
  barrasH($("#gEstaciones"), { filas: Object.entries(tipos).sort((a, b) => b[1] - a[1]).map(([t, v]) => ({ etiqueta: nombres[t] || t, valor: v, color: PALETA[2] })), fmtV: n0, anchoEtiqueta: 100 });
}

// =====================================================================
function correlaciones() {
  const C = G.correlaciones, vars = C.variables, filas = C.dispersion;
  const ids = Object.keys(vars);
  const opts = ids.map((v) => `<option value="${v}">${vars[v]}</option>`).join("");
  $("#ejeX").innerHTML = opts; $("#ejeY").innerHTML = opts;
  let metodo = "spearman";
  $("#corMetodo").innerHTML = `<button class="chip on" data-m="spearman">Spearman</button><button class="chip" data-m="pearson">Pearson</button>`;
  const pares = C.pares_top;
  kpis("#corKpis", [
    { v: ids.length, u: "variables", l: "Métricas trazables por distrito", f: "F20–F24 · correlaciones.json", sello: "der" },
    { v: n0(ids.length * (ids.length - 1) / 2), u: "pares", l: "Pares calculados", f: "F20–F24 · correlaciones.json", sello: "der" },
    { v: 18, u: "distritos", l: "Observaciones (sin imputación)", f: "F20–F24 · correlaciones.json", sello: "obs" },
    { v: pares.filter((p) => p.significativo_5pct).length, u: "de " + pares.length, l: "Pares destacados significativos al 5 %", f: "F20–F24 · correlaciones.json", sello: "der" },
  ]);
  const presets = [["Educación e ingreso", "pct_titulo_universitario_15_mas", "ingreso_mediano_hogar_hkd_2025"], ["Vivienda pública e ingreso", "pct_vivienda_publica_alquiler", "ingreso_mediano_hogar_hkd_2025"],
    ["Densidad y transporte", "densidad_hab_km2", "paradas_por_km2"], ["Envejecimiento y crecimiento", "pct_65_mas", "var_pob_2016_2025_pct"], ["Acceso a urgencias e ingreso", "dist_media_hospital_km", "ingreso_mediano_hogar_hkd_2025"]];
  $("#corPresets").innerHTML = presets.map((p, i) => `<button class="chip${i ? "" : " on"}" data-i="${i}">${p[0]}</button>`).join("");
  $("#ejeX").value = presets[0][1]; $("#ejeY").value = presets[0][2];
  const lectura = (r) => { const a = Math.abs(r); const f = a >= 0.8 ? "muy fuerte" : a >= 0.6 ? "fuerte" : a >= 0.4 ? "moderada" : a >= 0.2 ? "débil" : "casi nula"; return `${f} · ${r >= 0 ? "directa" : "inversa"}`; };
  const fmtVar = (v) => (/ingreso/.test(v) ? (x) => "HK$ " + fmtCorto(x) : /densidad/.test(v) ? fmtCorto : (x) => fmt(x, 1));
  function pintar() {
    const x = $("#ejeX").value, y = $("#ejeY").value;
    const xs = filas.map((f) => f[x]), ys = filas.map((f) => f[y]);
    const r = metodo === "spearman" ? spearman(xs, ys) : pearson(xs, ys);
    $("#coefNombre").textContent = metodo === "spearman" ? "rho de Spearman" : "r de Pearson";
    $("#coef").textContent = (r >= 0 ? "+" : "") + fmt(r, 2);
    $("#coefLectura").textContent = lectura(r);
    dispersion($("#gDisp"), { puntos: filas.map((f) => ({ x: f[x], y: f[y], etiqueta: f.distrito_es, resaltar: f.codigo === estado.a, codigo: f.codigo })), xNombre: vars[x], yNombre: vars[y], xFmt: fmtVar(x), yFmt: fmtVar(y), alto: 360, alClic: (p) => elegirDistrito(p.codigo, "graf") });
  }
  $("#corPresets").addEventListener("click", (e) => { const b = e.target.closest(".chip"); if (!b) return; document.querySelectorAll("#corPresets .chip").forEach((c) => c.classList.toggle("on", c === b)); const p = presets[+b.dataset.i]; $("#ejeX").value = p[1]; $("#ejeY").value = p[2]; pintar(); });
  $("#corMetodo").addEventListener("click", (e) => { const b = e.target.closest(".chip"); if (!b) return; metodo = b.dataset.m; document.querySelectorAll("#corMetodo .chip").forEach((c) => c.classList.toggle("on", c === b)); pintar(); });
  ["#ejeX", "#ejeY"].forEach((s) => $(s).addEventListener("change", () => { document.querySelectorAll("#corPresets .chip").forEach((c) => c.classList.remove("on")); pintar(); }));
  $("#corSwap").addEventListener("click", () => { const t = $("#ejeX").value; $("#ejeX").value = $("#ejeY").value; $("#ejeY").value = t; pintar(); });
  $("#pares").innerHTML = [...pares].sort((a, b) => Math.abs(b.spearman_rho) - Math.abs(a.spearman_rho)).slice(0, 10).map((p) => `<div class="par" data-x="${p.var_x}" data-y="${p.var_y}"><small>${p.etiqueta_x} ${p.spearman_rho >= 0 ? "↗" : "↘"} ${p.etiqueta_y}</small><b>${p.spearman_rho >= 0 ? "+" : ""}${fmt(p.spearman_rho, 2)}</b><em>Spearman · n=18</em></div>`).join("");
  $("#pares").addEventListener("click", (e) => { const c = e.target.closest(".par"); if (!c) return; $("#ejeX").value = c.dataset.x; $("#ejeY").value = c.dataset.y; document.querySelectorAll("#corPresets .chip").forEach((x) => x.classList.remove("on")); pintar(); document.getElementById("gDisp").scrollIntoView({ block: "center" }); });
  pintar(); estado.oyentes.push(pintar);
}

// =====================================================================
function atlas() {
  const D = G.D;
  const dims = [
    { nombre: "Prosperidad", desc: "Ingreso mediano del hogar 2025 · % con título universitario", v: [["ingreso_mediano_hogar_hkd_2025"], ["pct_titulo_universitario_15_mas"]] },
    { nombre: "Empleo", desc: "Participación laboral 2025 · ocupados sobre fuerza laboral 2021", v: [["tasa_participacion_laboral_pct_2025"], ["tasa_ocupacion_sobre_fuerza_laboral_pct"]] },
    { nombre: "Transporte", desc: "Paradas por 10.000 hab · paradas por km² · rutas distintas", v: [["paradas_por_10k_hab"], ["paradas_por_km2"], ["rutas_distintas"]] },
    { nombre: "Salud", desc: "Distancia media a urgencias (↓ mejor) · habitantes por hospital (↓ mejor)", v: [["dist_media_hospital_km", true], ["hab_por_hospital_urgencias", true]] },
    { nombre: "Dinamismo", desc: "Crecimiento de la población 2016–2025 · % de 65+ (↓ mejor) · crecimiento del ingreso", v: [["var_pob_2016_2025_pct"], ["pct_65_mas", true], ["var_ingreso_2016_2025_pct"]] },
  ];
  for (const dm of dims) {
    const partes = dm.v.map(([c, inv]) => {
      const vals = D.map((d) => d[c]);
      const peor = inv ? Math.max(...vals.filter((v) => v != null)) * 1.15 : 0; // sin hospital = peor que el peor
      return norm(vals.map((v) => (v == null ? peor : v)), inv);
    });
    dm.p = D.map((_, i) => partes.reduce((s, p) => s + p[i], 0) / partes.length);
  }
  const pesos = dims.map(() => 1);
  $("#atlasPesos").innerHTML = dims.map((d, i) => `<div class="peso"><div class="t"><b style="font-weight:600;color:var(--rojo)">${d.nombre}</b><span id="ap${i}">1</span></div><input type="range" min="0" max="3" step="1" value="1" data-i="${i}" aria-label="Peso ${d.nombre}"><div class="mono muted" style="font-size:10px;margin-top:4px;line-height:1.35">${d.desc}</div></div>`).join("");
  const presets = { Equilibrado: [1, 1, 1, 1, 1], "Prosperidad primero": [3, 1, 1, 1, 1], "Servicios (transporte y salud)": [1, 1, 3, 3, 1], Dinamismo: [1, 1, 1, 1, 3] };
  $("#atlasPresets").innerHTML = Object.keys(presets).map((p, i) => `<button class="chip${i ? "" : " on"}" data-p="${p}">${p}</button>`).join("") + `<a class="chip" href="#mapa" style="text-decoration:none">▲ ver en el mapa</a>`;
  const mini = (v) => `<span class="mini"><span class="pista"><i style="width:${Math.max(3, v)}%"></i></span>${n0(v)}</span>`;
  function pintar() {
    const s = pesos.reduce((a, b) => a + b, 0) || 1;
    pesos.forEach((p, i) => ($("#ap" + i).textContent = p));
    const idx = D.map((_, i) => dims.reduce((a, dm, j) => a + dm.p[i] * pesos[j], 0) / s);
    const orden = D.map((d, i) => ({ d, i, v: idx[i] })).sort((a, b) => b.v - a.v);
    G.indiceAtlas = Object.fromEntries(orden.map((o) => [o.d.codigo, o.v]));
    const vs = orden.map((o) => o.v);
    $("#atlasResumen").innerHTML = `Con estos pesos: <b>${orden[0].d.distrito_es}</b> lidera (${n0(orden[0].v)}) y <b>${orden[17].d.distrito_es}</b> cierra (${n0(orden[17].v)}); brecha de ${n0(vs[0] - vs[17])} puntos, mediana ${n0(mediana(vs))}.`;
    $("#atlasTabla").innerHTML = `<thead><tr><th>#</th><th>Distrito</th><th>Índice</th>${dims.map((d) => `<th>${d.nombre}</th>`).join("")}<th>Tipología</th></tr></thead><tbody>` +
      orden.map((o, k) => `<tr class="clic" data-c="${o.d.codigo}"${o.d.codigo === estado.a ? ' style="background:var(--rojo-suave)"' : ""}><td class="n">${k + 1}</td><td><b>${o.d.distrito_es}</b> <span class="muted">${o.d.distrito_zh}</span><div class="mono muted" style="font-size:10px">${n1(o.d.area_km2_oficial)} km² · ${n0(o.d.poblacion_2025)} hab</div></td>
        <td><span class="indice-pill${k < 3 ? " top" : ""}">${n0(o.v)}</span></td>${dims.map((dm) => `<td>${mini(dm.p[o.i])}</td>`).join("")}<td><span class="tipo-pill">${o.d.tipologia}</span></td></tr>`).join("") + "</tbody>";
  }
  $("#atlasPesos").addEventListener("input", (e) => { pesos[+e.target.dataset.i] = +e.target.value; document.querySelectorAll("#atlasPresets .chip").forEach((c) => c.classList.remove("on")); pintar(); });
  $("#atlasPresets").addEventListener("click", (e) => { const b = e.target.closest(".chip[data-p]"); if (!b) return; document.querySelectorAll("#atlasPresets .chip").forEach((c) => c.classList.toggle("on", c === b)); presets[b.dataset.p].forEach((v, i) => (pesos[i] = v)); document.querySelectorAll("#atlasPesos input").forEach((r, i) => (r.value = pesos[i])); pintar(); });
  $("#atlasTabla").addEventListener("click", (e) => { const tr = e.target.closest("tr[data-c]"); if (!tr) return; elegirDistrito(tr.dataset.c, "atlas"); G.mapa?.enfocar(tr.dataset.c); document.getElementById("mapa").scrollIntoView(); });
  pintar(); estado.oyentes.push(pintar);
}

// =====================================================================
const NOMBRE_TEMA = { vivienda: "Vivienda", comercio: "Comercio", transporte: "Transporte", desarrollo: "Desarrollo urbano", ambiente: "Ambiente", turismo: "Turismo", salud: "Salud" };
function titularesHTML(lista) {
  return lista.map((n) => `<a class="titular" href="${esc(n.url)}" target="_blank" rel="noopener"><span class="tema-tag">${NOMBRE_TEMA[n.tema] || n.tema}</span><span>${esc(n.titular)}<small>${esc(n.fuente)}${n.distritos_mencionados ? " · " + String(n.distritos_mencionados).split("|").map(G.nombre).join(", ") : ""}</small></span><span class="tono ${n.tono}">${n.tono}</span></a>`).join("");
}
function escucha() {
  const E = G.escucha, N = E.noticias;
  const pos = N.filter((n) => n.tono === "positivo").length, neg = N.filter((n) => n.tono === "negativo").length;
  const temas = [...E.temas].sort((a, b) => b.menciones - a.menciones);
  const men = E.menciones_por_distrito.filter((m) => m.menciones_noticias > 0).sort((a, b) => b.menciones_noticias - a.menciones_noticias);
  $("#escLead").innerHTML = `Qué se dice de Hong Kong en la prensa: <b>${N.length} titulares</b> en ${temas.length} temas, capturados el ${N[0].fecha_captura}. Domina <b>${(NOMBRE_TEMA[temas[0].tema] || temas[0].tema).toLowerCase()}</b> (${temas[0].menciones} titulares), seguido de ${(NOMBRE_TEMA[temas[1].tema] || temas[1].tema).toLowerCase()}. ${men.length ? `El distrito más nombrado es ${men[0].distrito_es} (${men[0].menciones_noticias} titulares).` : ""} El tono es una señal gruesa por léxico, no un análisis de sentimiento validado.`;
  kpis("#escKpis", [
    { v: N.length, u: "titulares", l: "Titulares capturados", f: "F32 · escucha.json", sello: "obs" },
    { v: temas.length, u: "temas", l: "Temas monitoreados", f: "F32 · escucha.json", sello: "der" },
    { v: n0(100 * pos / N.length), u: "%", l: "Titulares con tono positivo", f: "F32 · escucha.json", sello: "der" },
    { v: n0(100 * neg / N.length), u: "%", l: "Titulares con tono negativo", f: "F32 · escucha.json", sello: "der" },
    { v: men.length, u: "distritos", l: "Distritos nombrados en titulares", f: "F32, F33 · escucha.json", sello: "der" },
  ]);
  apiladaH($("#gTemas"), { filas: temas.map((t) => ({ etiqueta: NOMBRE_TEMA[t.tema] || t.tema, valores: { p: t.positivas, n: t.menciones - t.positivas - t.negativas, x: t.negativas } })),
    partes: [{ clave: "p", nombre: "Positivo", color: PALETA[1] }, { clave: "n", nombre: "Neutral", color: "#d9c9c6" }, { clave: "x", nombre: "Negativo", color: PALETA[2] }], fmtV: (v) => n0(v) + " titulares", anchoEtiqueta: 120 });
  $("#escNota").textContent = E.nota_metodologica;
  barrasH($("#gMenciones"), { filas: men.map((m) => ({ etiqueta: m.distrito_es, valor: m.menciones_noticias, resaltar: m.codigo === estado.a, alClic: () => elegirDistrito(m.codigo, "graf") })), fmtV: n0 });
  let filtro = "todos";
  $("#escFiltro").innerHTML = `<button class="chip on" data-t="todos">Todos</button>` + temas.map((t) => `<button class="chip" data-t="${t.tema}">${NOMBRE_TEMA[t.tema] || t.tema}</button>`).join("");
  const pintar = () => ($("#escLista").innerHTML = titularesHTML(N.filter((n) => filtro === "todos" || n.tema === filtro)));
  $("#escFiltro").addEventListener("click", (e) => { const b = e.target.closest(".chip"); if (!b) return; filtro = b.dataset.t; document.querySelectorAll("#escFiltro .chip").forEach((c) => c.classList.toggle("on", c === b)); pintar(); });
  pintar();
}

// =====================================================================
function fuentes() {
  const FU = G.fuentes.fuentes;
  const cuenta = (f) => FU.filter(f).length;
  const integ = cuenta((x) => x.estado === "Integrada al lago"), riesgo = cuenta((x) => x.riesgo_licencia), noVer = cuenta((x) => !x.licencia_verificada && x.licencia !== "no declara");
  $("#fuentesLead").innerHTML = `<b>${FU.length} fuentes en un solo catálogo</b> (F01–F18 registradas por el equipo en la wiki; F19–F34 descargadas por el pipeline; F35–F45 probadas y no integradas): ${integ} <span class="estado integrada">integradas</span> · ${cuenta((x) => x.estado === "Candidata")} <span class="estado candidata">candidatas</span> · ${cuenta((x) => /Descartada|No existe|No responde/.test(x.estado))} <span class="estado descartada">descartadas o sin respuesta</span>. Las licencias se copian <b>literales, en inglés</b>, tal como aparecen en cada sitio (revisadas ${G.fuentes.fecha_licencias}); ${noVer} quedan como «not verified» porque la herramienta no pudo abrir la página de avisos, y ${riesgo} tienen términos restrictivos o condicionados.`;
  const filtros = [["todas", () => true], ["integradas", (x) => x.estado === "Integrada al lago"], ["candidatas", (x) => x.estado === "Candidata"],
    ["descartadas / no existen", (x) => /Descartada|No existe|No responde/.test(x.estado)], ["licencia restrictiva", (x) => x.riesgo_licencia], ["licencia sin verificar", (x) => !x.licencia_verificada && x.licencia !== "no declara"]];
  $("#fuentesFiltro").innerHTML = filtros.map(([n], i) => `<button class="chip${i ? "" : " on"}" data-i="${i}">${n}</button>`).join("");
  const clase = (e) => (e === "Integrada al lago" ? "integrada" : e === "Candidata" ? "candidata" : "descartada");
  const pintar = (f) => {
    $("#fuentesTabla").innerHTML = `<thead><tr><th>ID</th><th>Dataset y entidad</th><th>Estado</th><th>Licencia (literal, tal como aparece)</th><th>Archivo del lago</th><th>URL</th></tr></thead><tbody>` +
      FU.filter(f).map((x) => `<tr><td class="mono" style="font-size:12px;font-weight:600;color:var(--rojo-osc)">${x.id}</td>
        <td><b>${esc(x.nombre)}</b><div class="muted" style="font-size:11.5px">${esc(x.entidad)}</div>${x.observaciones ? `<div class="muted" style="font-size:11px;margin-top:3px">${esc(x.observaciones)}</div>` : ""}</td>
        <td><span class="estado ${clase(x.estado)}">${esc(x.estado.toLowerCase())}</span>${x.riesgo_licencia ? `<div style="margin-top:4px"><span class="estado riesgo">licencia ${x.riesgo_licencia}</span></div>` : ""}</td>
        <td style="font-size:11.5px;max-width:420px">${x.licencia_verificada || x.licencia === "no declara" ? "" : '<span class="estado candidata">not verified</span> '}${esc(x.licencia)}${x.url_licencia ? `<div class="mono muted" style="font-size:10px;margin-top:3px"><a href="${esc(x.url_licencia)}" target="_blank" rel="noopener">${esc(x.url_licencia.replace(/^https?:\/\//, "").slice(0, 60))}</a></div>` : ""}</td>
        <td class="mono" style="font-size:10.5px">${x.archivos_lago.length ? x.archivos_lago.map((a) => `data/${a}`).join("<br>") : '<span class="muted">—</span>'}</td>
        <td>${/^https?:/.test(x.url) ? `<a href="${esc(x.url)}" target="_blank" rel="noopener" aria-label="Abrir ${x.id}">↗</a>` : ""}</td></tr>`).join("") + "</tbody>";
  };
  $("#fuentesFiltro").addEventListener("click", (e) => { const b = e.target.closest(".chip"); if (!b) return; document.querySelectorAll("#fuentesFiltro .chip").forEach((c) => c.classList.toggle("on", c === b)); pintar(filtros[+b.dataset.i][1]); });
  pintar(filtros[0][1]);
  const C = G.conciliacion.filas;
  $("#conciliacionTabla").innerHTML = `<thead><tr><th>Indicador</th><th>Wiki (a mano)</th><th>Lago (descargado)</th><th>Diagnóstico</th><th>Decisión en la página</th></tr></thead><tbody>` +
    C.map((r) => `<tr><td><b>${esc(r.indicador)}</b><div class="mono muted" style="font-size:10px">${esc(r.campo_wiki)}</div></td><td class="n">${fmt(r.valor_wiki)}<div class="mono muted" style="font-size:10px">${r.fuente_wiki}</div></td>
      <td class="n">${fmt(r.valor_lago)}<div class="mono muted" style="font-size:10px">${r.fuente_lago} · ${esc(r.campo_lago)}</div></td><td style="font-size:12px">${esc(r.diagnostico)}</td><td style="font-size:12px"><b>${esc(r.decision)}</b></td></tr>`).join("") + "</tbody>";
  $("#estadoLago").textContent = `lago único: ${FU.length} fuentes · ${integ} integradas`;
}

// =====================================================================
// trazabilidad: cada gráfico dice qué archivo del repo lee, qué campo y de qué fuente (F0x)
const TRAZAS = {
  gPobTotal: ["demografia.json", "serie_poblacion[].poblacion_mitad_anio (suma de 18 distritos)", ["F21"]],
  gEdad: ["demografia.json", "piramide_hk_2021", ["F20"]],
  gPobDist: ["atlas_zonas.json", "distritos[].poblacion_2025", ["F21"]],
  gEnvej: ["atlas_zonas.json", "distritos[].pct_65_mas", ["F20"]],
  gCrec: ["atlas_zonas.json", "distritos[].var_pob_2016_2025_pct", ["F21"]],
  gEdu: ["atlas_zonas.json", "distritos[].pct_titulo_universitario_15_mas", ["F20"]],
  gNatal: ["perfil_wiki.json", "temas.poblacion.tasa_bruta_natalidad_{1981,2011,2025}", ["F04"]],
  gIngreso: ["economia.json", "serie_distritos[].ingreso_mediano_hogar_hkd", ["F21"]],
  gRankIng: ["atlas_zonas.json", "distritos[].ingreso_mediano_hogar_hkd_2025", ["F21"]],
  gPib: ["economia.json", "macro[].pib_per_capita_usd_corrientes", ["F28"]],
  gInfl: ["economia.json", "macro[].inflacion_ipc_pct", ["F30"]],
  gTenencia: ["atlas_zonas.json", "distritos[].pct_vivienda_{publica_alquiler,subsidiada_venta,privada}", ["F20"]],
  gOferta: ["perfil_wiki.json", "temas.vivienda.{viviendas_privadas_terminadas_2024,oferta_privada_prevista_2026,oferta_privada_prevista_2027}", ["F05"]],
  gLlegadas: ["perfil_wiki.json", "temas.turismo.llegadas_*", ["F12"]],
  gParques: ["perfil_wiki.json", "suelo_parques[].area_ha", ["F13"]],
  turNoticias: ["escucha.json", "noticias[] (tema = turismo)", ["F32"]],
  gFin: ["perfil_wiki.json", "temas.finanzas_publicas.{ingreso_*,gasto_*,impuestos_*,derechos_timbre_*}", ["F08"]],
  gBalance: ["perfil_wiki.json", "temas.finanzas_publicas.{superavit_consolidado_*,deficit_capital_2026_27}", ["F08"]],
  gDelitos: ["escucha.json", "delitos_mensuales[].{delitos_totales,delitos_violentos}", ["F31"]],
  gVarDelitos: ["perfil_wiki.json", "temas.seguridad.var_*", ["F10"]],
  gParadas10k: ["atlas_zonas.json", "distritos[].paradas_por_10k_hab", ["F23", "F20"]],
  gDistHosp: ["atlas_zonas.json", "distritos[].dist_media_hospital_km", ["F24", "F19"]],
  gMtr: ["atlas_zonas.json", "distritos[].paradas_metro_mtr", ["F23"]],
  gModos: ["atlas_zonas.json", "distritos[].paradas_{bus,minibus,metro_mtr,tren_ligero,ferry}", ["F23"]],
  gAqhi: ["sensores.json", "calidad_aire[].aqhi", ["F27"]],
  gAgua: ["perfil_wiki.json", "temas.suelo.pct_consumo_*_2024", ["F14"]],
  gEstaciones: ["sensores.json", "estaciones_meteorologicas[].tipo", ["F25"]],
  gDisp: ["correlaciones.json", "dispersion[] (17 variables de 18 distritos)", ["F20", "F21", "F22", "F23", "F24"]],
  atlasTabla: ["atlas_zonas.json", "distritos[] (14 variables en 5 dimensiones)", ["F19", "F20", "F21", "F23", "F24"]],
  gTemas: ["escucha.json", "temas[].{positivas,negativas,menciones}", ["F32"]],
  gMenciones: ["escucha.json", "menciones_por_distrito[].menciones_noticias", ["F32", "F33"]],
  escLista: ["escucha.json", "noticias[]", ["F32"]],
};
function trazar() {
  const nombre = (id) => G.fuentes.fuentes.find((f) => f.id === id)?.entidad?.split(/[,(;]/)[0].trim() ?? id;
  for (const [id, [archivo, campo, ids]] of Object.entries(TRAZAS)) {
    const nodo = document.getElementById(id); if (!nodo) { console.warn("[traza] falta", id); continue; }
    const host = nodo.closest(".tabla-scroll") || nodo;
    const p = document.createElement("p"); p.className = "fuente";
    p.innerHTML = `<b>${ids.join(" · ")}</b> ${ids.map(nombre).filter((v, i, a) => a.indexOf(v) === i).join(" · ")} — archivo <code>data/${archivo}</code> → ${campo}`;
    host.insertAdjacentElement("afterend", p);
  }
}

// =====================================================================
// navegación, reloj, clima, paleta
function cromo() {
  const enlaces = [...document.querySelectorAll("#nav a")];
  const secs = enlaces.map((a) => document.querySelector(a.getAttribute("href")));
  const obs = new IntersectionObserver((ents) => {
    for (const e of ents) if (e.isIntersecting) {
      const a = enlaces[secs.indexOf(e.target)];
      enlaces.forEach((x) => x.classList.toggle("activo", x === a));
      $("#migas").textContent = a.querySelector("i").textContent + " " + a.textContent.slice(1);
    }
  }, { rootMargin: "-45% 0px -50% 0px" });
  secs.forEach((s) => obs.observe(s));
  $("#btnMenu").addEventListener("click", () => $("#lateral").classList.toggle("abierta"));
  enlaces.forEach((a) => a.addEventListener("click", () => $("#lateral").classList.remove("abierta")));
  const reloj = () => ($("#reloj").textContent = new Intl.DateTimeFormat("es-CO", { timeZone: "Asia/Hong_Kong", weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }).format(new Date()) + " HKT");
  reloj(); setInterval(reloj, 30000);
  // solo datos del repo: AQHI de la última captura (sensores.json, F27); no hay consultas en vivo
  const aqMax = Math.max(...G.sensores.calidad_aire.map((a) => a.aqhi));
  $("#clima").textContent = `AQHI máx. ${aqMax} · captura ${G.sensores.calidad_aire[0].publicado_hkt.slice(0, 10)} (F27)`;
  // paleta de comandos
  const items = [...enlaces.map((a) => ({ t: a.textContent.slice(1).trim(), s: "sección", ir: () => document.querySelector(a.getAttribute("href")).scrollIntoView() })),
    ...G.D.map((d) => ({ t: `${d.distrito_es} · ${d.distrito_en}`, s: d.distrito_zh, ir: () => { elegirDistrito(d.codigo, "paleta"); document.getElementById("diagnostico").scrollIntoView(); } })),
    ...Object.entries(G.barrios).map(([b, v]) => ({ t: b, s: "barrio → " + G.nombre(v.codigo), ir: () => { elegirDistrito(v.codigo, "paleta"); document.getElementById("diagnostico").scrollIntoView(); } }))];
  let sel = 0, vis = [];
  const abrir = () => { $("#paletaFondo").style.display = "flex"; $("#paletaInput").value = ""; filtrar(); $("#paletaInput").focus(); };
  const cerrar = () => ($("#paletaFondo").style.display = "none");
  const filtrar = () => {
    const q = $("#paletaInput").value.toLowerCase();
    vis = items.filter((i) => (i.t + " " + i.s).toLowerCase().includes(q)).slice(0, 12); sel = 0;
    $("#paletaLista").innerHTML = vis.map((i, k) => `<li class="${k === sel ? "sel" : ""}" data-k="${k}">${esc(i.t)}<small>${esc(i.s)}</small></li>`).join("") || `<li>Sin resultados</li>`;
  };
  $("#abrirPaleta").addEventListener("click", abrir);
  addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); abrir(); }
    if ($("#paletaFondo").style.display !== "flex") return;
    if (e.key === "Escape") cerrar();
    if (e.key === "ArrowDown" || e.key === "ArrowUp") { e.preventDefault(); sel = (sel + (e.key === "ArrowDown" ? 1 : -1) + vis.length) % vis.length; document.querySelectorAll("#paletaLista li").forEach((l, k) => l.classList.toggle("sel", k === sel)); }
    if (e.key === "Enter" && vis[sel]) { cerrar(); vis[sel].ir(); }
  });
  $("#paletaInput").addEventListener("input", filtrar);
  $("#paletaLista").addEventListener("click", (e) => { const li = e.target.closest("li[data-k]"); if (li) { cerrar(); vis[+li.dataset.k].ir(); } });
  $("#paletaFondo").addEventListener("click", (e) => e.target === $("#paletaFondo") && cerrar());
}

// =====================================================================
(async function iniciar() {
  try { await cargar(); } catch (e) {
    document.querySelector("main").insertAdjacentHTML("afterbegin", `<div class="tarjeta" style="margin-top:20px;border-color:var(--critico)">No se pudieron cargar los datos del lago (${esc(e.message)}). Abre la página desde un servidor (no como archivo local).</div>`);
    return;
  }
  const pasos = [panorama, gente, economia, turismo, gobierno, seguridad, infraestructura, ambiente, correlaciones, atlas, escucha, fuentes, trazar, cromo];
  for (const p of pasos) { try { p(); } catch (e) { console.error(`[cerebro] ${p.name}:`, e); } }
  try { G.mapa = await iniciarMapa(G, estado, elegirDistrito); } catch (e) { console.error("[cerebro] mapa:", e); }
})();
