"""Regenera el Excel del grupo (plantilla del Taller de Datos) desde el repo, sin cifras copiadas a mano.

- 1. Fuentes      ← catalogo/fuentes.json (F01–F45, licencias literales en inglés)
- 2. Diccionario  ← catalogo/diccionario_web.csv (un campo por fila de cada archivo de public/data que lee la web)
- 3. Bitácora IA  ← se conservan las filas del grupo y se agregan las del pipeline y la visualización,
                    incluidas las que la IA hizo a medias o mal
- Resumen         ← mismas fórmulas, con los rangos ampliados al número real de filas

Uso: python pipeline/excel_grupo.py <excel_del_grupo.xlsx> <salida.xlsx>
"""
from __future__ import annotations

import json
import sys
from copy import copy
from datetime import date
from pathlib import Path

import openpyxl
import pandas as pd
from openpyxl.styles import PatternFill

ROOT = Path(__file__).resolve().parents[1]
GRIS = PatternFill("solid", fgColor="FFEDEDED")

# IDs del Excel anterior del pipeline → catálogo único
VIEJO = {f"F{i:02d}": f"F{i + 18:02d}" for i in range(1, 14)} | {
    "F14": "F10", "F15": "F34", "F16": "F32", "F17": "F33", "F28": "F45"} | {f"F{i}": f"F{i + 17}" for i in range(18, 28)}

BITACORA_PIPELINE = [
    # (encargo, respuesta, comprobación, resultado, ids viejos, aprendizaje)
    ("Leer la página de referencia Cerebro Lima para copiar su estructura", "No pudo abrirla: pide clave y bloquea acceso automatizado. Armó las pestañas a partir de los nombres de archivo que le dimos.", "Más tarde un integrante escribió la clave en el navegador y se revisó la página real: las pestañas coincidían, pero el diseño se había supuesto.", "Parcial", "F28", "Lo que la IA no puede abrir lo reconstruye por inferencia; hay que verificarlo con la fuente real."),
    ("Conseguir los límites de los 18 distritos", "Propuso geoBoundaries y la colección de mapas de Highcharts.", "geoBoundaries dio 404 y la ruta de Highcharts no existe.", "Inventado", "F20, F21", "Una URL plausible no es una URL que exista: se prueba antes de anotarla."),
    ("Mismo encargo: límites de distritos", "Encontró el GeoJSON de circunscripciones DCCA 2019 de la EAC (espejo en GitHub).", "Contamos 452 circunscripciones y 18 distritos; el espejo no tiene archivo LICENSE y los polígonos incluyen mar.", "Correcto", "F01", "El dato sirve, pero la licencia del espejo no está declarada: queda anotado como «no declara»."),
    ("Traer el Censo 2021 por distrito", "Primero el XLSX/ZIP oficial (no lo pudo leer), luego el servicio WFS del portal CSDI.", "Sumamos grupos de edad y tipos de vivienda: igualan la población total en los 18 distritos.", "Correcto", "F02, F18, F19", "El primer camino falló; el bueno salió de la ficha de DATA.GOV.HK."),
    ("Serie anual de ingreso y población por distrito", "Usó la Encuesta General de Hogares 2016–2025 vía CSDI.", "La población 2021 de la serie coincide con el censo; la edad mediana viene redondeada.", "Correcto", "F03", ""),
    ("Red de transporte público con coordenadas", "Encontró la compilación hk-bus-crawling (15.285 paradas).", "Licencia GPL-2.0 revisada; paradas dentro del territorio.", "Correcto", "F05", "Es una compilación de un tercero, no el dato oficial de cada operador."),
    ("Hospitales con urgencias", "Tomó nombres y coordenadas de un paquete npm (ane-hk).", "Son los 18 hospitales A&E, pero no contrastamos coordenadas con fuente oficial y falta el hospital nuevo de Kai Tak.", "Parcial", "F06", ""),
    ("Estaciones meteorológicas con coordenadas", "Leyó la tabla del Observatorio (86 estaciones).", "Cruce con la capa CSDI: 24 de 26 a menos de 1 m.", "Correcto", "F07, F08", ""),
    ("Calidad del aire actual", "Leyó el RSS del AQHI de 18 estaciones.", "La hora publicada parecía de casi un día antes; es una captura puntual, no una serie.", "Parcial", "F09", "Una captura no es un sensor: la página la rotula con su fecha."),
    ("Indicadores macro (PIB per cápita, inflación)", "La API del Banco Mundial no respondió; tomó las mismas series de FRED.", "La página de FRED dice «2010 U.S. Dollars» pero los valores parecen base 2015: la discrepancia no se resolvió.", "Parcial", "F10, F11, F12, F26", ""),
    ("Delitos y seguridad", "Trajo el CSV mensual de la Policía y el informe Police in Figures.", "La suma mensual 2024 (94.948) no cuadra con el anual (94.747).", "Parcial", "F13, F14", ""),
    ("Escucha: qué se dice de Hong Kong", "Hizo 8 búsquedas por tema, guardó 32 titulares y les calculó un tono por léxico.", "Leímos los titulares: el tono heurístico se equivoca en frases como «needs more…».", "Parcial", "F16, F17", "El tono es indicativo, no un modelo validado."),
    ("Comparar el lago con la wiki del grupo", "Hizo una tabla de cifras coincidentes y de cobertura por tema.", "Recalculamos delitos 2025 y población; coinciden.", "Correcto", "F02, F13, F14", ""),
]

