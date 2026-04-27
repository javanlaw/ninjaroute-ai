🚚 NinjaRoute AI: Autonomous Route Optimization Engine
NinjaRoute AI is an end-to-end AI solution designed for Ninja Van to transform manual delivery planning into a dynamic, data-driven ecosystem. By integrating Constraint Optimization and Predictive Analytics, the system addresses the critical logistics "Triple Threat": Fuel Costs, Late Deliveries, and Driver Burnout.

🏗️ AI Architecture
The system employs a multi-layered approach to solve the Vehicle Routing Problem (VRP) specifically for the Singapore landscape:

Optimization Layer: Employs custom heuristics and logic to distribute parcel volume across a fleet, ensuring no vehicle exceeds its physical capacity while balancing load parity.

Predictive Layer (Risk Engine): Adjusts arrival times and fuel consumption estimates based on a Dynamic Risk Multiplier. This multiplier is fed by real-time environmental data.

Monitoring Layer: A reactive Streamlit-based "Control Tower" that provides real-time SLA risk assessments and fleet visualization.

🌦️ Smart Environmental Integration
The engine treats the environment as a living variable rather than a static constraint:

Live Weather Sync: Connects to the NEA 2-hour Nowcast API via data.gov.sg to detect rain or stormy conditions across Singapore.

Traffic Heuristic: Calculates congestion levels based on Singapore Standard Time (SGT). It automatically identifies morning and evening peak hours (e.g., 08:00–10:00 and 17:00–20:00) to adjust travel offsets.

Efficiency Factor: The system calculates a cumulative risk_mult.

Example: Heavy Rain (+0.5) + Heavy Traffic (+0.3) = 1.8x Efficiency Penalty on fuel and time.

🛠️ Tech Stack
Language: Python 3.9+

UI Framework: Streamlit (Logistics Control Tower)

Data Handling: Pandas (Fleet Load Management)

Visualization: Plotly Express (Operational Analytics)

API/Time: Requests (NEA API), Pytz (SGT Sync)
