import Decimal from 'decimal.js';

Decimal.set({ precision: 30, rounding: Decimal.ROUND_HALF_UP });
export const INTEREST = '0.15';
export const LEGACY_INTEREST = '0.02';
export const FREQUENCIES = ['Semanal', 'Quincenal', 'Mensual'];
export class AppError extends Error {
  constructor(message, status = 400) { super(message); this.status = status; }
}
export function assert(condition, message, status = 400) {
  if (!condition) throw new AppError(message, status);
}
export function id(value) {
  assert(typeof value === 'number' || (typeof value === 'string' && /^[1-9]\d*$/.test(value)), 'Identificador inválido.');
  const result = Number(value);
  assert(Number.isSafeInteger(result) && result > 0, 'Identificador inválido.');
  return result;
}
export function money(value, allowZero = false) {
  let n;
  try {
    assert(typeof value === 'number' || (typeof value === 'string' && value.trim() !== ''), 'Ingresa un monto numérico válido.');
    n = new Decimal(value);
  } catch { throw new AppError('Ingresa un monto numérico válido.'); }
  assert(n.isFinite() && n.gte(allowZero ? 0 : '0.01') && n.lte(100000000), 'El monto debe estar entre C$ 0.01 y C$ 100,000,000.');
  assert(n.decimalPlaces() <= 2, 'El monto solo puede tener dos decimales.');
  return n;
}
export const fixed = value => new Decimal(value).toFixed(2);
export function conditions(data) {
  const amount = money(data.monto);
  assert(Number.isInteger(data.plazo) && data.plazo >= 1 && data.plazo <= 360, 'El plazo debe ser un entero entre 1 y 360 cuotas.');
  assert(amount.mul(100).gte(data.plazo), 'El monto no alcanza para distribuir un centavo por cuota.');
  assert(FREQUENCIES.includes(data.frecuencia_pago ?? 'Mensual'), 'Frecuencia de pago inválida.');
  return amount;
}
export function today() {
  return new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Managua', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
}
export function date(value, allowPast = true, cut = today()) {
  assert(typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value), 'Selecciona una fecha válida.');
  const d = new Date(`${value}T00:00:00Z`);
  assert(Number.isFinite(d.getTime()) && d.toISOString().slice(0, 10) === value && value >= '1000-01-01', 'Selecciona una fecha válida.');
  assert(allowPast || value >= cut, 'La fecha no puede ser anterior a hoy.');
  return value;
}
const daysBetween = (end, start) => Math.max(0, Math.round((new Date(`${end}T00:00:00Z`) - new Date(`${start}T00:00:00Z`)) / 86400000));
export function addMonths(value, months) {
  date(value);
  const [year, month, day] = value.split('-').map(Number);
  const last = new Date(Date.UTC(year, month - 1 + months + 1, 0));
  return new Date(Date.UTC(last.getUTCFullYear(), last.getUTCMonth(), Math.min(day, last.getUTCDate()))).toISOString().slice(0, 10);
}
export function schedule(loan, rate = loan.tasa_interes ?? INTEREST) {
  const capital = conditions(loan);
  const first = date(loan.fecha_primer_pago);
  const interest = capital.mul(rate).toDecimalPlaces(2);
  const baseCapital = capital.div(loan.plazo).toDecimalPlaces(2, Decimal.ROUND_DOWN);
  const baseInterest = interest.div(loan.plazo).toDecimalPlaces(2, Decimal.ROUND_DOWN);
  return Array.from({ length: loan.plazo }, (_, i) => {
    const c = i === loan.plazo - 1 ? capital.minus(baseCapital.mul(i)) : baseCapital;
    const j = i === loan.plazo - 1 ? interest.minus(baseInterest.mul(i)) : baseInterest;
    let due = addMonths(first, i);
    if (loan.frecuencia_pago && loan.frecuencia_pago !== 'Mensual') {
      const d = new Date(`${first}T00:00:00Z`);
      d.setUTCDate(d.getUTCDate() + i * (loan.frecuencia_pago === 'Semanal' ? 7 : 15));
      due = d.toISOString().slice(0, 10);
    }
    return { numero: i + 1, fecha_vencimiento: due, capital: fixed(c), interes: fixed(j), monto: fixed(c.plus(j)) };
  });
}
export function installmentState(amount, due, payments, cut) {
  date(due); date(cut);
  let balance = new Decimal(amount), late = new Decimal(0), generated = new Decimal(0), last = due;
  const calculated = [];
  const accrue = end => {
    if (balance.gt(0) && end > last) {
      const fee = balance.mul('0.02').mul(daysBetween(end, last)).div(30).toDecimalPlaces(2);
      late = late.plus(fee); generated = generated.plus(fee);
    }
    if (end > last) last = end;
  };
  const included = [...payments].sort((a, b) => a.fecha_pago.localeCompare(b.fecha_pago));
  for (const p of included) {
    const paidOn = date(String(p.fecha_pago).slice(0, 10));
    if (paidOn > cut) continue;
    accrue(paidOn);
    const paid = money(p.monto, true);
    const applied = Decimal.min(paid, late);
    calculated.push({ ...p, mora_al_abono: fixed(late), mora_aplicada: fixed(applied) });
    late = late.minus(applied);
    balance = Decimal.max(0, balance.minus(paid.minus(applied)));
  }
  accrue(cut);
  return {
    saldo_cuota: fixed(balance), mora_pendiente: fixed(late), mora_generada: fixed(generated),
    dias_mora: balance.gt(0) || late.gt(0) ? daysBetween(cut, due) : 0,
    total_pendiente: fixed(balance.plus(late)), pagos_calculados: calculated,
  };
}
export function loanDetails(loan, payments = [], cut = today()) {
  const cuotas = schedule(loan).map(q => {
    const pagos = payments.filter(p => p.numero_cuota === q.numero && String(p.fecha_pago).slice(0, 10) <= cut);
    return { ...q, ...installmentState(q.monto, q.fecha_vencimiento, pagos, cut), pagos,
      pagado: fixed(pagos.reduce((s, p) => s.plus(p.monto), new Decimal(0))), fecha_corte: cut };
  });
  const pending = cuotas.filter(q => new Decimal(q.total_pendiente).gt(0));
  return { ...loan, cuotas, cuotas_pendientes: pending.length,
    interes_total: fixed(new Decimal(loan.monto).mul(loan.tasa_interes ?? INTEREST)),
    total: fixed(cuotas.reduce((s, q) => s.plus(q.monto), new Decimal(0))),
    saldo_pendiente: fixed(pending.reduce((s, q) => s.plus(q.total_pendiente), new Decimal(0))),
    proximo_vencimiento: pending[0]?.fecha_vencimiento ?? null,
    estado_actual: !pending.length ? 'Pagado' : pending.some(q => q.dias_mora > 0) ? 'Vencido' : 'Activo' };
}
export function password(value) {
  assert(typeof value === 'string' && value.trim() && value.length >= 8 && value.length <= 12 && !/[\x00-\x1f\x7f]/.test(value), 'La contraseña debe tener entre 8 y 12 caracteres, sin caracteres de control.');
  return value;
}
export function address(value) {
  assert(typeof value === 'string' && value.trim().length >= 5 && value.trim().length <= 40 && !/[\x00-\x1f\x7f]/.test(value), 'La dirección debe tener entre 5 y 40 caracteres.');
  return value.trim();
}
export function coordinates(lat, lng) {
  const empty = v => v === null || v === undefined || v === '';
  if (empty(lat) && empty(lng)) return [null, null];
  assert(!empty(lat) && !empty(lng) && typeof lat !== 'boolean' && typeof lng !== 'boolean', 'Selecciona un punto completo en el mapa.');
  lat = Number(lat); lng = Number(lng);
  assert(Number.isFinite(lat) && Number.isFinite(lng) && Math.abs(lat) <= 90 && Math.abs(lng) <= 180, 'Ubicación inválida.');
  return [Number(lat.toFixed(7)), Number(lng.toFixed(7))];
}
export function clientData(data, editing = false) {
  const nombre = String(data.nombre ?? '').trim(), cedula = String(data.cedula ?? '').trim(), correo = String(data.correo ?? '').trim();
  assert(nombre.length >= 2 && nombre.length <= 80 && /\p{L}/u.test(nombre) && /^[\p{L} '\-.]+$/u.test(nombre), 'El nombre debe tener entre 2 y 80 caracteres y contener letras.');
  assert(/^[A-Za-z0-9-]{6,20}$/.test(cedula), 'La cédula debe tener entre 6 y 20 letras, números o guiones.');
  assert(correo.length <= 100 && /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(correo), 'Correo electrónico inválido.');
  if (!editing || data.password) password(data.password);
  const [latitud, longitud] = coordinates(data.latitud, data.longitud);
  return { nombre, cedula, correo, direccion: address(data.direccion), monto: fixed(money(data.monto ?? 0, true)), latitud, longitud, ...(data.password ? { password: data.password } : {}) };
}
export function staffData(data, editing = false) {
  const usuario = String(data.usuario ?? '').trim();
  const name = usuario.length >= 2 && usuario.length <= 100 && /\p{L}/u.test(usuario) && /^[\p{L}\p{N} ]+$/u.test(usuario);
  const email = usuario.length <= 100 && /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(usuario);
  assert(name || email, 'Usa un nombre con letras, números y espacios, o un correo válido.');
  assert(['administrador', 'recepcionista', 'cobrador'].includes(data.rol), 'Rol inválido.');
  if (!editing || data.password) password(data.password);
  return { usuario, rol: data.rol };
}
