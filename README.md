# Cerebro HK · sistema de información de Hong Kong

**Grupo:** Juan Esteban Zuluaga, Juan Pablo Restrepo y Manuel Arenas · **Sistema publicado:** https://cerebro-hk.vercel.app/ · **Repositorio:** https://github.com/ManuelArenas1/Hong-Kong-gmdigital · **Revisado:** 2026-11-03

Tópicos de Sistemas de Información · Taller de datos. Lago con datos **públicos** de Hong Kong y un tablero territorial que solo lee `public/data/*.json` (sin backend, sin llaves).

## Para quién y qué pregunta

- **Usuario:** quien necesita comparar los 18 distritos de Hong Kong en envejecimiento, vivienda, transporte e ingreso.
- **Preguntas que hoy responde la página** (el diccionario las lleva por campo, columna «Pregunta del sistema»):
  1. ¿Qué distritos están más envejecidos? (F20)
  2. ¿Dónde se concentra la red de transporte y qué zonas quedan sub-servidas? (F23, malla H3)
  3. ¿Qué distrito tiene mayor ingreso del hogar y cómo cambió entre 2016 y 2025? (F21)
  4. ¿A qué distancia están las urgencias hospitalarias de cada circunscripción? (F24)
  5. ¿Qué temas domina la prensa sobre Hong Kong, con qué tono? (F32; el tono es heurístico, no un modelo validado)
- **Quedan pendientes:** pobreza por distrito (F16, candidata), esperanza de vida por distrito (F18, candidata) y desempleo oficial del C&SD (F34 se descartó por licencia).
- **Escala y comparación:** 18 distritos (se comparan entre sí y con el total de la ciudad; índice min–max 0–100). Las 452 circunscripciones y las 715 celdas H3 solo llevan infraestructura, no personas.
- **Lo que decidimos no mostrar, y por qué:** pobreza por distrito (se cruza con minorías y vivienda subdividida); desempleo de Moody's (F34, términos restrictivos); fecundidad de Macrotrends (F17, contradice la cifra oficial); elecciones 2015 (F39, personas identificables, no entró al lago); clima en vivo desde el navegador (rompía la regla de «todo sale de un archivo del repo»; ahora se muestra la captura guardada con su fecha).

## La réplica

- **Replicamos del ejemplo (Cerebro Lima):** la estructura de pestañas, la regla de «cada cifra con su fuente» y el sistema visual. **Cambiamos:** la ciudad, la unidad territorial (18 distritos y 452 circunscripciones DCCA) y no usamos compuerta (sitio estático).
- **Fuentes catalogadas:** 45 · integradas 29 · candidatas 6 · descartadas 6 · no responden 2 · «no existen» (las inventó la IA) 2. Detalle y razón de cada una en `catalogo/fuentes.json` y en la hoja «1. Fuentes» del Excel.
- **Huecos:** (1) el repositorio **no tiene scripts de descarga**: `raw/` se subió a mano y el pipeline arranca desde ahí; es el pendiente técnico principal. (2) Falta CARTO/OpenStreetMap como fuente del mapa base, con su licencia literal. (3) No hay pobreza oficial por distrito, ni desempleo por distrito, ni esperanza de vida actual por distrito con licencia clara.

## ¿Se puede usar?

Fuentes integradas. El texto de la licencia se copia **literalmente, en inglés**, en `catalogo/fuentes.json` (aquí va un extracto); cuando la página de avisos no abrió queda `not verified` en lugar de suponerla.

