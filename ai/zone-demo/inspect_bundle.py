"""Inspect a complete versioned model bundle without creating an inference session."""
import argparse
from pathlib import Path

from model import verify_bundle

parser = argparse.ArgumentParser()
parser.add_argument('--bundle', required=True, type=Path)
args = parser.parse_args()
record = verify_bundle(args.bundle.resolve())
print('Bundle file checksums: PASS')
print('Model:', record['model_id'], '| SoC:', record['soc'], '| TIDL:', record['tidl_release'])
print('Calibration frames:', len(record['calibration']['frames']))
print('Calibration source:', record['calibration']['source_sha256'])
print('Iterations:', record['quantization']['iterations'])
print('Base precision:', record['quantization']['base_bits'], 'bits; selected 16-bit outputs:', record['quantization']['selected_16bit_outputs'])
print('Files:', len(record['files']))
print('This checks the bundle, not task accuracy or target stability. Review compile.log separately.')
