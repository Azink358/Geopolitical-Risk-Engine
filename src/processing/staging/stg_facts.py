import os
import pandas as pd

PROCESSED_DIR = "data/processed"

def build_fact_energy_volatility():
    df = pd.DataFrame({
        "date_key": [202601, 202602],
        "country_key": [1, 2],
        "conflict_phase_key": [101, 102],
        "price_premium_pct": [5.2, 6.1],
        "disruption_risk_score": [0.7, 0.9],
    })
    path = os.path.join(PROCESSED_DIR, "fact_energy_volatility.csv")
    df.to_csv(path, index=False)
    return df

def build_fact_apac_dependency():
    df = pd.DataFrame({
        "date_key": [202601, 202602],
        "country_key": [1, 2],
        "fuel_type_key": [201, 202],
        "import_volume": [1000, 1200],
        "me_share_pct": [0.35, 0.40],
        "alt_source_pct": [0.20, 0.25],
        "spr_days_cover": [30, 28],
    })
    path = os.path.join(PROCESSED_DIR, "fact_apac_dependency.csv")
    df.to_csv(path, index=False)
    return df

def build_fact_supply_chain_impact():
    df = pd.DataFrame({
        "date_key": [202601, 202602],
        "country_key": [1, 2],
        "sector_key": [301, 302],
        "impact_score": [0.8, 0.6],
        "exposure_pct": [0.45, 0.55],
    })
    path = os.path.join(PROCESSED_DIR, "fact_supply_chain_impact.csv")
    df.to_csv(path, index=False)
    return df

def build_fact_shipping_disruptions():
    df = pd.DataFrame({
        "date_key": [202601, 202602],
        "event_key": [401, 402],
        "incident_type": ["blockade", "delay"],
        "severity_level": ["high", "medium"],
        "route_key": [501, 502],
        "delay_hours": [72, 24],
        "cargo_volume": [20000, 15000],
    })
    path = os.path.join(PROCESSED_DIR, "fact_shipping_disruptions.csv")
    df.to_csv(path, index=False)
    return df

def build_fact_strategic_responses():
    df = pd.DataFrame({
        "date_key": [202601, 202602],
        "response_key": [601, 602],
        "response_category": ["policy", "market"],
        "institution": ["Govt", "Private"],
        "effectiveness_score": [0.75, 0.65],
    })
    path = os.path.join(PROCESSED_DIR, "fact_strategic_responses.csv")
    df.to_csv(path, index=False)
    return df
