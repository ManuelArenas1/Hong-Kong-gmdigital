"""Construye el data lake de Hong Kong: raw -> curated -> public/data.

Uso:
    python pipeline/build.py

Capas:
    raw/       datos tal como se obtuvieron de la fuente (bronce)
    curated/   tablas y capas limpias, tipadas y unificadas por distrito (plata)
    public/data/  JSON listos para el front, uno por pestaña (oro)
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone

import geopandas as gpd
import h3
import numpy as np
import pandas as pd
from scipy import stats
from shapely.geometry import Point, mapping
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from common import (
    CRS_METRICO,
    CRS_WGS84,
    CURATED,
    DIST_DF,
    EN_A_CODIGO,
    PUBLIC,
    RAW,
    asegurar_dir,
    dms_a_decimal,
    escribir_csv,
    escribir_json,
    registros,
)

GENERADO = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# GEO
# ---------------------------------------------------------------------------
def construir_geo():
    dcca = gpd.read_file(RAW / "geo" / "eac_dcca_2019.geojson").set_crs(CRS_WGS84, allow_override=True)
    dcca = dcca.rename(columns={"CACODE": "codigo_dcca", "ENAME": "nombre_en", "CNAME": "nombre_zh"})
    dcca["codigo"] = dcca.codigo_dcca.str[0]
    dcca = dcca.merge(DIST_DF[["codigo", "distrito_en", "distrito_es", "region"]], on="codigo", how="left")
    assert dcca.distrito_en.notna().all(), "Hay circunscripciones sin distrito"

    m = dcca.to_crs(CRS_METRICO)
    m["geometry"] = m.buffer(0)
    dcca["area_km2_poligono"] = (m.area / 1e6).round(4)  # los límites de la EAC incluyen superficie marina

    distritos_m = m.dissolve(by="codigo", as_index=False)[["codigo", "geometry"]]
    distritos_m["area_km2_poligono_incluye_mar"] = (distritos_m.area / 1e6).round(3)
    c = distritos_m.geometry.representative_point().to_crs(CRS_WGS84)
    distritos_m["centro_lon"] = c.x.round(6)
    distritos_m["centro_lat"] = c.y.round(6)
    distritos = distritos_m.to_crs(CRS_WGS84).merge(DIST_DF, on="codigo")

    wiki = pd.read_csv(RAW / "referencia" / "wikipedia_distritos_area.csv")
    wiki["codigo"] = wiki.district.map(EN_A_CODIGO)
    distritos = distritos.merge(wiki[["codigo", "area_km2"]].rename(columns={"area_km2": "area_km2_oficial"}), on="codigo")
    distritos["n_circunscripciones"] = distritos.codigo.map(dcca.codigo.value_counts())

    regiones = distritos.to_crs(CRS_METRICO).dissolve(by="region", as_index=False)[["region", "geometry"]]
    regiones["area_km2"] = (regiones.area / 1e6).round(2)
    regiones = regiones.to_crs(CRS_WGS84)

    # Versiones simplificadas para la web (tolerancia en metros, en CRS métrico)
    def simplificar(gdf, tol):
        g = gdf.to_crs(CRS_METRICO).copy()
        g["geometry"] = g.geometry.simplify(tol, preserve_topology=True)
        return g.to_crs(CRS_WGS84)

    out = asegurar_dir(CURATED / "geo")
    cols_d = ["codigo", "distrito_en", "distrito_zh", "distrito_es", "region", "area_km2_oficial",
              "area_km2_poligono_incluye_mar", "centro_lat", "centro_lon", "n_circunscripciones", "geometry"]
    distritos = distritos[cols_d]
    distritos.to_file(out / "distritos.geojson", driver="GeoJSON")
    simplificar(distritos, 40).to_file(out / "distritos_web.geojson", driver="GeoJSON")
    cols_c = ["codigo_dcca", "nombre_en", "nombre_zh", "codigo", "distrito_en", "distrito_es", "region", "area_km2_poligono", "geometry"]
    dcca = dcca[cols_c]
    simplificar(dcca, 15).to_file(out / "circunscripciones_dcca_2019.geojson", driver="GeoJSON")
    regiones.to_file(out / "regiones.geojson", driver="GeoJSON")
    escribir_csv(out / "distritos.csv", pd.DataFrame(distritos.drop(columns="geometry")))
    escribir_csv(out / "circunscripciones_dcca_2019.csv", pd.DataFrame(dcca.drop(columns="geometry")))
    return distritos, dcca


def asignar_distrito(df: pd.DataFrame, distritos: gpd.GeoDataFrame, dcca: gpd.GeoDataFrame,
                     lat="lat", lon="lon") -> gpd.GeoDataFrame:
    """Añade codigo de distrito y de circunscripción por unión espacial (punto en polígono;
    si cae en el mar, se asigna el polígono más cercano dentro de 1 km)."""
    g = gpd.GeoDataFrame(df.copy(), geometry=gpd.points_from_xy(df[lon], df[lat]), crs=CRS_WGS84).to_crs(CRS_METRICO)
    zonas = dcca[["codigo_dcca", "codigo", "geometry"]].to_crs(CRS_METRICO)
    j = gpd.sjoin_nearest(g, zonas, how="left", max_distance=1000, distance_col="_dist_m")
    j = j[~j.index.duplicated(keep="first")]
    j = j.drop(columns=["index_right"]).to_crs(CRS_WGS84)
    j["ubicacion_en_tierra"] = j["_dist_m"].fillna(1e9) == 0
    return j.drop(columns=["_dist_m"])


# ---------------------------------------------------------------------------
# DEMOGRAFÍA
# ---------------------------------------------------------------------------
def construir_demografia(distritos):
    a = pd.read_csv(RAW / "demografia" / "csdi_census2021_dc_basico.csv")
    c = pd.read_csv(RAW / "demografia" / "csdi_census2021_dc_edad_educacion.csv")
    d = pd.read_csv(RAW / "demografia" / "csdi_census2021_dc_vivienda_origen.csv")
    df = a.merge(c.drop(columns=["GmlId", "OBJECTID"]), on="dc_eng").merge(d.drop(columns=["GmlId", "OBJECTID"]), on="dc_eng")
    df["codigo"] = df.dc_eng.map(EN_A_CODIGO)
    assert (df.dc_class == df.codigo).all()

    pob = df.t_pop
    out = pd.DataFrame({
        "codigo": df.codigo,
        "poblacion_2021": pob,
        "hogares_2021": df.dh,
        "tamano_medio_hogar": df.adhz,
        "edad_mediana": df.t_ma,
        "razon_sexos_hombres_por_1000_mujeres": df.sr,
        "pob_0_14": df.age_1, "pob_15_24": df.age_2, "pob_25_44": df.age_3, "pob_45_64": df.age_4, "pob_65_mas": df.age_5,
        "pct_0_14": (100 * df.age_1 / pob).round(2),
        "pct_15_24": (100 * df.age_2 / pob).round(2),
        "pct_25_44": (100 * df.age_3 / pob).round(2),
        "pct_45_64": (100 * df.age_4 / pob).round(2),
        "pct_65_mas": (100 * df.age_5 / pob).round(2),
        "indice_envejecimiento": (100 * df.age_5 / df.age_1).round(1),
        "pob_15_mas_con_titulo_universitario": df.edu_deg,
        "pct_titulo_universitario_15_mas": (100 * df.edu_deg / (pob - df.age_1)).round(2),
        "pob_nacida_en_hk": df.born_hk,
        "pct_nacida_en_hk": (100 * df.born_hk / pob).round(2),
        "pob_vivienda_publica_alquiler": df.pop_pub,
        "pob_vivienda_subsidiada_venta": df.pop_s,
        "pob_vivienda_privada": df.pop_pri,
        "pob_vivienda_temporal": df.pop_tem,
        "pob_no_domestica": df.pop_non,
        "pct_vivienda_publica_alquiler": (100 * df.pop_pub / pob).round(2),
        "pct_vivienda_subsidiada_venta": (100 * df.pop_s / pob).round(2),
        "pct_vivienda_privada": (100 * df.pop_pri / pob).round(2),
    })
    area = distritos.set_index("codigo").area_km2_oficial
    out["densidad_hab_km2"] = (out.poblacion_2021 / out.codigo.map(area)).round(0)
    out = DIST_DF.merge(out, on="codigo")

    panel = pd.read_csv(RAW / "economia" / "csdi_ghs_dc_panel_2016_2025.csv")
    panel["codigo"] = panel.dc_eng.map(EN_A_CODIGO)
    panel = panel.rename(columns={"year": "anio", "midyear_land_population": "poblacion_mitad_anio",
                                  "median_age_ghs": "edad_mediana"})
    pob_panel = panel[["anio", "codigo", "poblacion_mitad_anio", "edad_mediana"]]
    base = pob_panel[pob_panel.anio == 2016].set_index("codigo").poblacion_mitad_anio
    ult = pob_panel[pob_panel.anio == pob_panel.anio.max()].set_index("codigo").poblacion_mitad_anio
    out["poblacion_2025"] = out.codigo.map(ult)
    out["var_pob_2016_2025_pct"] = (100 * (out.codigo.map(ult) / out.codigo.map(base) - 1)).round(2)

    dst = asegurar_dir(CURATED / "demografia")
    escribir_csv(dst / "distritos_censo2021.csv", out)
    escribir_csv(dst / "panel_poblacion_2016_2025.csv", pob_panel)
    return out, pob_panel


# ---------------------------------------------------------------------------
# ECONOMÍA
# ---------------------------------------------------------------------------
def construir_economia():
    b = pd.read_csv(RAW / "economia" / "csdi_census2021_dc_economia.csv")
    b["codigo"] = b.dc_eng.map(EN_A_CODIGO)
    dist = pd.DataFrame({
        "codigo": b.codigo,
        "ingreso_mediano_hogar_hkd_2021": b.ma_hh,
        "ingreso_mediano_hogar_econ_activo_hkd_2021": b.ma_econhh,
        "ingreso_mediano_mensual_empleo_hkd_2021": b.t_mmearn,
        "tasa_participacion_laboral_pct_2021": b.lfpr_t,
        "fuerza_laboral_2021": b.t_lf,
        "poblacion_ocupada_2021": b.t_wp,
    })
    dist["tasa_ocupacion_sobre_fuerza_laboral_pct"] = (100 * dist.poblacion_ocupada_2021 / dist.fuerza_laboral_2021).round(2)

    panel = pd.read_csv(RAW / "economia" / "csdi_ghs_dc_panel_2016_2025.csv")
    panel["codigo"] = panel.dc_eng.map(EN_A_CODIGO)
    panel = panel.rename(columns={"year": "anio", "median_monthly_household_income_hkd": "ingreso_mediano_hogar_hkd",
                                  "labour_force_participation_rate_pct": "tasa_participacion_laboral_pct"})
    panel = panel[["anio", "codigo", "ingreso_mediano_hogar_hkd", "tasa_participacion_laboral_pct"]]
    ult_anio = int(panel.anio.max())
    ult = panel[panel.anio == ult_anio].set_index("codigo")
    p16 = panel[panel.anio == 2016].set_index("codigo")
    dist[f"ingreso_mediano_hogar_hkd_{ult_anio}"] = dist.codigo.map(ult.ingreso_mediano_hogar_hkd)
    dist[f"tasa_participacion_laboral_pct_{ult_anio}"] = dist.codigo.map(ult.tasa_participacion_laboral_pct)
    dist["var_ingreso_2016_2025_pct"] = (100 * (dist.codigo.map(ult.ingreso_mediano_hogar_hkd)
                                               / dist.codigo.map(p16.ingreso_mediano_hogar_hkd) - 1)).round(2)
    mediana_distritos = dist[f"ingreso_mediano_hogar_hkd_{ult_anio}"].median()
    dist["indice_ingreso_vs_mediana_distritos"] = (100 * dist[f"ingreso_mediano_hogar_hkd_{ult_anio}"] / mediana_distritos).round(1)
    dist = DIST_DF.merge(dist, on="codigo")

    gdp = pd.read_csv(RAW / "economia" / "worldbank_fred_gdp_per_capita_current_usd.csv")
    gdpk = pd.read_csv(RAW / "economia" / "worldbank_fred_gdp_per_capita_constant_usd.csv")
    cpi = pd.read_csv(RAW / "economia" / "worldbank_fred_cpi_inflation.csv")
    macro = gdp.merge(gdpk, on="year").merge(cpi, on="year").rename(columns={
        "year": "anio", "gdp_per_capita_usd_current": "pib_per_capita_usd_corrientes",
        "gdp_per_capita_usd_constant2015": "pib_per_capita_usd_constantes_2015",
        "cpi_inflation_pct": "inflacion_ipc_pct"})
    macro["crecimiento_real_pib_pc_pct"] = (100 * macro.pib_per_capita_usd_constantes_2015.pct_change()).round(2)
    recientes = pd.read_csv(RAW / "economia" / "indicadores_recientes.csv")

    dst = asegurar_dir(CURATED / "economia")
    escribir_csv(dst / "distritos_economia.csv", dist)
    escribir_csv(dst / "panel_ingreso_empleo_2016_2025.csv", panel)
    escribir_csv(dst / "macro_anual_2000_2025.csv", macro)
    escribir_csv(dst / "indicadores_recientes.csv", recientes)
    return dist, panel, macro, recientes, ult_anio


# ---------------------------------------------------------------------------
# INFRAESTRUCTURA
# ---------------------------------------------------------------------------
MODO_POR_OPERADOR = {
    "kmb": "bus", "ctb": "bus", "nlb": "bus", "lrtfeeder": "bus",
    "gmb": "minibus", "mtr": "metro_mtr", "lightRail": "tren_ligero",
    "sunferry": "ferry", "fortuneferry": "ferry", "hkkf": "ferry",
}


def construir_infraestructura(distritos, dcca, demo):
    rf = json.loads((RAW / "infraestructura" / "hkbus_routeFareList.min.json").read_text())
    stops, routes = rf["stopList"], rf["routeList"]

    # Operadores y rutas que atienden cada parada (a partir de las rutas)
    operadores = defaultdict(set)
    rutas_por_parada = defaultdict(set)
    for rid, r in routes.items():
        for co, lista in (r.get("stops") or {}).items():
            for sid in lista:
                operadores[sid].add(co)
                rutas_por_parada[sid].add(f"{co}:{r.get('route')}")

    filas = []
    for sid, s in stops.items():
        loc = s.get("location") or {}
        if not loc.get("lat"):
            continue
        ops = sorted(operadores.get(sid, []))
        modos = sorted({MODO_POR_OPERADOR.get(o, o) for o in ops})
        filas.append({
            "id_parada": sid,
            "nombre_en": (s.get("name") or {}).get("en"),
            "nombre_zh": (s.get("name") or {}).get("zh"),
            "lat": loc["lat"], "lon": loc["lng"],
            "operadores": "|".join(ops),
            "modos": "|".join(modos),
            "n_rutas": len(rutas_por_parada.get(sid, [])),
        })
    paradas = asignar_distrito(pd.DataFrame(filas), distritos, dcca)
    paradas = paradas[paradas.n_rutas > 0]

    mtr = paradas[paradas.operadores.str.contains(r"\bmtr\b", regex=True)].copy()
    mtr = mtr.rename(columns={"id_parada": "codigo_estacion"})

    hosp = pd.read_csv(RAW / "infraestructura" / "ha_hospitales_urgencias.csv")
    hosp = asignar_distrito(hosp, distritos, dcca)

    # Resumen por distrito
    res = DIST_DF[["codigo"]].copy()
    res["paradas_transporte"] = res.codigo.map(paradas.codigo.value_counts()).fillna(0).astype(int)
    for modo in ["bus", "minibus", "metro_mtr", "tren_ligero", "ferry"]:
        sub = paradas[paradas.modos.str.contains(modo)]
        res[f"paradas_{modo}"] = res.codigo.map(sub.codigo.value_counts()).fillna(0).astype(int)
    res["hospitales_urgencias"] = res.codigo.map(hosp.codigo.value_counts()).fillna(0).astype(int)
    rutas_d = defaultdict(set)
    for _, p in paradas.iterrows():
        rutas_d[p.codigo].update(rutas_por_parada[p.id_parada])
    res["rutas_distintas"] = res.codigo.map(lambda c: len(rutas_d.get(c, ())))
    area = distritos.set_index("codigo").area_km2_oficial
    pob = demo.set_index("codigo").poblacion_2021
    res["paradas_por_km2"] = (res.paradas_transporte / res.codigo.map(area)).round(2)
    res["paradas_por_10k_hab"] = (1e4 * res.paradas_transporte / res.codigo.map(pob)).round(2)
    res["hab_por_hospital_urgencias"] = (res.codigo.map(pob) / res.hospitales_urgencias.replace(0, np.nan)).round(0)

    # Distancia de cada circunscripción (centroide) al hospital de urgencias más cercano
    cen = dcca.to_crs(CRS_METRICO).copy()
    cen["geometry"] = cen.geometry.representative_point()
    h_m = hosp.to_crs(CRS_METRICO)[["hospital_en", "geometry"]]
    near = gpd.sjoin_nearest(cen[["codigo_dcca", "codigo", "geometry"]], h_m, distance_col="dist_m")
    near = near[~near.index.duplicated()]
    acceso = near[["codigo_dcca", "codigo", "hospital_en", "dist_m"]].rename(
        columns={"hospital_en": "hospital_urgencias_mas_cercano", "dist_m": "distancia_hospital_m"})
    acceso["distancia_hospital_m"] = acceso.distancia_hospital_m.round(0)
    res["dist_media_hospital_km"] = res.codigo.map(acceso.groupby("codigo").distancia_hospital_m.mean() / 1000).round(2)
    res = DIST_DF.merge(res, on="codigo")

    dst = asegurar_dir(CURATED / "infraestructura")
    cols_p = ["id_parada", "nombre_en", "nombre_zh", "lat", "lon", "operadores", "modos", "n_rutas",
              "codigo", "codigo_dcca", "ubicacion_en_tierra"]
    escribir_csv(dst / "paradas_transporte.csv", pd.DataFrame(paradas[cols_p]))
    escribir_csv(dst / "estaciones_mtr.csv", pd.DataFrame(mtr[["codigo_estacion", "nombre_en", "nombre_zh", "lat", "lon", "n_rutas", "codigo", "codigo_dcca"]]))
    escribir_csv(dst / "hospitales_urgencias.csv", pd.DataFrame(hosp.drop(columns="geometry")))
    escribir_csv(dst / "acceso_hospital_por_circunscripcion.csv", pd.DataFrame(acceso))
    escribir_csv(dst / "distritos_infraestructura.csv", res)
    return paradas, mtr, hosp, res, acceso, rutas_por_parada


# ---------------------------------------------------------------------------
# SENSORES
# ---------------------------------------------------------------------------
AQHI_ESTACION_DISTRITO = {
    "Central/Western": "A", "Southern": "D", "Eastern": "C", "Kwun Tong": "J", "Sham Shui Po": "F",
    "Kwai Chung": "S", "Tsuen Wan": "K", "Tseung Kwan O": "Q", "Yuen Long": "M", "Tuen Mun": "L",
    "Tung Chung": "T", "Tai Po": "P", "Sha Tin": "R", "North": "N", "Tap Mun": "P",
    "Causeway Bay": "B", "Central": "A", "Mong Kok": "E",
}
TIPO_ESTACION_HKO = {"Manned": "tripulada", "Automatic": "automatica", "Buoy": "boya", "Wind": "viento",
                     "Rainfall": "pluviometro", "Tide": "mareografo"}


def construir_sensores(distritos, dcca):
    hko = pd.read_csv(RAW / "sensores" / "hko_weather_stations.csv")
    hko["lat"] = hko.lat_dms.map(dms_a_decimal).round(6)
    hko["lon"] = hko.lon_dms.map(dms_a_decimal).round(6)
    hko["tipo"] = hko.type.map(TIPO_ESTACION_HKO)
    hko = hko.rename(columns={"name": "estacion", "code": "codigo_estacion", "elevation_m": "elevacion_m",
                              "first_operation": "inicio_operacion"})
    # Validación cruzada con la capa espacial oficial (CSDI) de humedad
    csdi = pd.read_csv(RAW / "sensores" / "hko_csdi_humidity_stations.csv")
    hko = asignar_distrito(hko[["estacion", "codigo_estacion", "tipo", "lat", "lon", "elevacion_m", "inicio_operacion"]],
                           distritos, dcca)
    # Distancia mínima de cada estación CSDI a la lista HKO (control de calidad de coordenadas)
    a = gpd.GeoDataFrame(csdi, geometry=gpd.points_from_xy(csdi.lon, csdi.lat), crs=CRS_WGS84).to_crs(CRS_METRICO)
    b = hko.to_crs(CRS_METRICO)
    qc = gpd.sjoin_nearest(a, b[["estacion", "geometry"]], distance_col="dist_m")
    qc = qc[~qc.index.duplicated()][["station_en", "estacion", "dist_m"]]

    aq = pd.read_csv(RAW / "sensores" / "epd_aqhi_snapshot.csv")
    aq["codigo"] = aq.station_name.map(AQHI_ESTACION_DISTRITO)
    aq = aq.rename(columns={"station_name": "estacion", "station_type": "tipo", "aqhi_value": "aqhi",
                            "health_risk": "riesgo_salud", "published_hkt": "publicado_hkt"})
    aq["tipo"] = aq.tipo.map({"General": "general", "Roadside": "borde_de_via"})
    aq["ubicacion"] = "asignada al distrito (sin coordenada exacta)"

    res = DIST_DF[["codigo"]].copy()
    res["estaciones_meteorologicas"] = res.codigo.map(hko.codigo.value_counts()).fillna(0).astype(int)
    res["estaciones_calidad_aire"] = res.codigo.map(aq.codigo.value_counts()).fillna(0).astype(int)
    res["aqhi_ultimo"] = res.codigo.map(aq[aq.tipo == "general"].groupby("codigo").aqhi.mean())
    res = DIST_DF.merge(res, on="codigo")

    dst = asegurar_dir(CURATED / "sensores")
    escribir_csv(dst / "estaciones_hko.csv", pd.DataFrame(hko.drop(columns="geometry")))
    escribir_csv(dst / "estaciones_hko_csdi_control_calidad.csv", pd.DataFrame(qc).round(1))
    escribir_csv(dst / "aqhi_estaciones_snapshot.csv", aq)
    escribir_csv(dst / "distritos_sensores.csv", res)
    return hko, aq, res, qc


# ---------------------------------------------------------------------------
# ESCUCHA (noticias + seguridad)
# ---------------------------------------------------------------------------
LEXICO_POS = ["rise", "rises", "surge", "growth", "growing", "grow", "boost", "adds", "open", "launch",
              "expands", "welcomes", "supports", "confidence", "innovation", "record", "jump", "jumps",
              "lifts", "resuming", "tops"]
LEXICO_NEG = ["low", "disrupted", "faulty", "pollution", "smog", "haze", "miss", "cool", "decline",
              "falls", "drop", "warn", "warning", "warnings", "defends", "subdivided", "crisis", "delay"]


def construir_escucha():
    noticias = pd.read_csv(RAW / "escucha" / "noticias_busqueda_2026-10-06.csv")
    loc = json.loads((RAW / "referencia" / "hkopendata_hk-location.json").read_text())
    # Diccionario lugar -> distrito (nombres de distrito + barrios de hkopendata)
    lugar_a_codigo = {}
    for d in loc["district"]:
        nombre = d["name"]["en"].replace(" District", "").replace("&", "and")
        cod = EN_A_CODIGO.get(nombre)
        if not cod:
            continue
        lugar_a_codigo[nombre.lower()] = cod
        lugares = []
        for l in d["location"]:  # algunos distritos traen la lista anidada
            lugares.extend(l if isinstance(l, list) else [l])
        for l in lugares:
            if len(l["en"]) > 3:
                lugar_a_codigo[l["en"].lower()] = cod
    lugar_a_codigo.update({"northern metropolis": "N|M", "kai tak": "G", "east kowloon": "H|J",
                           "tuen ma line": "L|M|R", "island line": "A|B|C",
                           "kwu tung": "N", "hung shui kiu": "M", "tsz wan shan": "H", "chuk yuen": "H"})

    def distritos_mencionados(t):
        t = t.lower()
        cods = set()
        for lugar, cod in lugar_a_codigo.items():
            if re.search(r"\b" + re.escape(lugar) + r"\b", t):
                cods.update(cod.split("|"))
        return "|".join(sorted(cods))

    def tono(t):
        w = re.findall(r"[a-z]+", t.lower())
        s = sum(x in LEXICO_POS for x in w) - sum(x in LEXICO_NEG for x in w)
        return s

    noticias["fuente"] = noticias.url.str.extract(r"https?://(?:www\.|m\.)?([^/]+)")[0]
    noticias["distritos_mencionados"] = (noticias.titular + " " + noticias.url).map(distritos_mencionados)
    noticias["puntaje_tono"] = noticias.titular.map(tono)
    noticias["tono"] = np.select([noticias.puntaje_tono > 0, noticias.puntaje_tono < 0], ["positivo", "negativo"], "neutral")
    noticias["fecha_captura"] = "2026-10-06"
    noticias["metodo_tono"] = "lexico_heuristico_v1"

    temas = noticias.groupby("tema").agg(
        menciones=("titular", "count"),
        tono_medio=("puntaje_tono", "mean"),
        positivas=("tono", lambda s: (s == "positivo").sum()),
        negativas=("tono", lambda s: (s == "negativo").sum()),
    ).reset_index().round(2)

    menciones_d = Counter()
    for v in noticias.distritos_mencionados:
        for c in filter(None, v.split("|")):
            menciones_d[c] += 1
    por_distrito = DIST_DF[["codigo", "distrito_en", "distrito_es"]].copy()
    por_distrito["menciones_noticias"] = por_distrito.codigo.map(menciones_d).fillna(0).astype(int)

    crimen = pd.read_csv(RAW / "escucha" / "hkpf_crime_monthly_2022_2024.csv")
    meses = {m: i for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}
    crimen["periodo"] = crimen.year.astype(str) + "-" + crimen.month.map(meses).map("{:02d}".format)
    crimen = crimen.rename(columns={"overall_crime": "delitos_totales", "violent_crime": "delitos_violentos"})
    crimen = crimen[["periodo", "delitos_totales", "delitos_violentos"]]
    crimen["pct_violentos"] = (100 * crimen.delitos_violentos / crimen.delitos_totales).round(2)

    dst = asegurar_dir(CURATED / "escucha")
    escribir_csv(dst / "noticias.csv", noticias)
    escribir_csv(dst / "temas_resumen.csv", temas)
    escribir_csv(dst / "menciones_por_distrito.csv", por_distrito)
    escribir_csv(dst / "delitos_mensuales.csv", crimen)
    return noticias, temas, por_distrito, crimen


# ---------------------------------------------------------------------------
# ATLAS DE ZONAS (distritos + circunscripciones)
# ---------------------------------------------------------------------------
VARS_TIPOLOGIA = ["densidad_hab_km2", "ingreso_mediano_hogar_hkd_2025", "pct_65_mas",
                  "pct_vivienda_publica_alquiler", "pct_titulo_universitario_15_mas", "paradas_por_10k_hab"]


def construir_atlas_zonas(distritos, dcca, demo, eco, infra, sens, menciones, paradas):
    tabla = (demo.merge(eco.drop(columns=["distrito_en", "distrito_zh", "distrito_es", "region"]), on="codigo")
             .merge(infra.drop(columns=["distrito_en", "distrito_zh", "distrito_es", "region"]), on="codigo")
             .merge(sens.drop(columns=["distrito_en", "distrito_zh", "distrito_es", "region"]), on="codigo")
             .merge(menciones[["codigo", "menciones_noticias"]], on="codigo")
             .merge(pd.DataFrame(distritos.drop(columns="geometry"))[["codigo", "area_km2_oficial", "centro_lat", "centro_lon", "n_circunscripciones"]], on="codigo"))

    # Tipología de zonas (k-means sobre variables estandarizadas, semilla fija)
    X = StandardScaler().fit_transform(tabla[VARS_TIPOLOGIA])
    km = KMeans(n_clusters=4, n_init=50, random_state=42).fit(X)
    tabla["cluster"] = km.labels_
    centros = pd.DataFrame(km.cluster_centers_, columns=VARS_TIPOLOGIA)

    # Nombres deterministas a partir de los centros (z-scores):
    restantes = set(centros.index)
    etiquetas = {}
    i = centros.loc[list(restantes), "ingreso_mediano_hogar_hkd_2025"].idxmax()
    etiquetas[i] = "Centro financiero de ingreso alto"; restantes.discard(i)
    i = centros.loc[list(restantes), "pct_vivienda_publica_alquiler"].idxmax()
    etiquetas[i] = "Núcleo denso de vivienda pública e ingreso bajo"; restantes.discard(i)
    i = centros.loc[list(restantes), "densidad_hab_km2"].idxmin()
    etiquetas[i] = "Suburbano de baja densidad"; restantes.discard(i)
    for i in restantes:
        etiquetas[i] = "Núcleo urbano denso de clase media"
    tabla["tipologia"] = tabla.cluster.map(etiquetas)

    # Índices compuestos 0-100 (min-max entre distritos)
    def mm(s, invertir=False):
        r = (s - s.min()) / (s.max() - s.min())
        return (100 * (1 - r if invertir else r)).round(1)
    tabla["indice_prosperidad"] = mm(tabla.ingreso_mediano_hogar_hkd_2025 * 0.6 / tabla.ingreso_mediano_hogar_hkd_2025.max()
                                     + tabla.pct_titulo_universitario_15_mas * 0.4 / tabla.pct_titulo_universitario_15_mas.max())
    tabla["indice_conectividad"] = mm(tabla.paradas_por_10k_hab / tabla.paradas_por_10k_hab.max()
                                      + (1 - tabla.dist_media_hospital_km / tabla.dist_media_hospital_km.max()))
    tabla["indice_presion_demografica"] = mm(tabla.densidad_hab_km2 / tabla.densidad_hab_km2.max()
                                             + tabla.pct_65_mas / tabla.pct_65_mas.max())
    for col in ["poblacion_2021", "ingreso_mediano_hogar_hkd_2025", "densidad_hab_km2", "pct_65_mas", "paradas_por_10k_hab"]:
        tabla[f"rank_{col}"] = tabla[col].rank(ascending=False, method="min").astype(int)

    # Circunscripciones: paradas por circunscripción y densidad de paradas
    dc = dcca.copy()
    dc["paradas_transporte"] = dc.codigo_dcca.map(paradas.codigo_dcca.value_counts()).fillna(0).astype(int)
    dc["paradas_por_km2_poligono"] = (dc.paradas_transporte / dc.area_km2_poligono).round(2)
    rutas = paradas.groupby("codigo_dcca").n_rutas.sum()
    dc["suma_rutas_en_paradas"] = dc.codigo_dcca.map(rutas).fillna(0).astype(int)

    dst = asegurar_dir(CURATED / "atlas_zonas")
    escribir_csv(dst / "atlas_distritos.csv", tabla)
    geo = distritos[["codigo", "geometry"]].merge(tabla, on="codigo")
    g = geo.to_crs(CRS_METRICO)
    g["geometry"] = g.geometry.simplify(40, preserve_topology=True)
    g.to_crs(CRS_WGS84).to_file(dst / "atlas_distritos.geojson", driver="GeoJSON")
    escribir_csv(dst / "atlas_circunscripciones.csv", pd.DataFrame(dc.drop(columns="geometry")))
    g2 = dc.to_crs(CRS_METRICO)
    g2["geometry"] = g2.geometry.simplify(15, preserve_topology=True)
    g2.to_crs(CRS_WGS84).to_file(dst / "atlas_circunscripciones.geojson", driver="GeoJSON")
    escribir_csv(dst / "tipologias_centros_estandarizados.csv",
                 centros.assign(tipologia=[etiquetas[i] for i in centros.index]).round(3))
    return tabla, dc, centros, etiquetas


# ---------------------------------------------------------------------------
# ATLAS DISTRIBUIDO (activos puntuales + malla hexagonal H3)
# ---------------------------------------------------------------------------
H3_RES = 8  # ~0,74 km² por hexágono


def construir_atlas_distribuidos(paradas, hosp, hko):
    capas = []
    p = pd.DataFrame(paradas.drop(columns="geometry"))
    capas.append(pd.DataFrame({"capa": "parada_transporte", "id": p.id_parada, "nombre": p.nombre_en,
                               "subtipo": p.modos, "lat": p.lat, "lon": p.lon, "codigo": p.codigo,
                               "codigo_dcca": p.codigo_dcca, "peso": p.n_rutas}))
    h = pd.DataFrame(hosp.drop(columns="geometry"))
    capas.append(pd.DataFrame({"capa": "hospital_urgencias", "id": h.hospital_en, "nombre": h.hospital_en,
                               "subtipo": "A&E", "lat": h.lat, "lon": h.lon, "codigo": h.codigo,
                               "codigo_dcca": h.codigo_dcca, "peso": 1}))
    s = pd.DataFrame(hko.drop(columns="geometry"))
    capas.append(pd.DataFrame({"capa": "estacion_meteorologica", "id": s.codigo_estacion + ":" + s.tipo, "nombre": s.estacion,
                               "subtipo": s.tipo, "lat": s.lat, "lon": s.lon, "codigo": s.codigo,
                               "codigo_dcca": s.codigo_dcca, "peso": 1}))
    puntos = pd.concat(capas, ignore_index=True)
    puntos["h3"] = [h3.latlng_to_cell(la, lo, H3_RES) for la, lo in zip(puntos.lat, puntos.lon)]

    hexes = (puntos.assign(n=1).pivot_table(index="h3", columns="capa", values="n", aggfunc="sum", fill_value=0)
             .reset_index())
    rutas = puntos[puntos.capa == "parada_transporte"].groupby("h3").peso.sum()
    hexes["rutas_servidas"] = hexes.h3.map(rutas).fillna(0).astype(int)
    hexes["codigo"] = hexes.h3.map(puntos.groupby("h3").codigo.agg(lambda x: x.mode().iat[0] if x.notna().any() else None))
    lat_lon = [h3.cell_to_latlng(c) for c in hexes.h3]
    hexes["lat"] = [round(a, 6) for a, _ in lat_lon]
    hexes["lon"] = [round(b, 6) for _, b in lat_lon]
    if "parada_transporte" in hexes:
        q = hexes.parada_transporte.rank(pct=True)
        hexes["nivel_cobertura"] = pd.cut(q, [0, .25, .5, .75, 1.0], labels=["baja", "media", "alta", "muy_alta"], include_lowest=True).astype(str)

    dst = asegurar_dir(CURATED / "atlas_distribuidos")
    escribir_csv(dst / "puntos.csv", puntos)
    escribir_csv(dst / "hex_h3_res8.csv", hexes)
    feats = []
    for _, r in hexes.iterrows():
        anillo = [[lo, la] for la, lo in h3.cell_to_boundary(r.h3)]
        anillo.append(anillo[0])
        props = {k: r[k] for k in hexes.columns if k not in ("lat", "lon")}
        feats.append({"type": "Feature", "properties": props, "geometry": {"type": "Polygon", "coordinates": [anillo]}})
    escribir_json(dst / "hex_h3_res8.geojson", {"type": "FeatureCollection", "features": feats})
    return puntos, hexes


# ---------------------------------------------------------------------------
# CORRELACIONES
# ---------------------------------------------------------------------------
VARS_CORR = {
    "densidad_hab_km2": "Densidad (hab/km²)",
    "edad_mediana": "Edad mediana",
    "pct_65_mas": "% 65+ años",
    "pct_0_14": "% 0-14 años",
    "tamano_medio_hogar": "Tamaño medio del hogar",
    "pct_titulo_universitario_15_mas": "% con título universitario",
    "pct_nacida_en_hk": "% nacida en HK",
    "pct_vivienda_publica_alquiler": "% vivienda pública de alquiler",
    "pct_vivienda_privada": "% vivienda privada",
    "ingreso_mediano_hogar_hkd_2025": "Ingreso mediano hogar 2025",
    "ingreso_mediano_mensual_empleo_hkd_2021": "Ingreso mediano por empleo 2021",
    "tasa_participacion_laboral_pct_2025": "Participación laboral 2025",
    "var_ingreso_2016_2025_pct": "Var. ingreso 2016-2025",
    "var_pob_2016_2025_pct": "Var. población 2016-2025",
    "paradas_por_10k_hab": "Paradas por 10k hab.",
    "paradas_por_km2": "Paradas por km²",
    "dist_media_hospital_km": "Dist. media a urgencias (km)",
}


def construir_correlaciones(tabla):
    vars_ = list(VARS_CORR)
    X = tabla[vars_]
    pear = X.corr(method="pearson")
    spear = X.corr(method="spearman")
    pares = []
    for i, a in enumerate(vars_):
        for b in vars_[i + 1:]:
            r, p = stats.pearsonr(X[a], X[b])
            rho, ps = stats.spearmanr(X[a], X[b])
            pares.append({"var_x": a, "var_y": b, "etiqueta_x": VARS_CORR[a], "etiqueta_y": VARS_CORR[b],
                          "pearson_r": round(r, 4), "pearson_p": round(p, 5),
                          "spearman_rho": round(rho, 4), "spearman_p": round(ps, 5), "n": len(X),
                          "significativo_5pct": bool(p < 0.05)})
    pares = pd.DataFrame(pares).sort_values("pearson_r", key=abs, ascending=False)

    dst = asegurar_dir(CURATED / "correlaciones")
    escribir_csv(dst / "matriz_pearson.csv", pear.round(4).reset_index().rename(columns={"index": "variable"}))
    escribir_csv(dst / "matriz_spearman.csv", spear.round(4).reset_index().rename(columns={"index": "variable"}))
    escribir_csv(dst / "pares.csv", pares)
    return pear, spear, pares


# ---------------------------------------------------------------------------
# CAPA ORO (public/data) — un JSON por pestaña
# ---------------------------------------------------------------------------
def geojson_dict(path):
    return json.loads(path.read_text())


def publicar(ctx):
    d = ctx
    meta = {"generado_utc": GENERADO, "ciudad": "Hong Kong", "unidad_territorial": "18 distritos (District Council districts)",
            "catalogo": "catalogo/catalogo.json"}
    t = d["atlas"]
    ult = d["ult_anio"]
    ghs = d["panel_eco"].merge(d["panel_pob"], on=["anio", "codigo"])
    ghs_ult = ghs[ghs.anio == ult]

    panorama = {
        "meta": meta,
        "kpis": {
            "poblacion_censo_2021": int(d["demo"].poblacion_2021.sum()),
            f"poblacion_tierra_mitad_anio_{ult}": int(ghs_ult.poblacion_mitad_anio.sum()),
            "hogares_2021": int(d["demo"].hogares_2021.sum()),
            "area_terrestre_km2": round(float(d["distritos"].area_km2_oficial.sum()), 2),
            "densidad_media_hab_km2": round(float(d["demo"].poblacion_2021.sum() / d["distritos"].area_km2_oficial.sum()), 0),
            "pct_65_mas_2021": round(float(100 * d["demo"].pob_65_mas.sum() / d["demo"].poblacion_2021.sum()), 2),
            f"ingreso_mediano_hogar_rango_distritos_{ult}": [int(ghs_ult.ingreso_mediano_hogar_hkd.min()), int(ghs_ult.ingreso_mediano_hogar_hkd.max())],
            "pib_per_capita_usd_2025": round(float(d["macro"].set_index("anio").loc[2025, "pib_per_capita_usd_corrientes"]), 0),
            "inflacion_ipc_2025_pct": round(float(d["macro"].set_index("anio").loc[2025, "inflacion_ipc_pct"]), 2),
            "paradas_transporte_publico": int(len(d["paradas"])),
            "estaciones_mtr": int(len(d["mtr"])),
            "hospitales_urgencias": int(len(d["hosp"])),
            "estaciones_meteorologicas": int(len(d["hko"])),
            "estaciones_calidad_aire": int(len(d["aq"])),
            "noticias_monitoreadas": int(len(d["noticias"])),
        },
        "indicadores_recientes": registros(d["recientes"]),
        "distritos": registros(t[["codigo", "distrito_es", "distrito_en", "distrito_zh", "region", "poblacion_2021",
                                  "densidad_hab_km2", f"ingreso_mediano_hogar_hkd_{ult}", "pct_65_mas", "tipologia",
                                  "indice_prosperidad", "indice_conectividad", "indice_presion_demografica",
                                  "centro_lat", "centro_lon"]]),
        "destacados": {
            "mas_poblado": t.loc[t.poblacion_2021.idxmax(), "distrito_es"],
            "mas_denso": t.loc[t.densidad_hab_km2.idxmax(), "distrito_es"],
            "mayor_ingreso": t.loc[t[f"ingreso_mediano_hogar_hkd_{ult}"].idxmax(), "distrito_es"],
            "menor_ingreso": t.loc[t[f"ingreso_mediano_hogar_hkd_{ult}"].idxmin(), "distrito_es"],
            "mas_envejecido": t.loc[t.pct_65_mas.idxmax(), "distrito_es"],
            "mayor_crecimiento_poblacion_2016_2025": t.loc[t.var_pob_2016_2025_pct.idxmax(), "distrito_es"],
        },
    }
    escribir_json(PUBLIC / "panorama.json", panorama)

    escribir_json(PUBLIC / "geo.json", {
        "meta": meta,
        "distritos": geojson_dict(CURATED / "geo" / "distritos_web.geojson"),
        "regiones": geojson_dict(CURATED / "geo" / "regiones.geojson"),
    })
    escribir_json(PUBLIC / "geo_circunscripciones.json", geojson_dict(CURATED / "geo" / "circunscripciones_dcca_2019.geojson"))

    escribir_json(PUBLIC / "demografia.json", {
        "meta": meta, "fuente": "Censo 2021 (C&SD vía CSDI) y Encuesta General de Hogares 2016-2025",
        "distritos": registros(d["demo"]),
        "serie_poblacion": registros(d["panel_pob"]),
        "piramide_hk_2021": {k: int(d["demo"][f"pob_{k}"].sum()) for k in ["0_14", "15_24", "25_44", "45_64", "65_mas"]},
    })
    escribir_json(PUBLIC / "economia.json", {
        "meta": meta, "fuente": "C&SD (Censo 2021, Encuesta General de Hogares) · Banco Mundial vía FRED · HKPF",
        "distritos": registros(d["eco"]),
        "serie_distritos": registros(d["panel_eco"]),
        "macro": registros(d["macro"]),
        "indicadores_recientes": registros(d["recientes"]),
    })
    escribir_json(PUBLIC / "infraestructura.json", {
        "meta": meta, "fuente": "hkbus/hk-bus-crawling (datos abiertos de operadores vía data.gov.hk) · Hospital Authority",
        "distritos": registros(d["infra"]),
        "estaciones_mtr": registros(d["mtr"][["codigo_estacion", "nombre_en", "nombre_zh", "lat", "lon", "n_rutas", "codigo"]]),
        "hospitales": registros(pd.DataFrame(d["hosp"].drop(columns="geometry"))),
        "acceso_hospital_dcca": registros(d["acceso"]),
    })
    escribir_json(PUBLIC / "infraestructura_paradas.json",
                  {"columnas": ["id", "nombre", "lat", "lon", "modos", "n_rutas", "codigo"],
                   "filas": d["paradas"][["id_parada", "nombre_en", "lat", "lon", "modos", "n_rutas", "codigo"]].values.tolist()})
    escribir_json(PUBLIC / "sensores.json", {
        "meta": meta, "fuente": "Hong Kong Observatory · Environmental Protection Department (AQHI)",
        "estaciones_meteorologicas": registros(pd.DataFrame(d["hko"].drop(columns="geometry"))),
        "calidad_aire": registros(d["aq"]),
        "distritos": registros(d["sens"]),
        "control_calidad_coordenadas": registros(d["qc"].round(1)),
    })
    escribir_json(PUBLIC / "escucha.json", {
        "meta": meta, "fuente": "Búsqueda web de titulares (captura 2026-10-06) · Hong Kong Police Force",
        "noticias": registros(d["noticias"]),
        "temas": registros(d["temas"]),
        "menciones_por_distrito": registros(d["menciones"]),
        "delitos_mensuales": registros(d["crimen"]),
        "nota_metodologica": "El tono es un puntaje heurístico por léxico (palabras positivas menos negativas en el titular). Es una señal exploratoria, no un análisis de sentimiento validado.",
    })
    escribir_json(PUBLIC / "atlas_zonas.json", {
        "meta": meta,
        "distritos": registros(t),
        "geo_distritos": geojson_dict(CURATED / "atlas_zonas" / "atlas_distritos.geojson"),
        "tipologias": {str(k): v for k, v in d["etiquetas"].items()},
        "variables_tipologia": VARS_TIPOLOGIA,
        "circunscripciones": registros(pd.DataFrame(d["dc"].drop(columns="geometry"))),
    })
    escribir_json(PUBLIC / "atlas_distribuidos.json", {
        "meta": meta, "resolucion_h3": H3_RES,
        "resumen_capas": d["puntos"].capa.value_counts().to_dict(),
        "hexagonos": registros(d["hexes"]),
        "puntos_no_transporte": registros(d["puntos"][d["puntos"].capa != "parada_transporte"]),
    })
    escribir_json(PUBLIC / "correlaciones.json", {
        "meta": meta, "n_observaciones": 18, "variables": VARS_CORR,
        "pearson": d["pear"].round(4).to_dict(), "spearman": d["spear"].round(4).to_dict(),
        "pares_top": registros(d["pares"].head(25)),
        "dispersion": registros(t[["codigo", "distrito_es"] + list(VARS_CORR)]),
        "advertencia": "Con 18 distritos las correlaciones son descriptivas (ecológicas); no implican causalidad.",
    })
    escribir_json(PUBLIC / "manifest.json", {
        "meta": meta,
        "pestanas": ["panorama", "geo", "demografia", "economia", "infraestructura", "sensores", "escucha",
                     "atlas_zonas", "atlas_distribuidos", "correlaciones"],
        "archivos": sorted(p.name for p in PUBLIC.glob("*.json")),
    })


def main():
    distritos, dcca = construir_geo()
    demo, panel_pob = construir_demografia(distritos)
    eco, panel_eco, macro, recientes, ult_anio = construir_economia()
    paradas, mtr, hosp, infra, acceso, _ = construir_infraestructura(distritos, dcca, demo)
    hko, aq, sens, qc = construir_sensores(distritos, dcca)
    noticias, temas, menciones, crimen = construir_escucha()
    atlas, dc, centros, etiquetas = construir_atlas_zonas(distritos, dcca, demo, eco, infra, sens, menciones, paradas)
    puntos, hexes = construir_atlas_distribuidos(paradas, hosp, hko)
    pear, spear, pares = construir_correlaciones(atlas)
    publicar(dict(distritos=distritos, demo=demo, panel_pob=panel_pob, eco=eco, panel_eco=panel_eco, macro=macro,
                  recientes=recientes, ult_anio=ult_anio, paradas=paradas, mtr=mtr, hosp=hosp, infra=infra,
                  acceso=acceso, hko=hko, aq=aq, sens=sens, qc=qc, noticias=noticias, temas=temas,
                  menciones=menciones, crimen=crimen, atlas=atlas, dc=dc, etiquetas=etiquetas,
                  puntos=puntos, hexes=hexes, pear=pear, spear=spear, pares=pares))
    print("Data lake construido:", GENERADO)


if __name__ == "__main__":
    main()
