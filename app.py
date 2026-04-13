from fastapi import FastAPI
from optimizer import create_data_model, solve_vrp # Assuming you renamed your logic to solve_vrp

app = FastAPI()

@app.get("/optimize")
def get_route():
    data = create_data_model()
    # Logic to run your solver and return JSON
    return {"status": "success", "total_distance": 3104, "routes": "..."}