import streamlit as st
import pandas as pd
from pathlib import Path

FEATURES_DIR = Path("data/features")

st.set_page_config(page_title="Macro-Sentry Risk Dashboard", layout="wide")

st.title("🌍 Macro-Sentry Geopolitical Risk Dashboard")

def load_data(filename):
    return pd.read_csv(FEATURES_DIR / filename)

# Create tabs for each fact table
tabs = st.tabs([
    "Energy Volatility",
    "Maritime Costs",
    "Shipping Disruptions",
    "Strategic Responses",
    "Supply Chain Impact",
    "APAC Dependency"
])

with tabs[0]:
    df = load_data("feat_energy_volatility.csv")
    st.subheader("Energy Volatility Trends")
    st.line_chart(df.groupby("date_key")[["price_value", "price_value_7d_avg"]].mean())

with tabs[1]:
    df = load_data("feat_maritime_costs.csv")
    st.subheader("Maritime Cost Ratios")
    st.bar_chart(df[["freight_rate_usd", "war_risk_vs_freight", "hull_insurance_vs_freight"]])

with tabs[2]:
    df = load_data("feat_shipping_disruptions.csv")
    st.subheader("Shipping Disruption Severity vs Delay")
    st.scatter_chart(df[["severity_norm", "delay_per_volume"]])

with tabs[3]:
    df = load_data("feat_strategic_responses.csv")
    st.subheader("Strategic Response Effectiveness")
    st.bar_chart(df[["effectiveness_norm", "cost_efficiency", "dependency_reduction_efficiency"]])

with tabs[4]:
    df = load_data("feat_supply_chain_impact.csv")
    st.subheader("Supply Chain Stress Indicators")
    st.line_chart(df.groupby("date_key")[["disruption_index_norm", "gdpimpact_per_delay"]].mean())

with tabs[5]:
    df = load_data("feat_apac_dependency.csv")
    st.subheader("APAC Dependency Risk")
    st.bar_chart(df[["risk_adjusted_import", "premium_vs_spr", "alt_source_efficiency"]])
