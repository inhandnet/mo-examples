"""Download the fixed official model, retaining existing files only when hashes match."""
import argparse
from pathlib import Path
import urllib.request

from model import MODEL_NAME, MODEL_SHA256, META_SHA256, UPSTREAM, sha256

parser = argparse.ArgumentParser()
parser.add_argument('--bundle', required=True, type=Path)
args = parser.parse_args()
directory = args.bundle / 'model'
directory.mkdir(parents=True, exist_ok=True)
for suffix, expected in (('.onnx', MODEL_SHA256), ('.prototxt', META_SHA256)):
    target = directory / (MODEL_NAME + suffix)
    if target.exists():
        if sha256(target) != expected:
            raise RuntimeError('Existing file differs; refusing to replace ' + str(target))
    else:
        partial = target.with_suffix(target.suffix + '.part')
        with urllib.request.urlopen(UPSTREAM + target.name, timeout=60) as response, partial.open('xb') as output:
            while block := response.read(1024 * 1024):
                output.write(block)
        if sha256(partial) != expected:
            raise RuntimeError('Downloaded checksum failed; retained ' + str(partial))
        partial.rename(target)
    print(target.name, expected, flush=True)
