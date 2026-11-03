import { query, transaction } from './db.js';
import { hashPassword } from './security.js';
import { assert, id, money, fixed, conditions, date, today, addMonths, clientData, coordinates, address, loanDetails, INTEREST, LEGACY_INTEREST } from './domain.js';

export const publicClient = c => { const { password, ...data } = c; return data; };
export async function scopedClients(user, db) {
  const fields = 'c.id, c.nombre, c.cedula, c.correo, c.direccion, c.monto, c.latitud, c.longitud';
  if (user.rol === 'cliente') return query(`SELECT ${fields} FROM clientes c WHERE c.id = ?`, [user.id], db);
  if (user.rol === 'cobrador') return query(`SELECT ${fields} FROM clientes c JOIN web_asignaciones a ON a.cliente_id = c.id WHERE a.usuario_id = ? ORDER BY c.nombre`, [user.id], db);
  return query(`SELECT ${fields} FROM clientes c ORDER BY c.nombre`, [], db);
}
export async function authorizeClient(user, clientId, db) {
  clientId = id(clientId);
  const clients = await scopedClients(user, db);
  const client = clients.find(c => c.id === clientId);
  assert(client, 'Cliente no disponible para tu cuenta.', 404);
  return client;
}
export async function getLoan(loanId, db) {
  const rows = await query('SELECT p.*, COALESCE(t.tasa_interes, ?) AS tasa_interes, c.nombre, c.cedula FROM prestamo p JOIN clientes c ON c.id = p.cliente_id LEFT JOIN web_prestamo_tasas t ON t.prestamo_id = p.id WHERE p.id = ?', [LEGACY_INTEREST, id(loanId)], db);
  assert(rows.length, 'El préstamo no existe.', 404);
  const payments = await query('SELECT id, numero_cuota, monto, fecha_pago FROM pagos_prestamo WHERE prestamo_id = ? ORDER BY fecha_pago, id', [id(loanId)], db);
  const [{ fecha }] = await query('SELECT CURRENT_DATE AS fecha', [], db);
  return loanDetails(rows[0], payments, fecha);
}
export async function scopedLoans(user, db) {
  const clients = await scopedClients(user, db);
  if (!clients.length) return [];
  const ids = clients.map(c => c.id);
  const rows = await query(`SELECT id FROM prestamo WHERE cliente_id IN (${ids.map(() => '?').join(',')}) ORDER BY id DESC`, ids, db);
  const result = [];
  for (const p of rows) result.push(await getLoan(p.id, db));
  return result;
}
async function ensureNoBalance(clientId, db) {
  const clients = await query('SELECT id FROM clientes WHERE id = ? FOR UPDATE', [clientId], db);
  assert(clients.length, 'El cliente no existe.', 404);
  const loans = await query('SELECT id FROM prestamo WHERE cliente_id = ? FOR UPDATE', [clientId], db);
  for (const p of loans) assert(Number((await getLoan(p.id, db)).saldo_pendiente) === 0, 'El cliente ya tiene un préstamo con saldo pendiente. Debe liquidarlo antes de solicitar otro.');
}
async function insertLoan(data, db) {
  const monto = fixed(conditions(data)), clientId = id(data.cliente_id);
  const first = date(data.fecha_primer_pago ?? addMonths(today(), 1), false);
  await ensureNoBalance(clientId, db);
  const result = await query("INSERT INTO prestamo (cliente_id, monto, plazo, estado, fecha_primer_pago, frecuencia_pago) VALUES (?, ?, ?, 'Activo', ?, ?)", [clientId, monto, data.plazo, first, data.frecuencia_pago ?? 'Mensual'], db);
  await query('INSERT INTO web_prestamo_tasas (prestamo_id, tasa_interes) VALUES (?, ?)', [result.insertId, INTEREST], db);
  return { id: result.insertId };
}
export const createLoan = data => transaction(db => insertLoan(data, db));
export async function updateLoan(loanId, data) {
  return transaction(async db => {
    loanId = id(loanId);
    const monto = fixed(conditions(data));
    assert(['Activo', 'Pagado', 'Vencido'].includes(data.estado), 'Estado de préstamo inválido.');
    await query('SELECT id FROM prestamo WHERE id = ? FOR UPDATE', [loanId], db);
    const loan = await getLoan(loanId, db);
    const [{ total }] = await query('SELECT COUNT(*) AS total FROM pagos_prestamo WHERE prestamo_id = ?', [loanId], db);
    assert(!total || (money(loan.monto).eq(monto) && loan.plazo === data.plazo), 'No puedes cambiar monto o plazo después de registrar abonos.');
    assert(data.estado !== 'Pagado' || money(loan.saldo_pendiente, true).isZero(), 'No se puede marcar como pagado con saldo pendiente.');
    await query('UPDATE prestamo SET monto = ?, plazo = ?, estado = ? WHERE id = ?', [monto, data.plazo, data.estado, loanId], db);
    return { id: loanId };
  });
}
export async function pay(loanId, data) {
  return transaction(async db => {
    loanId = id(loanId);
    await query('SELECT id FROM prestamo WHERE id = ? FOR UPDATE', [loanId], db);
    const loan = await getLoan(loanId, db);
    const cuota = loan.cuotas.find(q => q.numero === id(data.numero_cuota));
    assert(cuota, 'La cuota no existe.');
    const amount = money(data.monto);
    assert(amount.lte(cuota.total_pendiente), 'El abono no puede superar el total pendiente de la cuota.');
    const result = await query('INSERT INTO pagos_prestamo (prestamo_id, numero_cuota, monto) VALUES (?, ?, ?)', [loanId, cuota.numero, fixed(amount)], db);
    const updated = await getLoan(loanId, db);
    await query('UPDATE prestamo SET estado = ? WHERE id = ?', [updated.estado_actual, loanId], db);
    return { id: result.insertId, prestamo_id: loanId };
  });
}
export async function saveClient(clientId, data, user) {
  const editing = clientId != null;
  const valid = clientData(data, editing);
  if (valid.password) valid.password = await hashPassword(valid.password);
  return transaction(async db => {
    if (editing) await authorizeClient(user, clientId, db);
    const duplicates = await query('SELECT id FROM clientes WHERE (LOWER(TRIM(cedula)) = LOWER(?) OR LOWER(TRIM(correo)) = LOWER(?)) AND id <> ? LIMIT 1', [valid.cedula, valid.correo, clientId ?? 0], db);
    assert(!duplicates.length, 'Ya existe un cliente con esa cédula o correo.');
    const fields = Object.keys(valid);
    if (editing) {
      await query(`UPDATE clientes SET ${fields.map(f => `\`${f}\` = ?`).join(',')} WHERE id = ?`, [...Object.values(valid), id(clientId)], db);
      return { id: id(clientId) };
    }
    const result = await query(`INSERT INTO clientes (${fields.map(f => `\`${f}\``).join(',')}) VALUES (${fields.map(() => '?').join(',')})`, Object.values(valid), db);
    if (user.rol === 'cobrador') await query('INSERT INTO web_asignaciones (usuario_id, cliente_id) VALUES (?, ?)', [user.id, result.insertId], db);
    return { id: result.insertId };
  });
}
export async function updateAddress(clientId, data) {
  const [lat, lng] = coordinates(data.latitud, data.longitud);
  await query('UPDATE clientes SET direccion = ?, latitud = ?, longitud = ? WHERE id = ?', [address(data.direccion), lat, lng, id(clientId)]);
  return { id: id(clientId) };
}
export async function createRequest(data) {
  const amount = fixed(conditions(data)), income = fixed(money(data.ingreso_mensual));
  return transaction(async db => {
    await ensureNoBalance(id(data.cliente_id), db);
    const result = await query('INSERT INTO solicitudes_prestamo (cliente_id, monto, plazo, ingreso_mensual, frecuencia_pago) VALUES (?, ?, ?, ?, ?)', [id(data.cliente_id), amount, data.plazo, income, data.frecuencia_pago ?? 'Mensual'], db);
    return { id: result.insertId };
  });
}
export async function resolveRequest(requestId, data) {
  assert(typeof data.aprobada === 'boolean', 'Decisión de solicitud inválida.');
  return transaction(async db => {
    const rows = await query("SELECT * FROM solicitudes_prestamo WHERE id = ? AND estado = 'Pendiente' FOR UPDATE", [id(requestId)], db);
    assert(rows.length, 'La solicitud ya fue resuelta o no existe.');
    let result = {};
    if (data.aprobada) result = await insertLoan({ ...rows[0], fecha_primer_pago: data.fecha_primer_pago ?? today() }, db);
    await query('UPDATE solicitudes_prestamo SET estado = ? WHERE id = ?', [data.aprobada ? 'Aprobada' : 'Rechazada', id(requestId)], db);
    return result;
  });
}
export async function createAppointment(clientId, data) {
  const fecha = date(data.fecha, false);
  return transaction(async db => {
    await query('SELECT id FROM clientes WHERE id = ? FOR UPDATE', [id(clientId)], db);
    const duplicate = await query('SELECT id FROM citas WHERE cliente_id = ? AND fecha = ?', [id(clientId), fecha], db);
    assert(!duplicate.length, 'Ya tienes una cita registrada para esa fecha.');
    const result = await query('INSERT INTO citas (cliente_id, fecha) VALUES (?, ?)', [id(clientId), fecha], db);
    return { id: result.insertId };
  });
}
