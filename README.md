# 📊 Macro‑Sentry Geopolitical Risk Engine

## 🚀 Overview
Macro‑Sentry is a full-stack analytics project that models how energy shocks ripple through Asia‑Pacific supply chains.  
It integrates **dimensional modeling, ETL pipelines, machine learning, and interactive dashboards** to narrate a clear story:  
**Energy → Supply Chain → GDP → Resilience.**

---

## 🛠️ Features
- **Dimensional Warehouse**
  - Fact tables: imports, prices, supply chain, shipping, disruptions, responses
  - Dimension tables: country, fuel type, conflict phase, vessel type, route, sector, severity
  - Schema defined in `schema.yaml` with surrogate keys for clean joins

- **ETL Pipeline**
  - Modular builders (`dimension_builder.py`, `fact_builder.py`, `feature_builder.py`)
  - Validation layer (`validator.py`) ensures schema consistency
  - Database manager (`db_manager.py`) for explicit ownership and reproducibility

- **Analytics & Machine Learning**
  - Feature engineering for disruption and response modeling
  - Risk predictor with CV results, feature importance, and model summary
  - Serialized model (`risk_model.json`) for deployment readiness

- **Visualization**
  - Interactive Plotly dashboards showing Brent crude volatility, GDP impact, and import dependency by fuel type
  - Conflict phases shaded across timelines for geopolitical context
  - Clean, uncluttered visuals suitable for analysis and presentation

