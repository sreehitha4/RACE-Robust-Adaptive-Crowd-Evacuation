# 2D Crowd Evacuation & Normal Pedestrian Simulation System

An academic, discrete-event crowd simulator featuring **Normal Everyday Pedestrian Dynamics** and **Emergency Evacuation**, built with Python 3, Pygame, and Breadth-First Search (BFS) pathfinding.

---

## 1. Project Overview

The **2D Crowd Simulation System** models the spatial dynamics of human crowds in public architectural spaces.

The application features **two distinct behavioral modes**:
1. **Normal Crowd Flow (Default):** Everyday pedestrian circulation where people move between rooms, visit the central hall or library, walk down the concourse, and exit/enter through multiple gates with diverse walking speeds, continuous visual movement, and natural lane behavior.
2. **Emergency Evacuation Mode:** Triggered on demand (or with an alarm), commanding all occupants to immediately recalculate optimal egress paths to their nearest accessible emergency exit.

---

## 2. Key Enhancements & Features

### 2.1. Multiple Realistic Building Exits
The floor plan includes **4 distinct, clearly labeled exterior exits**:
1. **South Main Atrium Entrance / Exit:** Wide 4-cell grand portal on the southern boundary.
2. **North Plaza Exit:** Wide 2-cell exit at the north of the complex.
3. **West Wing Exit:** Dedicated side egress portal on the western perimeter.
4. **East Wing Exit:** Dedicated side egress portal on the eastern perimeter.

### 2.2. Natural Crowd Behavior & Smooth Walking
- **Continuous Visual Interpolation (Lerp):** Rather than rigid cell-by-cell jumping, agents glide across the floor with smooth sub-pixel continuous walking animations at 60 FPS.
- **Heterogeneous Walking Speeds:** Agents move with natural speed variations (strollers vs. brisk walkers).
- **Continuous Circulation in Normal Mode:** When an agent reaches a room destination or exterior portal in Normal Mode, they do not disappear; they select a new natural destination (e.g., crossing to another wing or concourse), simulating a continuous living environment.
- **Dynamic Egress Trigger:** Switch seamlessly between Normal Pedestrian Flow and Emergency Evacuation with one click or keypress (`[M]`).

---

## 3. Technology Stack

| Component | Technology | Rationale |
|---|---|---|
| **Language** | Python 3.11 / 3.13 | High readability, robust standard libraries, strong typing support. |
| **Simulation Environment** | Custom 2D Grid (`environment/grid.py`) | Discrete spatial modeling without heavy physics engine overhead. |
| **Pathfinding** | Breadth-First Search (`algorithms/pathfinding.py`) | Unweighted shortest-path guarantee ($O(V + E)$ optimality). |
| **Visualization & UI** | Pygame 2.6.1 | Lightweight, cross-platform 2D graphics and interactive event handling. |
| **Arbitration & Mechanics** | Rule-Based Discrete Movement | Deterministic reservation, swap prevention, and starvation avoidance. |
| **Testing** | Pytest 9.2.0 | Automated unit and integration testing (36 tests). |
| **Version Control** | Git | Standard source versioning. |

---

## 4. System Architecture & Folder Structure

```text
crowd-evacuation-simulation/
├── main.py                     # Entry point, 60 FPS visual interpolation, mode switcher, event loop
├── environment/
│   ├── grid.py                 # Discrete 2D spatial grid, boundaries, cell types (FLOOR, WALL, EXIT)
│   └── building.py             # 4 distinct exits, Room A, Room B, Room C, Main Concourse Corridor
├── agents/
│   ├── agent.py                # Agent entity, continuous visual lerp, speed factors, state machine
│   └── manager.py              # Spawning, collision-free placement, reproducible seeds, population queries
├── algorithms/
│   └── pathfinding.py          # Single-Source Queue BFS & Multi-Source Reverse BFS Distance Field
├── simulation/
│   ├── engine.py               # Dual-Mode orchestrator (NORMAL_FLOW vs EVACUATION), dynamic rerouting
│   └── movement.py             # Conflict resolution: single occupancy, swap prevention, priority
├── visualization/
│   ├── renderer.py             # Pygame graphics: 4 exit banners, smooth walking agents, room titles
│   └── dashboard.py            # Side-panel telemetry, live metrics, mode badges, interactive buttons
├── evaluation/
│   └── metrics.py              # Metrics: active crowd, evacuation %, tick timings, congestion wait delays
├── tests/
│   ├── test_building.py        # 12 tests: grid boundaries, walls, doorways, exit flood-fill reachability
│   ├── test_agents.py          # 6 tests: state transitions, placement, occupancy tracking
│   ├── test_pathfinding.py     # 9 tests: open grids, obstacles, mazes, multi-exit, unreachable targets
│   └── test_simulation.py      # 9 tests: normal flow, mode switching, contention, swap prevention, full run
├── requirements.txt            # Pinned dependencies
├── .gitignore                  # Git ignore rules
└── README.md                   # Complete documentation
```

---

## 5. Installation Instructions (Windows 11)

### Step 1: Open PowerShell
```powershell
cd "c:\Users\DELL\OneDrive\Desktop\capstone project"
```

### Step 2: Activate the Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```

*(If PowerShell displays an execution policy warning, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` once).*

### Step 3: Launch the Application
```powershell
python main.py
```

---

## 6. Controls & Interactive Demonstration

| Control | Action | Evaluation Demonstration Value |
|---|---|---|
| **[Start] / `SPACE`** | Starts or pauses simulation | Watch people smoothly walk through corridors and rooms. |
| **[Mode Switcher] / `M`** | **Toggle Normal Flow / Evacuation** | **Key Feature:** Toggle between everyday pedestrian movement and an emergency evacuation alarm. |
| **[Resume]** | Resumes from a paused state | Inspect dense doorway queues and lane dynamics. |
| **[Reset] / `R`** | Restores initial positions | Restores all agents back to their original starting locations. |
| **[New Seed] / `N`** | Respawns crowd with a new seed | Demonstrates that the simulation works for arbitrary crowd distributions. |
| **[Speed] / `S`** | Cycles speed (1.0x $\rightarrow$ 2.0x $\rightarrow$ 4.0x $\rightarrow$ 0.5x) | Examine bottlenecks in slow motion or fast-forward. |
| **[Block West Exit] / `B`** | **Dynamic Exit Blockage** | Block the West Exit and watch active agents dynamically re-route to the South or North portals in real time! |

---

## 7. Automated Test Suite (36 Tests)

Run the full automated test suite:
```powershell
pytest -v
```

All 36 tests pass with 100% success rate, verifying:
- 4-exit flood-fill reachability.
- Multi-mode engine execution (`NORMAL_FLOW` and `EVACUATION`).
- Collision avoidance and head-on swap prevention.
- BFS shortest-path optimality.
