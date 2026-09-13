import os

import mysql.connector
from mysql.connector import MySQLConnection


def obtener_conexion() -> MySQLConnection:
    """Abre una conexión nueva para una operación de base de datos."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "familia4214"),
        database=os.getenv("DB_NAME", "db_sistema_prestamos")
    )
