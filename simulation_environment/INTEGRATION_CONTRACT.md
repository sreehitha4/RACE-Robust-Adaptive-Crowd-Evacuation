# RACE Simulation Integration Contract

## Ownership
- Simulation owner: Keerthana — actual positions, velocities, navigation, safety constraints, exits, history.
- ML owner: Sreehitha — checkpoint and `RACEPredictor` inference.
- Backend owner: Hardhick — API lifecycle, WebSocket scheduling, serialization and orchestration.
- Frontend owner: Sinan — rendering, controls and statistics panel.

## ML contract
- Input: `float32` array of shape `(8, 2)`.
- Input order: oldest to newest sampled positions.
- Output: finite `float32` array of shape `(12, 2)`.
- Output coordinate frame: original input coordinate frame.
- Sampling: ETH notebook segments at frame-number increments of exactly 10.
- Time in seconds: not specified by the shared ML files; confirm dataset FPS before physical calibration.

## Actual vs predicted
`agents[].x/y` are the actual simulated positions. `agents[].predicted_trajectory` is an advisory future path only. Do not render predicted points as actual movement and do not let raw model output bypass obstacle/collision handling.

## State update fields
- `agents`: array of agent objects.
- `density`: active agent count divided by room area.
- `simulation_time`: seconds since reset.
- `evacuated_count`, `remaining_agents`, `statistics`.
- `status`: `ready`, `running`, or `completed` (the service facade can pause by setting `paused`).
- `ml_enabled`: true only if a predictor loaded successfully.

## Suggested WebSocket payload
Send the complete `CrowdSimulation.state()` object as JSON. For bandwidth reduction, the backend may later send only changed agent states while preserving the same field names and schema version.