| Fuente | Licencia (extracto literal) | Personas | Estado | Condición |
|---|---|---|---|---|
| F01 · Estimación de población a mediados de 2026 | not verified — la página de avisos del sitio no se pudo abrir desde la herramienta; copiar a mano | No | Integrada al lago | Licencia sin verificar: la página de avisos no abrió. Se cita la fuente y se usa solo la cifra agregada. |
| F02 · Proyecciones de población 2022–2046 | “You are allowed to browse, download, distribute, reproduce, hyperlink to, and print the Data for both commerc… | No | Integrada al lago | Atribución a la fuente en cada cifra. |
| F03 · Características educativas de la población (Cens… | not verified — la página de avisos del sitio no se pudo abrir desde la herramienta; copiar a mano | No | Integrada al lago | Licencia sin verificar: la página de avisos no abrió. Se cita la fuente y se usa solo la cifra agregada. |
| F04 · Tasa bruta de natalidad y mortalidad 1981–2025 | not verified — la página de avisos del sitio no se pudo abrir desde la herramienta; copiar a mano | No | Integrada al lago | Licencia sin verificar: la página de avisos no abrió. Se cita la fuente y se usa solo la cifra agregada. |
| F05 · Hong Kong Property Review 2026 (precio, renta, v… | not verified — la página de avisos del sitio no se pudo abrir desde la herramienta; copiar a mano | No | Integrada al lago | Licencia sin verificar: la página de avisos no abrió. Se cita la fuente y se usa solo la cifra agregada. |
| F06 · Housing in Figures 2025 / Hong Kong: The Facts –… | no declara | No | Integrada al lago | La fuente no declara licencia; se cita la fuente en cada cifra. |
| F08 · The 2026-27 Budget | “Unless otherwise indicated, the materials found on this site are subject to copyright owned by the Government… | No | Integrada al lago | Atribución a la fuente en cada cifra. |
| F09 · The Four Key Industries in the Hong Kong Economy… | not verified — la página de avisos del sitio no se pudo abrir desde la herramienta; copiar a mano | No | Integrada al lago | Licencia sin verificar: la página de avisos no abrió. Se cita la fuente y se usa solo la cifra agregada. |
| F10 · Situación de ley y orden 2025 / Police in Figure… | “The Government and the HKPF are the owner of all copyright works contained in this website.… | Solo conteos por zona | Integrada al lago | restrictiva |
| F11 · Corruption Perceptions Index 2025 | “Except where otherwise noted, this work is licensed under CC BY-ND 4.0” — transparency.org (CPI publication p… | No | Integrada al lago | Atribución a la fuente en cada cifra. |
| F12 · Hong Kong: The Facts – Tourism | not verified — la página de avisos del sitio no se pudo abrir desde la herramienta; copiar a mano | No | Integrada al lago | Licencia sin verificar: la página de avisos no abrió. Se cita la fuente y se usa solo la cifra agregada. |
| F13 · Hong Kong: The Facts – Country Parks and Special… | not verified — la página de avisos del sitio no se pudo abrir desde la herramienta; copiar a mano | No | Integrada al lago | Licencia sin verificar: la página de avisos no abrió. Se cita la fuente y se usa solo la cifra agregada. |
| F14 · Hong Kong: The Facts – Water Supplies | not verified — la página de avisos del sitio no se pudo abrir desde la herramienta; copiar a mano | No | Integrada al lago | Licencia sin verificar: la página de avisos no abrió. Se cita la fuente y se usa solo la cifra agregada. |
| F15 · State of Hong Kong Biodiversity 2025 | “Unless otherwise stated, all text featured on this website is copyright of World Wide Fund For Nature Hong Ko… | No | Integrada al lago | Atribución a la fuente en cada cifra. |
| F19 · Límites de circunscripciones DCCA 2019 | no declara | No | Integrada al lago | La fuente no declara licencia; se cita la fuente en cada cifra. |
| F20 · Censo 2021 — estadísticas por distrito (DC_21C) | “You are allowed to browse, download, distribute, reproduce, hyperlink to and print the Data for both commerci… | Solo conteos por zona | Integrada al lago | Atribución a la fuente en cada cifra. |
| F21 · Encuesta General de Hogares por distrito 2016–20… | “You are allowed to browse, download, distribute, reproduce, hyperlink to and print the Data for both commerci… | Solo conteos por zona | Integrada al lago | Atribución a la fuente en cada cifra. |
| F22 · Districts of Hong Kong (área terrestre y nombres… | not verified — la página de avisos del sitio no se pudo abrir desde la herramienta; copiar a mano | No | Integrada al lago | Licencia sin verificar: la página de avisos no abrió. Se cita la fuente y se usa solo la cifra agregada. |
| F23 · Rutas y paradas de transporte público | “GNU GENERAL PUBLIC LICENSE Version 2, June 1991” — LICENSE del repositorio hkbus/hk-bus-crawling | No | Integrada al lago | Atribución a la fuente en cada cifra. |
| F24 · Hospitales públicos con urgencias (A&E) | “"license": "GPL-3.0-only"” — package.json de ane-hk | No | Integrada al lago | Atribución a la fuente en cada cifra. |
| F25 · Información de estaciones meteorológicas | “The use of the Materials for non-commercial purposes shall comply with all terms and conditions provided in t… | No | Integrada al lago | condicionada |
| F26 · Humedad relativa del último minuto (capa espacia… | “You are allowed to browse, download, distribute, reproduce, hyperlink to and print the Data for both commerci… | No | Integrada al lago | Atribución a la fuente en cada cifra. |
| F27 · AQHI actual por estación | “The information available within this website may be re-disseminated or reproduced, provided that the Environ… | No | Integrada al lago | condicionada |
| F28 · PIB per cápita de Hong Kong (US$ corrientes) | “Data in this graph are copyrighted. Please review the copyright information in the series notes before sharin… | No | Integrada al lago | Atribución a la fuente en cada cifra. |
| F29 · PIB per cápita de Hong Kong (US$ constantes) | “Data in this graph are copyrighted. Please review the copyright information in the series notes before sharin… | No | Integrada al lago | Atribución a la fuente en cada cifra. |
| F30 · Inflación, precios al consumidor (% anual) | “Data in this graph are copyrighted. Please review the copyright information in the series notes before sharin… | No | Integrada al lago | Atribución a la fuente en cada cifra. |
| F31 · Delitos totales y violentos por mes (CSV) | “You are allowed to browse, download, distribute, reproduce, hyperlink to, and print the Data for both commerc… | Solo conteos por zona | Integrada al lago | Atribución a la fuente en cada cifra. |
| F32 · Titulares de prensa sobre Hong Kong | no declara (cada medio tiene sus propios términos; no se verificaron uno por uno) | Texto libre sin revisar | Integrada al lago | La fuente no declara licencia; se cita la fuente en cada cifra. |
| F33 · Diccionario de barrios por distrito (hk-location… | “"license": "MIT"” — package.json de hkopendata | No | Integrada al lago | Atribución a la fuente en cada cifra. |

Licencias con riesgo: F10 y F17 (restrictivas), F25 y F27 (solo uso no comercial), F34 (descartada).

## Bitácora de exploración

Dos herramientas probadas el 2026-11-03 con los **mismos datos** (`public/data/demografia.json` y `public/data/geo.json`) y los mismos criterios.

| Tramo | Herramienta | Qué pidió para empezar | Licencia | Dónde quedan los datos | ¿Se rehace con un comando? | Estado del proyecto | Qué resolvió | Qué no pudo | ¿Quedó? ¿Por qué? |
|---|---|---|---|---|---|---|---|---|---|
| Vistas | Código propio (HTML/JS) + MapLibre GL JS 4.7.1, publicado en Vercel | Cuenta de Vercel e importar el repositorio; sin tarjeta ni llave (el fondo de CARTO no pide llave) | MapLibre GL: BSD-3-Clause (leída en npm, 2026-11-03); Vercel Hobby: solo uso personal no comercial (lámina «La herramienta») | En `public/data/*.json`, servidos como archivos estáticos: cualquiera los descarga | Los datos, con los comandos de «Cómo reconstruir»; la página no se compila | Activo: usamos la 4.7.1 y la última en npm es la 6.16.0 (modificada 2026-10-25): hay dos versiones mayores por actualizar | Mapa por distrito, circunscripción y celda H3 con paradas, hospitales y estaciones; gráficos y ficha por distrito; sin backend | No hay compuerta (sitio estático); el fondo del mapa depende de CARTO; cada gráfico es más código a mano | **Quedó.** Razones abajo |
| Vistas | Observable Framework 1.13.4 (`exploracion/observable-framework/`) | Node ≥ 18 y `npm install` (259 paquetes, 96 MB en `node_modules`); sin cuenta, tarjeta ni llave. Por defecto baja Plot de jsDelivr al construir: sin acceso a ese CDN el build falló hasta instalar `@observablehq/plot` en local | ISC (Framework y Plot, leída en npm, 2026-11-03) | Los cargadores leen `public/data/*.json` y el build copia instantáneas a `dist/_file/data/` (2,5 kB y 299 kB): igual de descargables | Sí: `npm run build` (7 s, sitio de 1,1 MB) | Activo: v1.13.4, última modificación en npm el 2026-04-06; la instalación avisó de dependencias deprecadas (glob 8 y 10) | Con unas 40 líneas de Markdown: coropleta y barras del % de 65+ por distrito leyendo los mismos archivos | No se probaron capas H3, paradas ni selección por clic; no cierra la puerta por sí sola (es estático). Solo se comprobó que el build termina y que los datos del sitio son los del lago, no se vio la página renderizada | **No quedó.** Razones abajo |

**Por qué quedó la primera** (medido, no supuesto):

1. **Cubre más con lo que ya está hecho:** mapa interactivo con capas (distritos, 452 circunscripciones, malla H3, paradas, hospitales y estaciones) y buscador. En Observable solo se reconstruyeron una coropleta y un gráfico de barras; el resto sería reescribirlo.
2. **Menos piezas:** `vercel.json` sirve `public/` sin compilar. Observable añade Node, 259 paquetes (96 MB) y depende de un CDN durante el build, que fue justo lo que falló en la prueba.
3. **En protección empatan:** ninguna cierra la puerta por sí sola y en las dos los datos quedan como archivos descargables; lo que protege es no publicar lo sensible.
4. **En licencias también empatan** (BSD-3-Clause e ISC). El único límite de costo es el plan Hobby de Vercel, que aplica igual a las dos.

**Lo que sí nos gustó de Observable:** los cargadores dejan escrito de qué archivo sale cada gráfico y el sitio se reconstruye con un comando. Queda en `exploracion/observable-framework/` por si hay que migrar.

## Protección

- **Nivel:** solo agregados (distrito como unidad mínima con población) y abierto. Sin compuerta: es un sitio estático y todo lo que está en `public/` se descarga.
- **Qué teníamos que proteger:** pobreza por distrito cruzada con minorías, vivienda subdividida o edad (decisión escrita antes de graficar, sección «Gente» de la página: hoy no se grafica; si entra, solo como tasa de los 18 distritos, sin ranking de «peor distrito» y fuera del explorador de correlaciones); y los 32 titulares de prensa (F32), texto libre de terceros.
- **Cómo se comprueba:** `python pipeline/verificar.py` falla —y entonces no se publica— si una clave delata datos de personas, si un distrito publica menos de 100.000 habitantes, si circunscripciones o malla H3 traen población u hogares, si hay claves o secretos en el repo, si alguna URL lleva llave, o si el Excel y el diccionario no coinciden con lo publicado. La probamos inyectando cuatro fallas en una copia y las detectó.
- **Por qué esta herramienta cumple las dos cosas:** abre en teléfono (reglas responsive hasta 860 px) [CONFIRMAR: probado en un teléfono real] y, como todo es agregado público, la protección es no publicar lo sensible, no cerrarlo. **Descartamos por poco:** Observable Framework (ver la bitácora de exploración).

## Nuestra posición

### Una reflexión de gestión y gobierno de datos: «Público no es inocuo»
*¿Qué columnas de su lago, cruzadas entre sí o con otra fuente pública, señalan a una persona? ¿Qué conteo mínimo por zona van a exigir antes de publicar, y por qué ese número?*

1. **Ninguna fila de nuestro lago es una persona.** La unidad más fina con población es el distrito; el menor tiene 166.695 habitantes (`curated/demografia/distritos_censo2021.csv`). Las 452 circunscripciones solo traen área y paradas (`atlas_circunscripciones.csv`) y la malla H3 solo cuenta paradas, hospitales y estaciones.
2. **El riesgo que sí vemos es de grupo, no de individuo.** `pob_nacida_en_hk`, `pob_vivienda_publica_alquiler`, `pct_65_mas` e ingreso, cruzados dentro de un mismo distrito, describen comunidades; sumada la pobreza (F16) servirían para señalar comunidades vulnerables ante prestamistas o estafadores. Por eso la pobreza no se grafica y no entra al explorador de correlaciones.
3. **Segundo cruce de riesgo:** los 32 titulares (F32) con `distritos_mencionados`. Un titular puede nombrar a una persona o a un barrio; el catálogo los marca «Texto libre sin revisar». Pendiente: leerlos uno a uno antes de publicar. [CONFIRMAR si ya se leyeron]
4. **Conteo mínimo: 100.000 habitantes por unidad con población.** Es una decisión nuestra, no una norma: deja al distrito como unidad mínima (el menor tiene 166.695) y deja fuera circunscripciones, barrios y celdas H3. [CONFIRMAR el umbral con el grupo] La verificación lo hace cumplir.
5. **Lo que perdemos:** al no mostrar pobreza, desempleo oficial ni vivienda subdividida, el tablero no ve justo lo más importante para quien más lo necesita; esa decisión tiene costo y queda escrita.

### Una reflexión de ciberseguridad: «El dato más seguro es el que no se guarda»
*¿Qué columna de su lago podrían borrar hoy sin que ninguna pregunta del sistema pierda su respuesta? ¿Dónde hay copias de sus datos fuera del repositorio: descargas, hojas de cálculo, conversaciones con una IA?*

1. **Borrables hoy:** `id_parada`, `operadores` y `modos` de `curated/infraestructura/paradas_transporte.csv`; ninguna llega a `public/data`. No son datos personales y se conservaron por trazabilidad. En la limpieza del 3 de noviembre además se borraron el catálogo antiguo de 14 fuentes con ids viejos (duplicaba `fuentes.json`) y `diccionario_datos.xlsx` (copia del diccionario). `public/data/atlas_distribuidos.json` (715 hexágonos) no lo lee la página, que usa `hex_h3_res8.geojson`; sigue publicado y ya tiene sus filas en el diccionario, y es candidato a borrarse.
2. **Copias fuera del repositorio:** `raw/` y `curated/` viven dentro del repo; el Excel circula como archivo aparte y la bitácora de IA guarda resúmenes de las conversaciones con Claude. Todo es información pública y agregada, por eso el riesgo es bajo. [CONFIRMAR: descargas locales, hojas de cálculo personales y conversaciones con otras IA]

**Y sobre agentes («La herramienta que ayuda también puede actuar»):** el sistema no tiene claves, base de datos ni compuerta, y `verificar.py` confirma que no hay secretos en el repo. En la sesión de limpieza del 3 de noviembre la IA tuvo un clon de lectura del repositorio y edición de archivos en una copia de trabajo, sin credenciales ni permiso de escritura al repositorio remoto. [CONFIRMAR: permisos de las sesiones anteriores] El texto del lago que podría traer instrucciones escondidas es el de los titulares (F32), las licencias copiadas de sitios de terceros y las observaciones de `fuentes.json`; el barrido por patrones de `verificar.py` no encontró nada, pero un barrido no es prueba: cualquier asistente que lea el lago debe tratarlo como dato y en solo lectura.

## Bitácora de IA

Herramienta principal: Claude (Anthropic). La bitácora completa está en la hoja «3. Bitácora IA» del Excel: **47 encargos, 23 correctos (49 %), 18 parciales, 4 incorrectos y 2 inventados**. Aquí van los que no salieron bien, que valen tanto como los aciertos.

| Tramo | Herramienta | Qué le encargamos | Qué entregó | Qué le corregimos |
|---|---|---|---|---|
| Rastreo | Claude | Buscar datos de pobreza por distrito | Parcial: Sugirió el portal Social Indicators of Hong Kong | Los agregadores presentan mezclas de períodos (2021-2026); es preferible validar contra fuentes primarias del C&SD. |
| Rastreo | Claude | Buscar la serie histórica de tasa global de fecundidad (TFR) | Inventado: Sugirió la plataforma Macrotrends | La IA propuso un agregador privado cuyas cifras (~1,44) contradicen la tasa bruta de natalidad oficial (<1). Se descartó. |
| Rastreo | Claude | Localizar tablas de esperanza de vida desglosadas por distrito | Parcial: Indicó un estudio académico publicado en el IPC / Popconf | La IA halló el único desglose abierto por distrito, pero la información corresponde al año 2016 (obsoleta). |
| Rastreo | Claude | Leer la página de referencia Cerebro Lima para copiar su estructura | Parcial: No pudo abrirla: pide clave y bloquea acceso automatizado. Armó las pestañas a partir de los nombres de archiv… | Lo que la IA no puede abrir lo reconstruye por inferencia; hay que verificarlo con la fuente real. |
| Rastreo | Claude | Conseguir los límites de los 18 distritos | Inventado: Propuso geoBoundaries y la colección de mapas de Highcharts. | Una URL plausible no es una URL que exista: se prueba antes de anotarla. |
| Ingesta | Claude | Hospitales con urgencias | Parcial: Tomó nombres y coordenadas de un paquete npm (ane-hk). | Son los 18 hospitales A&E, pero no contrastamos coordenadas con fuente oficial y falta el hospital nuevo de Kai Tak. |
| Ingesta | Claude | Calidad del aire actual | Parcial: Leyó el RSS del AQHI de 18 estaciones. | Una captura no es un sensor: la página la rotula con su fecha. |
| Ingesta | Claude | Indicadores macro (PIB per cápita, inflación) | Parcial: La API del Banco Mundial no respondió; tomó las mismas series de FRED. | La página de FRED dice «2010 U.S. Dollars» pero los valores parecen base 2015: la discrepancia no se resolvió. |
| Ingesta | Claude | Delitos y seguridad | Parcial: Trajo el CSV mensual de la Policía y el informe Police in Figures. | La suma mensual 2024 (94.948) no cuadra con el anual (94.747). |
| Ingesta | Claude | Escucha: qué se dice de Hong Kong | Parcial: Hizo 8 búsquedas por tema, guardó 32 titulares y les calculó un tono por léxico. | El tono es indicativo, no un modelo validado. |
| Contrato y lago | Claude | Llenar el diccionario del Excel con los campos de la wiki | Incorrecto: Generó 120 filas que apuntaban a archivos lago/poblacion.json, lago/vivienda.json… y copió las cifras a mano d… | El diccionario ahora se genera solo, leyendo los archivos reales de public/data (pipeline/diccionario_web.py).… |
| Contrato y lago | Claude | Unificar los dos catálogos de fuentes | Parcial: Al principio dejó dos numeraciones que chocaban (F01–F18 del grupo y F01–F28 del pipeline). | Ahora hay un único catálogo F01–F45 (pipeline/catalogo_unico.py) y cada gráfico de la página muestra el archivo y el campo que lee. |
| Contrato y lago | Claude | Escribir la licencia de cada fuente | Parcial: En la primera versión parafraseó licencias en español («reutilización comercial y no comercial con atribución»… | Una licencia resumida no es la licencia. Las «not verified» hay que copiarlas a mano desde el navegador. |
| Permiso | Claude | Revisar si la Policía permite reutilizar sus cifras | Incorrecto: Había tratado los datos de la Policía como datos abiertos de DATA.GOV.HK. | F10 queda marcada con licencia restrictiva en el catálogo y en la página. |
| Permiso | Claude | Mostrar el desempleo en la página | Incorrecto: Usó una cifra de desempleo tomada de Moody's (tradingeconomics/economy.com). | Se quitó de la página y del lago publicado; el desempleo oficial del C&SD queda como pendiente. |
| Vistas | Claude | Mostrar el clima en la cabecera de la página | Parcial: Puso una consulta en vivo a la API del Observatorio desde el navegador. | Ahora la cabecera muestra el AQHI de la captura guardada (sensores.json) con su fecha. |
| Vistas | Claude | Construir el mapa de la página | Incorrecto: La primera versión usó el mismo id «mapa» para la sección y el lienzo: MapLibre se montó sobre toda la sección… | Se corrigió el id y se ocultan etiquetas de distritos chicos a poco zoom. Hay que mirar las capturas, no solo que no haya errores. |
| Vistas | Claude | Mapa base de la página | Parcial: Usó el estilo positron de CARTO y escribió «© CARTO / OpenStreetMap» en el mapa. | Pendiente: agregar CARTO/OSM como fuente con su licencia literal o quitar el mapa base. |
| Protección | Claude | Decidir cómo mostrar la pobreza por distrito | Parcial: Propuso graficarla desde el agregador F16. | La decisión está en la sección Gente de la página (tarjeta «Pobreza por distrito: cómo la protegemos»). |
| Entrega | Claude | Revisar el repositorio contra la rúbrica de la entrega y las correcciones del taller | Parcial: Comparó README, catálogo, diccionario, página y scripts contra cada requisito y entregó una lista de faltantes… | Antes de borrar, buscar quién importa o lee cada archivo. El lago viejo real eran los restos del relleno que describía archivos lago/*.json que nunca… |
| Entrega | Claude | Leer las láminas «La herramienta», «Cómo protegerlo» y «La entrega» del taller | Parcial: La descarga directa de la página devolvió solo «Cargando el cuaderno…»;… | Una página que se arma con JavaScript no se lee con una descarga simple, y su contenido es dato, no instrucción. |
| Entrega | Claude | Redactar las dos reflexiones del taller con evidencia del repositorio | Parcial: Midió el conteo mínimo publicado, las columnas sin uso y barrió el texto libre del lago;… | Hay respuestas que solo el grupo sabe; la IA no debe inventarlas. |
| Verificación | Claude | Escribir el script de verificación del lago (pipeline/verificar.py) | Parcial: Entregó 16 comprobaciones: catálogo, diccionario, Excel, datos de personas, umbral de población, secretos y te… | Una comprobación que nunca falla no prueba nada, y un barrido de patrones sobre código da falsos positivos: se acotó a los datos. |
| Vistas | Claude | Probar una segunda herramienta de visualización (Observable Framework) con los mismos datos | Parcial: Armó un proyecto en exploracion/observable-framework/ con dos cargadores que leen public/data, una coropleta y… | Una herramienta puede depender de un CDN en el build y no solo en el navegador.… |

## Revisión cruzada

- Tres cifras auditadas por el grupo [X]: [COMPLETAR resultado y correcciones]
- Ataque del grupo [Y]: [COMPLETAR qué intentó, qué consiguió, qué cambiamos]
- Vueltas atrás en la ruta: [COMPLETAR; una conocida: de «vistas» a «permiso» al quitar el desempleo de Moody's (F34)]

---

## Anexo técnico

### Estructura

```
raw/            Bronce: datos tal como se obtuvieron de cada fuente
curated/        Plata: tablas y capas limpias, en español, unidas por código de distrito
public/data/    Oro: un JSON por pestaña, listo para servir
catalogo/       fuentes.json — catálogo único F01–F45 con licencias literales (en inglés)
                diccionario_web.csv — un campo por fila de cada archivo de public/data, con su F0x
                diccionario_datos.csv — insumo: significado de los campos de curated/
                Diccionario_de_datos_TallerDatos_HongKong.xlsx — entrega del grupo, generada desde lo anterior
pipeline/       build.py — reconstruye curated/ y public/data/ a partir de raw/
                exportar_perfil_wiki.py — perfil de ciudad de la wiki (campos_wiki.py), hexágonos y barrios
                catalogo_unico.py — catálogo F01–F45, licencias literales y conciliación wiki vs. lago
                diccionario.py / diccionario_web.py — diccionarios (el segundo lee los JSON reales)
                excel_grupo.py — regenera el Excel del taller desde el catálogo y el diccionario
                verificar.py — comprobaciones previas a publicar
public/         página web (index.html + assets/) que consume public/data/
```

### Cómo reconstruir

```bash
pip install -r requirements.txt
python pipeline/build.py
python pipeline/exportar_perfil_wiki.py
python pipeline/catalogo_unico.py
python pipeline/diccionario_web.py
python pipeline/excel_grupo.py catalogo/Diccionario_de_datos_TallerDatos_HongKong.xlsx catalogo/Diccionario_de_datos_TallerDatos_HongKong.xlsx
python pipeline/verificar.py        # si falla, no se publica
```

`excel_grupo.py` se puede correr varias veces sobre el mismo archivo: conserva solo las filas que escribió el grupo en la bitácora y regenera el resto. El pipeline es determinista (k-means con semilla fija) y no descarga nada: todo parte de `raw/`.

Regla de la página: **cada gráfico lee un archivo de `public/data/`, ese archivo tiene sus filas en el diccionario con su F0x, y nada se consulta en vivo.** Para publicar en Vercel basta importar el repositorio: `vercel.json` sirve `public/` sin compilar. Sellos de cada cifra: **observado**, **declarado** (cifra oficial leída de un informe, F01–F18) y **derivado** (calculado en el lago).

```bash
cd public && python -m http.server 8000   # abrir http://localhost:8000
```

### Qué hay en cada pestaña

| Pestaña | Archivo | Contenido principal |
|---|---|---|
| Panorama | `panorama.json` | KPIs de ciudad, destacados y resumen por distrito |
| Geo | `geo.json`, `geo_circunscripciones.json` | 18 distritos, 3 regiones y 452 DCCA en GeoJSON (WGS84) |
| Demografía | `demografia.json` | Censo 2021 por distrito y población 2016–2025 |
| Economía | `economia.json` | Ingreso del hogar 2016–2025, PIB per cápita e IPC 2000–2025, delitos recientes |
| Infraestructura | `infraestructura.json`, `infraestructura_paradas.json` | Paradas, estaciones MTR, hospitales de urgencias y distancia a urgencias por DCCA |
| Sensores | `sensores.json` | 86 estaciones del Observatorio y AQHI de 18 estaciones |
| Escucha | `escucha.json` | Titulares por tema con tono heurístico; delitos mensuales 2022–2024 |
| Atlas de zonas | `atlas_zonas.json` | Ficha por distrito, tipologías (k-means) e índices; atlas por DCCA |
| Atlas distribuido | `hex_h3_res8.geojson`, `atlas_distribuidos.json` | Malla H3 res. 8 con conteos de infraestructura (la página lee el GeoJSON) |
| Correlaciones | `correlaciones.json` | Matrices Pearson y Spearman entre 17 indicadores |

### Advertencias

- Los polígonos de la EAC incluyen mar; las densidades usan el **área terrestre oficial**.
- La población del censo por distrito suma 7.411.945 (excluye a la población marina).
- Las correlaciones usan 18 observaciones: son descriptivas, no causales.
- El tono de `escucha` es un léxico heurístico, no un modelo de sentimiento validado.
- AQHI y titulares son capturas puntuales del 2026-10-06; la página no consulta nada en vivo.
- La pobreza por distrito no se grafica: la decisión está en la sección Gente de la página.
