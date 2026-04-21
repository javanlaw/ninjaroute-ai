import streamlit as st
import random
import pandas as pd
import plotly.express as px

# --- 1. HELPER FUNCTIONS & ENGINE ---

def calculate_arrival_time(index, van_load, risk_multiplier=1.0):
    """Calculates 12-hour format arrival time adjusted by environmental risk."""
    service_minutes = (van_load * 2) * risk_multiplier
    travel_offset = (index * 30) * risk_multiplier
    total_mins_from_midnight = 480 + travel_offset + service_minutes
    hour_24, mins = divmod(int(total_mins_from_midnight), 60)
    
    period = "AM" if hour_24 < 12 else "PM"
    if hour_24 == 0: hour_12 = 12
    elif hour_24 == 12: hour_12 = 12
    elif hour_24 > 12: hour_12 = hour_24 - 12
    else: hour_12 = hour_24
        
    return f"{hour_12}:{mins:02d} {period}"

def calculate_fuel_efficiency(load, distance, risk_multiplier):
    """Estimates fuel cost based on Singapore Petrol prices (~$2.85/L)."""
    base_rate = 0.12  
    load_impact = (load / 100) * 0.05
    traffic_impact = (risk_multiplier - 1) * 0.1
    total_liters = distance * (base_rate + load_impact + traffic_impact)
    return round(total_liters * 2.85, 2)

