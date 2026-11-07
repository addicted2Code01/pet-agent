// Builds the two canonical kernel artifacts (docs/spec/07-portable-core.md §7.1, §7.4):
//   dist/kernel.js   one strict-mode classic script (an IIFE exposing PawsitterKernel), ES2017 syntax
//   dist/kernel.mjs  the ES module wrapper generated from it
// and dist/manifest.json with each artifact's sha256.

import { parse } from 'acorn';
import { build } from 'esbuild';
import { createHash } from 'node:crypto';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const pkg = JSON.parse(readFileSync(join(root, 'package.json'), 'utf8'));

// Bundle as an ES module, where esbuild adds no export helpers, then wrap it in the IIFE ourselves.
// esbuild's own IIFE helpers create getters inside a loop, which 07 §7.4 forbids (Hermes shares loop bindings).
const result = await build({
  entryPoints: [join(root, 'src/index.ts')],
  bundle: true,
  write: false,
  format: 'esm',
  target: 'es2017',
  platform: 'neutral',
  charset: 'ascii',
  legalComments: 'none',
  define: { __KERNEL_VERSION__: JSON.stringify(pkg.version) },
  logLevel: 'warning',
});

const bundled = result.outputFiles[0].text;
const ast = parse(bundled, { ecmaVersion: 'latest', sourceType: 'module' });
const exportsNodes = ast.body.filter((node) => node.type !== 'ExpressionStatement' && node.type.startsWith('Export'));
const last = ast.body[ast.body.length - 1];
if (exportsNodes.length !== 1 || exportsNodes[0] !== last || last.type !== 'ExportNamedDeclaration' || last.source || last.declaration) {
  throw new Error('Unexpected esbuild output: expected a single trailing "export { ... }" statement');
}
const names = last.specifiers.map((s) => ({ local: s.local.name, exported: s.exported.name }));
const expected = ['KERNEL_VERSION', 'dispatch'];
if (names.map((n) => n.exported).sort().join(',') !== expected.join(',')) {
  throw new Error('Unexpected kernel exports: ' + names.map((n) => n.exported).join(', '));
}
const body = bundled.slice(0, last.start).trimEnd();
const indent = (text) => text.split('\n').map((line) => (line === '' ? line : '  ' + line)).join('\n');
const namespace = names.map((n) => n.exported + ': ' + n.local).sort().join(', ');
// 'use strict' at the top and inside the function body (07 §7.4).
let code = '"use strict";\nvar PawsitterKernel = (function () {\n  "use strict";\n' + indent(body) +
  '\n  return Object.freeze({ ' + namespace + ' });\n})();\n';

const esm = code + 'export const dispatch = PawsitterKernel.dispatch;\nexport const KERNEL_VERSION = PawsitterKernel.KERNEL_VERSION;\n';

const sha256 = (text) => createHash('sha256').update(text, 'utf8').digest('hex');
const dist = join(root, 'dist');
mkdirSync(dist, { recursive: true });
writeFileSync(join(dist, 'kernel.js'), code);
writeFileSync(join(dist, 'kernel.mjs'), esm);
const manifest = {
  kernelVersion: pkg.version,
  artifacts: [
    { name: 'classic', file: 'kernel.js', sha256: sha256(code), bytes: Buffer.byteLength(code) },
    { name: 'esm', file: 'kernel.mjs', sha256: sha256(esm), bytes: Buffer.byteLength(esm) },
  ],
};
writeFileSync(join(dist, 'manifest.json'), JSON.stringify(manifest, null, 2) + '\n');
console.log('built kernel ' + pkg.version + ': ' + manifest.artifacts.map((a) => a.file + ' ' + a.sha256.slice(0, 12)).join(', '));
