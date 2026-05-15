"""
Use Case 3 — Dr. Maria Stern (Professor of Macroeconomics)
Interest rate volatility vs Population Growth and Unemployment (workforce proxy).
"""
import plotly.express as px
import streamlit as st

from components.topbar import render_topbar
from components.ui_helpers import (
    render_kpi_card, kpi_row, insight_panel,
    add_events_to_fig, summary_table, key_takeaways,
)
from services.data_service import load_development_master

render_topbar(active="Population_Growth")

st.title("Interest Volatility, Population & Workforce")
st.caption("Persona: Dr. Maria Stern — Professor of Macroeconomics | How has interest rate volatility affected population growth and workforce employment? | Period: 2011–2020 (post-GFC to COVID onset)")

df = load_development_master()
df["country"] = df["country"].str.strip()  # Clean whitespace
countries = sorted(c for c in df["country"].unique() if c != "Japan")

# Define consistent country colors (Singapore = green)
color_map = {
    "Singapore": "#00aa55",  # Green
    "China": "#1f77b4",      # Blue
    "Hong Kong SAR China": "#ff7f0e",  # Orange
    "India": "#d62728",      # Red
}
year_min, year_max = int(df["year"].min()), int(df["year"].max())

# ── Filters ──────────────────────────────────────────────────────────────────
f_col = st.columns(1)[0]
with f_col:
    selected = st.multiselect(
        "Countries", options=countries, default=countries,
        format_func=lambda c: c,
        key="pop_countries",
    )
year_range = (year_min, 2020)

view = df[
    df["country"].isin(selected) & df["year"].between(*year_range)
].copy().sort_values(["country", "year"])

view["Rate Volatility"] = (
    view.groupby("country")["Interest Rate (%)"]
    .transform(lambda s: s.rolling(3, min_periods=2).std())
)
# Unemployment Volatility: complete for all 5 countries through 2025
view["Unemployment Volatility"] = (
    view.groupby("country")["Unemployment Rate (%)"]
    .transform(lambda s: s.rolling(3, min_periods=2).std())
)
# IR data coverage within 2011-2020: all 4 countries have complete IR data
ir_coverage = {
    "Singapore": 2021, "India": 2022,
    "Hong Kong SAR China": 2024, "China": 2024,
}

# ── KPI Cards ────────────────────────────────────────────────────────────────
avg_pop  = view["Population Growth (%)"].dropna().mean()
avg_vol  = view["Rate Volatility"].dropna().mean()
avg_unemp = view["Unemployment Rate (%)"].dropna().mean()

high_vol_c = view.groupby("country")["Rate Volatility"].mean().dropna() 
high_vol_c = high_vol_c.idxmax() if not high_vol_c.empty else "N/A"

cards = [
    render_kpi_card("Avg Population Growth",   f"{avg_pop:.2f}%",   "POP",
                    color="#2e7d32" if avg_pop > 0 else "#c62828",
                    bg="#f7fbf4" if avg_pop > 0 else "#fdf1f5"),
    render_kpi_card("Avg IR Volatility",        f"{avg_vol:.2f}pp",  "IR-VOL",
                    color="#e65100", bg="#fff9f0"),
    render_kpi_card("Avg Unemployment",         f"{avg_unemp:.2f}%", "LAB",
                    color="#1565c0", bg="#f2f8fd"),
]
kpi_row(cards)

