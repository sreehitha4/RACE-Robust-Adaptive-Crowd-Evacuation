# RACE - Pedestrian Trajectory Prediction using LSTM

## 1. Overview

This module implements an LSTM-based pedestrian trajectory prediction model for the RACE project.

The model learns ordinary pedestrian movement patterns from ETH-UCY trajectory data and predicts future positions using observed movement history.

## 2. Model Architecture

- Model: Encoder-Decoder LSTM
- Input features: 2 (x, y coordinates)
- Hidden size: 64
- Number of LSTM layers: 2
- Total parameters: 101,506
- Observed trajectory: 8 time steps
- Prediction horizon: 12 time steps

## 3. Dataset and Experimental Setup

Dataset: ETH-UCY pedestrian trajectory data.

- Training sequences: 30,307
- Validation sequences: 5,422
- Held-out ETH test sequences: 364

Training, validation and held-out test scenes were kept separate.

## 4. Validation Results

| Metric | Constant Velocity | LSTM |
|---|---:|---:|
| ADE | 0.4471 | 0.4425 |
| FDE | 0.9877 | 0.9524 |

- ADE improvement: 1.02%
- FDE improvement: 3.58%

## 5. Held-Out ETH Test Results

| Metric | Constant Velocity | LSTM |
|---|---:|---:|
| ADE | 1.0755 | 1.0085 |
| FDE | 2.2819 | 2.0268 |

- ADE improvement: 6.23%
- FDE improvement: 11.18%

The held-out ETH scene was not used for training or validation.

## 6. Project Structure

- `model_inference.py` - Model architecture and inference interface.
- `evaluate.py` - Reproducible evaluation script.
- `models/` - Trained model checkpoint (kept locally pending dataset licensing review).
- `data/` - Dataset-derived trajectory sequences (kept locally).
- `results/` - Evaluation metrics, plots and experiment metadata.
- `INTEGRATION.md` - Integration instructions for the RACE team.
- `requirements.txt` - Python dependencies.

## 7. Requirements

- Python 3.11+
- NumPy
- Pandas
- PyTorch

Install dependencies:

```bash
pip install -r requirements.txt
```

## 8. Inference Usage

```python
from model_inference import RACEPredictor

predictor = RACEPredictor(
    "models/trajectory_lstm_best.pth"
)

predictions = predictor.predict(observed_positions)
```

Input shape: `(8, 2)`

Output shape: `(12, 2)`

The input consists of eight consecutive positions, each containing x and y coordinates. The output contains twelve predicted future positions in the original coordinate system.

## 9. Limitations and Future Work

The model learns ordinary pedestrian movement patterns. It is not an emergency evacuation policy.

Emergency-specific behaviour, adversarial agents, reinforcement learning and generalization under evacuation disturbances remain future stages of the RACE project.

The model's predictions are intended as movement preferences for integration with the simulation's movement controller.
