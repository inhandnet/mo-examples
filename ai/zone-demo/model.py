"""Fixed TI YOLOX-tiny-lite (8210) contract. No model/activation rewriting."""
import hashlib
import json
from pathlib import Path

MODEL_NAME = 'yolox_tiny_lite_416x416_20220217_model'
MODEL_SHA256 = 'c9d2a3fdb21bed079a74029441d83235ddd910c82f1e7b9de5a2a5998bc3eeca'
META_SHA256 = 'bd8d5558af8c982da135579cd84851f9d95382aab6f089df7a49edacb846f142'
UPSTREAM = 'https://software-dl.ti.com/jacinto7/esd/modelzoo/11_02_00/models/vision/detection/coco/edgeai-mmdet/'


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def write_json(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def preprocess(bgr):
    import cv2
    import numpy as np
    if bgr is None or bgr.dtype != np.uint8 or bgr.ndim != 3 or bgr.shape[2] != 3:
        raise ValueError('Expected an 8-bit BGR image')
    height, width = bgr.shape[:2]
    ratio = min(416 / width, 416 / height)
    resized_width, resized_height = max(1, round(width * ratio)), max(1, round(height * ratio))
    resized = cv2.resize(bgr, (resized_width, resized_height), interpolation=cv2.INTER_LINEAR)
    canvas = np.full((416, 416, 3), 114, dtype=np.uint8)
    canvas[:resized_height, :resized_width] = resized
    # This model expects 0..255 float RGB, not uint8 and not RGB/255.
    tensor = np.ascontiguousarray(canvas[:, :, ::-1].transpose(2, 0, 1)[None], dtype=np.float32)
    return tensor, (resized_width / width, resized_height / height)


def detections(outputs, frame_shape, scales, threshold=0.4):
    import numpy as np
    if len(outputs) != 2:
        raise ValueError('Expected dets and labels outputs')
    boxes, labels = outputs
    if boxes.ndim != 2 or boxes.shape[1] != 5 or labels.ndim != 1 or len(boxes) != len(labels):
        raise ValueError('Unexpected detector output shapes')
    if not all(np.isfinite(v).all() for v in outputs):
        raise ValueError('Non-finite detector output')
    height, width = frame_shape[:2]
    results = []
    for row, label in zip(boxes, labels):
        score = float(row[4])
        if score < threshold:
            continue
        if not 0 <= score <= 1.001 or not float(label).is_integer() or not 0 <= label < 80:
            raise ValueError('Invalid score/class index')
        x1, y1, x2, y2 = [float(v) for v in row[:4]]
        x1, x2 = [max(0.0, min(width - 1.0, x / scales[0])) for x in (x1, x2)]
        y1, y2 = [max(0.0, min(height - 1.0, y / scales[1])) for y in (y1, y2)]
        if x2 <= x1 or y2 <= y1:
            continue
        results.append({'label': int(label), 'score': score, 'box': [x1, y1, x2, y2]})
    return results


def check_sources(bundle):
    for suffix, expected in (('.onnx', MODEL_SHA256), ('.prototxt', META_SHA256)):
        if sha256(bundle / 'model' / (MODEL_NAME + suffix)) != expected:
            raise ValueError('Unexpected model or metadata checksum: ' + suffix)


def verify_bundle(bundle):
    check_sources(bundle)
    manifest = json.loads((bundle / 'bundle.json').read_text())
    if manifest['soc'] != 'AM62A' or manifest['tidl_release'] != '11_02_17_00':
        raise ValueError('Unexpected bundle compatibility baseline')
    for name, expected in manifest['files'].items():
        path = (bundle / name).resolve()
        if not path.is_relative_to(bundle.resolve()) or sha256(path) != expected:
            raise ValueError('Bundle checksum failed: ' + name)
    return manifest


def session(bundle, backend, debug=0):
    import onnxruntime as ort
    if ort.__version__ != '1.23.0':
        raise RuntimeError('This tutorial pins ONNX Runtime 1.23.0')
    if backend == 'tidl':
        verify_bundle(bundle)
    else:
        check_sources(bundle)
    provider = 'TIDLExecutionProvider' if backend == 'tidl' else 'CPUExecutionProvider'
    if provider not in ort.get_available_providers():
        raise RuntimeError('Missing provider: ' + provider)
    settings = ort.SessionOptions()
    settings.intra_op_num_threads = 1
    settings.graph_optimization_level = ort.GraphOptimizationLevel.ORT_DISABLE_ALL
    # Pinned TI wrapper's output-reformat contract. Explicit checks remain above.
    settings.add_session_config_entry('session.disable_input_validation', '1')
    settings.add_session_config_entry('session.disable_output_validation', '1')
    providers = [provider, 'CPUExecutionProvider'] if backend == 'tidl' else [provider]
    options = [{'artifacts_folder': str(bundle / 'artifacts'), 'debug_level': debug}, {}] if backend == 'tidl' else [{}]
    instance = ort.InferenceSession(str(bundle / 'model' / (MODEL_NAME + '.onnx')),
                                   sess_options=settings, providers=providers, provider_options=options)
    inputs = instance.get_inputs()
    if len(inputs) != 1 or inputs[0].type != 'tensor(float)' or inputs[0].shape != [1, 3, 416, 416]:
        raise ValueError('Unexpected input contract')
    return instance
