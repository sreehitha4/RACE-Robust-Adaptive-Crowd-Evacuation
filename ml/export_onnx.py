"""Export the trained RACE LSTM checkpoint to ONNX for optional optimized serving.

Usage: python -m ml.export_onnx --checkpoint simulation_environment/ml/models/trajectory_lstm_best.pth
Requires: pip install onnx onnxruntime (and the existing PyTorch requirements).
"""
import argparse
from pathlib import Path
import torch
from ml.model_inference import TrajectoryLSTM

class ExportWrapper(torch.nn.Module):
    def __init__(self, model):
        super().__init__(); self.model = model
    def forward(self, observed):
        return self.model(observed, prediction_steps=12)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output", default="models/race_lstm.onnx")
    args = parser.parse_args()
    saved = torch.load(args.checkpoint, map_location="cpu", weights_only=True)
    cfg = saved["model_config"]
    model = TrajectoryLSTM(cfg["hidden_size"], cfg["num_layers"])
    model.load_state_dict(saved["model_state_dict"]); model.eval()
    output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True)
    sample = torch.zeros(1, 8, 2, dtype=torch.float32)
    torch.onnx.export(ExportWrapper(model), sample, str(output), input_names=["observed_positions"],
                      output_names=["predicted_positions"], dynamic_axes={"observed_positions": {0: "batch"}, "predicted_positions": {0: "batch"}},
                      opset_version=17, do_constant_folding=True)
    print(f"Exported ONNX model: {output}")

if __name__ == "__main__": main()
