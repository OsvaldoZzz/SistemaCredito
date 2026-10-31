import math


def validar_coordenadas(latitud, longitud):
    """Acepta un punto completo o una ubicación todavía sin marcar."""
    if latitud is None and longitud is None:
        return None, None
    try:
        if isinstance(latitud, bool) or isinstance(longitud, bool):
            raise ValueError
        lat, lng = float(latitud), float(longitud)
        if not (math.isfinite(lat) and math.isfinite(lng)
                and -90 <= lat <= 90 and -180 <= lng <= 180):
            raise ValueError
    except (ValueError, TypeError, OverflowError):
        raise ValueError("Selecciona una ubicación válida en el mapa.") from None
    return round(lat, 7), round(lng, 7)
