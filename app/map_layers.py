from __future__ import annotations

import json

import pandas as pd
import pydeck as pdk

from app.config import GEOMETRY_PATH, REGION_COLORS, US_TARGET
from app.route_experiment import (
    build_feeder_paths,
    build_structural_feeders,
    build_trunk_path_dataframe,
)


def _path_layer_records(df) -> list[dict]:
    """PathLayer rows as plain dicts so nested ``path`` survives Streamlit/pydeck JSON."""
    rows = []
    for rec in df.to_dict("records"):
        path = rec.get("path") or []
        clean_path = [
            [float(p[0]), float(p[1])]
            for p in path
            if p is not None and len(p) >= 2
        ]
        if len(clean_path) < 2:
            continue
        out = {**rec, "path": clean_path}
        if "width_pixels" in out:
            out["width_pixels"] = float(out["width_pixels"])
        rows.append(out)
    return rows


def _shift_geometry_longitude(geom: dict, delta_lon: float) -> dict:
    """Return geometry with all longitudes shifted by ``delta_lon`` degrees."""
    if not geom:
        return geom
    gtype = geom.get("type")
    coords = geom.get("coordinates")
    if coords is None:
        return geom

    def _shift(node):
        if isinstance(node, (list, tuple)) and node and isinstance(node[0], (int, float)):
            if len(node) >= 2:
                out = list(node)
                out[0] = float(out[0]) + float(delta_lon)
                return out
            return list(node)
        if isinstance(node, (list, tuple)):
            return [_shift(x) for x in node]
        return node

    return {"type": gtype, "coordinates": _shift(coords)}


def _duplicate_feature_collection_longitude(
    feature_collection: dict, deltas: tuple[float, ...] = (-360.0, 0.0, 360.0)
) -> dict:
    """Duplicate GeoJSON FeatureCollection with longitude-shifted copies."""
    if not feature_collection:
        return feature_collection
    feats = feature_collection.get("features", [])
    out_feats = []
    for delta in deltas:
        for feat in feats:
            geom = feat.get("geometry")
            shifted = _shift_geometry_longitude(geom, delta)
            out_feats.append(
                {
                    "type": "Feature",
                    "geometry": shifted,
                    "properties": feat.get("properties", {}),
                }
            )
    return {"type": "FeatureCollection", "features": out_feats}


def _duplicate_rows_longitude(
    rows: list[dict], *, point_keys: tuple[str, str] = ("lon", "lat"), deltas: tuple[float, ...] = (-360.0, 0.0, 360.0)
) -> list[dict]:
    """
    Duplicate dict rows for seam visibility:
    - point rows with ``lon``/``lat``
    - path rows with ``path`` list of [lon, lat]
    """
    out: list[dict] = []
    lon_key, lat_key = point_keys
    for delta in deltas:
        for row in rows:
            rec = dict(row)
            if "path" in rec and rec["path"]:
                rec["path"] = [[float(p[0]) + delta, float(p[1])] for p in rec["path"]]
            elif lon_key in rec and lat_key in rec:
                rec[lon_key] = float(rec[lon_key]) + delta
                rec[lat_key] = float(rec[lat_key])
            out.append(rec)
    return out


