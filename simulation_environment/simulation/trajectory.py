import numpy as np

class TrajectoryManager:
    """Maintains per-agent 8x2 histories sampled at the configured cadence."""
    def __init__(self, sample_interval_seconds=0.4):
        self.sample_interval_seconds = float(sample_interval_seconds)
        self._last_sample = {}

    def sample(self, agent, simulation_time, force=False):
        last = self._last_sample.get(agent.id)
        if force or last is None or simulation_time - last >= self.sample_interval_seconds - 1e-9:
            agent.record_position()
            self._last_sample[agent.id] = simulation_time
            return True
        return False

    @staticmethod
    def model_input(agent):
        if len(agent.trajectory_history) != 8:
            return None
        arr = np.asarray(agent.trajectory_history, dtype=np.float32)
        if arr.shape != (8, 2) or not np.isfinite(arr).all():
            return None
        return arr
