# 🎬 Roteiro Video Demo — AMD Hackathon Act II Track 1

**Duração total:** 2:30 — 3:00
**Forma:** Sua voz gravando, mostrando tela (OBS Studio)
**Tom:** Direto, confiante, sem enrolação. Mostrar que funciona.

---

## Setup antes de gravar

1. Terminal aberto no projeto (`/mnt/data/amd-hybrid-router`)
2. Server rodando (tmux session `amd-router`)
3. Playground aberto no navegador (`http://localhost:8999/playground`)
4. Dashboard aberto em outra aba (`http://localhost:8999/`)
5. OBS Studio configurado pra capturar tela (1080p60)

---

## [0:00 - 0:10] ABERTURA — Contexto

**Tela:** Terminal vazio

**Roteiro:**
> "Every AI app today faces the same problem: choosing between cheap models and good models. You either pay too much, or get bad answers. I built a router that solves this — it picks the cheapest Fireworks model that can still answer accurately, task by task."

---

## [0:10 - 0:30] ARQUITETURA — Slide ou terminal

**Tela:** Abra um diagrama simples (pode ser ASCII no terminal, ou um slide rápido) mostrando:

```
Prompt → Complexity Classifier → Model Selector → Fireworks API
                ↓                        ↓
           simple → glm-5p1          $0.30/M tok
           medium → gpt-oss-120b     $0.50/M tok
           complex → deepseek-v4     $1.20/M tok
```

**Roteiro:**
> "The architecture is simple. Every prompt goes through a complexity classifier — no LLM calls needed, just keyword matching and token estimation. Based on complexity, it routes to the cheapest adequate model: simple questions go to glm-5p1 at 30 cents per million tokens, code tasks to gpt-oss-120b at 50 cents, and hard reasoning to deepseek-v4-pro at a dollar-twenty. If the selected model fails, it falls back to the next cheapest."

---

## [0:30 - 1:00] DEMO CLI — Mostrar router em ação

**Tela:** Terminal

Comandos pra executar em sequência durante a gravação:

```bash
# Mostrar modelos disponíveis
router models

# Prompt simples
router run "say hello in 2 words"

# Prompt de código (medium)
router run "write a python function to reverse a string"

# Prompt complexo (complex)
router run "implement a balanced binary search tree in Python"
```

**Roteiro:**
> "Let me show it working. First — the model catalog. Six models from Fireworks AI, each with different costs.
> Now, a simple question — 'say hello'. It routes to glm-5p1, the cheapest. Cost: less than a thousandth of a cent. Latency: 3 seconds.
> A code task — 'write a reverse function'. Routes to gpt-oss-120b. The function it generates works, and it cost a fraction of a cent.
> And for hard reasoning — 'implement a BST'. This one goes to deepseek-v4-pro. It builds a complete implementation with insertion, deletion, and traversal. Still less than a hundredth of a cent."

---

## [1:00 - 1:30] DEMO PLAYGROUND — Mostrar a interface

**Tela:** Navegador com playground (`localhost:8999/playground`)

Digitar na caixa de prompt: `compare REST vs GraphQL for a real-time chat app`

**Roteiro:**
> "The playground makes it visual. I type a prompt, hit Route, and instantly see: complexity is classified as 'complex', it chose deepseek-v4-pro, and it cost this much. The comparison table below shows — if I had used glm-5p1 instead, it would have been cheaper, but probably less accurate. That's the trade-off the router makes for you."

Mostrar o resultado do playground com a tabela de custo comparativo.

---

## [1:30 - 2:00] DEMO DASHBOARD — Métricas em tempo real

**Tela:** Dashboard (`localhost:8999/`)

**Roteiro:**
> "The dashboard tracks everything in real time. Total requests, success rate, average latency, total tokens consumed. Provider breakdown shows how many requests went to each model. You can see which model is performing better for which type of task. And there's a Prometheus endpoint for Grafana integration."

---

## [2:00 - 2:15] DOCKER + GITHUB — Deployabilidade

**Tela:** Terminal

```bash
# Mostrar Docker
docker build -f Dockerfile.scoring -t router .
docker run --rm -p 8080:8000 router

# Mostrar GitHub
gh repo view ismaeldouglasdev/amd-hybrid-router
```

**Roteiro:**
> "Everything is containerized — the scoring image is lean, no local model dependencies, ready for the standardized test environment. The GitHub repo is public with full setup instructions."

---

## [2:15 - 2:30] FECHAMENTO — Impacto + call to action

**Tela:** Terminal ou slide

**Roteiro:**
> "The result: a routing agent that picks the cheapest sufficient model per task, tracks every decision, and scales to millions of requests. Total cost for 10,000 requests: about 13 cents. The smartest model wins — not the most expensive one. This is the AMD Hackathon Track 1 submission. Thanks."

---

## 🎙️ Dicas de gravação

- **Fale pausado, claro** — não corra, juiz assiste rápido mas precisa entender
- **Mostre o que tá falando** — quando falar "3 seconds", mostre a latência na tela
- **Não leia o roteiro** — decore os pontos, fale natural. Repetir até ficar fluido
- **Grave em 1-2 takes** — não precisa ser perfeito, autenticidade > produção

## 🛠️ Setup OBS

```
Áudio: mic desktop + capture window
Vídeo: Screen Capture (Linux) → 1920x1080
Output: H.264, 60fps, 5000 kbps
Formato: MP4
```

## ⏱️ Checklist antes de gravar

- [ ] Server rodando no tmux
- [ ] Playground testado com 3 prompts (functionando)
- [ ] Dashboard populado com dados
- [ ] Docker build testado
- [ ] GitHub repo atualizado
