// Gráficos SVG livianos para Cerebro HK (sin dependencias).
// Reglas: un solo eje Y, marcas finas, extremos redondeados, tooltip en hover, texto en tinta (no en color de serie).
const NS = "http://www.w3.org/2000/svg";
export const PALETA = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#9085e9"];
export const CORAL = "#ff8152";
const TINTA3 = "#789096";

const fmtNum = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 1 });
export const fmt = (v, dec) => (v == null || Number.isNaN(v) ? "—" : dec != null
  ? new Intl.NumberFormat("es-CO", { minimumFractionDigits: dec, maximumFractionDigits: dec }).format(v)
  : fmtNum.format(v));
export const fmtCorto = (v) => {
  const a = Math.abs(v);
  if (a >= 1e9) return fmt(v / 1e9, 1) + " mil M";
  if (a >= 1e6) return fmt(v / 1e6, a >= 1e7 ? 1 : 2) + " M";
  if (a >= 1e4) return fmt(v / 1e3, 0) + " k";
  return fmt(v);
};

function el(tag, attrs = {}, parent) {
  const n = document.createElementNS(NS, tag);
  for (const k in attrs) n.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(n);
  return n;
}

// ---------- tooltip compartido ----------
let tipEl;
function tip() {
  if (!tipEl) { tipEl = document.createElement("div"); tipEl.className = "tip"; document.body.appendChild(tipEl); }
  return tipEl;
}
export function mostrarTip(ev, html) {
  const t = tip();
  t.innerHTML = html; t.style.opacity = 1;
  const r = t.getBoundingClientRect();
  let x = ev.clientX + 14, y = ev.clientY + 14;
  if (x + r.width > innerWidth - 8) x = ev.clientX - r.width - 14;
  if (y + r.height > innerHeight - 8) y = ev.clientY - r.height - 14;
  t.style.left = x + "px"; t.style.top = y + "px";
}
export function ocultarTip() { if (tipEl) tipEl.style.opacity = 0; }

function escalaLineal(d0, d1, r0, r1) {
  const f = (v) => r0 + ((v - d0) / (d1 - d0 || 1)) * (r1 - r0);
  f.inv = (p) => d0 + ((p - r0) / (r1 - r0 || 1)) * (d1 - d0);
  return f;
}
function ticks(min, max, n = 4) {
  const span = max - min || 1;
  const paso0 = span / n, mag = Math.pow(10, Math.floor(Math.log10(paso0)));
  const paso = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((p) => span / p <= n + 0.5) || mag * 10;
  const t = [];
  for (let v = Math.ceil(min / paso) * paso; v <= max + 1e-9; v += paso) t.push(+v.toFixed(10));
  return t;
}
function contenedor(nodo, alto) {
  nodo.innerHTML = "";
  nodo.classList.add("graf");
  const ancho = Math.max(nodo.clientWidth || 600, 260);
  const svg = el("svg", { viewBox: `0 0 ${ancho} ${alto}`, role: "img" }, nodo);
  return { svg, ancho };
}
function redibujable(nodo, dibujar) {
  dibujar();
  if (nodo._ro) return;
  let w = nodo.clientWidth;
  nodo._ro = new ResizeObserver(() => { if (Math.abs(nodo.clientWidth - w) > 8) { w = nodo.clientWidth; dibujar(); } });
  nodo._ro.observe(nodo);
}
function leyenda(nodo, series) {
  if (series.length < 2) return;
  const l = document.createElement("div"); l.className = "leyenda";
  l.innerHTML = series.map((s) => `<span><i style="background:${s.color}"></i>${s.nombre}</span>`).join("");
  nodo.appendChild(l);
}

