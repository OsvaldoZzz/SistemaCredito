import os

from sqlalchemy import URL, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def crear_engine() -> Engine:
    """Crea un engine SQLAlchemy usando la configuración MySQL del entorno."""
    url = URL.create(
        drivername="mysql+mysqlconnector",
        username=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "familia4214"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_NAME", "db_sistema_prestamos"),
    )
    return create_engine(url, pool_pre_ping=True, pool_recycle=1800)


def configurar_engine(engine: Engine) -> None:
    """Configura el engine de la aplicación o uno aislado para pruebas."""
    global _engine, _session_factory
    if _engine is not None and _engine is not engine:
        _engine.dispose()
    _engine = engine
    _session_factory = sessionmaker(bind=engine, expire_on_commit=False)


def obtener_engine() -> Engine:
    global _engine
    if _engine is None:
        configurar_engine(crear_engine())
    return _engine


def obtener_sesion() -> Session:
    global _session_factory
    if _session_factory is None:
        configurar_engine(obtener_engine())
    return _session_factory()


def cerrar_engine() -> None:
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None
