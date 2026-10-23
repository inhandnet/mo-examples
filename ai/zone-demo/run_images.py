"""Save raw tensors and decoded detections for reproducible host/target comparison."""
import argparse
import json
from pathlib import Path
import platform
import time

import cv2
import numpy as np

from model import detections, preprocess, session, sha256, write_json

parser = argparse.ArgumentParser()
parser.add_argument('--bundle', required=True, type=Path)
parser.add_argument('--images', required=True, type=Path)
parser.add_argument('--backend', choices=('cpu', 'tidl'), required=True)
parser.add_argument('--output', required=True, type=Path)
parser.add_argument('--compare', type=Path, help='Host TIDL output directory for an exact target comparison')
args = parser.parse_args()
manifest = json.loads((args.images / 'inputs.json').read_text())
args.output.mkdir(parents=True, exist_ok=False)
runtime = session(args.bundle.resolve(), args.backend)
report = {'backend': args.backend, 'machine': platform.machine(), 'python': platform.python_version(),
          'source_sha256': manifest['source_sha256'], 'samples': [],
          'scope': 'Output agreement, not labeled task accuracy; calls include runtime overhead'}
for frame in manifest['frames']:
    path = args.images / frame['file']
    if path.parent != args.images or sha256(path) != frame['sha256']:
        raise ValueError('Evaluation frame checksum/path failed')
    image = cv2.imread(str(path))
    tensor, scales = preprocess(image)
    started = time.perf_counter()
    outputs = runtime.run(None, {runtime.get_inputs()[0].name: tensor})
    elapsed = (time.perf_counter() - started) * 1000
    values = detections(outputs, image.shape, scales)
    name = Path(frame['file']).stem
    np.savez(args.output / (name + '.npz'), dets=outputs[0], labels=outputs[1])
    entry = {'file': frame['file'], 'input_sha256': frame['sha256'],
             'inference_ms': elapsed, 'detections': values}
    if args.compare:
        with np.load(args.compare / (name + '.npz'), allow_pickle=False) as reference:
            if not all(np.array_equal(reference[key], value) for key, value in zip(('dets', 'labels'), outputs)):
                raise ValueError('Target output differs from host TIDL: ' + name)
        entry['host_tidl_exact_match'] = True
    report['samples'].append(entry)
    print(name, len(values), 'detections', f'{elapsed:.3f} ms', flush=True)
write_json(args.output / 'results.json', report)