// ---------- líneas (con crosshair) ----------
export function lineas(nodo, { series, alto = 260, yFmt = fmtCorto, xFmt = (x) => x, yMin, etiquetas = true, desde0 = false }) {
  redibujable(nodo, () => {
    const { svg, ancho } = contenedor(nodo, alto);
    const m = { t: 12, r: etiquetas ? 110 : 16, b: 26, l: 48 };
    const xs = [...new Set(series.flatMap((s) => s.valores.map((p) => p.x)))].sort((a, b) => a - b);
    const ys = series.flatMap((s) => s.valores.map((p) => p.y)).filter((v) => v != null);
    let y0 = yMin ?? (desde0 ? 0 : Math.min(...ys)), y1 = Math.max(...ys);
    const pad = (y1 - y0) * 0.08 || 1; if (!desde0 && yMin == null) y0 -= pad; y1 += pad;
    const X = escalaLineal(xs[0], xs[xs.length - 1], m.l, ancho - m.r), Y = escalaLineal(y0, y1, alto - m.b, m.t);
    const g = el("g", { class: "eje" }, svg);
    for (const t of ticks(y0, y1)) {
      el("line", { x1: m.l, x2: ancho - m.r, y1: Y(t), y2: Y(t), class: "rejilla-l" }, g);
      el("text", { x: m.l - 8, y: Y(t) + 3, "text-anchor": "end" }, g).textContent = yFmt(t);
    }
    const cada = Math.ceil(xs.length / Math.max(2, Math.floor((ancho - m.l - m.r) / 70)));
    xs.forEach((x, i) => { if (i % cada === 0 || i === xs.length - 1) el("text", { x: X(x), y: alto - 8, "text-anchor": "middle" }, g).textContent = xFmt(x); });
    const ultY = [];
    for (const s of series) {
      const pts = s.valores.filter((p) => p.y != null);
      const d = pts.map((p, i) => `${i ? "L" : "M"}${X(p.x).toFixed(1)},${Y(p.y).toFixed(1)}`).join("");
      el("path", { d, fill: "none", stroke: s.color, "stroke-width": s.grosor || 2, "stroke-linejoin": "round", "stroke-linecap": "round", opacity: s.tenue ? 0.35 : 1, "stroke-dasharray": s.punteada ? "4 4" : "" }, svg);
      if (etiquetas && !s.tenue && pts.length) {
        const p = pts[pts.length - 1]; let yy = Y(p.y);
        while (ultY.some((u) => Math.abs(u - yy) < 12)) yy += 12;
        ultY.push(yy);
        el("circle", { cx: X(p.x), cy: Y(p.y), r: 3.5, fill: s.color, stroke: "#0f1b20", "stroke-width": 2 }, svg);
        const t = el("text", { x: X(p.x) + 8, y: yy + 3, "font-family": "var(--mono)", "font-size": 10, fill: "#a8bbc0" }, svg);
        t.textContent = s.nombre.length > 14 ? s.nombre.slice(0, 13) + "…" : s.nombre;
      }
    }
    // crosshair
    const cruz = el("line", { y1: m.t, y2: alto - m.b, stroke: TINTA3, "stroke-width": 1, "stroke-dasharray": "3 3", opacity: 0 }, svg);
    const zona = el("rect", { x: m.l, y: m.t, width: ancho - m.l - m.r, height: alto - m.t - m.b, fill: "transparent" }, svg);
    zona.addEventListener("mousemove", (ev) => {
      const r = svg.getBoundingClientRect(), px = (ev.clientX - r.left) * (ancho / r.width);
      const xv = xs.reduce((a, b) => (Math.abs(X(b) - px) < Math.abs(X(a) - px) ? b : a));
      cruz.setAttribute("x1", X(xv)); cruz.setAttribute("x2", X(xv)); cruz.setAttribute("opacity", 1);
      const filas = series.map((s) => ({ s, p: s.valores.find((p) => p.x === xv) })).filter((o) => o.p && o.p.y != null)
        .sort((a, b) => b.p.y - a.p.y).slice(0, 10);
      mostrarTip(ev, `<div class="tt">${xFmt(xv)}</div>` + filas.map((o) => `<div class="fila"><span><i style="background:${o.s.color}"></i>${o.s.nombre}</span><b>${yFmt(o.p.y)}</b></div>`).join(""));
    });
    zona.addEventListener("mouseleave", () => { cruz.setAttribute("opacity", 0); ocultarTip(); });
    leyenda(nodo, series.filter((s) => !s.tenue));
  });
}

