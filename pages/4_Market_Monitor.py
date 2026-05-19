"""
Market Monitor — short-term country investment risk monitoring.
Daily stock index closes, FX vs EUR, Brent Oil, US 10Y Yield, and VIX.
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.topbar import render_topbar
from components.ui_helpers import render_kpi_card, kpi_row, insight_panel, key_takeaways
from services.data_service import load_macro_master, load_market_master

render_topbar(active="Market_Monitor")

st.title("🌍 Short-Term Country Investment Risk Monitor")
st.caption("Investor-facing live view for EU-based capital allocators assessing short-term opportunities and risk across Asian markets using equity, FX, oil, rates, and volatility signals.")

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

insight_panel(
    "Investor Context",
    [
        f"This page is a <b>short-horizon market pulse</b> built from live daily data spanning <b>{date_min.strftime('%d %b %Y')}</b> to <b>{date_max.strftime('%d %b %Y')}</b>.",
        "It connects directly to the previous research pages: those pages explain the <b>structural fundamentals</b> behind each economy, while this page shows how those fundamentals are being <b>priced by markets right now</b>.",
        "For an <b>EU-based investor</b>, this page is especially relevant because returns must be judged not only by local equity performance but also by <b>FX movements against the EUR</b>, which directly affect realised foreign-investment returns.",
        "The purpose of this view is not long-cycle forecasting; it is to support <b>short-term country allocation decisions</b> by identifying which Asian markets currently look more resilient, more volatile, or more exposed to external macro pressure.",
    ],
    color="#1a237e",
    bg="#e8eaf6",
)

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
    if vix is not None and brent is not None and us10y is not None:
        risk = "elevated" if vix > 25 else "moderate" if vix > 15 else "low"
        insight_panel("Market Conditions", [
            f"VIX at <b>{vix:.2f}</b> indicates <b>{risk}</b> market volatility / fear.",
            f"US 10Y Yield at <b>{us10y:.3f}%</b> — "
            + ("tightening financial conditions." if us10y > 4 else "relatively accommodative conditions."),
            f"Brent crude at <b>${brent:.2f}</b> — "
            + ("high energy costs may pressure inflation." if brent > 90 else "energy costs within moderate range."),
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
    key_takeaways([
        "Stock indices summarize the market's <b>current earnings and growth expectations</b>; over a short window, investors should focus on <b>relative direction, drawdown intensity, and recovery speed</b> rather than long-term valuation conclusions.",
        "This directly extends the <b>GDP divergence</b> page: economies that looked more resilient in the historical macro analysis should, in a supportive market regime, also show stronger equity stability or faster recovery in the live window.",
        "China's index is shown on an <b>absolute level basis</b>, so direct cross-country comparison is less useful than comparing <b>recent slope, stability, and recovery behaviour</b> across markets.",
        "In this live window, the chart is most useful for spotting <b>which market is absorbing risk best</b> and which is reacting more sharply to changes in global sentiment.",
        "For foreign investors, <b>dispersion across markets</b> matters as much as direction: when one market holds up while others weaken, it often signals stronger local resilience, better policy credibility, or a more attractive short-term risk-reward profile for international capital.",
    ])

with col_r:
    fig = px.line(market.sort_values("date"), x="date", y="FX_EUR_Rate",
                  color="country", title="FX Rate vs EUR", color_discrete_map=color_map)
    fig.update_traces(hovertemplate="<b>%{fullData.name}</b><br>%{x|%d %b %Y}<br>FX: %{y:.4f}<extra></extra>")
    fig.update_layout(margin=dict(t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)
    key_takeaways([
        "<b>Hong Kong's</b> near-flat FX line reflects its hard USD peg since 1983 — the HKMA defends a tight 7.75–7.85 HKD/USD band using massive foreign reserve interventions, effectively importing US monetary policy regardless of local conditions.",
        "<b>India's rupee</b> shows the most volatility in this group — driven by current account deficits, oil import dependency, and sensitivity to US rate differentials that trigger capital outflows whenever the Fed tightens.",
        "A <b>rising line</b> means the local currency is weakening against the EUR (more local currency needed per euro). For an EU investor, that can <b>reduce euro-denominated returns</b> even when the local equity market is rising.",
        "This extends the <b>interest rate and employment</b> analysis: monetary conditions do not only affect domestic labour markets, they also affect currency stability, which is critical for foreign investors measuring returns in EUR or USD terms.",
        "FX moves are a <b>real-time stress indicator</b>: over a short horizon, currency weakness often shows risk aversion faster than equity indices, making this chart valuable as an early warning signal before increasing country exposure.",
    ], color="#1565c0")

# ── Combined macro chart ──────────────────────────────────────────────────────
if not macro.empty:
    macro_cols = [c for c in ["Brent_Oil", "US10Y_Yield", "VIX"] if macro[c].notna().any()]
    fig = go.Figure()
    for col in macro_cols:
        fig.add_trace(go.Scatter(x=macro["date"], y=macro[col], name=col, mode="lines",
                                  hovertemplate=f"{col}: %{{y:.2f}}<br>%{{x|%d %b %Y}}<extra></extra>"))
    fig.update_layout(title="Global Macro Indicators - Recent Trend", xaxis_title="Date",
                      height=400, margin=dict(t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)
    key_takeaways([
        "<b>VIX</b>, <b>US 10-Year Yield</b>, and <b>Brent Oil</b> are the three fastest ways to read the current macro backdrop: volatility, global discount rates, and energy cost pressure.",
        "When the <b>US 10-Year Yield</b> rises, global capital can rotate toward US assets, which typically tightens financial conditions for Asian markets and puts pressure on risk assets and currencies.",
        "<b>Brent Oil</b> matters disproportionately for Asian importers: higher oil prices can feed inflation and squeeze margins, while lower oil prices can ease cost pressure but may also reflect weaker global demand.",
        "This links back to the <b>population growth and workforce</b> page: economies with stronger labour absorption and demographic support are generally better positioned to absorb external macro shocks over time, while this chart shows whether markets are currently rewarding that resilience.",
        "For investors, the main value here is <b>co-movement</b>: if volatility, yields, and oil all move against risk assets at the same time, the regional backdrop is becoming less supportive for fresh foreign allocations.",
        "This chart should be read as a <b>live country-risk dashboard</b>, not a long-history study; it helps investors assess the immediate environment in which Asian equities and FX are trading.",
    ], color="#1565c0")

# ── Conclusion ────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style='background:#fff8e1; padding:20px 24px; border-radius:8px; margin-top:16px;'>
    <h3 style='color:#e65100; margin-top:0;'>Conclusion — Why This Page Matters for Foreign Investors</h3>
  <p style='font-size:15px; color:#222;'>
      This page adds value for investors because it translates the dashboard from a purely historical research product into a <b>live country investment risk monitor</b>. Pages 1–3 explain <b>why these economies matter fundamentally</b>; this page shows <b>how those fundamentals are currently being priced</b> in equities, FX, and macro-sensitive indicators.
  </p>
  <ul style='font-size:15px; color:#333; line-height:1.8;'>
      <li><b>Short-horizon data is still decision-useful</b> when the objective is to assess present market tone, relative resilience, and cross-asset confirmation rather than to estimate structural relationships.</li>
      <li><b>Equity, FX, and macro indicators together</b> give foreign investors a practical read on whether the region is currently trading in a risk-on, neutral, or defensive regime.</li>
      <li><b>Currency moves matter directly to EU-based investors</b>: even if a local equity market performs well, FX weakness against the EUR can materially reduce realised returns.</li>
      <li><b>Cross-country dispersion</b> remains informative even in a short window: when one market or currency weakens materially faster than peers, it can signal higher vulnerability, weaker sentiment, or less attractive foreign-capital conditions.</li>
      <li><b>This page completes the investment story</b>: the earlier pages justify why the countries deserve attention, and this page helps decide where near-term risk appears most manageable for foreign capital.</li>
  </ul>
  <p style='font-size:15px; color:#222;'>
      <b>Answer:</b> Yes, this page makes sense for foreign investors when positioned correctly: the earlier pages establish the <b>investment case</b> through structural macro analysis, while this page helps assess <b>current timing, market sentiment, and currency risk</b>. Together, they support a more complete investment view: <b>why to consider these Asian markets</b>, <b>which ones look more resilient right now</b>, and <b>what external risks could affect euro-based returns</b>.
  </p>
</div>
""", unsafe_allow_html=True)

