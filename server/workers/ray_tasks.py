"""Optional Ray task for parallel offline scenario sweeps; never used for each live frame."""
from pathlib import Path


def _run_scenario(config_data, steps):
    from simulation_environment.simulation import CrowdSimulation, SimulationConfig
    from simulation_environment.simulation.environment import Environment
    config = SimulationConfig(**config_data)
    project_root = Path(__file__).resolve().parents[2] / "simulation_environment"
    simulation = CrowdSimulation(config=config, project_root=project_root)
    simulation.run(duration_seconds=max(config.dt, steps * config.dt))
    state = simulation.state()
    return {"simulation_time": state["simulation_time"], "status": state["status"],
            "evacuated_count": state["evacuated_count"], "remaining_agents": state["remaining_agents"],
            "ml_enabled": state["ml_enabled"]}


def submit_scenario(config_data, steps):
    try:
        import ray
    except ImportError as exc:
        raise RuntimeError("Install server/requirements-ray.txt to enable Ray workers") from exc
    address = __import__("os").getenv("RAY_ADDRESS")
    if not ray.is_initialized():
        ray.init(address=address or None, ignore_reinit_error=True, logging_level="ERROR")
    remote_fn = ray.remote(_run_scenario)
    return remote_fn.remote(config_data, int(steps))
