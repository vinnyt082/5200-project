"""Aggregates for cross-region comparison (existing processed inputs only)."""

from __future__ import annotations

import pandas as pd

from app.stage2 import region_data as rd

REGIONS_ORDER = ["Americas", "Africa", "Asia-Pacific"]


def _reindex_fill_zero(s: pd.Series) -> pd.Series:
    return s.reindex(REGIONS_ORDER).fillna(0.0)


def _reindex_nan(s: pd.Series) -> pd.Series:
    return s.reindex(REGIONS_ORDER)


def production_totals_by_region() -> pd.Series:
    p = rd.load_stage1_production()
    if p.empty or "region" not in p.columns or "production_tonnes" not in p.columns:
        return pd.Series(0.0, index=REGIONS_ORDER)
    g = p.groupby("region", as_index=True)["production_tonnes"].sum()
    return _reindex_fill_zero(g)


def import_totals_by_region() -> pd.Series:
    imp = rd.load_stage1_imports()
    if imp.empty or "region" not in imp.columns or "import_value_or_quantity" not in imp.columns:
        return pd.Series(0.0, index=REGIONS_ORDER)
    g = imp.groupby("region", as_index=True)["import_value_or_quantity"].sum()
    return _reindex_fill_zero(g)


def median_representative_elevation_by_region() -> pd.Series:
    """Median country representative elevation among origins in each region (terrain context)."""
    elev = rd.load_elevation_context()
    prod = rd.load_stage1_production()
    if elev.empty or prod.empty:
        return pd.Series(index=REGIONS_ORDER, dtype=float)
    need = {"country", "representative_elevation_m"}
    if not need.issubset(elev.columns) or "region" not in prod.columns:
        return pd.Series(index=REGIONS_ORDER, dtype=float)
    m = elev[list(need)].merge(prod[["country", "region"]], on="country", how="inner")
    g = m.groupby("region")["representative_elevation_m"].median()
    return _reindex_nan(g)


def cup_features_by_region() -> pd.DataFrame:
    """Lot-level cup rows with region label (for boxplots and counts)."""
    cup = rd.load_coffee_features()
    if cup.empty or "region" not in cup.columns:
        return pd.DataFrame()
    return cup[cup["region"].isin(REGIONS_ORDER)].copy()


def sensory_means_by_region() -> pd.DataFrame:
    """Mean sensory attributes by region (unweighted mean of lot scores)."""
    cup = cup_features_by_region()
    cols = [c for c in rd.SENSORY_NUMERIC if c in cup.columns]
    if cup.empty or not cols:
        return pd.DataFrame()
    g = cup.groupby("region")[cols].mean()
    return g.reindex(REGIONS_ORDER)


def regional_lot_altitude_score_summary() -> pd.DataFrame:
    """
    One summary row per region: median lot altitude, mean total cup points, lot count.
    """
    cup = cup_features_by_region()
    if cup.empty:
        return pd.DataFrame()
    rows = []
    for reg in REGIONS_ORDER:
        sub = cup.loc[cup["region"] == reg]
        n = len(sub)
        med_alt = float(sub["altitude"].median()) if n and "altitude" in sub.columns else float("nan")
        mean_pts = (
            float(sub["total_cup_points"].mean()) if n and "total_cup_points" in sub.columns else float("nan")
        )
        rows.append(
            {
                "region": reg,
                "n_lots": n,
                "median_lot_altitude_m": med_alt,
                "mean_total_cup_points": mean_pts,
            }
        )
    return pd.DataFrame(rows)


def lot_counts_by_region() -> pd.Series:
    cup = cup_features_by_region()
    if cup.empty:
        return pd.Series(0, index=REGIONS_ORDER)
    c = cup.groupby("region").size()
    return _reindex_fill_zero(c.astype(float))
