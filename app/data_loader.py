from __future__ import annotations

import pandas as pd

from app.config import (
    CENTROIDS_PATH,
    ELEVATION_CONTEXT_PATH,
    PRODUCTION_PATH,
    REGION_COLORS,
    US_IMPORT_PATH,
)

def _read_csv_if_exists(path):
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


def load_stage1_data() -> pd.DataFrame:
    """
    Build country-level table for Stage 1 map.

    Combines app-ready processed inputs:
    - stage1_country_production.csv
    - stage1_us_imports_by_origin.csv
    - stage1_country_centroids.csv
    - optional elevation context
    """
    prod = _read_csv_if_exists(PRODUCTION_PATH)
    imports_df = _read_csv_if_exists(US_IMPORT_PATH)
    centroids = _read_csv_if_exists(CENTROIDS_PATH)
    elev = _read_csv_if_exists(ELEVATION_CONTEXT_PATH)

    if prod.empty:
        raise FileNotFoundError(
            f"Missing production input: {PRODUCTION_PATH}. Run scripts/05_stage1_map_ingest.py first."
        )

    required_prod_cols = {"country", "region", "production_tonnes"}
    missing_prod = required_prod_cols - set(prod.columns)
    if missing_prod:
        raise ValueError(f"Production file missing columns: {sorted(missing_prod)}")

    prod_latest = prod.rename(
        columns={"production_tonnes": "production_tonnes_latest"}
    )[["country", "region", "production_tonnes_latest"]]

    if imports_df.empty:
        raise FileNotFoundError(
            f"Missing trade input: {US_IMPORT_PATH}. Run scripts/05_stage1_map_ingest.py first."
        )

    expected_import_cols = {"country", "normalized_route_weight", "import_value_or_quantity"}
    missing_import_cols = expected_import_cols - set(imports_df.columns)
    if missing_import_cols:
        raise ValueError(
            f"US import file missing columns: {sorted(missing_import_cols)}"
        )

    if centroids.empty:
        raise FileNotFoundError(
            f"Missing centroids input: {CENTROIDS_PATH}. Run scripts/05_stage1_map_ingest.py first."
        )

    for col in ["country", "lat", "lon"]:
        if col not in centroids.columns:
            raise ValueError("Centroids file must contain country, lat, lon columns.")

    stage = (
        prod_latest.merge(imports_df, on="country", how="left", suffixes=("_prod", "_trade"))
        .merge(centroids[["country", "lat", "lon"]], on="country", how="left")
    )

    if not elev.empty and {"country", "representative_elevation_m"}.issubset(elev.columns):
        stage = stage.merge(
            elev[["country", "representative_elevation_m"]],
            on="country",
            how="left",
        )
    else:
        stage["representative_elevation_m"] = pd.NA

    stage["normalized_route_weight"] = stage["normalized_route_weight"].fillna(0.0)
    stage["import_value_or_quantity"] = stage["import_value_or_quantity"].fillna(0.0)

    if "region_prod" in stage.columns:
        stage["region"] = stage["region_prod"]
    elif "region" not in stage.columns and "region_trade" in stage.columns:
        stage["region"] = stage["region_trade"]
    stage["region"] = stage["region"].fillna("Unknown")
    stage["color"] = stage["region"].apply(
        lambda x: REGION_COLORS.get(x, REGION_COLORS["Unknown"])
    )

    stage = stage.dropna(subset=["lat", "lon"]).copy()
    return stage

