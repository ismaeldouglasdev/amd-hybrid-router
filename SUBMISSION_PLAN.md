# AMD Hackathon Act II — Track 1: Plano de Entrega

## 📋 Status Atual (07/07)

### O Que Funciona
- Router core: classifier + provider selector + fallback chain
- Provider Ollama local (qwen2.5-coder:1.5b)
- Provider 9Router remote (combo-round-robin)
- CLI: run/bench/optimize/serve
- Métricas in-memory + Prometheus export
- Dashboard web com polling em tempo real
- API: `/v1/route`, `/v1/metrics`, `/v1/health`, `/v1/recent`, `/v1/bench`

### Stress Test
| Teste | Resultado |
|-------|-----------|
| 5 concorrentes (Ollama) | 5/5 ✅ | 9.3s wall | 0.5 req/s |
| 3 reqs 9Router | 10-30s cada | $0/req |
| Custo total | $0.000000 (ambos gratuitos) |

---

## 🚨 Desalinhamento com Track 1

Regras do hackathon:
1. **Só Fireworks AI conta pra pontuação** — Ollama local e 9Router não
2. Router precisa escolher **entre modelos Fireworks** (não local vs remote)
3. **Containerização obrigatória** (Docker)
4. Submissão: GitHub público + README + vídeo + slides

---

## 🎯 Roadmap de Implementação

### Fase 1: Provider Fireworks AI (bloqueante)
Trocar 9Router por Fireworks AI como provider remoto oficial.

```python
class FireworksProvider(BaseProvider):
    default_model = "accounts/fireworks/models/llama-v3p1-8b-instruct"
    allowed_models = [
        "llama-v3p1-8b-instruct",    # cheapest, ~$0.10/M tok
        "qwen2p5-coder-7b-instruct",  # mid, ~$0.20/M tok
        "qwen2p5-coder-32b-instruct", # expensive, ~$0.80/M tok
        "gemma-3-27b-it",             # Gemma bonus pool
    ]
```

Necessário: `FIREWORKS_API_KEY` no env.

### Fase 2: Router Adaptado pra Fireworks
Router atual decide local vs remote. Router novo decide **qual modelo Fireworks** usar baseado em:

- Complexidade da task (já implementado)
- Custo por 1K tokens de cada modelo
- Accuracy esperada (modelo maior = mais acurado, mais caro)

| Task Type | Modelo Fireworks | Custo/M tok | Quando |
|-----------|-----------------|-------------|--------|
| Simple Q&A | llama-v3p1-8b | $0.10 | perguntas curtas, factuais |
| Code gen | qwen2p5-coder-7b | $0.20 | funções pequenas, debug |
| Complex reasoning | qwen2p5-coder-32b | $0.80 | arquitetura, lógica pesada |
| Bonus | gemma-3-27b-it | $0.30 | quando acertar Gemma conta bônus |

### Fase 3: Accuracy Eval
- Auto-validação: executa output contra golden answers
- Só usa modelo mais barato que passa no threshold
- Score final = (1 - accuracy_drop) * cost_savings

### Fase 4: Containerização
```dockerfile
FROM python:3.12-slim
COPY . /app
WORKDIR /app
RUN pip install -e .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Fase 5: Material de Submissão
- README.md completo (setup, arquitetura, decisões, resultados)
- Slide deck (5 slides: problema, solução, arquitetura, resultados, demo)
- Demo video (2-3 min mostrando router em ação)
- GitHub repo público

---

## 💰 Projeção de Custos (Fireworks)

| Cenário | req/dia | Modelo médio | Custo/dia | Custo/mês |
|---------|---------|-------------|-----------|-----------|
| Dev/test | 100 | llama-8b ($0.10) | $0.01 | $0.30 |
| Leve | 1K | 70% llama + 30% qwen-7b | $0.13 | $3.90 |
| Moderado | 10K | mix ponderado | $1.30 | $39.00 |
| Pesado | 100K | mix ponderado | $13.00 | $390.00 |

Com `$50 Fireworks credits` do ADP: ~4 meses de uso moderado grátis.

---

## 🏆 Bônus: Gemma Pool ($1.000 Track 1)

Adicionar `gemma-3-27b-it` como modelo disponível no router. Quando prompt casar com perfil Gemma (raciocínio, multimodal), router prioriza Gemma pra concorrer ao prêmio "Best Use of Gemma Models".

---

## 📐 Arquitetura Final (Proposta)

```
Request → Complexity Classifier → Token Estimator
                                    ↓
                           Provider Selector
                           /      |       \
                     llama8b  qwen7b  qwen32b/gemma
                           \      |       /
                        Fallback Chain
                           ↓
                     Metrics Store
                           ↓
                    Dashboard + Prometheus
```

---

## 📊 O Que Falta vs O Que Tem

| Componente | Tem | Precisa |
|-----------|-----|---------|
| Router classifier | ✅ | 🔄 adaptar thresholds p/ Fireworks |
| Provider Ollama | ✅ | keep for dev | 
| Provider 9Router | ✅ | 🔄 substituir por Fireworks |
| Provider Fireworks | ❌ | criar |
| Accuracy eval | ❌ | criar |
| Docker | ❌ | criar |
| Gemma support | ❌ | adicionar |
| README atualizado | ❌ | reescrever |
| Slide deck | ❌ | criar |
| Demo video | ❌ | gravar |
| GitHub público | ❌ | criar repo e push |
