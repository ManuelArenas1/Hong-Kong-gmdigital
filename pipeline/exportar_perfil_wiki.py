"""Exporta el perfil de ciudad de la wiki (120 campos del diccionario del grupo) a public/data/perfil_wiki.json.

Fuentes F01–F18 = hoja «1. Fuentes» del archivo del grupo (Diccionario_de_datos_TallerDatos).
Uso: python pipeline/exportar_perfil_wiki.py
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import PUBLIC, escribir_json  # noqa: E402
from llenar_diccionario_wiki import CAMPOS  # noqa: E402

# Hoja «1. Fuentes» del grupo (copiada del archivo compartido por el equipo, 2026-10-06)
FUENTES_GRUPO = {
    "F01": ("Estimación de población a mediados de 2026", "Census and Statistics Department (C&SD)", "https://www.censtatd.gov.hk/en/scode150.html", "Integrada al lago"),
    "F02": ("Proyecciones de población 2022–2046", "Census and Statistics Department (C&SD)", "https://www.censtatd.gov.hk/en/EIndexbySubject.html?pcode=B1120015&scode=190", "Integrada al lago"),
    "F03": ("Características educativas de la población (Censo 2021)", "Census and Statistics Department (C&SD)", "https://www.census2021.gov.hk/doc/pub/21C_Articles_Educational.pdf", "Integrada al lago"),
    "F04": ("Tasa bruta de natalidad y mortalidad 1981–2025", "Centre for Health Protection, Department of Health", "https://www.chp.gov.hk/en/statistics/data/10/27/112.html", "Integrada al lago"),
    "F05": ("Hong Kong Property Review 2026", "Rating and Valuation Department (RVD)", "https://www.rvd.gov.hk/en/publications/property_market_statistics.html", "Integrada al lago"),
    "F06": ("Housing in Figures 2025", "Housing Bureau / Hong Kong Housing Authority", "https://www.hb.gov.hk/eng/publications/housing/HIF2025.pdf", "Integrada al lago"),
    "F07": ("Land and Housing 2025", "Our Hong Kong Foundation (OHKF)", "https://s3.ourhkfoundation.org.hk/s3fs-public/2025-04/Land-and-Housing-2025_full-report_EN.pdf", "Candidata"),
    "F08": ("The 2026-27 Budget", "Financial Secretary — Gobierno de la RAE de HK", "https://www.budget.gov.hk/2026/eng/budget54.html", "Integrada al lago"),
    "F09": ("The Four Key Industries in the Hong Kong Economy", "Census and Statistics Department (C&SD)", "https://www.censtatd.gov.hk/en/scode80.html?productCode=FA100099", "Integrada al lago"),
    "F10": ("Situación de ley y orden 2025", "Hong Kong Police Force (HKPF)", "https://www.police.gov.hk/ppp_en/09_statistics/csd.html", "Integrada al lago"),
    "F11": ("Corruption Perceptions Index 2025", "ICAC HK / Transparency International", "https://www.icac.org.hk/en/intl-persp/ranking-and-research/corruption-perceptions-index/index.html", "Integrada al lago"),
    "F12": ("Hong Kong: The Facts – Tourism", "gov.hk (datos de HKTB y C&SD)", "https://www.gov.hk/en/about/abouthk/factsheets/docs/tourism.pdf", "Integrada al lago"),
    "F13": ("Hong Kong: The Facts – Country Parks and Special Areas", "AFCD", "https://www.afcd.gov.hk/english/country/cou_lea/the_facts.html", "Integrada al lago"),
    "F14": ("Hong Kong: The Facts – Water Supplies", "Water Supplies Department (WSD)", "https://www.wsd.gov.hk/en/publications-and-statistics/pr-publications/the-facts/index.html", "Integrada al lago"),
    "F15": ("State of Hong Kong Biodiversity 2025", "WWF-Hong Kong", "https://www.wwf.org.hk/en/biodiversity/", "Integrada al lago"),
    "F16": ("Pobreza por distrito y demografía", "Social Indicators of Hong Kong", "https://socialindicators.org.hk/how-many-hong-kong-residents-live-in-poverty-breaking-down-the-latest-statistics-by-district-and-demographics/", "Candidata"),
    "F17": ("Serie histórica de fecundidad (TFR)", "Macrotrends", "https://www.macrotrends.net/global-metrics/countries/hkg/hong-kong/fertility-rate", "Descartada"),
    "F18": ("Esperanza de vida por distrito (2016)", "IPC / International Population Conference", "http://ipc2025.popconf.org/uploads/250834", "Candidata"),
}


def main():
    temas = defaultdict(dict)
    parques = defaultdict(dict)
    for fid, archivo, campo, _orig, sig, _tipo, unidad, ej, _vac, _rango, _trans, preg in CAMPOS:
        tema = Path(archivo).stem
        if tema == "suelo_parques":
            continue
        temas[tema][campo] = {"valor": ej, "unidad": unidad, "que_es": sig, "fuente": fid, "pregunta": preg}
    # Tabla de parques naturales (wiki 5.7): seis filas
    parques_tabla = [
        {"puesto": 1, "nombre_parque": "Lantau South", "area_ha": 5646},
        {"puesto": 2, "nombre_parque": "Tai Lam", "area_ha": 5412},
        {"puesto": 3, "nombre_parque": "Plover Cove", "area_ha": 4600},
        {"puesto": 4, "nombre_parque": "Sai Kung East", "area_ha": 4494},
        {"puesto": 5, "nombre_parque": "Pat Sin Leng", "area_ha": 3125},
        {"puesto": 6, "nombre_parque": "Sai Kung West", "area_ha": 3000},
    ]
    escribir_json(PUBLIC / "perfil_wiki.json", {
        "meta": {"origen": "Wiki del grupo «Perfil de la ciudad de Hong Kong» (compilada sep. 2026) + hoja Fuentes F01–F18",
                 "nota": "Cifras agregadas de ciudad; no tienen desagregación por distrito."},
        "temas": temas,
        "suelo_parques": parques_tabla,
        "fuentes": {k: {"nombre": n, "entidad": e, "url": u, "estado": s} for k, (n, e, u, s) in FUENTES_GRUPO.items()},
    })
    print("perfil_wiki.json:", {k: len(v) for k, v in temas.items()})


if __name__ == "__main__":
    main()


def copiar_auxiliares():
    """Copia a public/data los archivos que la web necesita y que viven en curated/ o catalogo/."""
    import json
    import shutil
    root = Path(__file__).resolve().parents[1]
    shutil.copy(root / "curated" / "atlas_distribuidos" / "hex_h3_res8.geojson", PUBLIC / "hex_h3_res8.geojson")
    cat = json.loads((root / "catalogo" / "catalogo.json").read_text())
    escribir_json(PUBLIC / "catalogo.json", {"fuentes": cat["fuentes"], "fecha_captura": cat.get("fecha_captura")})


if __name__ == "__main__":
    copiar_auxiliares()


def exportar_barrios():
    """Barrio -> código de distrito (diccionario hkopendata, MIT) para el buscador de la web."""
    import json
    from common import EN_A_CODIGO
    root = Path(__file__).resolve().parents[1]
    loc = json.loads((root / "raw" / "referencia" / "hkopendata_hk-location.json").read_text())
    barrios = {}
    for d in loc["district"]:
        cod = EN_A_CODIGO.get(d["name"]["en"].replace(" District", "").replace("&", "and"))
        if not cod:
            continue
        for l in d["location"]:
            for x in (l if isinstance(l, list) else [l]):
                barrios[x["en"]] = {"codigo": cod, "zh": x.get("tc", "")}
    escribir_json(PUBLIC / "barrios.json", barrios)
    print("barrios:", len(barrios))


if __name__ == "__main__":
    exportar_barrios()
