// Runs inside the kernel's realm on each new engine or page load (docs/spec/07-portable-core.md §7.8).

import { expectObject, expectInteger, type Obj } from '../validate';

function strictModeInEffect(): boolean {
  const frozen = Object.freeze({ a: 1 });
  try {
    (frozen as { a: number }).a = 2;
    return false;
  } catch (e) {
    return true;
  }
}

export function selfTest(request: Obj): unknown {
  const r = expectObject(request, '', ['schema_version']);
  expectInteger(r['schema_version'], 'schema_version', 1, 1);
  return { strict_mode: strictModeInEffect() };
}
