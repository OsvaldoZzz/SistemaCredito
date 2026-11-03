# SistCreditos web

Versión React + JavaScript del sistema de escritorio. El servidor usa Node.js,
Express y MySQL. La aplicación Python se sigue ejecutando con `python LOGIN.py`
desde la carpeta superior y conserva su base de datos original.

## Ejecutar en este equipo

La copia `db_sistema_prestamos_web` y el archivo local `.env` ya están preparados.
Desde PowerShell:

```powershell
cd C:\Users\5590\OneDrive\Documentos\Javascript\SistCreditos\web
npm run dev
```

Abre **http://127.0.0.1:5173**. La API escucha en `127.0.0.1:3001`.
MySQL debe estar iniciado. Detén el desarrollo con **Ctrl+C**.

El personal usa los mismos usuarios y contraseñas definidos en el login Python.
Los clientes usan sus correos y contraseñas originales. No hay cuentas de prueba
permanentes. Las contraseñas de la copia web se guardan con scrypt y no se envían
al navegador. Los cambios hechos en la web no se sincronizan con Python.

## Reglas conservadas y cambio de interés

- Los préstamos nuevos tienen **15 % fijo sobre el capital**, distribuido entre
  sus cuotas. No se multiplica por el número de meses. C$1,000 generan C$150.
- Los préstamos históricos importados mantienen **2 %**. La tasa se guarda por
  préstamo en `web_prestamo_tasas`; no se recalculan deudas anteriores al 15 %.
- La mora sigue siendo **2 % mensual**, prorrateada por días sobre el saldo de la
  cuota. Los abonos cubren primero mora y luego capital más interés de esa cuota.
- Los importes se calculan con `decimal.js`. Los centavos restantes se colocan
  en la última cuota. Frecuencias: semanal (7 días), quincenal (15) y mensual.
- No se emite otro préstamo mientras el cliente tenga saldo pendiente.
- El monto y plazo no pueden cambiar después del primer abono. Un préstamo con
  saldo no puede marcarse como pagado. Los abonos se registran en transacciones.

## Módulos y permisos

| Rol | Funciones |
| --- | --- |
| Administración | Clientes, préstamos, cuotas y abonos, solicitudes y decisiones, citas, usuarios, asignaciones y reportes |
| Recepción | Crear/editar/eliminar clientes, consultar préstamos y registrar abonos, enviar solicitudes, consultar citas y reportes |
| Cobranza | Consultar clientes asignados, crear clientes que quedan asignados a su cuenta, consultar préstamos, registrar abonos y descargar reportes de su cartera |
| Cliente | Consultar sus préstamos, cuotas y recibos, agendar y consultar sus citas, actualizar su dirección y ubicación |

Los usuarios y asignaciones del personal ahora persisten en MySQL. La versión
Python guardaba esas modificaciones solo en memoria: se importan sus cuentas
iniciales, y administración asigna los clientes a cada cobrador en **Usuarios y
roles → Asignar clientes**. Recepción y administración tienen acceso por rol.

Los mapas usan Leaflet y OpenStreetMap; sus imágenes requieren internet. Las
fuentes tienen alternativas locales si Google Fonts no está disponible.

## Instalar en otro equipo

Requisitos: Node.js 22.12 o superior, npm y MySQL compatible con el esquema
original. Instala las dependencias:

```powershell
npm ci
```

Para copiar la base Python local sin ejecutar Python:

```powershell
npm run db:copy
npm run db:prepare
```

`db:copy` lee los valores predeterminados de `../app/config/conexion.py`. Si el
origen usa otras credenciales, configura `PY_DB_HOST`, `PY_DB_PORT`, `PY_DB_USER`,
`PY_DB_PASSWORD` y `PY_DB_NAME` en el entorno. No se imprimen las credenciales.
Si no hay `.env`, se genera uno local con la conexión y el destino `_web`.

La copia exige tablas InnoDB, usa una instantánea de lectura y verifica cantidades.
Se niega a sobrescribir destinos que ya tengan tablas. Si hay vistas o triggers,
requiere exportación completa con MySQL Workbench. No elimina bases ante errores.
No repitas la copia sobre la base web que ya contiene datos.

