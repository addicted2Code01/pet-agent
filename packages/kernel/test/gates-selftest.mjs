// Tests for the tests: plant forbidden constructs in copies of the built artifact and check that
// the static gates and the hermetic realm catch each one.

import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHermeticKernel } from './hermetic.mjs';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const classic = readFileSync(join(root, 'dist/kernel.js'), 'utf8');
const anchor = 'function strictModeInEffect() {';
if (classic.indexOf(anchor) < 0) throw new Error('anchor not found in kernel.js');

const sha256 = (text) => createHash('sha256').update(text, 'utf8').digest('hex');
function gateOutput(source) {
  const dir = mkdtempSync(join(tmpdir(), 'kernel-gates-'));
  try {
    const esm = source + 'export const dispatch = PawsitterKernel.dispatch;\n';
    writeFileSync(join(dir, 'kernel.js'), source);
    writeFileSync(join(dir, 'kernel.mjs'), esm);
    writeFileSync(join(dir, 'manifest.json'), JSON.stringify({ kernelVersion: 'selftest', artifacts: [
      { name: 'classic', file: 'kernel.js', sha256: sha256(source) },
      { name: 'esm', file: 'kernel.mjs', sha256: sha256(esm) },
    ] }));
    try {
      execFileSync(process.execPath, [join(root, 'scripts/check-artifact.mjs'), dir], { encoding: 'utf8', stdio: 'pipe' });
      return { failed: false, output: '' };
    } catch (e) {
      return { failed: true, output: String(e.stdout) + String(e.stderr) };
    }
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

const plants = [
  { name: 'a banned global', code: 'Date.now();', expect: 'forbidden identifier Date' },
  { name: 'Math.random', code: 'Math.random();', expect: 'forbidden member .random' },
  { name: 'a function created in a loop', code: 'for (var q = 0; q < 1; q++) { var f = function () { return q; }; }', expect: 'function created inside a loop' },
  { name: 'this', code: 'var t = this;', expect: 'forbidden this' },
  { name: 'newer syntax (optional chaining)', code: 'var o = null; var v = o?.x;', expect: 'does not parse as an ES2017 script' },
  { name: 'for...in', code: 'for (var k in {}) {}', expect: 'forbidden for...in' },
];

let failures = 0;
for (const plant of plants) {
  const result = gateOutput(classic.replace(anchor, anchor + ' ' + plant.code));
  const caught = result.failed && result.output.indexOf(plant.expect) >= 0;
  console.log((caught ? 'caught  ' : 'MISSED  ') + plant.name);
  if (!caught) failures++;
}
const noStrict = gateOutput(classic.replace('"use strict";\n', ''));
const strictCaught = noStrict.failed && noStrict.output.indexOf('must start with "use strict"') >= 0;
console.log((strictCaught ? 'caught  ' : 'MISSED  ') + 'a missing "use strict"');
if (!strictCaught) failures++;
const clean = gateOutput(classic);
console.log((clean.failed ? 'MISSED  ' : 'passed  ') + 'the unmodified artifact');
if (clean.failed) failures++;

// The hermetic realm turns a hidden clock read into an INTERNAL error, never an answer.
const trapped = createHermeticKernel(classic.replace(anchor, anchor + ' Date.now();'));
const answer = trapped.dispatch('self_test', '{"schema_version":1}');
const trapCaught = answer === '{"schema_version":1,"ok":false,"error":{"code":"INTERNAL","path":null}}';
console.log((trapCaught ? 'caught  ' : 'MISSED  ') + 'a clock read at runtime in the hermetic realm');
if (!trapCaught) failures++;

console.log(failures === 0 ? 'Gate self-test passed.' : failures + ' gate checks missed.');
process.exit(failures === 0 ? 0 : 1);
