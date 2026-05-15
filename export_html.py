"""
Export all dashboard pages to standalone interactive HTML files.
Run from the project root:
    python export_html.py

Outputs to:  export/
  page1_interest_rate_employment.html
  page2_gdp_divergence.html
  page3_population_growth.html
  page4_market_monitor.html
  index.html
"""

import os
import sys
import types

# ── Mock Streamlit before anything else imports it ────────────────────────────
_st = types.ModuleType("streamlit")
_st.cache_data = lambda **kw: (lambda f: f)  # no-op decorator factory
_st.error   = lambda *a, **kw: print("ERROR:", *a)
_st.warning = lambda *a, **kw: print("WARN:", *a)
_st.stop    = lambda: None
_st.info    = lambda *a, **kw: None
_st.markdown = lambda *a, **kw: None
_st.divider  = lambda: None
sys.modules["streamlit"] = _st

# ── Now it's safe to import project code ─────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

from services.data_service import load_development_master, load_market_master, load_macro_master

# ── Constants ─────────────────────────────────────────────────────────────────
COLOR_MAP = {
    "Singapore":           "#00aa55",
    "China":               "#1f77b4",
    "Hong Kong SAR China": "#ff7f0e",
    "India":               "#d62728",
}

ECONOMIC_EVENTS = [
    {"year": 2015, "label": "China mkt crash"},
    {"year": 2018, "label": "Trade war"},
    {"year": 2020, "label": "COVID-19"},
]

YEAR_RANGE = (2011, 2020)

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "export")
os.makedirs(OUT_DIR, exist_ok=True)

# ── HTML helpers ──────────────────────────────────────────────────────────────
_plotly_cdn_included = False

def fig_div(fig, cols=1):
    """Return Plotly figure as an HTML div string. First call includes CDN JS."""
    global _plotly_cdn_included
    include_js = "cdn" if not _plotly_cdn_included else False
    _plotly_cdn_included = True
    html = pio.to_html(fig, full_html=False, include_plotlyjs=include_js,
                       config={"displayModeBar": False})
    width = "100%" if cols == 1 else f"calc({100//cols}% - 12px)"
    return f'<div style="width:{width};min-width:0">{html}</div>'


def row(*divs):
    """Wrap multiple fig_div strings in a flexbox row."""
    inner = "".join(divs)
    return f'<div style="display:flex;gap:20px;flex-wrap:wrap;margin:0 0 8px">{inner}</div>'


def section_head(text, color="#1565c0", size="h2"):
    return f'<{size} style="color:{color};margin:32px 0 6px">{text}</{size}>'


def caption(text):
    return f'<p style="color:#777;font-size:0.88em;margin:-4px 0 12px">{text}</p>'


def divider():
    return '<hr style="border:none;border-top:1px solid #e0e0e0;margin:32px 0">'


def takeaways(bullets, color="#1565c0"):
    items = "".join(f"<li style='margin:3px 0;line-height:1.5'>{b}</li>" for b in bullets)
    return (
        f'<div style="background:#f8f9ff;border-left:4px solid {color};'
        f'padding:10px 16px;border-radius:0 4px 4px 0;margin:4px 0 20px;font-size:0.84rem;color:#1a1a2e">'
        f'<b style="color:{color}">Key Takeaways</b>'
        f'<ul style="margin:5px 0 0;padding-left:16px">{items}</ul></div>'
    )


def insight_box(title, bullets, color="#1565c0", bg="#e3f2fd"):
    items = "".join(f"<li style='margin:5px 0;line-height:1.55'>{b}</li>" for b in bullets)
    return (
        f'<div style="background:{bg};border:1px solid rgba(10,61,92,0.10);'
        f'border-radius:8px;padding:14px 20px;margin-bottom:1rem">'
        f'<strong style="color:{color};font-size:0.92rem">{title}</strong>'
        f'<ul style="margin:8px 0 0;padding-left:18px;color:#1a1a2e;font-size:0.86rem">{items}</ul>'
        f'</div>'
    )