def build_map_layers(df, show_routes: bool, metric: str):
    """
    Build pydeck layers for Stage 1 landing view.

    metric:
      - "Production"
      - "U.S. import relevance"
      - "Elevation context"
    """
    working = df.copy()
    geometry_obj = None
    if GEOMETRY_PATH.exists():
        with GEOMETRY_PATH.open("r", encoding="utf-8") as f:
            geometry_obj = json.load(f)

    if metric == "Production":
        scale_col = "production_tonnes_latest"
    elif metric == "U.S. import relevance":
        scale_col = "normalized_route_weight"
    else:
        scale_col = "representative_elevation_m"

    scaled = working[scale_col].fillna(0.0)
    max_val = float(scaled.max()) if len(scaled) else 1.0
    if max_val <= 0:
        max_val = 1.0
    # Restrained point sizing to keep the landing map readable.
    working["point_radius"] = 15000 + (scaled / max_val) * 90000

    # Subtle world geography grounding layer (kept low contrast).
    layers = []
    if geometry_obj:
        world_fc = _duplicate_feature_collection_longitude(geometry_obj)
        world = pdk.Layer(
            "GeoJsonLayer",
            data=world_fc,
            stroked=True,
            filled=True,
            get_fill_color=[34, 39, 47, 140],
            get_line_color=[95, 105, 118, 110],
            line_width_min_pixels=0.45,
            pickable=False,
            wrap_longitude=True,
        )
        layers.append(world)

        # Producer-country highlight layer:
        # low-opacity regional tint for countries represented in the story.
        producer_features = []
        country_region = {
            row["country"]: row["region"]
            for _, row in working[["country", "region"]].drop_duplicates().iterrows()
        }
        for feature in geometry_obj.get("features", []):
            props = feature.get("properties", {})
            country_name = props.get("country") or props.get("NAME")
            # U.S. destination: same yellow family as the anchor marker, not a producer region.
            if country_name == US_TARGET["country"]:
                producer_features.append(
                    {
                        "type": "Feature",
                        "geometry": feature.get("geometry"),
                        "properties": {
                            "country": country_name,
                            "region": "U.S. market",
                            "fillColor": [255, 226, 135, 52],
                            "lineColor": [255, 226, 135, 96],
                        },
                    }
                )
                continue
            if country_name not in country_region:
                continue
            region = country_region[country_name]
            base_color = REGION_COLORS.get(region, REGION_COLORS["Unknown"])
            producer_feature = {
                "type": "Feature",
                "geometry": feature.get("geometry"),
                "properties": {
                    "country": country_name,
                    "region": region,
                    "fillColor": [base_color[0], base_color[1], base_color[2], 48],
                    "lineColor": [base_color[0], base_color[1], base_color[2], 92],
                },
            }
            producer_features.append(producer_feature)

        if producer_features:
            producer_fc = {"type": "FeatureCollection", "features": producer_features}
            producer_fc = _duplicate_feature_collection_longitude(producer_fc)
            producer_polygons = pdk.Layer(
                "GeoJsonLayer",
                data=producer_fc,
                stroked=True,
                filled=True,
                get_fill_color="properties.fillColor",
                get_line_color="properties.lineColor",
                line_width_min_pixels=0.55,
                pickable=False,
                wrap_longitude=True,
            )
            layers.append(producer_polygons)

    # Route experiment: PathLayer replaces ArcLayer. Geometry lives in
    # ``app/route_experiment.py`` (trunk polylines + per-origin feeders). Tune there.
    # Draw order: structural + country feeders → ribbon outer → ribbon body → ribbon core.
    # Americas: core-only; AP/Africa: three-tier editorial flow ribbons.
    # Rendered under origin points / U.S. anchor so markers stay legible.
    if show_routes:
        route_df = working[working["normalized_route_weight"] > 0].copy()
        if not route_df.empty:
            # Match trunk geometry to the same regions as the filtered country table
            # (sidebar "Region" filter); feeders already come from ``route_df``.
            route_regions = set(route_df["region"].dropna().astype(str).unique())
            trunk_df = build_trunk_path_dataframe(regions=route_regions)
            struct_df = build_structural_feeders(regions=route_regions)
            feeder_df = build_feeder_paths(route_df)
            if not struct_df.empty:
                feeder_df = pd.concat([struct_df, feeder_df], ignore_index=True)
            # Streamlit's pydeck path often serializes nested columns incorrectly when
            # passing a pandas DataFrame; plain dict rows keep ``path`` as JSON arrays.
            feeder_rows = _path_layer_records(feeder_df)
            trunk_rows = _path_layer_records(trunk_df)
            feeder_rows = _duplicate_rows_longitude(feeder_rows)
            trunk_rows = _duplicate_rows_longitude(trunk_rows)
            if feeder_rows:
                layers.append(
                    pdk.Layer(
                        "PathLayer",
                        data=feeder_rows,
                        get_path="path",
                        get_color="color",
                        get_width="width_pixels",
                        width_units="pixels",
                        cap_rounded=True,
                        joint_rounded=True,
                        width_min_pixels=1.5,
                        width_max_pixels=7,
                        opacity=0.48,
                        pickable=True,
                        wrap_longitude=True,
                    )
                )
            trunk_tiers = [
                ("ribbon_outer", 0.13, 8, 30),
                ("ribbon_body", 0.28, 5, 20),
                ("ribbon_core", 0.76, 2.0, 11),
            ]
            for tier, opacity, wmin, wmax in trunk_tiers:
                tier_rows = [r for r in trunk_rows if r.get("layer") == tier]
                if not tier_rows:
                    continue
                layers.append(
                    pdk.Layer(
                        "PathLayer",
                        data=tier_rows,
                        get_path="path",
                        get_color="color",
                        get_width="width_pixels",
                        width_units="pixels",
                        cap_rounded=True,
                        joint_rounded=True,
                        width_min_pixels=wmin,
                        width_max_pixels=wmax,
                        opacity=opacity,
                        pickable=False,
                        wrap_longitude=True,
                    )
                )

    points = pdk.Layer(
        "ScatterplotLayer",
        data=_duplicate_rows_longitude(working.to_dict("records")),
        get_position=["lon", "lat"],
        get_fill_color="color",
        get_radius="point_radius",
        radius_min_pixels=4,
        radius_max_pixels=22,
        opacity=0.74,
        pickable=True,
        stroked=True,
        get_line_color=[205, 205, 205],
        line_width_min_pixels=1,
        wrap_longitude=True,
    )
    layers.append(points)

    # Clear U.S. destination anchor marker.
    us_anchor = pdk.Layer(
        "ScatterplotLayer",
        data=_duplicate_rows_longitude([{"lon": US_TARGET["lon"], "lat": US_TARGET["lat"]}]),
        get_position=["lon", "lat"],
        get_fill_color=[255, 226, 135],
        get_radius=170000,
        radius_min_pixels=8,
        radius_max_pixels=16,
        opacity=0.92,
        pickable=False,
        stroked=True,
        get_line_color=[255, 250, 230],
        line_width_min_pixels=1.4,
        wrap_longitude=True,
    )
    layers.append(us_anchor)

    return layers


def initial_view_state():
    return pdk.ViewState(
        latitude=18,
        longitude=-35,
        zoom=1.4,
        min_zoom=1,
        max_zoom=6,
        pitch=18,
        bearing=0,
    )

