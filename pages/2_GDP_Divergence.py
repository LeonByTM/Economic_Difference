"""
Use Case 2 — Park Jun-ho (Economic Risk Researcher)
GDP Growth vs divergence with Unemployment across Asian economies.
"""
import plotly.express as px
import streamlit as st

from components.topbar import render_topbar
from components.ui_helpers import (
    COUNTRY_FLAGS, ECONOMIC_EVENTS,
    render_kpi_card, kpi_row, insight_panel,
    add_events_to_fig, summary_table, key_takeaways,
)
from services.data_service import load_development_master

render_topbar(active="GDP_Divergence")

st.title("GDP Growth & Economic Divergence")
st.caption("Persona: Park Jun-ho — Economic Risk Researcher | Which nations show the strongest divergence between GDP growth and unemployment? | Period: 2011–2020 (post-GFC to COVID onset)")

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
        "Countries",
        options=countries,
        default=countries,
        format_func=lambda c: c,
        key="gdp_countries",
    )
year_range = (year_min, 2020)

view = df[
    df["country"].isin(selected) & df["year"].between(*year_range)
].copy()
# Divergence requires both columns; NaN where either is missing
view["Divergence Index"] = view["GDP Growth (%)"] - view["Unemployment Rate (%)"]

# ── KPI Cards ────────────────────────────────────────────────────────────────
avg_gdp   = view["GDP Growth (%)"].dropna().mean()
avg_unemp = view["Unemployment Rate (%)"].dropna().mean()
avg_div   = view["Divergence Index"].dropna().mean()
med_gdp   = df["GDP Growth (%)"].dropna().median()
med_unemp = df["Unemployment Rate (%)"].dropna().median()
top_c     = view.groupby("country")["Divergence Index"].mean().idxmax() if not view.empty else "N/A"

gdp_ok  = avg_gdp >= med_gdp
unemp_ok = avg_unemp <= med_unemp
div_ok  = avg_div >= 0

kpi_row([
    render_kpi_card("Avg GDP Growth",       f"{avg_gdp:.2f}%",         "GDP",
                    delta=avg_gdp - med_gdp,
                    color="#2e7d32" if gdp_ok else "#c62828",
                    bg="#f7fbf4" if gdp_ok else "#fdf1f5"),
    render_kpi_card("Avg Unemployment",     f"{avg_unemp:.2f}%",       "LAB",
                    delta=-(avg_unemp - med_unemp),
                    color="#2e7d32" if unemp_ok else "#e65100",
                    bg="#f7fbf4" if unemp_ok else "#fff9f0"),
    render_kpi_card("Strongest Divergence", top_c,  "TOP",
                    color="#1565c0", bg="#f2f8fd"),
    render_kpi_card("Avg Divergence Index", f"{avg_div:+.2f}",         "DIV",
                    delta=avg_div,
                    color="#2e7d32" if div_ok else "#c62828",
                    bg="#f7fbf4" if div_ok else "#fdf1f5"),
])

# ── Insight Panel ─────────────────────────────────────────────────────────────
if not view.empty:
    c_divs = view.groupby("country")["Divergence Index"].mean().sort_values(ascending=False)
    trend  = view.groupby("year")["Divergence Index"].mean()
    slope  = (trend.iloc[-1] - trend.iloc[0]) / max(len(trend) - 1, 1) if len(trend) > 1 else 0
    trend_txt = "rising" if slope > 0.1 else "falling" if slope < -0.1 else "stable"

    bullets = [
        f"<b>{c_divs.index[0]}</b> leads with the highest average divergence index "
        f"({c_divs.iloc[0]:+.2f}), signalling GDP growth far outpacing unemployment.",
        f"<b>{c_divs.index[-1]}</b> shows the weakest divergence ({c_divs.iloc[-1]:+.2f}), "
        f"indicating labor market strain relative to output growth.",
        f"Overall divergence is <b>{trend_txt}</b> across the selected period "
        f"({'bullish' if slope > 0 else 'bearish'} macroeconomic signal).",
    ]
    if 2020 in view["year"].values and 2019 in view["year"].values:
        pre  = view[view["year"] == 2019]["GDP Growth (%)"].mean()
        post = view[view["year"] == 2020]["GDP Growth (%)"].mean()
        bullets.append(
            f"COVID-19 (2020) shifted average GDP growth from <b>{pre:.1f}%</b> "
            f"to <b>{post:.1f}%</b> across selected economies."
        )
    insight_panel("Key Economic Insights", bullets)