# ── Insight Panel ─────────────────────────────────────────────────────────────
if not view.empty:
    pop_trend = view.groupby("year")["Population Growth (%)"].mean()
    pop_slope = (pop_trend.iloc[-1] - pop_trend.iloc[0]) / max(len(pop_trend)-1, 1) if len(pop_trend) > 1 else 0
    pop_dir   = "declining" if pop_slope < -0.05 else "growing" if pop_slope > 0.05 else "stable"

    vol_corr = view[["Rate Volatility", "Population Growth (%)"]].dropna().corr().iloc[0, 1]

    unemp_vol_corr_pop = view[["Unemployment Volatility", "Population Growth (%)"]].dropna().corr().iloc[0, 1]

    bullets = [
        f"Population growth across selected economies is <b>{pop_dir}</b> over the period "
        f"(trend slope: {pop_slope:+.3f}% per year).",
        f"<b>{high_vol_c}</b> shows the highest interest rate volatility, potentially "
        "reflecting frequent central bank interventions or external shocks.",
        f"IR volatility vs population growth correlation: <b>{vol_corr:.3f}</b> — "
        + ("higher IR volatility appears linked to slower population growth." if vol_corr < -0.2
           else "no strong direct relationship observed."),
        f"Unemployment volatility vs population growth correlation: <b>{unemp_vol_corr_pop:.3f}</b> — "
        + ("labour market instability appears linked to slower population growth." if unemp_vol_corr_pop < -0.2
           else "no strong direct relationship observed."),
        "<b>Note:</b> Period 2011–2020 covers complete interest rate data for all 4 selected economies. "
        "Unemployment Volatility (3-yr rolling std of unemployment) is shown alongside IR Volatility as a complementary workforce instability measure.",
    ]
    insight_panel("Academic Macro Insights", bullets, color="#4a148c", bg="#faf2fb")

st.divider()

