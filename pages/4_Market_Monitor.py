"""
Market Monitor — Daily market_master + macro_master data.
Stock index closes, FX vs EUR, Brent Oil, US 10Y Yield, VIX.
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.topbar import render_topbar
from components.ui_helpers import render_kpi_card, kpi_row, insight_panel
from services.data_service import load_macro_master, load_market_master

render_topbar(active="Market_Monitor")

st.title("🌍 Market Monitor")
st.caption("Daily equity indices, FX rates vs EUR, Brent Oil, US 10Y Yield, and VIX across Asian economies.")

market = load_market_master()
macro  = load_macro_master()

# Define consistent country colors (Singapore = green)
color_map = {
    "Singapore": "#00aa55",  # Green
    "China": "#1f77b4",      # Blue
    "Hong Kong SAR China": "#ff7f0e",  # Orange
    "India": "#d62728",      # Red
}

if not market.empty:
    market["country"] = market["country"].str.strip()
if not macro.empty and "country" in macro.columns:
    macro["country"] = macro["country"].str.strip()

if market.empty:
    st.warning("No market data available.")
    st.stop()

# ── Filters ──────────────────────────────────────────────────────────────────
date_min, date_max = market["date"].min().date(), market["date"].max().date()

f_col, c_col = st.columns([2, 2])
with f_col:
    date_range = st.date_input(
        "Date range", value=(date_min, date_max),
        min_value=date_min, max_value=date_max,
    )
with c_col:
    countries = sorted(c for c in market["country"].unique() if c != "Japan")
    selected = st.multiselect(
        "Countries", options=countries, default=countries,
        format_func=lambda c: c,
    )

if len(date_range) == 2:
    start, end = date_range
    market = market[(market["date"].dt.date >= start) & (market["date"].dt.date <= end)]
    if not macro.empty:
        macro = macro[(macro["date"].dt.date >= start) & (macro["date"].dt.date <= end)]

market = market[market["country"].isin(selected)]

# ── Latest-day KPI Cards ──────────────────────────────────────────────────────
latest_date = market["date"].max()
latest = market[market["date"] == latest_date]
st.subheader(f"Latest snapshot — {latest_date.strftime('%d %b %Y')}")

if not latest.empty:
    cards = []
    for _, row in latest.iterrows():
        idx_val = pd.to_numeric(row["Index_Close"], errors="coerce")
        fx_val  = pd.to_numeric(row["FX_EUR_Rate"], errors="coerce")
        # Compute 1-day delta
        prev = market[(market["country"] == row["country"]) & (market["date"] < latest_date)]
        if not prev.empty:
            prev_idx = pd.to_numeric(prev.sort_values("date").iloc[-1]["Index_Close"], errors="coerce")
            delta = ((idx_val - prev_idx) / prev_idx * 100) if prev_idx else None
        else:
            delta = None

        idx_str = f"{idx_val:,.0f}" if isinstance(idx_val, (int, float)) else str(idx_val)
        fx_str  = f"{fx_val:.4f} EUR" if isinstance(fx_val, (int, float)) else str(fx_val)
        d_val   = delta
        color   = "#2e7d32" if (d_val or 0) >= 0 else "#c62828"
        bg      = "#f7fbf4" if (d_val or 0) >= 0 else "#fdf1f5"
        delta_display = d_val / 100 if d_val is not None else None  # convert % to ratio for render_kpi_card

        cards.append(render_kpi_card(
            row["country"],
            idx_str,
            "📊",
            delta=delta,
            color=color,
            bg=bg,
        ))
    kpi_row(cards)

# ── Macro KPIs ────────────────────────────────────────────────────────────────
if not macro.empty:
    latest_macro = macro[macro["date"] == macro["date"].max()].iloc[0]

    def _safe(val):
        import math
        return val if (val == val and not (isinstance(val, float) and math.isnan(val))) else None

    brent = _safe(latest_macro.get("Brent_Oil"))
    us10y = _safe(latest_macro.get("US10Y_Yield"))
    vix   = _safe(latest_macro.get("VIX"))

    macro_cards = [
        render_kpi_card("Brent Oil (USD)",  f"{brent:.2f}" if brent else "N/A",  "🛢️",
                        color="#e65100", bg="#fff9f0"),
        render_kpi_card("US 10Y Yield (%)", f"{us10y:.3f}" if us10y else "N/A", "📉",
                        color="#1565c0", bg="#f2f8fd"),
        render_kpi_card("VIX (Fear Index)", f"{vix:.2f}"   if vix   else "N/A",  "😨",
                        color="#c62828" if (vix or 0) > 25 else "#2e7d32",
                        bg="#fdf1f5" if (vix or 0) > 25 else "#f7fbf4"),
    ]
    st.subheader("Global Macro Indicators")
    kpi_row(macro_cards)

    # Insight
    if vix is not None:
        risk = "elevated" if vix > 25 else "moderate" if vix > 15 else "low"
        insight_panel("Market Conditions", [
            f"VIX at <b>{vix:.2f}</b> indicates <b>{risk}</b> market volatility / fear.",
            f"US 10Y Yield at <b>{us10y:.3f}%</b> — "
            + ("tightening financial conditions." if (us10y or 0) > 4 else "relatively accommodative conditions."),
            f"Brent crude at <b>${brent:.2f}</b> — "
            + ("high energy costs may pressure inflation." if (brent or 0) > 90 else "energy costs within moderate range."),
        ], color="#1a237e", bg="#e8eaf6")

st.divider()

# ── Equity & FX charts ────────────────────────────────────────────────────────
col_l, col_r = st.columns(2)
with col_l:
    fig = px.line(market.sort_values("date"), x="date", y="Index_Close",
                  color="country", title="Stock Index Close", color_discrete_map=color_map)
    fig.update_traces(hovertemplate="<b>%{fullData.name}</b><br>%{x|%d %b %Y}<br>Index: %{y:,.0f}<extra></extra>")
    fig.update_layout(margin=dict(t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)

with col_r:
    fig = px.line(market.sort_values("date"), x="date", y="FX_EUR_Rate",
                  color="country", title="FX Rate vs EUR", color_discrete_map=color_map)
    fig.update_traces(hovertemplate="<b>%{fullData.name}</b><br>%{x|%d %b %Y}<br>FX: %{y:.4f}<extra></extra>")
    fig.update_layout(margin=dict(t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)

# ── Combined macro chart ──────────────────────────────────────────────────────
if not macro.empty:
    macro_cols = [c for c in ["Brent_Oil", "US10Y_Yield", "VIX"] if macro[c].notna().any()]
    fig = go.Figure()
    for col in macro_cols:
        fig.add_trace(go.Scatter(x=macro["date"], y=macro[col], name=col, mode="lines",
                                  hovertemplate=f"{col}: %{{y:.2f}}<br>%{{x|%d %b %Y}}<extra></extra>"))
    fig.update_layout(title="Global Macro Indicators Over Time", xaxis_title="Date",
                      height=400, margin=dict(t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)

# ── Conclusion ────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style='background:#fff8e1; padding:20px 24px; border-radius:8px; margin-top:16px;'>
  <h3 style='color:#e65100; margin-top:0;'>Conclusion — Market Monitor: How do global macro conditions interact with Asian equity and FX markets?</h3>
  <p style='font-size:15px; color:#222;'>
    The Market Monitor reveals that Asian equity indices and FX rates are <b>closely coupled with global macro indicators</b> — particularly Brent Oil, US 10-Year Yields, and VIX — confirming that these open economies are deeply integrated into global financial cycles.
  </p>
  <ul style='font-size:15px; color:#333; line-height:1.8;'>
    <li><b>VIX spikes</b> (e.g. COVID-19 in 2020, taper tantrum in 2013) consistently coincide with equity sell-offs and FX depreciation across all four markets, confirming global risk-off behaviour overrides local fundamentals during crises.</li>
    <li><b>Rising US 10Y yields</b> tend to pressure Asian FX rates against the EUR as capital flows shift toward US dollar assets — Singapore and Hong Kong, with USD-pegged or managed currencies, are most exposed to this dynamic.</li>
    <li><b>Brent Oil</b> movements affect India most significantly due to its large energy import dependency; oil price drops (2014–2016, 2020) provided macroeconomic relief but also signalled global demand weakness.</li>
    <li><b>Equity index performance</b> diverged most sharply in 2020: China's market recovered faster than Hong Kong and India, reflecting domestic fiscal stimulus and earlier COVID containment.</li>
  </ul>
  <p style='font-size:15px; color:#222;'>
    <b>Answer:</b> Asian markets are significantly influenced by global macro conditions. Investors and policy analysts should monitor VIX, US yield trends, and oil prices as leading indicators of market stress across the region. Domestic macro fundamentals matter in calm periods, but global risk sentiment dominates during shocks.
  </p>
</div>
""", unsafe_allow_html=True)

