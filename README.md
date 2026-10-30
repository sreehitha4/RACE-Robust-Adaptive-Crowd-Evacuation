# 2D Crowd Evacuation Simulation System

An academic, discrete-event crowd evacuation simulation built using Python 3, Pygame, and Breadth-First Search (BFS) pathfinding.

---

## 1. Project Overview

The **2D Crowd Evacuation Simulation System** models the emergency egress dynamics of human crowds in indoor environments. Simulating evacuation during emergencies (e.g., fires, natural disasters, or structural hazards) is crucial for civil engineering, architectural safety compliance, and crisis response planning.

This project implements a fully functioning, grid-based multi-agent simulator with real-time Pygame visualization, deterministic collision arbitration, dynamic environmental rerouting, and quantitative performance evaluation.

---

## 2. Problem Statement

During emergency building evacuations:
- Occupants must identify and navigate towards available emergency exits.
- Physical bottlenecks (doorways, corridor intersections) lead to high local density, contention, and queue delays.
- Occupants cannot pass through solid architectural obstacles (walls, pillars) or occupy the same physical space simultaneously.
- If an emergency exit becomes inaccessible (e.g., fire blockage), occupants must dynamically detect the hazard and recalculate alternative paths to surviving exits.

Simulating these dynamics helps evaluate architectural designs, measure egress efficiency, identify high-congestion choke points, and determine minimum evacuation completion times.

---

## 3. Objectives

1. Model a multi-room building layout with rooms, corridors, doorways, and multiple exits on a discrete 2D grid.
2. Implement Breadth-First Search (BFS) to compute mathematically optimal shortest paths to reachable exits.
3. Develop a discrete movement arbitration engine enforcing single-cell occupancy, swap-collision prevention, and starvation-free priority scheduling.
4. Provide a real-time graphical interface using Pygame with live telemetry, progress tracking, and interactive controls (Start, Pause, Resume, Reset, Speed control, Dynamic Exit Blockage).
5. Calculate objective quantitative evacuation metrics (evacuation percentage, individual and average evacuation times, congestion wait-ticks).
6. Provide complete test coverage using `pytest`.

---

## 4. Technology Stack

| Component | Technology | Rationale |
|---|---|---|
| **Language** | Python 3.11 / 3.13 | High readability, robust standard libraries, strong typing support. |
| **Simulation Environment** | Custom 2D Grid (`environment/grid.py`) | Discrete spatial modeling without heavy physics engine overhead. |
| **Pathfinding** | Breadth-First Search (`algorithms/pathfinding.py`) | Unweighted shortest-path guarantee ($O(V + E)$ optimality). |
| **Visualization & UI** | Pygame 2.6.1 | Lightweight, cross-platform 2D graphics and interactive event handling. |
| **Arbitration & Mechanics** | Rule-Based Discrete Movement | Deterministic reservation, swap prevention, and starvation avoidance. |
| **Testing** | Pytest 9.2.0 | Automated unit and integration testing. |
| **Version Control** | Git | Standard source versioning. |

---

## 5. System Architecture & Folder Structure

The project strictly decouples **simulation logic and algorithms** from **graphical rendering**, enabling independent automated testing without opening a graphical window.

