"""Genera el diccionario de datos del lago (un registro por campo de cada tabla de curated/).

Uso:
    python pipeline/diccionario.py
Salidas:
    catalogo/diccionario_datos.csv
    catalogo/diccionario_datos.xlsx
"""
from __future__ import annotations

import glob
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CUR = ROOT / "curated"

COLUMNAS = ["ID fuente", "Archivo o tabla en el lago", "Nombre del campo en el lago", "Nombre original en la fuente",
            "Qué significa (en una frase)", "Tipo de dato", "Unidad de medida", "Ejemplo de valor",
            "¿Puede venir vacío?", "Valores permitidos o rango", "Clasificación", "Transformación que le hicieron",
            "Pregunta del sistema que ayuda a responder"]

# ---------------------------------------------------------------------------
# Fuente por tabla (la de la mayoría de sus campos) y excepciones por campo
# ---------------------------------------------------------------------------
FUENTE_TABLA = {
    "geo/distritos.csv": "eac_dcca_2019",
    "geo/circunscripciones_dcca_2019.csv": "eac_dcca_2019",
    "demografia/distritos_censo2021.csv": "census2021_dc",
    "demografia/panel_poblacion_2016_2025.csv": "ghs_dc_2016_2025",
    "economia/distritos_economia.csv": "census2021_dc",
    "economia/panel_ingreso_empleo_2016_2025.csv": "ghs_dc_2016_2025",
    "economia/macro_anual_2000_2025.csv": "fred_worldbank",
    "economia/indicadores_recientes.csv": "hkpf_delitos; unemployment_recent",
    "infraestructura/paradas_transporte.csv": "hkbus_routefarelist",
    "infraestructura/estaciones_mtr.csv": "hkbus_routefarelist",
    "infraestructura/hospitales_urgencias.csv": "ha_hospitales",
    "infraestructura/acceso_hospital_por_circunscripcion.csv": "ha_hospitales; eac_dcca_2019",
    "infraestructura/distritos_infraestructura.csv": "hkbus_routefarelist",
    "sensores/estaciones_hko.csv": "hko_estaciones",
    "sensores/estaciones_hko_csdi_control_calidad.csv": "hko_csdi_humedad; hko_estaciones",
    "sensores/aqhi_estaciones_snapshot.csv": "epd_aqhi",
    "sensores/distritos_sensores.csv": "hko_estaciones; epd_aqhi",
    "escucha/noticias.csv": "noticias_escucha",
    "escucha/temas_resumen.csv": "noticias_escucha",
    "escucha/menciones_por_distrito.csv": "noticias_escucha; hkopendata_lugares",
    "escucha/delitos_mensuales.csv": "hkpf_delitos",
    "atlas_zonas/atlas_distritos.csv": "derivado",
    "atlas_zonas/atlas_circunscripciones.csv": "derivado",
    "atlas_zonas/tipologias_centros_estandarizados.csv": "derivado",
    "atlas_distribuidos/puntos.csv": "derivado",
    "atlas_distribuidos/hex_h3_res8.csv": "derivado",
    "correlaciones/matriz_pearson.csv": "derivado",
    "correlaciones/matriz_spearman.csv": "derivado",
    "correlaciones/pares.csv": "derivado",
}
FUENTE_CAMPO = {
    "area_km2_oficial": "wiki_distritos",
    "densidad_hab_km2": "census2021_dc; wiki_distritos",
    "poblacion_2025": "ghs_dc_2016_2025",
    "var_pob_2016_2025_pct": "ghs_dc_2016_2025",
    "ingreso_mediano_hogar_hkd_2025": "ghs_dc_2016_2025",
    "tasa_participacion_laboral_pct_2025": "ghs_dc_2016_2025",
    "var_ingreso_2016_2025_pct": "ghs_dc_2016_2025",
    "indice_ingreso_vs_mediana_distritos": "ghs_dc_2016_2025",
    "hospitales_urgencias": "ha_hospitales",
    "hab_por_hospital_urgencias": "ha_hospitales; census2021_dc",
    "dist_media_hospital_km": "ha_hospitales; eac_dcca_2019",
    "paradas_por_km2": "hkbus_routefarelist; wiki_distritos",
    "paradas_por_10k_hab": "hkbus_routefarelist; census2021_dc",
    "codigo": "eac_dcca_2019", "distrito_en": "eac_dcca_2019", "distrito_zh": "wiki_distritos",
    "distrito_es": "eac_dcca_2019", "region": "eac_dcca_2019", "codigo_dcca": "eac_dcca_2019",
}

