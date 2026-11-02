"""Consulta de dados bibliográficos na API pública da Open Library (https://openlibrary.org)."""
import json
import re
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

URL_API = "https://openlibrary.org/api/books"
TEMPO_LIMITE = 8  # segundos


class ErroConsultaAPI(Exception):
    """A API não respondeu (sem internet, fora do ar ou resposta inválida)."""


def normalizar_isbn(texto):
    """Remove hifens e espaços e confere se há 10 ou 13 caracteres válidos. Devolve None se inválido."""
    isbn = re.sub(r"[\s-]", "", texto or "").upper()
    if re.fullmatch(r"\d{13}", isbn) or re.fullmatch(r"\d{9}[\dX]", isbn):
        return isbn
    return None


def _extrair(dados):
    ano = re.search(r"\b(1[5-9]\d{2}|20\d{2})\b", dados.get("publish_date", ""))
    return {
        "titulo": dados.get("title", "").strip(),
        "autor": "; ".join(a.get("name", "") for a in dados.get("authors", [])),
        "editora": (dados.get("publishers") or [{}])[0].get("name", ""),
        "ano": int(ano.group(1)) if ano else None,
        "assunto": (dados.get("subjects") or [{}])[0].get("name", ""),
    }


def buscar_dados_isbn(isbn):
    """Devolve um dicionário com título, autor, editora, ano e assunto, ou None se o ISBN não for encontrado.

    Lança ErroConsultaAPI se a API não puder ser consultada.
    """
    isbn = normalizar_isbn(isbn)
    if isbn is None:
        raise ValueError("ISBN inválido")
    consulta = urlencode({"bibkeys": f"ISBN:{isbn}", "format": "json", "jscmd": "data"})
    pedido = Request(f"{URL_API}?{consulta}", headers={"User-Agent": "AcervoFacil/1.0 (projeto academico Univesp)"})
    try:
        with urlopen(pedido, timeout=TEMPO_LIMITE) as resposta:
            corpo = json.loads(resposta.read().decode("utf-8"))
    except (URLError, TimeoutError, ValueError, OSError) as erro:
        raise ErroConsultaAPI(str(erro)) from erro
    dados = corpo.get(f"ISBN:{isbn}")
    return _extrair(dados) if dados else None
