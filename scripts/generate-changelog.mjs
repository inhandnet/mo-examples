#!/usr/bin/env node

import {execFileSync} from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import {compareVersions, tagPattern as versionPattern} from './lib/policy.mjs';

const headerPattern = /^(feat|fix|perf|docs|style|refactor|test|build|ci|chore|revert|sync)(?:\(([a-z0-9][a-z0-9/-]*)\))?(!)?: (.+)$/;
const sections = {
  feat: ['Features', '新功能'],
  fix: ['Fixes', '修复'],
  perf: ['Performance', '性能'],
  style: ['Style', '样式'],
  test: ['Tests', '测试'],
  build: ['Build', '构建'],
  revert: ['Reverts', '回退'],
  docs: ['Documentation', '文档'],
  refactor: ['Refactoring', '重构'],
  sync: ['Content synchronization', '内容同步'],
  ci: ['Continuous integration', '持续集成'],
  chore: ['Maintenance', '维护'],
};

export function parseCommitMessage(message, hash = '') {
  const lines = message.replace(/\r/g, '').trimEnd().split('\n');
  const header = lines[0] ?? '';
  const match = header.match(headerPattern);
  if (!match) throw new Error(`${hash || 'commit'} has an invalid conventional header`);
  // Prefer historical English release summaries, then the current subject.
  const block = message.match(/(?:^|\n)Message:\n[ \t]+en: ([^\n]+)/);
  const paragraph = message.match(/(?:^|\n)Message\.en:[ \t]*\n([^\n]+(?:\n(?!\n|Message\.)[^\n]+)*)/);
  const en = block?.[1]?.trim() || paragraph?.[1]?.replace(/\s+/g, ' ').trim() || match[4];
  return {
    hash, shortHash: hash.slice(0, 12), type: match[1], scope: match[2] ?? '',
    breaking: Boolean(match[3]) || /^BREAKING[ -]CHANGE:/m.test(message),
    subject: match[4], en, zh: en,
  };
}

export function renderChangelog(version, commits, language) {
  if (!versionPattern.test(version)) throw new Error('invalid release version');
  if (!['en', 'zh'].includes(language)) throw new Error('unsupported changelog language');
  const title = language === 'en' ? `# Mo examples ${version}` : `# Mo 示例 ${version}`;
  const intro = language === 'en'
    ? 'This changelog was generated from the English Git commit messages in this release.'
    : '本文件仅使用固定的中文标题与分类名称，变更条目保留英文。';
  const output = [title, '', intro, ''];
  const breaking = commits.filter(commit => commit.breaking);
  if (breaking.length) {
    output.push(language === 'en' ? '## Breaking changes' : '## 破坏性变更', '');
    for (const commit of breaking) output.push(formatEntry(commit, language));
    output.push('');
  }
  for (const type of Object.keys(sections)) {
    const matches = commits.filter(commit => commit.type === type && !commit.breaking);
    if (!matches.length) continue;
    output.push(`## ${sections[type][language === 'en' ? 0 : 1]}`, '');
    for (const commit of matches) output.push(formatEntry(commit, language));
    output.push('');
  }
  return `${output.join('\n').trimEnd()}\n`;
}

function formatEntry(commit, language) {
  const scope = commit.scope ? `**${commit.scope}:** ` : '';
  return `- ${scope}${commit[language]} (\`${commit.shortHash}\`)`;
}

function git(...args) {
  return execFileSync('git', args, {encoding: 'utf8'}).trim();
}

function readCommits(range) {
  const hashes = git('rev-list', '--reverse', '--no-merges', range).split('\n').filter(Boolean);
  return hashes.map(hash => parseCommitMessage(git('show', '-s', '--format=%B', hash), hash));
}

// A changelog always starts after the newest final release: release
// candidates describe everything since that release, and the final version
// repeats the candidate history instead of starting after the last candidate.
const finalVersionPattern = /^V(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/;

export function findPreviousVersion(version, head) {
  return git('tag', '--merged', head, '--list', 'V*', '--sort=-version:refname')
    .split('\n')
    .filter(tag => finalVersionPattern.test(tag) && compareVersions(tag, version) < 0)
    .sort(compareVersions).at(-1);
}

export function combinedReleaseNotes(english, chinese) {
  return [
    english.trimEnd(),
    '',
    '<details>',
    '<summary>简体中文</summary>',
    '',
    chinese.trimEnd(),
    '',
    '</details>',
    '',
  ].join('\n');
}

function parseArguments(args) {
  const values = {};
  for (let index = 0; index < args.length; index += 2) {
    if (!['--version', '--output', '--head'].includes(args[index]) || !args[index + 1]) {
      throw new Error('usage: generate-changelog.mjs --version VERSION --output DIR [--head REF]');
    }
    values[args[index].slice(2)] = args[index + 1];
  }
  if (!values.version || !values.output) throw new Error('version and output are required');
  return {...values, head: values.head ?? 'HEAD'};
}

function main() {
  const options = parseArguments(process.argv.slice(2));
  if (!versionPattern.test(options.version)) throw new Error('release version must match V<major>.<minor>.<patch> or V<major>.<minor>.<patch>-rc<n>');
  const previous = findPreviousVersion(options.version, options.head);
  const baseline = previous || fs.readFileSync(new URL('../release-notes/changelog-baseline', import.meta.url), 'utf8').trim();
  git('merge-base', '--is-ancestor', baseline, options.head);
  const commits = readCommits(`${baseline}..${options.head}`);
  if (!commits.length) throw new Error(`no release commits found after ${baseline}`);
  const english = renderChangelog(options.version, commits, 'en');
  const chinese = renderChangelog(options.version, commits, 'zh');
  fs.mkdirSync(options.output, {recursive: true});
  fs.writeFileSync(path.join(options.output, 'CHANGELOG.en.md'), english);
  fs.writeFileSync(path.join(options.output, 'CHANGELOG.zh-CN.md'), chinese);
  fs.writeFileSync(path.join(options.output, 'release-notes.md'), combinedReleaseNotes(english, chinese));
  process.stdout.write(`Generated changelogs for ${commits.length} commit(s) after ${previous || 'the baseline'}\n`);
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(new URL(import.meta.url).pathname)) {
  try {
    main();
  } catch (error) {
    process.stderr.write(`Changelog generation failed: ${error.message}\n`);
    process.exitCode = 1;
  }
}
