# RACE – Crowd Evacuation Simulation Engine

## 1. Project Overview

RACE is a crowd evacuation simulation system designed to model pedestrian movement and evacuation behaviour in indoor environments during emergency situations.

The simulation engine models pedestrians as individual agents and simulates their movement through an environment containing walls, obstacles, and emergency exits.

The system combines:

- Pedestrian agent modelling
- Indoor environment representation
- Navigation and pathfinding
- Obstacle avoidance
- Agent-agent collision avoidance
- LSTM-based trajectory prediction integration
- Evacuation tracking and statistics
- JSON-based simulation state export
- Browser-based simulation visualization

The simulation engine acts as the core component responsible for updating pedestrian positions, maintaining trajectories, handling evacuation, and providing simulation data to the backend and frontend components.

## 2. Objectives

The primary objectives of the simulation engine are:

1. Model pedestrians as individual autonomous agents.
2. Represent an indoor environment containing obstacles and emergency exits.
3. Calculate navigation paths for pedestrians towards their assigned exits.
4. Prevent pedestrians from moving through obstacles and walls.
5. Reduce collisions between pedestrians through separation-based collision avoidance.
6. Maintain pedestrian trajectory histories for machine learning inference.
7. Integrate an LSTM trajectory prediction model.
8. Track evacuation progress and calculate evacuation statistics.
9. Export simulation states in JSON format.
10. Provide an independently runnable simulation for testing and integration.

## 3. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Simulation engine implementation |
| NumPy | Numerical calculations and vector operations |
| Shapely | Geometric representation and collision checks |
| A* Pathfinding | Navigation path generation |
| LSTM | Pedestrian trajectory prediction |
| JSON | Simulation state export |
| HTML, CSS, JavaScript | Browser-based visualization |
| Python HTTP Server | Serving the browser demo |
| unittest | Automated testing |

## 4. Project Structure

```text
RACE/
│
├── browser_demo/
│   ├── server.py
│   └── index.html
│
├── simulation/
│   ├── __init__.py
│   ├── agent.py
│   ├── collision.py
│   ├── config.py
│   ├── environment.py
│   ├── export.py
│   ├── ml_integration.py
│   ├── movement.py
│   ├── obstacle.py
│   ├── service.py
│   ├── simulation.py
│   ├── statistics.py
│   └── trajectory.py
│
├── tests/
│   ├── test_collision_validation.py
│   └── other test files
│
├── models/
│   └── trajectory_lstm_best.pth
│
├── README.md
└── requirements.txt
```

*Note: The structure above describes the main modules. Keep only files and directories that actually exist in your repository. Add any other existing test files to the structure.*

## 5. Simulation Architecture

The simulation engine consists of several interconnected modules.

### 5.1 Pedestrian Agent Module

File: `simulation/agent.py`

Each pedestrian is represented as an individual agent.

An agent maintains:

- Unique agent ID
- Current X and Y position
- Velocity in X and Y directions
- Physical radius
- Current state
- Assigned emergency exit
- Trajectory history
- Predicted trajectory
- Navigation path
- Current waypoint index
- Evacuation timestamp

Agent states are used to distinguish pedestrians who are still moving from those who have successfully evacuated.

### 5.2 Environment Module

File: `simulation/environment.py`

The environment represents the indoor floor plan.

It contains:

- Room dimensions
- Walls and boundaries
- Static obstacles
- Emergency exits
- Walkable and non-walkable regions

The environment uses geometric representations to determine whether a pedestrian can safely occupy a particular position.

### 5.3 Navigation and Pathfinding

File: `simulation/environment.py`

The simulation uses A* pathfinding to calculate navigation paths.

The pathfinding mechanism:

1. Identifies the pedestrian's assigned exit.
2. Searches for a navigable route.
3. Avoids blocked regions.
4. Generates intermediate waypoints.
5. Allows the movement controller to follow the generated path.

This helps pedestrians navigate around obstacles instead of moving directly towards an exit.

### 5.4 Movement Controller

File: `simulation/movement.py`

The movement controller determines how pedestrians move during each simulation step.

It considers:

