import re
from datetime import date
from decimal import Decimal, InvalidOperation


MAX_MONTO = Decimal("100000000")


def validar_id(valor: int) -> None:
    if type(valor) is not int or valor <= 0:
        raise ValueError("El identificador debe ser un entero mayor que cero.")


def validar_monto(valor, permitir_cero=False) -> Decimal:
    try:
        monto = Decimal(str(valor))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("Ingresa un monto numérico válido.") from None
    if not monto.is_finite() or monto < 0 or monto > MAX_MONTO:
        raise ValueError("El monto debe estar entre 0 y C$ 100,000,000.")
    if not permitir_cero and monto < Decimal("0.01"):
        raise ValueError("El monto debe ser de al menos C$ 0.01.")
    if monto != monto.quantize(Decimal("0.01")):
        raise ValueError("El monto solo puede tener dos decimales.")
    return monto


def validar_plazo(plazo: int) -> None:
    if type(plazo) is not int or not 1 <= plazo <= 360:
        raise ValueError("El plazo debe ser un entero entre 1 y 360 cuotas.")


def validar_condiciones_prestamo(monto, plazo):
    monto = validar_monto(monto)
    validar_plazo(plazo)
    if monto * 100 < plazo:
        raise ValueError("El monto no alcanza para distribuir al menos un centavo de capital por cuota.")
    return monto


def validar_fecha(fecha: date, permitir_pasada=False) -> None:
    if type(fecha) is not date:
        raise ValueError("Selecciona una fecha válida.")
    if not permitir_pasada and fecha < date.today():
        raise ValueError("La fecha no puede ser anterior a hoy.")


def validar_password(password: str) -> str | None:
    if not isinstance(password, str) or not password.strip():
        return "Ingresa una contraseña."
    if not 8 <= len(password) <= 128:
        return "La contraseña debe tener entre 8 y 128 caracteres."
    if any(ord(c) < 32 or ord(c) == 127 for c in password):
        return "La contraseña no puede contener saltos de línea ni caracteres de control."
    return None


def validar_datos_rol(usuario, password, rol, usuarios, excluir_id=None):
    if not isinstance(usuario, str) or not re.fullmatch(r"[\w.-]{2,100}", usuario.strip()):
        return "El usuario debe tener entre 2 y 100 letras, números, puntos, guiones o guiones bajos."
    if rol not in ("administrador", "recepcionista", "cobrador"):
        return "Selecciona un rol válido."
    error = validar_password(password)
    if error:
        return error
    if any(u.get("id") != excluir_id and u["usuario"].strip().casefold() == usuario.strip().casefold() for u in usuarios):
        return "Ya existe un usuario con ese nombre."
    return None


def validar_campos_login(usuario: str, password: str) -> str | None:
    if not usuario.strip():
        return "Ingresa tu usuario o correo."
    if not password.strip():
        return "Ingresa tu contraseña."
    if "@" in usuario and not re.fullmatch(
        r"[^@\s]+@[^@\s]+\.[^@\s]+",
        usuario.strip(),
    ):
        return "Ingresa un correo electrónico válido."
    if len(usuario.strip()) > 254 or len(password) > 128:
        return "El usuario o la contraseña exceden la longitud permitida."
    return None


def validar_datos_cliente(
    nombre: str,
    cedula: str,
    correo: str,
    password: str,
    direccion: str,
) -> str | None:
    if not all(
        isinstance(valor, str) and valor.strip()
        for valor in (nombre, cedula, correo, password, direccion)
    ):
        return "Todos los campos son obligatorios."
    if not 2 <= len(nombre.strip()) <= 80 or not any(c.isalpha() for c in nombre):
        return "El nombre debe tener entre 2 y 80 caracteres e incluir letras."
    if any(not (c.isalpha() or c in " '-.") for c in nombre.strip()):
        return "El nombre solo puede contener letras, espacios, apóstrofos, puntos y guiones."
    if not re.fullmatch(r"[A-Za-z0-9-]{6,20}", cedula.strip()):
        return "La cédula debe tener entre 6 y 20 letras, números o guiones."
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", correo.strip()):
        return "Ingresa un correo electrónico válido."
    if len(correo.strip()) > 100:
        return "El correo no puede superar los 100 caracteres."
    error = validar_password(password)
    if error:
        return error
    if not 5 <= len(direccion.strip()) <= 40:
        return "La dirección debe tener entre 5 y 40 caracteres."
    if any(ord(c) < 32 or ord(c) == 127 for c in direccion):
        return "La dirección no puede contener caracteres de control."
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
