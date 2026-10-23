import {pathToFileURL} from 'node:url';
import {parseVersion} from './lib/policy.mjs';
export function validateOrdinaryVersion(value) {
  const version=parseVersion(value);
  if(version.rc!==null)throw Error('Business repositories publish ordinary VX.Y.Z versions; website RCs belong to developer.');
  return version;
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href) {
  try{validateOrdinaryVersion(process.argv[2]);console.log(`Validated ordinary version ${process.argv[2]}.`);}
  catch(error){console.error(error.message);process.exitCode=1;}
}
