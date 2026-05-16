import os
import psycopg2
import pandas as pd
import streamlit as st
import altair as alt
from dotenv import load_dotenv
from vega_datasets import data
from sqlalchemy import create_engine

# --- Load environment variables ---
load_dotenv()
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# --- Create SQLAlchemy engine once ---
engine = create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# --- Database helper ---
def get_data(query: str) -> pd.DataFrame:
    """Run SQL query and return DataFrame."""
    return pd.read_sql(query, engine)

# --- Streamlit page setup ---
st.set_page_config(page_title="Macro-Sentry Dashboard", layout="wide")
st.title("Macro-Sentry Geopolitical Risk Engine")
st.markdown("### Maritime Disruption Storytelling")

# --- Tabs ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Disruption", "Shipping Economics", "Country Risk", "Sector Impact", "Policy Response", "Cross-Validation"
])


# --- Tab 1: Disruption ---
with tab1:
    st.subheader("Disruption Events")

    # Filters (same as before)
    phase_filter = st.selectbox("Select Conflict Phase", ["All"] + list(get_data("SELECT conflict_phase FROM dim_conflict_phase ORDER BY conflict_phase")['conflict_phase']))
    vessel_filter = st.selectbox("Select Vessel Type", ["All"] + list(get_data("SELECT vessel_type FROM dim_vessel_type ORDER BY vessel_type")['vessel_type']))
    flag_filter = st.selectbox("Select Flag State", ["All"] + list(get_data("SELECT flag_state FROM dim_flag_state ORDER BY flag_state")['flag_state']))

    where_clauses = []
    if phase_filter != "All":
        where_clauses.append(f"cp.conflict_phase = '{phase_filter}'")
    if vessel_filter != "All":
        where_clauses.append(f"vt.vessel_type = '{vessel_filter}'")
    if flag_filter != "All":
        where_clauses.append(f"fs.flag_state = '{flag_filter}'")
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    query_disruption = f"""
    SELECT 
        dis.event_id,
        cp.conflict_phase,
        vt.vessel_type,
        fs.flag_state,
        dis.estimated_delay_hours,
        dis.cargo_volume_impacted_kt,
        dis.reroute_required,
        dis.lat,
        dis.lon
    FROM fact_disruption dis
    JOIN dim_vessel_type vt ON dis.vessel_type_key = vt.vessel_type_key
    JOIN dim_flag_state fs ON dis.flag_state_key = fs.flag_state_key
    JOIN dim_conflict_phase cp ON dis.conflict_phase_key = cp.conflict_phase_key
    {where_sql}
    ORDER BY cp.conflict_phase, dis.event_id;
    """
    df_disruption = get_data(query_disruption)

    # KPIs
    st.markdown("### Key Metrics (Filtered Selection)")
    col1, col2, col3 = st.columns(3)
    col1.metric("Events", len(df_disruption))
    col2.metric("Avg Delay (hrs)", round(df_disruption['estimated_delay_hours'].mean(), 1))
    col3.metric("Total Cargo Impact (kt)", int(df_disruption['cargo_volume_impacted_kt'].sum()))

    # Event table
    st.dataframe(df_disruption, width='stretch')

    # Scatter plot
    scatter = alt.Chart(df_disruption).mark_circle(size=60).encode(
        x='estimated_delay_hours:Q',
        y='cargo_volume_impacted_kt:Q',
        color='conflict_phase:N',
        tooltip=['event_id','conflict_phase','vessel_type','flag_state','estimated_delay_hours','cargo_volume_impacted_kt','reroute_required']
    ).properties(title="Event-wise Impact: Delay vs Cargo").interactive()
    st.altair_chart(scatter, width='stretch')

    # 🌍 World map view
    st.markdown("### Geographic Distribution of Disruptions")
    st.map(df_disruption[['lat','lon']])

    # Download option
    csv = df_disruption.to_csv(index=False).encode('utf-8')
    st.download_button("Download Filtered Events as CSV", csv, "disruptions.csv", "text/csv")

    # Recruiter-facing narrative
    st.markdown(f"""
    ### Recruiter-Facing Narrative
    The filtered selection shows **{len(df_disruption)} disruption events**.  
    Average delays of **{round(df_disruption['estimated_delay_hours'].mean(),1)} hours** translate into
    significant cargo bottlenecks (**{int(df_disruption['cargo_volume_impacted_kt'].sum())} kilotons impacted**).  

    The world map visualization highlights how disruptions are geographically distributed,
    turning raw lat/lon data into a clear global risk picture — a skill recruiters value in analytics portfolios.
    """)






