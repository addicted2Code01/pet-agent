// Checks the raw request text before JSON.parse sees it: size, nesting depth,
// NUL characters and ill-formed UTF-16.

import { kernelError } from './errors';

export const MAX_REQUEST_CHARS = 1048576;
export const MAX_DEPTH = 32;

export function prescan(text: string): void {
  if (text.length > MAX_REQUEST_CHARS) {
    throw kernelError('REQUEST_TOO_LARGE', null);
  }
  let depth = 0;
  let inString = false;
  let escaped = false;
  for (let i = 0; i < text.length; i++) {
    const c = text.charCodeAt(i);
    if (c === 0) {
      throw kernelError('INVALID_CHARACTER', null);
    }
    if (c >= 0xd800 && c <= 0xdbff) {
      const next = i + 1 < text.length ? text.charCodeAt(i + 1) : 0;
      if (next < 0xdc00 || next > 0xdfff) {
        throw kernelError('INVALID_CHARACTER', null);
      }
      i++;
      escaped = false;
      continue;
    }
    if (c >= 0xdc00 && c <= 0xdfff) {
      throw kernelError('INVALID_CHARACTER', null);
    }
    if (inString) {
      if (escaped) {
        escaped = false;
      } else if (c === 0x5c) {
        escaped = true;
      } else if (c === 0x22) {
        inString = false;
      }
      continue;
    }
    if (c === 0x22) {
      inString = true;
    } else if (c === 0x7b || c === 0x5b) {
      depth++;
      if (depth > MAX_DEPTH) {
        throw kernelError('REQUEST_TOO_DEEP', null);
      }
    } else if (c === 0x7d || c === 0x5d) {
      depth--;
    }
  }
}
