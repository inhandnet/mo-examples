import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
test('standalone application keeps the exact pinned model contract',()=>{
 const lock=JSON.parse(fs.readFileSync('products/mo62a/dependencies/model-contract.json','utf8'));
 assert.equal(lock.repository,'inhandnet/mo-models');assert.match(lock.commit,/^[a-f0-9]{40}$/);
 assert.deepEqual(lock.files.map(f=>[f.source,f.target]),[['products/mo62a/compile/zone-demo/model.py','products/mo62a/ai/zone-demo/model.py']]);
 for(const file of lock.files)assert.equal(createHash('sha256').update(fs.readFileSync(file.target)).digest('hex'),file.sha256);
});
