# Economic Difference

A scalable Streamlit project scaffold for analytics dashboards that load data from AWS S3.

## Tech Stack

- Python
- Streamlit
- AWS S3 via boto3
- Pandas for data loading and preprocessing
- Plotly for reusable chart rendering

## Recommended Folder Structure

```text
Economic Difference/
|-- app.py
|-- README.md
|-- requirements.txt
|-- .env.example
|-- assets/
|   |-- styles.css
|-- charts/
|   |-- __init__.py
|   |-- base.py
|-- components/
|   |-- __init__.py
|   |-- kpi_card.py
|   |-- sidebar.py
|-- config/
|   |-- __init__.py
|   |-- constants.py
|   |-- settings.py
|-- data/
|   |-- raw/
|   |   |-- .gitkeep
|   |-- processed/
|   |   |-- .gitkeep
|   |-- samples/
|       |-- .gitkeep
|-- pages/
|   |-- 1_Overview.py
|   |-- 2_Data_Explorer.py
|-- services/
|   |-- __init__.py
|   |-- auth_service.py
|   |-- data_service.py
|   |-- s3_service.py
|-- utils/
|   |-- __init__.py
|   |-- formatters.py
|   |-- logger.py
|   |-- session.py
```

## Purpose Of Each Folder

- `assets/`: Static files such as CSS, icons, images, and branding assets.
- `charts/`: Reusable chart builders and shared visualization patterns.
- `components/`: Reusable Streamlit UI blocks such as sidebars, cards, filters, and section headers.
- `config/`: Centralized application configuration, constants, and environment loading.
- `data/`: Optional local storage for raw extracts, processed outputs, and sample files used during development.
- `pages/`: Streamlit multi-page dashboard screens. Each file becomes a separate page.
- `services/`: External integration and business workflow layer, including S3 access, authentication, and dataset orchestration.
- `utils/`: Small reusable helper functions that do not belong to a specific domain service or component.

## Purpose Of Each File

- `app.py`: Main Streamlit entrypoint, page config, login screen, and project landing page.
- `README.md`: Project setup guide and structure reference.
- `requirements.txt`: Python dependencies for the dashboard application.
- `.env.example`: Template for environment variables and secrets.
- `assets/styles.css`: Shared styling overrides for the Streamlit app.
- `charts/__init__.py`: Convenience exports for chart utilities.
- `charts/base.py`: Generic reusable chart renderers for line and bar charts.
- `components/__init__.py`: Convenience exports for UI components.
- `components/kpi_card.py`: Reusable KPI metric card wrapper.
- `components/sidebar.py`: Shared sidebar rendering and logout action.
- `config/__init__.py`: Central config export.
- `config/constants.py`: Path constants for assets and local data directories.
- `config/settings.py`: Environment-driven settings loaded from `.env`.
- `data/raw/.gitkeep`: Keeps the raw data directory in version control.
- `data/processed/.gitkeep`: Keeps the processed data directory in version control.
- `data/samples/.gitkeep`: Keeps the sample data directory in version control.
- `pages/1_Overview.py`: Example dashboard page with reusable KPI and chart components.
- `pages/2_Data_Explorer.py`: Example page for loading a dataset from S3 and inspecting it.
- `services/__init__.py`: Convenience exports for service functions.
- `services/auth_service.py`: Session-based authentication helpers.
- `services/data_service.py`: Dataset loading orchestration and preprocessing entrypoint.
- `services/s3_service.py`: AWS S3 read access and object key handling.
- `utils/__init__.py`: Convenience exports for utility helpers.
- `utils/formatters.py`: Shared formatting utilities such as compact number formatting.
- `utils/logger.py`: Standard logging configuration helper.
- `utils/session.py`: Small wrappers around Streamlit session state.

## Why This Structure Scales

- Clear separation of concerns keeps UI, data access, configuration, and helper logic independent.
- Streamlit pages remain thin because reusable components, charts, and services live outside page files.
- AWS-specific logic is isolated in `services/`, which makes future migration to APIs, databases, or data lakes easier.
- Configuration is centralized, which supports local, staging, and production environments.
- The structure supports future additions such as tests, CI, feature-specific service modules, or stronger authentication providers.

## Getting Started

1. Create a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and update the values.
4. Run the app:
   ```bash
   streamlit run app.py
   ```

## Recommended Future Additions

- Add `tests/` for unit and integration coverage.
- Replace the simple login scaffold with AWS Cognito, SSO, or another identity provider.
- Add schema validation for incoming S3 datasets.
- Introduce feature-based modules if the dashboard grows into multiple domains.
