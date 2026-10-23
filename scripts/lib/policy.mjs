import {readFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';

export const policy = JSON.parse(readFileSync(new URL('../../config/repository-policy.json', import.meta.url)));
export const git = (...args) => execFileSync('git', args, {encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe']}).trim();
export const headerPattern = new RegExp(`^(${policy.types.join('|')})(?:\\(([a-z0-9][a-z0-9-]*(?:/[a-z0-9][a-z0-9-]*)*)\\))?(!)?: ([a-z].*[^.]|[a-z])$`);
export const tagPattern = new RegExp(policy.tagPattern);

export function parseVersion(tag) {
  const match = tagPattern.exec(tag);
  if (!match) throw new Error('Use VX.Y.Z or VX.Y.Z-rcN; uppercase V, no leading zeros, N starts at 1.');
  return {major: BigInt(match[1]), minor: BigInt(match[2]), patch: BigInt(match[3]), rc: match[4] ? BigInt(match[4]) : null};
}

export function compareVersions(a, b) {
  const x = parseVersion(a), y = parseVersion(b);
  for (const key of ['major', 'minor', 'patch']) {
    if (x[key] !== y[key]) return x[key] < y[key] ? -1 : 1;
  }
  if (x.rc === y.rc) return 0;
  if (x.rc === null) return 1;
  if (y.rc === null) return -1;
  return x.rc < y.rc ? -1 : 1;
}

export function cleanMessage(message) {
  return message.replace(/\r\n/g, '\n').split('\n# ------------------------ >8 ------------------------')[0]
    .split('\n').filter((line) => !line.startsWith('#')).map((line) => line.trimEnd()).join('\n').trim();
}

export function checkMessage(message, {titleOnly = false} = {}) {
  const text = cleanMessage(message);
  const lines = text.split('\n');
  const errors = [];
  if (!headerPattern.test(lines[0]) || /[^\x20-\x7e]/.test(lines[0])) errors.push('Use an English Conventional Commit title, e.g. fix(site): repair the download link.');
  if ([...lines[0]].length > policy.headerMaxLength) errors.push('The title must be at most 72 characters.');
  if (/\[(?:skip ci|ci skip|no ci|skip actions|actions skip)\]|^skip-checks:\s*true/im.test(message)) errors.push('Do not skip required CI checks.');
  if (/^Co-Authored-By:/im.test(text)) errors.push('Do not add Co-Authored-By trailers.');
  if (/(^|[^0-9])(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})([^0-9]|$)|inhand\.design|gitlab\.inhand/i.test(message)) errors.push('Remove private IP addresses and internal domains from the message.');
  if (titleOnly) {
    if (lines.length !== 1) errors.push('A title must contain exactly one line.');
    return errors;
  }
  if (lines.length > 1 && lines[1] !== '') errors.push('Leave a blank line after the title.');
  for (const [i, line] of lines.entries()) {
    if (i > 1 && [...line].length > 72 && !/https?:\/\/|^ {4}|^\t/.test(line)) errors.push(`Wrap line ${i + 1} at 72 characters.`);
  }
  // A short English title is sufficient. Historical Message blocks remain
  // readable by the changelog generator; new commits need no bilingual body.
  return errors;
}
