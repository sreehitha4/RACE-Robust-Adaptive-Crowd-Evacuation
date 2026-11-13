"""Sreehitha's RACE LSTM inference interface (kept API-compatible)."""
import torch
import torch.nn as nn
import numpy as np

class TrajectoryLSTM(nn.Module):
    def __init__(self, hidden_size=64, num_layers=2):
        super().__init__()
        self.encoder = nn.LSTM(input_size=2, hidden_size=hidden_size, num_layers=num_layers, batch_first=True)
        self.decoder = nn.LSTM(input_size=2, hidden_size=hidden_size, num_layers=num_layers, batch_first=True)
        self.output_layer = nn.Linear(hidden_size, 2)

    def forward(self, observed, prediction_steps=12):
        _, (hidden, cell) = self.encoder(observed)
        current_position = observed[:, -1:, :]
        predictions = []
        for _ in range(prediction_steps):
            decoder_output, (hidden, cell) = self.decoder(current_position, (hidden, cell))
            displacement = self.output_layer(decoder_output)
            current_position = current_position + displacement
            predictions.append(current_position)
        return torch.cat(predictions, dim=1)

class RACEPredictor:
    def __init__(self, checkpoint_path):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        saved = torch.load(checkpoint_path, map_location=self.device, weights_only=True)
        config = saved["model_config"]
        self.model = TrajectoryLSTM(hidden_size=config["hidden_size"], num_layers=config["num_layers"]).to(self.device)
        self.model.load_state_dict(saved["model_state_dict"])
        self.model.eval()

    def predict(self, observed_positions):
        positions = np.asarray(observed_positions, dtype=np.float32)
        if positions.shape != (8, 2):
            raise ValueError(f"Expected input shape (8, 2), received {positions.shape}")
        if not np.isfinite(positions).all():
            raise ValueError("Input contains non-finite values")
        origin = positions[-1].copy()
        normalized = positions - origin
        input_tensor = torch.tensor(normalized, dtype=torch.float32).unsqueeze(0).to(self.device)
        with torch.no_grad():
            prediction = self.model(input_tensor, prediction_steps=12)
        return prediction.squeeze(0).cpu().numpy() + origin
