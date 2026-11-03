import express from 'express';
import { randomBytes } from 'node:crypto';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { query, transaction } from './db.js';
import { assert, AppError, id, password, staffData, INTEREST, schedule, today } from './domain.js';
import { verifyPassword, equalPassword, hashPassword } from './security.js';
import * as service from './service.js';
import { portfolio, receipt } from './reports.js';

export function createApp() {
  const app = express(), sessions = new Map(), attempts = new Map();
  const ttl = 8 * 60 * 60 * 1000;
  const secure = process.env.COOKIE_SECURE === 'true';
  const publicOrigin = process.env.APP_ORIGIN ? new URL(process.env.APP_ORIGIN).origin : null;
  app.disable('x-powered-by');
  app.use(express.json({ limit: '64kb' }));
  app.use((req, res, next) => {
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('Referrer-Policy', 'same-origin');
    if (req.path.startsWith('/api')) res.setHeader('Cache-Control', 'no-store');
    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(req.method)) {
      const origin = req.get('origin');
      if (origin) {
        let allowed = false;
        try {
          const url = new URL(origin);
          allowed = origin === publicOrigin || origin === `${req.protocol}://${req.get('host')}` ||
            (!secure && ['localhost', '127.0.0.1'].includes(req.hostname) && ['localhost', '127.0.0.1'].includes(url.hostname) && ['5173', '3001'].includes(url.port) && url.protocol === 'http:');
        } catch { /* malformed origin */ }
        if (!allowed) return next(new AppError('Origen de la petición no permitido.', 403));
      }
    }
    const now = Date.now();
    for (const [key, s] of sessions) if (s.expires <= now) sessions.delete(key);
    for (const [key, a] of attempts) if (a.until <= now) attempts.delete(key);
    next();
  });
  const cookieName = 'sistcreditos_session';
  const getToken = req => req.headers.cookie?.split(';').map(v => v.trim()).find(v => v.startsWith(`${cookieName}=`))?.slice(cookieName.length + 1);
  const setCookie = (res, token, maxAge) => res.cookie(cookieName, token, { httpOnly: true, sameSite: 'strict', secure, maxAge, path: '/' });
  async function auth(req, res, next) {
    const session = sessions.get(getToken(req));
    assert(session && session.expires > Date.now(), 'Inicia sesión para continuar.', 401);
    const user = session.user;
    // Re-read roles so revoked accounts and permissions take effect immediately.
    const rows = user.rol === 'cliente'
      ? await query('SELECT id, nombre AS usuario FROM clientes WHERE id = ?', [user.id])
      : await query('SELECT id, usuario, rol FROM web_usuarios WHERE id = ?', [user.id]);
    assert(rows.length, 'La cuenta ya no está disponible.', 401);
    req.user = { ...user, ...rows[0] };
    req.session = session;
    if (!['GET', 'HEAD'].includes(req.method)) assert(req.get('x-csrf-token') === session.csrf, 'La sesión de seguridad cambió. Vuelve a ingresar.', 403);
    next();
  }
  const roles = (...allowed) => (req, res, next) => { assert(allowed.includes(req.user.rol), 'No tienes permiso para esta operación.', 403); next(); };
  const admin = roles('administrador'), staff = roles('administrador', 'recepcionista', 'cobrador');
  app.get('/api/health', async (req, res) => {
    try {
      await query('SELECT id FROM web_usuarios LIMIT 1');
      res.json({ ok: true, tasa_interes: INTEREST });
    } catch { res.status(503).json({ ok: false, message: 'Configura .env y ejecuta npm run db:prepare sobre una base separada.' }); }
  });
  app.post('/api/login', async (req, res) => {
    const usuario = String(req.body.usuario ?? '').trim();
    assert(usuario && usuario.length <= 254, 'Ingresa tu usuario o correo.');
    password(req.body.password);
    const key = `${req.ip}:${usuario.toLocaleLowerCase()}`;
    const trial = attempts.get(key);
    assert(!trial || trial.count < 3, 'Superaste los 3 intentos. Espera 15 minutos.', 429);
    const accounts = await query('SELECT * FROM web_usuarios WHERE LOWER(TRIM(usuario)) = LOWER(?) LIMIT 1', [usuario]);
    let user;
    if (accounts[0] && await verifyPassword(req.body.password, accounts[0].password_hash)) {
      const { id, usuario, rol } = accounts[0]; user = { id, usuario, rol };
    } else {
      const clients = await query('SELECT id, nombre, password FROM clientes WHERE LOWER(TRIM(correo)) = LOWER(?) LIMIT 1', [usuario]);
      if (clients[0]) {
        const stored = clients[0].password;
        const matches = String(stored).startsWith('scrypt:') ? await verifyPassword(req.body.password, stored) : equalPassword(req.body.password, stored);
        if (matches) user = { id: clients[0].id, usuario: clients[0].nombre, rol: 'cliente' };
      }
    }
    if (!user) {
      attempts.set(key, { count: (trial?.count ?? 0) + 1, until: trial?.until ?? Date.now() + 15 * 60 * 1000 });
      throw new AppError('Usuario o contraseña incorrectos.', 401);
    }
    attempts.delete(key);
    sessions.delete(getToken(req));
    const token = randomBytes(32).toString('hex'), csrf = randomBytes(24).toString('hex');
    sessions.set(token, { user, csrf, expires: Date.now() + ttl });
    setCookie(res, token, ttl);
    res.json({ user, csrf });
  });
  app.get('/api/session', auth, (req, res) => res.json({ user: req.user, csrf: req.session.csrf }));
  app.post('/api/logout', auth, (req, res) => { sessions.delete(getToken(req)); setCookie(res, '', 0); res.json({ ok: true }); });
  app.use('/api', auth);
  app.get('/api/clientes', async (req, res) => res.json(await service.scopedClients(req.user)));
  app.post('/api/clientes', staff, async (req, res) => res.status(201).json(await service.saveClient(null, req.body, req.user)));
  app.put('/api/clientes/:id', roles('administrador', 'recepcionista'), async (req, res) => res.json(await service.saveClient(id(req.params.id), req.body, req.user)));
  app.patch('/api/clientes/:id/ubicacion', async (req, res) => {
    assert(['cliente', 'administrador'].includes(req.user.rol), 'No tienes permiso para modificar la ubicación.', 403);
    await service.authorizeClient(req.user, req.params.id);
    res.json(await service.updateAddress(req.params.id, req.body));
  });
  app.delete('/api/clientes/:id', roles('administrador', 'recepcionista'), async (req, res) => {
    await service.authorizeClient(req.user, req.params.id);
    const result = await query('DELETE FROM clientes WHERE id = ?', [id(req.params.id)]);
    assert(result.affectedRows, 'El cliente ya no existe.', 404); res.json({ ok: true });
  });
  app.get('/api/prestamos', async (req, res) => res.json(await service.scopedLoans(req.user)));
  app.get('/api/prestamos/:id', async (req, res) => {
    const p = await service.getLoan(req.params.id); await service.authorizeClient(req.user, p.cliente_id); res.json(p);
  });
  app.post('/api/simulacion', (req, res) => res.json({ tasa_interes: INTEREST, cuotas: schedule(req.body, INTEREST) }));
  app.post('/api/prestamos', admin, async (req, res) => res.status(201).json(await service.createLoan(req.body)));
  app.put('/api/prestamos/:id', admin, async (req, res) => res.json(await service.updateLoan(req.params.id, req.body)));
  app.delete('/api/prestamos/:id', admin, async (req, res) => {
    const result = await query('DELETE FROM prestamo WHERE id = ?', [id(req.params.id)]);
    assert(result.affectedRows, 'El préstamo ya no existe.', 404); res.json({ ok: true });
  });
  app.post('/api/prestamos/:id/abonos', staff, async (req, res) => {
    const p = await service.getLoan(req.params.id); await service.authorizeClient(req.user, p.cliente_id);
    res.status(201).json(await service.pay(req.params.id, req.body));
  });
  app.get('/api/solicitudes', roles('administrador', 'recepcionista'), async (req, res) => {
    res.json(await query("SELECT s.*, c.nombre, c.cedula FROM solicitudes_prestamo s JOIN clientes c ON c.id = s.cliente_id WHERE s.estado = 'Pendiente' ORDER BY s.fecha_solicitud, s.id"));
  });
  app.post('/api/solicitudes', roles('administrador', 'recepcionista'), async (req, res) => {
    await service.authorizeClient(req.user, req.body.cliente_id);
    res.status(201).json(await service.createRequest(req.body));
  });
  app.patch('/api/solicitudes/:id', admin, async (req, res) => res.json(await service.resolveRequest(req.params.id, req.body)));
  app.get('/api/citas', roles('cliente', 'administrador', 'recepcionista'), async (req, res) => {
    const self = req.user.rol === 'cliente';
    res.json(await query(`SELECT a.*, c.nombre, c.cedula FROM citas a JOIN clientes c ON c.id = a.cliente_id ${self ? 'WHERE a.cliente_id = ?' : ''} ORDER BY a.fecha, a.id`, self ? [req.user.id] : []));
  });
  app.post('/api/citas', roles('cliente'), async (req, res) => res.status(201).json(await service.createAppointment(req.user.id, req.body)));
  app.get('/api/usuarios', admin, async (req, res) => {
    const users = await query('SELECT id, usuario, rol FROM web_usuarios ORDER BY usuario');
    const assignments = await query('SELECT usuario_id, cliente_id FROM web_asignaciones');
    res.json(users.map(u => ({ ...u, clientes_asignados: assignments.filter(a => a.usuario_id === u.id).map(a => a.cliente_id) })));
  });
  app.post('/api/usuarios', admin, async (req, res) => {
    const data = staffData(req.body), hash = await hashPassword(req.body.password);
    const result = await query('INSERT INTO web_usuarios (usuario, rol, password_hash) VALUES (?, ?, ?)', [data.usuario, data.rol, hash]);
    res.status(201).json({ id: result.insertId });
  });
  app.put('/api/usuarios/:id', admin, async (req, res) => {
    const userId = id(req.params.id), data = staffData(req.body, true);
    await transaction(async db => {
      const admins = await query("SELECT id FROM web_usuarios WHERE rol = 'administrador' FOR UPDATE", [], db);
      const rows = await query('SELECT id, rol FROM web_usuarios WHERE id = ? FOR UPDATE', [userId], db);
      assert(rows.length, 'El usuario no existe.', 404);
      assert(userId !== req.user.id || data.rol === req.user.rol, 'No puedes cambiar el rol de tu sesión activa.');
      assert(rows[0].rol !== 'administrador' || data.rol === 'administrador' || admins.length > 1, 'Debe quedar al menos un administrador.');
      if (req.body.password) await query('UPDATE web_usuarios SET usuario = ?, rol = ?, password_hash = ? WHERE id = ?', [data.usuario, data.rol, await hashPassword(req.body.password), userId], db);
      else await query('UPDATE web_usuarios SET usuario = ?, rol = ? WHERE id = ?', [data.usuario, data.rol, userId], db);
      if (data.rol !== 'cobrador') await query('DELETE FROM web_asignaciones WHERE usuario_id = ?', [userId], db);
    });
    // Invalidate sessions for changed credentials/role; the current session can refresh its name.
    for (const [token, session] of sessions) if (session.user.rol !== 'cliente' && session.user.id === userId && (req.body.password || data.rol !== session.user.rol)) sessions.delete(token);
    res.json({ ok: true });
  });
  app.delete('/api/usuarios/:id', admin, async (req, res) => {
    const userId = id(req.params.id);
    assert(userId !== req.user.id, 'No puedes eliminar tu sesión activa.');
    await transaction(async db => {
      const admins = await query("SELECT id FROM web_usuarios WHERE rol = 'administrador' FOR UPDATE", [], db);
      assert(!admins.some(u => u.id === userId) || admins.length > 1, 'Debe quedar al menos un administrador.');
      const result = await query('DELETE FROM web_usuarios WHERE id = ?', [userId], db);
      assert(result.affectedRows, 'El usuario ya no existe.', 404);
    });
    res.json({ ok: true });
  });
  app.put('/api/usuarios/:id/asignaciones', admin, async (req, res) => {
    const userId = id(req.params.id);
    assert(Array.isArray(req.body.clientes) && req.body.clientes.length <= 10000, 'Lista de clientes inválida.');
    const clients = [...new Set(req.body.clientes.map(id))];
    await transaction(async db => {
      const users = await query('SELECT rol FROM web_usuarios WHERE id = ? FOR UPDATE', [userId], db);
      assert(users[0]?.rol === 'cobrador', 'Solo los cobradores requieren asignación de clientes.');
      await query('DELETE FROM web_asignaciones WHERE usuario_id = ?', [userId], db);
      for (const clientId of clients) await query('INSERT INTO web_asignaciones (usuario_id, cliente_id) VALUES (?, ?)', [userId, clientId], db);
    });
    res.json({ ok: true });
  });
  app.get('/api/reportes/:tipo', staff, async (req, res) => {
    assert(['cartera', 'cobranza'].includes(req.params.tipo), 'Reporte no disponible.', 404);
    await portfolio(res, req.user, req.params.tipo);
  });
  app.get('/api/recibos/:id', async (req, res) => receipt(res, req.user, req.params.id));
  app.use('/api', (req, res) => res.status(404).json({ message: 'La operación no existe.' }));
  const dist = fileURLToPath(new URL('../dist', import.meta.url));
  if (existsSync(path.join(dist, 'index.html'))) {
    app.use(express.static(dist));
    app.get('/{*splat}', (req, res) => res.sendFile(path.join(dist, 'index.html')));
  }
  app.use((error, req, res, next) => {
    if (res.headersSent) return next(error);
    const status = error.status ?? (error.code === 'ER_DUP_ENTRY' ? 409 : error.code?.startsWith('ER_ROW_IS_REFERENCED') ? 409 : 500);
    const message = error instanceof AppError ? error.message : status === 409 ? 'Hay datos duplicados o registros relacionados que impiden la operación.' : status === 400 ? 'La petición no es válida.' : 'No se pudo completar la operación. Revisa la conexión y la preparación de MySQL.';
    if (status >= 500) console.error('Error de operación:', error.code ?? error.name);
    res.status(status).json({ message });
  });
  return app;
}
