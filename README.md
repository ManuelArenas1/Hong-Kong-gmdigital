# Cerebro HK — data lake de Hong Kong

Data lake con datos **públicos** de Hong Kong organizado en las mismas pestañas que el tablero de referencia *Cerebro Lima*: `panorama`, `geo`, `demografia`, `economia`, `infraestructura`, `sensores`, `escucha`, `atlas_zonas`, `atlas_distribuidos` y `correlaciones`.

La unidad territorial principal son los **18 distritos** de Hong Kong (códigos A–T del censo), con detalle fino en las **452 circunscripciones DCCA 2019**.

## Estructura

```
raw/            Bronce: datos tal como se obtuvieron de cada fuente
curated/        Plata: tablas y capas limpias, en español, unidas por código de distrito
public/data/    Oro: un JSON por pestaña, listo para servir en el front (Vercel/Next/Vite)
catalogo/       catalogo.json — fuentes, URLs, licencias, validaciones y notas
pipeline/       build.py — reconstruye curated/ y public/data/ a partir de raw/
```

## Cómo reconstruir

```bash
pip install -r requirements.txt
python pipeline/build.py
```

El pipeline es determinista (k-means con semilla fija) y no descarga nada: todo parte de `raw/`.

## Qué hay en cada pestaña

| Pestaña | Archivo | Contenido principal |
|---|---|---|
| Panorama | `public/data/panorama.json` | KPIs de ciudad (población, densidad, % 65+, PIB per cápita, inflación, red de transporte, sensores), destacados y resumen por distrito |
| Geo | `geo.json`, `geo_circunscripciones.json` | 18 distritos, 3 regiones y 452 DCCA en GeoJSON (WGS84) |
| Demografía | `demografia.json` | Censo 2021 por distrito: edad, hogares, educación, origen, tipo de vivienda, densidad; población 2016–2025 |
| Economía | `economia.json` | Ingreso mediano del hogar 2016–2025, ingreso por empleo, participación laboral; PIB per cápita e IPC 2000–2025; desempleo y delitos recientes |
| Infraestructura | `infraestructura.json`, `infraestructura_paradas.json` | 15.285 paradas (bus, minibús, MTR, tren ligero, ferry), 97 estaciones MTR, 18 hospitales de urgencias, distancia a urgencias por DCCA |
| Sensores | `sensores.json` | 86 estaciones del Observatorio con coordenadas y tipo; AQHI de 18 estaciones de calidad del aire |
| Escucha | `escucha.json` | Titulares de prensa por tema con distritos detectados y tono heurístico; delitos mensuales 2022–2024 |
| Atlas de zonas | `atlas_zonas.json` | Ficha integrada por distrito, tipologías (k-means), índices de prosperidad, conectividad y presión demográfica, rankings; atlas por DCCA |
| Atlas distribuido | `atlas_distribuidos.json` | Malla hexagonal H3 res. 8 (~0,74 km²) con conteos de paradas, rutas, hospitales y estaciones; nivel de cobertura |
| Correlaciones | `correlaciones.json` | Matrices Pearson y Spearman entre 17 indicadores, pares más fuertes con p-valor, datos para dispersión |

## Fuentes

Detalle completo en [`catalogo/catalogo.json`](catalogo/catalogo.json). Resumen:

- **C&SD** — Censo 2021 y Encuesta General de Hogares 2016–2025 por distrito (servicios WFS del portal CSDI).
- **EAC** — límites de las circunscripciones DCCA 2019 (vía `hkdce/dcca-boundaries`).
- **Hong Kong Observatory** — lista oficial de estaciones y capa espacial CSDI.
- **EPD** — AQHI por estación.
- **Operadores de transporte** (KMB, Citybus, NLB, GMB, MTR, ferris) compilados por `hkbus/hk-bus-crawling` (GPL-2.0).
- **Hospital Authority** — hospitales con urgencias.
- **Banco Mundial vía FRED** — PIB per cápita e inflación.
- **Hong Kong Police Force** — delitos mensuales y anuales.
- **Wikipedia** — área terrestre oficial por distrito (CC BY-SA).

## Advertencias

- Los polígonos de la EAC incluyen mar; las densidades usan el **área terrestre oficial**.
- La población del censo por distrito suma 7.411.945 (excluye a la población marina).
- Las correlaciones usan 18 observaciones: son descriptivas, no causales.
- El tono de `escucha` es un léxico heurístico, no un modelo de sentimiento validado.
- AQHI y titulares son capturas puntuales del 2026-10-06; para series en vivo conviene agendar la ingesta (ver `catalogo.json`, campo `data_url` de las estaciones HKO).
