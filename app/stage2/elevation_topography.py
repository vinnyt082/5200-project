"""
GMTED2010 clipped rasters: regional topography explorer (Streamlit).

Expects GeoTIFFs from ``scripts/06_gmted2010_study_elevation.py`` under
``data/raw/elevation/gmted2010_mn15_{ISO3}.tif`` (mean 15 arc-second).
"""

from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, List, Optional, Tuple

import geopandas as gpd
import numpy as np
import pandas as pd
import streamlit as st

from app.config import (
    EXTERNAL_DIR,
    GEOMETRY_PATH,
    GMTED_ELEVATION_DIR,
    STAGE2_GROWING_POINTS_PATH,
)
from app.stage2.region_shell import REGION_META

COUNTRY_CSV = EXTERNAL_DIR / "country_to_region.csv"

# CSV (lowercase) -> Natural Earth / GeoJSON ``country`` label
CSV_NAME_TO_GEOJSON: Dict[str, str] = {
    "tanzania, united republic of": "Tanzania",
}


@st.cache_data(show_spinner=False)
def _growing_points_table(path_str: str, mtime: float) -> pd.DataFrame:
    """Cached load of Stage 2 illustrative growing-location samples."""
    p = Path(path_str)
    if not p.is_file():
        return pd.DataFrame()
    return pd.read_csv(p)


def growing_points_for_country(country_label: str) -> pd.DataFrame:
    """Rows from ``stage2_country_growing_points.csv`` for one GeoJSON country label."""
    if not STAGE2_GROWING_POINTS_PATH.is_file():
        return pd.DataFrame()
    mtime = STAGE2_GROWING_POINTS_PATH.stat().st_mtime
    df = _growing_points_table(str(STAGE2_GROWING_POINTS_PATH.resolve()), mtime)
    if df.empty or "country" not in df.columns:
        return pd.DataFrame()
    return df[df["country"].astype(str) == country_label].copy()


def _is_usa(name_lower: str) -> bool:
    return name_lower.startswith("united states")


@lru_cache(maxsize=1)
def _country_to_iso3() -> Dict[str, str]:
    if not GEOMETRY_PATH.exists():
        return {}
    gdf = gpd.read_file(GEOMETRY_PATH)
    if "country" not in gdf.columns or "iso3" not in gdf.columns:
        return {}
    out: Dict[str, str] = {}
    for _, row in gdf.iterrows():
        out[str(row["country"])] = str(row["iso3"]).upper()
    return out


def _gmted_prefix() -> Optional[str]:
    """Detect mn15 (mean) or md15 (median) from files on disk."""
    if not GMTED_ELEVATION_DIR.exists():
        return None
    if list(GMTED_ELEVATION_DIR.glob("gmted2010_mn15_*.tif")):
        return "gmted2010_mn15"
    if list(GMTED_ELEVATION_DIR.glob("gmted2010_md15_*.tif")):
        return "gmted2010_md15"
    return None


def countries_with_topography(region: str) -> List[dict]:
    """
    Rows: { "label", "geojson_country", "iso3", "path" } sorted by label.
    ``path`` is None if no GeoTIFF exists for that ISO3.
    """
    if not COUNTRY_CSV.exists():
        return []
    df = pd.read_csv(COUNTRY_CSV)
    df = df[df["region"].astype(str) == region].copy()
    iso_map = _country_to_iso3()
    prefix = _gmted_prefix()
    rows: List[dict] = []
    for raw in df["country"].astype(str):
        key = raw.strip().lower()
        if _is_usa(key):
            continue
        gj_name = CSV_NAME_TO_GEOJSON.get(key, raw.strip().title())
        iso3 = iso_map.get(gj_name, "")
        slug = "".join(c if c.isalnum() else "_" for c in gj_name)[:12]
        path = None
        if prefix:
            candidates: List[Path] = []
            if iso3 and iso3 != "-99" and len(iso3) == 3:
                candidates.append(GMTED_ELEVATION_DIR / f"{prefix}_{iso3.upper()}.tif")
            candidates.append(GMTED_ELEVATION_DIR / f"{prefix}_{slug}.tif")
            for cand in candidates:
                if cand.is_file():
                    path = cand
                    break
        rows.append(
            {
                "label": gj_name,
                "geojson_country": gj_name,
                "iso3": iso3 if iso3 and iso3 != "-99" else slug,
                "path": path,
            }
        )
    rows.sort(key=lambda r: r["label"])
    return rows


