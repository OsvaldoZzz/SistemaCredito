# Sistema de créditos

Aplicación de escritorio con PySide6, MySQL y reportes PDF.

## Ejecutar

Desde la carpeta del proyecto:

```powershell
python LOGIN.py
```

Desde otra carpeta, ejecuta la ruta completa de `LOGIN.py`.
También puedes ejecutar `app/ui/login.py` directamente desde el IDE,
o usar `python -m app.ui.login` desde la carpeta del proyecto.
Las imágenes y los reportes usan rutas basadas en la ubicación del proyecto.

Dependencias: `PySide6`, `mysql-connector-python` y `reportlab`.
La conexión admite las variables `DB_HOST`, `DB_PORT`, `DB_USER`,
`DB_PASSWORD` y `DB_NAME`, configuradas en el entorno antes de iniciar.
La base de datos debe disponer de las tablas `clientes` y `prestamo`.

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
