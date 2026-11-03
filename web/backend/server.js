import { createApp } from './app.js';
import { pool } from './db.js';
const port = Number(process.env.PORT || 3001), host = process.env.HOST || '127.0.0.1';
const server = createApp().listen(port, host, () => console.log(`SistCreditos API: http://${host}:${port}`));
server.on('error', error => { console.error('No se pudo iniciar el servidor:', error.code); process.exitCode = 1; });
async function stop() { server.close(); await pool.end(); }
process.on('SIGINT', stop);
process.on('SIGTERM', stop);
