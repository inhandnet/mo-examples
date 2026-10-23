import test from 'node:test';
import assert from 'node:assert/strict';
import {validateOrdinaryVersion} from '../scripts/validate-release-version.mjs';
test('new business releases accept ordinary versions and reject RCs and ambiguous tags',()=>{
  for(const value of ['V0.0.0','V1.0.2','V12.34.56'])assert.doesNotThrow(()=>validateOrdinaryVersion(value));
  for(const value of ['V1.0.2-rc1','v1.0.2','V01.0.2','V1.0.2-beta1','release'])assert.throws(()=>validateOrdinaryVersion(value));
});