# ---------------------------------------------------------------------------
# Metadatos por campo: (significado, unidad, nombre original, transformación, pregunta, rol)
# ---------------------------------------------------------------------------
C21 = "Censo 2021 (DC_21C)"
GHS = "Encuesta General de Hogares (DC_GHS)"
M = {
    # Identificadores y nombres
    "codigo": ("Código de letra del distrito (A–T) usado por el censo y la EAC.", "—", "dc_class / 1ª letra de CACODE",
               "Derivado de la primera letra del código DCCA; se usa como llave de unión entre todas las tablas.",
               "¿A qué distrito pertenece este registro?", "Identificador"),
    "distrito_en": ("Nombre oficial del distrito en inglés.", "—", "dc_eng", "Estandarizado contra la tabla maestra de 18 distritos.",
                    "¿Cómo se llama el distrito?", "Dimensión"),
    "distrito_zh": ("Nombre del distrito en chino tradicional.", "—", "District (中文)", "Tomado de la tabla de Wikipedia y unido por nombre inglés.",
                    "¿Cómo se llama el distrito en chino?", "Dimensión"),
    "distrito_es": ("Nombre del distrito en español para la interfaz.", "—", "(no existe en la fuente)", "Traducción propia del nombre inglés.",
                    "¿Cómo mostrar el distrito al usuario?", "Dimensión"),
    "region": ("Gran región a la que pertenece el distrito (Isla de HK, Kowloon o Nuevos Territorios).", "—", "(no existe en la fuente)",
               "Asignada por tabla maestra según la división administrativa oficial; traducida al español.",
               "¿Cómo se reparte la población entre las tres regiones? (Wiki 1.2)", "Dimensión"),
    "codigo_dcca": ("Código de la circunscripción del Consejo de Distrito (DCCA 2019).", "—", "CACODE",
                    "Renombrado; para puntos se asigna por unión espacial punto-en-polígono (o polígono más cercano ≤1 km).",
                    "¿En qué circunscripción cae este punto o zona?", "Identificador"),
    "nombre_en": ("Nombre en inglés del lugar (circunscripción, parada o estación).", "—", "ENAME / name.en", "Renombrado.",
                  "¿Cómo se llama este lugar?", "Dimensión"),
    "nombre_zh": ("Nombre en chino del lugar (circunscripción, parada o estación).", "—", "CNAME / name.zh", "Renombrado.",
                  "¿Cómo se llama este lugar en chino?", "Dimensión"),
    # Geo
    "area_km2_oficial": ("Superficie terrestre oficial del distrito.", "km²", "Area (km²)", "Copiado; unido por nombre inglés del distrito.",
                         "¿Cuál es la densidad real de cada distrito? (Wiki 1.2, 6.5)", "Métrica"),
    "area_km2_poligono_incluye_mar": ("Área del polígono del distrito calculada en SIG, incluye superficie marina.", "km²", "(calculado)",
                                      "Disolución de DCCA por distrito y cálculo de área en EPSG:2326.",
                                      "¿Cuánto mar incluyen los límites administrativos?", "Métrica"),
    "area_km2_poligono": ("Área del polígono de la circunscripción calculada en SIG (incluye mar).", "km²", "Shape_Area (recalculado)",
                          "Área recalculada en EPSG:2326 tras reparar geometrías (buffer 0).",
                          "¿Qué tan grande es cada circunscripción?", "Métrica"),
    "centro_lat": ("Latitud de un punto representativo interior del distrito (para etiquetas en el mapa).", "grados decimales (WGS84)", "(calculado)",
                   "representative_point() del polígono disuelto, reproyectado a WGS84.", "¿Dónde ubicar la etiqueta del distrito en el mapa?", "Geoespacial"),
    "centro_lon": ("Longitud de un punto representativo interior del distrito.", "grados decimales (WGS84)", "(calculado)",
                   "representative_point() del polígono disuelto, reproyectado a WGS84.", "¿Dónde ubicar la etiqueta del distrito en el mapa?", "Geoespacial"),
    "n_circunscripciones": ("Número de circunscripciones DCCA 2019 dentro del distrito.", "conteo", "(calculado)", "Conteo de DCCA por código de distrito.",
                            "¿Con cuánto detalle territorial se puede analizar cada distrito?", "Métrica"),
    # Demografía
    "poblacion_2021": ("Población residente total del distrito en el Censo 2021.", "personas", "t_pop", "Renombrado; descarga vía WFS CSDI.",
                       "¿Cuánta gente vive en cada distrito? (Wiki 1)", "Métrica"),
    "hogares_2021": ("Número de hogares domésticos en 2021.", "hogares", "dh", "Renombrado.", "¿Cuántos hogares hay por distrito?", "Métrica"),
    "tamano_medio_hogar": ("Promedio de personas por hogar doméstico.", "personas/hogar", "adhz", "Renombrado.",
                           "¿Dónde viven hogares más grandes o más pequeños? (Wiki 2.8)", "Métrica"),
    "edad_mediana": ("Edad que divide a la población en dos mitades.", "años", f"t_ma ({C21}) / lbnp_ma_t ({GHS})",
                     "Renombrado; en el panel GHS la fuente la publica redondeada a entero.",
                     "¿Qué distritos están más envejecidos? (Wiki 1.3)", "Métrica"),
    "razon_sexos_hombres_por_1000_mujeres": ("Hombres por cada 1.000 mujeres (incluye empleadas domésticas extranjeras).", "hombres por 1.000 mujeres", "sr",
                                             "Renombrado.", "¿Cuál es el balance entre hombres y mujeres? (Wiki 1.3)", "Métrica"),
    "pob_0_14": ("Población de 0 a 14 años.", "personas", "age_1", "Renombrado; validado: la suma de los 5 grupos = t_pop.",
                 "¿Cuántos niños hay por distrito? (Wiki 1.3, 1.10)", "Métrica"),
    "pob_15_24": ("Población de 15 a 24 años.", "personas", "age_2", "Renombrado.", "¿Cuántos jóvenes hay por distrito?", "Métrica"),
    "pob_25_44": ("Población de 25 a 44 años.", "personas", "age_3", "Renombrado.", "¿Dónde se concentra la población adulta joven?", "Métrica"),
    "pob_45_64": ("Población de 45 a 64 años.", "personas", "age_4", "Renombrado.", "¿Dónde se concentra la población adulta mayor?", "Métrica"),
    "pob_65_mas": ("Población de 65 años o más.", "personas", "age_5", "Renombrado.", "¿Cuántas personas mayores hay por distrito? (Wiki 1.3)", "Métrica"),
    "pct_0_14": ("Porcentaje de la población con 0–14 años.", "%", "(calculado)", "100 × age_1 / t_pop, 2 decimales.",
                 "¿Qué distritos tienen más peso de niños? (Wiki 1.10)", "Métrica"),
    "pct_15_24": ("Porcentaje de la población con 15–24 años.", "%", "(calculado)", "100 × age_2 / t_pop.", "¿Qué peso tienen los jóvenes en cada distrito?", "Métrica"),
    "pct_25_44": ("Porcentaje de la población con 25–44 años.", "%", "(calculado)", "100 × age_3 / t_pop.", "¿Qué peso tiene la población adulta joven?", "Métrica"),
    "pct_45_64": ("Porcentaje de la población con 45–64 años.", "%", "(calculado)", "100 × age_4 / t_pop.", "¿Qué peso tiene la población adulta mayor?", "Métrica"),
    "pct_65_mas": ("Porcentaje de la población con 65 años o más.", "%", "(calculado)", "100 × age_5 / t_pop, 2 decimales.",
                   "¿Qué distritos están más envejecidos? (Wiki 1.3)", "Métrica"),
    "indice_envejecimiento": ("Personas de 65+ por cada 100 menores de 15 años.", "personas 65+ por 100 de 0–14", "(calculado)", "100 × age_5 / age_1.",
                              "¿Dónde hay más mayores que niños? (Wiki 1.3)", "Métrica"),
    "pob_15_mas_con_titulo_universitario": ("Personas de 15+ cuyo nivel más alto es título universitario (grado).", "personas", "edu_deg",
                                            "Renombrado. No incluye educación superior no universitaria.",
                                            "¿Cuánta población tiene educación universitaria? (Wiki 1.6)", "Métrica"),
    "pct_titulo_universitario_15_mas": ("Porcentaje de la población de 15+ con título universitario.", "%", "(calculado)",
                                        "100 × edu_deg / (t_pop − age_1).", "¿Qué distritos tienen más capital humano? (Wiki 1.6)", "Métrica"),
    "pob_nacida_en_hk": ("Personas nacidas en Hong Kong.", "personas", "born_hk", "Renombrado.", "¿Dónde vive más población local vs. migrante? (Wiki 1.9)", "Métrica"),
    "pct_nacida_en_hk": ("Porcentaje de la población nacida en Hong Kong.", "%", "(calculado)", "100 × born_hk / t_pop.",
                         "¿Qué distritos tienen más población nacida fuera? (Wiki 1.9)", "Métrica"),
    "pob_vivienda_publica_alquiler": ("Personas que viven en vivienda pública de alquiler (PRH).", "personas", "pop_pub", "Renombrado; validado: suma de tipos = t_pop.",
                                      "¿Cuánta gente depende de vivienda pública? (Wiki 2.4)", "Métrica"),
    "pob_vivienda_subsidiada_venta": ("Personas que viven en vivienda subsidiada en propiedad (HOS y similares).", "personas", "pop_s",
                                      "Renombrado; el guion '-' de la fuente se convirtió en 0.", "¿Cuánta gente vive en vivienda subsidiada? (Wiki 2.4)", "Métrica"),
    "pob_vivienda_privada": ("Personas que viven en vivienda privada permanente.", "personas", "pop_pri", "Renombrado.", "¿Cuánta gente vive en vivienda privada? (Wiki 2.4)", "Métrica"),
    "pob_vivienda_temporal": ("Personas que viven en vivienda temporal.", "personas", "pop_tem", "Renombrado.", "¿Dónde persiste la vivienda temporal? (Wiki 2.7)", "Métrica"),
    "pob_no_domestica": ("Personas en alojamientos no domésticos (residencias, instituciones).", "personas", "pop_non", "Renombrado.",
                         "¿Cuánta población vive fuera de hogares domésticos? (Wiki 2.4)", "Métrica"),
    "pct_vivienda_publica_alquiler": ("Porcentaje de la población en vivienda pública de alquiler.", "%", "(calculado)", "100 × pop_pub / t_pop.",
                                      "¿Qué distritos dependen más de la vivienda pública? (Wiki 2.4, 2.5)", "Métrica"),
    "pct_vivienda_subsidiada_venta": ("Porcentaje de la población en vivienda subsidiada en propiedad.", "%", "(calculado)", "100 × pop_s / t_pop.",
                                      "¿Dónde pesa más la vivienda subsidiada? (Wiki 2.4)", "Métrica"),
    "pct_vivienda_privada": ("Porcentaje de la población en vivienda privada permanente.", "%", "(calculado)", "100 × pop_pri / t_pop.",
                             "¿Dónde domina el mercado privado de vivienda? (Wiki 2.4)", "Métrica"),
    "densidad_hab_km2": ("Habitantes por kilómetro cuadrado de tierra.", "hab/km²", "(calculado)", "poblacion_2021 / area_km2_oficial, redondeado a entero.",
                         "¿Qué tan denso es cada distrito? (Wiki 1.2)", "Métrica"),
    "poblacion_2025": ("Población terrestre a mitad de 2025 según la Encuesta General de Hogares.", "personas", "my_lp (year=2025)", "Filtrado al último año y unido por código.",
                       "¿Cuánta gente vive hoy en cada distrito? (Wiki 1)", "Métrica"),
    "var_pob_2016_2025_pct": ("Variación porcentual de la población terrestre entre 2016 y 2025.", "%", "(calculado de my_lp)", "100 × (my_lp 2025 / my_lp 2016 − 1).",
                              "¿Qué distritos crecen y cuáles pierden población? (Wiki 1.1, 1.9)", "Métrica"),
    "anio": ("Año de referencia de la observación.", "año", "year", "Convertido a entero.", "¿Cómo evoluciona el indicador en el tiempo?", "Dimensión"),
    "poblacion_mitad_anio": ("Población terrestre a mitad de año del distrito.", "personas", "my_lp", "Renombrado; convertido a entero.",
                             "¿Cómo cambió la población de cada distrito entre 2016 y 2025? (Wiki 1.1)", "Métrica"),
    # Economía
    "ingreso_mediano_hogar_hkd_2021": ("Ingreso mensual mediano de los hogares domésticos en 2021.", "HK$ por mes", "ma_hh", "Renombrado.",
                                       "¿Qué distritos son más ricos o más pobres? (Wiki 1.7)", "Métrica"),
    "ingreso_mediano_hogar_econ_activo_hkd_2021": ("Ingreso mensual mediano de hogares con al menos un miembro económicamente activo (2021).", "HK$ por mes", "ma_econhh",
                                                   "Renombrado.", "¿Cómo cambia la brecha de ingreso al excluir hogares sin trabajadores? (Wiki 1.7)", "Métrica"),
    "ingreso_mediano_mensual_empleo_hkd_2021": ("Ingreso mensual mediano por empleo principal de la población ocupada (2021).", "HK$ por mes", "t_mmearn",
                                                "Renombrado.", "¿Cuánto gana un trabajador típico de cada distrito? (Wiki 1.7)", "Métrica"),
    "tasa_participacion_laboral_pct_2021": ("Porcentaje de la población de 15+ que trabaja o busca trabajo (2021).", "%", "lfpr_t", "Renombrado.",
                                            "¿Qué tan activa es la población en el mercado laboral?", "Métrica"),
    "fuerza_laboral_2021": ("Personas en la fuerza laboral (ocupadas + desocupadas) en 2021.", "personas", "t_lf", "Renombrado.",
                            "¿Cuánta fuerza laboral tiene cada distrito?", "Métrica"),
    "poblacion_ocupada_2021": ("Personas ocupadas residentes en el distrito en 2021.", "personas", "t_wp", "Renombrado.",
                               "¿Cuántos trabajadores residen en cada distrito?", "Métrica"),
    "tasa_ocupacion_sobre_fuerza_laboral_pct": ("Porcentaje de la fuerza laboral que está ocupada (100 − desempleo aproximado).", "%", "(calculado)",
                                                "100 × t_wp / t_lf.", "¿Dónde es mayor el desempleo relativo?", "Métrica"),
    "ingreso_mediano_hogar_hkd_2025": ("Ingreso mensual mediano de los hogares domésticos en 2025.", "HK$ por mes", "ma_hh (year=2025)", "Filtrado al último año del panel GHS.",
                                       "¿Qué distritos tienen menor ingreso hoy? (Wiki 1.7)", "Métrica"),
    "tasa_participacion_laboral_pct_2025": ("Tasa de participación laboral en 2025.", "%", "t_lfpr (year=2025)", "Filtrado al último año del panel GHS.",
                                            "¿Cómo está hoy la participación laboral por distrito?", "Métrica"),
    "var_ingreso_2016_2025_pct": ("Variación porcentual nominal del ingreso mediano del hogar entre 2016 y 2025.", "%", "(calculado de ma_hh)",
                                  "100 × (ma_hh 2025 / ma_hh 2016 − 1); no ajustado por inflación.", "¿Dónde creció más el ingreso? (Wiki 1.7)", "Métrica"),
    "indice_ingreso_vs_mediana_distritos": ("Ingreso mediano del hogar 2025 relativo a la mediana de los 18 distritos (=100).", "índice (mediana = 100)", "(calculado)",
                                            "100 × ingreso 2025 / mediana de los 18 valores.", "¿Qué tan por encima o debajo del típico está cada distrito?", "Métrica"),
    "ingreso_mediano_hogar_hkd": ("Ingreso mensual mediano de los hogares domésticos del distrito en el año.", "HK$ por mes", "ma_hh", "Renombrado; convertido a entero.",
                                  "¿Cómo evolucionó el ingreso de cada distrito 2016–2025? (Wiki 1.7)", "Métrica"),
    "tasa_participacion_laboral_pct": ("Tasa de participación laboral del distrito en el año.", "%", "t_lfpr", "Renombrado.",
                                       "¿Cómo evolucionó la participación laboral 2016–2025?", "Métrica"),
    "pib_per_capita_usd_corrientes": ("PIB por habitante a precios corrientes.", "US$ corrientes", "PCAGDPHKA646NWDB (NY.GDP.PCAP.CD)", "Fecha anual convertida a año; filtrado 2000–2025.",
                                      "¿Qué tan rica es la economía de Hong Kong? (Wiki 3.1)", "Métrica"),
    "pib_per_capita_usd_constantes_2015": ("PIB por habitante a precios constantes (base 2015).", "US$ constantes de 2015", "NYGDPPCAPKDHKG (NY.GDP.PCAP.KD)", "Fecha anual convertida a año; filtrado 2000–2025.",
                                           "¿Cuánto creció la economía en términos reales? (Wiki 3.1)", "Métrica"),
    "inflacion_ipc_pct": ("Variación anual del índice de precios al consumidor.", "%", "FPCPITOTLZGHKG (FP.CPI.TOTL.ZG)", "Fecha anual convertida a año.",
                          "¿Cómo ha evolucionado el costo de vida? (Wiki 2.1, 2.2)", "Métrica"),
    "crecimiento_real_pib_pc_pct": ("Crecimiento anual del PIB per cápita real.", "%", "(calculado)", "Variación porcentual año contra año del PIB per cápita constante.",
                                    "¿En qué años creció o se contrajo la economía?", "Métrica"),
    "indicador": ("Nombre del indicador puntual reciente.", "—", "(rotulado al capturar)", "Nombre normalizado en español y snake_case.",
                  "¿Cuál es el último dato de desempleo y delitos? (Wiki 4.1, 4.2)", "Dimensión"),
    "periodo": ("Periodo al que corresponde el valor (año, mes o ventana móvil).", "—", "Year/Month o periodo publicado",
                "En delitos: año y mes en inglés convertidos a AAAA-MM.", "¿A qué fecha corresponde el dato?", "Dimensión"),
    "valor": ("Valor numérico del indicador.", "según columna unidad", "(valor publicado)", "Copiado tal cual.", "¿Cuál es el valor del indicador?", "Métrica"),
    "unidad": ("Unidad del valor del indicador.", "—", "(rotulado)", "Escrito al capturar.", "¿En qué unidad está el valor?", "Metadato"),
    "fuente": ("Organismo o medio de origen del dato.", "—", "(rotulado / dominio de la URL)",
               "En noticias se extrae el dominio de la URL con expresión regular.", "¿De dónde viene este dato y qué tan confiable es?", "Metadato"),
    "url": ("Enlace a la fuente original.", "URL", "link / url", "Copiado tal cual.", "¿Dónde verificar el dato?", "Metadato"),
    # Infraestructura
    "id_parada": ("Identificador único de la parada en la base consolidada de transporte.", "—", "stopList key", "Copiado; se excluyen paradas sin rutas activas.",
                  "¿Qué parada es?", "Identificador"),
    "lat": ("Latitud del punto.", "grados decimales (WGS84)", "location.lat / Latitude / lat", "En estaciones HKO se convirtió de grados-minutos-segundos a decimal.",
            "¿Dónde está ubicado en el mapa?", "Geoespacial"),
    "lon": ("Longitud del punto.", "grados decimales (WGS84)", "location.lng / Longitude / long", "En estaciones HKO se convirtió de grados-minutos-segundos a decimal.",
            "¿Dónde está ubicado en el mapa?", "Geoespacial"),
    "operadores": ("Operadores que atienden la parada, separados por '|'.", "—", "routeList[].co", "Agregados a partir de todas las rutas que pasan por la parada.",
                   "¿Qué empresas sirven esta parada?", "Dimensión"),
    "modos": ("Modos de transporte presentes en la parada, separados por '|'.", "—", "(derivado de co)",
              "Operador → modo (kmb/ctb/nlb/lrtfeeder=bus, gmb=minibús, mtr=metro, lightRail=tren ligero, ferris=ferry).",
              "¿Qué tipo de transporte hay en cada zona?", "Dimensión"),
    "n_rutas": ("Número de rutas distintas que pasan por la parada o estación.", "rutas", "(calculado)", "Conteo de pares operador:ruta que incluyen la parada.",
                "¿Qué tan bien servida está la parada?", "Métrica"),
    "ubicacion_en_tierra": ("Indica si el punto cae dentro de un polígono DCCA (Verdadero) o se asignó al más cercano (Falso).", "booleano", "(calculado)",
                            "Unión espacial: distancia 0 = dentro; >0 y ≤1 km = asignado al más cercano.", "¿Es confiable la asignación territorial del punto?", "Metadato"),
    "codigo_estacion": ("Código de la estación (MTR de 3 letras u HKO).", "—", "stop id MTR / code HKO", "Renombrado.", "¿Qué estación es?", "Identificador"),
    "hospital_en": ("Nombre del hospital en inglés.", "—", "Hospital", "Copiado.", "¿Qué hospital es?", "Identificador"),
    "hospital_zh": ("Nombre del hospital en chino.", "—", "HospitalZh", "Copiado.", "¿Cómo se llama el hospital en chino?", "Dimensión"),
    "servicio": ("Tipo de servicio del hospital incluido en la tabla.", "—", "(rotulado)", "Constante 'A&E (urgencias)'.", "¿Qué servicio ofrece?", "Dimensión"),
    "hospital_urgencias_mas_cercano": ("Hospital con urgencias más cercano al centro de la circunscripción.", "—", "(calculado)",
                                       "Vecino más cercano en EPSG:2326 desde el punto representativo de la DCCA.", "¿A qué hospital iría alguien de esta zona? (Wiki 1.8)", "Dimensión"),
    "distancia_hospital_m": ("Distancia en línea recta al hospital con urgencias más cercano.", "metros", "(calculado)",
                             "Distancia euclidiana en EPSG:2326, redondeada.", "¿Qué zonas están más lejos de una urgencia? (Wiki 1.8)", "Métrica"),
    "paradas_transporte": ("Número de paradas de transporte público con rutas activas.", "paradas", "(calculado)", "Conteo de paradas por código de distrito o DCCA.",
                           "¿Qué zonas tienen más oferta de transporte?", "Métrica"),
    "paradas_bus": ("Paradas servidas por bus.", "paradas", "(calculado)", "Conteo de paradas cuyo campo modos contiene 'bus'.", "¿Dónde hay más cobertura de bus?", "Métrica"),
    "paradas_minibus": ("Paradas servidas por minibús verde (GMB).", "paradas", "(calculado)", "Conteo de paradas con modo 'minibus'.", "¿Dónde depende la gente del minibús?", "Métrica"),
    "paradas_metro_mtr": ("Estaciones del MTR (ferrocarril pesado).", "estaciones", "(calculado)", "Conteo de paradas con modo 'metro_mtr'.", "¿Qué distritos tienen más acceso al metro?", "Métrica"),
    "paradas_tren_ligero": ("Paradas del tren ligero (Light Rail).", "paradas", "(calculado)", "Conteo de paradas con modo 'tren_ligero'.", "¿Dónde opera el tren ligero?", "Métrica"),
    "paradas_ferry": ("Muelles servidos por ferris.", "muelles", "(calculado)", "Conteo de paradas con modo 'ferry'.", "¿Qué zonas dependen del ferry?", "Métrica"),
    "hospitales_urgencias": ("Hospitales públicos con urgencias ubicados en el distrito.", "hospitales", "(calculado)", "Conteo tras unión espacial de hospitales a distritos.",
                             "¿Cuántas urgencias hay en cada distrito? (Wiki 1.8)", "Métrica"),
    "rutas_distintas": ("Número de rutas distintas que tocan al menos una parada del distrito.", "rutas", "(calculado)", "Conteo de pares operador:ruta únicos por distrito.",
                        "¿Qué tan conectado está el distrito con el resto de la ciudad?", "Métrica"),
    "paradas_por_km2": ("Paradas de transporte por km² de tierra.", "paradas/km²", "(calculado)", "paradas_transporte / area_km2_oficial.",
                        "¿Dónde es más densa la red de transporte?", "Métrica"),
    "paradas_por_10k_hab": ("Paradas de transporte por cada 10.000 habitantes.", "paradas por 10.000 hab", "(calculado)", "10.000 × paradas_transporte / poblacion_2021.",
                            "¿Qué distritos tienen menos transporte por habitante?", "Métrica"),
    "hab_por_hospital_urgencias": ("Habitantes por cada hospital con urgencias dentro del distrito.", "hab/hospital", "(calculado)",
                                   "poblacion_2021 / hospitales_urgencias; vacío si el distrito no tiene ninguno.", "¿Qué distritos están más presionados en urgencias? (Wiki 1.8)", "Métrica"),
    "dist_media_hospital_km": ("Distancia media de las circunscripciones del distrito a la urgencia más cercana.", "km", "(calculado)",
                               "Promedio por distrito de distancia_hospital_m / 1000.", "¿Qué distritos tienen peor acceso a urgencias? (Wiki 1.8)", "Métrica"),
    # Sensores
    "estacion": ("Nombre de la estación de monitoreo.", "—", "Station / station_name", "Renombrado.", "¿Qué estación es?", "Identificador"),
    "tipo": ("Tipo de estación de monitoreo.", "—", "type / station_type", "Traducido al español (tripulada, automática, boya, viento, pluviómetro, mareógrafo; general, borde de vía).",
             "¿Qué mide o qué tipo de estación es?", "Dimensión"),
    "elevacion_m": ("Altura de la estación sobre el nivel medio del mar.", "metros", "Elevation (m)", "Copiado; vacío en mareógrafos.", "¿A qué altura mide la estación? (Wiki 6.1)", "Métrica"),
    "inicio_operacion": ("Fecha de inicio de operación de la estación.", "fecha (DD/MM/AAAA)", "First operation", "Copiado como texto.", "¿Desde cuándo hay datos de la estación?", "Metadato"),
    "station_en": ("Nombre de la estación en la capa espacial CSDI.", "—", "AutomaticWeatherStation_en", "Copiado.", "¿Coinciden las estaciones de las dos fuentes?", "Identificador"),
    "dist_m": ("Distancia entre la coordenada CSDI y la de la lista HKO para la misma estación.", "metros", "(calculado)", "Vecino más cercano en EPSG:2326.",
               "¿Son confiables las coordenadas de las estaciones?", "Métrica"),
    "aqhi": ("Índice de Salud de la Calidad del Aire de la estación en la hora publicada.", "índice 1–10+", "AQHI", "Convertido a entero.",
             "¿Cómo está el aire ahora por zona? (Wiki 6, ambiente)", "Métrica"),
    "riesgo_salud": ("Categoría de riesgo para la salud asociada al AQHI.", "—", "Health Risk", "Copiado (Low, Moderate, High, Very High, Serious).",
                     "¿Hay riesgo para la salud por contaminación?", "Dimensión"),
    "publicado_hkt": ("Fecha y hora de publicación del dato AQHI.", "fecha-hora ISO 8601 (+08:00)", "pubDate", "Convertido a ISO 8601 con zona horaria de HK.",
                      "¿Qué tan reciente es la lectura?", "Metadato"),
    "ubicacion": ("Cómo se ubicó la estación en el territorio.", "—", "(no existe en la fuente)", "Constante: asignada al distrito por nombre, sin coordenada.",
                  "¿Se puede ubicar la estación con precisión?", "Metadato"),
    "estaciones_meteorologicas": ("Estaciones del Observatorio ubicadas en el distrito.", "estaciones", "(calculado)", "Conteo tras unión espacial.",
                                  "¿Qué tan monitoreado está el clima en cada distrito?", "Métrica"),
    "estaciones_calidad_aire": ("Estaciones de calidad del aire asignadas al distrito.", "estaciones", "(calculado)", "Conteo por distrito asignado.",
                                "¿Qué distritos tienen medición de calidad del aire?", "Métrica"),
    "aqhi_ultimo": ("AQHI promedio de las estaciones generales del distrito en la última captura.", "índice 1–10+", "(calculado de AQHI)",
                    "Promedio de estaciones tipo general; vacío si el distrito no tiene estación.", "¿Qué distritos tienen peor aire ahora?", "Métrica"),
    # Escucha
    "tema": ("Tema de la conversación pública al que pertenece el titular.", "—", "(rotulado)", "Asignado según la consulta de búsqueda.",
             "¿De qué se está hablando en Hong Kong?", "Dimensión"),
    "consulta": ("Consulta de búsqueda con la que se obtuvo el titular.", "—", "(consulta)", "Copiado.", "¿Cómo se capturó el titular? (reproducibilidad)", "Metadato"),
    "titular": ("Titular de la noticia.", "—", "title", "Copiado; sin texto del artículo.", "¿Qué dice la prensa?", "Texto"),
    "distritos_mencionados": ("Códigos de distrito mencionados en el titular o la URL, separados por '|'.", "—", "(calculado)",
                              "Búsqueda por diccionario de distritos y barrios (hkopendata) más lugares clave.", "¿Qué distritos aparecen en la conversación pública?", "Dimensión"),
    "puntaje_tono": ("Palabras positivas menos negativas en el titular.", "puntos", "(calculado)", "Léxico heurístico v1 sobre el titular en minúsculas.",
                     "¿La cobertura es favorable o desfavorable?", "Métrica"),
    "tono": ("Clasificación del tono del titular.", "—", "(calculado)", "positivo si puntaje > 0, negativo si < 0, neutral si = 0.",
             "¿Predomina la conversación positiva o negativa por tema?", "Dimensión"),
    "fecha_captura": ("Fecha en que se capturó el titular.", "fecha (AAAA-MM-DD)", "(no existe en la fuente)", "Constante de la captura.",
                      "¿De cuándo es esta foto de la conversación?", "Metadato"),
    "metodo_tono": ("Versión del método usado para calcular el tono.", "—", "(no existe en la fuente)", "Constante 'lexico_heuristico_v1'.",
                    "¿Con qué método se calculó el tono?", "Metadato"),
    "menciones": ("Número de titulares del tema.", "titulares", "(calculado)", "Conteo por tema.", "¿Qué temas tienen más cobertura?", "Métrica"),
    "tono_medio": ("Promedio del puntaje de tono de los titulares del tema.", "puntos", "(calculado)", "Media de puntaje_tono por tema.",
                   "¿Qué temas tienen la cobertura más favorable?", "Métrica"),
    "positivas": ("Titulares con tono positivo en el tema.", "titulares", "(calculado)", "Conteo de tono = positivo.", "¿Cuántas noticias favorables hay por tema?", "Métrica"),
    "negativas": ("Titulares con tono negativo en el tema.", "titulares", "(calculado)", "Conteo de tono = negativo.", "¿Cuántas noticias desfavorables hay por tema?", "Métrica"),
    "menciones_noticias": ("Número de titulares que mencionan el distrito.", "titulares", "(calculado)", "Conteo de códigos en distritos_mencionados.",
                           "¿Qué distritos concentran la atención mediática?", "Métrica"),
    "delitos_totales": ("Delitos totales registrados en el mes.", "casos", "Overall", "Renombrado.", "¿Cómo evoluciona la criminalidad mes a mes? (Wiki 4.1)", "Métrica"),
    "delitos_violentos": ("Delitos violentos registrados en el mes.", "casos", "Violent", "Renombrado.", "¿Cómo evolucionan los delitos violentos? (Wiki 4.2)", "Métrica"),
    "pct_violentos": ("Porcentaje de delitos que son violentos en el mes.", "%", "(calculado)", "100 × delitos_violentos / delitos_totales.",
                      "¿Está cambiando la composición del delito? (Wiki 4.2, 4.4)", "Métrica"),
    # Atlas de zonas
    "cluster": ("Número de grupo asignado por k-means.", "—", "(calculado)", "K-means (k=4, semilla 42) sobre 6 variables estandarizadas.",
                "¿Qué distritos se parecen entre sí?", "Dimensión"),
    "tipologia": ("Nombre descriptivo del tipo de zona.", "—", "(calculado)", "Nombre asignado según el perfil del centro del grupo (ingreso, vivienda pública, densidad).",
                  "¿Qué tipo de zona es cada distrito?", "Dimensión"),
    "indice_prosperidad": ("Índice 0–100 que combina ingreso 2025 (60 %) y % universitario (40 %).", "índice 0–100", "(calculado)",
                           "Combinación ponderada normalizada y reescalada min-max entre los 18 distritos.", "¿Qué distritos son más prósperos? (Wiki 1.6, 1.7)", "Métrica"),
    "indice_conectividad": ("Índice 0–100 que combina paradas por habitante y cercanía a urgencias.", "índice 0–100", "(calculado)",
                            "Suma normalizada de paradas_por_10k_hab y (1 − distancia a urgencias relativa), reescalada min-max.",
                            "¿Qué distritos están mejor conectados y servidos?", "Métrica"),
    "indice_presion_demografica": ("Índice 0–100 que combina densidad y % de 65+.", "índice 0–100", "(calculado)",
                                   "Suma normalizada de densidad y pct_65_mas, reescalada min-max.", "¿Dónde hay más presión sobre servicios por densidad y envejecimiento? (Wiki 1.2, 1.3)", "Métrica"),
    "rank_poblacion_2021": ("Posición del distrito por población (1 = mayor).", "posición 1–18", "(calculado)", "Ranking descendente, empates con el menor puesto.", "¿Cuál es el distrito más poblado?", "Métrica"),
    "rank_ingreso_mediano_hogar_hkd_2025": ("Posición del distrito por ingreso 2025 (1 = mayor).", "posición 1–18", "(calculado)", "Ranking descendente.", "¿Cuál es el distrito más rico?", "Métrica"),
    "rank_densidad_hab_km2": ("Posición del distrito por densidad (1 = mayor).", "posición 1–18", "(calculado)", "Ranking descendente.", "¿Cuál es el distrito más denso?", "Métrica"),
    "rank_pct_65_mas": ("Posición del distrito por % de 65+ (1 = mayor).", "posición 1–18", "(calculado)", "Ranking descendente.", "¿Cuál es el distrito más envejecido?", "Métrica"),
    "rank_paradas_por_10k_hab": ("Posición del distrito por paradas por habitante (1 = mayor).", "posición 1–18", "(calculado)", "Ranking descendente.", "¿Qué distrito tiene más transporte por habitante?", "Métrica"),
    "suma_rutas_en_paradas": ("Suma del número de rutas en todas las paradas de la circunscripción.", "rutas-parada", "(calculado)", "Suma de n_rutas por DCCA.",
                              "¿Qué circunscripciones tienen más servicio de transporte?", "Métrica"),
    "paradas_por_km2_poligono": ("Paradas por km² del polígono de la circunscripción (incluye mar).", "paradas/km²", "(calculado)", "paradas_transporte / area_km2_poligono.",
                                 "¿Dónde es más densa la red de transporte a escala fina?", "Métrica"),
    # Atlas distribuido
    "capa": ("Tipo de activo puntual.", "—", "(no existe en la fuente)", "Rotulado al unir capas (parada, hospital, estación).", "¿Qué tipo de activo es?", "Dimensión"),
    "id": ("Identificador del activo dentro de su capa.", "—", "id_parada / hospital_en / codigo_estacion:tipo", "Unificado en una sola columna.", "¿Qué activo es?", "Identificador"),
    "nombre": ("Nombre del activo.", "—", "nombre_en / hospital_en / estacion", "Unificado en una sola columna.", "¿Cómo se llama el activo?", "Dimensión"),
    "subtipo": ("Subtipo del activo (modos de transporte, tipo de estación, servicio).", "—", "modos / tipo / servicio", "Unificado en una sola columna.", "¿Qué subtipo de activo es?", "Dimensión"),
    "peso": ("Peso del punto para agregaciones (rutas en paradas, 1 en el resto).", "rutas o unidades", "(calculado)", "n_rutas para paradas; 1 para hospitales y estaciones.",
             "¿Cuánto pesa cada punto en la cobertura?", "Métrica"),
    "h3": ("Índice de la celda hexagonal H3 resolución 8 (~0,74 km²).", "—", "(calculado)", "h3.latlng_to_cell(lat, lon, 8).", "¿En qué celda de la malla cae cada activo?", "Identificador"),
    "estacion_meteorologica": ("Estaciones meteorológicas en la celda.", "estaciones", "(calculado)", "Conteo por celda H3.", "¿Dónde hay sensores climáticos?", "Métrica"),
    "hospital_urgencias": ("Hospitales con urgencias en la celda.", "hospitales", "(calculado)", "Conteo por celda H3.", "¿Dónde están las urgencias?", "Métrica"),
    "parada_transporte": ("Paradas de transporte en la celda.", "paradas", "(calculado)", "Conteo por celda H3.", "¿Dónde se concentra la red de transporte?", "Métrica"),
    "rutas_servidas": ("Suma de rutas en las paradas de la celda.", "rutas-parada", "(calculado)", "Suma de n_rutas por celda.", "¿Qué celdas tienen más servicio de transporte?", "Métrica"),
    "nivel_cobertura": ("Nivel de cobertura de transporte de la celda según su cuartil de paradas.", "—", "(calculado)", "Cuartiles del rango percentil de parada_transporte.",
                        "¿Qué zonas están sub-servidas en transporte?", "Dimensión"),
    # Correlaciones
    "variable": ("Variable de la fila en la matriz de correlación.", "—", "(calculado)", "Nombre del campo del atlas.", "¿Con qué se relaciona esta variable?", "Dimensión"),
    "var_x": ("Primera variable del par.", "—", "(calculado)", "Nombre del campo del atlas.", "¿Qué pares de indicadores se mueven juntos?", "Dimensión"),
    "var_y": ("Segunda variable del par.", "—", "(calculado)", "Nombre del campo del atlas.", "¿Qué pares de indicadores se mueven juntos?", "Dimensión"),
    "etiqueta_x": ("Etiqueta legible de la primera variable.", "—", "(calculado)", "Traducción para la interfaz.", "¿Cómo mostrar la variable al usuario?", "Dimensión"),
    "etiqueta_y": ("Etiqueta legible de la segunda variable.", "—", "(calculado)", "Traducción para la interfaz.", "¿Cómo mostrar la variable al usuario?", "Dimensión"),
    "pearson_r": ("Correlación lineal de Pearson entre las dos variables.", "coeficiente −1 a 1", "(calculado)", "scipy.stats.pearsonr sobre los 18 distritos.",
                  "¿Qué tan fuerte es la relación lineal?", "Métrica"),
    "pearson_p": ("Valor p de la correlación de Pearson.", "probabilidad 0–1", "(calculado)", "scipy.stats.pearsonr.", "¿La relación es estadísticamente significativa?", "Métrica"),
    "spearman_rho": ("Correlación de rangos de Spearman.", "coeficiente −1 a 1", "(calculado)", "scipy.stats.spearmanr.", "¿Hay relación monótona aunque no sea lineal?", "Métrica"),
    "spearman_p": ("Valor p de la correlación de Spearman.", "probabilidad 0–1", "(calculado)", "scipy.stats.spearmanr.", "¿La relación de rangos es significativa?", "Métrica"),
    "n": ("Número de observaciones usadas.", "distritos", "(calculado)", "Constante 18.", "¿Con cuántos datos se calculó?", "Metadato"),
    "significativo_5pct": ("Indica si el valor p de Pearson es menor que 0,05.", "booleano", "(calculado)", "pearson_p < 0,05.", "¿Se puede confiar en la relación?", "Métrica"),
}

