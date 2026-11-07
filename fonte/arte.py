"""Gerador de artes da Organize Farma em vários formatos, sempre com a marca.

Uso:  python3 fonte/arte.py posts/AAAA-MM-DD-assunto/post.json

Toda tela sai com a logo oficial (símbolo + nome "Organize farma"), as cores da
marca (azul-marinho #0F1C52, verde-limão #BDE513, branco) e o @betaniaalhan.
O script confere que a logo foi desenhada em cada tela e que o texto não invade
o rodapé (reduz a fonte automaticamente se precisar). Se a marca faltar, falha.

Formatos (campo "formato" do post.json):
  carrossel  1080x1350, 2 a 10 telas            -> NN.jpg
  card       1080x1350, 1 tela (post único)     -> 01.jpg
  stories    1080x1920, 1 a 5 telas             -> story-NN.jpg
  reel       1080x1920, 3 a 6 telas animadas    -> reel.mp4 + capa.jpg (+ quadros)

Tipos de tela (campo "tipo" de cada item de "telas"):
  capa    titulo, lead, [dica]
  lista   [selo], titulo, itens[], [alerta], [nota]
  tabela  [selo], titulo, linhas[[rotulo, texto, cor]], [nota]   cor: ok|parc|usada|nao
  texto   [selo], titulo, paragrafos[], [alerta]
  numero  [selo], numero, titulo, [lead]                          (dado em destaque)
  mito    [selo], mito, verdade, [nota]                           (mito x verdade)
  frase   frase, [assinatura]                                     (opinião / citação)
  enquete pergunta, opcoes[], [lead]                               (stories: enquete/caixa)
  final   titulo, [cta], [fontes]                                 (logo grande)
Nos textos, <em>…</em> pinta de verde-limão e <b>…</b> destaca.

Chamada para ação (obrigatória): a ÚLTIMA tela de todo post precisa de CTA.
  - tela "final": campo "cta";
  - qualquer outro tipo (ex.: card único): campo "cta", que vira uma faixa
    verde-limão no fim da tela.
  Sem CTA na última tela, o gerador falha. Modelo de CTA: ver ROTINA.md, seção 3.
"""
import base64
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parents[1]
NAVY, LIME, BRANCO = "#0F1C52", "#BDE513", "#FFFFFF"
ARROBA = "@betaniaalhan"
TAMANHOS = {"carrossel": (1080, 1350), "card": (1080, 1350), "stories": (1080, 1920), "reel": (1080, 1920)}
LIMITES = {"carrossel": (2, 10), "card": (1, 1), "stories": (1, 5), "reel": (3, 6)}


def img64(nome):
    return "data:image/png;base64," + base64.b64encode((RAIZ / "marca" / nome).read_bytes()).decode()


SIMBOLO, LOGO, NOME = img64("simbolo.png"), img64("logo-completa.png"), img64("logo-nome.png")


