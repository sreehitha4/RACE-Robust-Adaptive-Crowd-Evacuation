# 2D Continuous Crowd Simulator — Social Force Model & BFS

An advanced, academic crowd evacuation and pedestrian simulation system featuring:
- **Helbing's Social Force Model (SFM)** continuous 2D vector dynamics.
- **Congestion-Aware Dynamic Exit Balancing:** detects bottleneck queues at congested doors and dynamically reroutes trailing crowds to faster open exits!
- **Multiple Unseen Floor Plans:** Campus Complex, Corporate Office Suites, Airport Transit Terminal, and Procedural Unseen Layouts.
- **Breadth-First Search (BFS):** Multi-source potential field global navigation guaranteeing shortest-path optimality.
- **Interactive Mouse Toolkit:** Inspect occupant dossier, drop dynamic fire hazards, and spawn pedestrians on the fly.
- **Real-Time Live Egress Curve Chart:** Plots cumulative evacuated population vs. time directly on the HUD.
- **Dynamic Density Heatmap:** Real-time translucent overlay highlighting bottleneck pressure.

---

## 1. Multiple Architectural Floor Plans

The system supports multiple distinct architectural complexes:

1. **University Student Center & Concourse (Campus Complex):**
   - 3 large wings (Lecture Hall, Central Atrium, Library) with architectural pillars and 4 cardinal exits.
2. **Corporate Office & Research Suites:**
   - Central horizontal spine hallway, 6 partitioned executive & team suites, and 3 dedicated fire exit stairwells.
3. **Airport Transit Terminal:**
   - Check-in concourse, narrow security screening choke point (testing severe bottleneck queuing), duty-free islands, and departure gates.
4. **Procedural Unseen Layout Generator:**
   - Procedural algorithmic room partitions proving that the BFS pathfinding and continuous physics operate robustly on arbitrary unseen floor plans.

*Cycle between floor plans at any time by pressing **`[L]`** or clicking **`[🏢 Cycle Map]`** on the dashboard.*

---

## 2. Congestion-Aware Dynamic Exit Balancing

In emergency situations, naive agents stubbornly pile into the closest exit, causing deadly crushing bottlenecks while alternative exits sit empty.

This simulator implements **Queuing-Aware Dynamic Egress Balancing**:
- For each exit portal $E_k$, the engine tracks the active queue size $Q(E_k)$ within its bottleneck catchment zone.
- Trailing agents continually evaluate their effective travel cost:
  $$\text{Cost}(E_k) = \text{Distance}(P_i, E_k) + \alpha \times Q(E_k)$$
- If an alternative exit portal $E_{\text{alt}}$ offers a significantly faster evacuation time (accounting for walking distance plus queue delay), trailing agents dynamically divert:
  *"The current exit is jammed! It is faster to walk an extra few meters to the open exit!"*
- The agent recalculates its BFS path to the alternative exit, updates its trajectory, and flags its status as `[REROUTED AROUND QUEUE]`.
- Toggle on/off with **`[C]`** or the **`[⚖️ Balancing: ON/OFF]`** dashboard button to demonstrate the performance difference to evaluators.

---

## 3. Technology Stack

| Component | Technology | Description |
|---|---|---|
| **Language** | Python 3.11 / 3.13 | High performance, standard math & collections. |
| **Global Pathfinding** | Multi-Source BFS (`algorithms/pathfinding.py`) | Unweighted shortest path calculation. |
| **Continuous Physics** | Helbing's Social Force Model (`simulation/physics.py`) | Vector velocity, social repulsion, wall repulsion, group cohesion. |
| **Exit Balancing** | Dynamic Congestion Heuristic (`simulation/engine.py`) | Queue-aware exit diversion. |
| **Visualization & HUD** | Pygame 2.6.1 (`visualization/`) | 60 FPS sub-pixel continuous rendering, live S-curve graph, dossier HUD. |
| **Testing** | Pytest 9.2.0 (`tests/`) | 43 automated unit tests covering physics, routing, floor plans, and balancing. |

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

## 5. Controls & Keyboard Shortcuts

| Feature | Key / Control | What Happens |
|---|:---:|---|
| **Start / Pause** | `SPACE` | Starts, pauses, or resumes the simulation. |
| **Cycle Floor Plans** | `L` / Button | **New:** Switch between Campus, Corporate Office, Airport Terminal, and Procedural plans. |
| **Toggle Exit Balancing** | `C` / Button | **New:** Toggles Congestion-Aware Rerouting (watch crowds split to avoid jammed doors!). |
| **Inspect Person** | `I` / Left-Click | Click any person to see their dossier, speed, stress level, and path ribbon. |
| **Drop Fire Hazard** | `F` / Left-Click | Click to drop a fire. Watch people steer around it! Right-click to extinguish. |
| **Spawn Person** | `P` / Left-Click | Click to spawn a new pedestrian anywhere on the floor. |
| **Panic Level** | `1`, `2`, `3` | Switch between Calm ($1.2\text{ m/s}$), Alert ($1.8\text{ m/s}$), and Panic ($2.6\text{ m/s}$). |
| **Density Heatmap** | `H` | Toggle dynamic crowd density heatmap overlay. |
| **Mode Switcher** | `M` | Switch between Everyday Circulation and Emergency Evacuation. |
| **Reset** | `R` | Reset crowd to initial starting condition. |
| **New Seed** | `N` | Respawn crowd with new names and companion pairings. |
| **Cycle Speed** | `S` | Adjusts simulation speed ($1.0\times \rightarrow 2.0\times \rightarrow 4.0\times \rightarrow 0.5\times$). |

---

## 6. Automated Testing (43 Tests)

Run the full automated test suite:
```powershell
pytest -v
```

```text
============================= 43 passed in 0.66s ==============================
```
