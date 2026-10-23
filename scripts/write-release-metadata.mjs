import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {validateOrdinaryVersion} from './validate-release-version.mjs';
const tag=process.argv[2];validateOrdinaryVersion(tag);
const config=JSON.parse(fs.readFileSync('config/release-catalog.json','utf8'));
const hash=file=>createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const name=config.repository.split('/')[1],archive=`${name}-${tag}.tar.gz`;
const commit=execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim();
const contract=JSON.parse(fs.readFileSync('validation/contract-lock.json','utf8'));
const data={schema_version:1,kind:'business-source',repository:config.repository,version:tag,commit,
  contract:{kind:'catalogs',version:contract.contract_version,commit:contract.commit},
  catalogs:config.catalogs.map(path=>({path,sha256:hash(path)})),
  archives:[{file:archive,bytes:fs.statSync(`dist/${archive}`).size,sha256:hash(`dist/${archive}`)}]};
fs.writeFileSync('dist/release.json',JSON.stringify(data,null,2)+'\n');
