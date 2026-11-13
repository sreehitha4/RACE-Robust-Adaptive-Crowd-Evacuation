class EvacuationStatistics:
    def __init__(self, total_agents):
        self.total_agents = int(total_agents)
        self.evacuated_count = 0
        self.evacuation_times = []
        self._evacuated_agent_ids = set()

    def mark_evacuated(self, elapsed, agent_id=None):

        # Prevent duplicate evacuation counting when an ID is supplied.
        if agent_id is not None:
            if agent_id in self._evacuated_agent_ids:
                return False

            self._evacuated_agent_ids.add(agent_id)

        # Never allow the count to exceed total agents.
        if self.evacuated_count >= self.total_agents:
            return False

        self.evacuated_count += 1
        self.evacuation_times.append(float(elapsed))

        return True

    def snapshot(self, simulation_time):

        remaining = max(
            0,
            self.total_agents - self.evacuated_count
        )

        percentage = min(
            100.0,
            100.0 * self.evacuated_count / max(1, self.total_agents)
        )

        return {
            "total_agents": self.total_agents,
            "evacuated_count": self.evacuated_count,
            "remaining_agents": remaining,
            "evacuation_percentage": percentage,
            "simulation_time": float(simulation_time),
            "mean_evacuation_time": (
                sum(self.evacuation_times) / len(self.evacuation_times)
                if self.evacuation_times
                else None
            )
        }