CORR_VARS = ["densidad_hab_km2", "edad_mediana", "pct_65_mas", "pct_0_14", "tamano_medio_hogar", "pct_titulo_universitario_15_mas",
             "pct_nacida_en_hk", "pct_vivienda_publica_alquiler", "pct_vivienda_privada", "ingreso_mediano_hogar_hkd_2025",
             "ingreso_mediano_mensual_empleo_hkd_2021", "tasa_participacion_laboral_pct_2025", "var_ingreso_2016_2025_pct",
             "var_pob_2016_2025_pct", "paradas_por_10k_hab", "paradas_por_km2", "dist_media_hospital_km"]

# Tabla donde nace cada campo que el atlas copia
ORIGEN_ATLAS = {}
for t in ["geo/distritos.csv", "demografia/distritos_censo2021.csv", "economia/distritos_economia.csv",
          "infraestructura/distritos_infraestructura.csv", "sensores/distritos_sensores.csv", "escucha/menciones_por_distrito.csv"]:
    for c in pd.read_csv(CUR / t, nrows=1).columns:
        ORIGEN_ATLAS.setdefault(c, t)


def tipo_dato(s: pd.Series) -> str:
    if s.dtype == bool or set(s.dropna().astype(str).unique()) <= {"True", "False"} and s.notna().any():
        return "Booleano"
    if pd.api.types.is_integer_dtype(s):
        return "Entero"
    if pd.api.types.is_float_dtype(s):
        nn = s.dropna()
        return "Entero" if len(nn) and (nn == nn.round()).all() and s.isna().any() else "Decimal"
    return "Texto"


