// A hermetic realm for running the kernel artifact (docs/spec/07-portable-core.md §7.11):
// host APIs that could change an answer are traps, and methods newer than ES2017 are removed.

import vm from 'node:vm';

const SETUP = `"use strict";
(function () {
  var g = globalThis;
  function trapGetter(name) {
    return { configurable: false, enumerable: false, get: function () { throw new Error('HERMETIC_TRAP: ' + name); } };
  }
  function trapGlobal(name) {
    try { delete g[name]; } catch (e) {}
    Object.defineProperty(g, name, trapGetter(name));
  }
  function trapMember(owner, ownerName, name) {
    if (owner && Object.prototype.hasOwnProperty.call(owner, name)) {
      try { delete owner[name]; } catch (e) {}
    }
    if (owner) { Object.defineProperty(owner, name, trapGetter(ownerName + '.' + name)); }
  }
  function remove(owner, name) {
    if (owner && Object.prototype.hasOwnProperty.call(owner, name)) { delete owner[name]; }
  }
  ['Date', 'Intl', 'Temporal', 'WeakRef', 'FinalizationRegistry', 'SharedArrayBuffer', 'Atomics',
   'WebAssembly', 'eval', 'Function', 'Proxy'].forEach(trapGlobal);
  trapMember(Math, 'Math', 'random');
  trapMember(Math, 'Math', 'pow');
  trapMember(String.prototype, 'String.prototype', 'localeCompare');
  trapMember(String.prototype, 'String.prototype', 'normalize');
  trapMember(String.prototype, 'String.prototype', 'toLocaleUpperCase');
  trapMember(String.prototype, 'String.prototype', 'toLocaleLowerCase');
  trapMember(Number.prototype, 'Number.prototype', 'toLocaleString');
  trapMember(Number.prototype, 'Number.prototype', 'toFixed');
  trapMember(Array.prototype, 'Array.prototype', 'toLocaleString');
  trapMember(Object.prototype, 'Object.prototype', 'toLocaleString');
  trapMember(Object.getPrototypeOf(function () {}), 'Function.prototype', 'constructor');
  // Newer than ES2017.
  ['flat', 'flatMap', 'at', 'findLast', 'findLastIndex', 'toSorted', 'toReversed', 'toSpliced', 'with']
    .forEach(function (n) { remove(Array.prototype, n); });
  ['fromAsync'].forEach(function (n) { remove(Array, n); });
  ['fromEntries', 'hasOwn', 'groupBy'].forEach(function (n) { remove(Object, n); });
  ['trimStart', 'trimEnd', 'matchAll', 'replaceAll', 'at', 'isWellFormed', 'toWellFormed']
    .forEach(function (n) { remove(String.prototype, n); });
  ['allSettled', 'any', 'withResolvers', 'try'].forEach(function (n) { remove(Promise, n); });
  ['groupBy'].forEach(function (n) { remove(Map, n); });
  ['escape'].forEach(function (n) { remove(RegExp, n); });
  ['union', 'intersection', 'difference', 'symmetricDifference', 'isSubsetOf', 'isSupersetOf', 'isDisjointFrom']
    .forEach(function (n) { remove(Set.prototype, n); });
})();`;

export function createHermeticKernel(kernelSource) {
  const context = vm.createContext(Object.create(null));
  vm.runInContext(SETUP, context, { filename: 'hermetic-setup.js' });
  vm.runInContext(kernelSource + '\nglobalThis.PawsitterKernel = PawsitterKernel;', context, { filename: 'kernel.js' });
  const kernel = vm.runInContext('globalThis.PawsitterKernel', context);
  return { dispatch: (op, text) => kernel.dispatch(op, text), version: kernel.KERNEL_VERSION };
}