def _land_dem_colormap():
    """
    Light-footprint DEM ramp: pale floor (lowlands) → greens → tans/browns (highlands).
    Tuned so 0–2000 m occupies most of the perceptual range (coffee origins).
    """
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap

    colors = [
        "#f7fafc",
        "#e3eef6",
        "#c5e3d1",
        "#7ec699",
        "#4a9d6f",
        "#b0a373",
        "#8b7355",
        "#e8e0d8",
    ]
    return LinearSegmentedColormap.from_list("coffee_dem", colors, N=256)


def _load_dem_stack(path: Path, max_dim: int = 3200) -> SimpleNamespace:
    """Read, downsample, and normalize elevation grid (shared by the hillshade renderer)."""
    import rasterio
    from rasterio.transform import Affine

    with rasterio.open(path) as src:
        arr = src.read(1).astype(np.float64)
        nd = src.nodata
        if nd is not None:
            arr[arr == float(nd)] = np.nan
        tr = src.transform
        bounds = src.bounds
        crs = src.crs

    h, w = arr.shape
    step = max(1, int(math.ceil(max(h, w) / max_dim)))
    if step > 1:
        arr = arr[::step, ::step]
        tr = tr * Affine.scale(step, step)

    mask_valid = np.isfinite(arr)
    valid = arr[mask_valid]
    if valid.size == 0:
        raise ValueError("No valid elevation pixels in raster.")

    p_lo = float(np.percentile(valid, 2))
    p_hi = float(np.percentile(valid, 98))
    z_min = min(0.0, p_lo)
    z_max = float(min(2600.0, max(2000.0, p_hi * 1.05)))
    if z_max - z_min < 400:
        z_max = z_min + 900

    z_plot = np.where(mask_valid, arr, z_min)
    mid_lat = (bounds.top + bounds.bottom) / 2.0
    m_lon = 111_320.0 * math.cos(math.radians(mid_lat))
    m_lat = 110_574.0
    dx = abs(tr.a) * m_lon
    dy = abs(tr.e) * m_lat

    return SimpleNamespace(
        arr=arr,
        mask_valid=mask_valid,
        bounds=bounds,
        transform=tr,
        crs=crs,
        z_min=z_min,
        z_max=z_max,
        z_plot=z_plot,
        dx=dx,
        dy=dy,
        step=step,
        h=arr.shape[0],
        w=arr.shape[1],
    )


