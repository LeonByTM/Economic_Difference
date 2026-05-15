"""Shared UI helpers: KPI cards, insight panels, year presets, event overlays."""
import streamlit as st

COUNTRY_FLAGS = {
    "China": "CN",
    "Hong Kong SAR China": "HK",
    "HongKong": "HK",
    "India": "IN",
    "Singapore": "SG",
}

ECONOMIC_EVENTS = [
    {"year": 2015, "label": "China mkt crash"},
    {"year": 2018, "label": "Trade war"},
    {"year": 2020, "label": "COVID-19"},
]


def flag(country: str) -> str:
    return COUNTRY_FLAGS.get(country, "")


def render_kpi_card(label: str, value: str, icon: str,
                    delta: float | None = None,
                    color: str = "#0a3d5c",
                    bg: str = "#f8fbff") -> str:
    delta_html = ""
    if delta is not None:
        delta_color = "#2e7d32" if delta >= 0 else "#c62828"
        arrow = "▲" if delta >= 0 else "▼"
        delta_html = (
            f'<p style="margin:3px 0 0;font-size:0.78rem;color:{delta_color};">'
            f'{arrow} {abs(delta):.2f} vs median</p>'
        )
    return f"""
<div style="background:{bg};border-radius:10px;padding:14px 18px;
                        border:1px solid rgba(10,61,92,0.06);height:132px;box-sizing:border-box;">
  <p style="margin:3px 0 0;font-size:0.78rem;color:#666;line-height:1.2;">{label}</p>
    <p style="margin:6px 0 0;font-size:2rem;font-weight:700;color:{color};
            line-height:1.2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{value}</p>
  {delta_html}
</div>"""


def kpi_row(cards: list) -> None:
    """Render a row of KPI card HTML strings."""
    cols = st.columns(len(cards))
    for col, html in zip(cols, cards):
        col.markdown(html, unsafe_allow_html=True)
    st.markdown("<div style='margin-top:1.2rem'></div>", unsafe_allow_html=True)


def insight_panel(title: str, bullets: list[str],
                  color: str = "#1565c0", bg: str = "#e3f2fd") -> None:
    items = "".join(
        f"<li style='margin:5px 0;line-height:1.55;'>{b}</li>" for b in bullets
    )
    st.markdown(f"""
<div style="background:{bg};border:1px solid rgba(10,61,92,0.10);border-radius:8px;
            padding:14px 20px;margin-bottom:1rem;">
  <strong style="color:{color};font-size:0.92rem;">{title}</strong>
  <ul style="margin:8px 0 0;padding-left:18px;color:#1a1a2e;font-size:0.86rem;">
    {items}
  </ul>
</div>""", unsafe_allow_html=True)


def key_takeaways(bullets: list, color: str = "#1565c0") -> None:
    """Render a compact key takeaways box below a chart."""
    items = "".join(f"<li style='margin:3px 0;line-height:1.5'>{b}</li>" for b in bullets)
    st.markdown(
        f"""<div style="background:#f8f9ff;border-left:4px solid {color};padding:10px 16px;
        border-radius:0 4px 4px 0;margin:2px 0 18px;font-size:0.84rem;color:#1a1a2e;">
        <b style="color:{color}">Key Takeaways</b>
        <ul style="margin:5px 0 0;padding-left:16px">{items}</ul></div>""",
        unsafe_allow_html=True,
    )


def add_events_to_fig(fig, year_col_is_numeric: bool = True):
    """Overlay economic event markers onto a plotly figure."""
    for ev in ECONOMIC_EVENTS:
        fig.add_vline(
            x=ev["year"],
            line_width=1.2,
            line_dash="dot",
            line_color="rgba(100,100,100,0.45)",
            annotation_text=ev["label"],
            annotation_position="top right",
            annotation_font_size=8.5,
            annotation_font_color="#666",
        )
    return fig


def summary_table(view, group_col: str = "country",
                  agg_cols: dict | None = None) -> None:
    """Render a styled summary ranking table."""
    if agg_cols is None:
        agg_cols = {}
    import pandas as pd
    rows = []
    for country, g in view.groupby(group_col):
        row = {
            "": flag(country),
            "Country": country,
        }
        for col_label, col_name in agg_cols.items():
            if col_name in g.columns:
                row[col_label] = round(g[col_name].mean(), 2)
        rows.append(row)
    df_table = pd.DataFrame(rows)
    # Sort by first numeric column
    numeric_cols = [c for c in df_table.columns if df_table[c].dtype in ["float64", "int64"]]
    if numeric_cols:
        df_table = df_table.sort_values(numeric_cols[0], ascending=False)
    st.dataframe(df_table, use_container_width=True, hide_index=True)
