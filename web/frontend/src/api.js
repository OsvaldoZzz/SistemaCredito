let csrf = '';
let onExpired = () => {};
export function configureSession(value, callback) { csrf = value || ''; if (callback) onExpired = callback; }
export async function api(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    ...options, credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf, ...options.headers },
    ...(options.body === undefined ? {} : { body: JSON.stringify(options.body) }),
  });
  if (!response.headers.get('content-type')?.includes('application/json')) {
    throw new Error('No se pudo conectar con la API. Revisa la conexión de Netlify con el servidor.');
  }
  const result = await response.json();
  if (!response.ok) {
    if (response.status === 401 && path !== '/login') onExpired();
    throw new Error(result.message || 'No se pudo completar la operación.');
  }
  return result;
}
export const currency = value => `C$ ${Number(value ?? 0).toLocaleString('es-NI', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
export const dateLabel = value => value ? String(value).slice(0, 10).split('-').reverse().join('/') : '—';
export const today = () => new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Managua', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
