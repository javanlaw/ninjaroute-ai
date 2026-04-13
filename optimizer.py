from ortools.constraint_solver import pywrapcp, routing_enums_pb2

def create_data_model():
    data = {}
    data['distance_matrix'] = [
        [0, 548, 776, 696], [548, 0, 684, 308],
        [776, 684, 0, 991], [696, 308, 991, 0],
    ]
    data['time_windows'] = [(0, 500), (50, 100), (100, 150), (50, 200)]
    data['demands'] = [0, 15, 25, 20]
    data['vehicle_capacities'] = [50, 50]
    data['num_vehicles'] = 2
    data['depot'] = 0
    data['service_time'] = 10
    data['speed_kmh'] = 20
    return data

def print_solution(data, manager, routing, solution):
    """Prints solution on console with Time, Distance, and Load details."""
    print(f"\n===== NINJA VAN AI OPTIMIZATION REPORT =====")
    time_dimension = routing.GetDimensionOrDie('Time')
    total_distance = 0
    total_load = 0

    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        plan_output = f'\nRoute for Ninja Van {vehicle_id + 1}:\n'
        route_distance = 0
        route_load = 0
        
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route_load += data['demands'][node_index]
            time_var = time_dimension.CumulVar(index)
            
            plan_output += (f" Stop {node_index} "
                           f"[Time: {solution.Value(time_var):>3}m | "
                           f"Load: {route_load:>2}/{data['vehicle_capacities'][vehicle_id]}] ->\n")
            
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += data['distance_matrix'][manager.IndexToNode(previous_index)][manager.IndexToNode(index)]

        time_var = time_dimension.CumulVar(index)
        plan_output += f" Depot {manager.IndexToNode(index)} [Arrival: {solution.Value(time_var)}m]"
        print(plan_output)
        print(f"  └─ Route Summary: {route_distance}m traveled | Final Load: {route_load}")
        total_distance += route_distance
        total_load += route_load

    print(f"\n--- FLEET TOTALS ---")
    print(f"Total Distance: {total_distance}m | Total Parcels: {total_load}")
    print(f"============================================\n")

def main():
    data = create_data_model()
    manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']),
                                           data['num_vehicles'], data['depot'])
    routing = pywrapcp.RoutingModel(manager)

    # Callbacks
    def time_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        travel_time = (data['distance_matrix'][from_node][to_node] / 1000) / data['speed_kmh'] * 60
        service_time = data['service_time'] if from_node != 0 else 0
        return int(travel_time + service_time)

    transit_callback_index = routing.RegisterTransitCallback(time_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Capacity
    def demand_callback(from_index):
        return data['demands'][manager.IndexToNode(from_index)]
    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(demand_callback_index, 0, data['vehicle_capacities'], True, 'Capacity')

    # Time Windows
    routing.AddDimension(transit_callback_index, 30, 500, False, 'Time')
    time_dimension = routing.GetDimensionOrDie('Time')
    for location_idx, time_window in enumerate(data['time_windows']):
        index = manager.NodeToIndex(location_idx)
        time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])

    # Search parameters
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    solution = routing.SolveWithParameters(search_parameters)
    if solution:
        print_solution(data, manager, routing, solution)
    else:
        print("No feasible solution found!")

if __name__ == '__main__':
    main()