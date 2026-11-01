# Review 2 Academic Project Report
## RACE: Robust & Adaptive Crowd Evacuation Simulation

---

### Project Metadata
- **Project Title:** RACE (Robust & Adaptive Crowd Evacuation)
- **Domain:** Continuous Multi-Agent Simulation, Computational Physics, Algorithm Design
- **Review Stage:** Review 2 Deliverables & Demonstration
- **Target Platform:** Windows 11 / Python 3.11+ / Pygame 2.6.1 / Pytest 9.2.0

---

## 1. Executive Summary & Review 2 Objectives

During **Review 2**, the objective was to elevate the simulation from a discrete grid mockup into an **architecturally realistic, continuous-space multi-agent simulation system**.

Key deliverables accomplished for Review 2:
1. **Continuous 2D Vector Physics:** Fully implemented Helbing's Social Force Model (SFM) with sub-pixel collision physics, wall repulsion, interpersonal compression forces, and social group cohesion.
2. **Multi-Source BFS Global Routing:** Guaranteed mathematically optimal shortest paths to multiple cardinal exits with $O(V + E)$ complexity.
3. **Generalization across Unseen Floor Plans:** Tested and verified the system across 4 distinct architectural environments (Campus Complex, Corporate Office Suites, Airport Transit Terminal, and an Algorithmic Procedural Generator).
4. **Congestion-Aware Dynamic Exit Balancing:** Implemented real-time doorway queue detection that autonomously reroutes trailing occupants to less congested exits when doorways become jammed.
5. **Realistic Architectural Obstacles:** Embedded 4 real architectural obstacles (Information Kiosks, Cedar Seating Benches, Botanical Planters, and Work Desks) with full physical collision boundaries.
6. **Interactive Visualization & Telemetry:** Built a 60 FPS graphical interface featuring a live S-Curve Evacuation chart, dynamic crowd density heatmap, live exit queue badges, and an interactive mouse toolkit (Inspect, Drop Fire, Spawn Pedestrian).
7. **Comprehensive QA Verification:** 45 automated unit tests covering all components with 100% pass rate.

---

## 2. Mathematical Models & Algorithmic Formulation

### 2.1 Helbing Social Force Model (SFM)
Each agent $i$ of mass $m_i$ navigates under continuous Newton-Euler vector acceleration:

$$m_i \frac{d\vec{v}_i}{dt} = \vec{f}_i^0 + \sum_{j \ne i} \vec{f}_{ij} + \sum_w \vec{f}_{iw} + \vec{f}_i^{\text{group}}$$

Where:
1. **Desired Driving Force ($\vec{f}_i^0$):**
   $$\vec{f}_i^0 = m_i \frac{v_i^0 \vec{e}_i^0 - \vec{v}_i}{\tau}$$
   Drives the agent towards their current BFS waypoint at their target speed $v_i^0$ with relaxation time $\tau \approx 0.5\text{ s}$.

2. **Interpersonal Repulsion Force ($\vec{f}_{ij}$):**
   $$\vec{f}_{ij} = A \exp\left(\frac{r_{ij} - d_{ij}}{B}\right) \vec{n}_{ij} + k g(r_{ij} - d_{ij}) \vec{n}_{ij}$$
   Prevents overlapping between agents ($A=2000\text{ N}$, $B=0.08\text{ m}$, $k=120000\text{ kg}\cdot\text{s}^{-2}$).

3. **Obstacle & Boundary Wall Repulsion ($\vec{f}_{iw}$):**
   $$\vec{f}_{iw} = A_w \exp\left(\frac{r_i - d_{iw}}{B_w}\right) \vec{n}_{iw}$$
   Smoothly repels agents away from exterior walls, interior room dividers, pillars, and architectural obstacles.

4. **Social Group Cohesion ($\vec{f}_i^{\text{group}}$):**
   $$\vec{f}_i^{\text{group}} = k_g (d_{ij} - d_{\text{pref}}) \vec{n}_{ij}$$
   Maintains proximity between paired companions and social groups walking together.

---

### 2.2 Global Pathfinding: Multi-Source BFS
To provide global spatial awareness without naive Euclidean line-of-sight pitfalls, a **Multi-Source Distance Field** computes the optimal wavefront:

$$\text{dist}(u) = \min_{v \in \text{Neighbors}(u)} (\text{dist}(v) + 1)$$

