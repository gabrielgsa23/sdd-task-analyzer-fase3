# sdd-task-analyzer

**Autor:** Gabriel Gonçalves Sá — RA 22352853 — gabriel.gsa@sempreceub.com

![CI](https://github.com/gabrielgsa23/sdd-task-analyzer-fase3/actions/workflows/ci.yml/badge.svg)

**TaskAnalyzer** — projeto cumulativo do Bootcamp III (Spec-Driven Development com IA).
Analisa tarefas em memória e calcula tempo médio de conclusão, taxa de atraso e totais por prioridade.

- **Fase 1:** especificação SDD e regras de governança de IA (`specs/`, `CONTEXT_RULES.md`).
- **Fase 2:** código gerado via IA (`src/task_analyzer.py`) validado por Test Harness (`tests/test_harness.py`).
- **Fase 3:** CI/CD (GitHub Actions), containerização (Docker) e relatório de governança.

## Estrutura

```
sdd-task-analyzer/
├── .github/workflows/ci.yml   # CI/CD (GitHub Actions)
├── Dockerfile                 # empacotamento (python:3.11-slim)
├── docker-compose.yml         # orquestração da suíte de testes
├── CONTEXT_RULES.md           # regras de governança para agentes de IA
├── specs/
│   ├── system_design_document.pdf     # especificação SDD (contrato)
│   └── requirements.yaml              # contrato em formato estruturado
├── tests/test_harness.py      # suíte pytest (cenários 1, 2 e bordas)
├── src/task_analyzer.py       # código gerado via IA e homologado por humano
├── requirements.txt
└── README.md
```

## Como executar

Requisito: Python 3.11+.

```bash
pip install -r requirements.txt
pytest tests/test_harness.py -v
```

Com Docker (um único comando, sem instalar nada além do Docker):

```bash
docker compose run --rm tests
```

## Exemplo de uso

```python
from src.task_analyzer import analyze_tasks, TaskValidationError

resultado = analyze_tasks([
    {
        "id": 1,
        "titulo": "Entregar relatório",
        "prioridade": "Alta",
        "data_criacao": "2026-03-01T08:00:00",
        "prazo_limite": "2026-03-01T18:00:00",
        "data_conclusao": "2026-03-01T16:00:00",
        "status": "Concluída",
    }
])
print(resultado["tempo_medio_conclusao_horas"]["geral"])  # 8.0
```

## Fluxo de trabalho

Branch principal `main`; funcionalidades em `feature/*` integradas via Pull Request após
homologação humana (testes 100%, auditoria de contrato, análise estática e bordas).
O histórico de branches e Pull Requests da Fase 2 está em https://github.com/gabrielgsa23/sdd-task-analyzer.

## CI/CD

O workflow roda em push e pull request nas branches `main` e `develop`: Ubuntu, Python 3.11,
instalação via `requirements.txt` e `pytest tests/test_harness.py -v`; em seguida, build da imagem e
execução da mesma suíte dentro do container.
