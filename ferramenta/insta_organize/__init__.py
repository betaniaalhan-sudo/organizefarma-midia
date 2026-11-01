"""Ferramenta de Instagram da Organize Farma (Instagram API com Instagram Login)."""

from .cliente import ClienteInstagram, Configuracao, ErroInstagram
from .legenda import checar_legenda

__all__ = ["ClienteInstagram", "Configuracao", "ErroInstagram", "checar_legenda"]
__version__ = "1.0.0"