def css(w, h, vertical):
    topo = 250 if vertical else 60          # stories/reels: fora da barra do perfil
    base = 330 if vertical else 56          # stories/reels: acima da barra de resposta
    conteudo = 360 if vertical else 170
    return f"""
*{{box-sizing:border-box;margin:0;padding:0}}
:root{{--k:1}}
body{{width:{w}px;height:{h}px;font-family:'Inter',sans-serif;background:{NAVY};color:{BRANCO};position:relative;overflow:hidden}}
.topo{{position:absolute;top:{topo}px;left:80px;right:80px;display:flex;justify-content:space-between;align-items:center}}
.tag{{font-size:25px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:{LIME}}}
.pill{{border:2px solid {LIME};color:{LIME};border-radius:999px;padding:8px 22px;font-size:24px;font-weight:700}}
.conteudo{{position:absolute;left:80px;right:80px;{'top:47%;transform:translateY(-50%)' if vertical else f'top:{conteudo}px'}}}
.selo{{display:inline-block;background:{LIME};color:{NAVY};font-size:calc(28px*var(--k));font-weight:800;letter-spacing:.06em;
  text-transform:uppercase;border-radius:12px;padding:10px 20px;margin-bottom:30px}}
h1{{font-size:calc(100px*var(--k));line-height:1.03;font-weight:800;letter-spacing:-.025em}}
h2{{font-size:calc(72px*var(--k));line-height:1.06;font-weight:800;letter-spacing:-.02em;margin-bottom:calc(40px*var(--k))}}
em{{font-style:normal;color:{LIME}}}
p.lead{{font-size:calc(44px*var(--k));line-height:1.36;color:#D7DCF0;margin-top:calc(40px*var(--k))}}
p.lead b,p.par b,li b{{color:{LIME}}}
p.par{{font-size:calc(40px*var(--k));line-height:1.4;color:#E9ECF7;margin-bottom:calc(28px*var(--k))}}
ul{{list-style:none}}
li{{font-size:calc(39px*var(--k));line-height:1.32;padding:calc(26px*var(--k)) 0 calc(26px*var(--k)) 58px;border-top:2px solid rgba(255,255,255,.16);position:relative;color:#E9ECF7}}
li:last-child{{border-bottom:2px solid rgba(255,255,255,.16)}}
li::before{{content:'';position:absolute;left:0;top:calc(40px*var(--k));width:26px;height:26px;border-radius:7px;background:{LIME}}}
.tabela{{border-radius:24px;overflow:hidden;background:{BRANCO}}}
.linha{{display:flex;font-size:calc(34px*var(--k));line-height:1.3;color:{NAVY}}}
.linha+.linha{{border-top:2px solid #E3E6F0}}
.linha .s{{width:42%;padding:calc(28px*var(--k)) 30px;font-weight:800;font-size:calc(30px*var(--k))}}
.linha .d{{width:58%;padding:calc(28px*var(--k)) 30px}}
.ok{{color:#1E7A35}}.parc{{color:#9A6A00}}.usada{{color:#4B5578}}.nao{{color:#B3261E}}
.alerta{{margin-top:calc(44px*var(--k));background:{LIME};color:{NAVY};border-radius:24px;padding:calc(36px*var(--k)) 42px;font-size:calc(37px*var(--k));line-height:1.34;font-weight:500}}
.alerta b{{font-weight:800}} .alerta em{{color:{NAVY};font-weight:800}}
.nota{{font-size:calc(29px*var(--k));line-height:1.4;color:#B9C0DE;margin-top:calc(36px*var(--k))}}
.numero{{font-size:calc(230px*var(--k));line-height:1;font-weight:900;color:{LIME};letter-spacing:-.04em;margin-bottom:24px}}
.caixa{{border-radius:24px;padding:calc(36px*var(--k)) 42px;font-size:calc(38px*var(--k));line-height:1.36}}
.caixa .r{{display:block;font-size:calc(26px*var(--k));font-weight:800;letter-spacing:.08em;text-transform:uppercase;margin-bottom:14px}}
.mito{{background:rgba(255,255,255,.08);border:2px solid rgba(255,255,255,.2);color:#D7DCF0;margin-bottom:28px}}
.mito .r{{color:#FF8A80}}
.verdade{{background:{LIME};color:{NAVY}}} .verdade .r{{color:{NAVY}}} .verdade em,.verdade b{{color:{NAVY};font-weight:800}}
.frase{{font-size:calc(68px*var(--k));line-height:1.18;font-weight:800;letter-spacing:-.015em}}
.aspas{{font-size:200px;line-height:.6;color:{LIME};font-weight:900;display:block;height:110px}}
.assin{{margin-top:44px;font-size:32px;color:{LIME};font-weight:700}}
.opcao{{background:{BRANCO};color:{NAVY};border-radius:22px;padding:calc(30px*var(--k)) 38px;font-size:calc(40px*var(--k));font-weight:700;margin-top:24px}}
.rodape{{position:absolute;bottom:{base}px;left:80px;right:80px;display:flex;justify-content:space-between;align-items:center}}
.marca{{display:flex;align-items:center;gap:18px}}
.marca img.s{{width:54px;height:54px}} .marca img.n{{height:62px}}
.arroba{{font-size:26px;color:#B9C0DE;font-weight:600}}
.dots{{display:flex;gap:10px}} .dots span{{width:14px;height:14px;border-radius:4px;background:rgba(255,255,255,.25)}}
.dots span.on{{background:{LIME}}}
.simbolo-grande{{position:absolute;right:-120px;bottom:-120px;width:620px;opacity:.10}}
.dica{{margin-top:60px;font-size:32px;font-weight:700;color:{LIME}}}
.logo-final{{width:560px;display:block;margin:0 auto 40px}}
.centro{{text-align:center}}
.fonte{{font-size:25px;line-height:1.45;color:#9AA3C9;margin-top:40px}}
"""


def selo(t):
    return f'<div class="selo">{t["selo"]}</div>' if t.get("selo") else ""


