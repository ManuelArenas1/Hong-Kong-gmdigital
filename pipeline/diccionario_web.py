"""Diccionario de datos de lo que la web lee: una fila por campo de cada archivo de public/data.

Recorre los JSON reales (no una lista escrita a mano), así que si un campo no está aquí la web no lo lee.
Cada fila lleva su ID de fuente F0x del catálogo único (catalogo/fuentes.json).

Uso:   python pipeline/diccionario_web.py
Salida: catalogo/diccionario_web.csv
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from catalogo_unico import ANTIGUOS, ARCHIVOS

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "public" / "data"

# Archivos que la web pide con fetch (app.js → ARCHIVOS; mapa.js → geo, circunscripciones, hexágonos, paradas)
WEB = ["panorama.json", "atlas_zonas.json", "demografia.json", "economia.json", "infraestructura.json", "sensores.json",
       "escucha.json", "correlaciones.json", "perfil_wiki.json", "fuentes.json", "conciliacion.json", "barrios.json",
       "geo.json", "geo_circunscripciones.json", "hex_h3_res8.geojson", "infraestructura_paradas.json"]

COLUMNAS = ["ID fuente", "Archivo o tabla en el lago", "Nombre del campo en el lago", "Nombre original en la fuente",
            "Qué significa (en una frase)", "Tipo de dato", "Unidad de medida", "Ejemplo de valor",
            "¿Puede venir vacío?", "Valores permitidos o rango", "Clasificación", "Transformación que le hicieron",
            "Pregunta del sistema que ayuda a responder"]

# Diccionarios cuyas claves son datos (no nombres de campo): se documentan como {clave}
MAPAS = {"correlaciones.json": {"variables", "pearson", "pearson.*", "spearman", "spearman.*"},
         "atlas_zonas.json": {"tipologias"},
         "barrios.json": {""}, "fuentes.json": {"archivos", "ids_antiguos"}}

# Campos que no tienen equivalente en el diccionario de curated/: significado escrito a mano
EXTRA: dict[str, tuple] = {
    # campo: (fuente o None=fuentes del archivo, original, significado, unidad, transformación, pregunta)
    "generado_utc": (None, "(pipeline)", "Momento en que el pipeline generó el archivo.", "fecha-hora UTC", "datetime.utcnow() al escribir el archivo.", "¿De cuándo son los datos que veo?"),
    "ciudad": (None, "(pipeline)", "Ciudad a la que corresponde el archivo.", "—", "Constante.", "¿De qué ciudad es el tablero?"),
    "unidad_territorial": (None, "(pipeline)", "Unidad territorial de las filas del archivo.", "—", "Constante.", "¿A qué escala se lee cada cifra?"),
    "catalogo": (None, "(pipeline)", "Ruta al catálogo de fuentes que documenta el archivo.", "—", "Constante.", "¿Dónde está la procedencia?"),
    "fuente": (None, "(pipeline)", "Entidad que publica la cifra de esa fila.", "—", "Texto copiado del catálogo.", "¿Quién dice esta cifra?"),
    "url": (None, "(pipeline)", "Dirección exacta de la que se tomó la cifra o la fuente.", "URL", "Ninguna.", "¿Dónde puedo comprobarla?"),
    "fuente_id": (None, "(pipeline)", "ID F0x de la fuente de la fila en el catálogo único.", "—", "Asignado por catalogo_unico.py.", "¿Qué fila de Fuentes respalda esto?"),
    "nota": (None, "(pipeline)", "Advertencia o aclaración sobre la cifra.", "—", "Texto escrito por el grupo.", "¿Qué cuidado hay que tener al leerla?"),
    "valor": (None, "(fuente)", "Valor numérico de la cifra.", "según «unidad»", "Ninguna (cifra publicada).", "¿Cuánto es?"),
    "unidad": (None, "(pipeline)", "Unidad del campo «valor».", "—", "Normalizada a español.", "¿En qué se mide?"),
    "periodo": (None, "(fuente)", "Periodo al que se refiere la cifra.", "año o mes", "Ninguna.", "¿De cuándo es la cifra?"),
    "indicador": (None, "(pipeline)", "Nombre corto del indicador.", "—", "Normalizado a snake_case.", "¿Qué se está midiendo?"),
}


# Metadatos por ruta exacta (campos calculados en build.py que no están en curated/)
P = "F20, F21, F22, F23, F28, F30, F32"
RUTAS = {
    "kpis.poblacion_censo_2021": ("F20", "Population (DC_21C)", "Población total del Censo 2021 (suma de los 18 distritos).", "personas", "Suma por distrito.", "¿Cuánta gente vive en Hong Kong?"),
    "kpis.poblacion_tierra_mitad_anio_2025": ("F21", "Land-based population (DC_GHS)", "Población terrestre a mitad de 2025 (suma de distritos).", "personas", "Suma por distrito del año 2025.", "¿Cuánta gente vive hoy?"),
    "kpis.area_terrestre_km2": ("F22", "Area (km²)", "Área terrestre oficial sumada de los 18 distritos.", "km²", "Suma de área por distrito.", "¿Qué tan grande es el territorio habitable?"),
    "kpis.densidad_media_hab_km2": ("F20, F22", "(calculado)", "Población del censo dividida por el área terrestre.", "hab/km²", "poblacion_censo_2021 / area_terrestre_km2.", "¿Qué tan denso es Hong Kong?"),
    "kpis.pct_65_mas_2021": ("F20", "(calculado)", "Porcentaje de la población con 65 años o más en 2021.", "%", "Suma 65+ / población × 100.", "¿Qué tan envejecida está la ciudad?"),
    "kpis.ingreso_mediano_hogar_rango_distritos_2025[]": ("F21", "Median monthly domestic household income", "Mínimo y máximo del ingreso mediano del hogar entre distritos en 2025.", "HK$/mes", "min() y max() sobre los 18 distritos.", "¿Qué tan desigual es el ingreso entre distritos?"),
    "kpis.pib_per_capita_usd_2025": ("F28", "NYGDPPCAPCDHKG", "PIB per cápita de Hong Kong en 2025.", "US$ corrientes", "Último año de la serie.", "¿Cómo va la economía?"),
    "kpis.inflacion_ipc_2025_pct": ("F30", "FPCPITOTLZGHKG", "Inflación anual del IPC en 2025.", "%", "Último año de la serie.", "¿Cómo cambian los precios?"),
    "kpis.paradas_transporte_publico": ("F23", "stopList", "Paradas de transporte público distintas.", "paradas", "Conteo de IDs únicos.", "¿Qué tan cubierta está la ciudad por transporte?"),
    "kpis.estaciones_mtr": ("F23", "stopList (co=mtr)", "Estaciones de la red MTR.", "estaciones", "Conteo de paradas del operador MTR.", "¿Qué tan cubierta está la ciudad por metro?"),
    "kpis.noticias_monitoreadas": ("F32", "(titulares)", "Titulares guardados en la escucha social.", "titulares", "Conteo.", "¿Cuánto se habló de la ciudad?"),
    "tipologias.{clave}": ("F20, F21, F22, F23, F24", "(calculado)", "Nombre interpretativo de cada grupo de k-means (clave = número de grupo).", "—", "KMeans(k=4, semilla 42) sobre variables estandarizadas; nombre puesto a mano.", "¿Qué distritos se parecen entre sí?"),
    "variables_tipologia[]": ("F20, F21, F22, F23", "(calculado)", "Variables usadas para agrupar los distritos.", "—", "Lista fija en build.py.", "¿Con qué criterio se agruparon?"),
    "nota_metodologica": ("F32", "(grupo)", "Cómo se calculó el tono de los titulares.", "—", "Texto escrito por el grupo.", "¿Qué tan confiable es el tono?"),
    "n_observaciones": ("F20, F21", "(calculado)", "Número de distritos usados en las correlaciones.", "distritos", "Casos completos.", "¿Con cuántos datos se calculó?"),
    "advertencia": ("F20, F21", "(grupo)", "Advertencia de lectura de las correlaciones.", "—", "Texto escrito por el grupo.", "¿Cómo no malinterpretarlas?"),
    "regiones.features[].properties.area_km2": ("F22", "Area (km²)", "Área terrestre oficial de la región (suma de sus distritos).", "km²", "dissolve por región y suma de áreas.", "¿Qué tan grande es cada región?"),
}
for k, n in [("0_14", "0 a 14"), ("15_24", "15 a 24"), ("25_44", "25 a 44"), ("45_64", "45 a 64"), ("65_mas", "65 o más")]:
    RUTAS[f"piramide_hk_2021.{k}"] = ("F20", f"Population aged {n.replace(' a ', '-').replace(' o más', '+')}", f"Personas de {n} años en Hong Kong (Censo 2021).", "personas", "Suma de los 18 distritos.", "¿Cómo es la estructura por edad?")
for k, v, d in [("mas_poblado", "F20", "Distrito con más población en 2021."), ("mas_denso", "F20, F22", "Distrito con mayor densidad."),
                ("mayor_ingreso", "F21", "Distrito con mayor ingreso mediano del hogar en 2025."), ("menor_ingreso", "F21", "Distrito con menor ingreso mediano del hogar en 2025."),
                ("mas_envejecido", "F20", "Distrito con mayor % de 65+."), ("mayor_crecimiento_poblacion_2016_2025", "F21", "Distrito que más creció en población entre 2016 y 2025.")]:
    RUTAS[f"destacados.{k}"] = (v, "(calculado)", d, "—", "idxmax/idxmin sobre los 18 distritos.", "¿Qué distrito destaca y en qué?")

GEO_ESTRUCTURA = re.compile(r"(^|\.)(type|name|crs\..*)$")


def tipo(vals):
    v = [x for x in vals if x is not None]
    if not v:
        return "Texto"
    if all(isinstance(x, bool) for x in v):
        return "Booleano"
    if all(isinstance(x, int) and not isinstance(x, bool) for x in v):
        return "Entero"
    if all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in v):
        return "Decimal"
    if all(isinstance(x, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}.*", x) for x in v):
        return "Fecha"
    if all(isinstance(x, (list, dict)) for x in v):
        return "Coordenada / geometría"
    return "Texto"


def rango(vals, t):
    v = [x for x in vals if x is not None]
    if not v:
        return "—"
    if t in ("Entero", "Decimal"):
        lo, hi = min(v), max(v)
        f = (lambda z: f"{z:,.0f}".replace(",", ".")) if t == "Entero" else (lambda z: f"{z:,.4g}".replace(",", " ").replace(".", ",").replace(" ", "."))
        return f"{f(lo)} a {f(hi)}"
    if t == "Booleano":
        return "true / false"
    if t == "Coordenada / geometría":
        return "GeoJSON WGS84 (EPSG:4326)"
    u = sorted({str(x) for x in v})
    if len(u) <= 8:
        return "; ".join(u)[:200]
    return f"{len(u)} valores distintos"


def ejemplo(vals):
    for x in vals:
        if x is not None and x != "":
            s = json.dumps(x, ensure_ascii=False) if isinstance(x, (list, dict)) else str(x)
            return s[:80] + ("…" if len(s) > 80 else "")
    return "—"


def recorrer(o, ruta, out, mapas):
    def es_mapa(r):
        return any(r == m or (m.endswith(".*") and r.rsplit(".", 1)[0] == m[:-2]) for m in mapas)
    if isinstance(o, dict):
        if es_mapa(ruta):
            pref = f"{ruta}." if ruta else ""
            for v in o.values():
                recorrer(v, f"{pref}{{clave}}", out, {m.replace(ruta, f'{pref}{{clave}}'.rstrip('.'), 1) if ruta else m for m in mapas} | mapas)
            return
        for k, v in o.items():
            recorrer(v, f"{ruta}.{k}" if ruta else k, out, mapas)
    elif isinstance(o, list):
        if o and all(isinstance(x, dict) for x in o):
            for x in o:
                recorrer(x, f"{ruta}[]", out, mapas)
        elif o and all(isinstance(x, list) for x in o) and ruta.endswith("coordinates"):
            out.setdefault(ruta, []).append(o)
        elif o and all(isinstance(x, list) for x in o):
            for x in o:
                recorrer(x, f"{ruta}[]", out, mapas)
        else:
            out.setdefault(f"{ruta}[]", []).extend(o)
            out.setdefault(f"{ruta}[]", [])
    else:
        out.setdefault(ruta, []).append(o)


def fids(texto, archivo):
    if not texto or texto == "derivado":
        return ", ".join(ARCHIVOS.get(archivo, [])) or "—"
    ids = []
    for t in re.split(r"[;,]\s*", str(texto)):
        ids += [x.strip() for x in ANTIGUOS.get(t.strip(), t.strip()).split(";")]
    return ", ".join(dict.fromkeys(i for i in ids if i))


def construir():
    viejo = pd.read_csv(ROOT / "catalogo" / "diccionario_datos.csv").fillna("")
    meta = {}
    for _, r in viejo.iterrows():
        meta.setdefault(r["Nombre del campo en el lago"], r)
    cat = json.loads((PUB / "fuentes.json").read_text())
    filas = []

    for archivo in WEB:
        datos = json.loads((PUB / archivo).read_text())
        a = f"public/data/{archivo}"

        # --- perfil_wiki: cada cifra de la wiki es un campo con su fuente F0x declarada ---
        if archivo == "perfil_wiki.json":
            for tema, campos in datos["temas"].items():
                for c, d in campos.items():
                    v = d.get("valor")
                    t = tipo([v])
                    filas.append([d.get("fuente", "").split(" ")[0] or "—", a, f"temas.{tema}.{c}.valor", "(cifra de informe, copiada a la wiki)",
                                  d.get("que_es", ""), t, d.get("unidad", ""), ejemplo([v]), "No", "valor único (cifra declarada)", "Pública",
                                  "Copiada a mano de la wiki del grupo; sello «declarado». Los campos que el lago ya calcula se retiraron (ver conciliacion.json).",
                                  d.get("pregunta", "")])
            for k in ("unidad", "que_es", "fuente", "pregunta"):
                filas.append(["F01–F15", a, f"temas.{{tema}}.{{campo}}.{k}", "(wiki del grupo)",
                              {"unidad": "Unidad de la cifra.", "que_es": "Qué significa la cifra, en una frase.",
                               "fuente": "ID F0x y nombre de la fuente de la cifra.", "pregunta": "Pregunta del sistema que responde."}[k],
                              "Texto", "—", "", "No", "texto libre", "Pública", "Copiado de la wiki.", "¿De dónde sale cada cifra declarada?"])
            for k in datos:
                if k == "temas":
                    continue
                out = {}
                recorrer(datos[k], k, out, set())
                for ruta, vals in out.items():
                    t = tipo(vals)
                    filas.append(["F13" if "parque" in ruta else "F01–F15", a, ruta, "(wiki del grupo)", "Metadato o tabla auxiliar del perfil de la wiki.",
                                  t, "—", ejemplo(vals), "Sí" if any(x is None for x in vals) else "No", rango(vals, t), "Pública",
                                  "Copiado de la wiki.", "¿Qué dice el informe oficial a escala de ciudad?"])
            continue

        # --- paradas: tabla columnar {columnas, filas} ---
        if archivo == "infraestructura_paradas.json":
            for i, col in enumerate(datos["columnas"]):
                vals = [f[i] for f in datos["filas"]]
                filas.append(fila(f"filas[][{i}] ({col})", col, vals, a, archivo, meta))
            continue

        out = {}
        recorrer(datos, "", out, MAPAS.get(archivo, set()))
        for ruta, vals in out.items():
            if GEO_ESTRUCTURA.search(ruta) and all(isinstance(x, str) for x in vals) and (
                    {"FeatureCollection", "Feature", "Polygon", "MultiPolygon", "name"} & set(vals) or "crs" in ruta or ruta.endswith(".name") or ruta == "name"):
                continue
            if ruta.endswith("geometry.coordinates"):
                fs = ", ".join(ARCHIVOS.get(archivo, [])[:2])
                filas.append([{"hex_h3_res8.geojson": "F23"}.get(archivo, "F19" if "dcca" in archivo or "circ" in archivo else fs), a, ruta.replace(".coordinates", ""),
                              "geometry", "Polígono del " + ("hexágono H3" if "hex" in archivo else "área (distrito, región o circunscripción)") + " en coordenadas lon/lat.",
                              "Coordenada / geometría", "grados WGS84", ejemplo(vals)[:40] + "…", "No", "Polygon / MultiPolygon, EPSG:4326", "Pública",
                              "Reproyectado de EPSG:2326 a 4326 y simplificado con geopandas." if "hex" not in archivo else "h3.cell_to_boundary.",
                              "¿Dónde queda cada zona en el mapa?"])
                continue
            hoja = re.sub(r"\[\]$", "", ruta.split(".")[-1]) or ruta
            filas.append(fila(ruta, hoja, vals, a, archivo, meta))

    df = pd.DataFrame(filas, columns=COLUMNAS)
    # F34 (Moody's) se descartó: los indicadores recientes que quedan son solo de la Policía (F10)
    rec = df["Nombre del campo en el lago"].str.contains("indicadores_recientes")
    df.loc[rec, "ID fuente"] = "F10"
    df["ID fuente"] = df["ID fuente"].str.replace(r",?\s*F34\b", "", regex=True).str.strip(", ")
    # Las fuentes del lago deben existir en el catálogo
    ids = {x["id"] for x in cat["fuentes"]}
    for v in df["ID fuente"]:
        for i in re.findall(r"F\d\d", v):
            assert i in ids, i
    df.to_csv(ROOT / "catalogo" / "diccionario_web.csv", index=False)
    return df


def fila(ruta, hoja, vals, a, archivo, meta):
    t = tipo(vals)
    vacio = "Sí" if any(x is None or x == "" for x in vals) else "No"
    if ruta in RUTAS:
        e = RUTAS[ruta]
        return [e[0], a, ruta, e[1], e[2], t, e[3], ejemplo(vals), vacio, rango(vals, t), "Pública", e[4], e[5]]
    r = meta.get(hoja)
    if archivo in ("fuentes.json",):
        return ["F01–F45", a, ruta, "(catálogo único)", f"Campo «{hoja}» de la ficha de cada fuente del catálogo.", t, "—", ejemplo(vals), vacio,
                rango(vals, t), "Pública", "Generado por pipeline/catalogo_unico.py; licencias copiadas literalmente en inglés.",
                "¿De dónde sale cada dato y bajo qué licencia?"]
    if archivo == "conciliacion.json":
        return ["F01–F06, F10, F20, F22", a, ruta, "(calculado)", f"Campo «{hoja}» de la comparación wiki (a mano) vs. lago (descargado).", t, "—",
                ejemplo(vals), vacio, rango(vals, t), "Pública", "pipeline/catalogo_unico.py → conciliacion().", "¿Por qué la página usa una cifra y no la otra?"]
    if archivo == "correlaciones.json" and "{clave}" in ruta:
        sig = {"variables": "Etiqueta legible de cada variable del explorador.", "pearson": "Coeficiente de Pearson entre dos variables (matriz 17×17).",
               "spearman": "Coeficiente de Spearman entre dos variables (matriz 17×17)."}[ruta.split(".")[0]]
        return [", ".join(ARCHIVOS[archivo]), a, ruta, "(calculado)", sig, t, "—" if t == "Texto" else "coeficiente", ejemplo(vals), vacio,
                "-1 a 1" if t != "Texto" else rango(vals, t), "Pública", "scipy.stats sobre los 18 distritos, casos completos.",
                "¿Qué variables se mueven juntas entre distritos?"]
    if archivo == "barrios.json":
        return ["F33", a, ruta, "name_en / name_zh", "Código de distrito o nombre chino del barrio (clave = nombre en inglés)." if hoja != "{clave}" else "Nombre del barrio en inglés.",
                "Código" if hoja == "codigo" else "Texto", "—", ejemplo(vals), vacio, rango(vals, t), "Pública",
                "Lugares de hkopendata agrupados por distrito.", "¿En qué distrito queda el barrio que busco?"]
    if r is not None:
        return [fids(r["ID fuente"], archivo), a, ruta, r["Nombre original en la fuente"], r["Qué significa (en una frase)"], t,
                r["Unidad de medida"] or "—", ejemplo(vals), vacio, rango(vals, t), r["Clasificación"].split(" · ")[0] or "Pública",
                r["Transformación que le hicieron"], r["Pregunta del sistema que ayuda a responder"]]
    e = EXTRA.get(hoja)
    if e:
        return [e[0] or (", ".join(ARCHIVOS.get(archivo, [])) or "—"), a, ruta, e[1], e[2], t, e[3], ejemplo(vals), vacio, rango(vals, t),
                "Pública", e[4], e[5]]
    return [", ".join(ARCHIVOS.get(archivo, [])) or "—", a, ruta, "?", "", t, "—", ejemplo(vals), vacio, rango(vals, t), "Pública", "", ""]


if __name__ == "__main__":
    df = construir()
    falt = df[df["Qué significa (en una frase)"] == ""]
    print(len(df), "campos;", len(falt), "sin significado")
    print(df.groupby("Archivo o tabla en el lago").size().to_string())
    for _, r in falt.iterrows():
        print("  ?", r["Archivo o tabla en el lago"].split("/")[-1], r["Nombre del campo en el lago"], "|", r["Ejemplo de valor"])
