"""Gera o carrossel 'SNCR no balcão' (1080x1350, JPEG) para o Instagram da Organize Farma.

Conteúdo: Cartilha SNCR e receituários controlados para farmácias (Anvisa, set/2026)
e RDC Anvisa 1.000/2025.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

SAIDA = Path(__file__).resolve().parents[2] / "posts" / "2026-11-sncr-balcao"
SAIDA.mkdir(parents=True, exist_ok=True)
TOTAL = 6

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{width:1080px;height:1350px;font-family:'Inter',sans-serif;background:#F6F3EE;color:#16313A;
  position:relative;overflow:hidden}
.topo{position:absolute;top:60px;left:80px;right:80px;display:flex;justify-content:space-between;
  align-items:center;font-size:26px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;color:#0E5C61}
.pill{background:#0E5C61;color:#F6F3EE;border-radius:999px;padding:10px 22px;font-size:24px;letter-spacing:.06em}
.conteudo{position:absolute;top:170px;left:80px;right:80px}
.passo{font-size:34px;font-weight:700;color:#D9603B;letter-spacing:.08em;text-transform:uppercase;margin-bottom:24px}
h1{font-family:'Inter Display','Inter',sans-serif;font-size:88px;line-height:1.04;font-weight:800;letter-spacing:-.02em}
h2{font-family:'Inter Display','Inter',sans-serif;font-size:76px;line-height:1.05;font-weight:800;letter-spacing:-.02em;margin-bottom:40px}
p.lead{font-size:38px;line-height:1.38;color:#2F4A52;margin-top:40px}
ul{list-style:none;margin-top:8px}
li{font-size:39px;line-height:1.32;padding:28px 0 28px 58px;border-top:2px solid #DCD5CA;position:relative}
li:last-child{border-bottom:2px solid #DCD5CA}
li::before{content:'';position:absolute;left:0;top:42px;width:26px;height:26px;border-radius:50%;background:#0E5C61}
li b{color:#0E5C61}
.tabela{margin-top:8px;border-radius:24px;overflow:hidden;border:2px solid #DCD5CA}
.linha{display:flex;font-size:35px;line-height:1.3;background:#fff}
.linha+.linha{border-top:2px solid #DCD5CA}
.linha .s{width:42%;padding:28px 30px;font-weight:800;font-size:31px;letter-spacing:.02em}
.linha .d{width:58%;padding:28px 30px;color:#2F4A52}
.ok{color:#11744A}.parc{color:#B07A12}.usada{color:#5A6B70}.nao{color:#B3372A}
.alerta{margin-top:44px;background:#0E5C61;color:#F6F3EE;border-radius:28px;padding:36px 42px;font-size:37px;line-height:1.35}
.alerta b{color:#FFD9C9}
.rodape{position:absolute;bottom:64px;left:80px;right:80px;display:flex;justify-content:space-between;
  align-items:flex-end;font-size:24px;color:#5A6B70}
.marca{font-weight:800;color:#0E5C61;font-size:28px}
.dots{display:flex;gap:10px}
.dots span{width:14px;height:14px;border-radius:50%;background:#DCD5CA}
.dots span.on{background:#D9603B}
.capa{background:#0E5C61;color:#F6F3EE}
.capa .topo{color:#BFE3DD}.capa .pill{background:#D9603B}
.capa h1{font-size:108px;color:#fff}
.capa p.lead{color:#D6ECE8;font-size:46px}
.capa .rodape{color:#BFE3DD}.capa .marca{color:#fff}
.capa .dots span{background:#2D7C80}.capa .dots span.on{background:#D9603B}
.faixa{position:fixed;left:80px;bottom:190px;font-size:30px;font-weight:700;color:#FFD9C9;letter-spacing:.04em}
.fonte{font-size:28px;color:#5A6B70;margin-top:44px;line-height:1.4}
"""


def dots(n):
    return '<div class="dots">' + "".join(
        f'<span class="{"on" if i == n else ""}"></span>' for i in range(1, TOTAL + 1)) + "</div>"