# --- Tab 2: Shipping Economics ---


with tab2:
    st.subheader("Shipping Economics")

    # Filters
    phase_filter = st.selectbox(
        "Select Conflict Phase",
        ["All"] + list(get_data("SELECT conflict_phase FROM dim_conflict_phase ORDER BY conflict_phase")['conflict_phase']),
        key="shipping_phase_filter"
    )

    # Restrict vessel filter to only the 4 valid types
    valid_vessels = ["VLCC", "Suezmax", "Aframax", "LNG Carrier"]
    vessel_filter = st.selectbox(
        "Select Vessel Type",
        ["All"] + valid_vessels,
        key="shipping_vessel_filter"
    )

    route_filter = st.selectbox(
        "Select Route",
        ["All"] + list(get_data("SELECT route FROM dim_route ORDER BY route")['route']),
        key="shipping_route_filter"
    )

    # Toggle for overlay
    show_all_routes = st.checkbox("Overlay all trade lanes", value=False)

    # Build WHERE clause dynamically
    where_clauses = []
    if phase_filter != "All":
        where_clauses.append(f"cp.conflict_phase = '{phase_filter}'")
    if vessel_filter != "All":
        where_clauses.append(f"vt.vessel_type = '{vessel_filter}'")
    if route_filter != "All" and not show_all_routes:
        where_clauses.append(f"r.route = '{route_filter}'")
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    # Query shipping economics + route coordinates
    query_shipping = f"""
    SELECT 
        r.route,
        cp.conflict_phase,
        vt.vessel_type,
        sh.freight_rate_usd_day,
        sh.war_risk_premium_pct,
        sh.hull_insurance_pct_value,
        sh.bunker_cost_usd_mt,
        sh.transit_time_days,
        sh.rerouting_extra_days,
        r.origin_lat, r.origin_lon,
        r.dest_lat, r.dest_lon
    FROM fact_shipping sh
    JOIN dim_conflict_phase cp ON sh.conflict_phase_key = cp.conflict_phase_key
    JOIN dim_route r ON sh.route_key = r.route_key
    JOIN dim_vessel_type vt ON sh.vessel_type_key = vt.vessel_type_key
    {where_sql}
    ORDER BY cp.conflict_phase, r.route;
    """
    df_shipping = get_data(query_shipping)

    # Restrict to only the 4 valid vessel types
    df_shipping = df_shipping[df_shipping["vessel_type"].isin(valid_vessels)]

    # KPIs
    st.markdown("### Key Metrics (Filtered Selection)")
    col1, col2, col3 = st.columns(3)
    col1.metric("Avg Freight Rate (USD/day)", round(df_shipping['freight_rate_usd_day'].mean(), 1))
    col2.metric("Avg War Risk Premium (%)", round(df_shipping['war_risk_premium_pct'].mean(), 1))
    col3.metric("Avg Bunker Cost (USD/mt)", round(df_shipping['bunker_cost_usd_mt'].mean(), 1))

    # Trend chart
    trend = alt.Chart(df_shipping).mark_line(point=True).encode(
        x='conflict_phase:N',
        y='freight_rate_usd_day:Q',
        color='route:N',
        tooltip=['route','vessel_type','freight_rate_usd_day','war_risk_premium_pct','bunker_cost_usd_mt']
    ).properties(title="Freight Rate by Conflict Phase")
    st.altair_chart(trend, width="stretch")

    # Table view
    st.dataframe(df_shipping, width="stretch")

    # 🌍 World map trade lanes
    st.markdown("### Global Shipping Lanes")

    routes_long = pd.DataFrame({
        'route': df_shipping['route'].repeat(2),
        'conflict_phase': df_shipping['conflict_phase'].repeat(2),
        'lon': df_shipping[['origin_lon','dest_lon']].values.flatten(),
        'lat': df_shipping[['origin_lat','dest_lat']].values.flatten()
    })

    # Background world map
    world_map = alt.topo_feature(data.world_110m.url, 'countries')
    background = alt.Chart(world_map).mark_geoshape(
        fill='lightgray',
        stroke='white'
    ).properties(width=900, height=450).project('mercator')

    # Route lines
    route_lines = alt.Chart(routes_long).mark_line().encode(
        longitude='lon:Q',
        latitude='lat:Q',
        detail='route:N',
        color='conflict_phase:N',
        tooltip=['route','conflict_phase']
    )

    # Port points
    ports = alt.Chart(routes_long).mark_circle(size=80).encode(
        longitude='lon:Q',
        latitude='lat:Q',
        color='conflict_phase:N',
        tooltip=['route','conflict_phase']
    )

    trade_lanes = (background + route_lines + ports).properties(
        title="All Trade Lanes by Conflict Phase" if show_all_routes else "Filtered Trade Lanes"
    )
    st.altair_chart(trade_lanes, width="stretch")

    # Download option
    csv = df_shipping.to_csv(index=False).encode('utf-8')
    st.download_button("Download Filtered Shipping Data as CSV", csv, "shipping_economics.csv", "text/csv")

    # ➕ NEW SECTION: Flag State Disruption Impact
    st.markdown("### Disruption Impact by Flag State")

    query_disruptions = """
    SELECT fs.flag_state, 
           SUM(d.estimated_delay_hours) AS total_delay_hours, 
           SUM(d.cargo_volume_impacted_kt) AS total_cargo_impacted
    FROM fact_disruption d
    JOIN dim_flag_state fs ON d.flag_state_key = fs.flag_state_key
    GROUP BY fs.flag_state
    ORDER BY total_delay_hours DESC;
    """
    df_disruptions = get_data(query_disruptions)

    st.bar_chart(df_disruptions.set_index("flag_state")["total_delay_hours"])

    st.markdown(f"""
    Flag states most affected include **{df_disruptions.iloc[0]['flag_state']}** 
    with total disruption delays of **{round(df_disruptions.iloc[0]['total_delay_hours'],1)} hours** 
    and cargo volume impacted of **{round(df_disruptions.iloc[0]['total_cargo_impacted'],1)} kt**.  
    This highlights how shipping economies tied to certain flag states bear disproportionate risk.
    """)

    # Recruiter-facing narrative
    st.markdown(f"""
    ### Recruiter-Facing Narrative
    Tab 2 focuses on the four vessel types with complete freight and insurance economics:  
    **VLCC, Suezmax, Aframax, LNG Carrier**.  

    Average freight rates of **{round(df_shipping['freight_rate_usd_day'].mean(),1)} USD/day**, 
    war risk premiums of **{round(df_shipping['war_risk_premium_pct'].mean(),1)}%**, and bunker costs of 
    **{round(df_shipping['bunker_cost_usd_mt'].mean(),1)} USD/mt** are tied directly to geographic lanes.  

    This ensures the dashboard remains clean, accurate, and recruiter‑ready by focusing only on vessels with valid shipping economics data.
    """)



