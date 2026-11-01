from datetime import datetime
from pathlib import Path

import pytest

from insta_organize import calendario
from insta_organize.cli import main
from insta_organize.cliente import ClienteInstagram, Configuracao, ErroInstagram
from insta_organize.legenda import ALTO, checar_legenda


# --------------------------------------------------------------- simulador
class Resp:
    def __init__(self, corpo, status=200):
        self._corpo, self.status_code = corpo, status

    def json(self):
        return self._corpo


class SessaoFalsa:
    """Responde conforme regras (método, trecho da URL) -> lista de respostas."""

    def __init__(self, regras):
        self.regras = {k: list(v) for k, v in regras.items()}
        self.chamadas = []

    def request(self, metodo, url, params=None, data=None, timeout=None):
        self.chamadas.append((metodo, url, dict(params or {}), dict(data or {})))
        for (m, trecho), respostas in self.regras.items():
            if m == metodo and trecho in url:
                return respostas.pop(0) if len(respostas) > 1 else respostas[0]
        raise AssertionError(f"Chamada inesperada: {metodo} {url}")

    def get(self, url, params=None, timeout=None):
        return self.request("GET", url, params=params)


def cliente(regras):
    s = SessaoFalsa(regras)
    return ClienteInstagram(Configuracao(token="T", ig_user_id="123"), sessao=s,
                            dormir=lambda _: None), s


# --------------------------------------------------------------- publicação
def test_publicar_imagem_fluxo_completo():
    c, s = cliente({
        ("POST", "/123/media_publish"): [Resp({"id": "POST1"})],
        ("POST", "/123/media"): [Resp({"id": "C1"})],
        ("GET", "/C1"): [Resp({"status_code": "IN_PROGRESS"}), Resp({"status_code": "FINISHED"})],
    })
    assert c.publicar_imagem("https://x/a.jpg", "Olá", alt_text="alt") == "POST1"
    metodo, url, params, dados = s.chamadas[0]
    assert url == "https://graph.instagram.com/v26.0/123/media"
    assert dados == {"image_url": "https://x/a.jpg", "caption": "Olá", "alt_text": "alt"}
    assert params["access_token"] == "T"
    assert s.chamadas[-1][3] == {"creation_id": "C1"}


def test_carrossel_cria_filhos_e_pai():
    c, s = cliente({
        ("POST", "/123/media_publish"): [Resp({"id": "P"})],
        ("POST", "/123/media"): [Resp({"id": "F1"}), Resp({"id": "F2"}), Resp({"id": "PAI"})],
        ("GET", "/F1"): [Resp({"status_code": "FINISHED"})],
        ("GET", "/F2"): [Resp({"status_code": "FINISHED"})],
        ("GET", "/PAI"): [Resp({"status_code": "FINISHED"})],
    })
    assert c.publicar_carrossel(["https://x/1.jpg", "https://x/2.mp4"], "Leg") == "P"
    posts = [ch[3] for ch in s.chamadas if ch[0] == "POST" and ch[1].endswith("/media")]
    assert posts[0] == {"image_url": "https://x/1.jpg", "is_carousel_item": "true"}
    assert posts[1] == {"video_url": "https://x/2.mp4", "media_type": "VIDEO", "is_carousel_item": "true"}
    assert posts[2] == {"media_type": "CAROUSEL", "children": "F1,F2", "caption": "Leg"}


def test_carrossel_exige_2_a_20():
    c, _ = cliente({})
    with pytest.raises(ValueError):
        c.criar_container_carrossel(["so1"])


def test_reel_parametros():
    c, s = cliente({
        ("POST", "/123/media_publish"): [Resp({"id": "R"})],
        ("POST", "/123/media"): [Resp({"id": "C"})],
        ("GET", "/C"): [Resp({"status_code": "FINISHED"})],
    })
    c.publicar_reel("https://x/v.mp4", "L", capa_url="https://x/c.jpg", compartilhar_no_feed=False)
    assert s.chamadas[0][3] == {"video_url": "https://x/v.mp4", "media_type": "REELS", "caption": "L",
                                "cover_url": "https://x/c.jpg", "share_to_feed": "false"}


def test_container_com_erro_para():
    c, _ = cliente({("POST", "/123/media"): [Resp({"id": "C"})],
                    ("GET", "/C"): [Resp({"status_code": "ERROR"})]})
    with pytest.raises(ErroInstagram):
        c.publicar_imagem("https://x/a.jpg", "x")


def test_erro_da_api_traz_dica():
    c, _ = cliente({("GET", "/123"): [Resp({"error": {"message": "Invalid OAuth", "code": 190}}, 400)]})
    with pytest.raises(ErroInstagram) as e:
        c.perfil()
    assert "renovar-token" in str(e.value)


# --------------------------------------------------------------- leitura
def test_limite_publicacao():
    c, _ = cliente({("GET", "content_publishing_limit"): [Resp(
        {"data": [{"quota_usage": 3, "config": {"quota_total": 100, "quota_duration": 86400}}]})]})
    assert c.limite_publicacao() == {"usado": 3, "total": 100, "janela_segundos": 86400}


def test_metricas_conta_total_value():
    c, s = cliente({("GET", "/123/insights"): [Resp({"data": [
        {"name": "reach", "total_value": {"value": 1500}},
        {"name": "views", "total_value": {"value": 4200}}]})]})
    assert c.metricas_conta(["reach", "views"], desde="2026-10-01") == {"reach": 1500, "views": 4200}
    assert s.chamadas[0][2]["metric_type"] == "total_value"
    assert s.chamadas[0][2]["since"] == "2026-10-01"


