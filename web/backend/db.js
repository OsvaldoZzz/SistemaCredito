import mysql from 'mysql2/promise';
import { AppError } from './domain.js';

export function databaseConfig() {
  const database = process.env.DB_NAME || 'db_sistema_prestamos_web';
  if (!/^[A-Za-z0-9_]+_(web|test)$/.test(database)) throw new AppError('DB_NAME debe terminar en _web o _test. Usa una copia de la base Python.', 503);
  return { host: process.env.DB_HOST || 'localhost', port: Number(process.env.DB_PORT || 3306),
    user: process.env.DB_USER || 'root', password: process.env.DB_PASSWORD || '', database,
    dateStrings: true, charset: 'utf8mb4', connectionLimit: 5, timezone: '-06:00' };
}
export const pool = mysql.createPool(databaseConfig());
pool.on('connection', c => c.query("SET time_zone = '-06:00'"));
export async function query(sql, params = [], db = pool) {
  const [result] = await db.execute(sql, params);
  return result;
}
export async function transaction(work) {
  const c = await pool.getConnection();
  try { await c.beginTransaction(); const result = await work(c); await c.commit(); return result; }
  catch (e) { await c.rollback(); throw e; }
  finally { c.release(); }
}
