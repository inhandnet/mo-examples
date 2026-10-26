"""Mo62A offline zone-occupancy application with evidence and business events.

Stock-footage playback with an illustrative ROI, not a safety system, live camera
measurement, person-identification system, or claim of unsafe worker behavior.
"""
import argparse
import csv
import datetime
import json
from pathlib import Path
import platform
import time

import cv2
import numpy as np

from logic import Occupancy, inside_polygon
from model import detections, preprocess, session, sha256, write_json


def annotate(frame, people, polygon, state, timestamp, inference_ms, backend, credit):
    height, width = frame.shape[:2]
    color = (0, 180, 255) if state == 'occupied' else (190, 210, 30)
    points = np.array([[round(x * (width - 1)), round(y * (height - 1))] for x, y in polygon], dtype=np.int32)
    cv2.polylines(frame, [points], True, color, 3)
    for person in people:
        x1, y1, x2, y2 = [round(v) for v in person['box']]
        box_color = (0, 180, 255) if person['inside'] else (80, 230, 100)
        cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
        cv2.circle(frame, (round((x1 + x2) / 2), y2), 5, box_color, -1)
        cv2.putText(frame, f'person {person["score"]:.2f}', (x1, max(70, y1 - 7)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)
    cv2.rectangle(frame, (0, 0), (width, 60), (26, 31, 40), -1)
    cv2.putText(frame, f'Mo62A | YOLOX-tiny-lite | {backend.upper()} | DEMO ZONE: {state.upper()}',
                (16, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (235, 240, 245), 2)
    inside = sum(person['inside'] for person in people)
    cv2.putText(frame, f'Video {timestamp:.2f}s  |  inside {inside}  |  inference call {inference_ms:.1f} ms',
                (16, 49), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (180, 200, 220), 1)
    cv2.rectangle(frame, (0, height - 30), (width, height), (26, 31, 40), -1)
    cv2.putText(frame, credit,
                (12, height - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (220, 225, 235), 1)
    return frame


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bundle', required=True, type=Path)
    parser.add_argument('--video', required=True, type=Path)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--backend', choices=('cpu', 'tidl'), default='tidl')
    parser.add_argument('--stride', type=int, default=1)
    parser.add_argument('--credit', required=True, help='Visible ASCII source/creator/license credit; keep the full source notice with the output')
    args = parser.parse_args()
    if args.stride < 1:
        parser.error('--stride must be positive')
    config = json.loads(args.config.read_text())
    occupancy = Occupancy(config)
    runtime = session(args.bundle.resolve(), args.backend)
    args.output.mkdir(parents=True, exist_ok=False)
    capture = cv2.VideoCapture(str(args.video))
    writer = None
    latencies, frame_count, events = [], 0, []
    failure = None
    fps = 0
    started = time.perf_counter()
    cpu_started = time.process_time()
    created = datetime.datetime.now(datetime.timezone.utc).isoformat()
    source_hash = sha256(args.video)
    try:
        if not capture.isOpened():
            raise RuntimeError('Cannot open input video')
        fps = capture.get(cv2.CAP_PROP_FPS)
        total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        if not np.isfinite(fps) or fps <= 0 or total < 1:
            raise ValueError('Expected a constant-frame-rate file with valid metadata')
        decoder = capture.getBackendName()
        with (args.output / 'events.jsonl').open('x') as event_file, \
             (args.output / 'frames.jsonl').open('x') as frame_file, \
             (args.output / 'events.csv').open('x', newline='') as csv_file:
            table = csv.DictWriter(csv_file, fieldnames=['event', 'zone_id', 'source_time_s', 'detected_since_s', 'people_inside', 'occupancy_duration_s'])
            table.writeheader()
            index = 0
            while True:
                ok, frame = capture.read()
                if not ok:
                    if index < total:
                        raise RuntimeError('Decoder ended before the declared frame count')
                    break
                current = index
                index += 1
                if current % args.stride:
                    continue
                if writer is None:
                    height, width = frame.shape[:2]
                    writer = cv2.VideoWriter(str(args.output / 'annotated.avi'), cv2.VideoWriter_fourcc(*'MJPG'),
                                             fps / args.stride, (width, height))
                    if not writer.isOpened():
                        raise RuntimeError('MJPEG output encoder is unavailable')
                tensor, scales = preprocess(frame)
                before = time.perf_counter()
                outputs = runtime.run(None, {runtime.get_inputs()[0].name: tensor})
                elapsed = (time.perf_counter() - before) * 1000
                latencies.append(elapsed)
                people = [d for d in detections(outputs, frame.shape, scales, config['score_threshold']) if d['label'] == 0]
                height, width = frame.shape[:2]
                for person in people:
                    x1, _, x2, y2 = person['box']
                    point = ((x1 + x2) / 2 / (width - 1), y2 / (height - 1))
                    person['inside'] = inside_polygon(point, config['polygon'])
                timestamp = current / fps
                event = occupancy.update(timestamp, sum(person['inside'] for person in people))
                record = {'frame': current, 'source_time_s': timestamp, 'state': occupancy.state,
                          'inference_ms': elapsed, 'people': people}
                frame_file.write(json.dumps(record, allow_nan=False) + '\n')
                rendered = annotate(frame, people, config['polygon'], occupancy.state, timestamp, elapsed, args.backend, args.credit)
                writer.write(rendered)
                frame_count += 1
                if frame_count == 1:
                    if not cv2.imwrite(str(args.output / 'first-frame.jpg'), rendered):
                        raise RuntimeError('Cannot write first-frame evidence')
                if event:
                    events.append(event)
                    event_file.write(json.dumps(event, allow_nan=False) + '\n')
                    event_file.flush()
                    table.writerow(event)
                    csv_file.flush()
                    if not cv2.imwrite(str(args.output / f'event-{len(events):04d}.jpg'), rendered):
                        raise RuntimeError('Cannot write event evidence')
                    print(json.dumps(event), flush=True)
                if frame_count % 50 == 0:
                    print(f'Processed {frame_count} frames; source={timestamp:.2f}s; state={occupancy.state}', flush=True)
            if not frame_count:
                raise RuntimeError('No frames processed')
    except BaseException as error:
        failure = error
    finally:
        capture.release()
        if writer is not None:
            writer.release()
        elapsed = time.perf_counter() - started
        summary = {'completed': failure is None, 'failure_type': type(failure).__name__ if failure else None,
                   'started_utc': created, 'backend': args.backend, 'machine': platform.machine(),
                   'python': platform.python_version(), 'opencv': cv2.__version__, 'numpy': np.__version__,
                   'input_sha256': source_hash, 'credit': args.credit, 'config': config, 'source_fps': fps,
                   'stride': args.stride, 'processed_frames': frame_count, 'elapsed_seconds': elapsed,
                   'processed_fps': frame_count / elapsed if elapsed else 0,
                   'process_cpu_seconds': time.process_time() - cpu_started,
                   'inference_ms': {'mean': float(np.mean(latencies)), 'p95': float(np.percentile(latencies, 95))} if latencies else None,
                   'last_zone_state': occupancy.state, 'events': events,
                   'measurement_scope': 'Offline decode, preprocessing, synchronous inference, zone rules, drawing and MJPEG/file output; excludes session creation. No realtime pacing or power measurement.',
                   'limitations': 'Illustrative stock-footage ROI; no identity tracking, labeled accuracy claim or safety certification. EOF is not a zone-clear event.'}
        if 'decoder' in locals():
            summary['opencv_capture_backend'] = decoder
        write_json(args.output / 'summary.json', summary)
        print(json.dumps(summary, indent=2), flush=True)
    if failure:
        raise failure


if __name__ == '__main__':
    main()
