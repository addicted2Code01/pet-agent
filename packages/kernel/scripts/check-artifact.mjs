// Static gates on the built artifacts (docs/spec/07-portable-core.md §7.4, §7.11):
// the classic script must parse as an ES2017 strict-mode script, expose only the kernel namespace,
// and contain none of the forbidden constructs; the manifest's hashes must match the files.

import { parse } from 'acorn';
import { fullAncestor } from 'acorn-walk';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
// The artifacts to check: dist/ by default, or a directory given as the first argument.
const dist = process.argv[2] ? process.argv[2] : join(root, 'dist');
const SIZE_BUDGET = 131072;

const BANNED_GLOBALS = new Set([
  'Date', 'Intl', 'Temporal', 'eval', 'Function', 'Proxy', 'WeakRef', 'FinalizationRegistry', 'BigInt',
  'Promise', 'setTimeout', 'setInterval', 'setImmediate', 'clearTimeout', 'clearInterval', 'queueMicrotask',
  'fetch', 'XMLHttpRequest', 'console', 'process', 'require', 'globalThis', 'window', 'self', 'global',
  'TextEncoder', 'TextDecoder', 'URL', 'URLSearchParams', 'structuredClone', 'SharedArrayBuffer', 'Atomics',
  'WebAssembly', 'arguments', 'parseFloat',
]);
const BANNED_MEMBERS = new Set([
  'random', 'pow', 'localeCompare', 'toLocaleString', 'toLocaleDateString', 'toLocaleTimeString',
  'toLocaleUpperCase', 'toLocaleLowerCase', 'normalize', 'toFixed',
]);
const LOOPS = new Set(['ForStatement', 'ForInStatement', 'ForOfStatement', 'WhileStatement', 'DoWhileStatement']);
const FUNCTIONS = new Set(['FunctionExpression', 'ArrowFunctionExpression', 'FunctionDeclaration']);

const problems = [];
function problem(node, message) {
  problems.push(message + (node ? ' at offset ' + node.start : ''));
}

const classic = readFileSync(join(dist, 'kernel.js'), 'utf8');
const esm = readFileSync(join(dist, 'kernel.mjs'), 'utf8');

// 1. Size, and ES2017 syntax as a classic script.
if (Buffer.byteLength(classic) > SIZE_BUDGET) {
  problem(null, 'kernel.js is ' + Buffer.byteLength(classic) + ' bytes, over the ' + SIZE_BUDGET + '-byte budget');
}
let ast = null;
try {
  ast = parse(classic, { ecmaVersion: 2017, sourceType: 'script' });
} catch (e) {
  problem(null, 'kernel.js does not parse as an ES2017 script: ' + e.message);
}
try {
  parse(esm, { ecmaVersion: 2017, sourceType: 'module' });
} catch (e) {
  problem(null, 'kernel.mjs does not parse as an ES2017 module: ' + e.message);
}

function isUseStrict(statement) {
  return statement && statement.type === 'ExpressionStatement' && statement.directive === 'use strict';
}

if (ast) {
  // 2. Shape: "use strict"; var PawsitterKernel = (function () { "use strict"; ... })();
  const [first, second, ...rest] = ast.body;
  if (!isUseStrict(first)) problem(first, 'kernel.js must start with "use strict"');
  const declarator = second && second.type === 'VariableDeclaration' && second.declarations.length === 1 ? second.declarations[0] : null;
  const call = declarator && declarator.id.name === 'PawsitterKernel' ? declarator.init : null;
  const fn = call && call.type === 'CallExpression' && call.arguments.length === 0 ? call.callee : null;
  if (!fn || fn.type !== 'FunctionExpression' || fn.params.length !== 0) {
    problem(second, 'kernel.js must declare PawsitterKernel as one immediately invoked function');
  } else {
    if (!isUseStrict(fn.body.body[0])) problem(fn, 'the kernel function body must start with "use strict"');
    for (const statement of fn.body.body) {
      if (statement.type === 'VariableDeclaration' && statement.kind === 'let') {
        problem(statement, 'top-level let in the kernel');
      }
    }
  }
  if (rest.length !== 0) problem(rest[0], 'kernel.js must contain nothing after the kernel declaration');

  // 3. Forbidden constructs.
  fullAncestor(ast, (node, _state, ancestors) => {
    const parent = ancestors[ancestors.length - 2];
    switch (node.type) {
      case 'Identifier': {
        const isPropertyName =
          (parent && parent.type === 'MemberExpression' && parent.property === node && !parent.computed) ||
          (parent && parent.type === 'Property' && parent.key === node && !parent.computed && !parent.shorthand);
        if (!isPropertyName && BANNED_GLOBALS.has(node.name)) problem(node, 'forbidden identifier ' + node.name);
        break;
      }
      case 'MemberExpression': {
        const name = node.computed ? (node.property.type === 'Literal' ? String(node.property.value) : null) : node.property.name;
        if (name !== null && BANNED_MEMBERS.has(name)) problem(node, 'forbidden member .' + name);
        break;
      }
      case 'ThisExpression':
        problem(node, 'forbidden this');
        break;
      case 'ClassDeclaration':
      case 'ClassExpression':
        problem(node, 'forbidden class');
        break;
      case 'ForInStatement':
        problem(node, 'forbidden for...in');
        break;
      case 'Literal':
        if (node.regex && /[gy]/.test(node.regex.flags)) problem(node, 'regular expression with the g or y flag');
        break;
      case 'VariableDeclaration':
        if (node.kind === 'let') {
          for (const d of node.declarations) {
            const inForOfOrIn = parent && (parent.type === 'ForOfStatement' || parent.type === 'ForInStatement');
            if (d.init === null && !inForOfOrIn) problem(node, 'let without an initializer');
          }
        }
        break;
      default:
        break;
    }
    if (FUNCTIONS.has(node.type)) {
      if (node.async) problem(node, 'forbidden async function');
      if (node.generator) problem(node, 'forbidden generator');
      // A function created anywhere inside a loop body (07 §7.4: Hermes shares loop bindings).
      for (let i = ancestors.length - 2; i >= 0; i--) {
        const a = ancestors[i];
        if (FUNCTIONS.has(a.type)) break;
        if (LOOPS.has(a.type)) {
          problem(node, 'function created inside a loop');
          break;
        }
      }
    }
  });
}

// 4. The manifest matches the files.
const manifest = JSON.parse(readFileSync(join(dist, 'manifest.json'), 'utf8'));
for (const artifact of manifest.artifacts) {
  const text = readFileSync(join(dist, artifact.file), 'utf8');
  const sha = createHash('sha256').update(text, 'utf8').digest('hex');
  if (sha !== artifact.sha256) problem(null, artifact.file + ' does not match its manifest hash');
}

if (problems.length > 0) {
  console.log('Artifact gates failed:\n  ' + problems.join('\n  '));
  process.exit(1);
}
console.log('Artifact gates passed: ES2017 strict script, no forbidden constructs, ' + Buffer.byteLength(classic) + ' bytes, manifest hashes match.');
