"""Catálogo ÚNICO de fuentes del lago (F01…F45) y conciliación wiki ↔ lago.

- F01–F18: fuentes que el equipo registró en la wiki y en el Excel (se conservan sus IDs).
- F19–F34: fuentes que descarga el pipeline (antes con IDs de texto como «census2021_dc»).
- F35–F45: fuentes probadas que no entraron (candidatas, descartadas, inexistentes).

Licencias: texto LITERAL en inglés copiado del sitio el 2026-10-26. Cuando la herramienta no pudo abrir
la página de avisos del sitio, `licencia_verificada` es False y el texto dice «not verified»: no se supone.

Salidas: catalogo/fuentes.json, public/data/fuentes.json, public/data/conciliacion.json
Uso: python pipeline/catalogo_unico.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import PUBLIC, escribir_json  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
HOY = "2026-10-26"

# ---- textos literales (copiados de cada sitio) ----
L_DATAGOV = ("“You are allowed to browse, download, distribute, reproduce, hyperlink to, and print the Data for both commercial and "
             "non-commercial purposes on a free-of-charge basis on condition that:- you shall identify clearly the source of the Data … "
             "you shall also give proper attribution to the Government, the Relevant Organisations and DATA.GOV.HK” — DATA.GOV.HK Terms and Conditions")
L_CSDI = ("“You are allowed to browse, download, distribute, reproduce, hyperlink to and print the Data for both commercial and "
          "non-commercial purposes on a free-of-charge basis on the condition that: you shall identify clearly the Government and the "
          "CSDI Portal as the source of the Data and acknowledge the Government and the relevant organisations’ ownership of the "
          "intellectual property rights in the Data …” — CSDI Portal Terms and Conditions")
L_HKPF = ("“The Government and the HKPF are the owner of all copyright works contained in this website. Any reproduction, adaptation, "
          "distribution, dissemination or making available of such copyright works to the public is strictly prohibited unless prior "
          "written authorization is obtained from HKPF.” — police.gov.hk Important Notices")
L_HKO = ("“The use of the Materials for non-commercial purposes shall comply with all terms and conditions provided in the … "
         "Besides, the use of the Materials for commercial purposes is strictly prohibited unless all the conditions provided in the … "
         "are complied with and prior written authorisation is obtained from the Hong Kong Observatory” — hko.gov.hk Readme / Copyright")
L_EPD = ("“The information available within this website may be re-disseminated or reproduced, provided that the Environmental "
         "Protection Department (EPD), as the source of information, is acknowledged and that the re-dissemination or reproduction is "
         "for non-commercial use.” — EPD Copyright Notice")
L_BUDGET = ("“Unless otherwise indicated, the materials found on this site are subject to copyright owned by the Government of the Hong "
            "Kong Special Administrative Region. Permission is required in adopting, reproducing or redistributing photographs, graphics, "
            "and audio and video materials on this website.” — budget.gov.hk Important Notices")
L_FRED = "“Data in this graph are copyrighted. Please review the copyright information in the series notes before sharing.” — FRED series page"
L_TI = "“Except where otherwise noted, this work is licensed under CC BY-ND 4.0” — transparency.org (CPI publication page)"
L_WWF = ("“Unless otherwise stated, all text featured on this website is copyright of World Wide Fund For Nature Hong Kong. Any reproduction, "
         "in full or in part, must credit World Wide Fund For Nature Hong Kong as the copyright holder” — wwf.org.hk Copyright")
L_MACRO = "“… copy, redistribute, transmit, sell, sublicense, publish, or otherwise exploit the Content except as expressly permitted; … Unauthorized use of the Content is strictly prohibited.” — macrotrends.net Terms of Service"
L_MOODYS = "“(i) obscure, alter, remove or delete any copyright or other proprietary notices or disclosures contained in the Materials,” — moodys.com Terms of Use (fragmento; uso restringido)"
L_GPL2 = "“GNU GENERAL PUBLIC LICENSE Version 2, June 1991” — LICENSE del repositorio hkbus/hk-bus-crawling"
L_NO_VERIF = "not verified — la página de avisos del sitio no se pudo abrir desde la herramienta; copiar a mano"

# Campos: id, nombre, entidad, tipo_publicador, url, formato, obtencion, licencia, verificada, url_licencia, personas,
#         cobertura, periodo, frecuencia, fecha_probada, estado, como, observaciones, riesgo_licencia
F = []
def f(*a):
    claves = ["id", "nombre", "entidad", "tipo_publicador", "url", "formato", "obtencion", "licencia", "licencia_verificada",
              "url_licencia", "personas", "cobertura", "periodo", "frecuencia", "fecha_probada", "estado", "como", "observaciones",
              "riesgo_licencia"]
    F.append(dict(zip(claves, a)))

# ---------------- F01–F18 (equipo, wiki) ----------------
f("F01", "Estimación de población a mediados de 2026", "Census and Statistics Department (C&SD)", "Entidad pública", "https://www.censtatd.gov.hk/en/scode150.html", "Página web", "Solo PDF o página", L_NO_VERIF, False, "https://www.censtatd.gov.hk/", "No", "Hong Kong (RAE)", "mediados de 2026", "Anual", "2026-09-21", "Integrada al lago", "IA (Claude) propuso C&SD; verificado en el portal", "Cifra provisional 7.518.300.", "")
f("F02", "Proyecciones de población 2022–2046", "Census and Statistics Department (C&SD)", "Entidad pública", "https://www.censtatd.gov.hk/en/EIndexbySubject.html?pcode=B1120015&scode=190", "XLSX", "Descarga directa", L_DATAGOV, True, "https://data.gov.hk/en/terms-and-conditions", "No", "Hong Kong (RAE)", "2022–2046 (base mid-2021)", "No se sabe", "2026-09-23", "Integrada al lago", "IA (Claude) + verificación en DATA.GOV.HK", "Base de la proyección excluye empleadas domésticas extranjeras: por eso su % de 65+ (20,5 %) difiere del censo (19,6 %).", "")
f("F03", "Características educativas de la población (Censo 2021)", "Census and Statistics Department (C&SD)", "Entidad pública", "https://www.census2021.gov.hk/doc/pub/21C_Articles_Educational.pdf", "PDF", "Descarga directa", L_NO_VERIF, False, "https://www.census2021.gov.hk/", "No", "Hong Kong (RAE)", "2011 vs 2021", "Única vez", "2026-09-23", "Integrada al lago", "IA (Claude) + verificación en el sitio del Censo", "«Educación superior» incluye no universitaria; el lago (F20) solo trae título universitario.", "")
f("F04", "Tasa bruta de natalidad y mortalidad 1981–2025", "Centre for Health Protection, Department of Health", "Entidad pública", "https://www.chp.gov.hk/en/statistics/data/10/27/112.html", "Página web", "Solo PDF o página", L_NO_VERIF, False, "https://www.chp.gov.hk/", "No", "Hong Kong (RAE)", "1981–2025", "Anual", "2026-09-23", "Integrada al lago", "IA (Claude) + verificación en CHP", "Sirvió para descartar la TFR de Macrotrends (F17).", "")
f("F05", "Hong Kong Property Review 2026 (precio, renta, vacancia)", "Rating and Valuation Department (RVD)", "Entidad pública", "https://www.rvd.gov.hk/en/publications/property_market_statistics.html", "PDF", "Descarga directa", L_NO_VERIF, False, "https://www.rvd.gov.hk/", "No", "Hong Kong (RAE)", "hasta 2025/2026", "Mensual", "2026-09-23", "Integrada al lago", "IA (Claude) + verificación en RVD", "", "")
f("F06", "Housing in Figures 2025 / Hong Kong: The Facts – Housing", "Housing Bureau / Hong Kong Housing Authority", "Entidad pública", "https://www.hb.gov.hk/eng/publications/housing/HIF2025.pdf", "PDF", "Descarga directa", "no declara", True, "https://hb.gov.hk/eng/notice/disclaimer.html", "No", "Hong Kong (RAE)", "2024/2025", "Anual", "2026-09-23", "Integrada al lago", "IA (Claude) + verificación en Housing Bureau", "La página de avisos de hb.gov.hk no trae aviso de copyright; solo: “The information contained in this website is compiled by the Housing Bureau of the Government”.", "")
f("F07", "Land and Housing 2025", "Our Hong Kong Foundation (OHKF)", "Academia u ONG", "https://s3.ourhkfoundation.org.hk/s3fs-public/2025-04/Land-and-Housing-2025_full-report_EN.pdf", "PDF", "Descarga directa", L_NO_VERIF, False, "https://www.ourhkfoundation.org.hk/", "No", "Hong Kong (RAE)", "2025–2029", "Anual", "2026-09-23", "Candidata", "IA (Claude) + verificación en OHKF", "Think tank; solo contexto.", "")
f("F08", "The 2026-27 Budget", "Financial Secretary — Gobierno de la RAE de HK", "Entidad pública", "https://www.budget.gov.hk/2026/eng/budget54.html", "Página web", "Solo PDF o página", L_BUDGET, True, "https://www.budget.gov.hk/2026/eng/notices.html", "No", "Hong Kong (RAE)", "Año fiscal 2026-27", "Anual", "2026-09-23", "Integrada al lago", "IA (Claude) + verificación en budget.gov.hk", "Se citan cifras puntuales (texto), no se reproducen gráficos ni fotos.", "")
f("F09", "The Four Key Industries in the Hong Kong Economy (FA100099)", "Census and Statistics Department (C&SD)", "Entidad pública", "https://www.censtatd.gov.hk/en/scode80.html?productCode=FA100099", "XLSX", "Descarga directa", L_NO_VERIF, False, "https://www.censtatd.gov.hk/", "No", "Hong Kong (RAE)", "2024", "Anual", "2026-09-23", "Integrada al lago", "IA (Claude) + verificación en C&SD", "", "")
f("F10", "Situación de ley y orden 2025 / Police in Figures 2025", "Hong Kong Police Force (HKPF)", "Entidad pública", "https://www.police.gov.hk/ppp_en/09_statistics/csd.html", "Página web", "Solo PDF o página", L_HKPF, True, "https://www.police.gov.hk/ppp_en/11_useful_info/disclaimer.html", "Solo conteos por zona", "Hong Kong (RAE)", "2024–2025", "Anual", "2026-09-23", "Integrada al lago", "IA (Claude) + verificación en HKPF", "Licencia restrictiva: se citan cifras agregadas con atribución; no se redistribuye contenido del sitio. Pedir autorización si el tablero se publica.", "restrictiva")
f("F11", "Corruption Perceptions Index 2025", "Transparency International (difundido por ICAC)", "Academia u ONG", "https://www.icac.org.hk/en/intl-persp/ranking-and-research/corruption-perceptions-index/index.html", "Página web", "Solo PDF o página", L_TI, True, "https://www.transparency.org/en/publications/corruption-perceptions-index-2024", "No", "Internacional (incluye HK)", "2025", "Anual", "2026-09-23", "Integrada al lago", "IA (Claude) + verificación en ICAC y TI", "CC BY-ND: se cita el puntaje sin modificarlo.", "")
f("F12", "Hong Kong: The Facts – Tourism", "gov.hk (datos de HKTB y C&SD)", "Entidad pública", "https://www.gov.hk/en/about/abouthk/factsheets/docs/tourism.pdf", "PDF", "Descarga directa", L_NO_VERIF, False, "https://www.gov.hk/", "No", "Hong Kong (RAE)", "2024/2025", "Anual", "2026-09-23", "Integrada al lago", "IA (Claude) + verificación en gov.hk", "", "")
f("F13", "Hong Kong: The Facts – Country Parks and Special Areas", "Agriculture, Fisheries and Conservation Department (AFCD)", "Entidad pública", "https://www.afcd.gov.hk/english/country/cou_lea/the_facts.html", "Página web", "Solo PDF o página", L_NO_VERIF, False, "https://www.afcd.gov.hk/", "No", "Hong Kong (RAE) por parque", "al 01-03-2024", "No se sabe", "2026-09-23", "Integrada al lago", "IA (Claude) + verificación en AFCD", "", "")
f("F14", "Hong Kong: The Facts – Water Supplies", "Water Supplies Department (WSD)", "Entidad pública", "https://www.wsd.gov.hk/en/publications-and-statistics/pr-publications/the-facts/index.html", "PDF", "Solo PDF o página", L_NO_VERIF, False, "https://www.wsd.gov.hk/", "No", "Hong Kong (RAE)", "2024/25", "Anual", "2026-09-23", "Integrada al lago", "IA (Claude) + verificación en WSD", "", "")
f("F15", "State of Hong Kong Biodiversity 2025", "WWF-Hong Kong", "Academia u ONG", "https://www.wwf.org.hk/en/biodiversity/", "Página web", "Solo PDF o página", L_WWF, True, "https://wwf.org.hk/en/copyright", "No", "Hong Kong (RAE)", "2025", "No se sabe", "2026-09-23", "Integrada al lago", "IA (Claude) + verificación en WWF", "Se acredita a WWF Hong Kong como titular.", "")
f("F16", "Pobreza por distrito y demografía", "Social Indicators of Hong Kong", "Academia u ONG", "https://socialindicators.org.hk/how-many-hong-kong-residents-live-in-poverty-breaking-down-the-latest-statistics-by-district-and-demographics/", "Página web", "Solo PDF o página", L_NO_VERIF, False, "https://socialindicators.org.hk/", "Solo conteos por zona", "Hong Kong por distrito", "~2021–2026 (mezcla)", "No se sabe", "2026-09-23", "Candidata", "IA (Claude); agregador, no fuente primaria", "Dato sensible: ver decisión de protección en la sección Gente del tablero. No se grafica.", "")
f("F17", "Serie histórica de fecundidad (TFR)", "Macrotrends", "Empresa privada", "https://www.macrotrends.net/global-metrics/countries/hkg/hong-kong/fertility-rate", "Página web", "Solo PDF o página", L_MACRO, True, "https://www.macrotrends.net/terms", "No", "Hong Kong (RAE)", "1950–2026", "Anual", "2026-09-23", "Descartada", "IA (Claude) la propuso; descartada tras comprobar", "TFR ~1,44 contradice la natalidad oficial (~4,2 por mil ⇒ TFR < 1).", "restrictiva")
f("F18", "Esperanza de vida por distrito (2016)", "IPC / International Population Conference", "Academia u ONG", "http://ipc2025.popconf.org/uploads/250834", "PDF", "Descarga directa", L_NO_VERIF, False, "http://ipc2025.popconf.org/", "No", "Hong Kong por distrito", "2016", "Única vez", "2026-09-23", "Candidata", "IA (Claude); dato viejo", "Pedir Life Tables actuales al C&SD.", "")
# ---------------- F19–F34 (pipeline del lago) ----------------
f("F19", "Límites de circunscripciones DCCA 2019", "Electoral Affairs Commission (EAC); GeoJSON publicado por hkdce en GitHub", "Entidad pública", "https://raw.githubusercontent.com/hkdce/dcca-boundaries/master/converted-geojson/DCCA_2019.geojson", "GeoJSON", "Descarga directa", "no declara", True, "https://github.com/hkdce/dcca-boundaries", "No", "18 distritos / 452 DCCA", "2019", "Única vez", "2026-10-06", "Integrada al lago", "Búsqueda web de la IA tras rutas inventadas (F37, F38)", "El repositorio no tiene archivo LICENSE (respuesta 404). Polígonos con mar.", "")
f("F20", "Censo 2021 — estadísticas por distrito (DC_21C)", "Census and Statistics Department, vía CSDI", "Entidad pública", "https://portal.csdi.gov.hk/server/services/common/censtatd_rcd_1635932856094_19982/MapServer/WFSServer", "CSV", "API sin llave", L_CSDI, True, "https://portal.csdi.gov.hk/csdi-webpage/doc/TNC?lang=en", "Solo conteos por zona", "18 distritos", "2021", "Única vez", "2026-10-06", "Integrada al lago", "La IA encontró el WFS en la ficha de data.gov.hk", "Validado: grupos de edad y tipos de vivienda suman la población total.", "")
f("F21", "Encuesta General de Hogares por distrito 2016–2025 (DC_GHS)", "Census and Statistics Department, vía CSDI", "Entidad pública", "https://portal.csdi.gov.hk/server/services/common/censtatd_rcd_1635934545173_69201/MapServer/WFSServer", "CSV", "API sin llave", L_CSDI, True, "https://portal.csdi.gov.hk/csdi-webpage/doc/TNC?lang=en", "Solo conteos por zona", "18 distritos", "2016–2025", "Anual", "2026-10-06", "Integrada al lago", "La IA la encontró en data.gov.hk", "Edad mediana redondeada a entero.", "")
f("F22", "Districts of Hong Kong (área terrestre y nombres en chino)", "Wikipedia (Wikimedia Foundation)", "Plataforma colaborativa", "https://en.wikipedia.org/wiki/Districts_of_Hong_Kong", "Página web", "Solo PDF o página", L_NO_VERIF, False, "https://en.wikipedia.org/wiki/Districts_of_Hong_Kong", "No", "18 distritos", "Censo 2021", "No se sabe", "2026-10-06", "Integrada al lago", "Consulta de la IA", "La herramienta no devolvió el pie de licencia del artículo; antes se anotó «CC BY-SA 4.0» de memoria: no se tomó del sitio.", "")
f("F23", "Rutas y paradas de transporte público", "hkbus/hk-bus-crawling (compila datos abiertos de operadores)", "Plataforma colaborativa", "https://raw.githubusercontent.com/hkbus/hk-bus-crawling/gh-pages/routeFareList.min.json", "JSON", "Descarga directa", L_GPL2, True, "https://github.com/hkbus/hk-bus-crawling", "No", "Todo Hong Kong", "vigente a 2026-10", "Diaria", "2026-10-06", "Integrada al lago", "Revisando el paquete npm hk-bus-eta", "GPL-2.0 exige mantener la licencia al redistribuir el archivo crudo.", "")
f("F24", "Hospitales públicos con urgencias (A&E)", "Paquete npm ane-hk", "Plataforma colaborativa", "https://registry.npmjs.org/ane-hk", "Otro", "Descarga directa", "“\"license\": \"GPL-3.0-only\"” — package.json de ane-hk", True, "https://www.npmjs.com/package/ane-hk", "No", "18 hospitales", "vigente a 2026-10", "No se sabe", "2026-10-06", "Integrada al lago", "Búsqueda de la IA en npm", "Solo nombres y coordenadas. Falta el hospital de Kai Tak.", "")
f("F25", "Información de estaciones meteorológicas", "Hong Kong Observatory (HKO)", "Entidad pública", "https://www.hko.gov.hk/en/cis/stn.htm", "Página web", "Solo PDF o página", L_HKO, True, "https://www.hko.gov.hk/en/readme/readme.htm", "No", "86 estaciones", "1884–2026", "No se sabe", "2026-10-06", "Integrada al lago", "Búsqueda web de la IA", "Uso no comercial con condiciones; uso comercial requiere autorización escrita.", "condicionada")
f("F26", "Humedad relativa del último minuto (capa espacial)", "Hong Kong Observatory, vía CSDI", "Entidad pública", "https://portal.csdi.gov.hk/server/services/common/hko_rcd_1634875711587_25731/MapServer/WFSServer", "GeoJSON", "API sin llave", L_CSDI, True, "https://portal.csdi.gov.hk/csdi-webpage/doc/TNC?lang=en", "No", "26 estaciones", "tiempo real", "Tiempo real", "2026-10-06", "Integrada al lago", "Ficha de data.gov.hk", "Control de calidad de coordenadas de F25.", "")
f("F27", "AQHI actual por estación", "Environmental Protection Department (EPD)", "Entidad pública", "https://www.aqhi.gov.hk/epd/ddata/html/out/aqhi_ind_rss_Eng.xml", "Otro", "Descarga directa", L_EPD, True, "https://epd.gov.hk/epd/misc/copyright/english/copyright.html", "No", "18 estaciones", "captura 2026-10-06 07:30 HKT", "Tiempo real", "2026-10-06", "Integrada al lago", "Ficha de data.gov.hk", "Solo uso no comercial con atribución a EPD.", "condicionada")
f("F28", "PIB per cápita de Hong Kong (US$ corrientes)", "Banco Mundial, publicado por FRED", "Entidad pública", "https://fred.stlouisfed.org/data/PCAGDPHKA646NWDB", "Página web", "Solo PDF o página", L_FRED, True, "https://fred.stlouisfed.org/series/PCAGDPHKA646NWDB", "No", "Hong Kong", "1960–2025", "Anual", "2026-10-06", "Integrada al lago", "Búsqueda web tras fallar la API del Banco Mundial (F43)", "", "")
f("F29", "PIB per cápita de Hong Kong (US$ constantes)", "Banco Mundial, publicado por FRED", "Entidad pública", "https://fred.stlouisfed.org/data/NYGDPPCAPKDHKG", "Página web", "Solo PDF o página", L_FRED, True, "https://fred.stlouisfed.org/series/NYGDPPCAPKDHKG", "No", "Hong Kong", "1961–2025", "Anual", "2026-10-06", "Integrada al lago", "Búsqueda web", "FRED dice “Units: 2010 U.S. Dollars”, pero el valor de 2015 coincide con el corriente (base 2015). Se anota la discrepancia.", "")
f("F30", "Inflación, precios al consumidor (% anual)", "Banco Mundial, publicado por FRED", "Entidad pública", "https://fred.stlouisfed.org/data/FPCPITOTLZGHKG", "Página web", "Solo PDF o página", L_FRED, True, "https://fred.stlouisfed.org/series/FPCPITOTLZGHKG", "No", "Hong Kong", "2000–2025 (usado)", "Anual", "2026-10-06", "Integrada al lago", "Búsqueda web", "", "")
f("F31", "Delitos totales y violentos por mes (CSV)", "Hong Kong Police Force, listado en DATA.GOV.HK", "Entidad pública", "https://www.police.gov.hk/info/doc/crime_details_overall.csv", "CSV", "Descarga directa", L_DATAGOV, True, "https://data.gov.hk/en/terms-and-conditions", "Solo conteos por zona", "Hong Kong (sin distritos)", "2022-01 a 2024-12", "Mensual", "2026-10-06", "Integrada al lago", "Ficha de data.gov.hk", "Se aplica la licencia de DATA.GOV.HK (donde está listado), no el aviso restrictivo del sitio de la Policía (F10).", "")
f("F32", "Titulares de prensa sobre Hong Kong", "Varios medios (The Standard, SCMP, RTHK, TVB, info.gov.hk…)", "Medio de comunicación", "(32 URL, una por titular, en public/data/escucha.json)", "Página web", "Solo PDF o página", "no declara (cada medio tiene sus propios términos; no se verificaron uno por uno)", False, "", "Texto libre sin revisar", "Hong Kong", "2025–2026-10", "Única vez", "2026-10-06", "Integrada al lago", "8 búsquedas web de la IA", "Solo titular y enlace. Revisar si nombran personas antes de publicar.", "")
f("F33", "Diccionario de barrios por distrito (hk-location.json)", "Paquete npm hkopendata 1.0.0", "Plataforma colaborativa", "https://registry.npmjs.org/hkopendata/-/hkopendata-1.0.0.tgz", "JSON", "Descarga directa", "“\"license\": \"MIT\"” — package.json de hkopendata", True, "https://www.npmjs.com/package/hkopendata", "No", "18 distritos", "No se sabe", "Única vez", "2026-10-06", "Integrada al lago", "Búsqueda de la IA en npm", "Buscador de barrios y detección de distritos en titulares.", "")
f("F34", "Tasa de desempleo desestacionalizada", "Moody's Analytics (economy.com), con datos del C&SD", "Empresa privada", "https://www.economy.com/hong-kong/unemployment-rate", "Página web", "Solo PDF o página", L_MOODYS, True, "https://www.moodys.com/web/en/us/legal/terms-of-use.html", "No", "Hong Kong", "2026-05 a 2026-08", "Mensual", "2026-10-06", "Descartada", "Búsqueda web", "Sitio privado con términos restrictivos: se retira del tablero. Reemplazar por la tabla oficial 210-06101 del C&SD.", "restrictiva")
# ---------------- F35–F45 (probadas, no integradas) ----------------
f("F35", "Censo 2021 — perfiles por distrito (DC_21C.xlsx)", "Census and Statistics Department", "Entidad pública", "https://www.census2021.gov.hk/doc/DC_21C.xlsx", "XLSX", "Bloquea scripts o pide sesión", L_NO_VERIF, False, "", "Solo conteos por zona", "18 distritos", "2021", "Única vez", "2026-10-06", "Candidata", "Página District Profiles del censo", "Mismos datos que F20; el entorno no pudo leer el binario.", "")
f("F36", "API de tablas web del C&SD (get.php)", "Census and Statistics Department", "Entidad pública", "https://www.censtatd.gov.hk/api/get.php?id=130-06805&lang=en&full_series=1", "JSON", "API sin llave", L_NO_VERIF, False, "", "Solo conteos por zona", "Hong Kong", "varía", "Mensual", "2026-10-06", "No responde", "La IA la propuso", "Respondió «Parameter is not defined».", "")
f("F37", "geoBoundaries — Hong Kong ADM1", "William & Mary geoLab", "Academia u ONG", "https://raw.githubusercontent.com/wmgeolab/geoBoundaries/main/releaseData/gbOpen/HKG/ADM1/geoBoundaries-HKG-ADM1.geojson", "GeoJSON", "Descarga directa", "no declara", False, "", "No", "Hong Kong", "—", "No se sabe", "2026-10-06", "No existe (la inventó la IA)", "La IA supuso la ruta", "404.", "")
f("F38", "Highcharts Map Collection — Hong Kong", "Highsoft", "Empresa privada", "https://registry.npmjs.org/@highcharts/map-collection", "JSON", "Descarga directa", "no declara", False, "", "No", "Hong Kong", "—", "No se sabe", "2026-10-06", "No existe (la inventó la IA)", "La IA supuso que traía countries/hk", "La versión 2.3.3 no incluye Hong Kong.", "")
f("F39", "DC2015_JSON — elecciones 2015", "UnKnoWn-Consortium (GitHub)", "Plataforma colaborativa", "https://github.com/UnKnoWn-Consortium/DC2015_JSON", "JSON", "Descarga directa", "no declara", False, "", "Personas identificables", "Circunscripciones 2015", "2015", "Única vez", "2026-10-06", "Descartada", "Búsqueda web", "Sin licencia y con datos de candidatos.", "")
f("F40", "hkdatasets — accidentes de tránsito 2014–2019", "Hong Kong Districts Info (paquete R)", "Academia u ONG", "https://github.com/Hong-Kong-Districts-Info/hkdatasets", "Otro", "Descarga directa", L_NO_VERIF, False, "", "No", "Hong Kong (puntos)", "2014–2019", "Única vez", "2026-10-06", "Descartada", "README del paquete", "Formato .fst no legible; datos viejos.", "")
f("F41", "Temperatura del último minuto por estación (CSV)", "Hong Kong Observatory", "Entidad pública", "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/latest_1min_temperature.csv", "CSV", "Bloquea scripts o pide sesión", L_DATAGOV, True, "https://data.gov.hk/en/terms-and-conditions", "No", "Estaciones HKO", "tiempo real", "Tiempo real", "2026-10-06", "Candidata", "Ficha de data.gov.hk", "robots.txt bloquea a la herramienta. El tablero ya no consulta clima en vivo: solo lee archivos del repo.", "")
f("F42", "Population and Household Statistics by DC District 2024 (PDF)", "Census and Statistics Department", "Entidad pública", "https://gia.info.gov.hk/general/202503/28/P2025032800255_490449_1_1743135159842.pdf", "PDF", "Solo PDF o página", L_NO_VERIF, False, "", "Solo conteos por zona", "18 distritos", "2024", "Anual", "2026-10-06", "Descartada", "Búsqueda web", "Mismos datos que F21.", "")
f("F43", "API de indicadores del Banco Mundial", "Banco Mundial", "Entidad pública", "https://api.worldbank.org/v2/country/HKG/indicator/NY.GDP.MKTP.CD?format=json", "JSON", "API sin llave", L_NO_VERIF, False, "", "No", "Hong Kong", "1960–2025", "Anual", "2026-10-06", "No responde", "La IA la propuso", "El permiso de consulta venció sin respuesta; reemplazada por FRED.", "")
f("F44", "Archivo histórico de DATA.GOV.HK", "Digital Policy Office", "Entidad pública", "https://api.data.gov.hk/v1/historical-archive/list-files", "JSON", "API sin llave", L_DATAGOV, True, "https://data.gov.hk/en/terms-and-conditions", "No", "Hong Kong", "varía", "Diaria", "2026-10-06", "Candidata", "La IA la probó", "Útil para series históricas de AQHI.", "")
f("F45", "Página de referencia Cerebro Lima", "Proyecto de referencia (Vercel)", "No se sabe", "https://cerebro-lima.vercel.app/", "Página web", "Bloquea scripts o pide sesión", "no declara", False, "", "No", "Lima", "—", "No se sabe", "2026-10-26", "Descartada", "La entregó el profesor/usuario como modelo", "Solo referencia de diseño; pide clave de acceso.", "")

# ---- archivo del lago (public/data) → fuentes que lo alimentan ----
ARCHIVOS = {
    "panorama.json": ["F20", "F21", "F22", "F23", "F24", "F25", "F27", "F28", "F30", "F32", "F10"],
    "geo.json": ["F19", "F22"],
    "geo_circunscripciones.json": ["F19"],
    "demografia.json": ["F20", "F21", "F22"],
    "economia.json": ["F20", "F21", "F28", "F29", "F30", "F10"],
    "infraestructura.json": ["F23", "F24", "F19"],
    "infraestructura_paradas.json": ["F23", "F19"],
    "sensores.json": ["F25", "F26", "F27", "F19"],
    "escucha.json": ["F32", "F33", "F31"],
    "atlas_zonas.json": ["F19", "F20", "F21", "F22", "F23", "F24", "F25", "F27", "F32"],
    "atlas_distribuidos.json": ["F23", "F24", "F25"],
    "hex_h3_res8.geojson": ["F23", "F24", "F25"],
    "correlaciones.json": ["F20", "F21", "F22", "F23", "F24"],
    "perfil_wiki.json": [f"F{i:02d}" for i in range(1, 16)],
    "barrios.json": ["F33"],
    "fuentes.json": [],
    "conciliacion.json": [],
}
# ID antiguo (texto) → F0x
ANTIGUOS = {"eac_dcca_2019": "F19", "census2021_dc": "F20", "ghs_dc_2016_2025": "F21", "wiki_distritos": "F22",
            "hkbus_routefarelist": "F23", "ha_hospitales": "F24", "hko_estaciones": "F25", "hko_csdi_humedad": "F26",
            "epd_aqhi": "F27", "hkpf_delitos": "F31", "noticias_escucha": "F32", "hkopendata_lugares": "F33",
            "unemployment_recent": "F34", "fred_worldbank": "F28; F29; F30"}

# ---- conciliación: misma idea en la wiki (copiada a mano) y en el lago (descargada) ----
def conciliacion():
    d = json.loads((PUBLIC / "demografia.json").read_text())["distritos"]
    k = json.loads((PUBLIC / "panorama.json").read_text())["kpis"]
    pob = sum(x["poblacion_2021"] for x in d)
    s = lambda c: sum(x[c] for x in d)  # noqa: E731
    pct = lambda c: round(100 * s(c) / pob, 2)  # noqa: E731
    rec = {r["indicador"] + "_" + r["periodo"]: r["valor"] for r in json.loads((PUBLIC / "economia.json").read_text())["indicadores_recientes"]}
    filas = [
        ("% de 65+ (2021)", "poblacion.pct_65_mas_2021", 20.5, "F02", "demografia.json · pob_65_mas / poblacion_2021", round(100 * s("pob_65_mas") / pob, 2), "F20",
         "Distinta base: la proyección (F02) excluye empleadas domésticas extranjeras; el censo las incluye.", "Se usa el lago (19,6 %). La wiki se cita solo para la proyección 2046."),
        ("Personas de 65+ (2021)", "poblacion.poblacion_65_mas_2021", 1450000, "F02", "demografia.json · pob_65_mas", s("pob_65_mas"), "F20", "Coinciden (la wiki redondea).", "Se usa el lago."),
        ("Densidad media (hab/km²)", "poblacion.densidad_hab_km2", 6801, "F01", "panorama.json · kpis.densidad_media_hab_km2", k["densidad_media_hab_km2"], "F20; F22",
         "Distinto año: la wiki usa población 2026 sobre otra área; el lago usa censo 2021 / área terrestre oficial.", "Se usa el lago."),
        ("% en vivienda pública de alquiler", "vivienda.pct_vivienda_publica_alquiler", 29, "F06", "demografia.json · pob_vivienda_publica_alquiler", pct("pob_vivienda_publica_alquiler"), "F20", "Coinciden con redondeo distinto.", "Se usa el lago."),
        ("% en vivienda subsidiada en propiedad", "vivienda.pct_vivienda_subsidiada_propiedad", 15.8, "F06", "demografia.json · pob_vivienda_subsidiada_venta", pct("pob_vivienda_subsidiada_venta"), "F20", "Diferencia de 0,1 pp (fuente y año distintos).", "Se usa el lago."),
        ("% en vivienda privada permanente", "vivienda.pct_vivienda_privada_permanente", 53.2, "F06", "demografia.json · pob_vivienda_privada", pct("pob_vivienda_privada"), "F20", "Diferencia de 0,3 pp.", "Se usa el lago."),
        ("% en alojamiento no doméstico", "vivienda.pct_vivienda_no_domestica", 1.2, "F06", "demografia.json · pob_no_domestica", pct("pob_no_domestica"), "F20", "Coinciden con redondeo distinto.", "Se usa el lago."),
        ("% en vivienda temporal", "vivienda.pct_vivienda_temporal", 0.7, "F06", "demografia.json · pob_vivienda_temporal", pct("pob_vivienda_temporal"), "F20", "Diferencia de 0,1 pp.", "Se usa el lago."),
        ("% en vivienda pública o subsidiada", "vivienda.pct_poblacion_vivienda_publica_o_subsidiada", 45, "F06", "demografia.json · pública + subsidiada", round(pct("pob_vivienda_publica_alquiler") + pct("pob_vivienda_subsidiada_venta"), 2), "F20", "Coinciden.", "Se usa el lago."),
        ("Educación superior 15+ (2021)", "poblacion.pct_15mas_educacion_superior_2021", 34.6, "F03", "demografia.json · pct_titulo_universitario_15_mas (ciudad)", round(100 * s("pob_15_mas_con_titulo_universitario") / (pob - s("pob_0_14")), 2), "F20",
         "Definiciones distintas: la wiki incluye educación superior no universitaria; el lago solo título universitario.", "Se muestran las dos con su definición explícita."),
        ("Delitos totales 2025", "seguridad.delitos_totales_2025", 89137, "F10", "economia.json · indicadores_recientes", rec.get("delitos_totales_2025"), "F10", "Coinciden.", "Se usa la wiki (trae además las variaciones)."),
        ("Delitos violentos 2025", "seguridad.delitos_violentos_2025", 8823, "F10", "economia.json · indicadores_recientes", rec.get("delitos_violentos_2025"), "F10", "Coinciden.", "Se usa la wiki."),
    ]
    return [dict(zip(["indicador", "campo_wiki", "valor_wiki", "fuente_wiki", "campo_lago", "valor_lago", "fuente_lago", "diagnostico", "decision"], r)) for r in filas]


# campos de la wiki que la web NO usa porque el lago tiene la versión descargada
REEMPLAZADOS = {r for r in ["poblacion.pct_65_mas_2021", "poblacion.poblacion_65_mas_2021", "poblacion.densidad_hab_km2",
                            "vivienda.pct_vivienda_publica_alquiler", "vivienda.pct_vivienda_subsidiada_propiedad",
                            "vivienda.pct_vivienda_privada_permanente", "vivienda.pct_vivienda_no_domestica",
                            "vivienda.pct_vivienda_temporal", "vivienda.pct_poblacion_vivienda_publica_o_subsidiada"]}


def main():
    for x in F:
        x["archivos_lago"] = [a for a, ids in ARCHIVOS.items() if x["id"] in ids]
    salida = {"fecha_licencias": HOY, "nota": "Catálogo único: F01–F18 del equipo (wiki), F19–F34 del pipeline, F35–F45 probadas y no integradas.",
              "fuentes": F, "archivos": ARCHIVOS, "ids_antiguos": ANTIGUOS}
    (ROOT / "catalogo" / "fuentes.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")
    escribir_json(PUBLIC / "fuentes.json", salida)
    escribir_json(PUBLIC / "conciliacion.json", {"nota": "Cifras de la wiki (copiadas a mano) frente a las del lago (descargadas por el pipeline). La web usa una sola por concepto.",
                                                 "filas": conciliacion(), "reemplazados": sorted(REEMPLAZADOS)})
    print(len(F), "fuentes ·", sum(1 for x in F if x["licencia_verificada"]), "licencias verificadas ·",
          sum(1 for x in F if x["riesgo_licencia"]), "con riesgo")


if __name__ == "__main__":
    main()