# ── Line charts ───────────────────────────────────────────────────────────────
col_l, col_r = st.columns(2)
with col_l:
    fig = px.line(
        view.dropna(subset=["Population Growth (%)"]).sort_values("year"),
        x="year", y="Population Growth (%)", color="country",
        markers=True, title="Population Growth Over Time", color_discrete_map=color_map,
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    add_events_to_fig(fig)
    fig.update_layout(margin=dict(t=40, b=20))
    fig.update_xaxes(range=[year_range[0] - 0.5, year_range[1] + 0.5], dtick=2)
    st.plotly_chart(fig, use_container_width=True)

with col_r:
    fig = px.line(
        view.dropna(subset=["Rate Volatility"]).sort_values("year"),
        x="year", y="Rate Volatility", color="country",
        markers=True, title="Interest Rate Volatility (3-yr rolling std)", color_discrete_map=color_map,
    )
    # Annotate data cutoff for countries with limited IR data
    for country, last_yr in ir_coverage.items():
        if last_yr < year_range[1] and country in selected:
            fig.add_annotation(
                x=last_yr, y=0, text=f"{country.split()[0]}: ends {last_yr}",
                showarrow=False, font=dict(size=8, color="#999"),
                yshift=-18, xshift=0,
            )
    add_events_to_fig(fig)
    fig.update_layout(margin=dict(t=40, b=30))
    fig.update_xaxes(range=[year_range[0] - 0.5, year_range[1] + 0.5], dtick=2)
    st.plotly_chart(fig, use_container_width=True)

if not view.empty:
    _pop_avg = view.groupby("country")["Population Growth (%)"].mean()
    _vol_avg = view.groupby("country")["Rate Volatility"].mean().dropna()
    key_takeaways([
        f"<b>{_pop_avg.idxmax()}</b> recorded the highest average population growth ({_pop_avg.max():.2f}% p.a.) over 2011\u20132020.",
        f"<b>{_pop_avg.idxmin()}</b> shows the slowest population growth ({_pop_avg.min():.2f}% p.a.), reflecting demographic maturity or net emigration.",
        f"IR volatility peaked around 2015 (China market crash) and 2018 (trade war), with <b>{'and '.join(_vol_avg.nlargest(1).index.tolist())}</b> showing the highest rate instability.",
    ])

# ── Dual volatility scatter plots ─────────────────────────────────────────────
st.subheader("Volatility vs Population Growth & Workforce")
st.caption("Left: IR Volatility · Right: Unemployment Volatility (3-yr rolling std of unemployment rate)")
col_l2, col_r2 = st.columns(2)
with col_l2:
    fig = px.scatter(
        view.dropna(subset=["Rate Volatility", "Population Growth (%)"]),
        x="Rate Volatility", y="Population Growth (%)",
        color="country", custom_data=["year", "country"],
        trendline="ols", height=420, opacity=0.82,
        title="IR Volatility vs Population Growth", color_discrete_map=color_map,
    )
    fig.update_traces(hovertemplate=(
        "<b>%{customdata[1]}</b> (%{customdata[0]})<br>"
        "IR Volatility: %{x:.2f}pp<br>Pop Growth: %{y:.2f}%<extra></extra>"
    ))
    st.plotly_chart(fig, use_container_width=True)

with col_r2:
    fig = px.scatter(
        view.dropna(subset=["Unemployment Volatility", "Population Growth (%)"]),
        x="Unemployment Volatility", y="Population Growth (%)",
        color="country", custom_data=["year", "country"],
        trendline="ols", height=420, opacity=0.82,
        title="Unemployment Volatility vs Population Growth", color_discrete_map=color_map,
    )
    fig.update_traces(hovertemplate=(
        "<b>%{customdata[1]}</b> (%{customdata[0]})<br>"
        "Unemp Volatility: %{x:.2f}pp<br>Pop Growth: %{y:.2f}%<extra></extra>"
    ))
    st.plotly_chart(fig, use_container_width=True)

col_l3, col_r3 = st.columns(2)
with col_l3:
    fig = px.scatter(
        view.dropna(subset=["Rate Volatility", "Unemployment Rate (%)"]),
        x="Rate Volatility", y="Unemployment Rate (%)",
        color="country", custom_data=["year", "country"],
        trendline="ols", height=420, opacity=0.82,
        title="IR Volatility vs Unemployment Rate", color_discrete_map=color_map,
    )
    fig.update_traces(hovertemplate=(
        "<b>%{customdata[1]}</b> (%{customdata[0]})<br>"
        "IR Volatility: %{x:.2f}pp<br>Unemployment: %{y:.2f}%<extra></extra>"
    ))
    st.plotly_chart(fig, use_container_width=True)

with col_r3:
    fig = px.line(
        view.dropna(subset=["Unemployment Volatility"]).sort_values(["country", "year"]),
        x="year", y="Unemployment Volatility", color="country",
        markers=True, title="Unemployment Volatility Over Time (3-yr rolling std, all countries)", color_discrete_map=color_map,
    )
    add_events_to_fig(fig)
    fig.update_layout(margin=dict(t=40, b=20))
    fig.update_xaxes(range=[year_range[0] - 0.5, year_range[1] + 0.5], dtick=2)
    fig.update_traces(hovertemplate="<b>%{fullData.name}</b><br>Year: %{x}<br>Unemp Volatility: %{y:.2f}pp<extra></extra>")
    st.plotly_chart(fig, use_container_width=True)

if not view.empty:
    _ir_pop_corr = view[["Rate Volatility", "Population Growth (%)"]].dropna().corr().iloc[0, 1]
    _uv_pop_corr = view[["Unemployment Volatility", "Population Growth (%)"]].dropna().corr().iloc[0, 1]
    key_takeaways([
        f"IR Volatility vs Population Growth: <b>r\u00a0=\u00a0{_ir_pop_corr:.3f}</b> \u2014 {'higher rate instability is associated with slower population growth' if _ir_pop_corr < -0.2 else 'no strong directional relationship found' if abs(_ir_pop_corr) < 0.2 else 'positive association between rate volatility and population growth'}.",
        f"Unemployment Volatility vs Population Growth: <b>r\u00a0=\u00a0{_uv_pop_corr:.3f}</b> \u2014 {'labour market instability links to slower population growth' if _uv_pop_corr < -0.2 else 'no strong direct relationship observed'}.",
        "OLS trendlines reveal per-country heterogeneity \u2014 the impact of volatility on demographics varies significantly across economies.",
    ], color="#4a148c")

# ── Unemployment Over Time (workforce proxy) ─────────────────────────────────
st.subheader("Unemployment Rate Over Time (Workforce Proxy)")
fig = px.line(
    view.dropna(subset=["Unemployment Rate (%)"]).sort_values(["country", "year"]),
    x="year", y="Unemployment Rate (%)", color="country",
    markers=True, title="Unemployment Rate Over Time",
    color_discrete_map=color_map,
)
add_events_to_fig(fig)
fig.update_layout(margin=dict(t=40, b=20))
fig.update_xaxes(range=[year_min - 0.5, 2025.5], dtick=2)
fig.update_yaxes(showgrid=False)
fig.update_traces(hovertemplate="<b>%{fullData.name}</b><br>Year: %{x}<br>Unemployment: %{y:.2f}%<extra></extra>")
st.plotly_chart(fig, use_container_width=True)
if not view.empty:
    _u3_avg = view.groupby("country")["Unemployment Rate (%)"].mean()
    key_takeaways([
        f"<b>{_u3_avg.idxmin()}</b> maintained the tightest labour market ({_u3_avg.min():.1f}% avg unemployment) \u2014 the most favourable workforce conditions in the region.",
        f"<b>{_u3_avg.idxmax()}</b> recorded the highest average unemployment ({_u3_avg.max():.1f}%), indicating persistent structural slack in the workforce.",
        "The COVID-19 shock (2020) is visible as a sharp divergence point, with some economies experiencing sudden unemployment spikes while others remained relatively stable.",
    ], color="#1565c0")

# ── Summary Table ─────────────────────────────────────────────────────────────
st.subheader("Country Summary")
agg = {
    "Avg Pop Growth (%)": "Population Growth (%)",
    "Avg IR Volatility": "Rate Volatility",
    "Avg Unemp Volatility": "Unemployment Volatility",
    "Avg Unemployment (%)": "Unemployment Rate (%)",
}
summary_table(view, agg_cols=agg)

# ── Conclusion ────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style='background:#fce4ec; padding:20px 24px; border-radius:8px; margin-top:16px;'>
  <h3 style='color:#880e4f; margin-top:0;'>Conclusion — RQ 3: How has interest rate volatility affected population growth and workforce employment?</h3>
  <p style='font-size:15px; color:#222;'>
    Across the four Asian economies (2011–2020), interest rate volatility shows <b>a weak but directionally negative relationship</b> with both population growth and employment stability — though structural and demographic factors dominate over monetary conditions.
  </p>
  <ul style='font-size:15px; color:#333; line-height:1.8;'>
    <li><b>India</b> exhibited the highest interest rate volatility, reflecting the Reserve Bank of India's frequent adjustments in response to inflation and currency pressures. Despite this, India maintained the highest population growth, suggesting demographics dwarf monetary influence on population dynamics.</li>
    <li><b>Singapore</b> had the lowest population growth and minimal rate volatility, consistent with a mature, low-fertility economy where monetary stability supports but cannot reverse demographic trends.</li>
    <li><b>China and Hong Kong</b> show that rate volatility coincided with moderate unemployment stability — central bank credibility and capital controls shielded labour markets from sharp monetary shocks.</li>
    <li>Periods of <b>elevated IR volatility</b> (2013–2015, taper tantrum era) correlate with slightly weaker workforce absorption, but the effect is lagged and confounded by global trade cycles.</li>
  </ul>
  <p style='font-size:15px; color:#222;'>
    <b>Answer:</b> Interest rate volatility has a <b>limited direct impact</b> on population growth — which is primarily driven by fertility rates and migration policy. Its effect on workforce employment is more visible: higher volatility introduces uncertainty that can suppress investment and hiring, particularly in export-dependent economies like Singapore and Hong Kong. Long-run demographic trends remain the dominant force.
  </p>
</div>
""", unsafe_allow_html=True)

