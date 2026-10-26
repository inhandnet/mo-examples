# Edge AI examples

Runnable edge AI examples for Mo boards. Each subdirectory has its own README with the exact board image, model and run commands it was written against.

| Directory | What it is | Origin |
| --- | --- | --- |
| `edgeai-cpp/` | C/C++ inference examples built on the board with `find_package(EdgeAI)`: `hello_inference` (single inference on one model) and `app_edgeai` (camera → inference → HDMI demo with YAML configs), plus the developer guide. | Mo62A repository, `board-support/extra-applications/edgeai-cpp/examples` and `src/apps_cpp` |
| `python-smoke/` | ONNX Runtime + TIDL execution provider smoke test in Python for the supplied YOLOX-nano bundle. | mo-docs inference APIs tutorial |
| `zone-demo/` | Application-side scripts of the YOLOX-tiny-lite 8210 zone-occupancy tutorial (detection contract, zone rules, input preparation, bundle inspection). | mo-docs tutorial package |

Model bundles are expected under `/opt/model_zoo/<name>/` on the board (`param.yaml`, `model/`, `artifacts/`). The model catalog, compile scripts and benchmark scripts live in [mo-models](https://github.com/inhandnet/mo-models); the toolchain pins and host setup live in [mo-tools](https://github.com/inhandnet/mo-tools).

Nothing in this directory was re-compiled or re-run as part of importing it into this repository; the per-directory READMEs state what was verified and where.
