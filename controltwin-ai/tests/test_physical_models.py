from app.simulation.physical_models import PhysicalModels


def test_pipeline_pressure_darcy_weisbach():
    out = PhysicalModels.pipeline_pressure(
        inlet_pressure_bar=40,
        flow_rate_m3h=100,
        pipe_length_km=10,
        pipe_diameter_mm=300,
        fluid_viscosity=0.001,
        fluid_density=850,
    )
    assert out < 40
    assert out > 0


def test_thermal_model_steady_state_convergence():
    temps = PhysicalModels.thermal_model(
        initial_temp_c=30,
        ambient_temp_c=25,
        heat_generation_kw=1.0,
        thermal_resistance=0.5,
        thermal_capacity=5000,
        time_steps_minutes=240,
    )
    assert len(temps) == 241
    assert temps[-1] > temps[0] - 10


def test_load_flow_energy_balance():
    nodes = ["A", "B", "C"]
    edges = [
        {"from": "A", "to": "B", "impedance": 0.2},
        {"from": "B", "to": "C", "impedance": 0.3},
        {"from": "A", "to": "C", "impedance": 0.25},
    ]
    generation = {"A": 50}
    loads = {"B": 20, "C": 28}
    res = PhysicalModels.load_flow_dc(nodes, edges, generation, loads)
    assert "voltages" in res and "flows" in res
    assert abs(sum(generation.values()) - sum(loads.values())) <= 5
