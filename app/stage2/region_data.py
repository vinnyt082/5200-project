"""
Stage 2 data access: cup-quality features, Stage 1 production/trade, elevation context.

Country keys are normalized to lowercase stripped strings for joins where needed.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.config import (
    COFFEE_FEATURES_PATH,
    ELEVATION_CONTEXT_PATH,
    PRODUCTION_PATH,
    RAW_DIR,
    US_IMPORT_PATH,
)


def _norm_country(s: object) -> str:
    return str(s).strip().lower() if s is not None and not (isinstance(s, float) and pd.isna(s)) else ""


@st.cache_data(show_spinner=False)
def load_coffee_features() -> pd.DataFrame:
    if not COFFEE_FEATURES_PATH.exists():
        raise FileNotFoundError(
            f"Missing {COFFEE_FEATURES_PATH}. Run scripts/01_load_clean.py and 02_feature_engineering.py."
        )
    return pd.read_csv(COFFEE_FEATURES_PATH)


@st.cache_data(show_spinner=False)
def stage1_production_reference_year() -> int | None:
    """
    Latest calendar year in the OWID-style production CSV (matches the ingest filter
    that keeps one year for map-ready production).
    """
    candidates = [
        RAW_DIR / "production" / "coffee-bean-production.csv",
        RAW_DIR / "coffee-bean-production.csv",
        RAW_DIR / "coffee-bean-production" / "coffee-bean-production.csv",
    ]
    for path in candidates:
        if not path.exists():
            continue
        try:
            ser = pd.read_csv(path, usecols=["Year"])["Year"]
        except (ValueError, KeyError, pd.errors.EmptyDataError):
            try:
                peek = pd.read_csv(path, nrows=5)
            except Exception:
                continue
            ycol = next((c for c in peek.columns if str(c).strip().lower() == "year"), None)
            if ycol is None:
                continue
            try:
                ser = pd.read_csv(path, usecols=[ycol])[ycol]
            except Exception:
                continue
        vals = pd.to_numeric(ser, errors="coerce").dropna()
        if not vals.empty:
            return int(vals.max())
    return None


@st.cache_data(show_spinner=False)
def load_stage1_production() -> pd.DataFrame:
    if not PRODUCTION_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(PRODUCTION_PATH)


@st.cache_data(show_spinner=False)
def load_stage1_imports() -> pd.DataFrame:
    if not US_IMPORT_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(US_IMPORT_PATH)


@st.cache_data(show_spinner=False)
def load_elevation_context() -> pd.DataFrame:
    if not ELEVATION_CONTEXT_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(ELEVATION_CONTEXT_PATH)


def coffee_features_for_region(df: pd.DataFrame, region: str) -> pd.DataFrame:
    return df[df["region"] == region].copy()


def production_for_region(region: str) -> pd.DataFrame:
    p = load_stage1_production()
    if p.empty or "region" not in p.columns:
        return pd.DataFrame()
    sub = p[p["region"] == region].copy()
    if "production_tonnes" in sub.columns:
        sub = sub.rename(columns={"production_tonnes": "production_tonnes_latest"})
    return sub.sort_values(
        "production_tonnes_latest", ascending=False, na_position="last"
    )


def imports_for_region(region: str) -> pd.DataFrame:
    imp = load_stage1_imports()
    if imp.empty or "region" not in imp.columns:
        return pd.DataFrame()
    return imp[imp["region"] == region].sort_values(
        "import_value_or_quantity", ascending=False, na_position="last"
    )


def elevation_context_for_region(region: str) -> pd.DataFrame:
    """Country-level illustrative elevations (not farm GPS)."""
    ctx = load_elevation_context()
    prod = load_stage1_production()
    if ctx.empty or prod.empty:
        return pd.DataFrame()
    if "production_tonnes" in prod.columns:
        prod = prod.rename(columns={"production_tonnes": "production_tonnes_latest"})
    keys = prod.loc[prod["region"] == region, "country"].map(_norm_country)
    countries = set(keys.dropna())
    ctx = ctx.copy()
    ctx["_k"] = ctx["country"].map(_norm_country)
    return ctx[ctx["_k"].isin(countries)].drop(columns=["_k"], errors="ignore")


# --- Cup profile columns (Arabica sensory attributes in processed dataset) -----
SENSORY_NUMERIC = [
    "aroma",
    "flavor",
    "aftertaste",
    "acidity",
    "body",
    "balance",
    "sweetness",
    "overall",
]


def sensory_summary_by_country(df: pd.DataFrame) -> pd.DataFrame:
    """Mean sensory attributes by country_of_origin (cupping lots, not national census)."""
    sub = df.dropna(subset=["country_of_origin"]).copy()
    if sub.empty:
        return pd.DataFrame()
    g = sub.groupby("country_of_origin", dropna=True)[SENSORY_NUMERIC + ["total_cup_points"]]
    return g.mean().reset_index().sort_values("total_cup_points", ascending=False)


def stage2_data_gaps_note() -> str:
    """
    Shortlist of optional enhancements if we invest in richer regional chapters.
    (Displayed in-page as a compact expander—not a separate doc file.)
    """
    return (
        "- **Finer trade story:** re-export HS-specific volumes/values by partner if you add "
        "a curated trade extract (OEC/UN Comtrade-style), beyond the current illustrative origin totals.\n"
        "- **Terrain maps:** small-multiple elevation maps per country need raster or simplified "
        "terrain geometry—not yet in the pipeline.\n"
        "- **Historical arc:** a dated regional production time series (OWID regional file exists raw) "
        "could back a “rise and shift” narrative once wired into processed tables."
    )
