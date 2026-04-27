"""
Stylized conceptual trade-flow paths for Stage 1 landing map (design experiment).

These are NOT literal shipping routes. Africa / Asia-Pacific trunks are rebuilt as
smooth flow ribbons (Chaikin-smoothed sparse controls + three-layer Path rendering).
Americas trunk is unchanged from the classic merge / Pacific arc description.
"""

from __future__ import annotations

from typing import List, Optional, Sequence, Set, Tuple

import pandas as pd

from app.config import REGION_COLORS

# --- U.S. entry anchors (conceptual landing zones, not ports) ----------------
# Americas + Asia-Pacific: shared stylized Pacific / West Coast landfall (SoCal).
US_WEST_COAST_LANDFALL: Tuple[float, float] = (-118.5, 33.8)  # SoCal corridor
# Africa: Atlantic / East Coast-facing U.S.
US_EAST_ENTRY: Tuple[float, float] = (-74.0, 40.2)  # NYC corridor

# --- Shared regional trunks (multi-segment polylines, lon/lat) ---------------
# Americas: merge in Central America, arc WNW over offshore Mexico / Baja, then
# into the same West Coast landfall as the Asia-Pacific corridor.
TRUNK_AMERICAS: List[Tuple[float, float]] = [
    (-86.0, 16.5),   # Central America merge (shared feeder target)
    (-93.5, 18.8),   # begin outward arc (WNW)
    (-101.0, 23.5),  # Mexican Pacific offshore bend
    (-109.5, 28.5),  # outer Baja / coastal approach
    (-115.5, 32.0),  # bend toward SoCal
    US_WEST_COAST_LANDFALL,
]


def _lerp(
    a: Tuple[float, float], b: Tuple[float, float], t: float
) -> Tuple[float, float]:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _dedupe_path(points: List[Tuple[float, float]], *, eps: float = 1e-5) -> List[Tuple[float, float]]:
    out: List[Tuple[float, float]] = []
    for p in points:
        if not out or abs(p[0] - out[-1][0]) > eps or abs(p[1] - out[-1][1]) > eps:
            out.append((float(p[0]), float(p[1])))
    return out


def _densify_polyline(
    points: Sequence[Tuple[float, float]], *, steps_per_segment: int = 8
) -> List[Tuple[float, float]]:
    """Insert evenly spaced vertices between control points (Bezier-like smoothness)."""
    pts = [tuple(map(float, p)) for p in points]
    if len(pts) < 2:
        return list(pts)
    steps = max(2, int(steps_per_segment))
    out: List[Tuple[float, float]] = [pts[0]]
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        for s in range(1, steps + 1):
            t = s / steps
            out.append(_lerp(a, b, t))
    return _dedupe_path(out)


def _chaikin_open(points: Sequence[Tuple[float, float]], iterations: int = 3) -> List[Tuple[float, float]]:
    """
    Chaikin corner-cutting on an open polyline (endpoints fixed in the limit).
    Produces smooth, editorial flow-curve geometry from very few control points.
    """
    pts: List[Tuple[float, float]] = [tuple(map(float, p)) for p in points]
    if len(pts) < 2:
        return pts
    for _ in range(max(1, iterations)):
        if len(pts) < 2:
            break
        n = len(pts)
        new_pts: List[Tuple[float, float]] = [pts[0]]
        for i in range(n - 1):
            p0, p1 = pts[i], pts[i + 1]
            q = (0.75 * p0[0] + 0.25 * p1[0], 0.75 * p0[1] + 0.25 * p1[1])
            r = (0.25 * p0[0] + 0.75 * p1[0], 0.25 * p0[1] + 0.75 * p1[1])
            new_pts.append(q)
            new_pts.append(r)
        new_pts.append(pts[-1])
        pts = _dedupe_path(new_pts, eps=1e-4)
    return pts


