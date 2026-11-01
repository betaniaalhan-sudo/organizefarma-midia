"""Carrossel 'Receita eletrônica no balcão (SNCR)' — Organize Farma.

Identidade: azul-marinho #0F1C52, verde-limão #BDE513, branco; logo oficial.
Conteúdo: RDC Anvisa 1.000/2025; Cartilha "SNCR e receituários controlados" para
farmácias (Anvisa, set/2026); prorrogação da transição de RCE/RET até 03/03/2027
(20ª ROP da Anvisa, 29/10/2026).
"""
import base64
from pathlib import Path
from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parents[2]
SAIDA = RAIZ / "posts" / "2026-11-sncr-balcao"
SAIDA.mkdir(parents=True, exist_ok=True)


def img64(nome):
    return "data:image/png;base64," + base64.b64encode((RAIZ / "marca" / nome).read_bytes()).decode()


SIMBOLO = img64("simbolo.png")
LOGO = img64("logo-completa.png")
NOME = img64("logo-nome.png")

NAVY, LIME, BRANCO = "#0F1C52", "#BDE513", "#FFFFFF"

CSS = f"""
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:1080px;height:1350px;font-family:'Inter',sans-serif;background:{NAVY};color:{BRANCO};position:relative;overflow:hidden}}
.topo{{position:absolute;top:60px;left:80px;right:80px;display:flex;justify-content:space-between;align-items:center}}
.topo .tag{{font-size:25px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:{LIME}}}
.pill{{border:2px solid {LIME};color:{LIME};border-radius:999px;padding:8px 22px;font-size:24px;font-weight:700}}
.conteudo{{position:absolute;top:170px;left:80px;right:80px}}
.passo{{display:inline-block;background:{LIME};color:{NAVY};font-size:28px;font-weight:800;letter-spacing:.06em;
  text-transform:uppercase;border-radius:12px;padding:10px 20px;margin-bottom:30px}}
h1{{font-family:'Inter Display','Inter',sans-serif;font-size:100px;line-height:1.03;font-weight:800;letter-spacing:-.025em}}
h2{{font-family:'Inter Display','Inter',sans-serif;font-size:74px;line-height:1.06;font-weight:800;letter-spacing:-.02em;margin-bottom:40px}}
h1 em,h2 em{{font-style:normal;color:{LIME}}}
p.lead{{font-size:44px;line-height:1.36;color:#D7DCF0;margin-top:40px}}
p.lead b{{color:{LIME}}}
ul{{list-style:none}}
li{{font-size:39px;line-height:1.32;padding:28px 0 28px 58px;border-top:2px solid rgba(255,255,255,.16);position:relative;color:#E9ECF7}}
li:last-child{{border-bottom:2px solid rgba(255,255,255,.16)}}
li::before{{content:'';position:absolute;left:0;top:42px;width:26px;height:26px;border-radius:7px;background:{LIME}}}
li b{{color:{LIME}}}
.tabela{{border-radius:24px;overflow:hidden;background:{BRANCO}}}
.linha{{display:flex;font-size:34px;line-height:1.3;color:{NAVY}}}
.linha+.linha{{border-top:2px solid #E3E6F0}}
.linha .s{{width:42%;padding:28px 30px;font-weight:800;font-size:30px;letter-spacing:.02em}}
.linha .d{{width:58%;padding:28px 30px}}
.ok{{color:#1E7A35}}.parc{{color:#9A6A00}}.usada{{color:#4B5578}}.nao{{color:#B3261E}}
.alerta{{margin-top:44px;background:{LIME};color:{NAVY};border-radius:24px;padding:36px 42px;font-size:37px;line-height:1.34;font-weight:500}}
.alerta b{{font-weight:800}}
.nota{{font-size:29px;line-height:1.4;color:#B9C0DE;margin-top:36px}}
.rodape{{position:absolute;bottom:56px;left:80px;right:80px;display:flex;justify-content:space-between;align-items:center}}
.marca{{display:flex;align-items:center;gap:18px}}
.marca img.s{{width:54px;height:54px}}
.marca img.n{{height:62px}}
.arroba{{font-size:26px;color:#B9C0DE;font-weight:600}}
.dots{{display:flex;gap:10px}}
.dots span{{width:14px;height:14px;border-radius:4px;background:rgba(255,255,255,.25)}}
.dots span.on{{background:{LIME}}}
.simbolo-grande{{position:fixed;right:-120px;bottom:-120px;width:620px;opacity:.10}}
.dica{{position:fixed;left:80px;bottom:170px;font-size:32px;font-weight:700;color:{LIME}}}
.logo-final{{width:560px;display:block;margin:0 auto 40px}}
.centro{{text-align:center}}
.fonte{{font-size:25px;line-height:1.45;color:#9AA3C9;margin-top:40px}}
"""

