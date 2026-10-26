# Python ONNX Runtime smoke test

`infer-yolox-nano.py` creates an ONNX Runtime session with the TI TIDL execution provider for the supplied bundle `/opt/model_zoo/ONR-OD-8200-yolox-nano-lite-mmdet-coco-416x416` and runs one inference on a blank input.

It only proves that the image's TI ONNX Runtime, the TIDL execution provider and the compiled artifacts load and execute together. It is **not** an accuracy test and not a video frame-rate measurement; blank input produces no meaningful detections.

Run on the board:

```bash
sudo python3 infer-yolox-nano.py
```

Origin: the mo-docs "Inference APIs" page for Mo62A (`static/downloads/ai/infer-yolox-nano.py`). The script requires the TI ONNX Runtime from the board image, not the Debian `onnxruntime` package. Latency measurements with repeated runs belong to the benchmark script in [mo-models](https://github.com/inhandnet/mo-models).
