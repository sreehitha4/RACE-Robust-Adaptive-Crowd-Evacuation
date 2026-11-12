import argparse, json
from pathlib import Path
from .config import SimulationConfig
from .simulation import CrowdSimulation
from .export import StateExporter

def main():
    parser = argparse.ArgumentParser(description="Run the RACE crowd simulation")
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--seconds", type=float, default=30.0)
    parser.add_argument("--output", default="outputs/latest_state.json")
    parser.add_argument("--no-ml", action="store_true")
    args = parser.parse_args()
    config = SimulationConfig.from_json(args.config) if Path(args.config).exists() else SimulationConfig()
    if args.no_ml: config.use_ml = False
    sim = CrowdSimulation(config)
    final = sim.run(args.seconds)
    StateExporter.write_json(sim, args.output)
    print(json.dumps({"status": final["status"], "time": final["simulation_time"],
                      "evacuated": final["evacuated_count"], "remaining": final["remaining_agents"],
                      "ml_enabled": final["ml_enabled"], "output": args.output}, indent=2))

if __name__ == "__main__": main()
