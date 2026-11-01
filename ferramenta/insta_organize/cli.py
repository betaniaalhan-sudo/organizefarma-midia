"""Linha de comando: python -m insta_organize <comando> [opções]

Configuração (arquivo .env na pasta do projeto ou variáveis de ambiente):
  IG_ACCESS_TOKEN   token de longa duração (60 dias)
  IG_USER_ID        id da conta Instagram (opcional; padrão "me")
  IG_APP_SECRET     só para trocar token curto por longo
  IG_API_VERSION    opcional; padrão v26.0
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

from . import calendario
from .cliente import (HOST_PADRAO, METRICAS_CONTA, VERSAO_PADRAO, ClienteInstagram,
                      Configuracao, ErroInstagram)
from .legenda import checar_legenda


def carregar_env(caminho: Path = Path(".env")) -> None:
    if not caminho.exists():
        return
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        os.environ.setdefault(chave.strip(), valor.strip().strip('"').strip("'"))


def _cliente() -> ClienteInstagram:
    token = os.environ.get("IG_ACCESS_TOKEN", "")
    if not token:
        raise SystemExit("Falta IG_ACCESS_TOKEN. Veja o passo a passo em LEIA-ME.md, seção 2.")
    # Token do login do Instagram (IG...) usa graph.instagram.com;
    # token do login do Facebook/empresas (EAA...) usa graph.facebook.com.
    host = os.environ.get("IG_HOST") or (
        "https://graph.facebook.com" if token.startswith("EA") else HOST_PADRAO)
    return ClienteInstagram(Configuracao(
        token=token,
        ig_user_id=os.environ.get("IG_USER_ID", "me") or "me",
        versao=os.environ.get("IG_API_VERSION", VERSAO_PADRAO) or VERSAO_PADRAO,
        host=host,
    ))


def _mostrar(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def _checar_ou_parar(legenda: str, forcar: bool) -> None:
    r = checar_legenda(legenda)
    print(r.resumo())
    if r.bloqueia and not forcar:
        raise SystemExit("\nPublicação interrompida por alerta ALTO. Ajuste a legenda "
                         "ou use --forcar depois de revisar.")


def _ler_legenda(args) -> str:
    if getattr(args, "arquivo_legenda", None):
        return Path(args.arquivo_legenda).read_text(encoding="utf-8").strip()
    return args.legenda or ""


def montar_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="insta_organize",
                                description="Instagram da Organize Farma via API oficial da Meta.")
    sub = p.add_subparsers(dest="comando", required=True)

    s = sub.add_parser("verificar-legenda", help="Checa a legenda contra a RDC 96/2008 (não precisa de token).")
    s.add_argument("legenda", nargs="?")
    s.add_argument("--arquivo-legenda")

    sub.add_parser("conta", help="Mostra dados do perfil.")
    sub.add_parser("limite", help="Mostra quantas publicações via API ainda cabem nas últimas 24 h.")

    for nome, ajuda in (("publicar-imagem", "Publica uma imagem JPEG."),
                        ("publicar-reel", "Publica um Reel (MP4)."),
                        ("publicar-story", "Publica um story (imagem ou vídeo).")):
        s = sub.add_parser(nome, help=ajuda)
        s.add_argument("url", help="URL pública da mídia.")
        if nome != "publicar-story":
            s.add_argument("--legenda", default="")
            s.add_argument("--arquivo-legenda")
            s.add_argument("--forcar", action="store_true", help="Publica mesmo com alerta ALTO.")
        if nome == "publicar-imagem":
            s.add_argument("--alt", help="Texto alternativo (acessibilidade).")
        if nome == "publicar-reel":
            s.add_argument("--capa", help="URL da capa.")
            s.add_argument("--so-reels", action="store_true", help="Não mostrar no feed.")

    s = sub.add_parser("publicar-carrossel", help="Publica carrossel (2 a 20 mídias).")
    s.add_argument("urls", nargs="+")
    s.add_argument("--legenda", default="")
    s.add_argument("--arquivo-legenda")
    s.add_argument("--forcar", action="store_true")

    s = sub.add_parser("posts", help="Lista os posts recentes.")
    s.add_argument("--limite", type=int, default=12)

    s = sub.add_parser("metricas-conta", help="Métricas da conta no período.")
    s.add_argument("--desde", help="AAAA-MM-DD")
    s.add_argument("--ate", help="AAAA-MM-DD")
    s.add_argument("--metricas", default=",".join(METRICAS_CONTA))

    s = sub.add_parser("metricas-post", help="Métricas de um post.")
    s.add_argument("media_id")
    s.add_argument("--tipo", default="FEED", choices=["FEED", "REELS", "STORY"])

    s = sub.add_parser("relatorio", help="Gera CSV com os posts recentes e suas métricas.")
    s.add_argument("--limite", type=int, default=30)
    s.add_argument("--saida", default="relatorio_instagram.csv")

    s = sub.add_parser("comentarios", help="Lista comentários de um post.")
    s.add_argument("media_id")

    s = sub.add_parser("responder", help="Responde a um comentário.")
    s.add_argument("comentario_id")
    s.add_argument("mensagem")

    s = sub.add_parser("ocultar", help="Oculta um comentário.")
    s.add_argument("comentario_id")
    s.add_argument("--mostrar", action="store_true", help="Desfaz a ocultação.")

    s = sub.add_parser("calendario", help="Publica os itens vencidos do calendário CSV.")
    s.add_argument("arquivo")
    s.add_argument("--executar", action="store_true", help="Publica de verdade (sem isso, só simula).")
    s.add_argument("--ignorar-alertas", action="store_true")

    s = sub.add_parser("modelo-calendario", help="Cria um calendário CSV de exemplo.")
    s.add_argument("arquivo", nargs="?", default="calendario.csv")

    sub.add_parser("renovar-token", help="Renova o token de 60 dias e atualiza o .env.")

    s = sub.add_parser("trocar-token", help="Troca token curto (1 h) por token de 60 dias.")
    s.add_argument("token_curto")
    return p


def _atualizar_env(chave: str, valor: str, caminho: Path = Path(".env")) -> None:
    linhas = caminho.read_text(encoding="utf-8").splitlines() if caminho.exists() else []
    novas, achou = [], False
    for l in linhas:
        if l.split("=", 1)[0].strip() == chave:
            novas.append(f"{chave}={valor}")
            achou = True
        else:
            novas.append(l)
    if not achou:
        novas.append(f"{chave}={valor}")
    caminho.write_text("\n".join(novas) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    carregar_env()
    args = montar_parser().parse_args(argv)
    c = args.comando

    try:
        if c == "verificar-legenda":
            texto = _ler_legenda(args)
            if not texto:
                raise SystemExit("Informe a legenda ou --arquivo-legenda.")
            r = checar_legenda(texto)
            print(r.resumo())
            return 1 if r.bloqueia else 0

        if c == "modelo-calendario":
            print(f"Modelo criado: {calendario.criar_modelo(args.arquivo)}")
            return 0

        if c == "trocar-token":
            segredo = os.environ.get("IG_APP_SECRET")
            if not segredo:
                raise SystemExit("Falta IG_APP_SECRET no .env.")
            r = ClienteInstagram.trocar_token_curto(args.token_curto, segredo)
            _atualizar_env("IG_ACCESS_TOKEN", r["access_token"])
            print(f"Token de longa duração salvo no .env (vale ~{int(r.get('expires_in', 0)) // 86400} dias).")
            return 0

        if c == "calendario" and not args.executar:
            for r in calendario.processar(args.arquivo, None, executar=False,
                                          ignorar_alertas=args.ignorar_alertas):
                print(f"Linha {r.linha} [{r.tipo}] {r.acao.upper()}: {r.detalhe}")
            print("\nSimulação. Para publicar de verdade, repita com --executar.")
            return 0

        cli = _cliente()

        if c == "conta":
            _mostrar(cli.perfil())
        elif c == "limite":
            r = cli.limite_publicacao()
            print(f"Publicações via API nas últimas 24 h: {r['usado']} de {r['total']}.")
        elif c == "publicar-imagem":
            leg = _ler_legenda(args)
            _checar_ou_parar(leg, args.forcar)
            print("Publicado. ID:", cli.publicar_imagem(args.url, leg, alt_text=args.alt))
        elif c == "publicar-reel":
            leg = _ler_legenda(args)
            _checar_ou_parar(leg, args.forcar)
            print("Processando o vídeo na Meta (pode levar alguns minutos)...")
            print("Publicado. ID:", cli.publicar_reel(args.url, leg, capa_url=args.capa,
                                                     compartilhar_no_feed=not args.so_reels))
        elif c == "publicar-story":
            print("Publicado. ID:", cli.publicar_story(args.url))
        elif c == "publicar-carrossel":
            leg = _ler_legenda(args)
            _checar_ou_parar(leg, args.forcar)
            print("Publicado. ID:", cli.publicar_carrossel(args.urls, leg))
        elif c == "posts":
            for p in cli.listar_posts(args.limite):
                leg = (p.get("caption") or "").replace("\n", " ")[:60]
                print(f"{p['timestamp'][:10]}  {p.get('media_product_type', p.get('media_type')):8}  "
                      f"{p.get('like_count', 0):>5} curt.  {p.get('comments_count', 0):>4} coment.  "
                      f"{p['id']}  {leg}")
        elif c == "metricas-conta":
            _mostrar(cli.metricas_conta(args.metricas.split(","), desde=args.desde, ate=args.ate))
        elif c == "metricas-post":
            _mostrar(cli.metricas_post(args.media_id, args.tipo))
        elif c == "relatorio":
            gerar_relatorio(cli, args.limite, args.saida)
            print(f"Relatório salvo em {args.saida}")
        elif c == "comentarios":
            for cm in cli.comentarios(args.media_id):
                oculto = " [oculto]" if cm.get("hidden") else ""
                print(f"{cm['timestamp'][:16]}  @{cm.get('username', '?')}{oculto}: {cm.get('text', '')}  (id {cm['id']})")
        elif c == "responder":
            print("Resposta publicada. ID:", cli.responder_comentario(args.comentario_id, args.mensagem))
        elif c == "ocultar":
            ok = cli.ocultar_comentario(args.comentario_id, ocultar=not args.mostrar)
            print("Feito." if ok else "A Meta não confirmou a alteração.")
        elif c == "calendario":
            for r in calendario.processar(args.arquivo, cli, executar=True,
                                          ignorar_alertas=args.ignorar_alertas):
                print(f"Linha {r.linha} [{r.tipo}] {r.acao.upper()}: {r.detalhe}")
        elif c == "renovar-token":
            r = cli.renovar_token()
            _atualizar_env("IG_ACCESS_TOKEN", r["access_token"])
            print(f"Token renovado e salvo no .env (vale ~{int(r.get('expires_in', 0)) // 86400} dias).")
        return 0
    except ErroInstagram as e:
        print(f"Erro da API do Instagram: {e}", file=sys.stderr)
        return 2


def gerar_relatorio(cli: ClienteInstagram, limite: int, saida: str) -> None:
    colunas = ["data", "tipo", "link", "curtidas", "comentarios", "reach", "views",
               "saved", "shares", "total_interactions", "legenda"]
    with open(saida, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=colunas, delimiter=";")
        w.writeheader()
        for p in cli.listar_posts(limite):
            tipo = p.get("media_product_type") or p.get("media_type") or "FEED"
            linha = {"data": p["timestamp"][:10], "tipo": tipo, "link": p.get("permalink", ""),
                     "curtidas": p.get("like_count", ""), "comentarios": p.get("comments_count", ""),
                     "legenda": (p.get("caption") or "").replace("\n", " ")[:200]}
            if p.get("media_type") != "CAROUSEL_ALBUM":
                try:
                    m = cli.metricas_post(p["id"], "REELS" if tipo == "REELS" else "FEED")
                    linha.update({k: m.get(k, "") for k in ("reach", "views", "saved", "shares",
                                                             "total_interactions")})
                except ErroInstagram:
                    pass
            w.writerow(linha)
