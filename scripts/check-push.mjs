#!/usr/bin/env node
import {readFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {policy} from './lib/policy.mjs';

try {
  const remote = process.argv[2];
  for (const line of readFileSync(0, 'utf8').trim().split('\n').filter(Boolean)) {
    const [localRef, localSha, remoteRef, remoteSha] = line.split(' ');
    if (remoteRef.startsWith('refs/tags/')) {
      continue; // Tag permissions are enforced by GitHub; validation runs in CI.
    } else if (remoteRef === `refs/heads/${policy.defaultBranch}`) {
      throw new Error('master only accepts pull requests.');
    } else if (!/^0+$/.test(localSha)) {
      const range = /^0+$/.test(remoteSha) ? [localSha, '--not', `--remotes=${remote}`] : [`${remoteSha}..${localSha}`];
      execFileSync('node', ['scripts/check-commit-msg.mjs', '--revs', ...range], {stdio: 'inherit'});
    }
  }
} catch (error) { console.error(`Push rejected: ${error.message}`); process.exitCode = 1; }
