# Rotina diária de postagem — Organize Farma (@betaniaalhan)

Um post por dia, cada dia num formato diferente. O assunto não se repete:
o tema pode voltar, mas cada post traz uma informação nova.
Toda arte sai com a logo, o nome "Organize farma" e as cores da marca.
**Nada é publicado sem o OK da Dra. Betânia.**

## 1. Calendário de formatos

| dia | formato | tipo de conteúdo | horário sugerido |
|---|---|---|---|
| segunda | **carrossel** (5–7 telas) | ENSINA: passo a passo ou checklist aplicável hoje | 12h |
| terça | **reel** animado (4–5 telas, ~15 s) | VOCÊ SABIA / pergunta e resposta rápida | 19h |
| quarta | **card** único | NÚMERO: um prazo, validade ou dado da norma em destaque | 12h |
| quinta | **carrossel** (4–6 telas) | ERROS COMUNS ou comparação em tabela (X × Y) | 12h |
| sexta | **reel** animado (3–4 telas) | OPINIÃO / frase da Dra. Betânia sobre o setor | 19h |
| sábado | **card** único | MITO × VERDADE | 10h |
| domingo | **stories** (3–5 telas) | ENQUETE ou caixa de perguntas + bastidor da semana | 18h |

Novidade regulatória urgente (norma nova, prazo, prorrogação) entra no lugar
do post do dia como **ALERTA**, no formato do dia. Se o tema já saiu nos
últimos 7 dias, vira só stories.

## 2. Pilares (temas) e regras de variedade

| código | pilar |
|---|---|
| CTRL | SNCR, receituários e medicamentos controlados (RDC 1.000/2025, Portaria 344/98, SNGPC) |
| ATM | Antimicrobianos e GLP-1 (RDC 471/2021, RDC 973/2025, IN 360/2025) |
| LIC | Licenças, vigilância sanitária e documentação (AFE, licença, POPs, PGRSS, autoinspeção) |
| SERV | Serviços farmacêuticos (EAC — RDC 978 e 986/2025, vacinação, prescrição, testes) |
| PUB | Publicidade, comunicação e vitrine (RDC 96/2008) |
| CAR | Carreira, liderança e responsabilidade técnica do farmacêutico |

1. Antes de criar, leia `posts/registro.csv` (tudo o que já foi feito).
2. **Nunca o mesmo pilar em dois dias seguidos**; no máximo 2 vezes por semana.
3. **Nunca o mesmo ângulo em menos de 60 dias.** Ângulo = a informação específica
   do post. Se um ponto já saiu, só pode ser citado em uma frase ("veja o post de…").
4. Escolha o ângulo em `banco-de-angulos.md` (marque como usado) ou crie um novo
   a partir de notícia da semana.
5. Todo dado regulatório é conferido na fonte oficial do dia (Anvisa, DOU, CFF, CRF)
   antes de entrar na arte. Datas, números de norma e prazos com fonte.
6. Nada de promover medicamento de venda sob prescrição ao público (RDC 96/2008).
   Não inventar casos nem números.

## 3. Identidade visual (obrigatória)

- Logo oficial (símbolo + "Organize farma") e @betaniaalhan em **todas** as telas.
- Cores: azul-marinho **#0F1C52** (fundo), verde-limão **#BDE513** (destaques), branco.
- Feed 1080×1350 JPEG; stories e reels 1080×1920.
- Use sempre o gerador `fonte/arte.py`: ele aplica a marca e **falha se a logo
  não aparecer** ou se o texto não couber.

## 4. Como produzir o post do dia

```
pasta=posts/AAAA-MM-DD-assunto-curto
mkdir -p $pasta
# escreva $pasta/post.json   (formatos e tipos de tela: ver topo de fonte/arte.py)
# escreva $pasta/legenda.txt (1ª linha com gancho; fonte da norma; 3 a 5 hashtags)
python3 fonte/arte.py $pasta/post.json
cd ferramenta && python3 -m insta_organize verificar-legenda ../$pasta/legenda.txt
```
Olhe a `previa.jpg` antes de enviar. Acrescente a linha no `posts/registro.csv`
com status `aguardando`, faça commit e push, e envie à Dra. Betânia a prévia e a
legenda, com o horário sugerido, perguntando se pode publicar.

Stories com enquete/caixa de perguntas: a API do Instagram não coloca figurinhas.
As telas vão prontas e ela publica pelo app, adicionando o figurinha na tela marcada.

## 5. Publicação (só depois do "publica" dela)

- Imagens/vídeo ficam públicos em
  `https://raw.githubusercontent.com/betaniaalhan-sudo/organizefarma-midia/main/<pasta>/<arquivo>`.
- A API (graph.facebook.com, v26.0, IG user 17841404439734351) só é alcançável
  pelo Chrome dela: `fetch` via Claude in Chrome a partir de uma página do
  facebook.com. O token está no `.env` em
  `Documentos\instagram-organize-farma` (ler pela ponte, **nunca exibir**).
- Fluxo: criar containers (`/media`), esperar `status_code=FINISHED`,
  `/media_publish`. Carrossel: itens com `is_carousel_item=true` e pai
  `media_type=CAROUSEL`. Reel: `media_type=REELS`, `video_url`, `cover_url`.
  Card: `image_url`.
- Depois de publicar: status `publicado` e o id da mídia no registro; commit e push.
