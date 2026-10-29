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
