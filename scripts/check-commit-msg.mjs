#!/usr/bin/env node
import {readFileSync} from 'node:fs';
import {checkMessage, git, policy} from './lib/policy.mjs';

const [mode, ...args] = process.argv.slice(2);
try {
  let entries;
  if (mode === '--file' || mode === '--title') {
    if (!args[0]) throw new Error('A message file is required.');
    entries = [['message', readFileSync(args[0], 'utf8')]];
  } else if (mode === '--revs') {
    const revs = args;
    if (!revs.length) throw new Error('A revision range is required.');
    // Keep legacy exclusion separate: another --not would toggle an existing
    // --not from pre-push and accidentally include old history.
    const legacy = new Set(git('rev-list', policy.legacyBoundary).split('\n'));
    entries = git('rev-list', '--no-merges', '--reverse', ...revs).split('\n').filter(sha => sha && !legacy.has(sha))
      .map((sha) => [sha.slice(0, 12), git('show', '-s', '--format=%B', sha)]);
  } else throw new Error('Usage: check-commit-msg.sh --file <file> | --title <file> | --revs <range>');
  let failed = false;
  for (const [label, message] of entries) {
    const errors = checkMessage(message, {titleOnly: mode === '--title'});
    if (errors.length) { failed = true; console.error(`${label}:\n${errors.map((error) => `  - ${error}`).join('\n')}`); }
  }
  if (failed) process.exitCode = 1;
} catch (error) { console.error(`Commit policy: ${error.message}`); process.exitCode = 1; }