SLIDES = [
    ("capa", """
<img class="simbolo-grande" src="{SIMBOLO}">
<h1>Chegou uma <em>receita eletrônica</em> de controlado no balcão.</h1>
<p class="lead">O que a farmácia precisa conferir <b>antes</b> de dispensar, no novo fluxo do SNCR.</p>
<div class="dica">Arraste para o lado →</div>"""),
    ("", """
<div class="passo">Passo 1</div>
<h2>Identifique o <em>receituário</em></h2>
<ul>
<li><b>NR</b> · Notificação de Receita (A, B, B2, retinoides, talidomida)</li>
<li><b>RCE</b> · Receita de Controle Especial</li>
<li><b>RET</b> · Receita sujeita à retenção (antimicrobianos e GLP-1)</li>
</ul>
<div class="alerta">Papel escaneado ou fotografado <b>não é</b> receita eletrônica. Siga as regras do receituário físico.</div>"""),
    ("", """
<div class="passo">Passo 2</div>
<h2>Valide a <em>assinatura</em> eletrônica</h2>
<ul>
<li><b>NR e RCE:</b> assinatura qualificada (certificado ICP-Brasil)</li>
<li><b>RET:</b> assinatura avançada ou qualificada</li>
<li>Use o validador do <b>ITI</b> ou o indicado pela plataforma emissora</li>
</ul>
<div class="alerta">A data da assinatura é a <b>data de emissão</b>. É dela que se conta a validade.</div>"""),
    ("", """
<div class="passo">Passo 3</div>
<h2>Consulte o número no <em>SNCR</em></h2>
<div class="tabela">
<div class="linha"><div class="s ok">AUTORIZADA</div><div class="d">Pode seguir com as demais conferências</div></div>
<div class="linha"><div class="s parc">UTILIZADA PARCIALMENTE</div><div class="d">Só RET, quando o parcelamento é permitido</div></div>
<div class="linha"><div class="s usada">UTILIZADA</div><div class="d">Já dispensada. Não pode ser usada de novo</div></div>
<div class="linha"><div class="s nao">CANCELADA / INVÁLIDA</div><div class="d">Não dispense com essa numeração</div></div>
</div>
<p class="nota">Confira também: número idêntico, tipo de receituário, meio ELETRÔNICO e prescritor vinculado.</p>"""),
    ("", """
<div class="passo">Passo 4</div>
<h2>Dispense e <em>registre</em> a utilização</h2>
<ul>
<li>Registre o uso <b>no SNCR</b>, logo após a dispensação</li>
<li>Errou? Cancelamento em até <b>30 minutos</b>, pelo mesmo estabelecimento</li>
<li>Guarde o registro em meio eletrônico para a fiscalização</li>
</ul>
<div class="alerta">O SNCR <b>não substitui</b> o SNGPC. A escrituração continua obrigatória.</div>"""),
    ("", """
<div class="passo">Atenção ao prazo</div>
<h2>Transição de RCE e RET prorrogada até <em>03/03/2027</em></h2>
<ul>
<li>Até lá, ainda podem chegar <b>RCE e RET eletrônicas sem número do SNCR</b>, emitidas pelo fluxo anterior</li>
<li>Nesse caso, <b>não há</b> consulta nem registro de utilização no SNCR</li>
<li>Guarde a receita e registre a dispensação no próprio documento</li>
</ul>
<p class="nota">Decisão da Diretoria Colegiada da Anvisa em 29/10/2026 (alteração da RDC 1.000/2025).</p>"""),
    ("final", """
<img class="logo-final" src="{LOGO}">
<h2 class="centro">"Autorizada" no SNCR <em>não encerra</em> a conferência.</h2>
<p class="lead centro">Salve este post e compartilhe com a equipe do balcão.</p>
<p class="fonte centro">Fontes: RDC Anvisa nº 1.000/2025 · Cartilha "SNCR e receituários controlados" para farmácias (Anvisa, set/2026) · Anvisa, 20ª ROP de 29/10/2026.</p>"""),
]
TOTAL = len(SLIDES)


def pagina(n, corpo, tipo):
    dots = "".join(f'<span class="{"on" if i == n else ""}"></span>' for i in range(1, TOTAL + 1))
    corpo = corpo.replace("{SIMBOLO}", SIMBOLO).replace("{LOGO}", LOGO)
    marca = ('<div class="marca"><span class="arroba">@betaniaalhan</span></div>' if tipo == "final"
             else f'<div class="marca"><img class="s" src="{SIMBOLO}"><img class="n" src="{NOME}"></div>')
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="topo"><span class="tag">Receita eletrônica · SNCR</span><span class="pill">{n}/{TOTAL}</span></div>
<div class="conteudo">{corpo}</div>
<div class="rodape">{marca}<div class="dots">{dots}</div></div>
</body></html>"""


def main():
    for antigo in SAIDA.glob("sncr-*.jpg"):
        antigo.unlink()
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        pag = nav.new_page(viewport={"width": 1080, "height": 1350})
        for i, (tipo, corpo) in enumerate(SLIDES, start=1):
            pag.set_content(pagina(i, corpo, tipo), wait_until="load")
            c, f = pag.evaluate("()=>[document.querySelector('.conteudo').getBoundingClientRect().bottom,"
                                "document.querySelector('.rodape').getBoundingClientRect().top]")
            aviso = "" if c < f - 30 else "  <-- SOBREPÕE O RODAPÉ"
            destino = SAIDA / f"sncr-{i:02d}.jpg"
            pag.screenshot(path=str(destino), type="jpeg", quality=92)
            print(destino.name, int(c), int(f), aviso)
        nav.close()


if __name__ == "__main__":
    main()