def test_metricas_nao_usa_descontinuadas():
    c, s = cliente({("GET", "/M/insights"): [Resp({"data": [{"name": "reach", "values": [{"value": 9}]}]})]})
    assert c.metricas_post("M", "REELS") == {"reach": 9}
    pedidas = s.chamadas[0][2]["metric"].split(",")
    assert not {"impressions", "plays", "video_views"} & set(pedidas)


def test_metricas_carrossel_indisponivel():
    c, _ = cliente({})
    with pytest.raises(ErroInstagram):
        c.metricas_post("M", "CAROUSEL_ALBUM")


def test_paginacao_comentarios():
    c, _ = cliente({
        ("GET", "/M/comments"): [Resp({"data": [{"id": "1"}], "paging": {"next": "https://graph.instagram.com/next"}})],
        ("GET", "/next"): [Resp({"data": [{"id": "2"}]})],
    })
    assert [x["id"] for x in c.comentarios("M")] == ["1", "2"]


def test_renovar_token_usa_endpoint_certo():
    c, s = cliente({("GET", "refresh_access_token"): [Resp({"access_token": "NOVO", "expires_in": 5184000})]})
    assert c.renovar_token()["access_token"] == "NOVO"
    assert s.chamadas[0][1] == "https://graph.instagram.com/refresh_access_token"
    assert s.chamadas[0][2]["grant_type"] == "ig_refresh_token"


# --------------------------------------------------------------- legenda
@pytest.mark.parametrize("texto", [
    "Ozempic com desconto aqui!",
    "Comprovado cientificamente, alivia em minutos.",
    "Exagerou na bebida? Resolva a ressaca rapidinho.",
    "100% seguro e sem efeitos colaterais.",
])
def test_legenda_alertas_altos(texto):
    assert checar_legenda(texto).bloqueia


def test_legenda_educativa_passa():
    texto = ("SNCR: o que a farmácia precisa conferir antes de dispensar uma receita eletrônica. "
             "Salve este post e compartilhe com a equipe.")
    r = checar_legenda(texto)
    assert not r.bloqueia


def test_legenda_imperativo_e_advertencia():
    r = checar_legenda("Tome este medicamento para dor de cabeça.")
    motivos = " ".join(a.base for a in r.alertas)
    assert "art. 8º, VII" in motivos
    assert "arts. 22 a 24" in motivos
    assert not r.bloqueia


def test_medicamento_para_criancas_vira_alto():
    assert checar_legenda("Xarope novo para crianças!").bloqueia
    assert not checar_legenda("Dia das crianças: horário especial da loja").bloqueia


def test_cli_simula_calendario_sem_token(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("IG_ACCESS_TOKEN", raising=False)
    p = _csv(tmp_path, "2020-01-01 09:00;imagem;https://x/a.jpg;Dica;;;;\n")
    assert main(["calendario", str(p)]) == 0
    assert "SIMULADO" in capsys.readouterr().out


def test_legenda_sem_acento_tambem_detecta():
    assert checar_legenda("comprovado CIENTIFICAMENTE").bloqueia


# --------------------------------------------------------------- calendário
def _csv(tmp_path: Path, linhas: str) -> Path:
    p = tmp_path / "cal.csv"
    p.write_text("data_hora;tipo;midias;legenda;capa;status;media_id;observacao\n" + linhas, encoding="utf-8")
    return p


AGORA = datetime(2026, 11, 10, 12, 0, tzinfo=calendario.BRASILIA)


def test_calendario_simula_sem_publicar(tmp_path):
    p = _csv(tmp_path, "2026-11-10 09:00;imagem;https://x/a.jpg;Dica de hoje;;;;\n"
                       "2026-11-20 09:00;imagem;https://x/b.jpg;Depois;;;;\n")
    r = calendario.processar(p, None, executar=False, agora=AGORA)
    assert [x.acao for x in r] == ["simulado", "aguardando"]


def test_calendario_bloqueia_alerta_alto(tmp_path):
    p = _csv(tmp_path, "2026-11-10 09:00;imagem;https://x/a.jpg;Mounjaro em promoção;;;;\n")
    r = calendario.processar(p, None, executar=True, agora=AGORA)
    assert r[0].acao == "bloqueado"
    assert "bloqueado" in p.read_text(encoding="utf-8-sig")


def test_calendario_publica_e_grava(tmp_path):
    p = _csv(tmp_path, "10/11/2026 09:00;imagem;https://x/a.jpg;Dica de hoje;;;;\n")
    c, _ = cliente({
        ("POST", "/123/media_publish"): [Resp({"id": "PUB9"})],
        ("POST", "/123/media"): [Resp({"id": "C"})],
        ("GET", "/C"): [Resp({"status_code": "FINISHED"})],
    })
    r = calendario.processar(p, c, executar=True, agora=AGORA)
    assert r[0].acao == "publicado"
    conteudo = p.read_text(encoding="utf-8-sig")
    assert "publicado" in conteudo and "PUB9" in conteudo
    # Rodar de novo não republica
    assert calendario.processar(p, c, executar=True, agora=AGORA) == []


# --------------------------------------------------------------- CLI
def test_cli_verificar_legenda(capsys):
    assert main(["verificar-legenda", "Comprovado cientificamente!"]) == 1
    assert "REVISAR" in capsys.readouterr().out


def test_cli_modelo_calendario(tmp_path):
    destino = tmp_path / "modelo.csv"
    assert main(["modelo-calendario", str(destino)]) == 0
    assert "data_hora" in destino.read_text(encoding="utf-8-sig")
