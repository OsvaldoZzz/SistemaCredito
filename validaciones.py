import re


def validar_campos_login(usuario: str, password: str) -> str | None:
    if not usuario.strip():
        return "Ingresa tu usuario o correo."
    if not password:
        return "Ingresa tu contraseña."
    if "@" in usuario and not re.fullmatch(
        r"[^@\s]+@[^@\s]+\.[^@\s]+",
        usuario.strip(),
    ):
        return "Ingresa un correo electrónico válido."
    return None


def validar_datos_cliente(
    nombre: str,
    cedula: str,
    correo: str,
    password: str,
    direccion: str,
) -> str | None:
    if not all(
        valor.strip()
        for valor in (nombre, cedula, correo, password, direccion)
    ):
        return "Todos los campos son obligatorios."
    if len(nombre.strip()) < 2:
        return "El nombre debe tener al menos 2 caracteres."
    if not re.fullmatch(r"[A-Za-z0-9-]{6,20}", cedula.strip()):
        return "La cédula debe tener entre 6 y 20 letras, números o guiones."
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", correo.strip()):
        return "Ingresa un correo electrónico válido."
    if len(password) < 8:
        return "La contraseña debe tener al menos 8 caracteres."
    if len(direccion.strip()) < 5:
        return "La dirección debe tener al menos 5 caracteres."
    return None


def validar_cliente_unico(
    clientes: list[dict],
    cedula: str,
    correo: str,
) -> str | None:
    cedula_normalizada = cedula.strip().casefold()
    correo_normalizado = correo.strip().casefold()
    for cliente in clientes:
        if str(cliente.get("cedula") or "").strip().casefold() == cedula_normalizada:
            return "Ya existe un cliente con esa cédula."
        if str(cliente.get("correo") or "").strip().casefold() == correo_normalizado:
            return "Ya existe un cliente con ese correo."
    return None
