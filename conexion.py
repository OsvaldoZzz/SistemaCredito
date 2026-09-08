import mysql.connector
from mysql.connector import errorcode

conexion = None

try:
    conexion = mysql.connector.connect(
        host="localhost",
        port=3306,
        user="roor",
        password= "familia4214",
        database="db_sistema_prestamos"
    )

    if conexion.is_connected():
        print("Conexion estable.")

except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Error de autenticacion: usuario o contraseña incorrectos.")
    elif err.errno == errorcode.ER_BAD_DB_ERROR: 
        print("ERROR: La base de datos no existe.")
    else:
        print(f"Error imprevisto de base de datos: {err}")

finally:
    if conexion is not None and conexion.is_connected():
        conexion.close()
        print("Conexion cerrada de forma segura. :)")



