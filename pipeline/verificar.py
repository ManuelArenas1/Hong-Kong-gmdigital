"""Verificación del lago: si algo falla, no se publica.

Uso:  python pipeline/verificar.py [raiz_del_repo]
Sale con código 1 si alguna comprobación falla (sirve como paso previo al despliegue).

Comprueba que lo publicado (public/data) coincide con lo que dicen el catálogo y el diccionario, que no hay
datos de personas a la vista, que ninguna zona publica población por debajo del umbral decidido, que no hay
llaves ni secretos en el repositorio y que el texto libre del lago no trae instrucciones escondidas.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
PUB = ROOT / "public" / "data"

# Decisión de protección: la unidad más fina con población es el distrito (el menor tiene 166.695 habitantes).
# Ninguna tabla publicada puede traer población de una zona con menos habitantes que este umbral.
UMBRAL_POBLACION = 100_000

# Claves que delatarían datos de personas (nombres propios, contacto, documentos, fechas de nacimiento).
CLAVES_PERSONALES = re.compile(r"(^|_)(email|correo|telefono|phone|direccion|address|dni|cedula|passport|pasaporte|"
                               r"apellido|surname|fecha_nacimiento|birth|nombre_persona|full_?name)($|_)", re.I)
# Claves que indicarían población por zonas más finas que el distrito.
CLAVES_POBLACION = re.compile(r"(poblacion|habitantes|hogares|^pob_|_pob_)", re.I)

SECRETOS = re.compile(r"(api[_-]?key|secret|passwd|password|access[_-]?token)\s*[:=]\s*['\"][^'\"\s]{8,}['\"]|"
                      r"BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{30,}", re.I)
URL_CON_LLAVE = re.compile(r"https?://[^\s\"'<>)]*[?&](key|apikey|api_key|access_token|token)=", re.I)
INSTRUCCIONES = re.compile(r"ignore (all |any |the )?(previous|above|prior)|disregard (all |the )?(previous|above)|system prompt|"
                           r"you are (now )?an? (ai|assistant)|as an ai\b|<\s*script|<\s*iframe|javascript:|"
                           r"ignora (las|todas las) instrucciones|instrucciones anteriores|[​‌‍⁠﻿]", re.I)

fallos: list[str] = []


def comprobar(nombre: str, ok: bool, detalle: str = "") -> None:
    print(("  OK     " if ok else "  FALLA  ") + nombre + (f" — {detalle}" if detalle else ""))
    if not ok:
        fallos.append(nombre)


def cargar(ruta: Path):
    return json.loads(ruta.read_text(encoding="utf-8"))


def claves(o, acum=None):
    acum = set() if acum is None else acum
    if isinstance(o, dict):
        for k, v in o.items():
            acum.add(str(k))
            claves(v, acum)
    elif isinstance(o, list):
        for v in o[:200]:
            claves(v, acum)
    return acum


def archivos_texto():
    for carpeta in ("pipeline", "public", "catalogo", "raw", "curated"):
        for p in (ROOT / carpeta).rglob("*"):
            if p.is_file() and p.suffix in {".py", ".js", ".html", ".css", ".json", ".geojson", ".csv", ".md"} and "__pycache__" not in p.parts:
                yield p
    for p in ROOT.glob("*.md"):
        yield p


def main() -> int:
    print(f"Verificando {ROOT}")

    # 1. Lo publicado existe y se lee
    manifest = cargar(PUB / "manifest.json")
    faltan, rotos = [], []
    for a in manifest["archivos"] + ["hex_h3_res8.geojson"]:
        try:
            cargar(PUB / a)
        except FileNotFoundError:
            faltan.append(a)
        except ValueError:
            rotos.append(a)
    comprobar("Cada archivo del manifest existe y es JSON válido", not faltan and not rotos, f"faltan {faltan} · rotos {rotos}" if faltan or rotos else f"{len(manifest['archivos']) + 1} archivos")

    # 2. Catálogo único F01–F45
    fuentes = cargar(PUB / "fuentes.json")["fuentes"]
    ids = [f["id"] for f in fuentes]
    comprobar("Catálogo con F01–F45 completas y sin repetir", ids == [f"F{i:02d}" for i in range(1, 46)], f"{len(ids)} fuentes")
    integradas = [f for f in fuentes if f["estado"] == "Integrada al lago"]
    sin_dato = []
    for f in integradas:
        try:
            ok_fecha = bool(date.fromisoformat(f["fecha_probada"]))
        except (ValueError, TypeError):
            ok_fecha = False
        if not (f["licencia"].strip() and ok_fecha and f["url"].strip() and f.get("archivos_lago")):
            sin_dato.append(f["id"])
    comprobar("Toda fuente integrada tiene licencia, URL, fecha de prueba real y archivos del lago", not sin_dato, f"incompletas: {sin_dato}" if sin_dato else f"{len(integradas)} integradas")
    inexistentes = [(f["id"], a) for f in integradas for a in f.get("archivos_lago", []) if not (PUB / a).exists()]
    comprobar("Los archivos del lago que cita cada fuente existen en public/data", not inexistentes, str(inexistentes[:3]) if inexistentes else "")
    futuras = [f["id"] for f in fuentes if f["fecha_probada"] > date.today().isoformat()]
    comprobar("Ninguna fecha de prueba está en el futuro", not futuras, str(futuras))

    # 3. Diccionario: solo lo que está en el lago, y todo lo publicado está en el diccionario
    with open(ROOT / "catalogo" / "diccionario_web.csv", encoding="utf-8", newline="") as fh:
        filas = list(csv.DictReader(fh))
    citados = {r["Archivo o tabla en el lago"] for r in filas}
    no_existen = sorted(a for a in citados if not (ROOT / a).exists())
    comprobar("Todo archivo que cita el diccionario existe", not no_existen, str(no_existen))
    publicados = {f"public/data/{p.name}" for p in PUB.iterdir() if p.is_file()} - {"public/data/manifest.json"}
    comprobar("Todo archivo publicado tiene filas en el diccionario", not (publicados - citados), str(sorted(publicados - citados)))
    estado = {f["id"]: f["estado"] for f in fuentes}
    ajenas = sorted({i for r in filas for i in re.findall(r"F\d\d", r["ID fuente"].replace("F01–F45", "")) if estado.get(i) != "Integrada al lago"})
    comprobar("Todo F0x del diccionario es una fuente integrada", not ajenas, str(ajenas))
    vacias = [r["Nombre del campo en el lago"] for r in filas if not r["Qué significa (en una frase)"].strip()]
    comprobar("Todo campo del diccionario tiene significado", not vacias, f"{len(filas)} campos")

    # 4. El Excel coincide con el lago
    try:
        import openpyxl
        wb = openpyxl.load_workbook(ROOT / "catalogo" / "Diccionario_de_datos_TallerDatos_HongKong.xlsx")
        n_dic = sum(1 for r in wb["2. Diccionario"].iter_rows(min_row=5, values_only=True) if r[2])
        n_fue = sum(1 for r in wb["1. Fuentes"].iter_rows(min_row=5, values_only=True) if r[0])
        comprobar("El Excel tiene los mismos campos y fuentes que el lago", n_dic == len(filas) and n_fue == len(fuentes), f"{n_dic} campos, {n_fue} fuentes")
    except ImportError:
        comprobar("El Excel tiene los mismos campos y fuentes que el lago (falta openpyxl)", False)

    # 5. Protección: sin personas, sin población por debajo del distrito
    personales = sorted({k for p in PUB.glob("*.json") for k in claves(cargar(p)) if CLAVES_PERSONALES.search(k)})
    comprobar("Ninguna clave publicada delata datos de personas", not personales, str(personales))
    dist = cargar(PUB / "demografia.json")["distritos"]
    dist = dist if isinstance(dist, list) else list(dist.values())
    minimo = min(d["poblacion_2021"] for d in dist)
    comprobar(f"Ningún distrito publicado tiene menos de {UMBRAL_POBLACION:,} habitantes".replace(",", "."), minimo >= UMBRAL_POBLACION, f"el menor tiene {minimo:,}".replace(",", "."))
    finas = {"geo_circunscripciones.json": cargar(PUB / "geo_circunscripciones.json"), "atlas_zonas.json:circunscripciones": cargar(PUB / "atlas_zonas.json")["circunscripciones"],
             "hex_h3_res8.geojson": cargar(PUB / "hex_h3_res8.geojson"), "atlas_distribuidos.json:hexagonos": cargar(PUB / "atlas_distribuidos.json")["hexagonos"]}
    con_poblacion = sorted(n for n, o in finas.items() if any(CLAVES_POBLACION.search(k) for k in claves(o)))
    comprobar("Circunscripciones y malla H3 no publican población ni hogares", not con_poblacion, str(con_poblacion))

    # 6. Secretos, llaves de pago y texto con instrucciones escondidas
    secretos, llaves, instrucciones = [], [], []
    for p in archivos_texto():
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = str(p.relative_to(ROOT))
        if SECRETOS.search(t):
            secretos.append(rel)
        if p.suffix in {".html", ".js", ".py"} and URL_CON_LLAVE.search(t):
            llaves.append(rel)
        if p.suffix in {".csv", ".json", ".geojson"} and INSTRUCCIONES.search(t):  # solo datos: el código sí lleva <script>
            instrucciones.append(rel)
    comprobar("No hay claves ni secretos en el repositorio", not secretos, str(secretos))
    comprobar("Ninguna URL de la página lleva llave o token", not llaves, str(llaves))
    comprobar("El texto libre del lago no trae instrucciones escondidas (barrido por patrones, no prueba absoluta)", not instrucciones, str(instrucciones))

    print()
    if fallos:
        print(f"{len(fallos)} comprobación(es) fallaron: no se publica.")
        return 1
    print("Todas las comprobaciones pasaron.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