- Direction towards the next navigation waypoint
- Desired movement speed
- Predicted trajectory information
- Separation forces from nearby pedestrians
- Obstacle safety constraints
- Collision checks

The movement controller retains authority over actual pedestrian movement.

LSTM predictions influence movement direction but do not directly determine the final position of an agent.

### 5.5 Obstacle Avoidance

File: `simulation/obstacle.py`

Obstacle avoidance prevents pedestrians from entering blocked regions.

The module:

- Checks whether a proposed position is walkable.
- Considers the pedestrian's physical radius.
- Checks the proposed movement against environmental boundaries.
- Attempts alternative movement directions when the initial movement is unsafe.
- Stops movement when no safe alternative is available.

### 5.6 Agent-Agent Collision Avoidance

File: `simulation/collision.py`

Collision avoidance calculates separation forces between nearby pedestrians.

For every pedestrian, the system examines other active pedestrians and calculates their relative distance.

When another pedestrian enters the separation distance, a repulsive force is generated.

The force encourages pedestrians to move away from one another.

The collision avoidance module also handles:

- Agents that are extremely close together.
- Coincident agent positions.
- Ignoring evacuated agents.
- Combining separation forces from nearby pedestrians.

The movement controller additionally checks candidate positions against other pedestrians before accepting movement.

## 6. LSTM Trajectory Prediction Integration

File: `simulation/ml_integration.py`

The simulation supports integration with the trajectory prediction model developed by the machine learning component.

The predictor interface is:

```python
from model_inference import RACEPredictor

predictor = RACEPredictor(
    "models/trajectory_lstm_best.pth"
)

predictions = predictor.predict(observed_positions)
```

### Input

The model receives eight consecutive observed pedestrian positions.

Input shape:

```text
(8, 2)
```

Each position contains:

```text
[x, y]
```

### Output

The model predicts twelve future positions.

Output shape:

```text
(12, 2)
```

### Prediction Workflow

1. The simulation maintains a trajectory history for each pedestrian.
2. Once sufficient observations are available, the trajectory is passed to the predictor.
3. The predictor generates twelve future positions.
4. The predicted trajectory is stored with the corresponding agent.
5. The movement controller can use the prediction as an additional movement preference.
6. Actual movement remains subject to navigation, obstacle avoidance, and collision checks.

The predictor is not itself an emergency evacuation policy.

## 7. Trajectory Management

File: `simulation/trajectory.py`

Each pedestrian maintains a history of eight consecutive observed positions.

The trajectory history is used as input for the LSTM prediction model.

The simulation also stores predicted future trajectories separately from observed positions.

This distinction allows the system to:

- Track actual pedestrian movement.
- Maintain historical observations.
- Generate future trajectory predictions.
- Compare predicted and actual movement during evaluation.

## 8. Evacuation Management and Statistics

File: `simulation/statistics.py`

The statistics module tracks evacuation progress.

The system maintains:

- Total number of pedestrians
- Number of evacuated pedestrians
- Number of remaining pedestrians
- Evacuation percentage
- Simulation time
- Mean evacuation time

When a pedestrian reaches their assigned emergency exit, their state is updated to `evacuated`.

Evacuated pedestrians are no longer treated as active moving pedestrians.

The statistics module also prevents duplicate evacuation counting for the same agent.

### Evacuation Percentage

```text
Evacuation Percentage =
(Evacuated Pedestrians / Total Pedestrians) × 100
```

### Remaining Pedestrians

```text
Remaining Pedestrians =
Total Pedestrians - Evacuated Pedestrians
```

## 9. Simulation State Export

File: `simulation/export.py`

The simulation state is exported in JSON format.

The exported information includes:

- Environment dimensions
- Obstacles
- Emergency exits
- Pedestrian positions
- Pedestrian velocities
- Agent states
- Assigned exits
- Trajectory histories
- Predicted trajectories
- Navigation paths
- Waypoint indices
- Evacuation timestamps
- Evacuation statistics
- Simulation time
- Simulation status
- ML integration status

The JSON representation provides a structured interface for communication with the backend and frontend components.

## 10. Browser-Based Simulation Demo

