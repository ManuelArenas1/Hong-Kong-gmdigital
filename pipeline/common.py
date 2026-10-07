"""Utilidades compartidas del pipeline del data lake de Hong Kong."""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
CURATED = ROOT / "curated"
PUBLIC = ROOT / "public" / "data"

# CRS métrico oficial de Hong Kong (HK 1980 Grid) para áreas y distancias.
CRS_METRICO = "EPSG:2326"
CRS_WGS84 = "EPSG:4326"

# Códigos oficiales de los 18 distritos (letra usada por el censo y por la EAC).
DISTRITOS = [
    # codigo, nombre_en, nombre_zh, nombre_es, region
    ("A", "Central and Western", "中西區", "Centro y Oeste", "Isla de Hong Kong"),
    ("B", "Wan Chai", "灣仔區", "Wan Chai", "Isla de Hong Kong"),
    ("C", "Eastern", "東區", "Este", "Isla de Hong Kong"),
    ("D", "Southern", "南區", "Sur", "Isla de Hong Kong"),
    ("E", "Yau Tsim Mong", "油尖旺區", "Yau Tsim Mong", "Kowloon"),
    ("F", "Sham Shui Po", "深水埗區", "Sham Shui Po", "Kowloon"),
    ("G", "Kowloon City", "九龍城區", "Ciudad de Kowloon", "Kowloon"),
    ("H", "Wong Tai Sin", "黃大仙區", "Wong Tai Sin", "Kowloon"),
    ("J", "Kwun Tong", "觀塘區", "Kwun Tong", "Kowloon"),
    ("K", "Tsuen Wan", "荃灣區", "Tsuen Wan", "Nuevos Territorios"),
    ("L", "Tuen Mun", "屯門區", "Tuen Mun", "Nuevos Territorios"),
    ("M", "Yuen Long", "元朗區", "Yuen Long", "Nuevos Territorios"),
    ("N", "North", "北區", "Norte", "Nuevos Territorios"),
    ("P", "Tai Po", "大埔區", "Tai Po", "Nuevos Territorios"),
    ("Q", "Sai Kung", "西貢區", "Sai Kung", "Nuevos Territorios"),
    ("R", "Sha Tin", "沙田區", "Sha Tin", "Nuevos Territorios"),
    ("S", "Kwai Tsing", "葵青區", "Kwai Tsing", "Nuevos Territorios"),
    ("T", "Islands", "離島區", "Islas", "Nuevos Territorios"),
]

DIST_DF = pd.DataFrame(
    DISTRITOS, columns=["codigo", "distrito_en", "distrito_zh", "distrito_es", "region"]
)
EN_A_CODIGO = dict(zip(DIST_DF.distrito_en, DIST_DF.codigo))


def asegurar_dir(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p


def _limpiar(o):
    """Convierte tipos numpy/NaN a tipos JSON nativos."""
    if isinstance(o, dict):
        return {k: _limpiar(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_limpiar(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        f = float(o)
        if math.isnan(f) or math.isinf(f):
            return None
        return round(f, 6)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return o


def escribir_json(ruta: Path, obj) -> None:
    asegurar_dir(ruta.parent)
    ruta.write_text(
        json.dumps(_limpiar(obj), ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )


def escribir_csv(ruta: Path, df: pd.DataFrame) -> None:
    asegurar_dir(ruta.parent)
    df.to_csv(ruta, index=False, encoding="utf-8")


def dms_a_decimal(txt: str) -> float:
    """'22°18'07"' -> 22.301944"""
    txt = txt.replace("″", '"').replace("′", "'")
    grados, resto = txt.split("°")
    minutos, resto = resto.split("'")
    segundos = resto.replace('"', "") or "0"
    return float(grados) + float(minutos) / 60 + float(segundos) / 3600


def registros(df: pd.DataFrame) -> list[dict]:
    return df.to_dict(orient="records")
