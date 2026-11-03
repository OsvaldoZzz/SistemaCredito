import { readFile } from 'node:fs/promises';
import mysql from 'mysql2/promise';
import { databaseConfig } from './db.js';
import { hashPassword } from './security.js';

// Explicit setup only: the HTTP server never creates or alters database tables.
const config = databaseConfig();
const { database, connectionLimit, ...connection } = config;
const db = await mysql.createConnection(connection);
try {
  await db.query(`CREATE DATABASE IF NOT EXISTS \`${database}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci`);
  await db.changeUser({ database });
  const sql = await readFile(new URL('./schema.sql', import.meta.url), 'utf8');
  for (const statement of sql.split(';').map(s => s.trim()).filter(Boolean)) await db.query(statement);
  const additions = {
    clientes: { latitud: 'DECIMAL(10,7) NULL', longitud: 'DECIMAL(10,7) NULL' },
    prestamo: { frecuencia_pago: "VARCHAR(10) NOT NULL DEFAULT 'Mensual'", fecha_primer_pago: 'DATE NULL' },
    solicitudes_prestamo: { frecuencia_pago: "VARCHAR(10) NOT NULL DEFAULT 'Mensual'", ingreso_mensual: 'DECIMAL(12,2) NULL' },
  };
  for (const [table, columns] of Object.entries(additions)) {
    const [existing] = await db.query(`SHOW COLUMNS FROM \`${table}\``);
    for (const [column, definition] of Object.entries(columns)) {
      if (!existing.some(c => c.Field === column)) await db.query(`ALTER TABLE \`${table}\` ADD COLUMN \`${column}\` ${definition}`);
    }
  }
  const [passwordColumns] = await db.query("SHOW COLUMNS FROM clientes LIKE 'password'");
  if (passwordColumns[0].Type !== 'varchar(255)') await db.query('ALTER TABLE clientes MODIFY COLUMN password VARCHAR(255) NOT NULL');
  const [clients] = await db.query('SELECT id, password FROM clientes');
  for (const client of clients) {
    if (!String(client.password).startsWith('scrypt:')) await db.execute('UPDATE clientes SET password = ? WHERE id = ?', [await hashPassword(String(client.password)), client.id]);
  }
  const [missing] = await db.query('SELECT COUNT(*) AS total FROM prestamo WHERE fecha_primer_pago IS NULL');
  if (missing[0].total) console.warn(`${missing[0].total} préstamos no tienen fecha de primer pago. Completa esas fechas en la copia antes de usarlos; no se inventaron vencimientos.`);
  await db.query('INSERT IGNORE INTO web_prestamo_tasas (prestamo_id, tasa_interes) SELECT id, 0.02 FROM prestamo');
  // Parse only the known literal account records, without evaluating Python or logging secrets.
  const python = await readFile(new URL('../../app/ui/login.py', import.meta.url), 'utf8');
  const block = python.split('self.usuarios = [')[1]?.split(']')[0];
  if (!block) throw new Error('No se encontró la lista original de usuarios.');
  const users = [...block.matchAll(/\{([^{}]+)\}/g)].map(match => {
    const fields = Object.fromEntries([...match[1].matchAll(/["'](id|rol|usuario|password)["']\s*:\s*["']([^"']*)["']/g)].map(m => [m[1], m[2]]));
    if (!fields.id || !fields.usuario || !fields.password || !['administrador', 'recepcionista', 'cobrador'].includes(fields.rol)) throw new Error('Formato de usuario Python no reconocido.');
    return fields;
  });
  if (!users.length) throw new Error('No se encontraron usuarios para importar.');
  for (const user of users) {
    const [found] = await db.execute('SELECT id FROM web_usuarios WHERE id = ? OR LOWER(TRIM(usuario)) = LOWER(?)', [user.id, user.usuario]);
    if (!found.length) await db.execute('INSERT INTO web_usuarios (id, usuario, password_hash, rol) VALUES (?, ?, ?, ?)', [user.id, user.usuario, await hashPassword(user.password), user.rol]);
  }
  console.log(`Base ${database} preparada. Usuarios originales importados sin cambiar cuentas existentes.`);
} finally { await db.end(); }