def corpo(t):
    tipo = t["tipo"]
    if tipo == "capa":
        dica = f'<div class="dica">{t["dica"]}</div>' if t.get("dica") else ""
        return (f'<img class="simbolo-grande" src="{SIMBOLO}">{selo(t)}<h1>{t["titulo"]}</h1>'
                f'<p class="lead">{t.get("lead", "")}</p>{dica}')
    if tipo == "lista":
        itens = "".join(f"<li>{i}</li>" for i in t["itens"])
        alerta = f'<div class="alerta">{t["alerta"]}</div>' if t.get("alerta") else ""
        nota = f'<p class="nota">{t["nota"]}</p>' if t.get("nota") else ""
        return f'{selo(t)}<h2>{t["titulo"]}</h2><ul>{itens}</ul>{alerta}{nota}'
    if tipo == "tabela":
        linhas = "".join(f'<div class="linha"><div class="s {c}">{r}</div><div class="d">{d}</div></div>'
                         for r, d, c in t["linhas"])
        nota = f'<p class="nota">{t["nota"]}</p>' if t.get("nota") else ""
        return f'{selo(t)}<h2>{t["titulo"]}</h2><div class="tabela">{linhas}</div>{nota}'
    if tipo == "texto":
        pars = "".join(f'<p class="par">{p}</p>' for p in t["paragrafos"])
        alerta = f'<div class="alerta">{t["alerta"]}</div>' if t.get("alerta") else ""
        return f'{selo(t)}<h2>{t["titulo"]}</h2>{pars}{alerta}'
    if tipo == "numero":
        return (f'{selo(t)}<div class="numero">{t["numero"]}</div><h2>{t["titulo"]}</h2>'
                f'<p class="lead">{t.get("lead", "")}</p>')
    if tipo == "mito":
        nota = f'<p class="nota">{t["nota"]}</p>' if t.get("nota") else ""
        return (f'{selo(t)}<div class="caixa mito"><span class="r">Mito</span>{t["mito"]}</div>'
                f'<div class="caixa verdade"><span class="r">Verdade</span>{t["verdade"]}</div>{nota}')
    if tipo == "frase":
        assin = f'<div class="assin">{t["assinatura"]}</div>' if t.get("assinatura") else ""
        return f'<span class="aspas">“</span><div class="frase">{t["frase"]}</div>{assin}'
    if tipo == "enquete":
        ops = "".join(f'<div class="opcao">{o}</div>' for o in t.get("opcoes", []))
        return f'{selo(t)}<h2>{t["pergunta"]}</h2>{ops}<p class="lead">{t.get("lead", "")}</p>'
    if tipo == "final":
        cta = f'<p class="lead centro">{t["cta"]}</p>' if t.get("cta") else ""
        fontes = f'<p class="fonte centro">Fontes: {t["fontes"]}</p>' if t.get("fontes") else ""
        return f'<img class="logo-final" src="{LOGO}"><h2 class="centro">{t["titulo"]}</h2>{cta}{fontes}'
    raise ValueError(f"tipo de tela desconhecido: {tipo}")


def faixa_cta(t):
    if t["tipo"] == "final" or not t.get("cta"):
        return ""
    return f'<div class="alerta">{t["cta"]}</div>'


