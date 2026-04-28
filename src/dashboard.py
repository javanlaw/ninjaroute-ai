import streamlit as st
import random
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime
import pytz

# --- 1. HELPER FUNCTIONS & ENGINE ---

def get_simulated_live_traffic():
    """Predicts SG traffic density based on current Singapore time (SGT)."""
    try:
        sg_tz = pytz.timezone('Asia/Singapore')
        now_sg = datetime.now(sg_tz)
        current_hour = now_sg.hour
        day_of_week = now_sg.weekday() 
        if day_of_week >= 5 or current_hour < 7 or current_hour > 21:
            return "Smooth"
        elif (8 <= current_hour <= 10) or (17 <= current_hour <= 20):
            return "Heavy Peak"
        else:
            return "Moderate"
    except:
        return "Moderate"

def fetch_sg_weather():
    """Fetches real-time weather from NEA API via data.gov.sg."""
    try:
        url = "https://api-open.data.gov.sg/v2/real-time/api/two-hr-nowcast"
        response = requests.get(url, timeout=3) 
        if response.status_code == 200:
            data = response.json()
            items = data.get('data', {}).get('items', [])
            if items:
                forecasts = items[0].get('forecasts', [])
                if forecasts:
                    forecast = forecasts[0].get('forecast', "Clear Skies")
                    if any(x in forecast for x in ["Thunder", "Heavy", "Storm"]):
                        return "Heavy Rain/Flash Flood"
                    elif any(x in forecast for x in ["Rain", "Showers"]):
                        return "Light Rain"
        return "Clear Skies" 
    except Exception:
        return "Clear Skies"

def fetch_api_data(api_url):
    """Fetches delivery data from an external API endpoint."""
    try:
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data)
    except Exception as e:
        st.sidebar.error(f"API Error: {e}")
        return None

def calculate_arrival_time(index, van_load, risk_multiplier=1.0):
    """Calculates 12-hour format arrival time adjusted by environmental risk."""
    service_minutes = (van_load * 2) * risk_multiplier
    travel_offset = (index * 30) * risk_multiplier
    total_mins_from_midnight = 480 + travel_offset + service_minutes
    hour_24, mins = divmod(int(total_mins_from_midnight), 60)
    
    period = "AM" if hour_24 < 12 else "PM"
    hour_12 = hour_24 % 12
    if hour_12 == 0: hour_12 = 12
    return f"{hour_12}:{mins:02d} {period}"

def calculate_fuel_efficiency(load, distance, risk_multiplier):
    """Estimates fuel cost based on Singapore Petrol prices (~$2.85/L)."""
    base_rate = 0.12  
    load_impact = (load / 100) * 0.05
    traffic_impact = (risk_multiplier - 1) * 0.1
    total_liters = distance * (base_rate + load_impact + traffic_impact)
    return round(total_liters * 2.85, 2)

def get_optimized_data(vans, capacity, total_parcels, risk_multiplier=1.0):
    """Heuristic Engine to distribute load across a fleet with Regional Routing."""
    if (vans * capacity) < total_parcels:
        return []

    ZONE_PLANS = [
        {"name": "North-East (Punggol/Sengkang)", "sectors": "53-55, 82", "route": "HQ → Sengkang East → Punggol Central → Northshore"},
        {"name": "West (Jurong/Clementi)", "sectors": "12, 60-64", "route": "HQ → Clementi Ave 6 → Jurong East St 21 → Tuas South"},
        {"name": "Central (CBD/Orchard)", "sectors": "01-09, 22-23", "route": "HQ → Tanjong Pagar → Raffles Quay → Orchard Rd"},
        {"name": "East (Tampines/Changi)", "sectors": "46-52, 81", "route": "HQ → Bedok South → Tampines Hub → Changi Cargo"},
        {"name": "North (Woodlands/Yishun)", "sectors": "72-76", "route": "HQ → Mandai Rd → Woodlands Sq → Sembawang Dr"}
    ]

    results = []
    remaining_parcels = total_parcels
    for i in range(vans):
        if i == vans - 1:
            van_load = remaining_parcels
        else:
            ideal_share = total_parcels // vans
            van_load = random.randint(max(5, ideal_share - 5), min(capacity, ideal_share + 10))
            van_load = min(van_load, remaining_parcels - (vans - i - 1))
        
        remaining_parcels -= van_load
        zone_info = ZONE_PLANS[i % len(ZONE_PLANS)]
        dist = 15 + (i * 2) 
        fuel_cost = calculate_fuel_efficiency(van_load, dist, risk_multiplier)
        
        results.append({
            "Van": f"Ninja Van {i + 1:02d}",
            "Stop": zone_info["name"],
            "Sectors": zone_info["sectors"],
            "Planned_Route": zone_info["route"],
            "Arrival": calculate_arrival_time(i, van_load, risk_multiplier), 
            "Load_Raw": van_load, 
            "Capacity": capacity, 
            "Fuel_Cost": fuel_cost,
            "Status": "⚠️ Potential Delay" if (van_load / capacity) > 0.90 or risk_multiplier > 1.3 else "✅ On Time"
        })
    return results

# --- 2. UI LAYOUT & CONTROL TOWER ---
st.set_page_config(page_title="NinjaRoute | Operational Control Tower", layout="wide")

