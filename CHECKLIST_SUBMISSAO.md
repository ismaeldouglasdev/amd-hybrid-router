# Submissão AMD Hackathon Act II — Track 1

## Checklist Passo a Passo

### ⬜ Passo 1: Conseguir FIREWORKS_API_KEY

O router **só funciona** com a chave da Fireworks AI. Sem ela, zero pontos.

```
1. Ir em https://fireworks.ai/login
2. Criar conta (ou logar)
3. Ir em API Keys → Create New Key
4. Copiar a key (formato: fw_3a_...)
5. Exportar:
   export FIREWORKS_API_KEY="fw_3a_..."
```

**Se não tiver créditos:** Usar os $50 do AMD AI Developer Program (se já se inscreveu, os créditos estão na sua conta Fireworks).

**Comando pra verificar:**
```bash
curl https://api.fireworks.ai/inference/v1/models \
  -H "Authorization: Bearer $FIREWORKS_API_KEY" | head -5
```

---

### ⬜ Passo 2: Rodar Accuracy Eval

Validar que o router escolhe o modelo certo e acerta as respostas.

```bash
cd /mnt/data/amd-hybrid-router
source .venv/bin/activate
FIREWORKS_API_KEY="fw_3a_..." python -m app.eval
```

**O que esperar:** Tabela com 8 tasks, accuracy por task, projeção de custo.
**Critério de aprovação:** ≥ 6/8 tasks com accuracy ≥ 50%.

Se falhar muito → ajustar os `_COMPLEX_TRIGGERS` em `app/router.py`
ou trocar o modelo mapeado pra uma task específica.

---

### ⬜ Passo 3: Rodar Docker Local (Teste de Containerização)

Obrigatório: **"All submissions must be containerized."**

```bash
# Build
cd /mnt/data/amd-hybrid-router
docker build -f Dockerfile.scoring -t hybrid-router-scoring .

# Run com a key
docker run --rm -p 8000:8000 \
  -e FIREWORKS_API_KEY="fw_3a_..." \
  hybrid-router-scoring

# Testar
curl http://localhost:8000/v1/route -X POST \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"say hello in 2 words"}'
```

**Verificar:** Health endpoint mostra "fireworks: configured"

---

### ⬜ Passo 4: Fazer Push pro GitHub (Público)

```bash
cd /mnt/data/amd-hybrid-router

# Renomear branch
git branch -m master main

# Criar repo no GitHub (via web ou gh CLI)
gh repo create amd-hybrid-router --public --source=. --push
# ou manual:
# 1. Ir em https://github.com/new
# 2. Criar repo SEM README, SEM .gitignore, SEM license
# 3. Rodar:
#    git remote add origin git@github.com:seu-user/amd-hybrid-router.git
#    git push -u origin main
```

---

### ⬜ Passo 5: Gravar Video Demo (2-3 min)

O que mostrar:
1. **0:00-0:30** — Contexto: "Hybrid router que escolhe o modelo Fireworks mais barato que ainda acerta"
2. **0:30-1:00** — CLI: `router run "prompt" --dry` mostrando decisão
3. **1:00-1:30** — API call com curl, mostrar resposta + custo
4. **1:30-2:00** — Dashboard: `/` com métricas em tempo real
5. **2:00-2:30** — Docker rodando, mostrar health check

**Ferramentas:** OBS Studio (Linux), ou `peek` pra GIF.

---

### ⬜ Passo 6: Preparar Slides

5 slides máx:
1. **Problema:** Modelos grandes são caros. Router decide qual usar.
2. **Solução:** Complexity classifier → cheapest adequate model
3. **Arquitetura:** Diagrama (app/router.py → Fireworks API)
4. **Resultados:** Benchmark accuracy + cost projection
5. **Demo:** Print do vídeo + link pro GitHub

Template: Google Slides ou PowerPoint. Exportar PDF.

---

### ⬜ Passo 7: Submeter no lablab.ai

1. Ir em https://lablab.ai/ai-hackathons/amd-developer-hackathon-act-ii
2. Clicar "Submit"
3. Preencher:
   - **Project Title:** "Hybrid Token-Efficient Routing Agent"
   - **Short Description:** "An intelligent router that selects the cheapest Fireworks AI model sufficient for each task, minimizing token usage while maintaining output accuracy."
   - **Long Description:** Explicar arquitetura, decisão de modelo, benchmark results
   - **Tags:** AI Agent, Routing, Token Optimization, Fireworks AI
4. Upload:
   - **Cover Image:** Screenshot do dashboard
   - **Video:** Demo gravado
   - **Slides:** PDF exportado
   - **GitHub URL:** https://github.com/seu-user/amd-hybrid-router
   - **Application URL:** (deixar vazio ou URL do deploy se tiver)

**Deadline:** Jul 11, 1:00 PM BST (≈ 9:00 AM BRT)

---

### ⬜ Bônus: Gemma $1k Pool

Para concorrer ao prêmio "Best Use of Gemma Models" ($1k extra no Track 1):

1. Router já suporta `gemma-3-27b-it` como modelo disponível
2. No README/video mencionar explicitamente: "Uses Gemma via Fireworks API"
3. No eval, incluir pelo menos 1 task rodando com Gemma

```bash
router run "explain AI ethics" --model gemma-3-27b-it
```

---

## Resumo do Que FALTA

| Item | Tempo estimado | Depende de |
|------|---------------|------------|
| 🔑 Fireworks API Key | 5 min | Conta Fireworks |
| 📊 Accuracy eval | 10 min | API Key |
| 🐳 Testar Docker | 15 min | API Key |
| 📤 Push GitHub | 5 min | — |
| 🎥 Gravar demo | 30 min | — |
| 📝 Slides | 20 min | — |
| 🚀 Submeter | 10 min | Tudo acima |
| **Total** | **~1h30** | |

**Dica:** Fazer tudo em sequência. Se travar na API Key, pedir ajuda no Discord do hackathon.
