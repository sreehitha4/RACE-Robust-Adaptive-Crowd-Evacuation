"""Agent movement and discrete collision resolution system.

Ensures strict single-occupancy of grid cells, prevents simultaneous swaps,
and employs starvation-free priority scheduling.
"""

from typing import Dict, List, Optional, Set, Tuple
from environment.building import Building
from agents.agent import Agent, AgentState
from agents.manager import AgentManager


class MovementResolver:
    """Resolves discrete movement intentions while enforcing physical constraints:
      1. Single cell occupancy (no two agents on the same floor cell).
      2. No head-on position swaps (A -> B while B -> A in the same tick).
      3. No movement into walls or out-of-bounds.
      4. Starvation prevention: agents waiting longer receive higher arbitration priority.
      5. Safe evacuation: agents reaching an exit cell safely evacuate and free the cell.
    """

    def __init__(self, building: Building, manager: AgentManager) -> None:
        self.building: Building = building
        self.manager: AgentManager = manager

    def step(self, current_tick: int) -> int:
        """Execute one simulation tick of agent movement.

        Returns:
            Number of agents that successfully stepped into a new cell this tick.
        """
        active_agents = self.manager.active_agents
        if not active_agents:
            return 0

        # Sort agents by priority:
        # Highest wait_ticks first (starvation-prevention),
        # tie-break with rotating tick offset so no agent ID is permanently favored.
        active_agents.sort(
            key=lambda a: (a.wait_ticks, (a.agent_id + current_tick) % (len(active_agents) + 1)),
            reverse=True
        )

        grid = self.building.grid
        current_positions: Dict[int, Tuple[int, int]] = {
            a.agent_id: a.current_pos for a in active_agents
        }
        # Inverted mapping: pos -> agent_id currently there
        cell_occupant: Dict[Tuple[int, int], int] = {
            pos: aid for aid, pos in current_positions.items()
        }

        # 1. Gather proposed moves
        # target_pos -> list of agent_ids wanting to move there
        intents: Dict[int, Tuple[int, int]] = {}
        for agent in active_agents:
            target = agent.next_intended_cell
            if target is not None and grid.is_walkable(target[0], target[1]):
                intents[agent.agent_id] = target

        # 2. Track planned new positions for this tick
        # Pre-populate with agents who have no valid intended move (they stay put)
        resolved_new_positions: Dict[int, Tuple[int, int]] = {}
        # Track reserved floor cells (exits can absorb multiple evacuees)
        reserved_cells: Set[Tuple[int, int]] = set()

        # Identify agents who definitely cannot move (e.g. at end of path without exit)
        for agent in active_agents:
            if agent.agent_id not in intents:
                resolved_new_positions[agent.agent_id] = agent.current_pos
                reserved_cells.add(agent.current_pos)
                agent.record_wait()

        # 3. Arbitrate candidates iteratively
        remaining_candidates = [a for a in active_agents if a.agent_id in intents]
        moved_count = 0

        # Run resolution passes to handle chains of movement (e.g., A follows B as B moves)
        changed = True
        while changed and remaining_candidates:
            changed = False
            unresolved: List[Agent] = []

            for agent in remaining_candidates:
                aid = agent.agent_id
                target = intents[aid]
                cur_pos = agent.current_pos

                # Check head-on swap conflict:
                # If target currently holds agent B, and agent B intends to move to cur_pos
                occupant_b = cell_occupant.get(target)
                if (
                    occupant_b is not None
                    and occupant_b != aid
                    and intents.get(occupant_b) == cur_pos
                ):
                    # Head-on conflict! The lower priority agent must yield.
                    # Since active_agents is sorted by priority, if occupant_b is already resolved,
                    # aid cannot take target if occupant_b stayed.
                    if occupant_b in resolved_new_positions:
                        if resolved_new_positions[occupant_b] == target:
                            # Occupant B stayed, so aid cannot move here
                            continue

                # Can agent reserve target?
                # Target is available if it's an EXIT, OR it has not been reserved yet
                # AND either nobody is currently standing there or whoever was there has already moved away.
                is_exit_cell = grid.is_exit(target[0], target[1])
                is_reserved = target in reserved_cells

                if not is_reserved or is_exit_cell:
                    # Check if previous occupant has moved away
                    prior_occupant = cell_occupant.get(target)
                    prior_occupant_moved = (
                        prior_occupant is None
                        or prior_occupant == aid
                        or (
                            prior_occupant in resolved_new_positions
                            and resolved_new_positions[prior_occupant] != target
                        )
                    )

                    if prior_occupant_moved:
                        # Success! Reserve destination
                        resolved_new_positions[aid] = target
                        if not is_exit_cell:
                            reserved_cells.add(target)
                        # Free agent's old position from reserved if it was reserved
                        if cur_pos in reserved_cells:
                            reserved_cells.discard(cur_pos)

                        # Actually advance the agent
                        agent.advance_to(target)
                        agent.wait_ticks = 0  # reset waiting streak
                        moved_count += 1
                        changed = True

                        # Check if agent has reached an emergency exit
                        if is_exit_cell:
                            agent.mark_evacuated(current_tick)
                        continue

                # If we couldn't resolve in this pass, keep for next check
                unresolved.append(agent)

            remaining_candidates = unresolved

        # 4. Any agents remaining unresolved could not move: they must wait in place
        for agent in remaining_candidates:
            resolved_new_positions[agent.agent_id] = agent.current_pos
            reserved_cells.add(agent.current_pos)
            agent.record_wait()

        return moved_count
