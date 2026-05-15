"""
Use Case 1 — Ana Silva (ECB Policy Analyst)
Interest Rate changes vs Unemployment Rate across Asian economies.
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.topbar import render_topbar
from components.ui_helpers import (
    COUNTRY_FLAGS,
    render_kpi_card, kpi_row, insight_panel,
    add_events_to_fig, summary_table, key_takeaways,
)
from services.data_service import load_development_master

render_topbar(active="Interest_Rate_Employment")

st.title("Interest Rate & Unemployment")
st.caption("Persona: Ana Silva — Central Bank Policy Analyst | How do interest rate changes correlate with unemployment trends? | Period: 2011–2020 (post-GFC to COVID onset)")

df = load_development_master()
df["country"] = df["country"].str.strip()  # Clean whitespace
# df_clean: used only for correlation scatter (needs both columns present)
df_clean = df.dropna(subset=["Interest Rate (%)", "Unemployment Rate (%)"])
# Use the full dataset for country list and year range so no year is excluded
countries = sorted(c for c in df["country"].unique() if c != "Japan")
year_min, year_max = int(df["year"].min()), int(df["year"].max())

# Define consistent country colors (Singapore = green)
color_map = {
    "Singapore": "#00aa55",  # Green
    "China": "#1f77b4",      # Blue
    "Hong Kong SAR China": "#ff7f0e",  # Orange
    "India": "#d62728",      # Red
}

# ── Filters ──────────────────────────────────────────────────────────────────
year_range = (year_min, 2020)
selected = st.multiselect(
    "Countries", options=countries, default=countries,
    format_func=lambda c: c,
    key="ir_countries",
)

view = df_clean[
    df_clean["country"].isin(selected) & df_clean["year"].between(*year_range)
].copy()

# Coverage note for countries with shorter time series.
selected_max_year = (
    df_clean[df_clean["country"].isin(selected)]
    .groupby("country")["year"]
    .max()
)
truncated = selected_max_year[selected_max_year < year_range[1]]
if not truncated.empty:
    parts = [f"{country}: data through {int(last_year)}" for country, last_year in truncated.items()]
    st.info("Data coverage note -> " + " | ".join(parts))

# ── KPI Cards ────────────────────────────────────────────────────────────────
avg_ir    = view["Interest Rate (%)"].mean()
avg_unemp = view["Unemployment Rate (%)"].mean()
n_countries = view["country"].nunique()
med_ir    = df_clean["Interest Rate (%)"].median()
med_unemp = df_clean["Unemployment Rate (%)"].median()

corr = view[["Interest Rate (%)", "Unemployment Rate (%)"]].corr().iloc[0, 1]
corr_label = "positive" if corr > 0.2 else "negative" if corr < -0.2 else "neutral"
corr_icon  = "High" if abs(corr) > 0.5 else "Medium" if abs(corr) > 0.2 else "Low"

kpi_row([
    render_kpi_card("Countries",        str(n_countries),       "CNT",
                    color="#1565c0", bg="#f2f8fd"),
    render_kpi_card("Avg Interest Rate", f"{avg_ir:.2f}%",      "IR",
                    delta=avg_ir - med_ir,
                    color="#1565c0", bg="#f5faff"),
    render_kpi_card("Avg Unemployment",  f"{avg_unemp:.2f}%",   "LAB",
                    delta=-(avg_unemp - med_unemp),
                    color="#2e7d32" if avg_unemp <= med_unemp else "#e65100",
                    bg="#f7fbf4" if avg_unemp <= med_unemp else "#fff9f0"),
    render_kpi_card("IR–Unemployment\nCorrelation", f"{corr_icon} {corr:.3f}", "CORR",
                    color="#4a148c", bg="#faf2fb"),
])

# ── Insight Panel ─────────────────────────────────────────────────────────────
if not view.empty:
    high_ir_c  = view.groupby("country")["Interest Rate (%)"].mean().idxmax()
    low_unemp_c = view.groupby("country")["Unemployment Rate (%)"].mean().idxmin()
    bullets = [
        f"<b>{high_ir_c}</b> maintains the highest average interest rate, suggesting "
        "an active monetary tightening stance over the period.",
        f"<b>{low_unemp_c}</b> records the lowest average unemployment, indicating "
        "a well-absorbed labour market despite rate movements.",
        f"Overall correlation between interest rates and unemployment is "
        f"<b>{corr_label}</b> (r = {corr:.3f}), suggesting monetary policy "
        + ("transmits clearly to labour markets." if abs(corr) > 0.4 else "has limited direct labour market impact."),
    ]
    if 2020 in view["year"].values:
        ir_2020 = view[view["year"] == 2020]["Interest Rate (%)"].mean()
        bullets.append(
            f"Post-COVID (2020) average interest rate across selected economies dropped to "
            f"<b>{ir_2020:.2f}%</b>, reflecting emergency monetary easing."
        )
    insight_panel("Policy Analyst Insights", bullets, color="#1a237e", bg="#e8eaf6")

st.divider()

# Build per-metric line views so a missing IR value doesn't drop unemployment rows (e.g. 2022)
_base = df[df["country"].isin(selected) & df["year"].between(*year_range)]
line_ir = (
    _base.dropna(subset=["Interest Rate (%)"])
    .groupby(["country", "year"], as_index=False)["Interest Rate (%)"]
    .mean()
    .sort_values(["country", "year"])
)
line_unemp = (
    _base.dropna(subset=["Unemployment Rate (%)"])
    .groupby(["country", "year"], as_index=False)["Unemployment Rate (%)"]
    .mean()
    .sort_values(["country", "year"])
)

# ── Line charts ───────────────────────────────────────────────────────────────
fig = px.line(
    line_ir, x="year", y="Interest Rate (%)",
    color="country", markers=True, title="Interest Rate Over Time",
    color_discrete_map=color_map,
)
fig.update_traces(
    hovertemplate="<b>%{fullData.name}</b><br>Year: %{x}<br>Rate: %{y:.2f}%<extra></extra>",
)
add_events_to_fig(fig)
fig.update_layout(margin=dict(t=40, b=20))
fig.update_yaxes(showgrid=False)
fig.update_xaxes(range=[year_range[0] - 0.5, year_range[1] + 0.5], dtick=2)
st.plotly_chart(fig, use_container_width=True)
if not line_ir.empty:
    _ir_avg = line_ir.groupby("country")["Interest Rate (%)"].mean()
    key_takeaways([
        f"<b>{_ir_avg.idxmax()}</b> maintained the highest average interest rate ({_ir_avg.max():.1f}%) across the decade — the Reserve Bank of India kept rates elevated to fight persistent inflation driven by food prices, oil imports, and a structurally weak rupee.",
        f"<b>{_ir_avg.idxmin()}</b> held rates at just {_ir_avg.min():.1f}% on average — Singapore's MAS manages monetary policy through exchange rates rather than interest rates, making its rate environment uniquely accommodative compared to peers.",
        "The <b>2015 dip</b> visible across all economies reflects the global commodity price collapse and China's growth slowdown, which gave central banks room to ease without triggering inflation.",
        "All four economies cut rates aggressively toward <b>2020</b> — an unprecedented coordinated global easing in response to COVID-19, bringing many rates to historic lows and signalling the limits of conventional monetary policy.",
    ])

fig = px.line(
    line_unemp, x="year", y="Unemployment Rate (%)",
    color="country", markers=True, title="Unemployment Rate Over Time",
    color_discrete_map=color_map,
)
fig.update_traces(
    hovertemplate="<b>%{fullData.name}</b><br>Year: %{x}<br>Unemployment: %{y:.2f}%<extra></extra>",
)
add_events_to_fig(fig)
fig.update_layout(margin=dict(t=40, b=20))
fig.update_yaxes(showgrid=False)
fig.update_xaxes(range=[year_range[0] - 0.5, year_range[1] + 0.5], dtick=2)
st.plotly_chart(fig, use_container_width=True)
if not line_unemp.empty:
    _u_avg = line_unemp.groupby("country")["Unemployment Rate (%)"].mean()
    key_takeaways([
        f"<b>{_u_avg.idxmin()}</b> averaged just {_u_avg.min():.1f}% unemployment — a world-class labour market performance achieved through strict foreign talent policies, continuous reskilling programmes, and an economy permanently at near-full employment.",
        f"<b>{_u_avg.idxmax()}</b> averaged {_u_avg.max():.1f}% unemployment — this is likely an undercount, as India's informal sector (employing over 80% of workers) is poorly captured in official statistics, making true underemployment far higher.",
        "The <b>remarkable stability</b> from 2011–2019 across all four economies reflects the long post-GFC recovery — a decade of low rates, expanding global trade, and rising middle-class consumption that kept labour markets tight.",
        "<b>2020</b> breaks the trend: the COVID-19 shock did not raise unemployment uniformly — service-heavy Singapore and Hong Kong saw sharper spikes while China's state-directed stimulus contained its headline figures.",
    ], color="#2e7d32")

# ── Correlation scatter ───────────────────────────────────────────────────────
st.markdown("<h3 style='color:#0a3d5c;'>Correlation: Interest Rate vs Unemployment Rate</h3>", unsafe_allow_html=True)
med_x = view["Interest Rate (%)"].median()
med_y = view["Unemployment Rate (%)"].median()

fig_s = px.scatter(
    view, x="Interest Rate (%)", y="Unemployment Rate (%)",
    color="country", symbol="country",
    custom_data=["year", "country"],
    trendline="ols",
    title="Interest Rate vs Unemployment Rate (OLS trendline per country)",
    height=500, opacity=0.82,
    color_discrete_map=color_map,
)
fig_s.update_traces(hovertemplate=(
    "<b>%{customdata[1]}</b> (%{customdata[0]})<br>"
    "Interest Rate: %{x:.2f}%<br>Unemployment: %{y:.2f}%<extra></extra>"
))
fig_s.add_hline(y=med_y, line_dash="dash", line_color="rgba(120,120,120,0.35)")
fig_s.add_vline(x=med_x, line_dash="dash", line_color="rgba(120,120,120,0.35)")
fig_s.update_layout(margin=dict(t=40, b=20))
fig_s.update_yaxes(showgrid=False)
st.plotly_chart(fig_s, use_container_width=True)
key_takeaways([
    f"The pooled IR\u2013unemployment correlation is <b>r\u00a0=\u00a0{corr:.3f}</b> ({corr_label}) — {'a meaningful signal that monetary tightening accompanies labour market shifts' if abs(corr) > 0.4 else 'a weak signal confirming that interest rates are not the primary driver of employment outcomes in these economies'}.",
    "The <b>median crosshairs</b> divide the chart into four regimes: high rate + high unemployment (monetary tightening failing to create jobs), low rate + low unemployment (accommodative success), and two intermediate zones that reveal structural complexity.",
    "India's cluster in the <b>high rate, high unemployment</b> zone is the most telling — despite years of rate cuts, unemployment has not fallen proportionally, pointing to supply-side barriers: skills gaps, agricultural dominance, and weak formal sector job creation.",
    "Singapore's cluster in the <b>low rate, low unemployment</b> corner confirms that its labour market success is institutional, not monetary — active workforce management, not rate policy, explains the outcome.",
    "OLS trendlines per country slope differently — some positive, some negative — proving there is <b>no universal monetary transmission rule</b> across Asian economies. Each requires its own policy toolkit.",
], color="#4a148c")

# ── Per-country correlation ranking ───────────────────────────────────────────
st.subheader("Which country shows the strongest IR–Unemployment link?")
country_corrs = []
for c, grp in view.groupby("country"):
    clean = grp[["Interest Rate (%)", "Unemployment Rate (%)"]].dropna()
    if len(clean) >= 3:
        r = clean.corr().iloc[0, 1]
        country_corrs.append({"Country": c, "r": round(r, 3)})
if country_corrs:
    corr_df = pd.DataFrame(country_corrs).sort_values("r")
    fig_cr = px.bar(
        corr_df, x="r", y="Country", orientation="h",
        title="Pearson r: Interest Rate vs Unemployment Rate (per country)",
        color="Country", color_discrete_map=color_map,
        height=280,
    )
    fig_cr.add_vline(x=0, line_dash="dash", line_color="gray")
    fig_cr.add_vline(x=0.5, line_dash="dot", line_color="rgba(0,150,0,0.4)",
                     annotation_text="strong +", annotation_position="top right")
    fig_cr.add_vline(x=-0.5, line_dash="dot", line_color="rgba(200,0,0,0.4)",
                     annotation_text="strong −", annotation_position="top left")
    fig_cr.update_traces(hovertemplate="<b>%{y}</b><br>r = %{x:.3f}<extra></extra>")
    fig_cr.update_layout(margin=dict(t=40, b=20), showlegend=False)
    fig_cr.update_xaxes(range=[-1, 1], title="Correlation coefficient (r)")
    st.plotly_chart(fig_cr, use_container_width=True)
    _sorted = pd.DataFrame(country_corrs).sort_values("r")
    _pos = _sorted.iloc[-1]
    _neg = _sorted.iloc[0]
    _bullets = [
        f"<b>{_pos['Country']}</b> shows the strongest IR\u2013unemployment link (r\u00a0=\u00a0{_pos['r']:+.3f}) — this economy's labour market is most sensitive to monetary policy changes, meaning central bank decisions here have direct and measurable employment consequences.",
        f"A positive correlation means rate hikes accompany <b>rising unemployment</b> — textbook monetary contraction. A negative correlation means rate hikes accompanied <b>falling unemployment</b>, suggesting the economy was overheating and tightening was appropriate, not harmful.",
    ]
    if _neg["r"] < -0.2:
        _bullets.append(f"<b>{_neg['Country']}</b> shows a negative link (r\u00a0=\u00a0{_neg['r']:+.3f}) — rate increases here coincided with tighter labour markets, consistent with a pro-cyclical monetary stance responding to overheating rather than causing unemployment.")
    _bullets.append("The <b>spread of r values</b> across the four economies is the key finding: ranging from strongly negative to strongly positive, it confirms that a single regional monetary policy would be deeply inappropriate — each economy requires calibrated domestic intervention.")
    key_takeaways(_bullets, color="#4a148c")

# ── Heatmaps ──────────────────────────────────────────────────────────────────
st.markdown("<h3 style='color:#0a3d5c;'>Rate & Unemployment Heatmaps</h3>", unsafe_allow_html=True)
st.caption("Colour intensity shows the level per country per year — darker = higher value.")

_base_heat = df[df["country"].isin(selected) & df["year"].between(*year_range)]

hm_col_l, hm_col_r = st.columns(2)

with hm_col_l:
    ir_pivot = (
        _base_heat.dropna(subset=["Interest Rate (%)"])
        .groupby(["country", "year"])["Interest Rate (%)"].mean()
        .unstack("year")
    )
    if not ir_pivot.empty:
        fig_hm1 = go.Figure(go.Heatmap(
            z=ir_pivot.values,
            x=[str(y) for y in ir_pivot.columns],
            y=ir_pivot.index.tolist(),
            colorscale="Blues",
            hovertemplate="<b>%{y}</b><br>Year: %{x}<br>Interest Rate: %{z:.2f}%<extra></extra>",
            colorbar=dict(title="Rate %", thickness=12),
        ))
        fig_hm1.update_layout(
            title="Interest Rate (%) — Country × Year",
            margin=dict(t=40, b=20), height=300,
            xaxis=dict(title="Year"), yaxis=dict(title=""),
        )
        st.plotly_chart(fig_hm1, use_container_width=True)

with hm_col_r:
    un_pivot = (
        _base_heat.dropna(subset=["Unemployment Rate (%)"])
        .groupby(["country", "year"])["Unemployment Rate (%)"].mean()
        .unstack("year")
    )
    if not un_pivot.empty:
        fig_hm2 = go.Figure(go.Heatmap(
            z=un_pivot.values,
            x=[str(y) for y in un_pivot.columns],
            y=un_pivot.index.tolist(),
            colorscale="Oranges",
            hovertemplate="<b>%{y}</b><br>Year: %{x}<br>Unemployment: %{z:.2f}%<extra></extra>",
            colorbar=dict(title="Unemp %", thickness=12),
        ))
        fig_hm2.update_layout(
            title="Unemployment Rate (%) — Country × Year",
            margin=dict(t=40, b=20), height=300,
            xaxis=dict(title="Year"), yaxis=dict(title=""),
        )
        st.plotly_chart(fig_hm2, use_container_width=True)

key_takeaways([
    "The <b>blue intensity heatmap</b> immediately reveals India's monetary stance: consistently the darkest row, India maintained rates 2–5x higher than Singapore throughout the decade — a reflection of its inflation management challenges rather than a policy choice to suppress growth.",
    "Singapore and Hong Kong appear as the <b>lightest rows</b> in the blue heatmap — not because their central banks are inactive, but because they operate through different mechanisms: exchange rate bands, reserve requirements, and macroprudential tools rather than rate adjustments.",
    "The <b>orange unemployment heatmap</b> shows remarkable temporal persistence: the ranking of countries by unemployment in 2011 is almost identical to 2020, suggesting that structural factors — education quality, labour market institutions, sectoral composition — lock in unemployment outcomes over decade-long horizons.",
    "<b>Cross-reading both heatmaps</b> by year reveals the key insight: years where India's rate darkened (tightening) did not consistently brighten its orange row (falling unemployment), undermining the classical monetary transmission theory for this economy.",
    "The <b>2020 column</b> in the orange heatmap shows divergence: some economies darkened (rising unemployment), others did not change much — reflecting how differently each country's institutions absorbed the same global shock.",
], color="#0a3d5c")

# ── Summary Table ─────────────────────────────────────────────────────────────
st.subheader("Country Summary")
summary_table(view, agg_cols={
    "Avg Interest Rate (%)": "Interest Rate (%)",
    "Avg Unemployment (%)": "Unemployment Rate (%)",
})

# ── Conclusion ────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style='background:#e8eaf6; padding:20px 24px; border-radius:8px; margin-top:16px;'>
  <h3 style='color:#1a237e; margin-top:0;'>Conclusion — RQ 1: How do interest rate changes correlate with unemployment trends across Asian economies?</h3>
  <p style='font-size:15px; color:#222;'>
    Across China, Hong Kong, India, and Singapore (2011–2020), the relationship between interest rates and unemployment is <b>weak and heterogeneous</b> — no single monetary policy pattern reliably predicts labour market outcomes across all four economies.
  </p>
  <ul style='font-size:15px; color:#333; line-height:1.8;'>
    <li><b>India</b> maintained the highest interest rates throughout the period, yet its labour market showed persistent structural unemployment, indicating that rate levels alone cannot resolve supply-side employment challenges.</li>
    <li><b>Singapore</b> held near-zero rates with consistently low unemployment, reflecting a structurally tight labour market driven by skills policy rather than monetary conditions.</li>
    <li><b>China and Hong Kong</b> show moderate and diverging correlations, suggesting that domestic fiscal policy and trade dynamics play a larger role than monetary policy in shaping employment outcomes.</li>
    <li>The universal rate cuts in <b>2020</b> (COVID-19 response) confirm that central banks reacted symmetrically to the external shock, yet unemployment impacts differed significantly across economies.</li>
  </ul>
  <p style='font-size:15px; color:#222;'>
    <b>Answer:</b> Interest rate changes show <b>limited and country-specific correlation</b> with unemployment across Asian economies. Monetary policy transmission to labour markets is mediated by structural factors — labour market flexibility, trade exposure, and institutional capacity — rather than rate levels alone.
  </p>
</div>
""", unsafe_allow_html=True)

