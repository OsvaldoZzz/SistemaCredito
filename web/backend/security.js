import { randomBytes, scrypt as scryptCallback, timingSafeEqual } from 'node:crypto';
import { promisify } from 'node:util';
const scrypt = promisify(scryptCallback);
export async function hashPassword(value) {
  const salt = randomBytes(16).toString('hex');
  const hash = await scrypt(value, salt, 64);
  return `scrypt:${salt}:${hash.toString('hex')}`;
}
export async function verifyPassword(value, encoded) {
  const [scheme, salt, hash] = String(encoded).split(':');
  if (scheme !== 'scrypt' || !salt || !hash) return false;
  const actual = await scrypt(value, salt, 64), expected = Buffer.from(hash, 'hex');
  return actual.length === expected.length && timingSafeEqual(actual, expected);
}
export function equalPassword(value, stored) {
  const a = Buffer.from(String(value)), b = Buffer.from(String(stored));
  return a.length === b.length && timingSafeEqual(a, b);
}