def pagina(n, corpo, classe=""):
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><style>{CSS}</style></head>
<body class="{classe}">
<div class="topo"><span>Receita eletrônica · SNCR</span><span class="pill">{n}/{TOTAL}</span></div>
<div class="conteudo">{corpo}</div>
<div class="rodape"><div><div class="marca">Organize Farma</div>@betaniaalhan</div>{dots(n)}</div>
</body></html>"""


SLIDES = [
    ("capa", """
<h1>Chegou uma receita eletrônica de controlado no balcão.</h1>
<p class="lead">O que a farmácia precisa conferir <b>antes</b> de dispensar — no novo fluxo do SNCR.</p>
<div class="faixa">Arraste para o lado →</div>"""),
    ("", """
<div class="passo">Passo 1</div>
<h2>Identifique o receituário</h2>
<ul>
<li><b>NR</b> — Notificação de Receita (A, B, B2, retinoides, talidomida)</li>
<li><b>RCE</b> — Receita de Controle Especial</li>
<li><b>RET</b> — Receita sujeita à retenção (antimicrobianos e GLP-1)</li>
</ul>
<div class="alerta">Papel escaneado ou fotografado <b>não é</b> receita eletrônica. Siga as regras do receituário físico.</div>"""),
    ("", """
<div class="passo">Passo 2</div>
<h2>Valide a assinatura eletrônica</h2>
<ul>
<li><b>NR e RCE:</b> assinatura qualificada (certificado ICP-Brasil)</li>
<li><b>RET:</b> assinatura avançada ou qualificada</li>
<li>Use o validador do <b>ITI</b> (Validar) ou o indicado pela plataforma emissora</li>
</ul>
<div class="alerta">A data da assinatura é a <b>data de emissão</b>. É dela que se conta a validade.</div>"""),
    ("", """
<div class="passo">Passo 3</div>
<h2>Consulte o número no SNCR</h2>
<div class="tabela">
<div class="linha"><div class="s ok">AUTORIZADA</div><div class="d">Pode seguir com as demais conferências</div></div>
<div class="linha"><div class="s parc">UTILIZADA PARCIALMENTE</div><div class="d">Só RET, quando o parcelamento é permitido</div></div>
<div class="linha"><div class="s usada">UTILIZADA</div><div class="d">Já dispensada. Não pode ser usada de novo</div></div>
<div class="linha"><div class="s nao">CANCELADA / INVÁLIDA</div><div class="d">Não dispense com essa numeração</div></div>
</div>
<p class="fonte">Confira também: número idêntico, tipo de receituário, meio ELETRÔNICO e prescritor vinculado.</p>"""),
    ("", """
<div class="passo">Passo 4</div>
<h2>Dispense e registre a utilização</h2>
<ul>
<li>Registre o uso <b>no SNCR</b>, logo após a dispensação</li>
<li>Errou? O cancelamento é possível em até <b>30 minutos</b>, pelo mesmo estabelecimento</li>
<li>Guarde o registro em meio eletrônico para a fiscalização</li>
</ul>
<div class="alerta">O SNCR <b>não substitui</b> o SNGPC. A escrituração continua obrigatória.</div>"""),
    ("capa", """
<h1>"Autorizada" no SNCR não encerra a conferência.</h1>
<p class="lead">Validade, campos obrigatórios e requisitos sanitários continuam sendo responsabilidade da farmácia.</p>
<p class="lead"><b>Salve este post</b> e compartilhe com a equipe do balcão.</p>
<p class="fonte" style="color:#BFE3DD">Fontes: RDC Anvisa nº 1.000/2025 e Cartilha "SNCR e receituários controlados" para farmácias (Anvisa, set/2026).</p>"""),
]


def main():
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        pag = nav.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
        for i, (classe, corpo) in enumerate(SLIDES, start=1):
            pag.set_content(pagina(i, corpo, classe), wait_until="networkidle")
            destino = SAIDA / f"sncr-{i:02d}.jpg"
            pag.screenshot(path=str(destino), type="jpeg", quality=92, full_page=False)
            print(destino)
        nav.close()


if __name__ == "__main__":
    main()
