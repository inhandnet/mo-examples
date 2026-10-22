# Zone-occupancy demo (YOLOX-tiny-lite 8210) — application side

Application-side scripts of the mo-docs tutorial that compiles the official TI YOLOX-tiny-lite 8210 (COCO, 416×416) model for Mo62A and uses it for a warehouse zone-occupancy demo.

| File | Purpose |
| --- | --- |
| `model.py` | Fixed model contract: upstream TI model name, download base, SHA-256 of the ONNX and prototxt files, preprocessing and bundle verification helpers. |
| `fetch_model.py` | Downloads the unchanged official model files and keeps existing files only when their hashes match. |
| `prepare_inputs.py` | Extracts reproducible representative frames; calibration and evaluation must come from separate clips. |
| `inspect_bundle.py` | Inspects a complete versioned model bundle without creating an inference session. |
| `compare_detections.py` | Matches CPU and quantized person detections; this is agreement between two runs, not ground truth. |
| `logic.py` | Pure zone-occupancy rules; no identity tracking and no safety control. |
| `sources.json`, `SOURCE.txt` | Model and footage provenance. |
| `LICENSE` | License of these scripts (see below). |

## What is not here

- The compile step (`compile_model.py`) and the x86 host setup (`setup_host.sh`, `activate_host.sh`, `requirements-host.txt`) are published from [mo-models](https://github.com/inhandnet/mo-models) (`compile/`) and [mo-tools](https://github.com/inhandnet/mo-tools) (`toolchain/`). `compile_model.py` imports this directory's `model.py`; until a mo-models release provides the shared contract, both repositories carry an identical copy of `model.py`.
- The two input clips (`inputs/calibration.mp4`, about 5.4 MB, and `inputs/evaluation.mp4`, about 4.4 MB) are not copied. They are derived from third-party CC BY 4.0 footage; `SOURCE.txt` records the originals and the edits applied.
- The complete tutorial package `mo62a-zone-demo.tar.gz` and its `.sha256` are still published by mo-docs under `/downloads/ai/`. This repository does not re-package it.

## Licensing

These scripts come from the mo-docs tutorial package and are licensed CC BY-SA 4.0 (the `LICENSE` file in this directory), which differs from the Apache-2.0 license of the rest of this repository. The footage is CC BY 4.0 by its creator as listed in `SOURCE.txt`. The TI model is subject to TI's model-zoo license referenced in `sources.json`.
