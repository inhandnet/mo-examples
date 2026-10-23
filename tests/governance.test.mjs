import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync, mkdirSync, readFileSync, writeFileSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {dirname, join} from 'node:path';
import {spawnSync} from 'node:child_process';
import {checkMessage, parseVersion, policy} from '../scripts/lib/policy.mjs';
import {eventSelection} from '../scripts/check-ci.mjs';

test('English one-line commits work; malformed and CI-bypassing messages fail', () => {
  for (const text of ['docs: explain the tested setup', 'fix(download)!: change the archive name\n\nExplain the compatibility impact.']) assert.deepEqual(checkMessage(text), []);
  for (const text of ['fix: 中文', 'fix: Capitalized', 'fix: period.', 'fix: '+ 'a'.repeat(70), 'fixup! docs: test',
    'fix: test\nbody', 'fix: test\n\nCo-Authored-By: example', 'fix: test [skip actions]', 'fix: test [no ci]',
    'fix: test\n\nskip-checks: true', 'fix: test\n\nAddress: 10.1.2.3']) assert.ok(checkMessage(text).length, text);
});

test('all supported tag names parse and ambiguous versions fail', () => {
  for (const tag of ['V0.0.0','V1.2.3','V1.2.3-rc1','V1.2.3-rc123']) assert.doesNotThrow(()=>parseVersion(tag));
  for (const tag of ['v1.2.3','V01.2.3','V1.02.3','V1.2.03','V1.2.3-rc0','V1.2.3-rc01','release','V1.2.3-beta1']) assert.throws(()=>parseVersion(tag));
});

test('CI validates PR data and fails closed on missing or malformed event refs', () => {
  const a='a'.repeat(40), b='b'.repeat(40);
  const pr={pull_request:{title:'docs: update the guide',base:{sha:a},head:{sha:b}}};
  assert.equal(eventSelection(pr,'pull_request'),`${a}..${b}`);
  pr.pull_request.title='bad title';assert.throws(()=>eventSelection(pr,'pull_request'),/PR title/);
  assert.throws(()=>eventSelection({before:a,after:'HEAD; echo injected'},'push'),/SHA/);
  assert.throws(()=>eventSelection({before:a,after:'0'.repeat(40)},'push'),/deleted/);
  assert.throws(()=>eventSelection({},'unknown'),/Unsupported/);
});

test('the hook entry point rejects invalid messages and invalid git ranges', () => {
  const dir=mkdtempSync(join(tmpdir(),'mo-policy-'));
  try {
    // Build the history this test needs instead of depending on checkout depth
    // or remote refs supplied by a developer's clone or a CI merge checkout.
    for (const file of ['.githooks/commit-msg', 'scripts/check-commit-msg.sh', 'scripts/check-commit-msg.mjs', 'scripts/lib/policy.mjs']) {
      mkdirSync(dirname(join(dir,file)), {recursive:true});
      writeFileSync(join(dir,file),readFileSync(new URL(`../${file}`,import.meta.url)),{mode:0o755});
    }
    const run=(command,args)=>spawnSync(command,args,{cwd:dir,encoding:'utf8'});
    const git=(...args)=>{
      const result=run('git',args);
      assert.equal(result.status,0,result.stderr);
      return result.stdout.trim();
    };
    git('init','--quiet');
    git('config','user.name','Policy test');
    git('config','user.email','policy@example.invalid');
    git('config','commit.gpgsign','false');
    git('commit','--allow-empty','-m','Legacy subject before the policy');
    const legacyBoundary=git('rev-parse','HEAD');
    mkdirSync(join(dir,'config'));
    writeFileSync(join(dir,'config/repository-policy.json'),JSON.stringify({...policy,legacyBoundary}));
    git('update-ref','refs/remotes/origin/master',legacyBoundary);
    git('commit','--allow-empty','-m','docs: add checked content');

    const message=join(dir,'message');writeFileSync(message,'docs: test hook feedback\n');
    const valid=run('bash',['.githooks/commit-msg',message]);
    assert.equal(valid.status,0,valid.stderr);
    writeFileSync(message,'not a conventional commit\n');
    assert.equal(run('bash',['.githooks/commit-msg',message]).status,1);
    assert.equal(run('node',['scripts/check-commit-msg.mjs','--revs','missing-revision..HEAD']).status,1);
    const range=['scripts/check-commit-msg.mjs','--revs','HEAD','--not','origin/master'];
    const accepted=run('node',range);
    assert.equal(accepted.status,0,accepted.stderr);
    git('commit','--allow-empty','-m','Invalid new subject');
    const rejected=run('node',range);
    assert.equal(rejected.status,1,rejected.stderr);
    assert.match(rejected.stderr,/English Conventional Commit/);
  } finally {rmSync(dir,{recursive:true,force:true});}
});