def _flow_ribbon(control_points: Sequence[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """Few intentional controls → Chaikin smooth → light densify for PathLayer."""
    smoothed = _chaikin_open(list(control_points), iterations=3)
    return _densify_polyline(smoothed, steps_per_segment=5)


# --- Asia-Pacific (hard reset): very few controls, smooth ribbon, ±180 seam.
# Collection west of Indonesia / Malaysia, one confident Pacific sweep, landfall SoCal.
_AP_WEST_CTRL: List[Tuple[float, float]] = [
    (114.2, 8.8),   # maritime SEA / western Indonesia collection
    (142.0, 13.5),  # open western Pacific
    (172.0, 22.5),  # mid-Pacific climb
    (179.38, 26.2),  # approach +180°
]
_AP_EAST_CTRL: List[Tuple[float, float]] = [
    (-179.38, 26.2),  # resume east of -180°
    (-148.0, 31.5),  # north-east Pacific
    US_WEST_COAST_LANDFALL,
]

TRUNK_ASIA_PACIFIC_WEST: List[Tuple[float, float]] = _flow_ribbon(_AP_WEST_CTRL)
TRUNK_ASIA_PACIFIC_EAST: List[Tuple[float, float]] = _flow_ribbon(_AP_EAST_CTRL)

# --- Africa (hard reset): five anchors — Horn collection → southern Indian Ocean →
# Cape band → Atlantic arc → U.S. East Coast (smooth ribbon, no busy interior zig-zag).
_AF_CTRL: List[Tuple[float, float]] = [
    (44.8, -3.6),  # Horn / western Indian Ocean head
    (41.2, -17.5),  # gentle south into the basin
    (40.0, -27.5),  # straight southerly run — no eastward jog toward Madagascar’s south
    (31.5, -35.8),  # WSW under Madagascar / Mozambique channel water; begins smooth Cape rounding
    (14.5, -39.0),  # south of Cape Agulhas; one continuous offshore arc (no hook east of Madagascar)
    (-5.5, -32.8),  # South Atlantic exit from the bend (smooth handoff north-west)
    (-42.0, 10.0),  # central Atlantic climb
    US_EAST_ENTRY,
]

TRUNK_AFRICA: List[Tuple[float, float]] = _flow_ribbon(_AF_CTRL)

# First segment per region (feeder lines converge to ``trunk[0]``).
TRUNKS: dict[str, List[Tuple[float, float]]] = {
    "Americas": TRUNK_AMERICAS,
    "Asia-Pacific": TRUNK_ASIA_PACIFIC_WEST,
    "Africa": TRUNK_AFRICA,
}

# All PathLayer trunk rows (Asia-Pacific contributes two polylines).
TRUNK_PATH_ROWS: list[tuple[str, List[Tuple[float, float]], str]] = [
    ("Americas", TRUNK_AMERICAS, "trunk"),
    ("Asia-Pacific", TRUNK_ASIA_PACIFIC_WEST, "trunk_ap_west"),
    ("Asia-Pacific", TRUNK_ASIA_PACIFIC_EAST, "trunk_ap_east"),
    ("Africa", TRUNK_AFRICA, "trunk"),
]

# Minimal structural hints (origins already shown as dots): two short merge legs each.
MERGE_AP: Tuple[float, float] = TRUNK_ASIA_PACIFIC_WEST[0]
STRUCTURAL_FEEDERS_AP: List[List[Tuple[float, float]]] = [
    [(103.5, 18.5), (110.0, 12.5), MERGE_AP],
    [(121.0, -5.5), (117.5, 4.0), MERGE_AP],
]

MERGE_AF: Tuple[float, float] = TRUNK_AFRICA[0]
STRUCTURAL_FEEDERS_AF: List[List[Tuple[float, float]]] = [
    [(48.5, -18.5), (46.5, -9.0), MERGE_AF],
    [(37.5, -2.8), (42.0, -3.2), MERGE_AF],
]


def _feeder_to_trunk(
    origin_lon: float,
    origin_lat: float,
    trunk: Sequence[Tuple[float, float]],
    route_idx: int,
) -> List[Tuple[float, float]]:
    """
    Short feeder from origin into the shared trunk (2–3 vertices).
    Slight lateral spread by route_idx so origins do not stack identically.
    """
    if not trunk:
        return [[float(origin_lon), float(origin_lat)]]

    target = trunk[0]
    spread = (route_idx % 5 - 2) * 0.35
    mid = _lerp((origin_lon, origin_lat), target, 0.45)
    mid = (mid[0] + spread * 0.4, mid[1] + spread * 0.15)

    return [
        [float(origin_lon), float(origin_lat)],
        [float(mid[0]), float(mid[1])],
        [float(target[0]), float(target[1])],
    ]


def build_trunk_path_dataframe(regions: Optional[Set[str]] = None) -> pd.DataFrame:
    """
    Shared corridor trunks for PathLayer (one row per drawable polyline).

    When ``regions`` is set (e.g. sidebar region filter), only trunks for those
    regions are included so geometry matches the visible producer countries.

    Africa + Asia-Pacific use three ribbon tiers (``layer``): soft outer wash,
    inner flow body, crisp core—drawn as separate PathLayers in ``map_layers``.
    Americas remains a single ``ribbon_core``-equivalent spine row only.
    """
    rows = []
    for region, trunk, kind in TRUNK_PATH_ROWS:
        if regions is not None and region not in regions:
            continue
        base = REGION_COLORS.get(region, [180, 180, 180])
        path = [[float(lon), float(lat)] for lon, lat in trunk]

        if region in {"Africa", "Asia-Pacific"}:
            rows.append(
                {
                    "region": region,
                    "path": path,
                    "width_pixels": 26.0,
                    "color": [base[0], base[1], base[2], 36],
                    "kind": kind,
                    "layer": "ribbon_outer",
                }
            )
            rows.append(
                {
                    "region": region,
                    "path": path,
                    "width_pixels": 11.5,
                    "color": [base[0], base[1], base[2], 100],
                    "kind": kind,
                    "layer": "ribbon_body",
                }
            )
            rows.append(
                {
                    "region": region,
                    "path": path,
                    "width_pixels": 2.65,
                    "color": [base[0], base[1], base[2], 252],
                    "kind": kind,
                    "layer": "ribbon_core",
                }
            )
        else:
            rows.append(
                {
                    "region": region,
                    "path": path,
                    "width_pixels": 3.2,
                    "color": [base[0], base[1], base[2], 210],
                    "kind": kind,
                    "layer": "ribbon_core",
                }
            )
    return pd.DataFrame(rows)


def build_structural_feeders(regions: Optional[Set[str]] = None) -> pd.DataFrame:
    """
    A few fixed merge-leg polylines so Africa / Asia-Pacific routes read as
    bundled corridors (regional feeders → shared trunk), without per-country clutter.
    """
    if regions is None:
        regions = {"Africa", "Asia-Pacific", "Americas"}
    rows: list[dict] = []
    if "Asia-Pacific" in regions:
        base = REGION_COLORS["Asia-Pacific"]
        for i, seg in enumerate(STRUCTURAL_FEEDERS_AP):
            dense = _densify_polyline(seg, steps_per_segment=4)
            path = [[float(lon), float(lat)] for lon, lat in dense]
            rows.append(
                {
                    "country": "",
                    "region": "Asia-Pacific",
                    "path": path,
                    "width_pixels": 2.0 + (i % 2) * 0.25,
                    "color": [base[0], base[1], base[2], 108],
                    "kind": "structural_feeder",
                }
            )
    if "Africa" in regions:
        base = REGION_COLORS["Africa"]
        for i, seg in enumerate(STRUCTURAL_FEEDERS_AF):
            dense = _densify_polyline(seg, steps_per_segment=4)
            path = [[float(lon), float(lat)] for lon, lat in dense]
            rows.append(
                {
                    "country": "",
                    "region": "Africa",
                    "path": path,
                    "width_pixels": 2.05 + (i % 2) * 0.25,
                    "color": [base[0], base[1], base[2], 105],
                    "kind": "structural_feeder",
                }
            )
    return pd.DataFrame(rows)


def build_feeder_paths(route_df: pd.DataFrame) -> pd.DataFrame:
    """
    Per-country feeder polylines only: origin -> first point of the regional trunk.

    Shared trunks are drawn once via ``build_trunk_path_dataframe`` so corridor
    geometry is not repeated under every origin (cleaner + clearer hierarchy).
    """
    rows = []
    route_df = route_df.sort_values(
        ["region", "normalized_route_weight"], ascending=[True, False]
    ).copy()
    route_df["route_idx"] = route_df.groupby("region").cumcount()

    max_w = max(float(route_df["normalized_route_weight"].max()), 1e-6)

    for _, r in route_df.iterrows():
        region = r["region"]
        trunk = TRUNKS.get(region)
        if not trunk:
            continue

        feeder = _feeder_to_trunk(
            float(r["lon"]),
            float(r["lat"]),
            trunk,
            int(r["route_idx"]),
        )
        path = [[float(p[0]), float(p[1])] for p in feeder]

        base = REGION_COLORS.get(region, [180, 180, 180])
        w = float(r["normalized_route_weight"]) / max_w
        width_px = 1.0 + w * 1.9
        alpha = int(75 + 95 * w)
        if region in {"Africa", "Asia-Pacific"}:
            width_px = width_px * 1.06
            alpha = min(195, int(alpha * 1.05))
        color = [base[0], base[1], base[2], alpha]

        rows.append(
            {
                "country": r["country"],
                "region": region,
                "path": path,
                "width_pixels": width_px,
                "color": color,
                "kind": "feeder",
            }
        )

    return pd.DataFrame(rows)
