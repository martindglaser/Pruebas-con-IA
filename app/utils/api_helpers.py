import re

def extraer_retry_delay(e: Exception, fallback: int = 60) -> int:
    """Extrae el tiempo de espera de un error de API."""
    s = str(e)
    m = re.search(r"retry[_\s-]?delay\s*{\s*seconds:\s*(\d+)", s, re.I)
    if m:
        return int(m.group(1))
    m = re.search(r"Retry-After:\s*(\d+)", s, re.I)
    if m:
        return int(m.group(1))
    return fallback

def es_429(e: Exception) -> bool:
    """Verifica si la excepción es un error de tipo 429 (Resource Exhausted)."""
    s = str(e).lower()
    return ("429" in s) or ("resource exhausted" in s) or ("quota" in s)