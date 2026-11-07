// The kernel boundary: dispatch(op, requestJson) returns responseJson (docs/spec/07-portable-core.md §7.4).

import { isKernelError, kernelError } from './errors';
import { prescan } from './prescan';
import { expectInteger, type Obj } from './validate';
import { canAdminister } from './ops/canAdminister';
import { selfTest } from './ops/selfTest';

const SCHEMA_VERSION = 1;

type Handler = (request: Obj) => unknown;

const OPS: Map<string, Handler> = new Map<string, Handler>([
  ['can_administer', canAdminister],
  ['self_test', selfTest],
]);

export const KERNEL_VERSION: string = __KERNEL_VERSION__;

function parseRequest(text: string): Obj {
  prescan(text);
  let parsed: unknown = null;
  try {
    parsed = JSON.parse(text);
  } catch (e) {
    throw kernelError('INVALID_JSON', null);
  }
  if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
    throw kernelError('EXPECTED_OBJECT', null);
  }
  const request = parsed as Obj;
  if (!Object.prototype.hasOwnProperty.call(request, 'schema_version')) {
    throw kernelError('MISSING_FIELD', 'schema_version');
  }
  const version = expectInteger(request['schema_version'], 'schema_version', 0, 1000000);
  if (version !== SCHEMA_VERSION) {
    throw kernelError('UNSUPPORTED_SCHEMA_VERSION', 'schema_version');
  }
  return request;
}

export function dispatch(op: unknown, requestJson: unknown): string {
  try {
    if (typeof op !== 'string' || typeof requestJson !== 'string') {
      throw kernelError('INVALID_ARGUMENT', null);
    }
    const handler = OPS.get(op);
    if (handler === undefined) {
      throw kernelError('UNKNOWN_OP', null);
    }
    const result = handler(parseRequest(requestJson));
    return JSON.stringify({ schema_version: SCHEMA_VERSION, ok: true, result: result });
  } catch (e) {
    const failure = isKernelError(e) ? e : kernelError('INTERNAL', null);
    return JSON.stringify({ schema_version: SCHEMA_VERSION, ok: false, error: { code: failure.code, path: failure.path } });
  }
}