@st.cache_data(show_spinner=False)
def _topography_figure(
    path_str: str,
    mtime: float,
    agg_label: str,
    max_dim: int = 3200,
    viz_rev: int = 4,
    overlay_country: str = "",
    growing_points_path: str = "",
    growing_points_mtime: float = -1.0,
):
    """Build matplotlib hillshade figure (cached by file path + mtime)."""
    import matplotlib.pyplot as plt
    from matplotlib.colors import LightSource
    from matplotlib.cm import ScalarMappable

    path = Path(path_str)
    dem = _load_dem_stack(path, max_dim=max_dim)
    mask_valid = dem.mask_valid
    bounds = dem.bounds
    crs = dem.crs
    z_min = dem.z_min
    z_max = dem.z_max
    z_plot = dem.z_plot
    dx = dem.dx
    dy = dem.dy
    step = dem.step

    cmap = _land_dem_colormap()

    ls = LightSource(azdeg=315, altdeg=50)
    rgb = ls.shade(
        z_plot,
        cmap=cmap,
        vert_exag=1.05,
        blend_mode="soft",
        dx=dx,
        dy=dy,
        vmin=z_min,
        vmax=z_max,
    )

    fig, ax = plt.subplots(figsize=(10.5, 6.2), dpi=120)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")
    for spine in ax.spines.values():
        spine.set_edgecolor("#9aa3ad")
        spine.set_linewidth(0.8)

    extent = (bounds.left, bounds.right, bounds.bottom, bounds.top)
    rgb_display = np.array(rgb, dtype=float, copy=True)
    if rgb_display.ndim == 3:
        invalid = ~mask_valid
        if rgb_display.shape[2] >= 3:
            rgb_display[invalid, :3] = 1.0
            if rgb_display.shape[2] == 4:
                rgb_display[invalid, 3] = 1.0

    ax.imshow(rgb_display, extent=extent, origin="upper", interpolation="bilinear")
    try:
        outline = plt.contour(
            mask_valid.astype(float),
            levels=[0.5],
            colors=[(0.129, 0.588, 0.953, 0.55)],
            linewidths=0.8,
            extent=extent,
            origin="upper",
        )
        for c in outline.collections:
            c.set_clip_on(True)
    except Exception:
        pass

    if overlay_country and growing_points_mtime >= 0.0 and growing_points_path:
        gp = _growing_points_table(growing_points_path, growing_points_mtime)
        if not gp.empty and {"longitude", "latitude"}.issubset(gp.columns):
            sub = gp[gp["country"].astype(str) == overlay_country]
            if not sub.empty:
                lon = sub["longitude"].to_numpy(dtype=float)
                lat = sub["latitude"].to_numpy(dtype=float)
                in_extent = (
                    (lon >= bounds.left)
                    & (lon <= bounds.right)
                    & (lat >= bounds.bottom)
                    & (lat <= bounds.top)
                )
                lon = lon[in_extent]
                lat = lat[in_extent]
                if lon.size > 0:
                    if "point_weight" in sub.columns:
                        w = sub["point_weight"].to_numpy(dtype=float)[in_extent]
                        w = np.clip(np.nan_to_num(w, nan=0.45), 0.08, 1.0)
                    else:
                        w = np.full(lon.shape, 0.45)
                    sizes = 6.0 + 20.0 * w
                    ax.scatter(
                        lon,
                        lat,
                        s=sizes,
                        c="#000000",
                        alpha=0.8,
                        linewidths=0,
                        zorder=6,
                        label=None,
                    )

    ax.set_xlim(bounds.left, bounds.right)
    ax.set_ylim(bounds.bottom, bounds.top)
    ax.set_aspect("equal")
    ax.set_xlabel("Longitude (°)", color="#374151")
    ax.set_ylabel("Latitude (°)", color="#374151")
    ax.tick_params(colors="#4b5563")
    title_country = overlay_country or "Selected country"
    ax.set_title(
        f"Elevation map — {title_country}",
        fontsize=13,
        pad=12,
        color="#111827",
    )

    sm = ScalarMappable(
        cmap=cmap,
        norm=plt.Normalize(vmin=z_min, vmax=z_max, clip=True),
    )
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, fraction=0.035, pad=0.02)
    cbar.set_label("Elevation (m, stretched for 0–2000 m band)", fontsize=10, color="#374151")
    cbar.ax.tick_params(colors="#4b5563")

    ax.grid(True, color="#e5e7eb", linestyle="-", linewidth=0.6, alpha=1.0)
    fig.text(
        0.5,
        0.01,
        f"CRS: {crs} · ~{dx:.0f} × {dy:.0f} m/pixel (display)"
        + (f" · downsampled ×{step}" if step > 1 else ""),
        ha="center",
        fontsize=8.5,
        color="#6b7280",
    )
    fig.subplots_adjust(bottom=0.12, top=0.9, left=0.07, right=0.97)
    return fig


def _subsample_elevations_for_hist(values: np.ndarray, *, max_points: int = 500_000) -> np.ndarray:
    """Deterministic thinning so large rasters stay responsive in Plotly."""
    if values.size <= max_points:
        return values
    step = int(np.ceil(values.size / max_points))
    return values[::step]


@st.cache_data(show_spinner=False)
def _cached_dem_elevations_1d(path_str: str, mtime: float, max_dim: int = 3200) -> np.ndarray:
    """Valid elevation pixels (same downsampling as hillshade) for histograms."""
    dem = _load_dem_stack(Path(path_str), max_dim=max_dim)
    return dem.arr[dem.mask_valid].astype(np.float32, copy=False)


def _elevation_histogram_figure(values: np.ndarray, *, country: str):
    """Plotly histogram aligned with the GMTED clip for the selected country."""
    import plotly.graph_objects as go

    from app.plotly_theme import plotly_layout_base

    v = _subsample_elevations_for_hist(values)
    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=v,
            nbinsx=72,
            marker=dict(color="#6eb896", line=dict(width=0)),
            opacity=0.92,
            hovertemplate="Elevation (m): %{x:.0f}<br>Pixel count: %{y}<extra></extra>",
        )
    )
    fig.update_layout(
        title=dict(
            text=f"Elevation distribution in clip — {country}",
            font=dict(size=14, color="#e2e8f0"),
        ),
        xaxis=dict(title=dict(text="Elevation (m)", font=dict(color="#94a3b8")), gridcolor="#1e293b", zeroline=False),
        yaxis=dict(
            title=dict(text="Pixels (downsampled grid)", font=dict(color="#94a3b8")),
            gridcolor="#1e293b",
            zeroline=False,
        ),
        **plotly_layout_base(height=300),
    )
    return fig