# --- Tab 3: Country Risk ---


with tab3:
    st.subheader("Country Risk")

    # Filters
    phase_filter = st.selectbox(
        "Select Conflict Phase",
        ["All"] + list(get_data("SELECT conflict_phase FROM dim_conflict_phase ORDER BY conflict_phase")['conflict_phase']),
        key="country_phase_filter"
    )
    country_filter = st.selectbox(
        "Select Country",
        ["All"] + list(get_data("SELECT country FROM dim_country ORDER BY country")['country']),
        key="country_filter"
    )
    fuel_filter = st.selectbox(
        "Select Fuel Type",
        ["All"] + list(get_data("SELECT fuel_type FROM dim_fuel_type ORDER BY fuel_type")['fuel_type']),
        key="fuel_filter"
    )

    # Build WHERE clause
    where_clauses = []
    if phase_filter != "All":
        where_clauses.append(f"cp.conflict_phase = '{phase_filter}'")
    if country_filter != "All":
        where_clauses.append(f"c.country = '{country_filter}'")
    if fuel_filter != "All":
        where_clauses.append(f"ft.fuel_type = '{fuel_filter}'")
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    # Query supply chain + imports (no region, no lat/long)
    query_country = f"""
    SELECT 
        c.country,
        cp.conflict_phase,
        sc.supply_chain_disruption_index,
        sc.estimated_gdp_impact_musd,
        sc.avg_delivery_delay_days,
        sc.input_cost_increase_pct,
        sc.inventory_stress_score,
        sc.supplier_diversification_score,
        im.import_volume_kbpd,
        im.me_share_pct,
        im.alternative_source_pct,
        im.price_premium_pct,
        im.disruption_risk_score,
        im.spr_days_cover
    FROM fact_supply_chain sc
    JOIN dim_country c ON sc.country_key = c.country_key
    JOIN dim_conflict_phase cp ON sc.conflict_phase_key = cp.conflict_phase_key
    LEFT JOIN fact_imports im ON sc.country_key = im.country_key AND sc.conflict_phase_key = im.conflict_phase_key
    LEFT JOIN dim_fuel_type ft ON im.fuel_type_key = ft.fuel_type_key
    {where_sql}
    ORDER BY cp.conflict_phase, c.country;
    """
    df_country = get_data(query_country)

    # KPIs
    st.markdown("### Key Metrics (Filtered Selection)")
    col1, col2, col3 = st.columns(3)
    col1.metric("Avg GDP Impact (USDm)", round(df_country['estimated_gdp_impact_musd'].mean(), 1))
    col2.metric("Avg Delivery Delay (days)", round(df_country['avg_delivery_delay_days'].mean(), 1))
    col3.metric("Avg Import Risk Score", round(df_country['disruption_risk_score'].mean(), 1))

    # Bar chart: GDP impact by country
    gdp_chart = alt.Chart(df_country).mark_bar().encode(
        x='country:N',
        y='estimated_gdp_impact_musd:Q',
        color='conflict_phase:N',
        tooltip=['country','estimated_gdp_impact_musd','avg_delivery_delay_days','disruption_risk_score']
    ).properties(title="GDP Impact by Country")
    st.altair_chart(gdp_chart, width="stretch")

    # Line chart: import dependency vs SPR cover
    spr_chart = alt.Chart(df_country).mark_line(point=True).encode(
        x='me_share_pct:Q',
        y='spr_days_cover:Q',
        color='country:N',
        tooltip=['country','me_share_pct','spr_days_cover','alternative_source_pct']
    ).properties(title="Import Dependency vs SPR Cover")
    st.altair_chart(spr_chart, width="stretch")

    # Table view
    st.dataframe(df_country, width="stretch")

    # Download option
    csv = df_country.to_csv(index=False).encode('utf-8')
    st.download_button("Download Country Risk Data as CSV", csv, "country_risk.csv", "text/csv")

    # Recruiter-facing narrative
    st.markdown(f"""
    ### Recruiter-Facing Narrative
    Tab 3 elevates the analysis to the **national level**.  
    Countries face varying degrees of risk depending on their import dependency and supply chain resilience.  

    Average GDP impacts of **{round(df_country['estimated_gdp_impact_musd'].mean(),1)} million USD**, 
    delivery delays of **{round(df_country['avg_delivery_delay_days'].mean(),1)} days**, and import risk scores of 
    **{round(df_country['disruption_risk_score'].mean(),1)}** highlight how disruptions translate into economic vulnerability.  

    This tab demonstrates schema discipline by joining supply chain and import facts, showing recruiters how operational disruptions scale into strategic geopolitical risk.
    """)