Directory: `browser_demo/`

The project includes a browser-based visualization for independently testing the simulation.

The demo provides:

- Visualization of the indoor environment
- Pedestrian representation
- Obstacle representation
- Emergency exit representation
- Pedestrian movement visualization
- Evacuation status
- Simulation statistics
- Start, Pause, and Reset controls

### Running the Browser Demo

Activate your virtual environment first.

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Start the browser demo from the project root:

```powershell
python -m browser_demo.server
```

Open the following address:

```text
http://127.0.0.1:8765/
```

The simulation state can also be accessed through:

```text
http://127.0.0.1:8765/state
```

## 11. Installation and Setup

### Prerequisites

- Python 3.12 or a compatible Python version
- pip
- Git
- Visual Studio Code (recommended)

### Step 1: Clone the Repository

```bash
git clone <repository-url>
```

Navigate into the project directory:

```bash
cd <repository-folder>
```

### Step 2: Create a Virtual Environment

Windows:

```powershell
python -m venv .venv
```

### Step 3: Activate the Environment

```powershell
.venv\Scripts\Activate.ps1
```

### Step 4: Install Dependencies

```powershell
python -m pip install --upgrade pip
```

```powershell
pip install -r requirements.txt
```

If the repository does not contain a `requirements.txt`, create one containing the actual dependencies used by the project.

## 12. Testing

The project uses Python's built-in `unittest` framework.

### 12.1 Collision Avoidance Validation

File:

```text
tests/test_collision_validation.py
```

The collision avoidance validation tests cover four cases.

| Test | Description |
|---|---|
| Safe Distance | Checks that pedestrians outside the separation distance experience no repulsive force. |
| Agents Too Close | Checks that nearby pedestrians experience force away from one another. |
| Coincident Agents | Checks that coincident pedestrians produce a finite, non-zero separation force. |
| Evacuated Agents | Checks that evacuated pedestrians are ignored during collision avoidance calculations. |

Run the collision validation tests:

```powershell
python -m unittest discover -s tests -p "test_collision_validation.py" -v
```

### 12.2 Run All Tests

To execute all automated tests:

```powershell
python -m unittest discover -s tests -v
```

### 12.3 Expected Collision Test Results

```text
test_agents_too_close ... ok
test_coincident_agents ... ok
test_evacuated_agents_are_ignored ... ok
test_safe_distance ... ok

Ran 4 tests

OK
```

These tests validate the collision separation-force calculations. They do not independently establish that collisions are impossible under every full-simulation scenario.

## 13. Team Integration

The simulation engine is designed to integrate with the other RACE components.

| Component | Responsibility |
|---|---|
| Simulation Engine | Pedestrian modelling, navigation, movement, obstacle avoidance and evacuation |
| ML Component | LSTM-based trajectory prediction |
| Backend | FastAPI services and WebSocket communication |
| Frontend | Browser-based visualization and interaction |

### Integration Flow

1. The simulation engine maintains the current pedestrian and environment state.
2. The ML component provides predicted pedestrian trajectories.
3. The movement controller uses predictions as movement preferences.
4. The simulation updates actual pedestrian positions.
5. The engine calculates evacuation progress and statistics.
6. The current state is exported in JSON format.
7. The backend and frontend can consume the exported state for communication and visualization.

## 14. Future Enhancements

Potential improvements include:

- Multi-exit evacuation optimization.
- Dynamic obstacle and hazard modelling.
- Fire and smoke propagation.
- Density-aware pedestrian movement.
- More advanced collision avoidance algorithms.
- Simulation performance optimization.
- Integration of real-time emergency scenarios.
- Evaluation across different indoor floor plans.
- Quantitative comparison between predicted and actual trajectories.
- Testing generalization across unseen environments.

## 15. Conclusion

The RACE simulation engine provides the core environment for modelling pedestrian evacuation behaviour.

It combines individual pedestrian agents, indoor environment representation, navigation, obstacle avoidance, collision avoidance, trajectory prediction integration, and evacuation statistics.

Its modular architecture supports independent testing and integration with the machine learning, backend, and frontend components of the RACE system.