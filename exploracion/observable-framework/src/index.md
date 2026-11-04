---
title: Envejecimiento por distrito
---

# Envejecimiento por distrito (Censo 2021)

Mismos datos que la página publicada: `public/data/demografia.json` (F20) y `public/data/geo.json` (F19).

```js
import * as Plot from "@observablehq/plot";
const distritos = await FileAttachment("data/distritos.json").json();
const geo = await FileAttachment("data/distritos.geojson").json();
const porCodigo = new Map(distritos.map((d) => [d.codigo, d]));
```

```js
Plot.plot({
  title: "Porcentaje de población de 65 años o más",
  projection: {type: "mercator", domain: geo},
  color: {type: "quantize", n: 5, scheme: "blues", legend: true, label: "% 65+"},
  marks: [
    Plot.geo(geo, {
      fill: (f) => porCodigo.get(f.properties.codigo).pct_65_mas,
      stroke: "white",
      title: (f) => `${porCodigo.get(f.properties.codigo).distrito}: ${porCodigo.get(f.properties.codigo).pct_65_mas} %`,
      tip: true
    })
  ]
})
```

```js
Plot.plot({
  marginLeft: 120,
  x: {label: "% 65+"},
  y: {label: null, sort: {y: "x", reverse: true}},
  marks: [Plot.barX(distritos, {x: "pct_65_mas", y: "distrito", fill: "#1f4e79", tip: true}), Plot.ruleX([0])]
})
```

Fuente: F20 (censo 2021), licencia en `catalogo/fuentes.json`. Cada cifra sale del archivo, no de una consulta en vivo.