// ---------- barras horizontales ----------
export function barrasH(nodo, { filas, fmtV = fmt, alto, color = PALETA[0], max, sufijo = "", anchoEtiqueta = 130, tipExtra }) {
  redibujable(nodo, () => {
    const h = alto || filas.length * 24 + 8;
    const { svg, ancho } = contenedor(nodo, h);
    const vmax = max ?? Math.max(...filas.map((f) => f.valor));
    const vmin = Math.min(0, ...filas.map((f) => f.valor));
    const X = escalaLineal(vmin, vmax, anchoEtiqueta, ancho - 70);
    const fh = (h - 8) / filas.length;
    filas.forEach((f, i) => {
      const y = 4 + i * fh, bh = Math.min(12, fh - 6);
      el("text", { x: anchoEtiqueta - 8, y: y + fh / 2 + 3.5, "text-anchor": "end", "font-size": 11, fill: f.resaltar ? "#edf4f5" : "#a8bbc0", "font-weight": f.resaltar ? 600 : 400 }, svg)
        .textContent = f.etiqueta;
      const x0 = X(Math.min(0, f.valor)), w = Math.max(2, Math.abs(X(f.valor) - X(0)));
      el("rect", { x: x0, y: y + (fh - bh) / 2, width: w, height: bh, rx: 3, fill: f.color || (f.resaltar ? CORAL : color) }, svg);
      el("text", { x: X(Math.max(0, f.valor)) + 6, y: y + fh / 2 + 3.5, "font-family": "var(--mono)", "font-size": 10, fill: "#a8bbc0" }, svg)
        .textContent = fmtV(f.valor) + sufijo;
      const hit = el("rect", { x: 0, y, width: ancho, height: fh, fill: "transparent" }, svg);
      hit.addEventListener("mousemove", (ev) => mostrarTip(ev, `<div class="tt">${f.etiqueta}</div><b>${fmtV(f.valor)}${sufijo}</b>${tipExtra ? tipExtra(f) : ""}`));
      hit.addEventListener("mouseleave", ocultarTip);
      if (f.alClic) { hit.style.cursor = "pointer"; hit.addEventListener("click", () => f.alClic(f)); }
    });
  });
}

// ---------- barras horizontales apiladas (composición) ----------
export function apiladaH(nodo, { filas, partes, alto, anchoEtiqueta = 130, fmtV = (v) => fmt(v, 1) + " %" }) {
  redibujable(nodo, () => {
    const h = alto || filas.length * 22 + 8;
    const { svg, ancho } = contenedor(nodo, h);
    const fh = (h - 8) / filas.length, W = ancho - anchoEtiqueta - 8;
    filas.forEach((f, i) => {
      const y = 4 + i * fh, bh = Math.min(12, fh - 6);
      el("text", { x: anchoEtiqueta - 8, y: y + fh / 2 + 3.5, "text-anchor": "end", "font-size": 11, fill: f.resaltar ? "#edf4f5" : "#a8bbc0" }, svg).textContent = f.etiqueta;
      const total = partes.reduce((a, p) => a + (f.valores[p.clave] || 0), 0) || 1;
      let x = anchoEtiqueta;
      partes.forEach((p) => {
        const w = (W * (f.valores[p.clave] || 0)) / total;
        if (w > 0) el("rect", { x, y: y + (fh - bh) / 2, width: Math.max(0, w - 2), height: bh, rx: 2, fill: p.color }, svg);
        x += w;
      });
      const hit = el("rect", { x: 0, y, width: ancho, height: fh, fill: "transparent" }, svg);
      hit.addEventListener("mousemove", (ev) => mostrarTip(ev, `<div class="tt">${f.etiqueta}</div>` +
        partes.map((p) => `<div class="fila"><span><i style="background:${p.color}"></i>${p.nombre}</span><b>${fmtV(f.valores[p.clave] || 0)}</b></div>`).join("")));
      hit.addEventListener("mouseleave", ocultarTip);
    });
    leyenda(nodo, partes.map((p) => ({ nombre: p.nombre, color: p.color })));
  });
}

