import test from 'node:test';
import assert from 'node:assert/strict';
import { once } from 'node:events';
import { randomBytes } from 'node:crypto';
import { createApp } from '../app.js';
import { pool, query } from '../db.js';
import { hashPassword } from '../security.js';
import { today } from '../domain.js';

test('API con MySQL: roles, préstamo al 15%, solicitudes, abonos, citas y PDF', async t => {
  const suffix = randomBytes(5).toString('hex');
  const credentials = { usuario: `Prueba ${suffix} Admin`, password: 'prueba123' };
  const emails = [`prueba-${suffix}@example.test`, `otra-${suffix}@example.test`];
  const staffIds = [], clientIds = [];
  let server;
  const cookie = { admin: '', reception: '', collector: '', client: '', other: '' };
  const csrf = {};
  let url;
  async function request(role, path, method = 'GET', body, expected = 200, headers = {}) {
    const response = await fetch(`${url}/api${path}`, { method, headers: { 'Content-Type': 'application/json', Cookie: cookie[role] || '', 'X-CSRF-Token': csrf[role] || '', ...headers }, ...(body === undefined ? {} : { body: JSON.stringify(body) }) });
    const isPDF = response.headers.get('content-type')?.includes('application/pdf');
    const result = isPDF ? Buffer.from(await response.arrayBuffer()) : await response.json();
    assert.equal(response.status, expected, `${method} ${path}: ${isPDF ? 'PDF' : JSON.stringify(result)}`);
    if (path === '/login' && expected === 200) {
      cookie[role] = response.headers.get('set-cookie').split(';')[0];
      csrf[role] = result.csrf;
      assert.match(response.headers.get('set-cookie'), /HttpOnly/);
    }
    return result;
  }
  try {
    const seeded = await query('INSERT INTO web_usuarios (usuario, rol, password_hash) VALUES (?, ?, ?)', [credentials.usuario, 'administrador', await hashPassword(credentials.password)]);
    staffIds.push(seeded.insertId);
    server = createApp().listen(0, '127.0.0.1'); await once(server, 'listening');
    url = `http://127.0.0.1:${server.address().port}`;
    await t.test('acceso sin sesión y origen ajeno se rechazan', async () => {
      await request('other', '/clientes', 'GET', undefined, 401);
      await request('other', '/login', 'POST', credentials, 403, { Origin: 'https://example.test' });
      await request('admin', '/login', 'POST', credentials);
      await request('admin', '/clientes', 'POST', {}, 403, { 'X-CSRF-Token': 'incorrecto' });
      assert.equal((await request('admin', '/health')).ok, true);
    });
    let reception, collector, client, other, loan, payment;
    await t.test('crear usuarios y clientes; no se exponen contraseñas', async () => {
      reception = await request('admin', '/usuarios', 'POST', { usuario: `Prueba ${suffix} Recepcion`, rol: 'recepcionista', password: 'prueba123' }, 201); staffIds.push(reception.id);
      collector = await request('admin', '/usuarios', 'POST', { usuario: `Prueba ${suffix} Cobranza`, rol: 'cobrador', password: 'prueba123' }, 201); staffIds.push(collector.id);
      const payload = { nombre: 'Ana Prueba', cedula: `QA-${suffix}`, correo: emails[0], password: 'cliente123', direccion: 'Barrio Central', monto: '0' };
      client = await request('admin', '/clientes', 'POST', payload, 201); clientIds.push(client.id);
      other = await request('admin', '/clientes', 'POST', { ...payload, nombre: 'Otra Prueba', cedula: `QB-${suffix}`, correo: emails[1] }, 201); clientIds.push(other.id);
      await request('admin', '/clientes', 'POST', payload, 400);
      const clients = await request('admin', '/clientes');
      assert.ok(clients.some(c => c.id === client.id));
      assert.ok(clients.every(c => !('password' in c)));
      const [stored] = await query('SELECT password FROM clientes WHERE id = ?', [client.id]);
      assert.match(stored.password, /^scrypt:/);
      await request('reception', '/login', 'POST', { usuario: `Prueba ${suffix} Recepcion`, password: 'prueba123' });
      await request('collector', '/login', 'POST', { usuario: `Prueba ${suffix} Cobranza`, password: 'prueba123' });
      await request('client', '/login', 'POST', { usuario: emails[0], password: 'cliente123' });
    });
    await t.test('asignaciones y datos propios limitan el acceso', async () => {
      assert.equal((await request('collector', '/clientes')).length, 0);
      await request('admin', `/usuarios/${collector.id}/asignaciones`, 'PUT', { clientes: [client.id] });
      assert.deepEqual((await request('collector', '/clientes')).map(c => c.id), [client.id]);
      assert.deepEqual((await request('client', '/clientes')).map(c => c.id), [client.id]);
      await request('client', `/clientes/${other.id}/ubicacion`, 'PATCH', { direccion: 'Nueva dirección', latitud: null, longitud: null }, 404);
      await request('client', '/usuarios', 'GET', undefined, 403);
      await request('reception', '/usuarios', 'GET', undefined, 403);
      await request('collector', '/solicitudes', 'GET', undefined, 403);
      await request('client', `/clientes/${client.id}/ubicacion`, 'PATCH', { direccion: 'Dirección actualizada', latitud: '12.1364', longitud: '-86.2514' });
      assert.equal((await request('client', '/clientes'))[0].direccion, 'Dirección actualizada');
    });
    await t.test('simulación y préstamo al 15%; recepción no puede emitir', async () => {
      const body = { cliente_id: client.id, monto: '1000', plazo: 2, frecuencia_pago: 'Mensual', fecha_primer_pago: today(), tasa_interes: '0.01' };
      const preview = await request('admin', '/simulacion', 'POST', body);
      assert.equal(preview.cuotas[0].monto, '575.00');
      await request('reception', '/prestamos', 'POST', body, 403);
      loan = await request('admin', '/prestamos', 'POST', body, 201);
      const detail = await request('client', `/prestamos/${loan.id}`);
      assert.equal(detail.total, '1150.00');
      assert.equal(Number(detail.tasa_interes), 0.15);
      await request('admin', '/prestamos', 'POST', body, 400);
      await request('client', `/prestamos/${loan.id}/abonos`, 'POST', { numero_cuota: 1, monto: '1' }, 403);
    });
    await t.test('abonos, límite de cuota, edición protegida y recibo PDF', async () => {
      await request('collector', `/prestamos/${loan.id}/abonos`, 'POST', { numero_cuota: 1, monto: '575.01' }, 400);
      payment = await request('collector', `/prestamos/${loan.id}/abonos`, 'POST', { numero_cuota: 1, monto: '575.00' }, 201);
      await request('admin', `/prestamos/${loan.id}`, 'PUT', { monto: '2000', plazo: 2, estado: 'Activo' }, 400);
      await request('admin', `/prestamos/${loan.id}`, 'PUT', { monto: '1000', plazo: 2, estado: 'Pagado' }, 400);
      const pdf = await request('client', `/recibos/${payment.id}`);
      assert.equal(pdf.subarray(0, 5).toString(), '%PDF-');
      assert.equal((await request('admin', `/prestamos/${loan.id}`)).saldo_pendiente, '575.00');
    });
    await t.test('pago concurrente no permite cobrar dos veces el saldo', async () => {
      const responses = await Promise.all([1, 2].map(() => fetch(`${url}/api/prestamos/${loan.id}/abonos`, { method: 'POST', headers: { 'Content-Type': 'application/json', Cookie: cookie.collector, 'X-CSRF-Token': csrf.collector }, body: JSON.stringify({ numero_cuota: 2, monto: '575.00' }) })));
      assert.deepEqual(responses.map(r => r.status).sort(), [201, 400]);
      await Promise.all(responses.map(r => r.json()));
      const paid = await request('client', `/prestamos/${loan.id}`);
      assert.equal(paid.estado_actual, 'Pagado'); assert.equal(paid.saldo_pendiente, '0.00');
    });
    await t.test('solicitud, aprobación única y nuevo préstamo tras liquidar', async () => {
      const result = await request('reception', '/solicitudes', 'POST', { cliente_id: client.id, monto: '500', plazo: 2, ingreso_mensual: '2000', frecuencia_pago: 'Semanal' }, 201);
      await request('reception', `/solicitudes/${result.id}`, 'PATCH', { aprobada: true }, 403);
      const approved = await request('admin', `/solicitudes/${result.id}`, 'PATCH', { aprobada: true, fecha_primer_pago: today() });
      await request('admin', `/solicitudes/${result.id}`, 'PATCH', { aprobada: true }, 400);
      assert.equal((await request('client', `/prestamos/${approved.id}`)).total, '575.00');
      const rejected = await request('reception', '/solicitudes', 'POST', { cliente_id: other.id, monto: '200', plazo: 2, ingreso_mensual: '1000' }, 201);
      await request('admin', `/solicitudes/${rejected.id}`, 'PATCH', { aprobada: false });
    });
    await t.test('citas propias, duplicados y reportes PDF', async () => {
      await request('client', '/citas', 'POST', { fecha: today() }, 201);
      await request('client', '/citas', 'POST', { fecha: today() }, 400);
      assert.ok((await request('client', '/citas')).every(c => c.cliente_id === client.id));
      for (const role of ['admin', 'reception', 'collector']) for (const kind of ['cartera', 'cobranza']) {
        const pdf = await request(role, `/reportes/${kind}`);
        assert.equal(pdf.subarray(0, 5).toString(), '%PDF-');
      }
      await request('client', '/reportes/cartera', 'GET', undefined, 403);
    });
    await t.test('usuario actualizado, revocación y cierre de sesión', async () => {
      await request('admin', `/usuarios/${collector.id}`, 'PUT', { usuario: `Prueba ${suffix} Cobranza`, rol: 'recepcionista', password: '' });
      await request('collector', '/clientes', 'GET', undefined, 401);
      await request('admin', `/usuarios/${reception.id}`, 'DELETE');
      await request('reception', '/clientes', 'GET', undefined, 401);
      await request('client', '/logout', 'POST');
      await request('client', '/clientes', 'GET', undefined, 401);
    });
  } finally {
    // Remove only records created with this run's random identifiers.
    for (const clientId of clientIds) {
      await query('DELETE p FROM pagos_prestamo p JOIN prestamo l ON l.id = p.prestamo_id WHERE l.cliente_id = ?', [clientId]);
      await query('DELETE t FROM web_prestamo_tasas t JOIN prestamo l ON l.id = t.prestamo_id WHERE l.cliente_id = ?', [clientId]);
      await query('DELETE FROM prestamo WHERE cliente_id = ?', [clientId]);
      await query('DELETE FROM solicitudes_prestamo WHERE cliente_id = ?', [clientId]);
      await query('DELETE FROM citas WHERE cliente_id = ?', [clientId]);
      await query('DELETE FROM web_asignaciones WHERE cliente_id = ?', [clientId]);
      await query('DELETE FROM clientes WHERE id = ? AND correo IN (?, ?)', [clientId, ...emails]);
    }
    for (const staffId of staffIds) await query('DELETE FROM web_usuarios WHERE id = ? AND usuario LIKE ?', [staffId, `Prueba ${suffix}%`]);
    if (server) await new Promise(resolve => server.close(resolve));
    await pool.end();
  }
});