def _stats_block(path: Path) -> Tuple[str, dict]:
    import rasterio

    with rasterio.open(path) as src:
        arr = src.read(1).astype(np.float64)
        nd = src.nodata
        if nd is not None:
            arr[arr == float(nd)] = np.nan
        valid = arr[np.isfinite(arr)]
        if valid.size == 0:
            return "No valid elevation pixels in this clip.", {}
        stats = {
            "min_m": float(np.nanmin(valid)),
            "max_m": float(np.nanmax(valid)),
            "mean_m": float(np.nanmean(valid)),
            "p10_m": float(np.percentile(valid, 10)),
            "p90_m": float(np.percentile(valid, 90)),
            "pixels": int(np.sum(np.isfinite(arr))),
        }
    txt = (
        f"**Pixel summary (clipped GMTED):** min {stats['min_m']:.0f} m · max {stats['max_m']:.0f} m · "
        f"mean {stats['mean_m']:.0f} m · middle band (10–90%) {stats['p10_m']:.0f}–{stats['p90_m']:.0f} m."
    )
    return txt, stats


def render_regional_topography_explorer(region: str, *, compact_vertical: bool = False) -> None:
    """
    Dropdown of study countries in ``region`` + hillshade-style map + narrative.

    ``compact_vertical``: when True (Americas layout pass), slightly tighter vertical rhythm
    between the terrain header, map, histogram, and follow-on text.
    """
    meta = REGION_META.get(region, {})
    accent = meta.get("accent", "#888888")
    prefix = _gmted_prefix() or ""
    agg_word = "median" if "md15" in prefix else "mean"
    agg_title = agg_word.capitalize()

    if region in ("Americas", "Africa", "Asia-Pacific"):
        sub_kicker, sub_title = "Terrain", "Terrain and growing regions"
    else:
        sub_kicker, sub_title = "Topography", "Terrain and coffee-growing concentration"
    hdr_margin = "5px 0 7px 0" if compact_vertical else "8px 0 14px 0"
    st.markdown(
        f"""
<div style="border-left:3px solid {accent}; padding-left:12px; margin: {hdr_margin};">
  <div style="font-size:0.78rem; letter-spacing:0.06em; text-transform:uppercase; color:#7a8290;">
    {sub_kicker}</div>
  <div style="font-size:1.05rem; font-weight:600; color:#e8ecf1;">{sub_title}</div>
</div>
        """,
        unsafe_allow_html=True,
    )
    if compact_vertical:
        st.markdown(
            '<div style="margin:0;padding:0;height:0;line-height:0;font-size:0;margin-top:-0.22rem" aria-hidden="true"></div>',
            unsafe_allow_html=True,
        )

    rows = countries_with_topography(region)
    if not rows:
        st.info("No country list found for this region (`country_to_region.csv`).")
        return

    available = [r for r in rows if r["path"] is not None]
    if not available:
        st.warning(
            "No GMTED2010 GeoTIFFs found under `data/raw/elevation/`. "
            "Run `python scripts/06_gmted2010_study_elevation.py --aggregation mean` "
            "to build per-country clips, then refresh this page."
        )
        return

    labels = [r["label"] for r in available]
    choice = st.selectbox(
        "Country",
        options=labels,
        index=0,
        key=f"gmted_topography_{region}",
        help=f"Polygon-clipped GMTED2010 ({agg_title}) for each origin in this region.",
    )
    row = next(r for r in available if r["label"] == choice)
    path: Path = row["path"]  # type: ignore
    overlay_pts = growing_points_for_country(choice)

    if region == "Americas":
        explorer_intro = f"""
National-scale terrain for **{choice}**—ridges, basins, uplands in one frame. Black points mark representative coffee-growing
samples; they cluster uphill, not on the flattest country-wide average. Not farm GPS—just a clearer read of the land behind the label.
        """
    elif region == "Africa":
        explorer_intro = f"""
National-scale terrain for **{choice}**—ridges, escarpments, plateaus, basins in one frame. Black points mark representative
coffee-growing samples; they cluster in uplands and broken relief, not on the flattest country-wide average. Not farm GPS—just a clearer read of the land behind the trade name.
        """
    elif region == "Asia-Pacific":
        explorer_intro = f"""
National-scale terrain for **{choice}**—islands, coasts, volcanic belts, interior uplands in one frame. Black points mark representative
coffee-growing samples; they cluster on island highs, volcanic slopes, escarpments, and broken interior belts rather than the widest lowland averages. Not farm GPS—just a clearer read of the land behind the trade name.
        """
    else:
        explorer_intro = f"""
The elevation map shows the broad vertical structure of **{choice}**—coasts, valleys, plateaus, and
mountain systems in one consistent view. Black dots mark representative coffee-growing region
samples, which cluster where terrain is typically higher and more broken than the country-wide
average. They are not verified farm coordinates, but they help connect coffee geography to the land
shape you see on the map.
        """
    st.markdown(explorer_intro)
    if compact_vertical:
        st.markdown(
            '<div style="margin:0;padding:0;height:0;line-height:0;font-size:0;margin-top:-0.32rem" aria-hidden="true"></div>',
            unsafe_allow_html=True,
        )

    try:
        import matplotlib.pyplot as plt

        mtime = path.stat().st_mtime
        gp_path = STAGE2_GROWING_POINTS_PATH
        gp_mtime = float(gp_path.stat().st_mtime) if gp_path.is_file() else -1.0
        fig = _topography_figure(
            str(path.resolve()),
            mtime,
            agg_title,
            viz_rev=4,
            overlay_country=choice,
            growing_points_path=str(gp_path.resolve()) if gp_path.is_file() else "",
            growing_points_mtime=gp_mtime,
        )
        st.pyplot(fig, clear_figure=True, use_container_width=True)
        plt.close(fig)
        if compact_vertical:
            st.markdown(
                '<div style="margin:0;padding:0;height:0;line-height:0;font-size:0;margin-top:-0.48rem" aria-hidden="true"></div>',
                unsafe_allow_html=True,
            )

        from app.plotly_theme import PLOTLY_CONFIG

        elev_1d = _cached_dem_elevations_1d(str(path.resolve()), mtime, max_dim=3200)
        if elev_1d.size > 0:
            fig_hist = _elevation_histogram_figure(elev_1d, country=choice)
            if region in ("Americas", "Africa", "Asia-Pacific"):
                fig_hist.update_layout(
                    title=dict(
                        text=f"Land by elevation in this clip — {choice}",
                        font=dict(size=14, color="#e2e8f0"),
                    ),
                    yaxis=dict(
                        title=dict(text="Land area at elevation (pixels)", font=dict(color="#94a3b8")),
                        gridcolor="#1e293b",
                        zeroline=False,
                    ),
                )
            if compact_vertical:
                fig_hist.update_layout(
                    height=268,
                    margin=dict(l=52, r=22, t=40, b=40),
                    title=dict(font=dict(size=13, color="#e2e8f0")),
                )
            slug = "".join(c if c.isalnum() else "_" for c in choice)[:24]
            st.plotly_chart(
                fig_hist,
                use_container_width=True,
                key=f"gmted_elev_hist_{region}_{slug}",
                config=PLOTLY_CONFIG,
            )
            if compact_vertical:
                st.markdown(
                    '<div style="margin:0;padding:0;height:0;line-height:0;font-size:0;margin-top:-0.38rem" aria-hidden="true"></div>',
                    unsafe_allow_html=True,
                )
            if region == "Americas":
                st.caption(
                    "Same clip as the map: each bar is how much land in this grid sits near that elevation—"
                    "a quick lowland-versus-upland read."
                )
            elif region == "Africa":
                st.caption(
                    "Same clip as the map: each bar is land near that elevation—a quick read of low ground versus upland footprint."
                )
            elif region == "Asia-Pacific":
                st.caption(
                    "Same clip as the map: land near each elevation—useful for seeing whether coffee sits in narrow upland spines "
                    "or inside a broader elevated footprint."
                )
            else:
                st.caption(
                    "Linked to the country dropdown above: same GMTED clip and display downsampling as the map. "
                    "Counts are pixels on that grid, not a full-resolution census."
                )
    except ImportError:
        st.error("Install `rasterio` and `matplotlib` to render topography (`pip install rasterio`).")
        return
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not render topography: {exc}")
        return

    stats_md, stats = _stats_block(path)
    if region == "Americas" and stats:
        stats_md = (
            f"**In this clip,** most of **{choice}** sits between about **{stats['p10_m']:.0f} m** and "
            f"**{stats['p90_m']:.0f} m**—the grid's broad middle—while extremes run **{stats['min_m']:.0f}–"
            f"{stats['max_m']:.0f} m**. Large countries can hide narrow upland belts where coffee actually concentrates inside a "
            "much wider lowland footprint."
        )
    elif region == "Africa" and stats:
        stats_md = (
            f"**In this clip,** much of **{choice}** sits between about **{stats['p10_m']:.0f} m** and "
            f"**{stats['p90_m']:.0f} m**, with extremes near **{stats['min_m']:.0f}–{stats['max_m']:.0f} m**. "
            "“African highland coffee” can sound singular in the market while the land behind the label stays internally uneven—"
            "escarpments, basins, upland pockets, and broader elevated belts under one flag."
        )
    elif region == "Asia-Pacific" and stats:
        stats_md = (
            f"**In this clip,** much of **{choice}** sits between about **{stats['p10_m']:.0f} m** and "
            f"**{stats['p90_m']:.0f} m**, with extremes near **{stats['min_m']:.0f}–{stats['max_m']:.0f} m**. "
            "That spread is the point: one country name can hold coast, interior upland, volcanic slope, and island ridge at once."
        )
    if compact_vertical and region == "Americas":
        st.markdown(
            '<div style="margin:0;padding:0;height:0;line-height:0;font-size:0;margin-top:-0.2rem" aria-hidden="true"></div>',
            unsafe_allow_html=True,
        )
        st.markdown(f'<div class="americas-terrain-stats">{stats_md}</div>', unsafe_allow_html=True)
    else:
        st.markdown(stats_md)

    if region == "Americas":
        hist_note = f"""
The histogram tracks how much of **{choice}** sits low versus high, not only where relief peaks. With the map, it helps explain why a country label stays useful and still blunt: coffee often sits in a tighter upland band than the bag suggests.
        """
        if compact_vertical:
            st.markdown(f'<div class="americas-terrain-foot">{hist_note}</div>', unsafe_allow_html=True)
        else:
            st.markdown(hist_note)
    elif region == "Africa":
        st.markdown(
            f"""
Whether **{choice}** reads as **low ground with coffee tucked uphill** or a **wider elevated footprint**, the histogram tracks how
much land sits low versus high, not peaks alone. With the map, internal geography reads clearer—and it is easier to see why “Africa” is too broad for one elevation story.
            """
        )
    elif region == "Asia-Pacific":
        st.markdown(
            f"""
The histogram asks whether **{choice}** reads as **mostly low ground with coffee pushed into spines and slopes** or a
**broader high footprint**. With the map, uneven terrain becomes clearer—and so does why one country label can hold several land stories at once.
            """
        )
    else:
        st.markdown(
            f"""
Color and hillshade are tuned so the 0–2000 m band stays readable while preserving higher peaks.
Use this view together with the supporting charts below: the map shows where relief concentrates,
while lot-altitude and country-context charts quantify those elevation patterns from different angles.
            """
        )

    # Operational hint for missing overlay rows (hidden on Americas / Africa / Asia-Pacific narrative pass).
    if region not in ("Americas", "Africa", "Asia-Pacific") and STAGE2_GROWING_POINTS_PATH.is_file() and overlay_pts.empty:
        st.caption(
            "Growing-location overlay CSV is present but has no rows for this country—re-run "
            "`python scripts/07_stage2_growing_points.py` after updating study countries."
        )

    # Technical note hidden on regional narrative pages; other callers still see the expander.
    if region not in ("Americas", "Africa", "Asia-Pacific"):
        with st.expander("Technical note"):
            st.markdown(
                f"""
- Source: GMTED2010 global **{agg_word}** grid (`{'md15' if agg_word == 'median' else 'mn15'}_grd.zip`)
  via USGS `edcintl.cr.usgs.gov`, clipped with `rasterio.mask` to each study country polygon from
  `stage1_countries.geojson`.
- Vertical exaggeration in shading is modest so large countries remain interpretable.
- The app auto-detects `gmted2010_mn15_*.tif` vs. `gmted2010_md15_*.tif` in `data/raw/elevation/`.
- **Growing-location overlay:** `data/processed/stage2_country_growing_points.csv` from
  `scripts/07_stage2_growing_points.py`. Columns include `point_source_type` (e.g.
  `elevation_constrained_sample` vs `illustrative_fallback`) and `point_weight` (relative marker
  size within the country, derived from sampled elevation spread—not trade volume). Optional verified
  rows can be merged from `data/external/manual_growing_points.csv` as `exact_location_match`.
                """
            )