Para una base vacía o una copia ya importada, crea `.env` a partir de
`.env.example`, configura la conexión y ejecuta `npm run db:prepare`.
El nombre debe terminar en `_web` o `_test`, y debe ser distinto de la base Python.
La preparación agrega las tablas web, importa las cuentas iniciales y adapta
contraseñas y columnas **solo en el destino**. Los préstamos sin fecha de primer
pago se notifican para completar sus fechas reales en la copia, sin inventarlas.

## Compilar y ejecutar la versión compilada

```powershell
npm run build
npm start
```

Abre **http://127.0.0.1:3001**. El servidor entrega la interfaz compilada y la API.
Las sesiones duran ocho horas, se
guardan en memoria y se cierran al reiniciar el servidor. Tras tres intentos
fallidos se bloquea ese usuario y dirección durante quince minutos.

## Netlify y servidor de datos

Netlify publica la interfaz. Express debe estar ejecutándose en un servidor
HTTPS accesible desde internet, con conexión a la base MySQL web ya preparada.
La carpeta `dist` por sí sola no contiene el servidor ni los datos. Una dirección
`localhost` en otro equipo no permite acceder al MySQL de esta computadora.

1. En el alojamiento de Express, configura `HOST=0.0.0.0`, `COOKIE_SECURE=true`,
   `APP_ORIGIN=https://tu-sitio.netlify.app` y las variables `DB_*` de la base
   web accesible desde ese servidor. Ejecuta `npm start`. Conserva una sola
   instancia mientras las sesiones se guarden en memoria.
2. En Netlify, selecciona `SistCreditos/web` como directorio base si el
   repositorio contiene la carpeta `SistCreditos`; si el repositorio comienza
   directamente en `web`, usa ese directorio como base. La configuración
   `netlify.toml` usa `npm run build:netlify` y publica `dist`.
3. Agrega la variable de compilación `API_SERVER_URL` con el origen público de
   Express, por ejemplo `https://tu-servidor.example.com`, sin `/api`. Vuelve a
   desplegar. La compilación genera `dist/_redirects` y conserva `/api` antes
   de la regla de navegación de React. Las cookies y los PDF usan esa misma ruta.
4. Comprueba `https://tu-servidor.example.com/api/health` y después
   `https://tu-sitio.netlify.app/api/health`: ambos deben devolver JSON con
   `"ok": true`. Si el primero falla, revisa Express/MySQL; si solo falla el
   segundo, revisa `API_SERVER_URL` y el nuevo despliegue.

Para subir una carpeta manualmente, configura `API_SERVER_URL` en el entorno
local y ejecuta `npm run build:netlify`; sube la carpeta `dist` resultante.
`npm run build` sigue disponible para servir la web directamente con Express.
No publiques `.env` ni credenciales de MySQL en variables `VITE_*`.

## Verificación

```powershell
npm test
npm run test:integration
npm run build
npm run test:browser
```

Las pruebas unitarias no necesitan MySQL. Las de integración y navegador usan la
base del `.env`, crean registros temporales con identificadores aleatorios y los
eliminan al terminar. No cambian los registros importados. Las pruebas de
navegador usan Edge instalado; se puede configurar `BROWSER_CHANNEL=chrome` para
Chrome. Las capturas locales se guardan en `test-results/`, ignorado por Git.

## Organización

```text
backend/
  app.js          API, autenticación, sesiones y permisos
  service.js      Operaciones y transacciones con MySQL
  domain.js       Validaciones, cuotas, interés y mora
  reports.js      Reportes y recibos PDF
  prepare.js      Preparación explícita de la base web
  copy-database.js Copia independiente de la base original
  tests/          Pruebas de cálculos y API
frontend/
  src/main.jsx    Pantallas, formularios y navegación por rol
  src/Map.jsx     Selector y consulta de ubicación
  src/styles.css  Diseño adaptable a escritorio y móvil
scripts/
  dev.js          Servidor y cliente durante el desarrollo
  browser-test.js Pruebas de navegador con datos temporales
```

No subas `.env`, copias de la base ni credenciales al repositorio.
