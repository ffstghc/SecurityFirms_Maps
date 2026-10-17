"""Paths and loaders for every input file."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
DASH = RAW / "dashboard"      # data behind the "Security Supply vs Event Demand" dashboard
DESTATIS = RAW / "destatis"   # written by code/fetch_owners_data.py
MANUAL = RAW / "manual"       # optional files you export by hand (see README)
RESULTS = ROOT / "results"

# Destatis Land keys -> the two-letter codes used everywhere else
LAND_KEY = {"01": "SH", "02": "HH", "03": "NI", "04": "HB", "05": "NW", "06": "HE",
            "07": "RP", "08": "BW", "09": "BY", "10": "SL", "11": "BE", "12": "BB",
            "13": "MV", "14": "SN", "15": "ST", "16": "TH"}


def _csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"ags": str, "code": str}, encoding="utf-8")


def _shapes(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------- Part 1: Germany ----------

def security_staff() -> pd.DataFrame:
    """Workers in WZ 80.1 per state, 31 Mar 2026: svb_801 (insured) + gb_801 (minijobs)."""
    return _csv(DASH / "security_staff.csv")


def population() -> pd.DataFrame:
    """Residents per state, 31 Dec 2025."""
    return _csv(DASH / "population.csv")


def events() -> pd.DataFrame:
    """118 recurring crowd events with annual visits; `code` is the state."""
    return _csv(DASH / "events.csv")


def state_shapes() -> list[dict]:
    return _shapes(DASH / "state_shapes.json")


# ---------- Part 2: Bavaria ----------

def by_districts() -> pd.DataFrame:
    """96 Bavarian districts: KldB 53 workers (svb + gb, 31 Mar 2026), residents 31 Dec 2024."""
    return _csv(DASH / "by_districts.csv")


def by_events() -> pd.DataFrame:
    """33 Bavarian events with annual visits; `ags` is the district."""
    return _csv(DASH / "by_events.csv")


def by_shapes() -> list[dict]:
    """96 district outlines (level 'district') and 7 Regierungsbezirke (level 'region')."""
    return _shapes(DASH / "by_shapes.json")


# ---------- Part 3: Owners ----------

def _tidy_destatis(path: Path, region_col: str | None) -> pd.DataFrame:
    """Flat GENESIS CSV -> one row per (region, year, wz, measure) with a numeric value.

    GENESIS writes '.' for suppressed cells and '-' for zero.
    """
    raw = pd.read_csv(path, dtype=str)
    wz_col = [c for c in raw.columns if c.endswith("_variable_code")
              and raw[c].astype(str).str.startswith("WZ08").all()][0].replace("_variable_code", "")
    out = pd.DataFrame({
        "year": raw["time"].astype(int),
        "wz": raw[f"{wz_col}_variable_attribute_code"].str.replace("WZ08-", "", regex=False),
        "wz_label": raw[f"{wz_col}_variable_attribute_label"],
        "measure": raw["value_variable_code"].map({"STR040": "firms", "STR042": "turnover_keur"}),
        "value": pd.to_numeric(raw["value"].replace({"-": "0", ".": None}), errors="coerce"),
    })
    if region_col:
        out.insert(0, region_col, raw[f"{_var_index(raw, region_col)}_variable_attribute_code"])
    return out


def _var_index(raw: pd.DataFrame, variable: str) -> str:
    return next(c.replace("_variable_code", "") for c in raw.columns
                if c.endswith("_variable_code") and raw[c].iloc[0] == variable)


def vat_firms_by_state() -> pd.DataFrame:
    """VAT taxpayers and taxable turnover in WZ 80 per state and year (Destatis 73311-0011)."""
    df = _tidy_destatis(DESTATIS / "73311-0011_wz80_laender.csv", "DLAND")
    df["code"] = df.pop("DLAND").map(LAND_KEY)
    return df


def vat_firms_germany() -> pd.DataFrame:
    """The same for Germany as a whole (Destatis 73311-0002)."""
    return _tidy_destatis(DESTATIS / "73311-0002_wz80_deutschland.csv", None)


def vat_firms_by_legal_form() -> pd.DataFrame:
    """The same for Germany by legal form, 2020-2024 (Destatis 73311-0005)."""
    df = _tidy_destatis(DESTATIS / "73311-0005_wz80_rechtsformen.csv", "RECF03")
    df = df.rename(columns={"RECF03": "legal_form"})
    df["legal_form"] = df["legal_form"].fillna("TOTAL")  # the "Insgesamt" row has no code
    raw = pd.read_csv(DESTATIS / "73311-0005_wz80_rechtsformen.csv", dtype=str)
    labels = dict(zip(raw[f"{_var_index(raw, 'RECF03')}_variable_attribute_code"],
                      raw[f"{_var_index(raw, 'RECF03')}_variable_attribute_label"]))
    df["legal_form_label"] = df["legal_form"].map(labels)
    return df


def manual_bavaria_firms() -> pd.DataFrame | None:
    """Optional: security firms per Bavarian district that you exported by hand.

    Expected file: data/raw/manual/bavaria_firms_by_district.csv with columns
    `ags` (5-digit district key, e.g. 09162) and `firms`, plus optional `year`
    and `source`. See README, Part 3.
    """
    path = MANUAL / "bavaria_firms_by_district.csv"
    return _csv(path) if path.exists() else None
