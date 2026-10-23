import test from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync, spawnSync} from 'node:child_process';
import {mkdtempSync, mkdirSync, writeFileSync, readFileSync, rmSync} from 'node:fs';
import {join, resolve} from 'node:path';
import {tmpdir} from 'node:os';

const consoleScript = resolve('r5f/mcu-console/mcu-console.py');
const reloadScript = resolve('r5f/mcu-console/reload-cycle.sh');
const videoScript = resolve('ai/npu-demo/run-video-demo.sh');

test('MCU console rejects invalid byte lengths and transport failures', () => {
  execFileSync('python3', ['-B', '-c', `
import importlib.util, unittest.mock as m, sys
spec=importlib.util.spec_from_file_location('console',sys.argv[1]); c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
with m.patch.object(c.os,'write',return_value=4) as write, m.patch.object(c.select,'select',return_value=([4],[],[])), m.patch.object(c.os,'read',return_value=b'ok\\n'):
    assert c.run(4,'help') == 'ok'
    for text in ('', 'x'*497, '界'*166):
        try: c.run(4,text)
        except ValueError: pass
        else: raise AssertionError('invalid length accepted')
    assert write.call_count == 1
with m.patch.object(c.os,'write',return_value=4), m.patch.object(c.select,'select',return_value=([],[],[])):
    try: c.run(4,'help')
    except TimeoutError: pass
    else: raise AssertionError('timeout reported as success')
with m.patch.object(c.os,'write',return_value=1):
    try: c.run(4,'help')
    except OSError: pass
    else: raise AssertionError('short write accepted')
`, consoleScript]);
  const timeout = spawnSync('python3', ['-B', '-c', `
import glob,os,select,runpy,sys
script=sys.argv[1];sys.argv=[script,'help']
glob.glob=lambda pattern: ['/tmp/79000000.r5f/rpmsg0']
os.open=lambda *args: 99
os.close=lambda fd: None
os.write=lambda fd,payload: len(payload)
select.select=lambda *args: ([],[],[])
runpy.run_path(script,run_name='__main__')
`, consoleScript], {encoding:'utf8'});
  assert.equal(timeout.status, 1);
  assert.match(timeout.stderr, /no reply/);
});

function reloadFixture(t) {
  const dir=mkdtempSync(join(tmpdir(),'mo reload '));t.after(()=>rmSync(dir,{recursive:true,force:true}));
  const core=join(dir,'rproc/remoteproc1'), traces=join(dir,'trace/remoteproc1');
  for (const p of [core,traces,join(dir,'firmware')]) mkdirSync(p,{recursive:true});
  writeFileSync(join(core,'name'),'79000000.r5f\n');writeFileSync(join(core,'state'),'running\n');
  writeFileSync(join(core,'firmware'),'original.out');writeFileSync(join(dir,'firmware/test.out'),'firmware');
  writeFileSync(join(traces,'trace0'),'end point 14');writeFileSync(join(dir,'echo tool'),'#!/bin/sh\nexit 0\n',{mode:0o755});
  const env={...process.env,MO_RPROC_ROOT:join(dir,'rproc'),MO_TRACE_ROOT:join(dir,'trace'),MO_FIRMWARE_ROOT:join(dir,'firmware'),MO_ECHO_TOOL:join(dir,'echo tool')};
  return {dir,core,env,run:(...args)=>spawnSync('bash',[reloadScript,...args],{env,encoding:'utf8'})};
}

test('reload helper validates cycles and unique MCU before changing state', t => {
  const f=reloadFixture(t);
  for (const args of [[],['test.out','0'],['test.out','-1'],['../test.out','2'],['missing.out','2'],['test.out','1001']]) assert.notEqual(f.run(...args).status,0);
  assert.equal(readFileSync(join(f.core,'state'),'utf8'),'running\n');
  mkdirSync(join(f.dir,'rproc/remoteproc9'));writeFileSync(join(f.dir,'rproc/remoteproc9/name'),'79000000.r5f\n');
  assert.match(f.run('test.out','2').stderr,/exactly one/);
  assert.equal(readFileSync(join(f.core,'state'),'utf8'),'running\n');
});

test('reload helper stops on firmware write or echo failure and handles paths with spaces', t => {
  const f=reloadFixture(t);
  assert.match(f.run('test.out','2').stdout,/PASS 2\/2/);
  writeFileSync(join(f.core,'state'),'running\n');
  rmSync(join(f.core,'firmware'));mkdirSync(join(f.core,'firmware'));
  const failure=f.run('test.out','2');assert.notEqual(failure.status,0);assert.match(failure.stderr,/FIRMWARE WRITE FAILED/);
  assert.equal(readFileSync(join(f.core,'state'),'utf8'),'stop\n');assert.doesNotMatch(failure.stdout,/PASS/);
  rmSync(join(f.core,'firmware'),{recursive:true});writeFileSync(join(f.core,'firmware'),'original.out');writeFileSync(join(f.core,'state'),'running\n');
  writeFileSync(join(f.dir,'echo tool'),'#!/bin/sh\nexit 4\n',{mode:0o755});
  const echo=f.run('test.out','1');assert.notEqual(echo.status,0);assert.match(echo.stderr,/echo FAILED/);assert.doesNotMatch(echo.stdout,/PASS/);
});

test('video cleanup reports recovery failures and preserves original errors', () => {
  const run = (status, reset, desktop) => spawnSync('bash',['-c',`
source "$1"
test_reset=$3
test_desktop=$4
reset_c7x() { return "$test_reset"; }
systemctl() { return "$test_desktop"; }
restore_desktop=true
cleanup "$2"
`, 'test',videoScript,String(status),String(reset),String(desktop)],{encoding:'utf8'});
  assert.equal(run(0,0,0).status,0);
  assert.equal(run(0,1,0).status,1);
  assert.equal(run(0,0,1).status,1);
  const failed=run(42,1,1);assert.equal(failed.status,42);assert.match(failed.stderr,/recovery failed/);assert.doesNotMatch(failed.stdout,/restored/);
});

test('accelerator reset fails if reading or writing the state fails, even inside a condition', t => {
  const dir=mkdtempSync(join(tmpdir(),'mo-reset-'));t.after(()=>rmSync(dir,{recursive:true,force:true}));
  const result=spawnSync('bash',['-c',`
source "$1"
rproc="$2"
cat() { echo running; }
sleep() { :; }
if reset_c7x; then exit 0; else exit 7; fi
`, 'test',videoScript,dir],{encoding:'utf8'});
  assert.equal(result.status,7);
});