BITACORA_WEB = [
    ("Llenar el diccionario del Excel con los campos de la wiki", "Generó 120 filas que apuntaban a archivos lago/poblacion.json, lago/vivienda.json… y copió las cifras a mano desde la wiki.",
     "El profesor notó que esos archivos no existen en el repo y que varias cifras no coinciden con las del lago (p. ej. 65+: 20,5 % en la wiki vs. 19,6 % en el censo).",
     "Incorrecto", "F01, F02, F06", "El diccionario ahora se genera solo, leyendo los archivos reales de public/data (pipeline/diccionario_web.py). Las diferencias quedaron explicadas en public/data/conciliacion.json."),
    ("Unificar los dos catálogos de fuentes", "Al principio dejó dos numeraciones que chocaban (F01–F18 del grupo y F01–F28 del pipeline).",
     "Se veía la misma etiqueta «F01» para dos fuentes distintas en la web y en el Excel.", "Parcial", "F01–F45",
     "Ahora hay un único catálogo F01–F45 (pipeline/catalogo_unico.py) y cada gráfico de la página muestra el archivo y el campo que lee."),
    ("Escribir la licencia de cada fuente", "En la primera versión parafraseó licencias en español («reutilización comercial y no comercial con atribución») y puso «CC BY-SA 4.0» a Wikipedia de memoria.",
     "Se abrieron las páginas de términos: 23 de 45 licencias se copiaron literalmente en inglés; las páginas que la herramienta no pudo abrir quedan como «not verified», sin inventar texto.",
     "Parcial", "F01–F45", "Una licencia resumida no es la licencia. Las «not verified» hay que copiarlas a mano desde el navegador."),
    ("Revisar si la Policía permite reutilizar sus cifras", "Había tratado los datos de la Policía como datos abiertos de DATA.GOV.HK.",
     "El aviso de police.gov.hk dice que la reproducción requiere autorización escrita; solo el CSV publicado en DATA.GOV.HK (F31) tiene la licencia abierta.",
     "Incorrecto", "F10, F31", "F10 queda marcada con licencia restrictiva en el catálogo y en la página."),
    ("Mostrar el desempleo en la página", "Usó una cifra de desempleo tomada de Moody's (tradingeconomics/economy.com).",
     "Los términos de Moody's restringen la reutilización.", "Incorrecto", "F34",
     "Se quitó de la página y del lago publicado; el desempleo oficial del C&SD queda como pendiente."),
    ("Mostrar el clima en la cabecera de la página", "Puso una consulta en vivo a la API del Observatorio desde el navegador.",
     "Eso rompe la regla de que todo lo que se ve sale de un archivo del repo con su fila en el diccionario.", "Parcial", "F25, F27",
     "Ahora la cabecera muestra el AQHI de la captura guardada (sensores.json) con su fecha."),
    ("Construir el mapa de la página", "La primera versión usó el mismo id «mapa» para la sección y el lienzo: MapLibre se montó sobre toda la sección.",
     "Se vio en las capturas de prueba; además las etiquetas de distritos pequeños se encimaban.", "Incorrecto", "F19, F22",
     "Se corrigió el id y se ocultan etiquetas de distritos chicos a poco zoom. Hay que mirar las capturas, no solo que no haya errores."),
    ("Mapa base de la página", "Usó el estilo positron de CARTO y escribió «© CARTO / OpenStreetMap» en el mapa.",
     "No se copió la licencia literal de CARTO al catálogo y en las pruebas locales el mapa base se bloqueó, así que no se verificó su carga.", "Parcial", "—",
     "Pendiente: agregar CARTO/OSM como fuente con su licencia literal o quitar el mapa base."),
    ("Decidir cómo mostrar la pobreza por distrito", "Propuso graficarla desde el agregador F16.",
     "El grupo decidió por escrito antes de graficar: hoy no se grafica; si entra será solo tasa de los 18 distritos, sin cruces con etnia, vivienda subdividida o edad, y sin ranking de «peor distrito».",
     "Parcial", "F16", "La decisión está en la sección Gente de la página (tarjeta «Pobreza por distrito: cómo la protegemos»)."),
    ("Cambiar la paleta a los colores de la bandera", "Rehízo la hoja de estilos en rojo #DE2910 y blanco; dejó los colores de series en azul, verde y violeta validados para daltonismo.",
     "Se probó en escritorio y móvil con capturas; aparecieron textos largos que desbordaban en móvil y se corrigieron.", "Correcto", "—", "El rojo se reserva para tipografía, fondos y el elemento destacado."),
]


