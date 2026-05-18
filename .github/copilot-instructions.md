# GitHub Copilot Instructions — Economic Difference Dashboard

## Project Overview

This is a **Streamlit multi-page analytics dashboard** for an HSLU MSc Applied Information & Data Science project.
It analyses macroeconomic data (2011–2020) across four Asian economies: **China, Hong Kong SAR China, India, and Singapore**.
Data is loaded live from **AWS S3** (bucket: `economic-warehouse-curated`).

---

## Workspace Structure

```
Economic Difference/
├── Overview.py                  # Main entry point / landing page
├── export_html.py               # Static HTML export script
├── requirements.txt
├── .env                         # Local secrets — NEVER commit
├── .gitignore
├── assets/
│   └── styles.css               # Global CSS overrides
├── charts/
│   ├── __init__.py
│   └── base.py                  # Reusable Plotly chart helpers
├── components/
│   ├── __init__.py
│   ├── kpi_card.py              # KPI card HTML renderer
│   ├── sidebar.py               # Sidebar navigation
│   ├── topbar.py                # Top navigation bar
│   └── ui_helpers.py            # Shared UI utilities (key_takeaways, insight_panel, etc.)
├── config/
│   ├── __init__.py
│   ├── constants.py             # Country lists, color maps, event markers
│   └── settings.py              # App-level settings loaded from .env
├── data/
│   ├── raw/                     # Raw data (not committed)
│   ├── processed/               # Processed data (not committed)
│   └── samples/                 # Sample/mock data for local dev
├── pages/
│   ├── 1_Interest_Rate_Employment.py   # RQ1 — Ana Silva persona
│   ├── 2_GDP_Divergence.py             # RQ2 — Park Jun-ho persona
│   ├── 3_Population_Growth.py          # RQ3 — Dr. Maria Stern persona
│   └── 4_Market_Monitor.py             # Market & macro daily monitor
├── services/
│   ├── __init__.py
│   ├── auth_service.py          # Login / session authentication
│   ├── data_service.py          # S3 data loading functions
│   └── s3_service.py            # Raw boto3 S3 client wrapper
├── utils/
│   ├── __init__.py
│   ├── formatters.py            # Number/date formatting helpers
│   ├── logger.py                # Logging setup
│   └── session.py               # Streamlit session state helpers
└── export/                      # Static HTML exports of each page
```

---

## AI Assistant Rules

### General Behaviour
- Make **only the changes explicitly requested**. Do not refactor, rename, or restructure code that was not mentioned.
- Do not add comments, docstrings, or type hints to code you did not change.
- Do not create new files unless the user specifically asks for one.
- Prefer editing existing files over creating new ones.
- Keep answers short and direct. Expand only when the task is complex.

### Code Style
- Follow existing patterns in the codebase — do not introduce new abstractions or patterns.
- Use **Plotly Express / Graph Objects** for all charts (already used throughout).
- Use **`st.plotly_chart(fig, use_container_width=True)`** for all chart renders.
- Always call **`key_takeaways([...])`** after every chart — imported from `components.ui_helpers`.
- Use **`insight_panel(...)`** for summary insight blocks at the top of pages.
- Use **`render_kpi_card` + `kpi_row`** for KPI metric displays.
- Country color map must always be:
  ```python
  color_map = {
      "Singapore": "#00aa55",
      "China": "#1f77b4",
      "Hong Kong SAR China": "#ff7f0e",
      "India": "#d62728",
  }
  ```
- Always strip whitespace from country names: `df["country"] = df["country"].str.strip()`

### Data & Services
- All data is loaded via `services/data_service.py` — do not read S3 directly in page files.
- Main datasets: `load_development_master()`, `load_macro_master()`, `load_market_master()`.
- Filter out Japan from country lists: `sorted(c for c in df["country"].unique() if c != "Japan")`.
- Year range for research pages: **2011–2020**. Do not change this unless asked.

### Security
- **Never commit `.env`** — it contains AWS credentials and app password.
- **Never hardcode credentials** in any file.
- Do not push `__pycache__/`, `.pyc` files, or any compiled Python artifacts.
- AWS session tokens expire frequently — remind the user to refresh them when the app shows credential errors.
- Secrets for deployment go into **Streamlit Community Cloud → App Settings → Secrets** (TOML format), not into the repo.

### Git & Deployment
- GitLab repo: `https://gitlab.com/economic-difference/hslu-project-economic-difference`
- Default branch: `main`
- To push: commit changes, then push with the GitLab personal access token.
- For Streamlit Community Cloud deployment: push to **GitHub** (GitLab is not supported directly).
- Entry point for Streamlit: **`Overview.py`**

### Conclusion Sections
- Every research page must end with a styled conclusion box answering its research question.
- Conclusion boxes use `st.markdown(..., unsafe_allow_html=True)` with a coloured background div.
- No emojis in conclusion headings. No left border/side bar on the box.
- Style template:
  ```python
  st.markdown("""
  <div style='background:#e8eaf6; padding:20px 24px; border-radius:8px; margin-top:16px;'>
    <h3 style='color:#1a237e; margin-top:0;'>Conclusion — RQ X: ...</h3>
    <p>...</p>
  </div>
  """, unsafe_allow_html=True)
  ```

### Research Questions
| Page | Persona | Research Question |
|------|---------|-------------------|
| 1 — Interest Rate & Employment | Ana Silva (ECB Policy Analyst) | How do interest rate changes correlate with unemployment trends across Asian economies? |
| 2 — GDP Divergence | Park Jun-ho (Economic Risk Researcher) | Which nations show the strongest divergence between GDP growth and unemployment rates? |
| 3 — Population Growth | Dr. Maria Stern (Professor of Macroeconomics) | How has interest rate volatility affected population growth and workforce employment? |
| 4 — Market Monitor | — | Daily equity indices, FX vs EUR, Brent Oil, US 10Y Yield, VIX |