def pagina(spec, n, total, t, w, h, vertical):
    dots = "".join(f'<span class="{"on" if i == n else ""}"></span>' for i in range(1, total + 1)) if total > 1 else ""
    pill = f'<span class="pill">{n}/{total}</span>' if total > 1 and spec["formato"] == "carrossel" else ""
    if t["tipo"] == "final":   # logo grande no centro; rodapé leva o @ e o nome
        marca = f'<div class="marca"><img class="n" src="{NOME}"><span class="arroba">{ARROBA}</span></div>'
    else:
        marca = (f'<div class="marca"><img class="s" src="{SIMBOLO}"><img class="n" src="{NOME}">'
                 f'<span class="arroba">{ARROBA}</span></div>')
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><style>{css(w, h, vertical)}</style></head><body>
<div class="topo"><span class="tag">{spec["tag"]}</span>{pill}</div>
<div class="conteudo">{corpo(t)}{faixa_cta(t)}</div>
<div class="rodape">{marca}<div class="dots">{dots}</div></div></body></html>"""


def renderizar(pag, html):
    """Desenha, confere a marca e reduz a fonte até o texto caber acima do rodapé."""
    k = 1.0
    while True:
        pag.set_content(html.replace("--k:1}", f"--k:{k:.2f}}}"), wait_until="load")
        t, c, f, logo_ok = pag.evaluate("""()=>[document.querySelector('.conteudo').getBoundingClientRect().top
              - document.querySelector('.topo').getBoundingClientRect().bottom,
            document.querySelector('.conteudo').getBoundingClientRect().bottom,
            document.querySelector('.rodape').getBoundingClientRect().top,
            [...document.querySelectorAll('.marca img.n')].every(i=>i.complete&&i.naturalWidth>0)]""")
        if not logo_ok:
            raise RuntimeError("logo da marca não carregou: arte não pode sair sem a marca")
        if c < f - 30 and t > 30:
            return k
        if k <= 0.7:
            raise RuntimeError(f"texto não cabe mesmo com fonte a {k:.0%}: encurte o conteúdo")
        k -= 0.05


def gerar(caminho_json):
    arq = Path(caminho_json).resolve()
    spec = json.loads(arq.read_text(encoding="utf-8"))
    fmt = spec["formato"]
    w, h = TAMANHOS[fmt]
    vertical = h > 1350
    telas = spec["telas"]
    mn, mx = LIMITES[fmt]
    if not mn <= len(telas) <= mx:
        raise ValueError(f"{fmt} pede de {mn} a {mx} telas; vieram {len(telas)}")
    if not telas[-1].get("cta"):
        raise ValueError("a última tela precisa de chamada para ação (campo \"cta\"); ver ROTINA.md, seção 3")
    saida = arq.parent
    for antigo in list(saida.glob("*.jpg")) + list(saida.glob("*.mp4")):
        antigo.unlink()
    nomes = []
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        pag = nav.new_page(viewport={"width": w, "height": h})
        for i, t in enumerate(telas, start=1):
            k = renderizar(pag, pagina(spec, i, len(telas), t, w, h, vertical))
            nome = {"stories": f"story-{i:02d}.jpg", "reel": f"quadro-{i:02d}.jpg"}.get(fmt, f"{i:02d}.jpg")
            pag.screenshot(path=str(saida / nome), type="jpeg", quality=92)
            nomes.append(nome)
            print(f"{nome}  fonte {k:.0%}")
        nav.close()
    if fmt == "reel":
        montar_reel(saida, nomes, spec.get("segundos_por_tela", 3.5))
    previa(saida, nomes, vertical)
    return nomes


def montar_reel(saida, nomes, seg):
    """Vídeo vertical H.264 com transição suave entre as telas e trilha silenciosa."""
    (saida / "capa.jpg").write_bytes((saida / nomes[0]).read_bytes())
    entradas, filtros = [], []
    for n in nomes:
        entradas += ["-loop", "1", "-t", f"{seg}", "-i", str(saida / n)]
    fade = 0.5
    ultimo = "[0:v]"
    for i in range(1, len(nomes)):
        off = i * (seg - fade)
        rot = f"[v{i}]"
        filtros.append(f"{ultimo}[{i}:v]xfade=transition=slideleft:duration={fade}:offset={off:.2f}{rot}")
        ultimo = rot
    total = len(nomes) * seg - (len(nomes) - 1) * fade
    cmd = ["ffmpeg", "-y", "-loglevel", "error", *entradas,
           "-f", "lavfi", "-t", f"{total:.2f}", "-i", "anullsrc=r=44100:cl=stereo",
           "-filter_complex", ";".join(filtros) + f";{ultimo}format=yuv420p,fps=30[v]",
           "-map", "[v]", "-map", f"{len(nomes)}:a", "-c:v", "libx264", "-preset", "veryfast",
           "-crf", "20", "-c:a", "aac", "-shortest", "-movflags", "+faststart", str(saida / "reel.mp4")]
    subprocess.run(cmd, check=True)
    print(f"reel.mp4  {total:.1f}s")


def previa(saida, nomes, vertical):
    from PIL import Image
    ims = [Image.open(saida / n) for n in nomes]
    w = 300
    hh = int(w * (1920 / 1080 if vertical else 1350 / 1080))
    cols = min(len(ims), 5)
    linhas = (len(ims) + cols - 1) // cols
    g = Image.new("RGB", (cols * (w + 10) + 10, linhas * (hh + 10) + 10), "white")
    for k, im in enumerate(ims):
        g.paste(im.resize((w, hh)), (10 + (k % cols) * (w + 10), 10 + (k // cols) * (hh + 10)))
    g.save(saida / "previa.jpg", quality=88)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    gerar(sys.argv[1])
