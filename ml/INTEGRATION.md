
# RACE ML Integration Guide

## 1. Purpose

The ML component predicts ordinary pedestrian movement
using an Encoder-Decoder LSTM trained on ETH-UCY data.

## 2. Model Interface

Import:

from model_inference import RACEPredictor

Initialize:

predictor = RACEPredictor(
    "models/trajectory_lstm_best.pth"
)

Predict:

predictions = predictor.predict(observed_positions)

## 3. Input Contract

Input shape: (8, 2)

Eight consecutive pedestrian positions.

Each position contains:
- x coordinate
- y coordinate

Input must use the same coordinate units and orientation
as the training data.

## 4. Output Contract

Output shape: (12, 2)

Twelve predicted future positions in the original
coordinate system.

## 5. Integration Responsibilities

ML component:
- Load trained checkpoint.
- Accept observed trajectory.
- Predict future positions.
- Return predictions.

Simulation component:
- Maintain agent state.
- Apply collision avoidance.
- Handle obstacles.
- Control actual agent movement.
- Handle exits and emergency decisions.

Backend component:
- Coordinate model and simulation communication.
- Manage API and WebSocket messages.

Frontend component:
- Display agents and predicted trajectories.
- Visualize simulation state.

## 6. Model Limitations

The model learns ordinary pedestrian movement patterns.
It is not an emergency evacuation policy.

Emergency-specific movement, adversarial behaviour,
and reinforcement learning remain future RACE stages.

## 7. Validation Results

Validation:
ADE: 0.4425
FDE: 0.9524

Held-out ETH test:
ADE: 1.0085
FDE: 2.0268

Constant-velocity baseline on held-out ETH:
ADE: 1.0755
FDE: 2.2819

## 8. Integration Note

The model currently expects eight consecutive positions.
The simulation must maintain a compatible trajectory
history for each agent.

The model predicts movement preferences; it does not
directly control the simulation.
