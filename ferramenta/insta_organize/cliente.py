"""Cliente da Instagram API (Instagram Login, graph.instagram.com).

Substitui a antiga biblioteca python-instagram (facebookarchive), que usava
a API Legacy já desligada pela Meta.

Fluxo de publicação da Meta (2 etapas):
  1. POST /{ig-user-id}/media          -> cria um "container" e devolve o id
  2. GET  /{container-id}?fields=status_code  até FINISHED
  3. POST /{ig-user-id}/media_publish  com creation_id=<container>

Requisitos da Meta (conferir sempre a documentação oficial):
  - conta profissional (Empresa ou Criador de conteúdo);
  - mídia em URL pública (imagem só JPEG);
  - limite de publicações via API por 24 h (consultar com publishing_limit()).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Iterable

import requests

VERSAO_PADRAO = "v26.0"
HOST_PADRAO = "https://graph.instagram.com"

# Métricas aceitas pela Meta em 2026. "impressions", "plays" e "video_views"
# foram descontinuadas em 2025 e não devem ser usadas.
METRICAS_CONTA = ("reach", "views", "accounts_engaged", "total_interactions",
                  "likes", "comments", "shares", "saves", "replies",
                  "profile_links_taps", "follows_and_unfollows")
METRICAS_POST = ("reach", "views", "likes", "comments", "shares", "saved",
                 "total_interactions", "profile_visits", "follows")
METRICAS_REEL = ("reach", "views", "likes", "comments", "shares", "saved",
                 "total_interactions", "ig_reels_avg_watch_time",
                 "ig_reels_video_view_total_time")
METRICAS_STORY = ("reach", "views", "replies", "shares", "total_interactions",
                  "navigation")


class ErroInstagram(Exception):
    """Erro devolvido pela API, com a mensagem original da Meta."""

    def __init__(self, mensagem: str, codigo: int | None = None,
                 subcodigo: int | None = None, status_http: int | None = None):
        super().__init__(mensagem)
        self.codigo = codigo
        self.subcodigo = subcodigo
        self.status_http = status_http

    @property
    def dica(self) -> str:
        if self.codigo == 190:
            return "Token inválido ou vencido. Gere um novo ou rode 'renovar-token'."
        if self.codigo in (4, 17, 32, 613) or self.subcodigo == 2207042:
            return "Limite de chamadas ou de publicações atingido. Aguarde e tente mais tarde."
        if self.codigo == 10 or self.codigo == 200:
            return "Permissão faltando no app. Confira os escopos instagram_business_*."
        if self.codigo == 9004 or self.subcodigo == 2207052:
            return "A Meta não conseguiu baixar a mídia. A URL precisa ser pública e a imagem, JPEG."
        return ""

    def __str__(self) -> str:
        base = super().__str__()
        extra = f" (código {self.codigo})" if self.codigo is not None else ""
        return base + extra + (f" — {self.dica}" if self.dica else "")


@dataclass
class Configuracao:
    token: str
    ig_user_id: str = "me"
    versao: str = VERSAO_PADRAO
    host: str = HOST_PADRAO
    timeout: int = 60


class ClienteInstagram:
    def __init__(self, config: Configuracao, sessao: requests.Session | None = None,
                 dormir: Callable[[float], None] = time.sleep):
        if not config.token:
            raise ValueError("Token de acesso não informado (IG_ACCESS_TOKEN).")
        self.config = config
        self.sessao = sessao or requests.Session()
        self._dormir = dormir

    # ------------------------------------------------------------------ base
    def _url(self, caminho: str) -> str:
        return f"{self.config.host}/{self.config.versao}/{caminho.lstrip('/')}"

    def _requisicao(self, metodo: str, caminho: str, *, params: dict | None = None,
                    data: dict | None = None, url_completa: str | None = None) -> dict:
        params = dict(params or {})
        params.setdefault("access_token", self.config.token)
        url = url_completa or self._url(caminho)
        resp = self.sessao.request(metodo, url, params=params, data=data,
                                   timeout=self.config.timeout)
        try:
            corpo = resp.json()
        except ValueError:
            corpo = {}
        if resp.status_code >= 400 or "error" in corpo:
            erro = corpo.get("error", {}) if isinstance(corpo, dict) else {}
            raise ErroInstagram(
                erro.get("error_user_msg") or erro.get("message") or f"HTTP {resp.status_code}",
                codigo=erro.get("code"),
                subcodigo=erro.get("error_subcode"),
                status_http=resp.status_code,
            )
        return corpo

    def _get(self, caminho: str, **params: Any) -> dict:
        return self._requisicao("GET", caminho, params=params)

    def _post(self, caminho: str, **dados: Any) -> dict:
        dados = {k: v for k, v in dados.items() if v is not None}
        return self._requisicao("POST", caminho, data=dados)

    def _paginar(self, caminho: str, limite: int | None = None, **params: Any) -> list[dict]:
        itens: list[dict] = []
        corpo = self._get(caminho, **params)
        while True:
            itens.extend(corpo.get("data", []))
            if limite and len(itens) >= limite:
                return itens[:limite]
            proxima = corpo.get("paging", {}).get("next")
            if not proxima:
                return itens
            corpo = self._requisicao("GET", "", url_completa=proxima, params={})

    @property
    def _uid(self) -> str:
        return self.config.ig_user_id

    # ----------------------------------------------------------------- conta
    def perfil(self) -> dict:
        return self._get(self._uid, fields="id,username,name,"
                                           "followers_count,follows_count,media_count")

    def limite_publicacao(self) -> dict:
        """Uso da cota de publicações via API nas últimas 24 h."""
        corpo = self._get(f"{self._uid}/content_publishing_limit",
                          fields="config,quota_usage")
        dados = (corpo.get("data") or [{}])[0]
        return {
            "usado": dados.get("quota_usage"),
            "total": (dados.get("config") or {}).get("quota_total"),
            "janela_segundos": (dados.get("config") or {}).get("quota_duration"),
        }

    # ------------------------------------------------------------- publicação
    def criar_container_imagem(self, image_url: str, legenda: str | None = None, *,
                               carrossel: bool = False, alt_text: str | None = None) -> str:
        corpo = self._post(f"{self._uid}/media", image_url=image_url,
                           caption=None if carrossel else legenda,
                           is_carousel_item="true" if carrossel else None,
                           alt_text=alt_text)
        return corpo["id"]

    def criar_container_video(self, video_url: str, legenda: str | None = None, *,
                              carrossel: bool = False, capa_url: str | None = None,
                              compartilhar_no_feed: bool = True) -> str:
        if carrossel:
            corpo = self._post(f"{self._uid}/media", video_url=video_url,
                               media_type="VIDEO", is_carousel_item="true")
        else:
            corpo = self._post(f"{self._uid}/media", video_url=video_url,
                               media_type="REELS", caption=legenda, cover_url=capa_url,
                               share_to_feed="true" if compartilhar_no_feed else "false")
        return corpo["id"]

    def criar_container_story(self, url: str, video: bool = False) -> str:
        chave = "video_url" if video else "image_url"
        corpo = self._post(f"{self._uid}/media", media_type="STORIES", **{chave: url})
        return corpo["id"]

    def criar_container_carrossel(self, filhos: Iterable[str], legenda: str | None = None) -> str:
        filhos = list(filhos)
        if not 2 <= len(filhos) <= 20:
            raise ValueError("Carrossel precisa de 2 a 20 itens.")
        corpo = self._post(f"{self._uid}/media", media_type="CAROUSEL",
                           children=",".join(filhos), caption=legenda)
        return corpo["id"]

    def status_container(self, container_id: str) -> str:
        return self._get(container_id, fields="status_code").get("status_code", "")

    def aguardar_container(self, container_id: str, intervalo: float = 10,
                           tentativas: int = 30) -> None:
        """Espera o container ficar FINISHED (vídeos podem levar alguns minutos)."""
        for _ in range(tentativas):
            status = self.status_container(container_id)
            if status in ("FINISHED", "PUBLISHED"):
                return
            if status in ("ERROR", "EXPIRED"):
                raise ErroInstagram(f"Container {container_id} com status {status}. "
                                    "Confira formato, tamanho e URL pública da mídia.")
            self._dormir(intervalo)
        raise ErroInstagram(f"Container {container_id} não ficou pronto a tempo.")

    def publicar_container(self, container_id: str) -> str:
        corpo = self._post(f"{self._uid}/media_publish", creation_id=container_id)
        return corpo["id"]

    def publicar_imagem(self, image_url: str, legenda: str, alt_text: str | None = None) -> str:
        cid = self.criar_container_imagem(image_url, legenda, alt_text=alt_text)
        self.aguardar_container(cid, intervalo=3)
        return self.publicar_container(cid)

    def publicar_carrossel(self, urls: Iterable[str], legenda: str) -> str:
        filhos = []
        for url in urls:
            if _e_video(url):
                filhos.append(self.criar_container_video(url, carrossel=True))
            else:
                filhos.append(self.criar_container_imagem(url, carrossel=True))
        for f in filhos:
            self.aguardar_container(f, intervalo=5)
        cid = self.criar_container_carrossel(filhos, legenda)
        self.aguardar_container(cid, intervalo=3)
        return self.publicar_container(cid)

    def publicar_reel(self, video_url: str, legenda: str, capa_url: str | None = None,
                      compartilhar_no_feed: bool = True) -> str:
        cid = self.criar_container_video(video_url, legenda, capa_url=capa_url,
                                         compartilhar_no_feed=compartilhar_no_feed)
        self.aguardar_container(cid)
        return self.publicar_container(cid)

    def publicar_story(self, url: str) -> str:
        cid = self.criar_container_story(url, video=_e_video(url))
        self.aguardar_container(cid, intervalo=5)
        return self.publicar_container(cid)

    # --------------------------------------------------------------- leitura
    def listar_posts(self, limite: int = 25) -> list[dict]:
        campos = ("id,caption,media_type,media_product_type,permalink,timestamp,"
                  "like_count,comments_count")
        return self._paginar(f"{self._uid}/media", limite=limite, fields=campos, limit=min(limite, 50))

    def metricas_conta(self, metricas: Iterable[str] = METRICAS_CONTA, periodo: str = "day",
                       desde: str | None = None, ate: str | None = None) -> dict[str, Any]:
        """Métricas totais da conta no período (datas AAAA-MM-DD)."""
        params: dict[str, Any] = {"metric": ",".join(metricas), "period": periodo,
                                  "metric_type": "total_value"}
        if desde:
            params["since"] = desde
        if ate:
            params["until"] = ate
        corpo = self._get(f"{self._uid}/insights", **params)
        return {m["name"]: (m.get("total_value") or {}).get("value",
                            (m.get("values") or [{}])[-1].get("value"))
                for m in corpo.get("data", [])}

    def metricas_post(self, media_id: str, tipo: str = "FEED") -> dict[str, Any]:
        tipo = tipo.upper()
        if tipo in ("CAROUSEL_ALBUM", "CAROUSEL"):
            raise ErroInstagram("A Meta não fornece métricas de carrossel pela API.")
        metricas = {"REELS": METRICAS_REEL, "STORY": METRICAS_STORY}.get(tipo, METRICAS_POST)
        corpo = self._get(f"{media_id}/insights", metric=",".join(metricas))
        return {m["name"]: (m.get("values") or [{}])[0].get("value",
                            (m.get("total_value") or {}).get("value"))
                for m in corpo.get("data", [])}

    def comentarios(self, media_id: str, limite: int = 50) -> list[dict]:
        return self._paginar(f"{media_id}/comments", limite=limite,
                             fields="id,text,username,timestamp,like_count,hidden")

    def responder_comentario(self, comentario_id: str, mensagem: str) -> str:
        return self._post(f"{comentario_id}/replies", message=mensagem)["id"]

    def ocultar_comentario(self, comentario_id: str, ocultar: bool = True) -> bool:
        return bool(self._post(comentario_id, hide="true" if ocultar else "false").get("success"))

    # ----------------------------------------------------------------- token
    def renovar_token(self) -> dict:
        """Renova o token de longa duração (precisa ter mais de 24 h e não estar vencido)."""
        url = f"{self.config.host}/refresh_access_token"
        return self._requisicao("GET", "", url_completa=url,
                                params={"grant_type": "ig_refresh_token",
                                        "access_token": self.config.token})

    @staticmethod
    def trocar_token_curto(token_curto: str, app_secret: str,
                           host: str = HOST_PADRAO,
                           sessao: requests.Session | None = None) -> dict:
        """Troca o token de 1 hora por um de 60 dias."""
        s = sessao or requests.Session()
        resp = s.get(f"{host}/access_token", params={
            "grant_type": "ig_exchange_token",
            "client_secret": app_secret,
            "access_token": token_curto,
        }, timeout=60)
        corpo = resp.json()
        if resp.status_code >= 400 or "error" in corpo:
            erro = corpo.get("error", {})
            raise ErroInstagram(erro.get("message", f"HTTP {resp.status_code}"),
                                codigo=erro.get("code"))
        return corpo


def _e_video(url: str) -> bool:
    return url.lower().split("?")[0].endswith((".mp4", ".mov"))