- **Optimality:** Guarantees shortest path across arbitrary room partitions and doorways.
- **Complexity:** $O(V + E)$ where $V = W \times H$.
- **Dynamic Re-computation:** Automatically re-triggers when doorways are blocked or fire hazards are placed.

---

### 2.3 Queue-Aware Dynamic Exit Balancing Heuristic
Naive evacuation models suffer from exit herding where agents crowd into the closest exit while adjacent exits remain empty. Our heuristic continually evaluates:

$$\text{Cost}(E_k) = \text{Distance}(P_i, E_k) + \alpha \times Q(E_k)$$

Where:
- $Q(E_k)$ is the active occupant queue waiting in the doorway catchment zone of exit $E_k$.
- $\alpha = 2.2$ is the doorway delay penalty factor.
- If an alternative exit $E_{\text{alt}}$ satisfies:
  $$\text{Cost}(E_{\text{alt}}) + \delta < \text{Cost}(E_{\text{current}})$$
  (with hysteresis threshold $\delta = 1.2$ to eliminate oscillation), the trailing agent autonomously recalculates their BFS route to $E_{\text{alt}}$, illuminates a golden halo, and displays a **`⚡ DIVERTER`** badge.

---

## 3. Floor Plan Architectural Generalization

| Floor Plan | Description | Architectural Highlights |
|---|---|---|
| **1. Campus Complex** | 3-wing university academic student center | Lecture Hall, Central Atrium, Library, 4 cardinal exits, structural pillars. |
| **2. Corporate Office Suites** | Multi-suite research and executive offices | Central spine hallway, 6 enclosed lab suites, 3 fire stairwells. |
| **3. Airport Transit Terminal** | Transit concourse with high-density chokepoints | Ticketing hall, narrow security screening checkpoint, duty-free islands. |
| **4. Procedural Unseen Layout** | Algorithmic layout generated from seed | Multi-partition randomized rooms proving robustness on unseen maps. |

---

## 4. Architectural Obstacles

Each environment incorporates **4 permanent architectural obstacles** affecting navigation:
1. **Information Kiosk (`KIOSK`):** Polished counter in concourse intersections.
2. **Cedar Seating Benches (`BENCH`):** Slat benches positioned along circulation corridors.
3. **Botanical Planters (`PLANTER`):** Green foliage boxes flanking main thoroughfares.
4. **Lecture & Work Desks (`DESK`):** Furniture clusters in classrooms and office suites.

---

## 5. Automated Testing & Verification

The suite contains **45 automated unit tests** verified via `pytest`:

```text
tests/test_agents.py (6 tests)
  - Agent initialization, physical state transitions, group dynamics.
  - Occupancy tracking and seed reproducibility.

tests/test_building.py (16 tests)
  - Grid geometry, 4-way neighbor lookups, boundary integrity.
  - Unseen floor plans connectivity (Office, Terminal, Procedural).
  - Architectural obstacles registration and collision properties.

tests/test_pathfinding.py (9 tests)
  - Single-source and multi-source BFS shortest paths.
  - Dead-end avoidance, maze navigation, and distance field parity.

tests/test_simulation.py (14 tests)
  - Helbing continuous physics integration and repulsion forces.
  - Dynamic hazard placement and real-time rerouting.
  - Dynamic congestion exit balancing and diverter validation.
  - Floor plan cycling and Scenario 5 benchmark execution.
```

**Result:** `45 passed in 0.89s (100% Pass Rate)`

---

## 6. How to Run the Demonstration

### 1. Launch Environment
```powershell
cd "Review 2"
..\venv\Scripts\Activate.ps1
python main.py
```

### 2. Review 2 Demonstration Controls
- **`[B]` / `[⚖️ Scenario 5: Demo Balancing]`:** Launches the 1-click Exit Balancing showcase (20 occupants cluster at West Exit, trailing crowd visibly diverts to South and North exits).
- **`[L]` / `[🏢 Cycle Map]`:** Cycles across the 4 unseen floor plans.
- **`[C]` / `[⚖️ Balancing: ON/OFF]`:** Toggles exit balancing on/off to compare egress times.
- **`[SPACE]`:** Start / Pause simulation.
- **`[M]`:** Switch between Normal Circulation and Emergency Evacuation.
- **`[H]`:** Toggle dynamic crowd density heatmap overlay.
- **Left-Click:** Inspect pedestrian dossier, drop fire hazards, or spawn new occupants.
