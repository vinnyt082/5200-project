"""Shared Plotly layout and Streamlit config for interactive charts (no rasterized pyplot)."""

from __future__ import annotations

from typing import Any

# Streamlit embeds Plotly as interactive HTML (pan/zoom/hover), not static PNG.
PLOTLY_CONFIG: dict[str, Any] = {
    "scrollZoom": True,
    "displayModeBar": True,
    "displaylogo": False,
    "responsive": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
}


def plotly_layout_base(*, height: int = 380) -> dict[str, Any]:
    """Page-level look only; each figure sets ``xaxis`` / ``yaxis`` to avoid duplicate keys."""
    return {
        "template": "plotly_dark",
        "paper_bgcolor": "#0b1220",
        "plot_bgcolor": "#0b1220",
        "font": {"color": "#94a3b8", "size": 11},
        "margin": {"l": 56, "r": 28, "t": 52, "b": 48},
        "height": height,
        "hovermode": "closest",
    }
