# Cerebro HK — data lake de Hong Kong

Data lake con datos **públicos** de Hong Kong organizado en las mismas pestañas que el tablero de referencia *Cerebro Lima*: `panorama`, `geo`, `demografia`, `economia`, `infraestructura`, `sensores`, `escucha`, `atlas_zonas`, `atlas_distribuidos` y `correlaciones`.

La unidad territorial principal son los **18 distritos** de Hong Kong (códigos A–T del censo), con detalle fino en las **452 circunscripciones DCCA 2019**.

## Página web (Cerebro HK)

`public/index.html` es el tablero territorial, con el mismo sistema visual de *Cerebro Lima*: menú lateral, panorama con diagnóstico comparativo, mapa MapLibre (coropletas, circunscripciones, malla H3, MTR, hospitales, estaciones), y secciones de gente, economía y vivienda, turismo, finanzas públicas, seguridad, transporte y salud, ambiente, correlaciones, atlas de los 18 distritos, escucha social y fuentes. Lee solo `public/data/*.json`; no tiene backend.

```bash
cd public && python -m http.server 8000   # abrir http://localhost:8000
```

Para publicarla en Vercel basta con importar el repositorio: `vercel.json` sirve la carpeta `public/` sin paso de compilación.

Sellos de cada cifra: **observado** (descargado y procesado por el pipeline), **declarado** (cifra oficial leída de un informe y registrada en la wiki, fuentes F01–F18), **derivado** (calculado en el lago).

## Estructura

```
raw/            Bronce: datos tal como se obtuvieron de cada fuente
curated/        Plata: tablas y capas limpias, en español, unidas por código de distrito
public/data/    Oro: un JSON por pestaña, listo para servir en el front (Vercel/Next/Vite)
catalogo/       fuentes.json — catálogo único F01–F45 con licencias literales (en inglés)
                diccionario_web.csv — un campo por fila de cada archivo de public/data que lee la web, con su F0x
                Diccionario_de_datos_TallerDatos_HongKong.xlsx — entrega del grupo, generada desde los dos anteriores
pipeline/       build.py — reconstruye curated/ y public/data/ a partir de raw/
                exportar_perfil_wiki.py — perfil de ciudad de la wiki, hexágonos y barrios para la web
                catalogo_unico.py — catálogo F01–F45, licencias literales y conciliación wiki vs. lago
                diccionario_web.py — diccionario generado leyendo los JSON reales de public/data
                excel_grupo.py — llena la plantilla del taller desde el catálogo y el diccionario
public/         página web (index.html + assets/) que consume public/data/
```

## Cómo reconstruir

```bash
pip install -r requirements.txt
python pipeline/build.py
python pipeline/exportar_perfil_wiki.py
python pipeline/catalogo_unico.py
python pipeline/diccionario_web.py
python pipeline/excel_grupo.py <excel_del_grupo.xlsx> catalogo/Diccionario_de_datos_TallerDatos_HongKong.xlsx
```

Regla de la página: **cada gráfico lee un archivo de `public/data/`, ese archivo tiene sus filas en el diccionario con su F0x, y nada se consulta en vivo.** Debajo de cada gráfico la página muestra la fuente, el archivo y el campo.

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

El catálogo único está en [`catalogo/fuentes.json`](catalogo/fuentes.json) (también en la sección «Fuentes» de la página): 45 fuentes, de las cuales 29 están integradas. Las licencias se copian **literalmente, en inglés**; cuando la página de avisos no se pudo abrir quedan como `not verified` en vez de suponerlas. Licencias con riesgo: F10 y F17 (restrictivas), F34 (Moody's, descartada), F25 y F27 (solo uso no comercial).

## Advertencias

- Los polígonos de la EAC incluyen mar; las densidades usan el **área terrestre oficial**.
- La población del censo por distrito suma 7.411.945 (excluye a la población marina).
- Las correlaciones usan 18 observaciones: son descriptivas, no causales.
- El tono de `escucha` es un léxico heurístico, no un modelo de sentimiento validado.
- AQHI y titulares son capturas puntuales del 2026-10-06; la página no consulta nada en vivo.
- La pobreza por distrito no se grafica: la decisión de cómo protegerla está escrita en la sección Gente de la página.
