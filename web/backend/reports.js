import PDFDocument from 'pdfkit';
import { scopedClients, scopedLoans, getLoan, authorizeClient } from './service.js';
import { query } from './db.js';
import { id, assert, today } from './domain.js';

const currency = value => `C$ ${Number(value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
function document(res, title, filename) {
  const doc = new PDFDocument({ margin: 45, size: 'A4' });
  res.type('application/pdf');
  res.setHeader('Content-Disposition', `attachment; filename="${filename}.pdf"`);
  doc.pipe(res);
  doc.fontSize(10).fillColor('#687787').text(`SISTEMA DE CREDITOS  /  ${today()}`);
  doc.moveDown().fontSize(22).fillColor('#12314a').text(title).moveDown();
  return doc;
}
function line(doc, text) {
  if (doc.y > 740) doc.addPage();
  doc.fontSize(10).fillColor('#172f40').text(text).moveDown(0.4);
}
export async function portfolio(res, user, kind) {
  const clients = await scopedClients(user), loans = await scopedLoans(user);
  const doc = document(res, kind === 'cartera' ? 'Estado de cartera' : 'Reporte de cobranza', `reporte-${kind}`);
  for (const client of clients) {
    const records = loans.filter(p => p.cliente_id === client.id);
    line(doc, `${client.nombre} | ${client.cedula}`);
    if (!records.length) line(doc, 'Sin préstamos.');
    for (const p of records) {
      line(doc, `Préstamo #${p.id} | Capital ${currency(p.monto)} | Interés ${Number(p.tasa_interes) * 100}%: ${currency(p.interes_total)}`);
      line(doc, `Total ${currency(p.total)} | Saldo con mora ${currency(p.saldo_pendiente)} | ${p.cuotas_pendientes}/${p.plazo} cuotas pendientes | ${p.estado_actual}`);
      if (kind === 'cobranza') for (const q of p.cuotas.filter(q => Number(q.total_pendiente) > 0)) line(doc, `  Cuota ${q.numero} | ${q.fecha_vencimiento} | Saldo ${currency(q.total_pendiente)} | Mora ${currency(q.mora_pendiente)}`);
    }
    doc.moveDown();
  }
  if (!clients.length) line(doc, 'No hay clientes disponibles.');
  doc.end();
}
export async function receipt(res, user, paymentId) {
  const rows = await query('SELECT * FROM pagos_prestamo WHERE id = ?', [id(paymentId)]);
  assert(rows.length, 'El abono no existe.', 404);
  const payment = rows[0], loan = await getLoan(payment.prestamo_id);
  await authorizeClient(user, loan.cliente_id);
  const doc = document(res, 'Recibo de pago', `recibo-${payment.id}`);
  for (const text of [`Recibo #${payment.id}`, `Cliente: ${loan.nombre}`, `Cédula: ${loan.cedula}`, `Préstamo #${loan.id} | Cuota ${payment.numero_cuota}`, `Fecha: ${payment.fecha_pago}`, `Monto abonado: ${currency(payment.monto)}`]) line(doc, text);
  doc.end();
}