// ---------- columnas (categorías o años) ----------
export function columnas(nodo, { filas, alto = 220, color = PALETA[0], fmtV = fmtCorto, etiquetasValor = true }) {
  redibujable(nodo, () => {
    const { svg, ancho } = contenedor(nodo, alto);
    const m = { t: 18, r: 8, b: 26, l: 44 };
    const vals = filas.map((f) => f.valor);
    const y0 = Math.min(0, ...vals), y1 = Math.max(0, ...vals) * 1.08 || 1;
    const Y = escalaLineal(y0, y1, alto - m.b, m.t);
    const g = el("g", { class: "eje" }, svg);
    for (const t of ticks(y0, y1)) {
      el("line", { x1: m.l, x2: ancho - m.r, y1: Y(t), y2: Y(t), class: "rejilla-l" }, g);
      el("text", { x: m.l - 8, y: Y(t) + 3, "text-anchor": "end" }, g).textContent = fmtV(t);
    }
    const bw = (ancho - m.l - m.r) / filas.length;
    const cada = Math.ceil(filas.length / Math.max(2, Math.floor((ancho - m.l - m.r) / 46)));
    filas.forEach((f, i) => {
      const x = m.l + i * bw, w = Math.max(3, Math.min(42, bw - 4));
      const ya = Y(Math.max(0, f.valor)), yb = Y(Math.min(0, f.valor));
      el("rect", { x: x + (bw - w) / 2, y: ya, width: w, height: Math.max(1.5, yb - ya), rx: 3, fill: f.color || color }, svg);
      if (i % cada === 0) el("text", { x: x + bw / 2, y: alto - 8, "text-anchor": "middle" }, g).textContent = f.etiqueta;
      if (etiquetasValor && filas.length <= 8) el("text", { x: x + bw / 2, y: (f.valor >= 0 ? ya - 5 : yb + 12), "text-anchor": "middle", "font-family": "var(--mono)", "font-size": 10, fill: "#a8bbc0" }, svg).textContent = fmtV(f.valor);
      const hit = el("rect", { x, y: m.t, width: bw, height: alto - m.t - m.b, fill: "transparent" }, svg);
      hit.addEventListener("mousemove", (ev) => mostrarTip(ev, `<div class="tt">${f.etiqueta}</div><b>${fmt(f.valor)}</b>${f.nota ? `<div class="muted">${f.nota}</div>` : ""}`));
      hit.addEventListener("mouseleave", ocultarTip);
    });
  });
}

