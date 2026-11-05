# Rotina diária de postagem — Organize Farma (@betaniaalhan)

Um post por dia, cada dia num formato diferente. O assunto não se repete:
o tema pode voltar, mas cada post traz uma informação nova.
Toda arte sai com a logo, o nome "Organize farma" e as cores da marca.
**Nada é publicado sem o OK da Dra. Betânia.**

## 1. Calendário de formatos e temas (a partir de 05/11/2026)

Cada dia da semana tem um TEMA fixo. O formato continua variando.

| dia | formato | tema do dia | horário sugerido |
|---|---|---|---|
| segunda | **carrossel** (5–7 telas) | **VIGILÂNCIA SANITÁRIA**: normas da Anvisa, da vigilância estadual e da municipal (licença, AFE, POPs, inspeção, RDCs) | 12h |
| terça | **reel** animado (4–5 telas, ~15 s) | **CFF E ATUAÇÃO DO FARMACÊUTICO**: resoluções do CFF sobre atribuições, responsabilidades e áreas de atuação; licenciamento de consultório farmacêutico, telefarmácia e farmácia | 19h |
| quarta | **card** único | **CARREIRA**: crescimento e desenvolvimento profissional do farmacêutico (ponte para a mentoria) | 12h |
| quinta | **carrossel** (4–6 telas) | **PERFIL COMPORTAMENTAL**: liga com o tema de quarta. O farmacêutico está na atividade certa para o perfil dele? Gasta energia demais no que poderia fazer melhor e mais rápido? | 12h |
| sexta | **reel** animado (3–4 telas) | **SEXTOU (LEVE)**: tom leve e bem-humorado, lembrando que muito farmacêutico trabalha sábado, domingo e feriado; chama para a mentoria (mais tempo de qualidade) | 19h |
| sábado | **card** único | **MITO × VERDADE** (tema livre entre os pilares, respeitando a variedade) | 10h |
| domingo | **stories** (3–5 telas) | **ENQUETE** ou caixa de perguntas + bastidor da semana | 18h |

Novidade regulatória urgente (norma nova, prazo, prorrogação) entra no lugar
do post do dia como **ALERTA**, no formato do dia. Se o tema já saiu nos
últimos 7 dias, vira só stories.

## 2. Pilares (temas) e regras de variedade

| código | pilar | dia |
|---|---|---|
| VISA | Vigilância sanitária: Anvisa, estadual e municipal (AFE, licença, POPs, PGRSS, inspeção, controlados, antimicrobianos, RDC 44/2009, RDC 1.000/2025…) | segunda |
| CFF | Resoluções do CFF: atribuições, responsabilidades, áreas de atuação; licenciamento de consultório, telefarmácia e farmácia | terça |
| CAR | Carreira e desenvolvimento do farmacêutico | quarta |
| PERF | Perfil comportamental e energia no trabalho (liga com a quarta) | quinta |
| LEVE | Sextou: leve, humor, descanso e qualidade de vida do farmacêutico | sexta |

Sábado e domingo usam qualquer pilar acima, sem repetir o pilar do dia anterior.
Os códigos antigos (CTRL, ATM, LIC, SERV, PUB) do registro contam como VISA,
exceto SERV, que conta como CFF.

1. Antes de criar, leia `posts/registro.csv` (tudo o que já foi feito).
2. O tema do dia manda (segunda a sexta). No sábado/domingo, nunca o mesmo pilar do dia anterior.
3. **Nunca o mesmo ângulo em menos de 60 dias.** Ângulo = a informação específica
   do post. Se um ponto já saiu, só pode ser citado em uma frase ("veja o post de…").
4. Escolha o ângulo em `banco-de-angulos.md` (marque como usado) ou crie um novo
   a partir de notícia da semana.
5. Todo dado regulatório é conferido na fonte oficial do dia (Anvisa, DOU, CFF, CRF,
   vigilância estadual/municipal) antes de entrar na arte. Datas, números de norma e prazos com fonte.
