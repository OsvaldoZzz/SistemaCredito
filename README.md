# Sistema de créditos

La nueva versión **React + JavaScript** está en [`web/`](web/README.md), con
interés del 15 % para préstamos nuevos y una copia independiente de MySQL.
La aplicación de escritorio también calcula el interés total al 15 % sobre
el capital; la mora se mantiene en 2 % mensual. Como la base original no guarda
la tasa por préstamo, el 15 % también se aplica al volver a calcular los
préstamos existentes.

Aplicación de escritorio con PySide6, MySQL y reportes PDF.

## Ejecutar

Instala las dependencias de Python desde la raíz del proyecto:

```powershell
python -m pip install -r requirements.txt
```

Desde la carpeta del proyecto:

```powershell
python LOGIN.py
```

Desde otra carpeta, ejecuta la ruta completa de `LOGIN.py`.
También puedes ejecutar `app/ui/login.py` directamente desde el IDE,
o usar `python -m app.ui.login` desde la carpeta del proyecto.
Las imágenes y los reportes usan rutas basadas en la ubicación del proyecto.

Las operaciones CRUD usan SQLAlchemy ORM sobre MySQL y el controlador
`mysql-connector-python`. Los modelos existentes se encuentran en
`app/datos/modelos.py`; las tablas originales se conservan. Las tablas de
abonos, solicitudes y asignaciones se crean al necesitarlas, y las columnas
adicionales de las tablas originales se agregan de forma compatible.

La conexión admite las variables `DB_HOST`, `DB_PORT`, `DB_USER`,
`DB_PASSWORD` y `DB_NAME`, configuradas en el entorno antes de iniciar.
La base de datos debe disponer de las tablas `clientes`, `prestamo` y
`usuarios` (con las columnas `id`, `rol`, `nombre` y `password`). El login
carga de `usuarios` las cuentas del personal; desde Administración, el botón
**Actualizar datos** de cobradores y recepcionistas guarda el nombre y la
contraseña modificados en MySQL. La tabla `cobrador_clientes`, que relaciona
cobradores con clientes, se crea automáticamente al cargar usuarios; MySQL
necesita permiso `CREATE` la primera vez.

## Mapa de clientes

Al crear clientes desde administración, recepción o cobranza se puede usar
**Marcar en el mapa**. El administrador también puede cambiar el punto desde
**Actualizar cliente**. La ubicación es opcional y se guarda con el formulario.
El cliente puede editarla en **Mi dirección y ubicación**. Administración y
cobranza tienen **Ver ubicación en el mapa**, con un botón para abrir la ruta
en Google Maps. Si el cliente todavía no marcó un punto, se muestra un aviso.

El mapa usa OpenStreetMap por defecto y requiere conexión a internet.
Para el visor integrado debe estar disponible `PySide6-Addons`:

```powershell
python -m pip install PySide6-Addons
```

Si falta ese componente, el selector muestra instrucciones y la consulta de
una ubicación guardada abre la ruta en el navegador.

Se conserva la adaptación de Google Maps del proyecto `sistema-credito-mapa`.
Para activarla, configura `GOOGLE_MAPS_API_KEY` o guarda la llave en
`SistCreditos/google_maps_key.txt` (ignorado por Git). La llave debe tener
habilitadas Maps JavaScript API y Geocoding API; si restringes referentes,
incluye `https://sistema-crediticio.local/*`.

Al consultar o crear clientes, el sistema comprueba las columnas `latitud` y
`longitud` y agrega las que falten como `DECIMAL(10, 7) NULL`. La cuenta de
MySQL necesita permiso `ALTER` para esta primera actualización. Los clientes
existentes conservan sus datos y comienzan sin ubicación. No es necesario
importar ni reemplazar la base de datos con el SQL del proyecto de origen.

## Organización

```text
SistCreditos/
├── LOGIN.py                 # Inicio de la aplicación
├── app/
│   ├── config/              # Conexión a MySQL y rutas del proyecto
│   ├── datos/               # Consultas y operaciones CRUD
│   ├── logica/              # Cálculos de préstamos y validaciones
│   ├── reportes/            # Generadores de documentos PDF
│   └── ui/                  # Login, paneles y diálogos
├── assets/
│   └── img/                 # Logotipo e iconos
├── docs/                    # Apuntes, pendientes e historial
└── reportes/                # Archivos PDF generados
```

Los módulos internos se importan mediante `app`, por ejemplo:
`from app.datos.clientes_crud import listar_clientes`.
El login admite ambos puntos de entrada; los demás módulos se cargan desde él.
Los archivos `__pycache__` los genera Python automáticamente y se ignoran
para archivos nuevos en Git.

Las reglas de entrada y el comando para ejecutar las pruebas están en
[docs/validaciones.md](docs/validaciones.md).
