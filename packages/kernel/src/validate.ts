// Strict request validation: allowlisted keys, exact types, explicit bounds.
// Unknown keys (including __proto__, constructor and prototype) are rejected.

import { kernelError } from './errors';

export type Obj = { readonly [key: string]: unknown };

export function join(path: string, key: string): string {
  return path === '' ? key : path + '.' + key;
}

export function at(path: string, index: number): string {
  return path + '[' + String(index) + ']';
}

function pathOrNull(path: string): string | null {
  return path === '' ? null : path;
}

export function expectObject(value: unknown, path: string, keys: readonly string[]): Obj {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    throw kernelError('EXPECTED_OBJECT', pathOrNull(path));
  }
  const own = Object.keys(value);
  for (let i = 0; i < own.length; i++) {
    const key = own[i] as string;
    if (keys.indexOf(key) < 0) {
      throw kernelError('UNKNOWN_FIELD', join(path, key));
    }
  }
  for (let i = 0; i < keys.length; i++) {
    const key = keys[i] as string;
    if (!Object.prototype.hasOwnProperty.call(value, key)) {
      throw kernelError('MISSING_FIELD', join(path, key));
    }
  }
  return value as Obj;
}

export function expectArray(value: unknown, path: string, maxLength: number): readonly unknown[] {
  if (!Array.isArray(value)) {
    throw kernelError('EXPECTED_ARRAY', pathOrNull(path));
  }
  if (value.length > maxLength) {
    throw kernelError('TOO_MANY_ITEMS', pathOrNull(path));
  }
  return value;
}

export function expectInteger(value: unknown, path: string, min: number, max: number): number {
  if (typeof value !== 'number' || !Number.isSafeInteger(value) || Object.is(value, -0)) {
    throw kernelError('INVALID_INTEGER', pathOrNull(path));
  }
  if (value < min || value > max) {
    throw kernelError('OUT_OF_RANGE', pathOrNull(path));
  }
  return value;
}

export function expectNullableInteger(value: unknown, path: string, min: number, max: number): number | null {
  return value === null ? null : expectInteger(value, path, min, max);
}

export function expectBoolean(value: unknown, path: string): boolean {
  if (typeof value !== 'boolean') {
    throw kernelError('INVALID_BOOLEAN', pathOrNull(path));
  }
  return value;
}

export function expectEnum(value: unknown, path: string, allowed: readonly string[]): string {
  if (typeof value !== 'string' || allowed.indexOf(value) < 0) {
    throw kernelError('INVALID_ENUM', pathOrNull(path));
  }
  return value;
}

const ID_MAX = 64;

function isIdChar(c: number): boolean {
  return (c >= 0x30 && c <= 0x39) || (c >= 0x41 && c <= 0x5a) || (c >= 0x61 && c <= 0x7a) || c === 0x5f || c === 0x2d;
}

export function expectId(value: unknown, path: string): string {
  if (typeof value !== 'string' || value.length === 0 || value.length > ID_MAX) {
    throw kernelError('INVALID_ID', pathOrNull(path));
  }
  for (let i = 0; i < value.length; i++) {
    if (!isIdChar(value.charCodeAt(i))) {
      throw kernelError('INVALID_ID', pathOrNull(path));
    }
  }
  return value;
}

export function expectNullableId(value: unknown, path: string): string | null {
  return value === null ? null : expectId(value, path);
}
