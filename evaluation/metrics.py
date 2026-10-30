"""Simulation evaluation and quantitative performance metrics.

Calculates crowd evacuation statistics, percentage completed,
congestion wait delays, and individual/aggregate evacuation timings.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from agents.agent import Agent, AgentState
from agents.manager import AgentManager


@dataclass
class EvacuationSummary:
    """Summary snapshot of evacuation performance metrics."""
    total_agents: int
    evacuated_agents: int
    active_agents: int
    stuck_agents: int
    remaining_agents: int
    evacuation_percentage: float
    total_ticks: int
    avg_evacuation_ticks: float
    min_evacuation_ticks: Optional[int]
    max_evacuation_ticks: Optional[int]
    total_wait_ticks: int
    agent_timings: Dict[int, Optional[int]] = field(default_factory=dict)


class MetricsCollector:
    """Collects and computes real-time and terminal evacuation statistics."""

    def __init__(self, manager: AgentManager) -> None:
        self.manager: AgentManager = manager

    def get_summary(self, current_tick: int) -> EvacuationSummary:
        """Compute comprehensive metrics for the current simulation state."""
        agents = self.manager.agents
        total = len(agents)

        evacuated = [a for a in agents if a.is_evacuated]
        active = [a for a in agents if a.is_active]
        stuck = [a for a in agents if a.is_stuck]

        evacuated_count = len(evacuated)
        active_count = len(active)
        stuck_count = len(stuck)
        remaining_count = active_count + stuck_count

        # Evacuation percentage formula with zero-division safeguard
        if total > 0:
            pct = (evacuated_count / total) * 100.0
        else:
            pct = 0.0

        # Timing analysis
        timings: Dict[int, Optional[int]] = {a.agent_id: a.evacuation_tick for a in agents}
        evac_times = [a.evacuation_tick for a in evacuated if a.evacuation_tick is not None]

        if evac_times:
            avg_time = sum(evac_times) / len(evac_times)
            min_time = min(evac_times)
            max_time = max(evac_times)
        else:
            avg_time = 0.0
            min_time = None
            max_time = None

        total_waits = sum(a.wait_ticks for a in agents)

        return EvacuationSummary(
            total_agents=total,
            evacuated_agents=evacuated_count,
            active_agents=active_count,
            stuck_agents=stuck_count,
            remaining_agents=remaining_count,
            evacuation_percentage=round(pct, 2),
            total_ticks=current_tick,
            avg_evacuation_ticks=round(avg_time, 2),
            min_evacuation_ticks=min_time,
            max_evacuation_ticks=max_time,
            total_wait_ticks=total_waits,
            agent_timings=timings
        )
