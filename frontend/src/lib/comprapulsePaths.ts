export const compraPulseStandalone =
  import.meta.env.VITE_COMPRAPULSE_STANDALONE === 'true';

export function compraPulsePath(path = ''): string {
  const base = compraPulseStandalone ? '' : '/comprapulse';
  return `${base}${path}` || '/';
}
