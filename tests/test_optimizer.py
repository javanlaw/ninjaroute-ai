import pytest
from src.dashboard import get_optimized_data

def test_optimizer_logic():
    # Test if 2 vans with 50 capacity can carry 60 parcels
    result = get_optimized_data(2, 50, 60)
    assert len(result) == 2
    assert result[0]['Status'] in ["✅ On Time", "⚠️ Potential Delay"]

def test_infeasible_scenario():
    # Test if 1 van with 10 capacity fails to carry 100 parcels
    result = get_optimized_data(1, 10, 100)
    assert result == []

def test_time_formatting():
    # Test if the arrival time string is formatted correctly (e.g., "8:30 AM")
    result = get_optimized_data(1, 10, 10)
    arrival_time = result[0]['Arrival']
    assert ":" in arrival_time
    assert ("AM" in arrival_time or "PM" in arrival_time)
