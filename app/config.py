from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
EXTERNAL_DIR = DATA_DIR / "external"

# GMTED2010 clips (``scripts/06_gmted2010_study_elevation.py``)
GMTED_ELEVATION_DIR = RAW_DIR / "elevation"

# Cup-quality features (01/02 pipeline)
COFFEE_FEATURES_PATH = PROCESSED_DIR / "coffee_features.csv"

# Stage 1 inputs (ingested, app-ready)
PRODUCTION_PATH = PROCESSED_DIR / "stage1_country_production.csv"
US_IMPORT_PATH = PROCESSED_DIR / "stage1_us_imports_by_origin.csv"
CENTROIDS_PATH = PROCESSED_DIR / "stage1_country_centroids.csv"
GEOMETRY_PATH = PROCESSED_DIR / "stage1_countries.geojson"
ELEVATION_CONTEXT_PATH = EXTERNAL_DIR / "country_elevation_context.csv"

# Stage 2 illustrative coffee-growing samples (``scripts/07_stage2_growing_points.py``)
STAGE2_GROWING_POINTS_PATH = PROCESSED_DIR / "stage2_country_growing_points.csv"

# Landing U.S. macro time series (``scripts/08_landing_us_timeseries.py``)
US_COFFEE_IMPORTS_TIMESERIES_PATH = PROCESSED_DIR / "us_coffee_imports_timeseries.csv"
US_COFFEE_STOREFRONTS_TIMESERIES_PATH = PROCESSED_DIR / "us_coffee_storefronts_timeseries.csv"

# Map target location (continental US centroid-ish)
US_TARGET = {
    "country": "United States",
    "lat": 39.8283,
    "lon": -98.5795,
}

# Region color palette (RGB)
REGION_COLORS = {
    # Tuned for legibility on dark basemap
    "Americas": [232, 111, 81],
    "Africa": [88, 196, 134],
    "Asia-Pacific": [104, 162, 255],
    "Unknown": [150, 150, 150],
}

# Browser tab / Streamlit ``page_icon`` (``assets/favicon.svg``).
FAVICON_PATH = PROJECT_ROOT / "assets" / "favicon.svg"

# Stage-1 landing map mode switch:
# - "interactive_backup": current pydeck baseline (default)
# - "backup_image": static fallback image
MAP_MODE = "interactive_backup"
MAP_BACKUP_IMAGE_PATH = PROJECT_ROOT / "assets" / "map_backup_current.png"


def streamlit_page_icon() -> str:
    """Path for ``st.set_page_config(page_icon=...)`` or emoji fallback."""
    if FAVICON_PATH.is_file():
        return str(FAVICON_PATH.resolve())
    return "☕"