st.divider()

# ── Bar charts ────────────────────────────────────────────────────────────────
col_l, col_r = st.columns(2)
with col_l:
    fig = px.line(
        view.dropna(subset=["GDP Growth (%)"]).sort_values(["country", "year"]),
        x="year", y="GDP Growth (%)", color="country",
        markers=True, title="GDP Growth (%) Over Time",
        color_discrete_map=color_map,
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.update_traces(
        hovertemplate="<b>%{fullData.name}</b><br>Year: %{x}<br>GDP Growth: %{y:.2f}%<extra></extra>",
    )
    add_events_to_fig(fig)
    fig.update_layout(margin=dict(t=40, b=20))
    fig.update_xaxes(range=[year_range[0] - 0.5, year_range[1] + 0.5], dtick=2)
    fig.update_yaxes(showgrid=False)
    st.plotly_chart(fig, use_container_width=True)
    if not view.empty:
        _gdp_avg = view.groupby("country")["GDP Growth (%)"].mean()
        key_takeaways([
            f"<b>{_gdp_avg.idxmax()}</b> averaged {_gdp_avg.max():.1f}% annual GDP growth — the highest in the group and one of the highest sustained growth rates globally over this period, powered by state-directed investment, infrastructure spending, and a manufacturing export engine operating at scale.",
            f"<b>{_gdp_avg.idxmin()}</b> recorded the lowest average GDP growth at {_gdp_avg.min():.1f}% p.a. — as a mature, services-driven economy deeply exposed to global financial flows, it is the most vulnerable to external shocks and trade cycle downturns.",
            "The <b>2015 dip</b> visible in multiple economies reflects China's stock market crash and the commodity supercycle collapse, which rippled across Asia through trade linkages and capital flow reversals.",
            "<b>2020</b> is the defining event: every economy crossed the zero line into negative territory simultaneously — the only time since World War II that all four experienced synchronised GDP contraction, driven by COVID-19 lockdowns destroying services output overnight.",
            "The dashed zero line is the <b>recession boundary</b> — any observation below it means economic contraction. Crossing it in 2020 was historically unprecedented in its speed and synchronisation across Asia.",
        ])

with col_r:
    avg_df = (
        view.groupby("country")["Divergence Index"].mean()
        .reset_index().sort_values("Divergence Index", ascending=False)
    )
    avg_df["color"] = avg_df["Divergence Index"].apply(lambda v: "#2e7d32" if v >= 0 else "#c62828")
    fig = px.bar(
        avg_df, x="country", y="Divergence Index", color="country",
        title="Avg Divergence Index by Country (GDP – Unemployment)",
        color_discrete_sequence=avg_df["color"].tolist(),
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.update_traces(hovertemplate="<b>%{x}</b><br>Divergence: %{y:+.2f}<extra></extra>")
    fig.update_layout(margin=dict(t=40, b=20), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    if not view.empty:
        _div_avg = view.groupby("country")["Divergence Index"].mean().sort_values(ascending=False)
        key_takeaways([
            f"<b>{_div_avg.index[0]}</b> leads with the highest average divergence index of {_div_avg.iloc[0]:+.2f} — this means GDP growth exceeded unemployment by this margin on average each year, a sign of an economy where output growth is decoupled from job market pressures.",
            f"<b>{_div_avg.index[-1]}</b> sits at the bottom with {_div_avg.iloc[-1]:+.2f} — a structurally concerning signal that economic output growth is not being converted into proportional employment gains, suggesting jobless growth or deep informal sector dominance.",
            "Green bars represent economies where GDP growth outpaces unemployment (healthy), red bars indicate the opposite. The <b>height difference between the tallest and shortest bar</b> measures the macro inequality between these four economies.",
            "This single chart is arguably the most policy-relevant in the dashboard: a country can have positive GDP growth and still fail its workers if the divergence index is low or negative.",
        ], color="#2e7d32")

# ── Quadrant Scatter ──────────────────────────────────────────────────────────
st.subheader("GDP Growth vs Unemployment — Economic Quadrants")
med_x = view["GDP Growth (%)"].median()
med_y = view["Unemployment Rate (%)"].median()

fig_s = px.scatter(
    view.dropna(subset=["GDP Growth (%)", "Unemployment Rate (%)"]),
    x="GDP Growth (%)", y="Unemployment Rate (%)",
    color="country", size_max=16,
    custom_data=["year", "country", "Divergence Index"],
    trendline="ols", height=520, opacity=0.82,
    title="GDP Growth vs Unemployment Rate (OLS per country)",
    color_discrete_map=color_map,
)
fig_s.update_traces(hovertemplate=(
    "<b>%{customdata[1]}</b> (%{customdata[0]})<br>"
    "GDP Growth: %{x:.2f}%<br>Unemployment: %{y:.2f}%<br>"
    "Divergence Index: %{customdata[2]:+.2f}<extra></extra>"
))

# Quadrant background zones
x0 = view["GDP Growth (%)"].min() - 1
x1 = view["GDP Growth (%)"].max() + 1
y0 = view["Unemployment Rate (%)"].min() - 0.5
y1 = view["Unemployment Rate (%)"].max() + 0.5

for (qx0, qx1, qy0, qy1, fill, label, ax, ay) in [
    (x0, med_x, med_y, y1, "rgba(244,67,54,0.08)",   "Structural\nImbalance", (x0+med_x)/2, y1-0.3),
    (med_x, x1, med_y, y1, "rgba(76,175,80,0.08)",   "Strong\nEconomy",      (med_x+x1)/2, y1-0.3),
    (x0, med_x, y0, med_y, "rgba(244,67,54,0.08)",   "Weak\nEconomy",        (x0+med_x)/2, y0+0.3),
    (med_x, x1, y0, med_y, "rgba(33,150,243,0.08)",  "Slow &\nStable",       (med_x+x1)/2, y0+0.3),
]:
    fig_s.add_shape(type="rect", x0=qx0, x1=qx1, y0=qy0, y1=qy1,
                    fillcolor=fill, line_width=0, layer="below")
    fig_s.add_annotation(x=ax, y=ay, text=label, showarrow=False,
                         font=dict(size=9, color="#777"), opacity=0.75)

fig_s.add_hline(y=med_y, line_dash="dash", line_color="rgba(120,120,120,0.35)")
fig_s.add_vline(x=med_x, line_dash="dash", line_color="rgba(120,120,120,0.35)")
fig_s.update_layout(margin=dict(t=40, b=20))
st.plotly_chart(fig_s, use_container_width=True)
if not view.empty:
    key_takeaways([
        f"Countries clustering in the <b>'Strong Economy'</b> quadrant (high GDP growth, low unemployment) are the macro ideal — growth is broad-based and inclusive. <b>{top_c}</b> spends the most time here, though its low unemployment figures require contextual interpretation given state employment policies.",
        "The <b>'Structural Imbalance'</b> quadrant (low growth, high unemployment) is the most dangerous zone — economies here face rising social pressure, fiscal strain from welfare spending, and political risk. Avoiding this quadrant is the central challenge for economic policymakers.",
        "The <b>2020 COVID-19 shock</b> moves nearly all data points sharply left into negative GDP territory — the horizontal spread of the 2020 points shows how differently each economy's unemployment responded to the same growth collapse, a function of labour market flexibility and government intervention speed.",
        "OLS trendlines with a <b>negative slope</b> indicate that as GDP growth rises, unemployment falls — the textbook growth-absorption relationship. A positive slope signals that growth and unemployment rise together, pointing to economic overheating or measurement distortions.",
        "The divergence index encoded in the hover tooltip lets you read both axes simultaneously: the further right and lower a data point, the healthier the macro environment for that country-year.",
    ])

# ── Divergence Over Time ──────────────────────────────────────────────────────
st.subheader("Divergence Index Over Time")
div_t = view.dropna(subset=["Divergence Index"]).sort_values("year")
fig = px.line(div_t, x="year", y="Divergence Index", color="country", markers=True, color_discrete_map=color_map)
fig.update_traces(
    hovertemplate="<b>%{fullData.name}</b><br>Year: %{x}<br>Divergence: %{y:+.2f}<extra></extra>",
)
fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="neutral")
add_events_to_fig(fig)
fig.update_layout(margin=dict(t=40, b=20))
fig.update_xaxes(range=[year_range[0] - 0.5, year_range[1] + 0.5], dtick=2)
st.plotly_chart(fig, use_container_width=True)
if not view.empty:
    key_takeaways([
        f"Divergence is <b>{trend_txt}</b> over 2011\u20132020 — {'a positive macro signal: on average, these economies are generating more output relative to unemployment, suggesting improving economic efficiency and labour absorption capacity' if slope > 0 else 'a warning signal: unemployment is growing faster than GDP output, or GDP growth is decelerating faster than job losses, compressing the gap between the two'}.",
        f"<b>{c_divs.index[0]}</b> sustains the highest divergence line throughout the period — its GDP growth so consistently outpaces unemployment that its line sits structurally above all peers, reflecting an economy where the growth model is genuinely labour-efficient (or where unemployment is systematically underreported).",
        "The <b>neutral zero line</b> is the policy benchmark: when a country's divergence index falls below zero, GDP growth is no longer sufficient to offset unemployment — a politically and socially dangerous threshold.",
        "The <b>2020 COVID-19 collapse</b> is the most dramatic single-year event in this chart: every line plunges simultaneously as GDP growth crashes into negative territory, while unemployment responds more slowly — proving that GDP is a faster-moving crisis indicator than unemployment data, which lags by months due to survey timing and reporting cycles.",
        "Recovery trajectories after 2020 will diverge based on each economy's fiscal capacity, vaccine rollout speed, and exposure to global trade — making the post-2020 divergence trend the critical variable to watch for assessing long-term macro health.",
    ], color="#1565c0")

# ── Summary Table ─────────────────────────────────────────────────────────────
st.subheader("Country Rankings")
summary_table(view, agg_cols={
    "Avg GDP Growth (%)": "GDP Growth (%)",
    "Avg Unemployment (%)": "Unemployment Rate (%)",
    "Avg Divergence Index": "Divergence Index",
})

# ── Conclusion ────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style='background:#e8f5e9; padding:20px 24px; border-radius:8px; margin-top:16px;'>
  <h3 style='color:#1b5e20; margin-top:0;'>Conclusion — RQ 2: Which nations show the strongest divergence between GDP growth and unemployment rates?</h3>
  <p style='font-size:15px; color:#222;'>
    The divergence index (GDP Growth % − Unemployment Rate %) reveals that Asian economies are <b>not converging</b> in their macro performance — each follows a distinct growth-employment dynamic over 2011–2020.
  </p>
  <ul style='font-size:15px; color:#333; line-height:1.8;'>
    <li><b>China</b> consistently leads in divergence: double-digit GDP growth far outpaced its already-low unemployment rate, reflecting the efficiency of state-directed investment and export-led industrialisation.</li>
    <li><b>India</b> shows the weakest divergence — moderate GDP growth coexists with persistently high unemployment, exposing a structural gap between economic output and job creation, particularly in formal sectors.</li>
    <li><b>Singapore and Hong Kong</b> occupy a middle position: tight labour markets keep unemployment low, but mature economies limit GDP growth headroom, producing moderate divergence scores.</li>
    <li>The <b>2020 COVID-19 shock</b> compressed divergence across all economies as GDP growth collapsed, while unemployment responded with a lag — highlighting that GDP is a more immediate crisis indicator than unemployment data.</li>
  </ul>
  <p style='font-size:15px; color:#222;'>
    <b>Answer:</b> <b>China</b> shows the strongest positive divergence, driven by high GDP growth relative to unemployment. <b>India</b> shows the weakest divergence, indicating that economic growth has not translated proportionally into employment gains — a key policy risk for an economy with a large young workforce.
  </p>
</div>
""", unsafe_allow_html=True)

