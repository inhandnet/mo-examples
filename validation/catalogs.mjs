// Versioned, dependency-free business catalog checks shared with source CI.
import fs from 'node:fs';
import path from 'node:path';

export const catalogContractVersion = 1;
const sha256 = /^[a-f0-9]{64}$/;
const commit = /^[a-f0-9]{40}$/;
const ordinaryVersion = /^V(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/;
function need(value, location, message) { if (!value) throw Error(`${location}: ${message}`); }
function text(value, location) { need(typeof value === 'string' && value.trim(), location, 'non-empty string required'); }
function url(value, location) {
  let parsed;
  try { parsed = new URL(value); } catch { /* reported below */ }
  need(parsed?.protocol === 'https:' && !parsed.username && !parsed.password, location, 'HTTPS URL required');
}
function strings(value, location, {empty = false} = {}) {
  need(Array.isArray(value) && (empty || value.length), location, 'array of unique strings required');
  for (const item of value) text(item, location);
  need(new Set(value).size === value.length, location, 'duplicate value');
}
export function catalogFile(root, relative) {
  need(typeof relative === 'string' && relative && !relative.includes('\\') && !path.isAbsolute(relative) &&
    relative.split('/').every(part => part && part !== '..' && part !== '.'), relative, 'unsafe repository path');
  const file = path.join(root, relative);
  need(fs.existsSync(file) && fs.lstatSync(file).isFile() &&
    fs.realpathSync(file).startsWith(fs.realpathSync(root) + path.sep), relative, 'regular repository file required');
  return file;
}
const json = (root, name) => JSON.parse(fs.readFileSync(catalogFile(root, name), 'utf8'));
function evidence(value, location) {
  need(value && /^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(value.repository) && commit.test(value.commit), location, 'pinned evidence repository and commit required');
  text(value.path, `${location}.path`); text(value.scope, `${location}.scope`);
}

export function checkTools(root) {
  const data = json(root, 'toolchain/versions.json'), where = 'mo-tools/toolchain/versions.json';
  need(data.schema_version === 1, where, 'unsupported schema');
  const tidl = data.tidl_tools;
  need(tidl && commit.test(tidl.commit) && commit.test(tidl.compiler_commit), where, 'pinned TIDL commits required');
  text(tidl.tag, `${where}.tidl_tools.tag`);
  text(tidl.compiler_release, `${where}.tidl_tools.compiler_release`);
  for (const key of ['repository', 'compiler_archive', 'compatibility_table', 'target_update_script']) url(tidl[key], `${where}.tidl_tools.${key}`);
  need(sha256.test(tidl.compiler_archive_sha256), where, 'compiler archive SHA-256 required');
  for (const key of ['python', 'architecture', 'onnxruntime_tidl']) text(data.host?.[key], `${where}.host.${key}`);
  url(data.host.onnxruntime_tidl_wheel, `${where}.host.onnxruntime_tidl_wheel`);
  catalogFile(root, `toolchain/${data.host.setup}`);
  strings(data.target?.mo_images, `${where}.target.mo_images`);
  need(data.target.mo_images.every(v => ordinaryVersion.test(v)), where, 'ordinary image versions required');
  text(data.target.am62a_sdk_baseline, `${where}.target.am62a_sdk_baseline`);
  const r5f = data.r5f;
  need(r5f?.id === 'mcu-r5f' && r5f.board === 'mo-62a' && r5f.verification === 'documented', `${where}.r5f`, 'documented MCU toolchain required');
  strings(r5f.images, `${where}.r5f.images`);
  need(r5f.images.every(v => ordinaryVersion.test(v)), where, 'ordinary R5F image versions required');
  evidence(r5f.evidence, `${where}.r5f.evidence`);
  need(r5f.host?.os === 'Linux' && r5f.host.architecture === 'x86_64', `${where}.r5f.host`, 'documented Linux x86_64 host required');
  need(Array.isArray(r5f.components) && r5f.components.length === 3, `${where}.r5f`, 'SDK, compiler and SysConfig required');
  const names = new Set();
  for (const component of r5f.components) {
    text(component.name, where); text(component.version, where); text(component.file, where);
    need(!names.has(component.name), where, 'duplicate R5F component'); names.add(component.name);
    url(component.url, where);
    need(sha256.test(component.sha256) && Number.isSafeInteger(component.bytes) && component.bytes > 0, where, 'installer hash and size required');
  }
  need(data.linux_cross?.id === 'linux-a53' && data.linux_cross.verification === 'unverified' &&
    Array.isArray(data.linux_cross.components) && data.linux_cross.components.length === 0, `${where}.linux_cross`, 'unverified Linux combination must not advertise installers');
  return data;
}

export function checkModels(root) {
  const catalog = json(root, 'models.json'), compat = json(root, 'compat/compat.json');
  need(catalog.schema_version === 2 && Array.isArray(catalog.models) && catalog.models.length, 'mo-models/models.json', 'unsupported or empty model catalog');
  need(compat.schema_version === 1 && Array.isArray(compat.baselines) && compat.baselines.length, 'mo-models/compat/compat.json', 'unsupported or empty compatibility catalog');
  text(compat.source, 'mo-models/compat/compat.json.source');
  const seen = new Set();
  for (const model of catalog.models) {
    const where = `mo-models/models.json/${model.id}`;
    need(typeof model.id === 'string' && /^[a-zA-Z0-9_-]+$/.test(model.id) && !seen.has(model.id), where, 'unique safe model id required');
    seen.add(model.id);
    for (const key of ['task', 'runtime', 'input', 'tidl']) text(model[key], `${where}.${key}`);
    strings(model.boards, `${where}.boards`); strings(model.images, `${where}.images`);
    need(['inventory', 'tutorial', 'audited-latency'].includes(model.verification), where, 'unknown verification state');
    catalogFile(root, `models/${model.id}/README.md`);
    for (const section of ['source', 'upstream_artifact']) {
      const ref = model[section];
      if (!ref && section === 'upstream_artifact') continue;
      need(ref, `${where}.${section}`, 'source reference required');
      url(ref.url, `${where}.${section}.url`);
      need(fs.readFileSync(catalogFile(root, ref.link), 'utf8').trim() === ref.url, where, `${ref.link} differs from catalog URL`);
      if (section === 'source') need(sha256.test(ref.sha256), where, 'source model SHA-256 required');
    }
    need(model.artifact?.status === 'pending-hosting' && model.artifact.download_url === null, where, 'only pending-hosting artifacts are supported by this contract');
    if (model.verification === 'audited-latency') {
      need(model.latency?.record, where, 'audited latency needs a raw record');
      const record = json(root, model.latency.record);
      need(record.model === model.id && record.model_sha256 === model.source.sha256 &&
        Array.isArray(record.samples_ms) && record.samples_ms.length === record.runs &&
        record.samples_ms.every(x => Number.isFinite(x) && x >= 0), where, 'latency record does not match model or sample count');
      need(Number.isFinite(record.mean_ms) && Math.abs(record.mean_ms - record.samples_ms.reduce((a,b) => a+b, 0) / record.runs) < 0.000001, where, 'latency mean differs from raw samples');
      for (const key of ['mean_ms', 'median_ms', 'p95_ms']) need(Number.isFinite(model.latency[key]) && Math.abs(model.latency[key] - record[key]) <= 0.000500001, where, `catalog ${key} differs from raw record rounded to three decimals`);
      need(model.latency.runs === record.runs && model.latency.warmup === record.warmup, where, 'catalog sampling parameters differ from raw record');
    } else need(model.latency === null, where, 'latency requires audited-latency evidence');
    for (const board of model.boards) for (const image of model.images) {
      need(compat.baselines.some(b => b.board === board && b.image === image && b.tidl === model.tidl), where, `no matching compatibility baseline for ${board}/${image}/${model.tidl}`);
    }
  }
  return {catalog, compat};
}

export function checkExamples(root) {
  const data = json(root, 'examples.json');
  need(data.schema_version === 1 && Array.isArray(data.examples) && data.examples.length, 'mo-examples/examples.json', 'unsupported or empty examples catalog');
  const seen = new Set();
  for (const item of data.examples) {
    const where = `mo-examples/examples.json/${item.id}`;
    need(typeof item.id === 'string' && /^[a-z0-9-]+$/.test(item.id) && !seen.has(item.id), where, 'unique example id required'); seen.add(item.id);
    for (const key of ['title', 'category', 'notes']) text(item[key], `${where}.${key}`);
    need(item.verification === 'source-available', where, 'unknown verification state');
    need(typeof item.path === 'string' && item.readme === `${item.path}/README.md`, where, 'README must belong to the example directory');
    catalogFile(root, item.readme);
    strings(item.entrypoints, `${where}.entrypoints`);
    for (const file of item.entrypoints) {
      need(file.startsWith(`${item.path}/`) && !file.endsWith('.md'), where, 'entrypoint must be code in the example directory');
      catalogFile(root, file);
    }
    strings(item.boards, `${where}.boards`); strings(item.images, `${where}.images`); strings(item.models, `${where}.models`, {empty:true});
    need(/^\/docs\/[a-z0-9/-]+\/$/.test(item.documentation), where, 'documentation route required');
    if (item.toolchain) {
      need(item.toolchain.id === 'mcu-r5f' && Array.isArray(item.toolchain.components) && item.toolchain.components.length === 3, where, 'invalid R5F toolchain dependency');
      const names = new Set();
      for (const part of item.toolchain.components) {
        text(part.name, `${where}.toolchain.name`); text(part.version, `${where}.toolchain.version`);
        need(!names.has(part.name) && /^[a-f0-9]{64}$/.test(part.sha256), where, 'duplicate or unpinned R5F component'); names.add(part.name);
      }
    }
  }
  return data;
}

// Cross-repository compatibility is checked by developer against this exact set.
export function checkCatalogCombination({tools, models, compat, examples, board}, docsRoot) {
  for (const baseline of compat.baselines.filter(b => b.board === board.board && b.image === board.version)) {
    need(tools.target.mo_images.includes(baseline.image) && baseline.tidl === tools.tidl_tools.tag &&
      baseline.host_toolchain?.commit === tools.tidl_tools.commit && baseline.ti_onnxruntime === tools.host.onnxruntime_tidl,
    'composition/mo-tools+mo-models', `toolchain mismatch for ${baseline.board}/${baseline.image}`);
  }
  need(compat.baselines.some(b => b.board === board.board && b.image === board.version), 'composition/Mo62A+mo-models', 'selected image has no model compatibility baseline');
  const byId = new Map(models.models.map(m => [m.id, m]));
  for (const item of examples.examples) {
    if (item.toolchain) {
      const selected=tools.r5f;
      need(selected?.id===item.toolchain.id && item.boards.every(b=>b===selected.board) && item.images.every(v=>selected.images.includes(v)) &&
        item.toolchain.components.length===selected.components.length && item.toolchain.components.every(required=>selected.components.some(part=>part.name===required.name && part.version===required.version && part.sha256===required.sha256)),
        `composition/mo-examples/${item.id}`, 'R5F SDK/compiler/SysConfig combination differs from the example requirement');
    }
    for (const id of item.models) {
      const model = byId.get(id);
      need(model && item.boards.every(b => model.boards.includes(b)) && item.images.every(v => model.images.includes(v)),
        `composition/mo-examples/${item.id}`, `missing or incompatible model ${id}`);
    }
    const relative = item.documentation.replace(/^\/docs\//, '').replace(/\/$/, '');
    const candidates = [`docs/${relative}.mdx`, `docs/${relative}.md`, `docs/${relative}/index.mdx`];
    need(candidates.some(file => fs.existsSync(path.join(docsRoot, file))), `composition/mo-examples/${item.id}`, `missing documentation ${item.documentation}`);
  }
}
