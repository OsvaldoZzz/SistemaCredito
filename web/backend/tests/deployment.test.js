import test from 'node:test';
import assert from 'node:assert/strict';
import { once } from 'node:events';
import { createApp } from '../app.js';
import { api } from '../../frontend/src/api.js';

test('la API rechaza HTML aunque el alojamiento devuelva HTTP 200', async t => {
  t.mock.method(globalThis, 'fetch', async () => new Response('<html>React</html>', {
    headers: { 'Content-Type': 'text/html' },
  }));
  await assert.rejects(api('/health'), /No se pudo conectar con la API/);
});

test('la API conserva los errores JSON del servidor', async t => {
  t.mock.method(globalThis, 'fetch', async () => Response.json({ message: 'MySQL no disponible' }, { status: 503 }));
  await assert.rejects(api('/health'), /MySQL no disponible/);
});

test('el proxy permite solo el origen público configurado sin omitir validaciones', async () => {
  const previous = process.env.APP_ORIGIN;
  process.env.APP_ORIGIN = 'https://credito.example.test';
  let server;
  try {
    server = createApp().listen(0, '127.0.0.1');
    await once(server, 'listening');
    const url = `http://127.0.0.1:${server.address().port}/api/login`;
    // Empty credentials stop before MySQL; 400 shows origin passed validation.
    for (const [origin, status] of [
      ['https://credito.example.test', 400],
      ['https://otro.example.test', 403],
      ['https://credito.example.test.evil.test', 403],
    ]) {
      const response = await fetch(url, { method: 'POST', headers: { Origin: origin, 'Content-Type': 'application/json' }, body: '{}' });
      assert.equal(response.status, status, origin);
    }
  } finally {
    if (server) await new Promise(resolve => server.close(resolve));
    if (previous === undefined) delete process.env.APP_ORIGIN;
    else process.env.APP_ORIGIN = previous;
  }
});
