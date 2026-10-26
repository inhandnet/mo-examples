# C/C++ Edge AI examples (Mo62A)

C/C++ inference examples that are compiled **on the Mo62A board**, without a cross-compilation setup. The board image installs the Edge AI C/C++ SDK (headers in `/usr/include/edgeai/`, static libraries in `/usr/lib/edgeai/`, the CMake package in `/usr/lib/cmake/EdgeAI/`, TI runtime shared libraries in `/opt/ti/edgeai/lib/`), so a single `find_package(EdgeAI)` line pulls in every include path and library.

| Path | Content |
| --- | --- |
| `DEV_GUIDE.md` | Developer guide (Chinese) shipped with the SDK: what the SDK installs, a minimal program, build and debug notes. |
| `hello_inference/` | Minimal example: loads one model directory, runs a single inference on a zero-filled input and prints the output tensors and timing. |
| `app_edgeai/` | Full camera/video → inference → HDMI demo, the C/C++ counterpart of the Python `app_edgeai.py`. It reads the same YAML configuration schema. |
| `configs/` | Example configurations for `app_edgeai`: CSI (IMX219) and USB camera object detection. |

## Build on the board

```bash
cd hello_inference        # or app_edgeai
mkdir build && cd build
cmake .. && make
```

`app_edgeai/CMakeLists.txt` at the top level of that directory is the thin board build file (`find_package(EdgeAI)` + `file(GLOB)` over `common/`, `utils/` and `app_edgeai/src`). The `CMakeLists.txt` files inside `common/`, `utils/` and `app_edgeai/` subdirectories come from the TI source tree and are not used by this build; they are kept unchanged for reference.

## Run

```bash
./hello_inference /opt/model_zoo/ONR-OD-8200-yolox-nano-lite-mmdet-coco-416x416

sudo systemctl stop lightdm            # kmssink needs DRM master
sudo -E ./app_edgeai ../configs/object_detection_csi.yaml
```

Inference needs root (C7x, VPAC and DRM access). A model directory must contain `param.yaml`, `model/` and `artifacts/` as described in the [mo-models](https://github.com/inhandnet/mo-models) catalog.

## Verification status

- The same sources are installed on the Mo62A image under `/usr/share/edgeai-cpp-examples/` and were built and run on the board when the SDK was delivered (the supplied detection model reported all nodes offloaded to the C7x).
- Importing them into this repository did **not** rebuild or re-run them. Verify against the image version named in the mo-docs version map before relying on the numbers in `DEV_GUIDE.md`.
- `DEV_GUIDE.md` still describes the TI ONNX Runtime as "1.15"; the audited V1.1.0 image reports 1.23.0 (see the mo-docs version map). The guide text is kept as shipped.

## Origin and licensing

- `hello_inference/`, `configs/`, `DEV_GUIDE.md` and the top-level `app_edgeai/CMakeLists.txt`: Mo62A repository, `board-support/extra-applications/edgeai-cpp/examples` (Apache-2.0, same as this repository).
- `app_edgeai/common/`, `app_edgeai/utils/`, `app_edgeai/app_edgeai/`: TI edge AI application sources (Copyright Texas Instruments Incorporated) carried in the Mo62A SDK tree; each file keeps its original TI license header.
