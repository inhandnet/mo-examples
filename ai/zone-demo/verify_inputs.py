"""Check the prepared, attributed tutorial inputs before selecting frames."""
import json
from pathlib import Path

from model import sha256

root = Path(__file__).resolve().parent
record = json.loads((root / 'sources.json').read_text())
for source in record['videos']:
    path = (root / source['prepared_file']).resolve()
    if not path.is_relative_to(root) or sha256(path) != source['prepared_sha256']:
        raise ValueError('Input checksum/path failed: ' + source['prepared_file'])
    print(source['prepared_file'], source['prepared_sha256'], 'PASS')
print('Keep SOURCE.txt with the inputs and result media; copyright permission is not a blanket rights warranty.')
