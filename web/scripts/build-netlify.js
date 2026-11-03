import { writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { build } from 'vite';

// Keep /api on the frontend origin so session cookies and PDF links work.
const value = process.env.API_SERVER_URL;
if (!value) throw new Error('Configura API_SERVER_URL en Netlify con la URL HTTPS pública del servidor Express.');
const upstream = new URL(value);
if (upstream.protocol !== 'https:' || upstream.username || upstream.password ||
    upstream.search || upstream.hash || upstream.pathname !== '/' ||
    ['localhost', '127.0.0.1', '[::1]'].includes(upstream.hostname)) {
  throw new Error('API_SERVER_URL debe ser el origen HTTPS público del servidor, sin /api, credenciales ni parámetros.');
}

await build({ configFile: fileURLToPath(new URL('../frontend/vite.config.js', import.meta.url)) });
await writeFile(new URL('../dist/_redirects', import.meta.url),
  `/api/* ${upstream.origin}/api/:splat 200!\n/* /index.html 200\n`);
