
import argparse
import os
import numpy as np
import pandas as pd
import torch
import torch.nn as nn


class TrajectoryLSTM(nn.Module):

    def __init__(self, hidden_size=64, num_layers=2):
        super().__init__()

        self.encoder = nn.LSTM(
            2, hidden_size, num_layers, batch_first=True
        )

        self.decoder = nn.LSTM(
            2, hidden_size, num_layers, batch_first=True
        )

        self.output_layer = nn.Linear(hidden_size, 2)

    def forward(self, observed, prediction_steps=12):

        _, (hidden, cell) = self.encoder(observed)
        current_position = observed[:, -1:, :]
        predictions = []

        for _ in range(prediction_steps):
            output, (hidden, cell) = self.decoder(
                current_position, (hidden, cell)
            )

            current_position = (
                current_position + self.output_layer(output)
            )

            predictions.append(current_position)

        return torch.cat(predictions, dim=1)


def create_sequences(df):

    X, Y = [], []

    for _, pedestrian in df.groupby("pedestrian_id"):

        pedestrian = pedestrian.sort_values("frame")
        frames = pedestrian["frame"].to_numpy()
        positions = pedestrian[["x", "y"]].to_numpy(
            dtype=np.float32
        )

        # Split discontinuous trajectories
        breaks = np.where(np.diff(frames) != 10)[0] + 1

        for segment in np.split(positions, breaks):

            for start in range(len(segment) - 19):

                window = segment[start:start + 20]

                origin = window[7].copy()

                X.append(window[:8] - origin)
                Y.append(window[8:] - origin)

    return (
        np.asarray(X, dtype=np.float32),
        np.asarray(Y, dtype=np.float32)
    )


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("--data", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output", default="test_results.csv")

    args = parser.parse_args()

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    df = pd.read_csv(
        args.data,
        sep=r"\s+",
        header=None,
        names=["frame", "pedestrian_id", "x", "y"]
    )

    X_test, Y_test = create_sequences(df)

    if len(X_test) == 0:
        raise ValueError("No valid test sequences found.")

    saved = torch.load(
        args.checkpoint,
        map_location=device,
        weights_only=True
    )

    config = saved["model_config"]

    model = TrajectoryLSTM(
        hidden_size=config["hidden_size"],
        num_layers=config["num_layers"]
    ).to(device)

    model.load_state_dict(saved["model_state_dict"])
    model.eval()

    predictions = []

    with torch.no_grad():

        for start in range(0, len(X_test), 128):

            batch = torch.tensor(
                X_test[start:start + 128],
                dtype=torch.float32
            ).to(device)

            output = model(batch, prediction_steps=12)
            predictions.append(output.cpu().numpy())

    Y_lstm = np.concatenate(predictions)

    # LSTM metrics
    lstm_distances = np.linalg.norm(
        Y_lstm - Y_test, axis=2
    )

    lstm_ade = lstm_distances.mean()
    lstm_fde = lstm_distances[:, -1].mean()

    # Constant velocity baseline
    velocity = X_test[:, -1] - X_test[:, -2]

    Y_baseline = np.stack(
        [
            X_test[:, -1] + step * velocity
            for step in range(1, 13)
        ],
        axis=1
    )

    baseline_distances = np.linalg.norm(
        Y_baseline - Y_test, axis=2
    )

    baseline_ade = baseline_distances.mean()
    baseline_fde = baseline_distances[:, -1].mean()

    results = pd.DataFrame({
        "Metric": ["ADE", "FDE"],
        "Constant Velocity": [baseline_ade, baseline_fde],
        "LSTM": [lstm_ade, lstm_fde]
    })

    results.to_csv(args.output, index=False)

    print("\nHELD-OUT ETH EVALUATION")
    print("----------------------")
    print("Test sequences:", len(X_test))
    print(results.to_string(index=False))

    print("\nResults saved:", args.output)


if __name__ == "__main__":
    main()
