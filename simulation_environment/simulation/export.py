import json
from pathlib import Path


class StateExporter:

    @staticmethod
    def to_dict(simulation):

        # Identify pedestrians who have not evacuated.
        active = [
            agent
            for agent in simulation.agents
            if agent.state != "evacuated"
        ]

        # Calculate room area.
        area = max(
            1e-9,
            simulation.environment.width
            * simulation.environment.height
        )

        # Get current evacuation statistics.
        stats = simulation.statistics.snapshot(
            simulation.time
        )

        # Export all pedestrian information.
        agents_data = []

        for agent in simulation.agents:

            agent_data = agent.to_dict()

            # Include navigation information for debugging.
            agent_data["navigation_path"] = [
                list(point)
                for point in agent.navigation_path
            ]

            agent_data["waypoint_index"] = (
                agent.waypoint_index
            )

            # Include evacuation timestamp.
            agent_data["evacuated_at"] = (
                agent.evacuated_at
            )

            agents_data.append(agent_data)

        return {
            "schema_version": "1.0",

            "coordinate_system": simulation.coordinate_system,

            "environment": simulation.environment.to_dict(),

            "agents": agents_data,

            "density": len(active) / area,

            "simulation_time": simulation.time,

            "evacuated_count": stats["evacuated_count"],

            "remaining_agents": stats["remaining_agents"],

            "statistics": stats,

            "status": simulation.status,

            "ml_enabled": simulation.ml.enabled
        }

    @classmethod
    def write_json(cls, simulation, path):

        path = Path(path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        path.write_text(
            json.dumps(
                cls.to_dict(simulation),
                indent=2
            ),
            encoding="utf-8"
        )

        return path