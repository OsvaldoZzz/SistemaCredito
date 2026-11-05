from mysql.connector import Error as MySQLConnectorError
from sqlalchemy.exc import SQLAlchemyError


ERRORES_BASE_DATOS = (MySQLConnectorError, SQLAlchemyError)