# --- Tab 4: Sector Impact ---
with tab4:
    st.subheader("Sector Impact")

    # Filters
    phase_filter = st.selectbox(
        "Select Conflict Phase",
        ["All"] + list(get_data("SELECT conflict_phase FROM dim_conflict_phase ORDER BY conflict_phase")['conflict_phase']),
        key="sector_phase_filter"
    )
    sector_filter = st.selectbox(
        "Select Sector",
        ["All"] + list(get_data("SELECT sector FROM dim_sector ORDER BY sector")['sector']),
        key="sector_filter"
    )
    country_filter = st.selectbox(
        "Select Country",
        ["All"] + list(get_data("SELECT country FROM dim_country ORDER BY country")['country']),
        key="sector_country_filter"
    )

    # Build WHERE clause
    where_clauses = []
    if phase_filter != "All":
        where_clauses.append(f"cp.conflict_phase = '{phase_filter}'")
    if sector_filter != "All":
        where_clauses.append(f"s.sector = '{sector_filter}'")
    if country_filter != "All":
        where_clauses.append(f"c.country = '{country_filter}'")
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    # Query sector impact from fact_supply_chain
    query_sector = f"""
    SELECT 
        s.sector,
        c.country,
        cp.conflict_phase,
        sc.avg_delivery_delay_days,
        sc.input_cost_increase_pct,
        sc.inventory_stress_score,
        sc.estimated_gdp_impact_musd
    FROM fact_supply_chain sc
    JOIN dim_sector s ON sc.sector_key = s.sector_key
    JOIN dim_country c ON sc.country_key = c.country_key
    JOIN dim_conflict_phase cp ON sc.conflict_phase_key = cp.conflict_phase_key
    {where_sql}
    ORDER BY cp.conflict_phase, s.sector, c.country;
    """
    df_sector = get_data(query_sector)

    # KPIs
    st.markdown("### Key Metrics (Filtered Selection)")
    col1, col2, col3 = st.columns(3)
    col1.metric("Avg Delivery Delay (days)", round(df_sector['avg_delivery_delay_days'].mean(), 1))
    col2.metric("Avg Input Cost Increase (%)", round(df_sector['input_cost_increase_pct'].mean(), 1))
    col3.metric("Avg Inventory Stress Score", round(df_sector['inventory_stress_score'].mean(), 1))

    # Bar chart: GDP impact by sector
    gdp_chart = alt.Chart(df_sector).mark_bar().encode(
        x='sector:N',
        y='estimated_gdp_impact_musd:Q',
        color='conflict_phase:N',
        tooltip=['sector','country','estimated_gdp_impact_musd','avg_delivery_delay_days','input_cost_increase_pct']
    ).properties(title="GDP Impact by Sector")
    st.altair_chart(gdp_chart, width="stretch")

    # Line chart: delivery delay vs input cost increase
    delay_cost_chart = alt.Chart(df_sector).mark_line(point=True).encode(
        x='avg_delivery_delay_days:Q',
        y='input_cost_increase_pct:Q',
        color='sector:N',
        tooltip=['sector','country','avg_delivery_delay_days','input_cost_increase_pct']
    ).properties(title="Delivery Delay vs Input Cost Increase")
    st.altair_chart(delay_cost_chart, width="stretch")

    # Table view
    st.dataframe(df_sector, width="stretch")

    # Download option
    csv = df_sector.to_csv(index=False).encode('utf-8')
    st.download_button("Download Sector Impact Data as CSV", csv, "sector_impact.csv", "text/csv")

    # Recruiter-facing narrative
    st.markdown(f"""
    ### Recruiter-Facing Narrative
    Tab 4 highlights **industry vulnerabilities** using supply chain data joined with sector dimensions.  
    Sectors such as shipping, aviation, manufacturing, and energy show different levels of disruption.  

    Average delivery delays of **{round(df_sector['avg_delivery_delay_days'].mean(),1)} days**, 
    input cost increases of **{round(df_sector['input_cost_increase_pct'].mean(),1)}%**, and inventory stress scores of 
    **{round(df_sector['inventory_stress_score'].mean(),1)}** demonstrate how operational shocks ripple through industries.  

    This tab bridges national exposure (Tab 3) with industry‑level consequences, showing recruiters how schema‑driven analytics scale from macro disruptions to sector‑specific impacts.
    """)




