#!/usr/bin/env node
// Explicit maintainer action; the checked-in model copy is generated from Git.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
if(process.argv.length!==3)throw Error('Usage: node scripts/sync-model-contract.mjs /path/to/mo-models');
const sourceRoot=path.resolve(process.argv[2]);
const commit=execFileSync('git',['-C',sourceRoot,'rev-parse','HEAD'],{encoding:'utf8'}).trim();
const source='compile/zone-demo/model.py',target='ai/zone-demo/model.py';
const data=execFileSync('git',['-C',sourceRoot,'show',`${commit}:${source}`]);
if(!data.equals(fs.readFileSync(path.join(sourceRoot,source))))throw Error('Commit the authoritative model contract before exporting');
fs.writeFileSync(path.join(root,target),data);
fs.writeFileSync(path.join(root,'dependencies/model-contract.json'),JSON.stringify({schema_version:1,repository:'inhandnet/mo-models',commit,files:[{source,target,sha256:createHash('sha256').update(data).digest('hex')}]},null,2)+'\n');
console.log(`Exported model contract from ${commit}.`);
