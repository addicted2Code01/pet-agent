// Checked integer arithmetic. Every result must stay a safe integer.

import { kernelError } from './errors';

export function add(a: number, b: number): number {
  const result = a + b;
  if (!Number.isSafeInteger(result)) {
    throw kernelError('INTEGER_OVERFLOW', null);
  }
  return result;
}

export function sub(a: number, b: number): number {
  const result = a - b;
  if (!Number.isSafeInteger(result)) {
    throw kernelError('INTEGER_OVERFLOW', null);
  }
  return result;
}
