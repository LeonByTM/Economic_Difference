import streamlit as st

from config.settings import settings
from components.topbar import render_topbar


st.set_page_config(page_title=settings.app_title, layout="wide")

render_topbar()

st.title("Economic Difference Dashboard")
st.caption("A Comparative Data Lake & Warehouse Analysis of Macroeconomic Performance in Asia — HSLU MSc Applied Information & Data Science")

st.markdown("---")

# ── Project context ───────────────────────────────────────────────────────────
col_a, col_b = st.columns([3, 2])
with col_a:
    st.markdown("""
### About this Project
This dashboard was built as part of the **HSLU MSc Applied Information & Data Science** programme.
It analyses macroeconomic data from four major Asian economies — **China, Hong Kong SAR China, India, and Singapore** —
covering the period **2011 to 2020** (post-Global Financial Crisis recovery through the COVID-19 onset).

All data is stored in **AWS S3** as a curated Data Lake and accessed live. Charts are interactive — hover for details,
click legend entries to filter countries.
""")

with col_b:
    st.markdown("""
### Research Period
| | |
|---|---|
| **Start** | 2011 (post-GFC stabilisation) |
| **End** | 2020 (COVID-19 onset) |
| **Economies** | China, Hong Kong, India, Singapore |
| **Data source** | AWS S3 · `economic-warehouse-curated` |
""")

st.markdown("---")

# ── Research questions ────────────────────────────────────────────────────────
st.markdown("### Research Questions")

rq_cols = st.columns(3)
with rq_cols[0]:
    st.markdown("""
<div style="background:#e8eaf6;border-radius:8px;padding:16px 18px;height:100%;">
<b style="color:#1a237e;font-size:1rem;">RQ 1 — Interest Rate & Employment</b><br><br>
<span style="font-size:0.88rem;color:#1a1a2e;">How do interest rate changes correlate with unemployment trends across Asian economies?</span><br><br>
<span style="font-size:0.8rem;color:#555;">Persona: <b>Ana Silva</b> — Central Bank Policy Analyst</span>
</div>""", unsafe_allow_html=True)

with rq_cols[1]:
    st.markdown("""
<div style="background:#e8f5e9;border-radius:8px;padding:16px 18px;height:100%;">
<b style="color:#1b5e20;font-size:1rem;">RQ 2 — GDP Divergence</b><br><br>
<span style="font-size:0.88rem;color:#1a1a2e;">Which nations show the strongest divergence between GDP growth and unemployment rates?</span><br><br>
<span style="font-size:0.8rem;color:#555;">Persona: <b>Park Jun-ho</b> — Economic Risk Researcher</span>
</div>""", unsafe_allow_html=True)

with rq_cols[2]:
    st.markdown("""
<div style="background:#fce4ec;border-radius:8px;padding:16px 18px;height:100%;">
<b style="color:#880e4f;font-size:1rem;">RQ 3 — Population & Workforce</b><br><br>
<span style="font-size:0.88rem;color:#1a1a2e;">How does interest rate volatility affect population growth and workforce employment?</span><br><br>
<span style="font-size:0.8rem;color:#555;">Persona: <b>Dr. Maria Stern</b> — Professor of Macroeconomics</span>
</div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

# ── Data inventory ────────────────────────────────────────────────────────────
st.markdown("### Data Inventory")
st.markdown("""
| Dataset | Metrics | Coverage | Granularity |
|---|---|---|---|
| `development_master` | GDP Growth, Interest Rate, Unemployment, Population Growth | 2011–2024 (IR: 2011–2020 for all 4) | Annual |
| `market_master` | Equity index closes, FX vs EUR | Daily | Daily |
| `macro_master` | Brent Oil, US 10Y Yield, VIX | Daily | Daily |
""")

st.markdown("---")
st.caption("Navigate using the sidebar. All charts are interactive — hover for values, click legend to filter.")

