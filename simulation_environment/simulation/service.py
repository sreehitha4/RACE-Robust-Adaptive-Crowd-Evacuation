"""Small integration facade for the FastAPI/WebSocket owner."""
from .export import StateExporter

class SimulationService:
    def __init__(self, simulation):
        self.simulation = simulation

    def start(self):
        self.simulation.status = "running"
        return self.state()

    def pause(self):
        if self.simulation.status == "running":
            self.simulation.status = "paused"
        return self.state()

    def advance(self, steps=1):
        if self.simulation.status == "paused":
            return self.state()
        return self.simulation.step(steps)

    def reset(self):
        return self.simulation.reset()

    def state(self):
        return StateExporter.to_dict(self.simulation)
