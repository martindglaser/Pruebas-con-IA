import re
from bs4 import BeautifulSoup

def limpiar_html(raw_html: str, max_len: int = 80000) -> str:
    """
    Limpia el HTML crudo, eliminando scripts, styles y exceso de saltos de línea.
    """
    soup = BeautifulSoup(raw_html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    limpio = soup.get_text(separator="\n")
    limpio = re.sub(r"\n{3,}", "\n\n", limpio).strip()
    return limpio[:max_len]