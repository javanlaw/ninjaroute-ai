import streamlit as st
import random
import pandas as pd
import plotly.express as px

# --- 1. CORE ENGINE ---
def get_optimized_data(vans, capacity, total_parcels):
    if (vans * capacity) < total_parcels:
        return []

    sg_zones = [
        "North-East (Punggol/Sengkang)", 
        "West (Jurong/Clementi)", 
        "Central (CBD/Orchard)", 
        "East (Tampines/Changi)", 
        "North (Woodlands/Yishun)"
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
        
        service_minutes = van_load * 2  
        travel_offset = i * 30 
        total_minutes_after_8 = travel_offset + service_minutes
        
        hour = 8 + (total_minutes_after_8 // 60)
        minutes = total_minutes_after_8 % 60

        utilization = van_load / capacity
        status = "⚠️ Potential Delay" if utilization > 0.95 else "✅ On Time"

        results.append({
            "Van": f"Ninja Van {i + 1}",
            "Stop": sg_zones[i % len(sg_zones)],
            "Arrival": f"{hour}:{minutes:02d} AM", 
            "Load_Raw": van_load,
            "Capacity": capacity,
            "Status": status
        })
    return results

# --- 2. UI LAYOUT ---
st.set_page_config(page_title="Ninja Van Optimizer", layout="wide")
st.title("🚚 NinjaRoute AI: Singapore Dispatcher")

with st.sidebar:
    st.header("📂 Data Integration")
    uploaded_file = st.file_uploader("Upload Delivery Dataset (CSV)", type=["csv"])
    
    st.divider()
    st.header("Fleet Controls")
    num_vans = st.slider("Active Vans", 1, 10, 3)
    max_load = st.number_input("Max Parcels per Van", value=50)
    total_parcels = st.slider("Total Volume", 10, 500, 120)
    st.button("🔄 Re-Optimize Fleet", use_container_width=True)

# --- 3. EXECUTION LOGIC ---
if uploaded_file is not None:
    df_raw = pd.read_csv(uploaded_file)
    df = df_raw.copy()
    df['Load_Raw'] = df['Load']
    df['Utilization'] = df['Load'] / df['Capacity']
    df['Status'] = df['Utilization'].apply(lambda x: "⚠️ Potential Delay" if x > 0.95 else "✅ On Time")
    df['Load_Display'] = df['Load'].astype(str) + "/" + df['Capacity'].astype(str)
    display_df = df[['Van', 'Stop', 'Load_Display', 'Status']].rename(columns={"Load_Display": "Load"})
    plot_df = df
else:
    route_data = get_optimized_data(num_vans, max_load, total_parcels)
    if not route_data:
        st.error(f"❌ Infeasible: Capacity exceeded.")
        st.stop()
    df = pd.DataFrame(route_data)
    df['Load'] = df['Load_Raw'].astype(str) + "/" + df['Capacity'].astype(str)
    display_df = df[['Van', 'Stop', 'Arrival', 'Load', 'Status']]
    plot_df = df

# --- 4. ENHANCED METRICS & SLA PERCENTAGE ---
actual_load = int(plot_df['Load_Raw'].sum())
fleet_capacity = len(plot_df) * max_load
utilization_pct = (actual_load / fleet_capacity) * 100

# SLA Percentage Calculation: 
# We simulate a "target" utilization of 85%. 
# If load goes over 95%, SLA drops significantly.
if utilization_pct > 95:
    sla_percentage = 100 - (utilization_pct - 85) * 2  # Drastic drop
    sla_label = "⚠️ High Risk"
    sla_color = "inverse"
elif utilization_pct > 80:
    sla_percentage = 98.5
    sla_label = "⚡ Optimized"
    sla_color = "normal"
else:
    sla_percentage = 100.0
    sla_label = "✅ Stable"
    sla_color = "normal"

col1, col2, col3 = st.columns(3)

col1.metric("Total Fleet Distance", f"{15 + (len(plot_df) * 10)} km", delta="Optimized", delta_color="normal")
col2.metric("Total Dispatch Volume", f"{actual_load} Units")

# Displaying SLA with the Percentage
col3.metric(
    label="SLA Compliance Score", 
    value=f"{sla_percentage:.1f}%", 
    delta=sla_label, 
    delta_color=sla_color
)

# --- 5. TABLE & CHART ---
st.subheader("📍 Singapore Cluster Dispatch Schedule")
st.dataframe(display_df, use_container_width=True, hide_index=True)

st.subheader("📊 Vehicle Load Analysis")
fig = px.bar(
    plot_df, x="Van", y="Load_Raw", color="Status", text="Load_Raw",
    title="Fleet Load Distribution",
    labels={'Load_Raw': 'Parcels'},
    color_discrete_map={"✅ On Time": "#2ecc71", "⚠️ Potential Delay": "#e74c3c"},
    template="plotly_white"
)
st.plotly_chart(fig, use_container_width=True)
