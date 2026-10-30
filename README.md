# 2D Continuous Crowd Simulator — Social Force Model & BFS

A modern, continuous-physics crowd simulation system modeling both **Everyday Pedestrian Dynamics** and **Emergency Evacuation** in an expansive campus complex using Python 3, Pygame, Helbing's Social Force Model (SFM), and Breadth-First Search (BFS) pathfinding.

---

## 1. Project Overview & Architecture

This simulation bridges **discrete global graph pathfinding** with **continuous 2D physical and social dynamics**:

1. **Global Macro-Navigation (BFS Potential Field):**
   - The unweighted building grid computes an exact, multi-source shortest-path gradient toward exits or room targets in $O(V + E)$ time.
2. **Local Micro-Physics (Helbing's Social Force Model):**
   - Individuals move with continuous floating-point coordinates and velocities.
   - Realistic personal space comfort zones (psychological social repulsion).
   - Solid wall and obstacle avoidance for smooth corner gliding.
   - Physical body contact elasticity and tangential friction when crowds press against bottlenecks.
3. **Social Group Cohesion:**
   - Individuals can belong to pairs or friend groups, exerting mutual attraction forces to stay together while navigating.
4. **Interactive Simulation Tools:**
   - **Inspect Person (`[I]`):** Click on any individual to open their real-time dossier (Name, Stress level, Speed, Companion, Target).
   - **Drop Fire / Hazard (`[F]`):** Click anywhere on the floor to place an emergency flame hazard. Watch occupants dynamically avoid the hazard and re-route in real time! (Right-click removes hazard).
   - **Spawn Person (`[P]`):** Click to instantly spawn a new pedestrian anywhere on the floor.
   - **Panic Modulator (`[1]`, `[2]`, `[3]`):** Toggle crowd mood between Calm ($1.2\text{ m/s}$), Alert ($1.8\text{ m/s}$), and Panic ($2.6\text{ m/s}$).
   - **Real-Time Density Heatmap (`[H]`):** Semi-transparent crowd density overlay highlighting congestion choke points.

---

## 2. Architectural Floor Plan

The campus complex ($34 \times 22$ grid) features:
- **West Wing (Lecture Theater & Classrooms):** High-density seating area with dedicated concourse doorway.
- **Central Atrium & Food Court:** Expansive multi-purpose space with architectural load-bearing pillars and seating clusters.
- **East Wing (Library & Research Study):** Quiet study zone.
- **Main Concourse Corridor:** Central thoroughfare connecting all wings and portals.
- **Four Distinct Cardinal Exits:**
  1. **South Grand Entrance / Egress:** 4-cell wide portal.
  2. **North Plaza Exit:** 2-cell wide exterior portal.
  3. **West Wing Courtyard Exit:** Dedicated western side portal.
  4. **East Wing Garden Exit:** Dedicated eastern side portal.

---

## 3. Technology Stack

| Component | Technology | Description |
|---|---|---|
| **Language** | Python 3.11 / 3.13 | High readability, robust standard math and collections. |
| **Global Pathfinding** | Multi-Source BFS (`algorithms/pathfinding.py`) | Unweighted shortest path calculation. |
| **Continuous Physics** | Helbing's Social Force Model (`simulation/physics.py`) | Vector velocity, social repulsion, wall repulsion, group cohesion. |
| **Visualization & HUD** | Pygame 2.6.1 (`visualization/`) | 60 FPS sub-pixel continuous rendering, dashboard, inspector HUD. |
| **Testing** | Pytest 9.2.0 (`tests/`) | 38 automated unit tests covering physics, routing, and groups. |

---

## 4. Installation & Execution (Windows 11)

### Step 1: Open PowerShell
```powershell
cd "c:\Users\DELL\OneDrive\Desktop\capstone project"
```

### Step 2: Activate the Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```

### Step 3: Run the Application
```powershell
python main.py
```

---

## 5. Controls & Interactive Keyboard Shortcuts

| Control | Key | Action |
|---|:---:|---|
| **Start / Pause** | `SPACE` | Starts, pauses, or resumes the continuous simulation. |
| **Inspect Tool** | `I` / Button | Left-click on any person to view their dossier and projected path. |
| **Drop Fire Hazard** | `F` / Button | Left-click on the floor to place a fire. Right-click to remove. |
| **Spawn Person** | `P` / Button | Left-click on the floor to spawn a new pedestrian. |
| **Calm / Alert / Panic** | `1`, `2`, `3` | Adjusts crowd walking speed, aggression, and stress levels. |
| **Toggle Heatmap** | `H` | Toggles dynamic crowd congestion density heatmap overlay. |
| **Toggle Mode** | `M` | Switches between Normal Everyday Circulation and Emergency Evacuation. |
| **Reset** | `R` | Restores the simulation to original starting conditions. |
| **New Seed** | `N` | Respawns the crowd with new random positions, names, and companion pairings. |
| **Cycle Speed** | `S` | Adjusts simulation speed ($1.0\times \rightarrow 2.0\times \rightarrow 4.0\times \rightarrow 0.5\times$). |

---

## 6. Automated Testing (38 Tests)

Execute the full automated test suite:
```powershell
pytest -v
```

```text
============================= 38 passed in 0.35s ==============================
```