def kpi_cards_html(cards):
    """cards = list of (label, value, color, bg)"""
    inner = "".join(
        f'<div style="background:{bg};border-radius:10px;padding:14px 18px;'
        f'border-left:4px solid {color};min-width:140px;flex:1">'
        f'<div style="font-size:0.78rem;color:#666">{label}</div>'
        f'<div style="font-size:1.6rem;font-weight:700;color:{color};margin-top:4px">{value}</div>'
        f'</div>'
        for label, value, color, bg in cards
    )
    return f'<div style="display:flex;gap:16px;flex-wrap:wrap;margin:16px 0 24px">{inner}</div>'


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — HSLU Economic Dashboard</title>
<style>
  body{{font-family:'Segoe UI',Arial,sans-serif;max-width:1400px;margin:0 auto;
        padding:24px 40px 60px;background:#fff;color:#1a1a2e}}
  h1{{color:#0a3d5c;border-bottom:3px solid #0a3d5c;padding-bottom:10px}}
  a{{color:#1565c0}}
  .back{{margin-bottom:20px;font-size:0.9em}}
</style>
</head>
<body>
<div class="back"><a href="index.html">← Back to Overview</a></div>
{body}
</body>
</html>"""

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>HSLU Economic Dashboard</title>
<style>
  body{{font-family:'Segoe UI',Arial,sans-serif;max-width:900px;margin:40px auto;padding:0 40px;color:#1a1a2e}}
  h1{{color:#0a3d5c;border-bottom:3px solid #0a3d5c;padding-bottom:10px}}
  .cards{{display:flex;gap:20px;flex-wrap:wrap;margin:28px 0}}
  .card{{flex:1;min-width:200px;border-radius:10px;padding:18px 22px;text-decoration:none;color:inherit;
          border:1px solid #e0e0e0;transition:box-shadow .15s}}
  .card:hover{{box-shadow:0 4px 16px rgba(0,0,0,.12)}}
  .card h3{{margin:0 0 8px;font-size:1.05rem}}
  .card p{{margin:0;font-size:0.85rem;color:#555}}
  table{{width:100%;border-collapse:collapse;margin:16px 0;font-size:0.9rem}}
  th{{background:#f0f4fa;text-align:left;padding:8px 12px;border:1px solid #ddd}}
  td{{padding:8px 12px;border:1px solid #eee}}
  code{{background:#f0f4fa;padding:1px 5px;border-radius:3px;font-size:0.85em}}
</style>
</head>
<body>
<h1>HSLU Economic Dashboard</h1>
<p style="color:#555">HSLU MSc Applied Information &amp; Data Science — Macroeconomic Analysis of Asian Economies<br>
<strong>Economies:</strong> China, Hong Kong SAR China, India, Singapore &nbsp;|&nbsp;
<strong>Period:</strong> 2011–2020</p>

<div class="cards">
  <a class="card" href="page1_interest_rate_employment.html" style="border-top:4px solid #1a237e;background:#f5f7ff">
    <h3 style="color:#1a237e">RQ 1 — Interest Rate &amp; Employment</h3>
    <p>How do interest rate changes correlate with unemployment trends across Asian economies?</p>
    <p style="margin-top:8px;color:#999;font-size:0.8rem">Persona: Ana Silva — Central Bank Policy Analyst</p>
  </a>
  <a class="card" href="page2_gdp_divergence.html" style="border-top:4px solid #1b5e20;background:#f5fff7">
    <h3 style="color:#1b5e20">RQ 2 — GDP Divergence</h3>
    <p>Which nations show the strongest divergence between GDP growth and unemployment rates?</p>
    <p style="margin-top:8px;color:#999;font-size:0.8rem">Persona: Park Jun-ho — Economic Risk Researcher</p>
  </a>
  <a class="card" href="page3_population_growth.html" style="border-top:4px solid #880e4f;background:#fff5f9">
    <h3 style="color:#880e4f">RQ 3 — Population &amp; Workforce</h3>
    <p>How does interest rate volatility affect population growth and workforce employment?</p>
    <p style="margin-top:8px;color:#999;font-size:0.8rem">Persona: Dr. Maria Stern — Professor of Macroeconomics</p>
  </a>
  <a class="card" href="page4_market_monitor.html" style="border-top:4px solid #e65100;background:#fff9f5">
    <h3 style="color:#e65100">Market Monitor</h3>
    <p>Daily equity indices, FX vs EUR, Brent Oil, US 10Y Yield, and VIX.</p>
    <p style="margin-top:8px;color:#999;font-size:0.8rem">Contextual daily market data</p>
  </a>
</div>

<h2 style="color:#0a3d5c">Data Inventory</h2>
<table>
  <tr><th>Dataset</th><th>Metrics</th><th>Coverage</th><th>Granularity</th></tr>
  <tr><td><code>development_master</code></td><td>GDP Growth, Interest Rate, Unemployment, Population Growth</td><td>2011–2024 (IR: 2011–2020 for all 4)</td><td>Annual</td></tr>
  <tr><td><code>market_master</code></td><td>Equity index closes, FX vs EUR</td><td>Daily</td><td>Daily</td></tr>
  <tr><td><code>macro_master</code></td><td>Brent Oil, US 10Y Yield, VIX</td><td>Daily</td><td>Daily</td></tr>
</table>
</body>
</html>"""


# ── Shared figure helpers ─────────────────────────────────────────────────────
def add_events(fig):
    for ev in ECONOMIC_EVENTS:
        fig.add_vline(
            x=ev["year"], line_width=1.2, line_dash="dot",
            line_color="rgba(100,100,100,0.45)",
            annotation_text=ev["label"], annotation_position="top right",
            annotation_font_size=8.5, annotation_font_color="#666",
        )
    return fig


# ═════════════════════════════════════════════════════════════════════════════
# PAGE 1 — Interest Rate & Employment
# ═════════════════════════════════════════════════════════════════════════════
def build_page1():
    print("  Building Page 1 — Interest Rate & Employment…")
    df = load_development_master()
    df["country"] = df["country"].str.strip()
    df_clean = df.dropna(subset=["Interest Rate (%)", "Unemployment Rate (%)"])
    countries = sorted(c for c in df["country"].unique() if c != "Japan")
    year_min = int(df["year"].min())
    yr = YEAR_RANGE

    _base = df[df["country"].isin(countries) & df["year"].between(*yr)]
    view  = df_clean[df_clean["country"].isin(countries) & df_clean["year"].between(*yr)].copy()

    line_ir = (
        _base.dropna(subset=["Interest Rate (%)"])
        .groupby(["country", "year"], as_index=False)["Interest Rate (%)"].mean()
        .sort_values(["country", "year"])
    )
    line_unemp = (
        _base.dropna(subset=["Unemployment Rate (%)"])
        .groupby(["country", "year"], as_index=False)["Unemployment Rate (%)"].mean()
        .sort_values(["country", "year"])
    )

    corr = view[["Interest Rate (%)", "Unemployment Rate (%)"]].corr().iloc[0, 1]
    corr_label = "positive" if corr > 0.2 else "negative" if corr < -0.2 else "neutral"
    avg_ir    = view["Interest Rate (%)"].mean()
    avg_unemp = view["Unemployment Rate (%)"].mean()

    # KPI cards
    kpi = kpi_cards_html([
        ("Countries",              "4",                "#1565c0", "#f2f8fd"),
        ("Avg Interest Rate",      f"{avg_ir:.2f}%",   "#1565c0", "#f5faff"),
        ("Avg Unemployment",       f"{avg_unemp:.2f}%","#2e7d32", "#f7fbf4"),
        ("IR–Unemployment Corr.",  f"{corr:.3f}",      "#4a148c", "#faf2fb"),
    ])

    # Insight
    high_ir_c   = view.groupby("country")["Interest Rate (%)"].mean().idxmax()
    low_unemp_c = view.groupby("country")["Unemployment Rate (%)"].mean().idxmin()
    ins = insight_box("Policy Analyst Insights", [
        f"<b>{high_ir_c}</b> maintains the highest average interest rate over the period.",
        f"<b>{low_unemp_c}</b> records the lowest average unemployment.",
        f"Overall correlation is <b>{corr_label}</b> (r = {corr:.3f}).",
    ], color="#1a237e", bg="#e8eaf6")

    # IR line chart
    fig1 = px.line(line_ir, x="year", y="Interest Rate (%)", color="country",
                   markers=True, title="Interest Rate Over Time", color_discrete_map=COLOR_MAP)
    fig1.update_traces(hovertemplate="<b>%{fullData.name}</b><br>Year: %{x}<br>Rate: %{y:.2f}%<extra></extra>")
    add_events(fig1)
    fig1.update_xaxes(range=[yr[0]-0.5, yr[1]+0.5], dtick=2)
    fig1.update_yaxes(showgrid=False)
    fig1.update_layout(margin=dict(t=40, b=20))

    _ir_avg = line_ir.groupby("country")["Interest Rate (%)"].mean()
    tk1 = takeaways([
        f"<b>{_ir_avg.idxmax()}</b> maintained the highest average interest rate ({_ir_avg.max():.1f}%).",
        f"<b>{_ir_avg.idxmin()}</b> held the lowest average rate ({_ir_avg.min():.1f}%).",
        "All four economies cut rates toward 2020, responding to COVID-19.",
    ])

    # Unemployment line chart
    fig2 = px.line(line_unemp, x="year", y="Unemployment Rate (%)", color="country",
                   markers=True, title="Unemployment Rate Over Time", color_discrete_map=COLOR_MAP)
    fig2.update_traces(hovertemplate="<b>%{fullData.name}</b><br>Year: %{x}<br>Unemployment: %{y:.2f}%<extra></extra>")
    add_events(fig2)
    fig2.update_xaxes(range=[yr[0]-0.5, yr[1]+0.5], dtick=2)
    fig2.update_yaxes(showgrid=False)
    fig2.update_layout(margin=dict(t=40, b=20))

    _u_avg = line_unemp.groupby("country")["Unemployment Rate (%)"].mean()
    tk2 = takeaways([
        f"<b>{_u_avg.idxmin()}</b> consistently recorded the lowest unemployment ({_u_avg.min():.1f}%).",
        f"<b>{_u_avg.idxmax()}</b> had the highest average unemployment ({_u_avg.max():.1f}%).",
        "Unemployment remained broadly stable until the COVID-19 shock in 2020.",
    ], color="#2e7d32")

    # OLS scatter
    med_x = view["Interest Rate (%)"].median()
    med_y = view["Unemployment Rate (%)"].median()
    try:
        fig3 = px.scatter(view, x="Interest Rate (%)", y="Unemployment Rate (%)",
                          color="country", symbol="country", custom_data=["year", "country"],
                          trendline="ols", title="Interest Rate vs Unemployment Rate (OLS per country)",
                          height=500, opacity=0.82, color_discrete_map=COLOR_MAP)
    except Exception:
        fig3 = px.scatter(view, x="Interest Rate (%)", y="Unemployment Rate (%)",
                          color="country", symbol="country", custom_data=["year", "country"],
                          title="Interest Rate vs Unemployment Rate", height=500, opacity=0.82,
                          color_discrete_map=COLOR_MAP)
    fig3.update_traces(hovertemplate=(
        "<b>%{customdata[1]}</b> (%{customdata[0]})<br>"
        "IR: %{x:.2f}%<br>Unemployment: %{y:.2f}%<extra></extra>"
    ))
    fig3.add_hline(y=med_y, line_dash="dash", line_color="rgba(120,120,120,0.35)")
    fig3.add_vline(x=med_x, line_dash="dash", line_color="rgba(120,120,120,0.35)")
    fig3.update_layout(margin=dict(t=40, b=20))
    fig3.update_yaxes(showgrid=False)

    tk3 = takeaways([
        f"Overall IR–unemployment correlation: <b>r = {corr:.3f}</b> ({corr_label}).",
        "OLS trendlines per country reveal heterogeneous relationships.",
        "Countries in the upper-left quadrant face high unemployment despite low rates.",
    ], color="#4a148c")

    # Per-country correlation bar
    country_corrs = []
    for c, grp in view.groupby("country"):
        clean = grp[["Interest Rate (%)", "Unemployment Rate (%)"]].dropna()
        if len(clean) >= 3:
            r = clean.corr().iloc[0, 1]
            country_corrs.append({"Country": c, "r": round(r, 3)})
    if country_corrs:
        corr_df = pd.DataFrame(country_corrs).sort_values("r")
        fig4 = px.bar(corr_df, x="r", y="Country", orientation="h",
                      title="Pearson r: IR vs Unemployment (per country)",
                      color="Country", color_discrete_map=COLOR_MAP, height=280)
        fig4.add_vline(x=0, line_dash="dash", line_color="gray")
        fig4.add_vline(x=0.5, line_dash="dot", line_color="rgba(0,150,0,0.4)",
                       annotation_text="strong +", annotation_position="top right")
        fig4.add_vline(x=-0.5, line_dash="dot", line_color="rgba(200,0,0,0.4)",
                       annotation_text="strong −", annotation_position="top left")
        fig4.update_traces(hovertemplate="<b>%{y}</b><br>r = %{x:.3f}<extra></extra>")
        fig4.update_layout(margin=dict(t=40, b=20), showlegend=False)
        fig4.update_xaxes(range=[-1, 1], title="Correlation coefficient (r)")
        _sorted = corr_df
        _pos = _sorted.iloc[-1]
        _neg = _sorted.iloc[0]
        tk4_bullets = [f"<b>{_pos['Country']}</b> shows the strongest correlation (r = {_pos['r']:+.3f})."]
        if _neg["r"] < -0.2:
            tk4_bullets.append(f"<b>{_neg['Country']}</b> shows a negative link (r = {_neg['r']:+.3f}).")
        tk4_bullets.append("Diverging signs across countries suggest different monetary transmission mechanisms.")
        tk4 = takeaways(tk4_bullets, color="#4a148c")
    else:
        fig4 = None
        tk4 = ""

    # Heatmaps
    _base_heat = df[df["country"].isin(countries) & df["year"].between(*yr)]
    ir_pivot = (
        _base_heat.dropna(subset=["Interest Rate (%)"])
        .groupby(["country", "year"])["Interest Rate (%)"].mean()
        .unstack("year")
    )
    un_pivot = (
        _base_heat.dropna(subset=["Unemployment Rate (%)"])
        .groupby(["country", "year"])["Unemployment Rate (%)"].mean()
        .unstack("year")
    )
    fig_hm1 = go.Figure(go.Heatmap(
        z=ir_pivot.values, x=[str(y) for y in ir_pivot.columns], y=ir_pivot.index.tolist(),
        colorscale="Blues", colorbar=dict(title="Rate %", thickness=12),
        hovertemplate="<b>%{y}</b><br>Year: %{x}<br>IR: %{z:.2f}%<extra></extra>",
    ))
    fig_hm1.update_layout(title="Interest Rate (%) — Country × Year",
                           margin=dict(t=40, b=20), height=300,
                           xaxis=dict(title="Year"), yaxis=dict(title=""))
    fig_hm2 = go.Figure(go.Heatmap(
        z=un_pivot.values, x=[str(y) for y in un_pivot.columns], y=un_pivot.index.tolist(),
        colorscale="Oranges", colorbar=dict(title="Unemp %", thickness=12),
        hovertemplate="<b>%{y}</b><br>Year: %{x}<br>Unemployment: %{z:.2f}%<extra></extra>",
    ))
    fig_hm2.update_layout(title="Unemployment Rate (%) — Country × Year",
                           margin=dict(t=40, b=20), height=300,
                           xaxis=dict(title="Year"), yaxis=dict(title=""))
    tk5 = takeaways([
        "Darker blue cells = tighter monetary policy (higher rates). India stands out with elevated rates.",
        "The orange heatmap reveals unemployment persistence across the period.",
        "Comparing both heatmaps highlights where rate changes did — or did not — coincide with unemployment shifts.",
    ], color="#0a3d5c")

    # Assemble
    body = "\n".join([
        "<h1>Interest Rate &amp; Unemployment</h1>",
        caption("Persona: Ana Silva — Central Bank Policy Analyst | How do interest rate changes correlate with unemployment trends? | Period: 2011–2020"),
        kpi,
        ins,
        divider(),
        fig_div(fig1),
        tk1,
        fig_div(fig2),
        tk2,
        section_head("Correlation: Interest Rate vs Unemployment Rate", color="#0a3d5c", size="h2"),
        fig_div(fig3),
        tk3,
        section_head("Which country shows the strongest IR–Unemployment link?", size="h3", color="#1565c0"),
        (row(fig_div(fig4, cols=2)) if fig4 else ""),
        tk4,
        section_head("Rate &amp; Unemployment Heatmaps", color="#0a3d5c", size="h2"),
        caption("Colour intensity shows the level per country per year — darker = higher value."),
        row(fig_div(fig_hm1, cols=2), fig_div(fig_hm2, cols=2)),
        tk5,
    ])

    return PAGE_TEMPLATE.format(title="Interest Rate & Employment", body=body)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE 2 — GDP Divergence
# ═════════════════════════════════════════════════════════════════════════════
def build_page2():
    print("  Building Page 2 — GDP Divergence…")
    df = load_development_master()
    df["country"] = df["country"].str.strip()
    countries = sorted(c for c in df["country"].unique() if c != "Japan")
    yr = YEAR_RANGE
    year_min = int(df["year"].min())

    view = df[df["country"].isin(countries) & df["year"].between(*yr)].copy()
    view["Divergence Index"] = view["GDP Growth (%)"] - view["Unemployment Rate (%)"]

    avg_gdp = view["GDP Growth (%)"].dropna().mean()
    avg_unemp = view["Unemployment Rate (%)"].dropna().mean()
    avg_div = view["Divergence Index"].dropna().mean()
    top_c = view.groupby("country")["Divergence Index"].mean().idxmax() if not view.empty else "N/A"

    kpi = kpi_cards_html([
        ("Avg GDP Growth",       f"{avg_gdp:.2f}%",  "#2e7d32", "#f7fbf4"),
        ("Avg Unemployment",     f"{avg_unemp:.2f}%","#1565c0", "#f2f8fd"),
        ("Strongest Divergence", top_c,              "#1565c0", "#f2f8fd"),
        ("Avg Divergence Index", f"{avg_div:+.2f}",  "#2e7d32" if avg_div >= 0 else "#c62828",
         "#f7fbf4" if avg_div >= 0 else "#fdf1f5"),
    ])

    c_divs = view.groupby("country")["Divergence Index"].mean().sort_values(ascending=False)
    trend  = view.groupby("year")["Divergence Index"].mean()
    slope  = (trend.iloc[-1] - trend.iloc[0]) / max(len(trend)-1, 1)
    trend_txt = "rising" if slope > 0.1 else "falling" if slope < -0.1 else "stable"

    bullets = [
        f"<b>{c_divs.index[0]}</b> leads with the highest average divergence index ({c_divs.iloc[0]:+.2f}).",
        f"<b>{c_divs.index[-1]}</b> shows the weakest divergence ({c_divs.iloc[-1]:+.2f}).",
        f"Overall divergence is <b>{trend_txt}</b> over the period.",
    ]
    if 2020 in view["year"].values and 2019 in view["year"].values:
        pre  = view[view["year"] == 2019]["GDP Growth (%)"].mean()
        post = view[view["year"] == 2020]["GDP Growth (%)"].mean()
        bullets.append(f"COVID-19 (2020) shifted avg GDP growth from <b>{pre:.1f}%</b> to <b>{post:.1f}%</b>.")
    ins = insight_box("Key Economic Insights", bullets)

    # GDP line
    fig1 = px.line(
        view.dropna(subset=["GDP Growth (%)"]).sort_values(["country", "year"]),
        x="year", y="GDP Growth (%)", color="country",
        markers=True, title="GDP Growth (%) Over Time", color_discrete_map=COLOR_MAP)
    fig1.add_hline(y=0, line_dash="dash", line_color="gray")
    fig1.update_traces(hovertemplate="<b>%{fullData.name}</b><br>Year: %{x}<br>GDP Growth: %{y:.2f}%<extra></extra>")
    add_events(fig1)
    fig1.update_xaxes(range=[yr[0]-0.5, yr[1]+0.5], dtick=2)
    fig1.update_yaxes(showgrid=False)
    fig1.update_layout(margin=dict(t=40, b=20))

    # Avg divergence bar
    avg_df = (view.groupby("country")["Divergence Index"].mean()
              .reset_index().sort_values("Divergence Index", ascending=False))
    avg_df["color"] = avg_df["Divergence Index"].apply(lambda v: "#2e7d32" if v >= 0 else "#c62828")
    fig2 = px.bar(avg_df, x="country", y="Divergence Index", color="country",
                  title="Avg Divergence Index by Country (GDP – Unemployment)",
                  color_discrete_sequence=avg_df["color"].tolist())
    fig2.add_hline(y=0, line_dash="dash", line_color="gray")
    fig2.update_traces(hovertemplate="<b>%{x}</b><br>Divergence: %{y:+.2f}<extra></extra>")
    fig2.update_layout(margin=dict(t=40, b=20), showlegend=False)

    _gdp_avg = view.groupby("country")["GDP Growth (%)"].mean()
    tk1 = takeaways([
        f"<b>{_gdp_avg.idxmax()}</b> averaged the highest GDP growth ({_gdp_avg.max():.1f}% p.a.).",
        f"<b>{top_c}</b> leads the divergence ranking — GDP growth consistently outpaces unemployment.",
        "Countries with a negative divergence index show labour market stress relative to growth performance.",
    ])

    # Quadrant scatter
    med_x = view["GDP Growth (%)"].median()
    med_y = view["Unemployment Rate (%)"].median()
    try:
        fig3 = px.scatter(
            view.dropna(subset=["GDP Growth (%)", "Unemployment Rate (%)"]),
            x="GDP Growth (%)", y="Unemployment Rate (%)",
            color="country", custom_data=["year", "country", "Divergence Index"],
            trendline="ols", height=520, opacity=0.82,
            title="GDP Growth vs Unemployment Rate (OLS per country)", color_discrete_map=COLOR_MAP)
    except Exception:
        fig3 = px.scatter(
            view.dropna(subset=["GDP Growth (%)", "Unemployment Rate (%)"]),
            x="GDP Growth (%)", y="Unemployment Rate (%)",
            color="country", custom_data=["year", "country", "Divergence Index"],
            height=520, opacity=0.82,
            title="GDP Growth vs Unemployment Rate", color_discrete_map=COLOR_MAP)
    fig3.update_traces(hovertemplate=(
        "<b>%{customdata[1]}</b> (%{customdata[0]})<br>"
        "GDP Growth: %{x:.2f}%<br>Unemployment: %{y:.2f}%<br>"
        "Divergence: %{customdata[2]:+.2f}<extra></extra>"
    ))
    fig3.add_hline(y=med_y, line_dash="dash", line_color="rgba(120,120,120,0.35)")
    fig3.add_vline(x=med_x, line_dash="dash", line_color="rgba(120,120,120,0.35)")
    fig3.update_layout(margin=dict(t=40, b=20))

    tk2 = takeaways([
        f"Countries in the 'Strong Economy' quadrant (high GDP, low unemployment). <b>{top_c}</b> clusters here most consistently.",
        "The 2020 COVID-19 shock pulls observations sharply left (negative GDP growth).",
        "Negative OLS slope indicates healthy labour absorption as output grows.",
    ])

    # Divergence over time
    div_t = view.dropna(subset=["Divergence Index"]).sort_values("year")
    fig4 = px.line(div_t, x="year", y="Divergence Index", color="country",
                   markers=True, color_discrete_map=COLOR_MAP)
    fig4.update_traces(hovertemplate="<b>%{fullData.name}</b><br>Year: %{x}<br>Divergence: %{y:+.2f}<extra></extra>")
    fig4.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="neutral")
    add_events(fig4)
    fig4.update_xaxes(range=[yr[0]-0.5, yr[1]+0.5], dtick=2)
    fig4.update_layout(margin=dict(t=40, b=20))

    tk3 = takeaways([
        f"Divergence trend is <b>{trend_txt}</b> over 2011–2020.",
        "The 2020 COVID-19 shock caused a sharp divergence drop as GDP collapsed.",
        f"<b>{c_divs.index[0]}</b> maintains the highest sustained divergence.",
    ], color="#1565c0")

    body = "\n".join([
        "<h1>GDP Growth &amp; Economic Divergence</h1>",
        caption("Persona: Park Jun-ho — Economic Risk Researcher | Which nations show the strongest divergence between GDP growth and unemployment? | Period: 2011–2020"),
        kpi,
        ins,
        divider(),
        row(fig_div(fig1, cols=2), fig_div(fig2, cols=2)),
        tk1,
        section_head("GDP Growth vs Unemployment — Economic Quadrants", size="h2", color="#1565c0"),
        fig_div(fig3),
        tk2,
        section_head("Divergence Index Over Time", size="h2", color="#1565c0"),
        fig_div(fig4),
        tk3,
    ])
    return PAGE_TEMPLATE.format(title="GDP Divergence", body=body)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE 3 — Population Growth & Workforce
# ═════════════════════════════════════════════════════════════════════════════
def build_page3():
    print("  Building Page 3 — Population Growth & Workforce…")
    df = load_development_master()
    df["country"] = df["country"].str.strip()
    countries = sorted(c for c in df["country"].unique() if c != "Japan")
    yr = YEAR_RANGE

    view = df[df["country"].isin(countries) & df["year"].between(*yr)].copy().sort_values(["country", "year"])
    view["Rate Volatility"] = (
        view.groupby("country")["Interest Rate (%)"]
        .transform(lambda s: s.rolling(3, min_periods=2).std())
    )
    view["Unemployment Volatility"] = (
        view.groupby("country")["Unemployment Rate (%)"]
        .transform(lambda s: s.rolling(3, min_periods=2).std())
    )

    avg_pop  = view["Population Growth (%)"].dropna().mean()
    avg_vol  = view["Rate Volatility"].dropna().mean()
    avg_unemp = view["Unemployment Rate (%)"].dropna().mean()
    high_vol_c = view.groupby("country")["Rate Volatility"].mean().dropna().idxmax()

    kpi = kpi_cards_html([
        ("Avg Population Growth", f"{avg_pop:.2f}%",  "#2e7d32", "#f7fbf4"),
        ("Avg IR Volatility",     f"{avg_vol:.2f}pp", "#e65100", "#fff9f0"),
        ("Avg Unemployment",      f"{avg_unemp:.2f}%","#1565c0", "#f2f8fd"),
    ])

    pop_trend = view.groupby("year")["Population Growth (%)"].mean()
    pop_slope = (pop_trend.iloc[-1] - pop_trend.iloc[0]) / max(len(pop_trend)-1, 1)
    pop_dir   = "declining" if pop_slope < -0.05 else "growing" if pop_slope > 0.05 else "stable"
    vol_corr = view[["Rate Volatility", "Population Growth (%)"]].dropna().corr().iloc[0, 1]
    unemp_vol_corr_pop = view[["Unemployment Volatility", "Population Growth (%)"]].dropna().corr().iloc[0, 1]

    ins = insight_box("Academic Macro Insights", [
        f"Population growth is <b>{pop_dir}</b> (slope: {pop_slope:+.3f}% per year).",
        f"<b>{high_vol_c}</b> shows the highest interest rate volatility.",
        f"IR volatility vs population growth: r = <b>{vol_corr:.3f}</b>.",
        f"Unemployment volatility vs population growth: r = <b>{unemp_vol_corr_pop:.3f}</b>.",
    ], color="#4a148c", bg="#faf2fb")

    # Population Growth line
    fig1 = px.line(view.dropna(subset=["Population Growth (%)"]).sort_values("year"),
                   x="year", y="Population Growth (%)", color="country",
                   markers=True, title="Population Growth Over Time", color_discrete_map=COLOR_MAP)
    fig1.add_hline(y=0, line_dash="dash", line_color="gray")
    add_events(fig1)
    fig1.update_xaxes(range=[yr[0]-0.5, yr[1]+0.5], dtick=2)
    fig1.update_layout(margin=dict(t=40, b=20))

    # IR Volatility line
    fig2 = px.line(view.dropna(subset=["Rate Volatility"]).sort_values("year"),
                   x="year", y="Rate Volatility", color="country",
                   markers=True, title="Interest Rate Volatility (3-yr rolling std)", color_discrete_map=COLOR_MAP)
    add_events(fig2)
    fig2.update_xaxes(range=[yr[0]-0.5, yr[1]+0.5], dtick=2)
    fig2.update_layout(margin=dict(t=40, b=30))

    _pop_avg = view.groupby("country")["Population Growth (%)"].mean()
    _vol_avg = view.groupby("country")["Rate Volatility"].mean().dropna()
    tk1 = takeaways([
        f"<b>{_pop_avg.idxmax()}</b> recorded the highest average population growth ({_pop_avg.max():.2f}% p.a.).",
        f"<b>{_pop_avg.idxmin()}</b> shows the slowest growth ({_pop_avg.min():.2f}% p.a.).",
        f"IR volatility peaked around 2015 and 2018 economic shocks.",
    ])

    # Scatter 1: IR Vol vs Population Growth
    try:
        fig3 = px.scatter(view.dropna(subset=["Rate Volatility", "Population Growth (%)"]),
                          x="Rate Volatility", y="Population Growth (%)",
                          color="country", custom_data=["year", "country"],
                          trendline="ols", height=420, opacity=0.82,
                          title="IR Volatility vs Population Growth", color_discrete_map=COLOR_MAP)
    except Exception:
        fig3 = px.scatter(view.dropna(subset=["Rate Volatility", "Population Growth (%)"]),
                          x="Rate Volatility", y="Population Growth (%)",
                          color="country", custom_data=["year", "country"],
                          height=420, opacity=0.82,
                          title="IR Volatility vs Population Growth", color_discrete_map=COLOR_MAP)
    fig3.update_traces(hovertemplate=(
        "<b>%{customdata[1]}</b> (%{customdata[0]})<br>"
        "IR Volatility: %{x:.2f}pp<br>Pop Growth: %{y:.2f}%<extra></extra>"
    ))

    # Scatter 2: Unemployment Vol vs Population Growth
    try:
        fig4 = px.scatter(view.dropna(subset=["Unemployment Volatility", "Population Growth (%)"]),
                          x="Unemployment Volatility", y="Population Growth (%)",
                          color="country", custom_data=["year", "country"],
                          trendline="ols", height=420, opacity=0.82,
                          title="Unemployment Volatility vs Population Growth", color_discrete_map=COLOR_MAP)
    except Exception:
        fig4 = px.scatter(view.dropna(subset=["Unemployment Volatility", "Population Growth (%)"]),
                          x="Unemployment Volatility", y="Population Growth (%)",
                          color="country", custom_data=["year", "country"],
                          height=420, opacity=0.82,
                          title="Unemployment Volatility vs Population Growth", color_discrete_map=COLOR_MAP)
    fig4.update_traces(hovertemplate=(
        "<b>%{customdata[1]}</b> (%{customdata[0]})<br>"
        "Unemp Volatility: %{x:.2f}pp<br>Pop Growth: %{y:.2f}%<extra></extra>"
    ))

    # Scatter 3: IR Vol vs Unemployment
    try:
        fig5 = px.scatter(view.dropna(subset=["Rate Volatility", "Unemployment Rate (%)"]),
                          x="Rate Volatility", y="Unemployment Rate (%)",
                          color="country", custom_data=["year", "country"],
                          trendline="ols", height=420, opacity=0.82,
                          title="IR Volatility vs Unemployment Rate", color_discrete_map=COLOR_MAP)
    except Exception:
        fig5 = px.scatter(view.dropna(subset=["Rate Volatility", "Unemployment Rate (%)"]),
                          x="Rate Volatility", y="Unemployment Rate (%)",
                          color="country", custom_data=["year", "country"],
                          height=420, opacity=0.82,
                          title="IR Volatility vs Unemployment Rate", color_discrete_map=COLOR_MAP)
    fig5.update_traces(hovertemplate=(
        "<b>%{customdata[1]}</b> (%{customdata[0]})<br>"
        "IR Volatility: %{x:.2f}pp<br>Unemployment: %{y:.2f}%<extra></extra>"
    ))

    # Unemployment Volatility over time
    fig6 = px.line(view.dropna(subset=["Unemployment Volatility"]).sort_values(["country", "year"]),
                   x="year", y="Unemployment Volatility", color="country",
                   markers=True, title="Unemployment Volatility Over Time (3-yr rolling std)",
                   color_discrete_map=COLOR_MAP)
    add_events(fig6)
    fig6.update_xaxes(range=[yr[0]-0.5, yr[1]+0.5], dtick=2)
    fig6.update_layout(margin=dict(t=40, b=20))
    fig6.update_traces(hovertemplate="<b>%{fullData.name}</b><br>Year: %{x}<br>Unemp Volatility: %{y:.2f}pp<extra></extra>")

    _ir_pop_corr = view[["Rate Volatility", "Population Growth (%)"]].dropna().corr().iloc[0, 1]
    _uv_pop_corr = view[["Unemployment Volatility", "Population Growth (%)"]].dropna().corr().iloc[0, 1]
    tk2 = takeaways([
        f"IR Volatility vs Population Growth: <b>r = {_ir_pop_corr:.3f}</b>.",
        f"Unemployment Volatility vs Population Growth: <b>r = {_uv_pop_corr:.3f}</b>.",
        "OLS trendlines reveal per-country heterogeneity in how volatility affects demographics.",
    ], color="#4a148c")

    # Unemployment Rate Over Time
    fig7 = px.line(view.dropna(subset=["Unemployment Rate (%)"]).sort_values(["country", "year"]),
                   x="year", y="Unemployment Rate (%)", color="country",
                   markers=True, title="Unemployment Rate Over Time", color_discrete_map=COLOR_MAP)
    add_events(fig7)
    fig7.update_xaxes(range=[yr[0]-0.5, yr[1]+0.5], dtick=2)
    fig7.update_yaxes(showgrid=False)
    fig7.update_layout(margin=dict(t=40, b=20))
    fig7.update_traces(hovertemplate="<b>%{fullData.name}</b><br>Year: %{x}<br>Unemployment: %{y:.2f}%<extra></extra>")

    _u3_avg = view.groupby("country")["Unemployment Rate (%)"].mean()
    tk3 = takeaways([
        f"<b>{_u3_avg.idxmin()}</b> maintained the tightest labour market ({_u3_avg.min():.1f}% avg unemployment).",
        f"<b>{_u3_avg.idxmax()}</b> recorded the highest average unemployment ({_u3_avg.max():.1f}%).",
        "The COVID-19 shock (2020) is visible as a sharp divergence point across economies.",
    ], color="#1565c0")

    body = "\n".join([
        "<h1>Interest Volatility, Population &amp; Workforce</h1>",
        caption("Persona: Dr. Maria Stern — Professor of Macroeconomics | How has interest rate volatility affected population growth and workforce employment? | Period: 2011–2020"),
        kpi,
        ins,
        divider(),
        row(fig_div(fig1, cols=2), fig_div(fig2, cols=2)),
        tk1,
        section_head("Volatility vs Population Growth &amp; Workforce", size="h2", color="#4a148c"),
        caption("Left: IR Volatility · Right: Unemployment Volatility (3-yr rolling std of unemployment rate)"),
        row(fig_div(fig3, cols=2), fig_div(fig4, cols=2)),
        row(fig_div(fig5, cols=2), fig_div(fig6, cols=2)),
        tk2,
        section_head("Unemployment Rate Over Time (Workforce Proxy)", size="h2", color="#1565c0"),
        fig_div(fig7),
        tk3,
    ])
    return PAGE_TEMPLATE.format(title="Population Growth & Workforce", body=body)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE 4 — Market Monitor
# ═════════════════════════════════════════════════════════════════════════════
def build_page4():
    print("  Building Page 4 — Market Monitor…")
    market = load_market_master()
    macro  = load_macro_master()

    if market.empty:
        body = "<h1>Market Monitor</h1><p>No market data available.</p>"
        return PAGE_TEMPLATE.format(title="Market Monitor", body=body)

    market["country"] = market["country"].str.strip()
    if not macro.empty and "country" in macro.columns:
        macro["country"] = macro["country"].str.strip()

    countries = sorted(c for c in market["country"].unique() if c != "Japan")
    market = market[market["country"].isin(countries)].copy()
    market["Index_Close"] = pd.to_numeric(market["Index_Close"], errors="coerce")
    market["FX_EUR_Rate"]  = pd.to_numeric(market["FX_EUR_Rate"],  errors="coerce")

    # Latest snapshot KPIs
    latest_date = market["date"].max()
    latest = market[market["date"] == latest_date]
    kpi_list = []
    for _, row_ in latest.iterrows():
        idx_val = row_["Index_Close"]
        prev = market[(market["country"] == row_["country"]) & (market["date"] < latest_date)]
        if not prev.empty:
            prev_idx = prev.sort_values("date").iloc[-1]["Index_Close"]
            delta = ((idx_val - prev_idx) / prev_idx * 100) if prev_idx else None
        else:
            delta = None
        color = "#2e7d32" if (delta or 0) >= 0 else "#c62828"
        bg    = "#f7fbf4" if (delta or 0) >= 0 else "#fdf1f5"
        d_str = f" ({delta:+.2f}%)" if delta is not None else ""
        kpi_list.append((row_["country"], f"{idx_val:,.0f}{d_str}" if pd.notna(idx_val) else "N/A", color, bg))
    kpi = kpi_cards_html(kpi_list)

    # Stock index chart
    fig1 = px.line(market.sort_values("date"), x="date", y="Index_Close",
                   color="country", title="Stock Index Close", color_discrete_map=COLOR_MAP)
    fig1.update_traces(hovertemplate="<b>%{fullData.name}</b><br>%{x|%d %b %Y}<br>Index: %{y:,.0f}<extra></extra>")
    fig1.update_layout(margin=dict(t=40, b=20))

    # FX chart
    fig2 = px.line(market.sort_values("date"), x="date", y="FX_EUR_Rate",
                   color="country", title="FX Rate vs EUR", color_discrete_map=COLOR_MAP)
    fig2.update_traces(hovertemplate="<b>%{fullData.name}</b><br>%{x|%d %b %Y}<br>FX: %{y:.4f}<extra></extra>")
    fig2.update_layout(margin=dict(t=40, b=20))

    macro_section = ""
    if not macro.empty:
        macro_cols = [c for c in ["Brent_Oil", "US10Y_Yield", "VIX"] if c in macro.columns and macro[c].notna().any()]
        if macro_cols:
            fig3 = go.Figure()
            for col in macro_cols:
                fig3.add_trace(go.Scatter(
                    x=macro["date"], y=macro[col], name=col, mode="lines",
                    hovertemplate=f"{col}: %{{y:.2f}}<br>%{{x|%d %b %Y}}<extra></extra>"
                ))
            fig3.update_layout(title="Global Macro Indicators Over Time",
                                height=400, margin=dict(t=40, b=20))
            macro_section = "\n".join([
                section_head("Global Macro Indicators", size="h2", color="#e65100"),
                fig_div(fig3),
            ])

    body = "\n".join([
        "<h1>🌍 Market Monitor</h1>",
        caption(f"Daily equity indices, FX rates vs EUR, Brent Oil, US 10Y Yield, and VIX. Latest: {latest_date.strftime('%d %b %Y')}"),
        f"<h3 style='color:#555'>Latest Snapshot — {latest_date.strftime('%d %b %Y')}</h3>",
        kpi,
        divider(),
        row(fig_div(fig1, cols=2), fig_div(fig2, cols=2)),
        macro_section,
    ])
    return PAGE_TEMPLATE.format(title="Market Monitor", body=body)


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════
def main():
    global _plotly_cdn_included
    pages = [
        ("page1_interest_rate_employment.html", build_page1),
        ("page2_gdp_divergence.html",           build_page2),
        ("page3_population_growth.html",         build_page3),
        ("page4_market_monitor.html",            build_page4),
    ]

    for filename, builder in pages:
        _plotly_cdn_included = False   # reset CDN flag for each page
        try:
            html = builder()
            path = os.path.join(OUT_DIR, filename)
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"  ✓ Saved: export/{filename}")
        except Exception as exc:
            print(f"  ✗ Failed {filename}: {exc}")

    # Index page
    idx_path = os.path.join(OUT_DIR, "index.html")
    with open(idx_path, "w", encoding="utf-8") as f:
        f.write(INDEX_TEMPLATE)
    print(f"  ✓ Saved: export/index.html")
    print(f"\nDone! Open:  {OUT_DIR}\\index.html")


if __name__ == "__main__":
    main()
