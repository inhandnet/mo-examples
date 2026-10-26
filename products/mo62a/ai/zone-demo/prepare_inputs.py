"""Extract reproducible representative frames; use separate clips for calibration/evaluation."""
import argparse
from pathlib import Path

import cv2
import numpy as np

from model import sha256, write_json

parser = argparse.ArgumentParser()
parser.add_argument('--video', required=True, type=Path)
parser.add_argument('--output', required=True, type=Path)
parser.add_argument('--count', type=int, default=32)
args = parser.parse_args()
if args.count < 1:
    parser.error('--count must be positive')
capture = cv2.VideoCapture(str(args.video))
try:
    if not capture.isOpened():
        raise RuntimeError('Cannot open input video')
    total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = capture.get(cv2.CAP_PROP_FPS)
    if total < args.count or not np.isfinite(fps) or fps <= 0:
        raise ValueError('Insufficient frames or invalid video metadata')
    indices = set(np.linspace(0, total - 1, args.count).astype(int).tolist())
    args.output.mkdir(parents=True, exist_ok=False)
    manifest = {'source_sha256': sha256(args.video), 'source_fps': fps,
                'source_frames': total, 'selection': 'uniform frame indices', 'frames': []}
    for index in range(total):
        ok, frame = capture.read()
        if not ok:
            raise RuntimeError('Video ended before declared frame count')
        if index in indices:
            name = f'frame-{index:06d}.png'
            path = args.output / name
            if not cv2.imwrite(str(path), frame):
                raise RuntimeError('Cannot write extracted frame')
            manifest['frames'].append({'file': name, 'index': index, 'time_s': index / fps, 'sha256': sha256(path)})
    write_json(args.output / 'inputs.json', manifest)
    print(f'Extracted {len(manifest["frames"])} frames from {total} frames at {fps:g} fps.')
finally:
    capture.release()