```text
crowd-evacuation-simulation/
|
|-- main.py                     # Application entry point, Pygame event loop, timing coordinator
|
|-- environment/                # Spatial environment representation
|   |-- __init__.py
|   |-- grid.py                 # 2D discrete grid, cell types, coordinate boundaries, neighbor lookups
|   |-- building.py             # Architectural floor plan: rooms, corridors, doorways, emergency exits
|
|-- agents/                     # Crowd entities and population management
|   |-- __init__.py
|   |-- agent.py                # Agent dataclass, state machine (ACTIVE, EVACUATED, STUCK), tracking
|   |-- manager.py              # Spawning, collision-free placement, reproducible seeds, population queries
|
|-- algorithms/                 # Pathfinding and graph algorithms
|   |-- __init__.py
|   |-- pathfinding.py          # Queue-based BFS and Multi-Source Reverse BFS Distance Field
|
|-- simulation/                 # Discrete-event simulation engine
|   |-- __init__.py
|   |-- engine.py               # Orchestrator: tick advancement, dynamic rerouting, lifecycle states
|   |-- movement.py             # Conflict resolution: single-cell occupancy, swap prevention, priority
|
|-- visualization/              # Graphical rendering & UI
|   |-- __init__.py
|   |-- renderer.py             # Pygame grid drawing, agent circles, room labels, exit styling
|   |-- dashboard.py            # Side-panel telemetry, live metrics, progress meters, interactive buttons
|
|-- evaluation/                 # Metrics & statistical analysis
|   |-- __init__.py
|   |-- metrics.py              # Real-time and terminal evacuation metrics computation
|
|-- tests/                      # Automated Pytest suite
|   |-- __init__.py
|   |-- test_building.py        # 12 tests: grid boundaries, walls, doorways, exit flood-fill reachability
|   |-- test_agents.py          # 6 tests: agent state transitions, placement, occupancy tracking
|   |-- test_pathfinding.py     # 9 tests: open grids, obstacles, mazes, multi-exit, unreachable targets
|   |-- test_simulation.py      # 7 tests: live movement, contention, swap prevention, full run, rerouting
|
|-- requirements.txt            # Pinned Python package dependencies
|-- .gitignore                  # Git ignore rules for venv, caches, and temp files
|-- README.md                   # Comprehensive project documentation
```

---

## 6. Mathematical & Algorithmic Concepts

### 6.1. Grid Representation
The building is modeled as a uniform 2D Cartesian grid of dimensions $W \times H$:
- Coordinate $(x, y)$ denotes the column $x \in [0, W-1]$ and row $y \in [0, H-1]$.
- Every cell $c(x, y)$ has a discrete type:
  $$\text{CellType} \in \{\text{FLOOR}=0, \text{WALL}=1, \text{EXIT}=2\}$$
- Movement is constrained to 4-connected orthogonal neighbors (von Neumann neighborhood):
  $$\mathcal{N}(x, y) = \{(x+1, y), (x-1, y), (x, y+1), (x, y-1)\} \cap \text{Walkable}$$

### 6.2. Multi-Source BFS Pathfinding
In an indoor building with multiple emergency exits $E = \{e_1, e_2, \dots, e_k\}$, running individual BFS for dozens of agents is redundant. Instead, we compute a **Multi-Source Reverse BFS Distance Field**:
1. Initialize a FIFO queue $Q$ containing all active exit coordinates at distance $d(e) = 0$.
2. Dequeue cell $u$, explore each unvisited walkable neighbor $v \in \mathcal{N}(u)$.
3. Assign distance $d(v) = d(u) + 1$, and set direction pointer $\text{next\_step}(v) = u$.
4. Enqueue $v$.

**Time Complexity:** $\mathcal{O}(V + E)$ where $V = W \times H$ and $E \le 4V$.

Every agent at coordinate $(x, y)$ can immediately retrieve:
- Its exact shortest distance to the nearest exit: $d(x, y)$.
- Its optimal step towards safety: $\text{next\_step}(x, y)$.

### 6.3. Movement Arbitration & Collision Prevention
At each discrete simulation tick $t$:
1. **Intended Moves:** Each active agent $i$ determines its desired target $T_i = \text{next\_step}(P_i)$.
2. **Head-on Swap Prevention:** If Agent $A$ intends to move to $P_B$ and Agent $B$ intends to move to $P_A$, a physical boundary collision would occur. The conflict resolver detects this condition and requires the lower-priority agent to yield.
3. **Single Cell Occupancy:** If multiple agents target the same cell $T$, only one agent is granted the reservation. The winner is selected based on:
   - Primary: Accumulated wait ticks (highest wait ticks win to prevent starvation).
   - Secondary: Deterministic rotating offset $(i + t) \pmod N$ so no agent ID is permanently favored.
4. **Evacuation Drain:** When an agent steps onto an exit cell, it transitions to `EVACUATED` and frees its floor cell for trailing agents.

---

## 7. Installation Instructions (Windows 11)

