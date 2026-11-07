// Runs the golden corpus against both canonical artifacts, comparing responses byte for byte
// (docs/spec/07-portable-core.md §7.11). The classic script runs in a hermetic realm, with every
// case in a seeded random order inside one long-lived realm, to catch state leaking between calls.
// Works the same under Node and Bun.

import { readFileSync, readdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createHermeticKernel } from './hermetic.mjs';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const corpusDir = join(root, 'corpus');

const cases = [];
for (const folder of readdirSync(corpusDir).sort()) {
  for (const file of readdirSync(join(corpusDir, folder)).sort()) {
    if (!file.endsWith('.json')) continue;
    const body = JSON.parse(readFileSync(join(corpusDir, folder, file), 'utf8'));
    cases.push({
      name: folder + '/' + file.replace(/\.json$/, ''),
      op: body.op,
      text: body.request_text !== undefined ? body.request_text : JSON.stringify(body.request),
      expected: JSON.stringify(body.response),
    });
  }
}

// Seeded shuffle (mulberry32), so a failing order can be reproduced with CORPUS_SEED.
const seed = Number(process.env.CORPUS_SEED || 20261107) >>> 0;
let state = seed;
function rand() {
  state = (state + 0x6d2b79f5) >>> 0;
  let t = state;
  t = Math.imul(t ^ (t >>> 15), t | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
}
const shuffled = cases.slice();
for (let i = shuffled.length - 1; i > 0; i--) {
  const j = Math.floor(rand() * (i + 1));
  [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
}

const runtime = typeof Bun !== 'undefined' ? 'Bun ' + Bun.version : 'Node ' + process.versions.node;
let failures = 0;
function check(label, dispatch, list) {
  let passed = 0;
  for (const c of list) {
    let actual;
    try {
      actual = dispatch(c.op, c.text);
    } catch (e) {
      actual = 'THREW: ' + (e && e.message);
    }
    if (actual === c.expected) {
      passed++;
    } else {
      failures++;
      console.log('FAIL ' + label + ' ' + c.name + '\n  expected ' + c.expected + '\n  actual   ' + actual);
    }
  }
  console.log(label + ': ' + passed + '/' + list.length + ' passed');
}

const classic = readFileSync(join(root, 'dist/kernel.js'), 'utf8');
const hermetic = createHermeticKernel(classic);
check('classic artifact, hermetic realm, seed ' + seed, hermetic.dispatch, shuffled);

const esm = await import(pathToFileURL(join(root, 'dist/kernel.mjs')).href);
check('esm artifact', esm.dispatch, cases);

console.log(runtime + ', kernel ' + hermetic.version + ': ' + (failures === 0 ? 'all passed' : failures + ' failed'));
process.exit(failures === 0 ? 0 : 1);
