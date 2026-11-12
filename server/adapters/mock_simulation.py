"""Temporary deterministic adapter for frontend/backend integration testing.

This is NOT the team's final crowd simulation. Replace it with an adapter around
Keerthana's engine once that implementation is available.
"""

from server.schemas import AgentMessage, EnvironmentMessage, ExitSchema, FrameMessage


class MockSimulationAdapter:
    def __init__(self, population: int = 24):
        self.population = population
        self.reset()

    def environment(self) -> EnvironmentMessage:
        return EnvironmentMessage(
            width=40.0,
            height=24.0,
            walls=[[(0.0, 0.0), (40.0, 0.0), (40.0, 24.0),
                    (0.0, 24.0), (0.0, 0.0)]],
            obstacles=[],
            exits=[
                ExitSchema(
                    id="E1",
                    polygon=[(39.4, 10.0), (40.0, 10.0),
                             (40.0, 14.0), (39.4, 14.0)],
                )
            ],
        )

    def reset(self) -> None:
        self.simulation_time = 0.0
        self.evacuated = 0
        self._agents: list[dict] = []
        for index in range(self.population):
            col, row = index % 6, index // 6
            self._agents.append({
                "id": index + 1,
                "x": 3.0 + col * 1.6,
                "y": 5.0 + row * 3.0,
                "vx": 0.8,
                "vy": 0.0,
                "state": "walking",
            })

    def step(self, dt: float) -> None:
        self.simulation_time += dt
        remaining = []
        for agent in self._agents:
            # Placeholder only: a simple demonstration drift towards the right exit.
            dy = 12.0 - agent["y"]
            vy = max(-0.45, min(0.45, dy * 0.12))
            vx = 0.8
            agent["vx"], agent["vy"] = vx, vy
            agent["x"] += vx * dt
            agent["y"] += vy * dt
            if agent["x"] >= 39.4:
                self.evacuated += 1
            else:
                remaining.append(agent)
        self._agents = remaining

    def frame(self) -> FrameMessage:
        return FrameMessage(
            simulation_time=self.simulation_time,
            total_agents=self.population,
            evacuated=self.evacuated,
            density=len(self._agents) / (40.0 * 24.0),
            prediction_model="mock-constant-velocity",
            agents=[
                AgentMessage(
                    id=a["id"], x=a["x"], y=a["y"],
                    vx=a["vx"], vy=a["vy"], state=a["state"],
                )
                for a in self._agents
            ],
        )