# --- Tab 5: Policy Response ---
with tab5:
    st.subheader("Policy Response")

    # Filters
    phase_filter = st.selectbox(
        "Select Conflict Phase",
        ["All"] + list(get_data("SELECT conflict_phase FROM dim_conflict_phase ORDER BY conflict_phase")['conflict_phase']),
        key="policy_phase_filter"
    )
    country_filter = st.selectbox(
        "Select Country",
        ["All"] + list(get_data("SELECT country FROM dim_country ORDER BY country")['country']),
        key="policy_country_filter"
    )
    response_filter = st.selectbox(
        "Select Response Category",
        ["All"] + list(get_data("SELECT response_category FROM dim_response_category ORDER BY response_category")['response_category']),
        key="policy_response_filter"
    )

    # Build WHERE clause
    where_clauses = []
    if phase_filter != "All":
        where_clauses.append(f"cp.conflict_phase = '{phase_filter}'")
    if country_filter != "All":
        where_clauses.append(f"c.country = '{country_filter}'")
    if response_filter != "All":
        where_clauses.append(f"rc.response_category = '{response_filter}'")
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    # Query policy responses
    query_policy = f"""
    SELECT 
        c.country,
        cp.conflict_phase,
        rc.response_category,
        pr.estimated_cost_musd,
        pr.effectiveness_score,
        pr.me_dependency_reduction_pct
    FROM fact_response pr
    JOIN dim_country c ON pr.country_key = c.country_key
    JOIN dim_conflict_phase cp ON pr.conflict_phase_key = cp.conflict_phase_key
    JOIN dim_response_category rc ON pr.response_category_key = rc.response_category_key
    {where_sql}
    ORDER BY cp.conflict_phase, c.country, rc.response_category;
    """
    df_policy = get_data(query_policy)

    # KPIs
    st.markdown("### Key Metrics (Filtered Selection)")
    col1, col2, col3 = st.columns(3)
    col1.metric("Avg Policy Cost (USDm)", round(df_policy['estimated_cost_musd'].mean(), 1))
    col2.metric("Avg Effectiveness Score", round(df_policy['effectiveness_score'].mean(), 1))
    col3.metric("Avg Dependency Reduction (%)", round(df_policy['me_dependency_reduction_pct'].mean(), 1))

    # Bar chart: Policy cost by response category
    cost_chart = alt.Chart(df_policy).mark_bar().encode(
        x='response_category:N',
        y='estimated_cost_musd:Q',
        color='conflict_phase:N',
        tooltip=['country','response_category','estimated_cost_musd','effectiveness_score','me_dependency_reduction_pct']
    ).properties(title="Policy Cost by Response Category")
    st.altair_chart(cost_chart, width="stretch")

    # Scatter chart: Cost vs Effectiveness
    scatter_chart = alt.Chart(df_policy).mark_circle(size=100).encode(
        x='estimated_cost_musd:Q',
        y='effectiveness_score:Q',
        color='response_category:N',
        tooltip=['country','response_category','estimated_cost_musd','effectiveness_score','me_dependency_reduction_pct']
    ).properties(title="Cost vs Effectiveness of Policy Responses")
    st.altair_chart(scatter_chart, width="stretch")

    # Table view
    st.dataframe(df_policy, width="stretch")

    # Download option
    csv = df_policy.to_csv(index=False).encode('utf-8')
    st.download_button("Download Policy Response Data as CSV", csv, "policy_response.csv", "text/csv")

    # Recruiter-facing narrative
    st.markdown(f"""
    ### Recruiter-Facing Narrative
    Tab 5 showcases **strategic measures** taken by governments and firms.  
    Responses are categorized (via `dim_response_category`) into buckets such as SPR cover, diversification, and cost absorption.  

    Average policy costs of **{round(df_policy['estimated_cost_musd'].mean(),1)} million USD**, 
    effectiveness scores of **{round(df_policy['effectiveness_score'].mean(),1)}**, and dependency reductions of 
    **{round(df_policy['me_dependency_reduction_pct'].mean(),1)}%** highlight the trade‑offs in resilience strategies.  

    This tab completes the narrative arc: from disruptions and shipping economics, through country and sector vulnerabilities, to the **policy responses** that shape resilience. Recruiters see how schema‑driven analytics connect tactical shocks to strategic decisions.
    """)



