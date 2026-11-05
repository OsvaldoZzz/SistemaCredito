import unittest

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.config.conexion import cerrar_engine, configurar_engine
from app.datos.modelos import Base


class OrmTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        configurar_engine(cls.engine)

    @classmethod
    def tearDownClass(cls):
        cerrar_engine()
        super().tearDownClass()

    def setUp(self):
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
