# Instagram da Organize Farma — ferramenta pela API oficial

Publica posts, carrosséis, Reels e stories, lê métricas e comentários e
**checa a legenda contra a RDC 96/2008** antes de publicar.

Substitui a antiga biblioteca `python-instagram` (facebookarchive), que não
funciona mais: ela usava a API Legacy do Instagram, já desligada pela Meta.
Esta ferramenta usa a **Instagram API com Instagram Login**
(`graph.instagram.com`, versão v26.0).

---

## 1. Antes de começar (uma vez só)

| O que | Por quê |
|---|---|
| Conta do Instagram **profissional** (Empresa ou Criador de conteúdo) | A API não funciona em conta pessoal. No app: Configurações → Tipo de conta e ferramentas → Mudar para conta profissional. |
| Python 3.9 ou mais novo | Para rodar a ferramenta. No Mac, já vem instalado ou instale por python.org. |
| Imagens e vídeos em **URL pública** | A Meta baixa a mídia de um link. Imagem só em **JPEG**. Vídeo em MP4. Serve um link de site, um bucket de nuvem, etc. Links do Google Drive/Dropbox normalmente não funcionam. |

Instalação, dentro desta pasta:

```bash
python3 -m pip install requests
```

> **No Windows**: instale o Python pelo site python.org (marque *Add Python to PATH*),
> abra o *Prompt de Comando* nesta pasta e troque `python3` por `py` em todos os
> comandos deste guia. Ex.: `py -m pip install requests` e `py -m insta_organize conta`.
> Para agendar o calendário, use o *Agendador de Tarefas* do Windows.

## 2. Criar o app na Meta e gerar o token (precisa da sua conta)

1. Acesse **developers.facebook.com** → *Meus apps* → *Criar app*.
2. Caso de uso: **Gerenciar mensagens e conteúdo no Instagram** (tipo *Empresa*).
3. No painel do app, abra **API do Instagram → Configuração da API com login do Instagram**.
4. Em *Gerar tokens de acesso*, clique em **Adicionar conta** e entre com o Instagram da Organize Farma.
5. Autorize as permissões:
   - `instagram_business_basic`
   - `instagram_business_content_publish`
   - `instagram_business_manage_comments`
   - `instagram_business_manage_insights`
6. Copie o **token gerado** (já vem com validade de 60 dias) e o **ID da conta do Instagram**.
7. Copie `.env.exemplo` para `.env` e preencha `IG_ACCESS_TOKEN` e `IG_USER_ID`.

> Enquanto o app estiver em *modo de desenvolvimento*, ele funciona para as
> contas adicionadas como testadoras/administradoras — o suficiente para uso
> próprio. Não é preciso enviar o app para análise da Meta só para publicar
> no seu próprio perfil.

Teste:

```bash
python3 -m insta_organize conta
python3 -m insta_organize limite
```

**Renovação:** o token vale 60 dias. Rode `python3 -m insta_organize renovar-token`
pelo menos uma vez por mês (ele precisa ter mais de 24 h e ainda não ter vencido).
O novo token é gravado no `.env` automaticamente.

## 3. Uso do dia a dia

### Checar uma legenda (não precisa de token)

```bash
python3 -m insta_organize verificar-legenda "Texto da legenda aqui"
python3 -m insta_organize verificar-legenda --arquivo-legenda legenda.txt
```

Níveis de alerta:
- **ALTO** — trava a publicação (ex.: nome de medicamento tarjado/controlado/GLP-1,
  "comprovado cientificamente", "sem efeitos colaterais", ressaca/excessos).
- **MÉDIO** — revisar (imperativos como "tome/use", desconto sem preço integral,
  sorteio, falta da advertência obrigatória).
- **INFO** — lembrete (ex.: "novo", "seguro/eficaz").

É uma triagem por padrões de texto. **Não substitui a revisão da RT.**

### Publicar

```bash
python3 -m insta_organize publicar-imagem https://SEU-SITE/post.jpg --legenda "..." --alt "descrição da imagem"
python3 -m insta_organize publicar-carrossel https://SEU-SITE/1.jpg https://SEU-SITE/2.jpg --arquivo-legenda legenda.txt
python3 -m insta_organize publicar-reel https://SEU-SITE/video.mp4 --legenda "..." --capa https://SEU-SITE/capa.jpg
python3 -m insta_organize publicar-story https://SEU-SITE/story.jpg
```

Se a checagem der alerta ALTO, a publicação para. Depois de revisar, dá para
forçar com `--forcar`.

### Calendário de conteúdo (CSV)

```bash
python3 -m insta_organize modelo-calendario calendario.csv     # cria um exemplo
python3 -m insta_organize calendario calendario.csv            # SIMULA (não publica)
python3 -m insta_organize calendario calendario.csv --executar # publica o que já venceu
```

Colunas: `data_hora; tipo; midias; legenda; capa; status; media_id; observacao`.
- `tipo`: imagem, carrossel, reel ou story.
- `midias`: URL pública; no carrossel, separe por `|`.
- A ferramenta preenche `status` (publicado / erro / bloqueado), `media_id` e `observacao`.
- Itens já publicados nunca são publicados de novo.

Abre normalmente no Excel. Para publicar sozinho no horário, agende o comando
com `--executar` (ex.: a cada 30 minutos) no agendador do computador.

### Métricas e comentários

```bash
python3 -m insta_organize posts --limite 12
python3 -m insta_organize metricas-conta --desde 2026-10-01 --ate 2026-10-31
python3 -m insta_organize metricas-post ID_DO_POST --tipo REELS
python3 -m insta_organize relatorio --limite 30 --saida relatorio_outubro.csv
python3 -m insta_organize comentarios ID_DO_POST
python3 -m insta_organize responder ID_DO_COMENTARIO "Obrigada pela pergunta! ..."
python3 -m insta_organize ocultar ID_DO_COMENTARIO
```

O relatório sai em CSV (`;`), pronto para o Excel.

## 4. Limites e regras da Meta (conferir na documentação oficial)

- Publicações via API: cota por 24 h (a documentação cita 100; carrossel conta como 1). Consulte com `limite`.
- Carrossel: 2 a 20 itens. A Meta **não fornece métricas de carrossel**.
- Imagem: só JPEG. Vídeo: MP4; Reels processam por alguns minutos antes de publicar.
- Métricas descontinuadas em 2025 (`impressions`, `plays`, `video_views`) não são usadas.
- Métricas de story só ficam disponíveis por 24 h.

## 5. Erros comuns

| Mensagem | O que fazer |
|---|---|
| Token inválido ou vencido (código 190) | Gere um novo no painel da Meta ou rode `renovar-token`. |
| Não conseguiu baixar a mídia | A URL precisa abrir sem login, e a imagem precisa ser JPEG. |
| Limite atingido | Aguarde a janela de 24 h. |
| Permissão faltando | Gere o token de novo marcando as 4 permissões `instagram_business_*`. |

## 6. Testes

```bash
python3 -m pip install pytest
python3 -m pytest -q
```

Os testes simulam a API: não publicam nada nem precisam de token.
