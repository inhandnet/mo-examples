#!/usr/bin/env node
import {readFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {pathToFileURL} from 'node:url';
import {checkMessage, policy} from './lib/policy.mjs';

// Read event data as data, never interpolate PR text into shell source.
export function eventSelection(event, name) {
  const sha = value => {
    if (!/^[a-f0-9]{40}$/.test(value ?? '')) throw new Error('Missing or invalid event commit SHA.');
    return value;
  };
  if (name === 'pull_request') {
    const pr = event.pull_request;
    const errors = checkMessage(pr?.title ?? '', {titleOnly: true});
    if (errors.length) throw new Error(`PR title: ${errors.join(' ')}`);
    return `${sha(pr.base.sha)}..${sha(pr.head.sha)}`;
  }
  if (name === 'push') {
    const before = sha(event.before), after = sha(event.after);
    if (/^0+$/.test(after)) throw new Error('The default branch must not be deleted.');
    return `${/^0+$/.test(before) ? policy.legacyBoundary : before}..${after}`;
  }
  throw new Error(`Unsupported policy event: ${name}`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    const event = JSON.parse(readFileSync(process.env.GITHUB_EVENT_PATH, 'utf8'));
    execFileSync('node', ['scripts/check-commit-msg.mjs', '--revs', eventSelection(event, process.env.GITHUB_EVENT_NAME)], {stdio: 'inherit'});
  } catch (error) {
    console.error(`Commit policy: ${error.message}`);
    process.exitCode = 1;
  }
}
