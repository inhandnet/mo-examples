#!/usr/bin/env python3
"""Mo62A supplied YOLOX-nano smoke test; blank input does not test accuracy."""
from pathlib import Path

import numpy as np
import onnxruntime as ort

model_dir = Path("/opt/model_zoo/ONR-OD-8200-yolox-nano-lite-mmdet-coco-416x416")
model = model_dir / "model/yolox_nano_lite_416x416_20220214_model.onnx"
if "TIDLExecutionProvider" not in ort.get_available_providers():
    raise RuntimeError("The image's TI ONNX Runtime is required")
options = ort.SessionOptions()
options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_DISABLE_ALL
# Follow the pinned TI 1.23 wrapper, then check this example's tensors explicitly.
options.add_session_config_entry("session.disable_input_validation", "1")
options.add_session_config_entry("session.disable_output_validation", "1")
session = ort.InferenceSession(
    str(model),
    sess_options=options,
    providers=["TIDLExecutionProvider", "CPUExecutionProvider"],
    provider_options=[{"artifacts_folder": str(model_dir / "artifacts")}, {}],
)
inputs = session.get_inputs()
if len(inputs) != 1 or inputs[0].shape != [1, 3, 416, 416] or inputs[0].type != "tensor(uint8)":
    raise RuntimeError("Unexpected model input: stop and inspect the model bundle")
inp = inputs[0]
frame = np.zeros((1, 3, 416, 416), dtype=np.uint8)
print("INPUT", inp.name, inp.shape, inp.type)
for run in range(3):
    outputs = session.run(None, {inp.name: frame})
    if len(outputs) != 2 or [tuple(x.shape) for x in outputs] != [(200, 5), (200,)]:
        raise RuntimeError("Unexpected output shapes")
    if not all(np.isfinite(x).all() for x in outputs):
        raise RuntimeError("Non-finite model output")
    print("RUN", run + 1, "OUTPUTS", [(x.shape, str(x.dtype)) for x in outputs], "finite")
print("Completed three calls; blank-input smoke test, not accuracy or FPS.")