// ---------- dispersión con recta de tendencia ----------
export function dispersion(nodo, { puntos, alto = 360, xNombre, yNombre, xFmt = fmtCorto, yFmt = fmtCorto, tendencia = true, alClic }) {
  redibujable(nodo, () => {
    const { svg, ancho } = contenedor(nodo, alto);
    const m = { t: 14, r: 18, b: 44, l: 76 };
    const xs = puntos.map((p) => p.x), ys = puntos.map((p) => p.y);
    const px = (Math.max(...xs) - Math.min(...xs)) * 0.08 || 1, py = (Math.max(...ys) - Math.min(...ys)) * 0.1 || 1;
    const X = escalaLineal(Math.min(...xs) - px, Math.max(...xs) + px, m.l, ancho - m.r);
    const Y = escalaLineal(Math.min(...ys) - py, Math.max(...ys) + py, alto - m.b, m.t);
    const g = el("g", { class: "eje" }, svg);
    for (const t of ticks(Math.min(...ys) - py, Math.max(...ys) + py)) {
      el("line", { x1: m.l, x2: ancho - m.r, y1: Y(t), y2: Y(t), class: "rejilla-l" }, g);
      el("text", { x: m.l - 8, y: Y(t) + 3, "text-anchor": "end" }, g).textContent = yFmt(t);
    }
    for (const t of ticks(Math.min(...xs) - px, Math.max(...xs) + px, 5)) {
      el("line", { y1: m.t, y2: alto - m.b, x1: X(t), x2: X(t), class: "rejilla-l" }, g);
      el("text", { x: X(t), y: alto - m.b + 16, "text-anchor": "middle" }, g).textContent = xFmt(t);
    }
    el("text", { x: (m.l + ancho - m.r) / 2, y: alto - 6, "text-anchor": "middle", "font-size": 11, fill: "#a8bbc0" }, svg).textContent = xNombre;
    el("text", { x: -(alto - m.b + m.t) / 2, y: 12, transform: "rotate(-90)", "text-anchor": "middle", "font-size": 11, fill: "#a8bbc0" }, svg).textContent = yNombre;
    if (tendencia && puntos.length > 2) {
      const n = xs.length, mx = xs.reduce((a, b) => a + b) / n, my = ys.reduce((a, b) => a + b) / n;
      const b = xs.reduce((s, x, i) => s + (x - mx) * (ys[i] - my), 0) / (xs.reduce((s, x) => s + (x - mx) ** 2, 0) || 1);
      const a = my - b * mx, xa = Math.min(...xs), xb = Math.max(...xs);
      el("line", { x1: X(xa), x2: X(xb), y1: Y(a + b * xa), y2: Y(a + b * xb), stroke: TINTA3, "stroke-width": 1.5, "stroke-dasharray": "5 4" }, svg);
    }
    const orden = [...puntos].sort((p, q) => (p.resaltar ? 1 : 0) - (q.resaltar ? 1 : 0));
    for (const p of orden) {
      const c = el("circle", { cx: X(p.x), cy: Y(p.y), r: p.resaltar ? 7 : 5.5, fill: p.resaltar ? CORAL : PALETA[0], stroke: "#0f1b20", "stroke-width": 2 }, svg);
      if (p.resaltar || p.etiquetar) {
        el("text", { x: X(p.x) + 9, y: Y(p.y) - 7, "font-size": 11, "font-weight": 600, fill: p.resaltar ? "#ffb090" : "#a8bbc0" }, svg).textContent = p.etiqueta;
      }
      const hit = el("circle", { cx: X(p.x), cy: Y(p.y), r: 12, fill: "transparent" }, svg);
      hit.addEventListener("mousemove", (ev) => mostrarTip(ev, `<div class="tt">${p.etiqueta}</div><div class="fila"><span>${xNombre}</span><b>${xFmt(p.x)}</b></div><div class="fila"><span>${yNombre}</span><b>${yFmt(p.y)}</b></div>`));
      hit.addEventListener("mouseleave", ocultarTip);
      if (alClic) { hit.style.cursor = "pointer"; hit.addEventListener("click", () => alClic(p)); }
      void c;
    }
  });
}

// ---------- estadística ----------
export function pearson(xs, ys) {
  const n = xs.length, mx = xs.reduce((a, b) => a + b) / n, my = ys.reduce((a, b) => a + b) / n;
  let sxy = 0, sxx = 0, syy = 0;
  for (let i = 0; i < n; i++) { sxy += (xs[i] - mx) * (ys[i] - my); sxx += (xs[i] - mx) ** 2; syy += (ys[i] - my) ** 2; }
  return sxy / Math.sqrt(sxx * syy || 1);
}
function rangos(v) {
  const idx = v.map((x, i) => [x, i]).sort((a, b) => a[0] - b[0]), r = new Array(v.length);
  for (let i = 0; i < idx.length;) {
    let j = i; while (j + 1 < idx.length && idx[j + 1][0] === idx[i][0]) j++;
    for (let k = i; k <= j; k++) r[idx[k][1]] = (i + j) / 2 + 1;
    i = j + 1;
  }
  return r;
}
export const spearman = (xs, ys) => pearson(rangos(xs), rangos(ys));
