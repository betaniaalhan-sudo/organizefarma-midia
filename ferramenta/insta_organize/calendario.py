"""Calendário de conteúdo em CSV.

Colunas (separador ; ou ,):
  data_hora   AAAA-MM-DD HH:MM (horário de Brasília)
  tipo        imagem | carrossel | reel | story
  midias      URL(s) públicas; no carrossel, separe por |
  legenda     texto do post
  capa        (opcional) URL da capa do Reel
  status      vazio = pendente; o programa preenche com publicado/erro
  media_id    preenchido pelo programa
  observacao  preenchido pelo programa

Rodar sem --executar só simula: mostra o que seria publicado e os alertas
da checagem de legenda, sem tocar no Instagram.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .cliente import ClienteInstagram, ErroInstagram
from .legenda import checar_legenda

BRASILIA = timezone(timedelta(hours=-3))
COLUNAS = ["data_hora", "tipo", "midias", "legenda", "capa", "status", "media_id", "observacao"]
TIPOS = {"imagem", "carrossel", "reel", "story"}


@dataclass
class ItemResultado:
    linha: int
    tipo: str
    acao: str
    detalhe: str


def _ler(caminho: Path) -> tuple[list[dict], str]:
    texto = caminho.read_text(encoding="utf-8-sig")
    amostra = texto.splitlines()[0] if texto else ""
    sep = ";" if amostra.count(";") > amostra.count(",") else ","
    leitor = csv.DictReader(texto.splitlines(), delimiter=sep)
    linhas = [{c: (l.get(c) or "").strip() for c in COLUNAS} for l in leitor]
    return linhas, sep


def _gravar(caminho: Path, linhas: list[dict], sep: str) -> None:
    with caminho.open("w", encoding="utf-8-sig", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUNAS, delimiter=sep)
        escritor.writeheader()
        escritor.writerows(linhas)


def _data(valor: str) -> datetime:
    for formato in ("%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(valor, formato).replace(tzinfo=BRASILIA)
        except ValueError:
            continue
    raise ValueError(f"Data inválida: '{valor}'. Use AAAA-MM-DD HH:MM ou DD/MM/AAAA HH:MM.")


def processar(caminho: str | Path, cliente: ClienteInstagram | None, *, executar: bool = False,
              agora: datetime | None = None, ignorar_alertas: bool = False) -> list[ItemResultado]:
    caminho = Path(caminho)
    linhas, sep = _ler(caminho)
    agora = agora or datetime.now(BRASILIA)
    resultados: list[ItemResultado] = []
    alterou = False

    for n, item in enumerate(linhas, start=2):  # linha 1 é o cabeçalho
        if item["status"].lower() == "publicado":
            continue
        tipo = item["tipo"].lower()
        try:
            quando = _data(item["data_hora"])
        except ValueError as e:
            resultados.append(ItemResultado(n, tipo, "erro", str(e)))
            continue
        if quando > agora:
            resultados.append(ItemResultado(n, tipo, "aguardando", quando.strftime("%d/%m/%Y %H:%M")))
            continue
        if tipo not in TIPOS:
            resultados.append(ItemResultado(n, tipo, "erro", f"Tipo '{tipo}' desconhecido. Use: {', '.join(sorted(TIPOS))}."))
            continue
        midias = [m.strip() for m in item["midias"].split("|") if m.strip()]
        if not midias:
            resultados.append(ItemResultado(n, tipo, "erro", "Sem URL de mídia."))
            continue

        checagem = checar_legenda(item["legenda"])
        if checagem.bloqueia and not ignorar_alertas:
            item["status"] = "bloqueado"
            item["observacao"] = "; ".join(f"{a.trecho}: {a.base}" for a in checagem.alertas if a.nivel == "ALTO")
            alterou = True
            resultados.append(ItemResultado(n, tipo, "bloqueado", checagem.resumo()))
            continue

        if not executar:
            detalhe = f"{len(midias)} mídia(s). " + checagem.resumo()
            resultados.append(ItemResultado(n, tipo, "simulado", detalhe))
            continue

        try:
            if tipo == "imagem":
                mid = cliente.publicar_imagem(midias[0], item["legenda"])
            elif tipo == "carrossel":
                mid = cliente.publicar_carrossel(midias, item["legenda"])
            elif tipo == "reel":
                mid = cliente.publicar_reel(midias[0], item["legenda"], capa_url=item["capa"] or None)
            else:
                mid = cliente.publicar_story(midias[0])
            item.update(status="publicado", media_id=mid,
                        observacao=f"publicado em {datetime.now(BRASILIA):%d/%m/%Y %H:%M}")
            resultados.append(ItemResultado(n, tipo, "publicado", mid))
        except ErroInstagram as e:
            item.update(status="erro", observacao=str(e)[:300])
            resultados.append(ItemResultado(n, tipo, "erro", str(e)))
        alterou = True

    if alterou:
        # Em simulação, só os bloqueios mudam o arquivo (para a revisão ficar registrada).
        _gravar(caminho, linhas, sep)
    return resultados


def criar_modelo(caminho: str | Path) -> Path:
    caminho = Path(caminho)
    exemplo = [
        {"data_hora": "2026-11-10 09:00", "tipo": "carrossel",
         "midias": "https://SEU-SITE/slide1.jpg|https://SEU-SITE/slide2.jpg|https://SEU-SITE/slide3.jpg",
         "legenda": "SNCR: o que a farmácia precisa conferir antes de dispensar uma receita eletrônica. "
                    "Salve este post e compartilhe com a equipe. #farmacia #anvisa #SNCR",
         "capa": "", "status": "", "media_id": "", "observacao": ""},
        {"data_hora": "2026-11-12 18:30", "tipo": "reel",
         "midias": "https://SEU-SITE/reel-glp1.mp4",
         "legenda": "Receita de GLP-1: validade de 90 dias e retenção obrigatória (IN 360/2025). "
                    "Dúvidas? Fale com a Organize Farma.",
         "capa": "https://SEU-SITE/capa-glp1.jpg", "status": "", "media_id": "", "observacao": ""},
    ]
    _gravar(caminho, exemplo, ";")
    return caminho