def rango(s: pd.Series, tipo: str, campo: str) -> str:
    nn = s.dropna()
    if not len(nn):
        return "—"
    if tipo == "Booleano":
        return "True / False"
    if tipo in ("Entero", "Decimal"):
        f = (lambda v: f"{v:,.0f}".replace(",", ".")) if tipo == "Entero" else (lambda v: f"{v:,.4g}")
        return f"{f(nn.min())} a {f(nn.max())}"
    u = nn.astype(str).unique()
    if campo in ("lat", "lon"):
        return ""
    if len(u) <= 12:
        return ", ".join(sorted(u))
    if campo == "codigo_dcca":
        return "Letra A–T + 2 dígitos (452 valores)"
    if campo == "h3":
        return "Índice H3 de 15 caracteres hexadecimales"
    return f"Texto libre ({len(u)} valores distintos)"


def ejemplo(s: pd.Series, tipo: str) -> str:
    nn = s.dropna()
    if not len(nn):
        return ""
    v = nn.iloc[0]
    if tipo == "Entero":
        return str(int(v))
    if tipo == "Decimal":
        return f"{v:.6g}"
    v = str(v)
    return v if len(v) <= 80 else v[:77] + "…"


def construir():
    filas = []
    for ruta in sorted(glob.glob(str(CUR / "**" / "*.csv"), recursive=True)):
        tabla = str(Path(ruta).relative_to(CUR))
        df = pd.read_csv(ruta)
        for campo in df.columns:
            s = df[campo]
            meta = M.get(campo)
            es_matriz = tabla.startswith("correlaciones/matriz") and campo in CORR_VARS
            es_centro = tabla.endswith("tipologias_centros_estandarizados.csv") and campo != "tipologia"
            if es_matriz:
                metodo = "Pearson" if "pearson" in tabla else "Spearman"
                meta = (f"Coeficiente de {metodo} entre la variable de la fila y {campo}.", "coeficiente −1 a 1", "(calculado)",
                        f"Matriz {metodo} sobre los 18 distritos del atlas.", f"¿Qué se relaciona con {campo}?", "Métrica")
            elif es_centro:
                base = M[campo]
                meta = (f"Valor estandarizado (z) del centro de cada tipología para: {base[0][0].lower() + base[0][1:]}", "desviaciones estándar",
                        "(calculado)", "Centro del k-means sobre variables estandarizadas (media 0, desvío 1).",
                        "¿Qué rasgo define a cada tipo de zona?", "Métrica")
            if meta is None:
                raise KeyError(f"Falta metadato para {tabla}:{campo}")
            sig, unidad, orig, trans, preg, rol = meta
            fuente = FUENTE_CAMPO.get(campo, FUENTE_TABLA[tabla])
            if tabla.startswith("atlas_zonas/atlas_distritos") and campo in ORIGEN_ATLAS:
                fuente = FUENTE_CAMPO.get(campo, FUENTE_TABLA[ORIGEN_ATLAS[campo]])
                trans = f"Copiado de curated/{ORIGEN_ATLAS[campo]} (unión por codigo). Origen: {trans}"
            if tabla.startswith("economia/distritos_economia") and campo in ("ingreso_mediano_hogar_hkd_2025", "tasa_participacion_laboral_pct_2025"):
                orig = orig.replace("ma_hh", "ma_hh").replace("t_lfpr", "t_lfpr")
            t = tipo_dato(s)
            vacio = "Sí" if s.isna().any() else "No"
            if campo in ("aqhi_ultimo", "hab_por_hospital_urgencias", "distritos_mencionados", "elevacion_m", "codigo", "codigo_dcca"):
                vacio = "Sí" if s.isna().any() or campo in ("aqhi_ultimo", "hab_por_hospital_urgencias", "distritos_mencionados") else vacio
            filas.append({
                "ID fuente": fuente,
                "Archivo o tabla en el lago": f"curated/{tabla}",
                "Nombre del campo en el lago": campo,
                "Nombre original en la fuente": orig,
                "Qué significa (en una frase)": sig,
                "Tipo de dato": t,
                "Unidad de medida": unidad,
                "Ejemplo de valor": ejemplo(s, t),
                "¿Puede venir vacío?": vacio,
                "Valores permitidos o rango": rango(s, t, campo) or ("−90 a 90" if campo == "lat" else "−180 a 180"),
                "Clasificación": f"Pública · {rol}",
                "Transformación que le hicieron": trans,
                "Pregunta del sistema que ayuda a responder": preg,
            })
    return pd.DataFrame(filas, columns=COLUMNAS)


if __name__ == "__main__":
    d = construir()
    out = ROOT / "catalogo" / "diccionario_datos.csv"
    d.to_csv(out, index=False, encoding="utf-8")
    print(len(d), "campos documentados ->", out)