6. Nada de promover medicamento de venda sob prescrição ao público (RDC 96/2008).
   Não inventar casos nem números.
7. CAR, PERF e LEVE: sem promessas de resultado ("dobre seu salário"), sem
   diagnóstico de perfil pelo post e sem estatísticas sem fonte. Pergunta e
   reflexão funcionam melhor que afirmação.

## 3. Identidade visual (obrigatória)

- Logo oficial (símbolo + "Organize farma") e @betaniaalhan em **todas** as telas.
- Cores: azul-marinho **#0F1C52** (fundo), verde-limão **#BDE513** (destaques), branco.
- Feed 1080×1350 JPEG; stories e reels 1080×1920.
- Use sempre o gerador `fonte/arte.py`: ele aplica a marca e **falha se a logo
  não aparecer**, se o texto não couber ou se faltar a chamada para ação.

### Chamada para ação (CTA) — obrigatória em todo post

Todo post informa **e** convida. A **última tela** sempre leva a CTA da
Organize Farma (no carrossel/reel/stories, a tela `final` com `cta`; no card
único, o campo `cta` na própria tela). A legenda também termina com a CTA.

- Temas técnicos (VISA, CFF, ALERTA): "Está com dificuldade? Sua empresa ainda
  não resolveu isso? **Fale com a Organize Farma. Nós resolvemos para você.**"
  Na terça, quando couber: "Fazemos o licenciamento de consultório farmacêutico,
  telefarmácia e farmácia."
- Temas de carreira (CAR, PERF, LEVE): "Quer desenvolver sua carreira e ter mais
  tempo de qualidade? **Fale com a Organize Farma sobre a mentoria de
  desenvolvimento de carreira.**"
- Canal: "Chame no Direct" (até a Dra. Betânia definir outro canal, como WhatsApp).
- Pode variar as palavras, mas não a ideia: problema → Organize Farma resolve → como chamar.

## 4. Como produzir o post do dia

```
pasta=posts/AAAA-MM-DD-assunto-curto
mkdir -p $pasta
# escreva $pasta/post.json   (formatos e tipos de tela: ver topo de fonte/arte.py)
# escreva $pasta/legenda.txt (1ª linha com gancho; fonte da norma; 3 a 5 hashtags)
# escreva $pasta/acessibilidade.txt (texto alternativo de cada tela: "Tela 1:", "Tela 2:"…)
python3 fonte/arte.py $pasta/post.json
cd ferramenta && python3 -m insta_organize verificar-legenda ../$pasta/legenda.txt
```
Olhe a `previa.jpg` antes de enviar. Acrescente a linha no `posts/registro.csv`
com status `aguardando`, faça commit e push, e envie à Dra. Betânia as artes
(as telas em ordem, e o reel.mp4 nos dias de reel), a legenda pronta para
copiar, com o horário sugerido, e **o texto alternativo de cada tela** (do
`acessibilidade.txt`), para ela colar em Configurações avançadas >
Acessibilidade no app. Sempre, em todo post, sem ela precisar pedir. **Ela publica pelo app.**

Stories com enquete/caixa de perguntas: a API do Instagram não coloca figurinhas.
As telas vão prontas e ela publica pelo app, adicionando a figurinha na tela marcada.

## 5. Publicação: SEMPRE pela Dra. Betânia, pelo app

**Desde 04/11/2026 não há publicação automática.** A Meta restringiu o portfólio
de empresas por suspeita de automação. Por isso:

- **Não publicar** por Windsor.ai, Graph API, Claude in Chrome nem nenhuma outra
  automação, mesmo que ela peça "publica". Nesse caso, lembre que a publicação é
  pelo app e mande de novo as artes e a legenda, se for útil.
- A rotina só **prepara**: artes, legenda, registro como `aguardando` e envio a ela.
- Quando ela avisar que publicou, mude o status para `publicado` (sem media_id,
  ou com o link do post se ela mandar), faça commit e push.
- Esta regra só muda se a Dra. Betânia pedir explicitamente a volta da
  publicação automática **depois** de a restrição da Meta ser resolvida.
