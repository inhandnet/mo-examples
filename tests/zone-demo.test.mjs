import test from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {readFile, readdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';

const root = new URL('../products/mo62a/ai/zone-demo/', import.meta.url);

test('zone rules validate coordinates, hysteresis and end-of-stream semantics', () => {
  const output = execFileSync('python3', ['-B', '-m', 'unittest', 'discover', '-s', root.pathname,
    '-p', 'test_*.py', '-v'], {encoding: 'utf8', env: {...process.env, PYTHONDONTWRITEBYTECODE: '1'}});
  assert.doesNotMatch(output, /FAILED|Traceback/);
});

test('licensed input clips retain their attribution and exact hashes', async () => {
  const sources = JSON.parse(await readFile(new URL('sources.json', root)));
  for (const source of sources.videos) {
    assert.equal(source.license, 'CC BY 4.0');
    assert.equal(source.creator, 'domdomegg');
    assert.equal(createHash('sha256').update(await readFile(new URL(source.prepared_file, root))).digest('hex'), source.prepared_sha256);
  }
});

test('published target evidence agrees with repeated runs and source contracts', async () => {
  const evidence = JSON.parse(await readFile(new URL('../products/mo62a/ai/zone-demo/evidence/zone-demo-evidence.json', import.meta.url)));
  assert.equal(evidence.bundle.model_id, 'od-8210');
  assert.equal(evidence.bundle.calibration.frames.length, 32);
  assert.equal(evidence.bundle.quantization.iterations, 3);
  assert.equal(evidence.board_images.samples.length, 8);
  assert.ok(evidence.board_images.samples.every(s => s.host_tidl_exact_match));
  assert.equal(evidence.video_runs.length, 3);
  const frames = (await readFile(new URL('../products/mo62a/ai/zone-demo/evidence/zone-demo-frames.jsonl', import.meta.url), 'utf8')).trim().split('\n').map(s => JSON.parse(s));
  assert.equal(frames.length, 611);
  for (const run of evidence.video_runs) {
    assert.equal(run.completed, true);
    assert.equal(run.machine, 'aarch64');
    assert.equal(run.backend, 'tidl');
    assert.equal(run.processed_frames, 611);
    assert.ok(Math.abs(run.processed_fps - 611 / run.elapsed_seconds) < 1e-9);
    assert.deepEqual(run.events, evidence.video_runs[0].events);
    assert.equal(run.input_sha256, evidence.evaluation.source_sha256);
  }
  const mean = frames.reduce((sum, row) => sum + row.inference_ms, 0) / frames.length;
  assert.ok(Math.abs(mean - evidence.video_runs[0].inference_ms.mean) < 1e-9);
  assert.match(evidence.cpu_quantized_agreement.scope, /not labeled accuracy/);
});

test('downloadable example retains explicit model and measurement contracts', async () => {
  const model = await readFile(new URL('model.py', root), 'utf8');
  const run = await readFile(new URL('run_video.py', root), 'utf8');
  assert.ok(model.includes('0..255 float RGB, not uint8 and not RGB/255'));
  assert.ok(model.includes('c9d2a3fdb21bed079a74029441d83235ddd910c82f1e7b9de5a2a5998bc3eeca'));
  assert.ok(run.includes('EOF is not a zone-clear event'));
  assert.ok(run.includes("exist_ok=False"));
  for (const name of await readdir(root, {recursive: true})) {
    assert.doesNotMatch(name, /__pycache__|\.pyc$/);
    if (/\.(py|json|md|txt)$/.test(name)) {
      assert.doesNotMatch(await readFile(new URL(name, root), 'utf8'), /10\.5\.\d+\.\d+|user_password|password=/i);
    }
  }
});
