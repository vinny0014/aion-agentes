# GUIA DE PUBLICAÇÃO — AION AGENTES

Siga na ordem. Copie e cole cada comando. Linhas que começam com `#` são só explicação — não precisa copiar.

---

## PASSO 1 — Descompactar o projeto

Abra o Terminal (Mac/Linux) ou o **Git Bash** (Windows — instale em https://git-scm.com se não tiver) na pasta onde está o arquivo baixado e rode:

```bash
mkdir aion-agentes
tar -xzf aion-agentes-v1.1.tar.gz -C aion-agentes
cd aion-agentes
ls
```

✅ Você deve ver: `backend  frontend  README.md  vercel.json  render.yaml` (entre outros).

---

## PASSO 2 — Subir para o GitHub

**2.1.** Entre em https://github.com/new e crie um repositório:
- Repository name: `aion-agentes`
- Deixe **Public** ou **Private** (tanto faz)
- **NÃO** marque "Add a README" nem nenhuma outra opção
- Clique no botão verde **Create repository**

**2.2.** De volta ao terminal, dentro da pasta `aion-agentes`, rode (troque `SEU_USUARIO` pelo seu usuário do GitHub):

```bash
git remote add origin https://github.com/SEU_USUARIO/aion-agentes.git
git push -u origin main
```

Se pedir senha: o GitHub não aceita mais senha comum, ele quer um **token**. Crie em https://github.com/settings/tokens → **Generate new token (classic)** → marque a caixa **repo** → **Generate** → copie o token e cole no lugar da senha.

✅ Recarregue a página do repositório: os arquivos devem aparecer, e a aba **Actions** vai rodar os testes sozinha (fica verde em ~2 minutos).

---

## PASSO 3 — Backend no Render (faça ANTES da Vercel)

> Fazemos o backend primeiro porque a Vercel vai precisar do endereço dele.

**3.1.** Entre em https://render.com e crie conta / faça login (pode usar o botão "Sign in with GitHub").

**3.2.** No painel, clique em **New +** (canto superior direito) → **Blueprint**.

**3.3.** Conecte sua conta GitHub se pedir, e selecione o repositório **aion-agentes**.

**3.4.** O Render vai ler o arquivo `render.yaml` e mostrar o serviço **aion-news-api**. Clique em **Apply** (ou **Deploy Blueprint**).

**3.5.** Aguarde o deploy terminar (5–10 min). Ao final, copie a URL do serviço — algo como:
`https://aion-news-api.onrender.com`
**Guarde essa URL, você vai usar no Passo 4 e 5.**

---

## PASSO 4 — Frontend na Vercel

**4.1.** Entre em https://vercel.com e faça login (botão "Continue with GitHub").

**4.2.** Clique em **Add New…** → **Project**.

**4.3.** Ache **aion-agentes** na lista e clique em **Import**.

**4.4.** Nas configurações que aparecem:
- **Root Directory:** clique em **Edit** e escolha a pasta `frontend`
- **Framework Preset:** Vite (detecta sozinho)
- Abra **Environment Variables** e adicione:
  - Name: `VITE_API_URL`
  - Value: a URL do Render do Passo 3.5 (ex.: `https://aion-news-api.onrender.com`) — **sem barra no final**

**4.5.** Clique em **Deploy** e aguarde (~2 min).

**4.6.** Copie a URL final do site — algo como `https://aion-news-os.vercel.app`.

**4.7.** ÚLTIMO AJUSTE — avisar o backend qual é o endereço do site (CORS):
- Volte ao Render → serviço **aion-news-api** → aba **Environment**
- Edite a variável `CORS_ORIGINS` e coloque a URL da Vercel do passo 4.6 (ex.: `https://aion-news-os.vercel.app`)
- Clique em **Save Changes** (o serviço reinicia sozinho)

---

## PASSO 5 — Variáveis do .env (referência)

**Em produção você NÃO cria arquivo .env** — as variáveis ficam nos painéis (Render/Vercel), como feito acima. O `render.yaml` já configurou quase tudo sozinho:

| Onde | Variável | Valor |
|---|---|---|
| Render | `SECRET_KEY` | gerada automaticamente pelo Blueprint ✅ |
| Render | `CORS_ORIGINS` | URL da Vercel (você ajustou no 4.7) |
| Render | `DATABASE_URL` | já configurada com disco persistente ✅ |
| Render | `ANTHROPIC_API_KEY` (ou `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `GEMINI_API_KEY`) | **opcional** — adicione quando quiser que a IA escreva os artigos completos. Sem ela, o sistema gera rascunhos estruturados. |
| Vercel | `VITE_API_URL` | URL do Render (você colocou no 4.4) |

**Para rodar no SEU computador** (opcional), aí sim usa .env:

```bash
cd backend
cp .env.example .env
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```
Copie o texto que apareceu e cole no `.env` na linha `SECRET_KEY=`. Depois:
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
E em outro terminal:
```bash
cd frontend
npm install
npm run dev
```
Acesse http://localhost:5173

---

## PASSO 6 — Testar se está tudo no ar

**6.1.** Teste o backend (troque pela sua URL do Render):

```bash
curl https://aion-news-api.onrender.com/api/health
```
✅ Deve responder algo com `"status":"ok"` e `"database":"ok"`.
⚠️ No plano gratuito do Render, a primeira chamada pode demorar ~50 segundos (o serviço "acorda"). É normal.

**6.2.** Teste o site: abra a URL da Vercel no navegador.
✅ A landing page deve carregar com o "Quadro de operação".

**6.3.** Teste o fluxo completo:
1. Clique em **Criar conta** e cadastre-se → **o primeiro usuário cadastrado vira admin automaticamente**
2. Você deve cair no **Dashboard** com os 9 agentes
3. Clique em **Administração** → aba **Conteúdo** → **Novo artigo** → escreva algo → **Publicar**
4. Abra `https://SEU-SITE.vercel.app/conteudos` → o artigo deve aparecer
5. Teste a fila: aba **Fila** → adicione um tópico → **Processar fila agora** → um rascunho aparece na aba Conteúdo

**6.4.** Teste o SEO:
```bash
curl https://aion-news-api.onrender.com/robots.txt
curl https://aion-news-api.onrender.com/sitemap.xml
```

**6.5.** (Opcional) Popular com artigos de demonstração: no Render, abra a aba **Shell** do serviço e rode:
```bash
python scripts_seed.py
```

---

## PASSO 7 — Se der erro

**"git: command not found"**
→ Instale o Git: https://git-scm.com/downloads

**Push rejeitado / pede senha e falha**
→ Use o token do GitHub como senha (Passo 2.2). Ou instale o GitHub CLI e rode `gh auth login`.

**Deploy do Render falhou**
→ Abra a aba **Logs** do serviço e leia a última linha vermelha. Causa mais comum: branch errada — confirme que o código está na branch `main`.

**Site abre mas login/cadastro dá erro ou "Failed to fetch"**
→ 90% das vezes é um destes dois:
1. `VITE_API_URL` errada na Vercel (confira se é a URL do Render, sem `/` no final). Depois de corrigir, vá em **Deployments** → **Redeploy**.
2. `CORS_ORIGINS` no Render sem a URL da Vercel (Passo 4.7).

**Backend responde 502 ou demora**
→ Plano gratuito do Render hiberna. Espere ~1 minuto e tente de novo.

**"Muitas tentativas. Aguarde um minuto."**
→ É a proteção de rate limit funcionando. Espere 60 segundos.

**Página do site dá 404 ao atualizar (F5)**
→ Confirme que o Root Directory na Vercel é `frontend` (o `vercel.json` cuida do resto). Redeploy.

**Fila gera só rascunhos, não artigos completos**
→ Comportamento esperado sem API de IA. Adicione `ANTHROPIC_API_KEY` (ou outra) no Environment do Render e reprocesse a fila.

**Qualquer outro erro**
→ Copie a mensagem exata do log (Render → Logs, ou Vercel → Deployments → clique no deploy → Logs) e me envie aqui que eu corrijo.