def copiar_estilo(ws, fila_origen, fila_destino, ncols):
    for c in range(1, ncols + 1):
        o, d = ws.cell(fila_origen, c), ws.cell(fila_destino, c)
        d.font, d.fill, d.border, d.alignment, d.number_format = copy(o.font), copy(o.fill), copy(o.border), copy(o.alignment), o.number_format


def escribir(ws, inicio, filas, ncols, estilo_de):
    for i in range(inicio, max(ws.max_row, inicio + len(filas)) + 1):
        for c in range(1, ncols + 1):
            ws.cell(i, c).value = None
    for k, fila in enumerate(filas):
        r = inicio + k
        copiar_estilo(ws, estilo_de, r, ncols)
        for c, v in enumerate(fila, start=1):
            ws.cell(r, c).value = v
    return inicio + len(filas) - 1


def ampliar_validaciones(ws, primera, ultima):
    for dv in ws.data_validations.dataValidation:
        cols = {str(rng).split(":")[0].rstrip("0123456789") for rng in dv.sqref.ranges}
        dv.sqref = openpyxl.worksheet.cell_range.MultiCellRange(" ".join(f"{c}{primera}:{c}{ultima}" for c in cols))


def main(entrada, salida):
    wb = openpyxl.load_workbook(entrada)
    cat = json.loads((ROOT / "public" / "data" / "fuentes.json").read_text())["fuentes"]
    dic = pd.read_csv(ROOT / "catalogo" / "diccionario_web.csv").fillna("")

    # ---------------- 1. Fuentes ----------------
    ws = wb["1. Fuentes"]
    estilo = 5
    filas = []
    for f in cat:
        obs = [f["observaciones"]]
        if f.get("riesgo_licencia"):
            obs.append(f"Riesgo de licencia: {f['riesgo_licencia']}.")
        if f.get("url_licencia"):
            obs.append(f"Licencia leída en: {f['url_licencia']}")
        if f.get("archivos_lago"):
            obs.append("Archivos del lago: " + ", ".join(f"public/data/{a}" for a in f["archivos_lago"]))
        filas.append([f["id"], f["nombre"], f["entidad"], f["tipo_publicador"], f["url"], f["formato"], f["obtencion"], f["licencia"],
                      f["personas"], f["cobertura"], f["periodo"], f["frecuencia"], date.fromisoformat(f["fecha_probada"]), f["estado"],
                      f["como"], " ".join(o for o in obs if o)])
    # fila 4 = ejemplo de la plantilla (el resumen no la cuenta): se deja vacía y gris
    for c in range(1, 17):
        ws.cell(4, c).value = None
        ws.cell(4, c).fill = GRIS
    ws.cell(4, 2).value = "(fila de ejemplo de la plantilla: el resumen no la cuenta; las fuentes empiezan en la fila 5)"
    ult_f = escribir(ws, 5, filas, 16, estilo)
    for r in range(5, ult_f + 1):
        ws.cell(r, 13).number_format = "yyyy-mm-dd"
    ampliar_validaciones(ws, 4, ult_f)

    # ---------------- 2. Diccionario ----------------
    ws = wb["2. Diccionario"]
    for c in range(1, 14):
        ws.cell(4, c).value = None
        ws.cell(4, c).fill = GRIS
    ws.cell(4, 2).value = "(fila de ejemplo de la plantilla: vacía a propósito)"
    ult_d = escribir(ws, 5, dic.values.tolist(), 13, 5)
    ampliar_validaciones(ws, 5, ult_d)

    # ---------------- 3. Bitácora IA ----------------
    ws = wb["3. Bitácora IA"]
    grupo = []
    for r in ws.iter_rows(min_row=4, max_col=8, values_only=True):
        if r[2]:
            grupo.append(list(r))
    for i, g in enumerate(grupo, start=1):
        g[0] = i
    n = len(grupo)
    extra = []
    for enc, resp, comp, res, ids, apr in BITACORA_PIPELINE:
        nuevos = ", ".join(VIEJO.get(x.strip(), x.strip()) for x in ids.split(","))
        extra.append([None, "Claude (Anthropic)", enc, resp, comp, res, nuevos, apr])
    for enc, resp, comp, res, ids, apr in BITACORA_WEB:
        extra.append([None, "Claude (Anthropic)", enc, resp, comp, res, ids, apr])
    for k, e in enumerate(extra, start=n + 1):
        e[0] = k
    ult_b = escribir(ws, 4, grupo + extra, 8, 5)
    ampliar_validaciones(ws, 4, ult_b)

    # ---------------- Resumen ----------------
    ws = wb["Resumen"]
    for row in ws.iter_rows(min_row=4, max_col=2):
        v = row[1].value
        if isinstance(v, str) and v.startswith("="):
            v = v.replace("A5:A44", f"A5:A{ult_f}").replace("N5:N44", f"N5:N{ult_f}").replace("H5:H44", f"H5:H{ult_f}").replace("I5:I44", f"I5:I{ult_f}")
            v = v.replace("C5:C44", f"C5:C{ult_d}").replace("K5:K44", f"K5:K{ult_d}").replace("M5:M44", f"M5:M{ult_d}")
            v = v.replace("C4:C43", f"C4:C{ult_b}").replace("F4:F43", f"F4:F{ult_b}")
            row[1].value = v
    # Las fórmulas de «Fuentes» y «Diccionario» comparten letras de columna; se corrigen por hoja
    for row in ws.iter_rows(min_row=4, max_col=2):
        v = row[1].value
        if isinstance(v, str) and "'2. Diccionario'" in v:
            row[1].value = v.replace(f"C5:C{ult_f}", f"C5:C{ult_d}")

    # Instrucciones: dónde está la página y de dónde sale todo
    ws = wb["Instrucciones"]
    ws["A8"] = ("Página: public/index.html del mismo repositorio. Este Excel se genera con pipeline/excel_grupo.py desde "
                "catalogo/fuentes.json y public/data/*.json: ninguna cifra se copia a mano.")
    ws["A8"].font = copy(ws["A7"].font)

    wb.save(salida)
    print(f"Fuentes: {len(filas)} (filas 5–{ult_f}) · Diccionario: {len(dic)} (5–{ult_d}) · Bitácora: {len(grupo)} del grupo + {len(extra)} nuevas (4–{ult_b})")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
