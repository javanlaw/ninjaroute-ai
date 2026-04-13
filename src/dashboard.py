import streamlit as st
import random
import pandas as pd
import pandas as pd
import plotly.express as px


# 1. Define the dynamic function
def get_optimized_data(vans, capacity, total_parcels):
    if (vans * capacity) < total_parcels:
        return []

    results = []
    remaining_parcels = total_parcels
    
    for i in range(vans):
        # Calculate Load distribution
        if i == vans - 1:
            van_load = remaining_parcels
        else:
            ideal_share = total_parcels // vans
            van_load = random.randint(max(5, ideal_share - 5), min(capacity, ideal_share + 10))
            van_load = min(van_load, remaining_parcels - (vans - i - 1))
            
        remaining_parcels -= van_load
        
        # TIME LOGIC: 2 mins per parcel + 30 min zone offset
        service_minutes = van_load * 2  
        travel_offset = i * 30 
        total_minutes_after_8 = travel_offset + service_minutes
        
        hour = 8 + (total_minutes_after_8 // 60)
        minutes = total_minutes_after_8 % 60

        # STATUS LOGIC: Check if this specific van is at high risk
        van_utilization = van_load / capacity
        if van_utilization > 0.95:
            van_status = "⚠️ Potential Delay"
        else:
            van_status = "✅ On Time"

        results.append({
            "Van": f"Ninja Van {i + 1}",
            "Stop": f"Zone {chr(65 + i)} Cluster",
            "Arrival": f"{hour}:{minutes:02d} AM", 
            "Load": f"{van_load}/{capacity}",
            "Status": van_status
        })
        
    return results

# 2. Streamlit UI Layout
st.set_page_config(page_title="Ninja Van Optimizer", layout="wide")
st.title("🚚 Ninja Van: AI Route Dispatcher")

with st.sidebar:
    st.header("Fleet Controls")
    num_vans = st.slider("Active Vans", 1, 5, 2)
    max_load = st.number_input("Max Parcels per Van", value=50)
    total_parcels = st.slider("Total Parcels to Deliver", 10, 200, 60) 
    st.button("Re-Optimize Fleet")

# 3. Execution Logic
# FIX: Added total_parcels to the function call
route_data = get_optimized_data(num_vans, max_load, total_parcels)

if not route_data:
    st.error(f"❌ Infeasible: {num_vans} van(s) cannot carry {total_parcels} parcels with a {max_load} limit.")
else:
    df = pd.DataFrame(route_data)
    df['Load_Numeric'] = df['Load'].apply(lambda x: int(x.split('/')[0]))

    # 4. Global SLA Logic (for the Metric Box)
    fleet_utilization = total_parcels / (num_vans * max_load)
    if fleet_utilization > 0.95:
        sla_val, sla_delta = "92%", "-8% (High Risk)"
    else:
        sla_val, sla_delta = "100%", "Stable"

    # 5. Metrics Row
    col1, col2, col3 = st.columns(3)
    estimated_dist = f"{3000 + (total_parcels * 10):,.0f} m"
    col1.metric("Total Distance", estimated_dist, "Optimized")
    col2.metric("Total Parcels", f"{total_parcels} Units") 
    col3.metric("SLA Compliance", sla_val, sla_delta)

    # 6. Table & Visuals
    st.subheader("Optimized Delivery Schedule")
    st.table(df.drop(columns=['Load_Numeric']))

    st.subheader("Vehicle Load Analysis")
    fig = px.bar(
        df, x="Van", y="Load_Numeric", color="Van", text="Load", 
        title=f"Fleet Load Distribution (Cap: {max_load})",
        labels={'Load_Numeric': 'Number of Parcels'},
        template="plotly_white"
    )
    st.plotly_chart(fig, use_container_width=True)