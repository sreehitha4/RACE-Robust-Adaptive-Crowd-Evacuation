# RACE: Robust & Adaptive Crowd Evacuation Simulation

**Research and implementation of robust continuous crowd evacuation and dynamic exit balancing in unseen architectural environments.**

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Pygame](https://img.shields.io/badge/Pygame-2.6.1-green.svg)](https://www.pygame.org/)
[![Tests](https://img.shields.io/badge/Tests-45%20Passing-brightgreen.svg)](tests/)
[![Milestone](https://img.shields.io/badge/Milestone-Review%202-orange.svg)](Review%202/)

---

## 📌 Repository Overview & Review 2 Milestone

This repository contains the complete implementation, benchmarks, and deliverables for the **RACE (Robust & Adaptive Crowd Evacuation)** project.

📁 **All Review 2 source code, assets, test fixtures, and comprehensive academic documentation are packaged inside the [`Review 2/`](Review%202/) directory.**

### Key Engineering Features
- **Helbing's Social Force Model (SFM):** Continuous 2D vector dynamics (desired drive, interpersonal repulsion, boundary wall friction, and social group cohesion).
- **Congestion-Aware Dynamic Exit Balancing:** Trailing occupants actively detect doorway bottleneck queues and dynamically re-route to alternative exits.
- **Realistic Architectural Obstacles:** Information Kiosks, Cedar Benches, Botanical Planters, and Work Desks with physical collision boundaries.
- **Real-Time Exit Queue Badges:** Real-time doorway status pills (`[Q:0 CLEAR]`, `[Q:1 MODERATE]`, `[Q:X JAMMED!]`).
- **Visual Diverter Badges:** Glowing golden halos and `⚡ DIVERTER` indicators over agents who dynamically route around bottleneck queues.
- **1-Click Dynamic Balancing Benchmark (Scenario 5):** Instant demonstration of 20 clustered occupants detecting a jammed doorway and dynamically splitting across open exits (Hotkey `B`).
- **Multiple Unseen Floor Plans:** Campus Complex, Corporate Office Suites, Airport Transit Terminal, and Procedural Unseen Layouts.
- **Breadth-First Search (BFS):** Multi-source potential field global navigation guaranteeing shortest-path optimality.
- **Interactive Mouse Toolkit:** Inspect occupant dossier, drop dynamic fire hazards, and spawn pedestrians on the fly.
- **Real-Time Live Egress Curve Chart:** Plots cumulative evacuated population vs. time directly on the HUD.
- **Dynamic Density Heatmap:** Real-time translucent overlay highlighting bottleneck pressure.

---

## 1. Multiple Architectural Floor Plans & Realistic Obstacles

The system supports multiple distinct architectural complexes:

1. **University Student Center & Concourse (Campus Complex):**
   - 3 large wings (Lecture Hall, Central Atrium, Library) with architectural pillars and 4 cardinal exits.
2. **Corporate Office & Research Suites:**
   - Central horizontal spine hallway, 6 partitioned executive & team suites, and 3 dedicated fire exit stairwells.
3. **Airport Transit Terminal:**
   - Check-in concourse, narrow security screening choke point (testing severe bottleneck queuing), duty-free islands, and departure gates.
4. **Procedural Unseen Layout Generator:**
   - Procedural algorithmic room partitions proving that the BFS pathfinding and continuous physics operate robustly on arbitrary unseen floor plans.

### Architectural Obstacles Rendered in Each Building:
- **`[INFO]` Information Kiosk:** Teak/mahogany reception counters in high-traffic concourse intersections.
- **`[|||]` Cedar Seating Benches:** Real slat benches providing realistic corridor obstacles.
- **`[🌿]` Botanical Planters:** Lush green foliage planter boxes flanking main pedestrian thoroughfares.
- **`[💻]` Lecture & Workstation Desks:** Functional student desk pods and office cubicles with computer monitors.

*Cycle between floor plans at any time by pressing **`[L]`** or clicking **`[🏢 Cycle Map]`** on the dashboard.*

---

## 2. Congestion-Aware Dynamic Exit Balancing

In emergency situations, naive agents stubbornly pile into the closest exit, causing deadly crushing bottlenecks while alternative exits sit empty.

This simulator implements **Queue-Aware Dynamic Egress Balancing**:
- For each exit portal $E_k$, the engine tracks the active queue size $Q(E_k)$ within its bottleneck catchment zone.
- Trailing agents continually evaluate their effective travel cost:
  $$\text{Cost}(E_k) = \text{Distance}(P_i, E_k) + \alpha \times Q(E_k)$$
- If an alternative exit portal $E_{\text{alt}}$ offers a significantly faster evacuation time (accounting for walking distance plus doorway queue delay), trailing agents dynamically divert:
  *"The current exit is jammed! It is faster to walk an extra few meters to the open exit!"*
- The agent recalculates its BFS path to the alternative exit, updates its trajectory, and visibly displays a golden glowing ring and **`⚡ DIVERTER`** badge.
- Live exit banners display real-time statuses: `[Q:0 CLEAR]` (green), `[Q:1 MODERATE]` (amber), and `[Q:2+ JAMMED!]` (crimson).
- **1-Click Demo:** Press **`[B]`** or click **`[⚖️ Scenario 5: Demo Balancing]`** to launch a live showcase where 20 agents cluster at the West Exit and trailing occupants visibly divert to the South and North exits!

---

## 3. Technology Stack

| Component | Technology | Description |
|---|---|---|
| **Language** | Python 3.11 / 3.13 | High performance, standard math & collections. |
| **Global Pathfinding** | Multi-Source BFS (`algorithms/pathfinding.py`) | Unweighted shortest path calculation. |
| **Continuous Physics** | Helbing's Social Force Model (`simulation/physics.py`) | Vector velocity, social repulsion, wall repulsion, group cohesion. |
| **Exit Balancing** | Dynamic Congestion Heuristic (`simulation/engine.py`) | Queue-aware exit diversion and real-time portal monitoring. |
| **Visualization & HUD** | Pygame 2.6.1 (`visualization/`) | 60 FPS sub-pixel continuous rendering, live S-curve graph, dossier HUD. |
| **Testing** | Pytest 9.2.0 (`tests/`) | 45 automated unit tests covering physics, routing, floor plans, obstacles, and balancing. |

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
| **Demo Dynamic Balancing** | `B` / Button | **1-click benchmark:** 20 occupants queue up at West Exit and trailing crowd visibly diverts! |
| **Start / Pause** | `SPACE` | Starts, pauses, or resumes the simulation. |
| **Cycle Floor Plans** | `L` / Button | Switch between Campus, Corporate Office, Airport Terminal, and Procedural plans. |
| **Toggle Exit Balancing** | `C` / Button | Toggles Congestion-Aware Rerouting on/off to compare standard vs. balanced egress. |
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

## 6. Automated Testing (45 Tests)

Run the full automated test suite:
```powershell
pytest -v
```
All 45 tests verify:
- BFS optimal pathfinding on all floor plans.
- Helbing continuous social force physics & wall repulsion.
- Architectural obstacle collision and placement (Kiosk, Bench, Planter, Desk).
- Dynamic congestion queue detection and real-time agent rerouting.