### Prerequisites
- Python 3.11 or Python 3.13 installed with PATH enabled.
- Git for Windows.

### Step 1: Open PowerShell in the Project Directory
```powershell
cd "c:\Users\DELL\OneDrive\Desktop\capstone project"
```

### Step 2: Activate the Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```

*(Note: If PowerShell displays a script policy warning, enable script execution for the current user once:)*
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

---

## 8. Execution Instructions

Launch the complete interactive simulation:
```powershell
python main.py
```

### Graphical Interface Controls:
- **[Start] / [Spacebar]:** Start or pause the simulation.
- **[Resume]:** Resume a paused simulation.
- **[Reset] / [R]:** Reset all agents back to starting positions and restore original paths.
- **[New Seed] / [N]:** Respawn agents in randomly distributed new starting locations across rooms.
- **[Speed] / [S]:** Cycle simulation tick speed (1.0x $\rightarrow$ 2.0x $\rightarrow$ 4.0x $\rightarrow$ 0.5x).
- **[Block West Exit] / [B]:** Dynamically seal the West Exit with an emergency barrier, triggering immediate BFS path recalculation and live rerouting of all crowd agents to the East Exit!

---

## 9. Testing & Validation

The codebase includes an automated test suite verifying all architectural, algorithmic, physical, and metric components.

Run all unit tests with verbose output:
```powershell
pytest -v
```

### Test Suite Breakdown (34 Tests):
- `tests/test_building.py` (12 tests):
  - Validates grid boundaries, out-of-bounds safety, and cell type mutation.
  - Verifies architectural dimensions of Room A, Room B, Room C, and Main Corridor.
  - Runs a flood-fill algorithm verifying that 100% of walkable cells have reachable paths to emergency exits.
- `tests/test_agents.py` (6 tests):
  - Validates agent lifecycle state transitions (`ACTIVE`, `EVACUATED`, `STUCK`).
  - Verifies random agent placement: strictly floor cells, no walls, no exits, no duplicated starts.
- `tests/test_pathfinding.py` (9 tests):
  - Validates BFS shortest path on open grids, obstacle grids, and serpentine mazes.
  - Verifies multiple-exit selection, unreachable destination detection, and distance field equivalence.
- `tests/test_simulation.py` (7 tests):
  - Validates live movement to exits, destination contention resolution, head-on swap avoidance.
  - Runs full end-to-end evacuation to 100% completion.
  - Tests dynamic exit blockage and real-time agent rerouting.

---

## 10. Evaluation Metrics

The system continuously measures:
1. **Total Population ($N$):** Number of agents initialized.
2. **Active Agents:** Agents currently navigating towards exits.
3. **Evacuated Agents ($E$):** Agents that have safely reached an exit.
4. **Stuck Agents ($S$):** Agents with no accessible path to any open exit.
5. **Evacuation Percentage:**
   $$\text{Evacuation \%} = \left(\frac{E}{N}\right) \times 100\%$$
6. **Total Evacuation Time:** Discrete simulation ticks elapsed from simulation start to complete egress.
7. **Average Evacuation Time:** Mean number of simulation ticks required per evacuated agent:
   $$\bar{T} = \frac{1}{E} \sum_{i \in \text{Evacuated}} T_i$$
8. **Congestion Wait Ticks:** Cumulative number of ticks agents spent waiting in place due to cell occupancy contention.

---

## 11. Known Limitations & Future Enhancements

### Limitations
- **Discrete Grid Representation:** Movement occurs on discrete grid cells rather than continuous physical vectors (no social force model or velocity steering).
- **Homogeneous Movement Speed:** All agents step at uniform speed (1 cell per simulation tick) without age, physical disability, or fatigue differences.

### Future Enhancements
- **Heterogeneous Agent Speeds:** Adding agent demographic profiles (e.g., fast runners vs. slower mobility-assisted occupants).
- **Smoke & Hazard Propagation:** Simulating cellular automata smoke spread that dynamically restricts floor walkability and reduces agent visibility.
- **Panic & Herding Dynamics:** Introducing flocking/leader-follower behaviors where uninformed agents follow local crowds rather than knowing optimal exit routes.