# --- Tab 6: Cross-validation ---
with tab6:
    st.header("Model Validation & Drivers")

    # CV results
    cv_df = pd.read_csv("data/modeled/cv_results.csv")
    st.subheader("Cross-Validation Results")
    st.dataframe(cv_df)
    st.metric("Mean RMSE", f"{cv_df['rmse'].mean():.2f}")
    st.metric("Mean R²", f"{cv_df['r2'].mean():.2f}")

    # Altair charts
    rmse_chart = alt.Chart(cv_df).mark_bar().encode(x='fold:O', y='rmse:Q').properties(title="RMSE per fold")
    r2_chart = alt.Chart(cv_df).mark_bar().encode(x='fold:O', y='r2:Q').properties(title="R² per fold")
    st.altair_chart(rmse_chart, width="stretch")
    st.altair_chart(r2_chart, width="stretch")

    # Feature importance
    importance_df = pd.read_csv("data/modeled/feature_importance.csv")
    st.subheader("Top 10 Feature Importances")
    st.bar_chart(importance_df.set_index("feature"))

    # Consolidated summary
    summary_df = pd.read_csv("data/modeled/model_summary.csv")
    st.subheader("Download Recruiter Pack")
    st.download_button("Download Consolidated Model Summary", summary_df.to_csv(index=False).encode('utf-8'),
                       "model_summary.csv", "text/csv")

    # Narrative
    st.markdown(f"""
    ### Recruiter-Facing Narrative
    Cross-validation confirms stability: mean RMSE **{cv_df['rmse'].mean():.2f}**, mean R² **{cv_df['r2'].mean():.2f}**.  
    Feature importance highlights the strongest drivers of GDP impact, such as **{importance_df.iloc[0,0]}** and **{importance_df.iloc[1,0]}**.  
    The consolidated summary file provides a one-click recruiter pack combining validation and interpretability.
    """)