st.title("🛡️ NinjaRoute AI: Command & Control Center")

if 'live_weather' not in st.session_state:
    st.session_state.live_weather = fetch_sg_weather()
if 'live_traffic' not in st.session_state:
    st.session_state.live_traffic = get_simulated_live_traffic()

t1, t2, t3, t4 = st.columns([2, 1, 1, 1])
with t1:
    st.caption("SYSTEM STATUS: ONLINE")
    st.write(f"**Last Telemetry Sync:** {datetime.now().strftime('%H:%M:%S')} SGT")
with t2:
    st.metric("LIVE WEATHER", st.session_state.live_weather)
with t3:
    st.metric("TRAFFIC DENSITY", st.session_state.live_traffic)
with t4:
    if st.button("🔄 Sync Telemetry", use_container_width=True):
        st.session_state.live_weather = fetch_sg_weather()
        st.session_state.live_traffic = get_simulated_live_traffic()
        st.rerun()

st.divider()

with st.sidebar:
    st.header("⚙️ Mission Parameters")
    
    with st.expander("📡 Data Feed", expanded=True):
        use_api = st.checkbox("Connect to Live API Feed")
        api_endpoint = st.text_input("API URL", value="https://api.example.com/deliveries")
        uploaded_file = st.file_uploader("Upload Delivery Dataset (CSV)", type=["csv"])

    st.divider()
    st.header("Fleet Controls")
    num_vans = st.slider("Active Vans", 1, 10, 6)
    max_load = st.number_input("Max Parcels per Van", value=50)
    total_parcels_slider = st.slider("Total Volume (Manual)", 10, 500, 200)
    
    st.button("🔄 Re-Optimize Fleet", use_container_width=True, type="primary")

    risk_mult = 1.0
    if st.session_state.live_weather == "Light Rain": risk_mult += 0.2
    elif st.session_state.live_weather == "Heavy Rain/Flash Flood": risk_mult += 0.5
    if st.session_state.live_traffic == "Moderate": risk_mult += 0.1
    elif st.session_state.live_traffic == "Heavy Peak": risk_mult += 0.3

# --- 3. EXECUTION LOGIC ---
api_df = fetch_api_data(api_endpoint) if use_api else None
source_df = api_df if api_df is not None else (pd.read_csv(uploaded_file, encoding='utf-8-sig') if uploaded_file else None)

if source_df is not None:
    source_df.columns = source_df.columns.str.strip().str.title()
    active_volume = int(source_df['Load'].sum()) if 'Load' in source_df.columns else total_parcels_slider
else:
    active_volume = total_parcels_slider

route_data = get_optimized_data(num_vans, max_load, active_volume, risk_mult)

if not route_data:
    st.error(f"🚨 **ALERT: FLEET CAPACITY EXCEEDED!** Shortfall: {active_volume - (num_vans * max_load)} units")
    st.stop()

df = pd.DataFrame(route_data)

# --- 4. ENHANCED METRICS ---
col1, col2, col3 = st.columns(3)
col1.metric("Est. Total Fuel Cost", f"S${df['Fuel_Cost'].sum():.2f}", delta=f"{risk_mult}x Risk")
col2.metric("Total Dispatch Volume", f"{int(df['Load_Raw'].sum())} Units")
col3.metric("Fleet Est. Distance", f"{15 + (len(df) * 12)} km")

# --- 5. TABLE & CHART ---
st.subheader("📍 Singapore Cluster Dispatch Schedule")
display_df = df[['Van', 'Stop', 'Sectors', 'Planned_Route', 'Arrival', 'Load_Raw', 'Status']].rename(
    columns={"Load_Raw": "Load (Units)", "Planned_Route": "Route Plan"}
)

# UPDATED: Using data_editor with column_config to prevent "Potential Delay" truncation
st.data_editor(
    display_df,
    use_container_width=True,
    hide_index=True,
    disabled=True,
    column_config={
        "Status": st.column_config.Column(
            "Status",
            width="medium",
            help="Real-time delivery status"
        ),
        "Route Plan": st.column_config.Column(
            "Route Plan",
            width="large"
        )
    }
)

st.divider() 
st.subheader("📊 Operational Analytics")

chart_col1, chart_col2 = st.columns(2)
with chart_col1:
    fig_scatter = px.scatter(df, 
                             x="Load_Raw", 
                             y="Fuel_Cost", 
                             size="Fuel_Cost", 
                             color="Status",
                             text="Van", 
                             title="Fuel Consumption vs Payload (by Vehicle)", 
                             template="plotly_white",
                             labels={"Load_Raw": "Units", "Fuel_Cost": "Cost (S$)"},
                             color_discrete_map={"✅ On Time": "#2ecc71", "⚠️ Potential Delay": "#e74c3c"})
    
    fig_scatter.update_traces(textposition='top center')
    st.plotly_chart(fig_scatter, use_container_width=True)

with chart_col2:
    fig_bar = px.bar(df, x="Van", y="Load_Raw", color="Status", title="Fleet Resource Distribution",
                     labels={"Load_Raw": "Units"},
                     color_discrete_map={"✅ On Time": "#2ecc71", "⚠️ Potential Delay": "#e74c3c"})
    st.plotly_chart(fig_bar, use_container_width=True)
