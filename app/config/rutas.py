from pathlib import Path


PROYECTO_DIR = Path(__file__).resolve().parents[2]
IMAGENES_DIR = PROYECTO_DIR / "assets" / "img"
REPORTES_DIR = PROYECTO_DIR / "reportes"


def ruta_reporte(filename: str | Path) -> str:
    ruta = Path(filename)
    if not ruta.is_absolute():
        ruta = REPORTES_DIR / ruta
    ruta.parent.mkdir(parents=True, exist_ok=True)
    return str(ruta)
