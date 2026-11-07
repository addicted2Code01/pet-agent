// Stable error codes. Failures cross the boundary as these codes, never as engine messages.

const ERROR_MARK: { readonly kind: 'kernel_error' } = { kind: 'kernel_error' };

export interface KernelError {
  readonly mark: typeof ERROR_MARK;
  readonly code: string;
  readonly path: string | null;
}

export function kernelError(code: string, path: string | null): KernelError {
  return { mark: ERROR_MARK, code: code, path: path };
}

export function isKernelError(value: unknown): value is KernelError {
  return typeof value === 'object' && value !== null && (value as { mark?: unknown }).mark === ERROR_MARK;
}
