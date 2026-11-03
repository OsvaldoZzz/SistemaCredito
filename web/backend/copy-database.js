import mysql from 'mysql2/promise';
import { readFile, writeFile } from 'node:fs/promises';
import { databaseConfig } from './db.js';

// Read only the os.getenv defaults in the original config; never execute Python.
const sourceText = await readFile(new URL('../../app/config/conexion.py', import.meta.url), 'utf8');
const defaults = Object.fromEntries([...sourceText.matchAll(/os\.getenv\("(DB_[A-Z_]+)",\s*"([^"\r\n]*)"\)/g)].map(m => [m[1], m[2]]));
if (!defaults.DB_NAME || !defaults.DB_HOST || !defaults.DB_USER) throw new Error('No se reconoció la configuración Python. No se copió ningún dato.');
const destination = databaseConfig();
const sourceConfig = {
  host: process.env.PY_DB_HOST || defaults.DB_HOST,
  port: Number(process.env.PY_DB_PORT || defaults.DB_PORT || 3306),
  user: process.env.PY_DB_USER || defaults.DB_USER,
  password: process.env.PY_DB_PASSWORD ?? defaults.DB_PASSWORD ?? '',
  database: process.env.PY_DB_NAME || defaults.DB_NAME,
  dateStrings: true, charset: 'utf8mb4', timezone: '-06:00',
};
if (sourceConfig.database.toLowerCase() === destination.database.toLowerCase()) throw new Error('El origen y destino deben ser bases diferentes.');
// If no web .env exists, use the local Python connection credentials for the copy.
let envExists = true;
try { await readFile(new URL('../.env', import.meta.url)); } catch (e) { if (e.code === 'ENOENT') envExists = false; else throw e; }
if (!envExists) Object.assign(destination, { host: sourceConfig.host, port: sourceConfig.port, user: sourceConfig.user, password: sourceConfig.password });
const { database, connectionLimit, ...destinationConfig } = destination;
const source = await mysql.createConnection(sourceConfig);
let target;
try {
  target = await mysql.createConnection(destinationConfig);
  await source.query("SET time_zone = '-06:00'");
  await target.query("SET time_zone = '-06:00'");
  const [tables] = await source.query("SELECT TABLE_NAME AS name, ENGINE AS engine FROM information_schema.TABLES WHERE TABLE_SCHEMA = ? AND TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME", [sourceConfig.database]);
  if (!tables.length) throw new Error('La base origen no contiene tablas.');
  if (tables.some(t => t.engine !== 'InnoDB')) throw new Error('La copia consistente requiere tablas InnoDB. No se modificó el origen.');
  const [triggers] = await source.query('SELECT COUNT(*) AS total FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA = ?', [sourceConfig.database]);
  const [views] = await source.query("SELECT COUNT(*) AS total FROM information_schema.TABLES WHERE TABLE_SCHEMA = ? AND TABLE_TYPE = 'VIEW'", [sourceConfig.database]);
  if (triggers[0].total || views[0].total) throw new Error('El origen contiene vistas o triggers. Requiere exportación completa con MySQL Workbench para conservarlos.');
  const [existing] = await target.query('SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = ?', [database]);
  if (existing.length) throw new Error(`La base ${database} ya contiene tablas. No se sobrescribió. Usa otro DB_NAME terminado en _web.`);
  const envEntries = { DB_HOST: destination.host, DB_PORT: String(destination.port), DB_USER: destination.user, DB_PASSWORD: destination.password, DB_NAME: database, PORT: '3001', HOST: '127.0.0.1', COOKIE_SECURE: 'false' };
  if (Object.values(envEntries).some(v => /['\r\n]/.test(String(v)))) throw new Error('Configura .env manualmente: los valores contienen caracteres no admitidos por el generador.');
  await target.query('CREATE DATABASE IF NOT EXISTS ?? CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci', [database]);
  await target.changeUser({ database });
  await target.query('SET FOREIGN_KEY_CHECKS = 0');
  await source.query('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');
  await source.query('START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY');
  const counts = [];
  for (const table of tables) {
    const [ddl] = await source.query('SHOW CREATE TABLE ??', [table.name]);
    const create = ddl[0]['Create Table'];
    if (create.includes(`\`${sourceConfig.database}\`.`)) throw new Error('El esquema contiene referencias explícitas al origen. Se detuvo la copia.');
    await target.query(create);
    const [columns] = await source.query('SHOW COLUMNS FROM ??', [table.name]);
    const fields = columns.filter(c => !/GENERATED/.test(c.Extra)).map(c => c.Field);
    let offset = 0;
    while (true) {
      const [rows] = await source.query('SELECT ?? FROM ?? LIMIT 500 OFFSET ?', [fields, table.name, offset]);
      if (!rows.length) break;
      await target.query('INSERT INTO ?? (??) VALUES ?', [table.name, fields, rows.map(row => fields.map(f => row[f]))]);
      offset += rows.length;
    }
    const [[count]] = await target.query('SELECT COUNT(*) AS total FROM ??', [table.name]);
    if (Number(count.total) !== offset) throw new Error(`No coincide la cantidad copiada en ${table.name}.`);
    counts.push({ tabla: table.name, registros: offset });
  }
  await source.commit();
  await target.query('SET FOREIGN_KEY_CHECKS = 1');
  if (!envExists) await writeFile(new URL('../.env', import.meta.url), Object.entries(envEntries).map(([k, v]) => `${k}='${v}'`).join('\n') + '\n', { flag: 'wx' });
  console.table(counts);
  console.log(`Copia verificada en ${database}. La base Python quedó intacta. Siguiente: npm run db:prepare`);
} catch (e) {
  await source.rollback().catch(() => {});
  console.error('La copia no se completó:', e.code || e.message);
  console.error('No se eliminó ni sobrescribió el origen. Si el destino tiene tablas parciales, usa otro nombre de base antes de reintentar.');
  process.exitCode = 1;
} finally { await source.end(); if (target) await target.end(); }
