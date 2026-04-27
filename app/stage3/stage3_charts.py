"""Dark-theme Plotly figures for Stage 3 (``st.plotly_chart`` embeds live Plotly.js, not PNG)."""

from __future__ import annotations

from typing import Sequence

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from app.plotly_theme import plotly_layout_base

REGION_COLORS = {
    "Americas": "#e86f51",
    "Africa": "#58c486",
    "Asia-Pacific": "#68a2ff",
}


def _apply_base(fig: go.Figure, *, title: str, x_title: str = "", y_title: str = "", height: int = 380) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color="#e2e8f0")),
        **plotly_layout_base(height=height),
    )
    xa = dict(gridcolor="#1e293b", zeroline=False, linecolor="#334155")
    if x_title:
        xa["title_text"] = x_title
    ya = dict(gridcolor="#1e293b", zeroline=False, linecolor="#334155")
    if y_title:
        ya["title_text"] = y_title
    fig.update_xaxes(**xa)
    fig.update_yaxes(**ya)
    return fig


def fig_horizontal_bar_regions(
    values: pd.Series,
    *,
    title: str,
    xlabel: str,
    value_scale: float = 1.0,
    x_format: str = "{:.2f}",
) -> go.Figure:
    regions = list(values.index)
    scaled = (values.astype(float) * value_scale).tolist()
    colors = [REGION_COLORS.get(r, "#94a3b8") for r in regions]
    text = []
    for v in scaled:
        if pd.isna(v):
            text.append("")
        else:
            text.append(x_format.format(v))
    fig = go.Figure(
        go.Bar(
            x=scaled,
            y=regions,
            orientation="h",
            marker=dict(color=colors, line=dict(width=0)),
            text=text,
            textposition="outside",
            hovertemplate="%{y}<br>%{x}<extra></extra>",
        )
    )
    fig.update_yaxes(categoryorder="array", categoryarray=list(reversed(regions)))
    fig = _apply_base(fig, title=title, x_title=xlabel, y_title="", height=320)
    fig.update_layout(margin=dict(l=56, r=96, t=52, b=48))
    return fig


def fig_boxplot_altitude_by_region(df: pd.DataFrame, *, title: str) -> go.Figure:
    regions = ["Americas", "Africa", "Asia-Pacific"]
    fig = go.Figure()
    for reg in regions:
        y = df.loc[df["region"] == reg, "altitude"].dropna()
        if y.empty:
            continue
        fig.add_trace(
            go.Box(
                y=y,
                name=reg,
                marker_color=REGION_COLORS.get(reg, "#64748b"),
                boxmean=False,
                hovertemplate="%{y:.0f} m<extra></extra>",
            )
        )
    return _apply_base(fig, title=title, x_title="", y_title="Lot altitude (m)", height=380)


def fig_grouped_sensory_regions(df: pd.DataFrame, *, attrs: Sequence[str], title: str) -> go.Figure:
    regions = [r for r in ["Americas", "Africa", "Asia-Pacific"] if r in df.index]
    attrs = [a for a in attrs if a in df.columns]
    if not regions or not attrs:
        fig = go.Figure()
        return _apply_base(fig, title=title, height=280)

    bar_colors = ["#cbd5e1", "#a5b4fc", "#fde68a", "#fca5a5"]
    fig = go.Figure()
    for i, attr in enumerate(attrs):
        vals = [float(df.loc[r, attr]) if r in df.index and pd.notna(df.loc[r, attr]) else 0.0 for r in regions]
        fig.add_trace(
            go.Bar(
                name=attr.capitalize(),
                x=regions,
                y=vals,
                marker_color=bar_colors[i % len(bar_colors)],
                hovertemplate=f"%{{x}}<br>{attr}: %{{y:.2f}}<extra></extra>",
            )
        )
    fig.update_layout(barmode="group", legend=dict(orientation="h", yanchor="bottom", y=1.02, x=1, xanchor="right"))
    return _apply_base(fig, title=title, y_title="Mean score (lot average)", height=400)


def fig_sensory_heatmap_regions(df: pd.DataFrame, *, attrs: Sequence[str], title: str) -> go.Figure:
    """Region × sensory heatmap; color = deviation from the simple mean across the three regions (per attribute)."""
    regions = [r for r in ("Americas", "Africa", "Asia-Pacific") if r in df.index]
    attrs = [a for a in attrs if a in df.columns]
    if len(regions) < 2 or len(attrs) < 2:
        fig = go.Figure()
        return _apply_base(fig, title=title, height=360)

    raw = df.loc[regions, attrs].astype(float)
    col_means = raw.mean(axis=0, skipna=True)
    centered = raw.subtract(col_means, axis=1)
    vmax = float(np.nanmax(np.abs(centered.values)))
    if not np.isfinite(vmax) or vmax < 1e-6:
        vmax = 0.12

    x_labels = [a.capitalize() for a in attrs]
    z = centered.values
    text = np.round(raw.values.astype(float), 2)
    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=x_labels,
            y=list(raw.index),
            text=text,
            texttemplate="%{text:.2f}",
            textfont={"size": 12, "color": "#e8ecf1"},
            colorscale=[
                [0.0, "#4a6fa5"],
                [0.5, "#1e293b"],
                [1.0, "#fde68a"],
            ],
            zmid=0.0,
            zmin=-vmax,
            zmax=vmax,
            hovertemplate=(
                "<b>%{y}</b> · %{x}<br>Mean: %{text:.2f}<br>Δ vs 3-region avg: %{z:+.2f}<extra></extra>"
            ),
            colorbar=dict(
                title=dict(text="Δ vs mean<br>across regions", font=dict(size=10, color="#94a3b8")),
                tickfont=dict(color="#94a3b8"),
            ),
        )
    )
    fig.update_layout(
        **plotly_layout_base(height=380),
        title=dict(text=title, font=dict(size=14, color="#e2e8f0")),
        xaxis=dict(side="top", tickfont=dict(color="#94a3b8"), gridcolor="#1e293b"),
        yaxis=dict(
            title=dict(text="", font=dict(color="#94a3b8")),
            tickfont=dict(size=12, color="#cbd5e1"),
            autorange="reversed",
            gridcolor="#1e293b",
        ),
    )
    return fig


def fig_scatter_region_summary(summary: pd.DataFrame, *, title: str) -> go.Figure:
    fig = go.Figure()
    if summary.empty:
        return _apply_base(fig, title=title, height=360)
    for _, row in summary.iterrows():
        reg = row["region"]
        x = row["median_lot_altitude_m"]
        y = row["mean_total_cup_points"]
        if pd.isna(x) or pd.isna(y):
            continue
        fig.add_trace(
            go.Scatter(
                x=[x],
                y=[y],
                mode="markers+text",
                name=reg,
                text=[reg],
                textposition="top right",
                marker=dict(
                    size=18,
                    color=REGION_COLORS.get(reg, "#94a3b8"),
                    line=dict(width=1, color="#0f172a"),
                ),
                hovertemplate="%{text}<br>Median altitude: %{x:.0f} m<br>Mean points: %{y:.2f}<extra></extra>",
            )
        )
    return _apply_base(
        fig,
        title=title,
        x_title="Regional median lot altitude (m)",
        y_title="Regional mean total cup points",
        height=380,
    )


def fig_production_share_bars(production: pd.Series, *, title: str) -> go.Figure:
    tot = float(production.sum()) or 1.0
    share = production.astype(float) / tot
    return fig_horizontal_bar_regions(
        share,
        title=title,
        xlabel="Share of production in this dataset",
        value_scale=1.0,
        x_format="{:.0%}",
    )
