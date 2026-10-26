"""Match CPU and quantized person detections; this is agreement, not ground truth."""
import argparse
import json
from pathlib import Path

from model import write_json


def iou(a, b):
    left, top = max(a[0], b[0]), max(a[1], b[1])
    right, bottom = min(a[2], b[2]), min(a[3], b[3])
    intersection = max(0, right - left) * max(0, bottom - top)
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - intersection
    return intersection / union if union else 0


def compare(cpu, quantized):
    if cpu['source_sha256'] != quantized['source_sha256']:
        raise ValueError('Inputs differ')
    reference = {s['file']: s for s in cpu['samples']}
    actual = {s['file']: s for s in quantized['samples']}
    if set(reference) != set(actual):
        raise ValueError('Frame sets differ')
    rows = []
    for name, sample in reference.items():
        other = actual[name]
        if sample['input_sha256'] != other['input_sha256']:
            raise ValueError('Frame bytes differ')
        a = [d for d in sample['detections'] if d['label'] == 0]
        b = [d for d in other['detections'] if d['label'] == 0]
        candidates = sorted(((iou(x['box'], y['box']), i, j) for i, x in enumerate(a) for j, y in enumerate(b)), reverse=True)
        used_a, used_b, matches = set(), set(), []
        for overlap, i, j in candidates:
            if overlap >= 0.5 and i not in used_a and j not in used_b:
                used_a.add(i)
                used_b.add(j)
                matches.append({'iou': overlap, 'score_delta': b[j]['score'] - a[i]['score']})
        rows.append({'file': name, 'cpu_person_count': len(a), 'quantized_person_count': len(b), 'matches_iou_0_5': matches,
                     'unmatched_cpu': len(a) - len(matches), 'unmatched_quantized': len(b) - len(matches)})
    return {'scope': 'Greedy same-class box agreement at score >=0.4 and IoU >=0.5, not labeled accuracy or mAP.', 'frames': rows}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cpu', required=True, type=Path)
    parser.add_argument('--quantized', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    report = compare(json.loads(args.cpu.read_text()), json.loads(args.quantized.read_text()))
    write_json(args.output, report)
    print(json.dumps(report, indent=2))