def get_optimized_data(vans, capacity, total_parcels, risk_multiplier=1.0):
    """Heuristic Engine to distribute load across a fleet."""
    if (vans * capacity) < total_parcels:
        return []

    sg_zones = [
        "North-East (Punggol/Sengkang)", "West (Jurong/Clementi)", 
        "Central (CBD/Orchard)", "East (Tampines/Changi)", "North (Woodlands/Yishun)"
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
        dist = 15 + (i * 2) 
        fuel_cost = calculate_fuel_efficiency(van_load, dist, risk_multiplier)
        
        results.append({
            "Van": f"Ninja Van {i + 1:02d}",
            "Stop": sg_zones[i % len(sg_zones)],
            "Arrival": calculate_arrival_time(i, van_load, risk_multiplier), 
            "Load_Raw": van_load,
            "Capacity": capacity,
            "Fuel_Cost": fuel_cost,
            "Status": "⚠️ Potential Delay" if (van_load / capacity) > 0.90 or risk_multiplier > 1.3 else "✅ On Time"
        })
    return results

# --- 2. UI LAYOUT ---
st.set_page_config(page_title="Ninja Van Optimizer Pro", layout="wide")
st.title("🚚 NinjaRoute AI: Smart Dispatcher")

with st.sidebar:
    st.header("📂 Data Integration")
    uploaded_file = st.file_uploader("Upload Delivery Dataset (CSV)", type=["csv"])
    
    st.divider()
    st.header("🌦️ Environmental Factors")
    weather = st.selectbox("Current Weather", ["Clear Skies", "Light Rain", "Heavy Rain/Flash Flood"])
    traffic = st.select_slider("Traffic Density", options=["Smooth", "Moderate", "Heavy Peak"])
    
    risk_mult = 1.0
    if weather == "Light Rain": risk_mult += 0.2
    if weather == "Heavy Rain/Flash Flood": risk_mult += 0.5
    if traffic == "Moderate": risk_mult += 0.1
    if traffic == "Heavy Peak": risk_mult += 0.3

    st.divider()
    st.header("Fleet Controls")
    num_vans = st.slider("Active Vans", 1, 10, 5)
    max_load = st.number_input("Max Parcels per Van", value=50)
    total_parcels_slider = st.slider("Total Volume (Manual)", 10, 500, 150)
    
    optimize_upload = st.checkbox("Optimize Uploaded CSV Data", value=True)
    st.button("🔄 Re-Optimize Fleet", use_container_width=True)

# --- 3. EXECUTION LOGIC (Updated for Independence) ---
if uploaded_file is not None:
    df_raw = pd.read_csv(uploaded_file, encoding='utf-8-sig')
    df_raw.columns = df_raw.columns.str.strip().str.title()
    
    if 'Load' not in df_raw.columns:
        st.error("❌ Column Mismatch: CSV must contain a 'Load' header.")
        st.stop()
    
    # Use Volume from CSV, ignoring the Manual Slider
    active_volume = int(df_raw['Load'].sum())
    st.info(f"📁 Source: CSV File ({active_volume} Units)")

    if optimize_upload:
        # Optimization logic applied to CSV data
        route_data = get_optimized_data(num_vans, max_load, active_volume, risk_mult)
        if not route_data:
            st.error(f"❌ Infeasible: CSV Volume ({active_volume}) exceeds Fleet Capacity.")
            st.stop()
        df = pd.DataFrame(route_data)
    else:
        # Display CSV data exactly as is
        df = df_raw.copy()
        df['Load_Raw'] = df['Load'].fillna(0).astype(int)
        if 'Van' not in df.columns: df['Van'] = [f"Van {i+1}" for i in range(len(df))]
        if 'Stop' not in df.columns: df['Stop'] = "Local Cluster"
        df['Arrival'] = [calculate_arrival_time(i, row['Load_Raw'], risk_mult) for i, row in df.iterrows()]
        df['Fuel_Cost'] = [calculate_fuel_efficiency(row['Load_Raw'], 15 + (i*2), risk_mult) for i, row in df.iterrows()]
        df['Status'] = df['Load_Raw'].apply(lambda x: "⚠️ Potential Delay" if x/max_load > 0.90 or risk_mult > 1.3 else "✅ On Time")
else:
    # Source: Manual Slider
    active_volume = total_parcels_slider
    st.info(f"🤖 Source: Manual Simulation ({active_volume} Units)")
    
    route_data = get_optimized_data(num_vans, max_load, active_volume, risk_mult)
    if not route_data:
        st.error(f"❌ Infeasible: Increase Vans or Capacity to meet volume.")
        st.stop()
    df = pd.DataFrame(route_data)

plot_df = df
display_df = df[['Van', 'Stop', 'Arrival', 'Load_Raw', 'Fuel_Cost', 'Status']].rename(columns={"Load_Raw": "Load (Units)"})

# --- 4. ENHANCED METRICS ---
actual_load = int(plot_df['Load_Raw'].sum())
total_fuel = round(plot_df['Fuel_Cost'].sum(), 2)
total_dist = 15 + (len(plot_df) * 12)

col1, col2, col3 = st.columns(3)
col1.metric("Est. Total Fuel Cost", f"S${total_fuel}", delta=f"{risk_mult}x Risk Factor", delta_color="inverse")
col2.metric("Total Dispatch Volume", f"{actual_load} Units")
col3.metric("Fleet Est. Distance", f"{total_dist} km", delta="Weather Adjusted")

# --- 5. TABLE & CHART ---
st.subheader("📍 Singapore Cluster Dispatch Schedule")
st.dataframe(display_df, use_container_width=True, hide_index=True)

st.subheader("📊 Operational Analytics")
tab1, tab2 = st.tabs(["Fuel vs Load", "SLA Status"])

with tab1:
    fig_scatter = px.scatter(
        plot_df, x="Load_Raw", y="Fuel_Cost", size="Fuel_Cost", color="Status",
        hover_name="Van", title="Fuel Consumption relative to Parcel Weight",
        labels={'Load_Raw': 'Parcels', 'Fuel_Cost': 'Fuel Cost (S$)'},
        color_discrete_map={"✅ On Time": "#2ecc71", "⚠️ Potential Delay": "#e74c3c"},
        template="plotly_white"
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with tab2:
    fig_bar = px.bar(
        plot_df, x="Van", y="Load_Raw", color="Status",
        title="Fleet Load Distribution",
        color_discrete_map={"✅ On Time": "#2ecc71", "⚠️ Potential Delay": "#e74c3c"}
    )
    st.plotly_chart(fig_bar, use_container_width=True)
