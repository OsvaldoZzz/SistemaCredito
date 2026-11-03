import test from 'node:test';
import assert from 'node:assert/strict';
import Decimal from 'decimal.js';
import { schedule, installmentState, loanDetails, money, date, clientData, coordinates } from '../domain.js';
const loan = { monto: '1000.00', plazo: 3, fecha_primer_pago: '2028-01-31', frecuencia_pago: 'Mensual' };

test('15% exacto, reparto de centavos y suma de capital e interés', () => {
  const cuotas = schedule(loan);
  const sum = field => cuotas.reduce((s, q) => s.plus(q[field]), new Decimal(0)).toFixed(2);
  assert.equal(sum('capital'), '1000.00');
  assert.equal(sum('interes'), '150.00');
  assert.equal(sum('monto'), '1150.00');
  assert.equal(cuotas[2].capital, '333.34');
  assert.equal(schedule({ ...loan, monto: '0.10', plazo: 1 })[0].interes, '0.02');
});
test('préstamos históricos mantienen el 2% por préstamo', () => {
  const detail = loanDetails({ ...loan, tasa_interes: '0.02' }, [], '2028-01-01');
  assert.equal(detail.total, '1020.00');
  assert.equal(detail.interes_total, '20.00');
});
test('fechas mensuales conservan el día original; año bisiesto y frecuencias', () => {
  assert.deepEqual(schedule(loan).map(q => q.fecha_vencimiento), ['2028-01-31', '2028-02-29', '2028-03-31']);
  assert.equal(schedule({ ...loan, frecuencia_pago: 'Semanal' })[1].fecha_vencimiento, '2028-02-07');
  assert.equal(schedule({ ...loan, frecuencia_pago: 'Quincenal' })[1].fecha_vencimiento, '2028-02-15');
  assert.throws(() => date('2027-02-29'));
  assert.throws(() => date('2028-01-01', false, '2028-01-02'));
});
test('mora del 2% mensual y abono se aplica primero a mora', () => {
  const state = installmentState('100.00', '2026-01-01', [{ monto: '52.00', fecha_pago: '2026-01-31 12:00:00' }], '2026-03-02');
  assert.equal(state.mora_generada, '3.00');
  assert.equal(state.mora_pendiente, '1.00');
  assert.equal(state.saldo_cuota, '50.00');
  assert.equal(state.total_pendiente, '51.00');
  assert.equal(state.pagos_calculados[0].mora_aplicada, '2.00');
});
test('pago anticipado no genera mora; pago futuro no afecta el corte', () => {
  const early = installmentState('100.00', '2026-02-01', [{ monto: '100.00', fecha_pago: '2026-01-01' }], '2026-03-01');
  assert.equal(early.total_pendiente, '0.00');
  assert.equal(early.dias_mora, 0);
  const future = installmentState('100.00', '2026-02-01', [{ monto: '100.00', fecha_pago: '2026-04-01' }], '2026-02-01');
  assert.equal(future.total_pendiente, '100.00');
});
test('liquidación tardía conserva mora generada y deja saldo cero', () => {
  const detail = loanDetails({ monto: '100', plazo: 1, fecha_primer_pago: '2026-01-01', tasa_interes: '0.02' }, [{ id: 1, numero_cuota: 1, monto: '104.04', fecha_pago: '2026-01-31' }], '2026-02-10');
  assert.equal(detail.estado_actual, 'Pagado');
  assert.equal(detail.saldo_pendiente, '0.00');
  assert.equal(detail.cuotas[0].mora_generada, '2.04');
});
test('rechaza montos inválidos y condiciones que pierden centavos', () => {
  for (const bad of ['NaN', 'Infinity', '', null, true, '-1', '0.001', '100000001']) assert.throws(() => money(bad));
  for (const bad of [0, 361, 2.5, '3', true]) assert.throws(() => schedule({ ...loan, plazo: bad }));
  assert.throws(() => schedule({ ...loan, monto: '0.01', plazo: 2 }));
});
test('valida nombres, ubicación completa y contraseña opcional al editar', () => {
  const client = { nombre: 'Ana María', cedula: '001-123456', correo: 'ana@example.com', password: 'clave123', direccion: 'Barrio Central', monto: '0' };
  assert.equal(clientData(client).nombre, 'Ana María');
  assert.throws(() => clientData({ ...client, nombre: 'Ana+María' }));
  assert.throws(() => clientData({ ...client, nombre: 'Ana(María)' }));
  assert.equal(clientData({ ...client, password: '' }, true).password, undefined);
  assert.deepEqual(coordinates(null, null), [null, null]);
  for (const point of [[90.1, 0], [null, 0], [0, ''], [false, 0]]) assert.throws(() => coordinates(...point));
});
