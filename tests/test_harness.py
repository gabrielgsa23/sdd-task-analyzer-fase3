"""Test Harness do TaskAnalyzer: traduz os cenários de aceite da especificação em testes pytest."""

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.task_analyzer import TaskValidationError, analyze_tasks  # noqa: E402

PRIORIDADES = ("Baixa", "Média", "Alta")


def _tarefa(
    task_id: int,
    prioridade: str,
    criacao: str,
    prazo: str,
    conclusao: str | None,
) -> dict[str, Any]:
    """Cria uma tarefa de teste; ``conclusao`` nulo gera tarefa pendente."""
    return {
        "id": task_id,
        "titulo": f"Tarefa {task_id}",
        "prioridade": prioridade,
        "data_criacao": datetime.fromisoformat(criacao),
        "prazo_limite": datetime.fromisoformat(prazo),
        "data_conclusao": None if conclusao is None else datetime.fromisoformat(conclusao),
        "status": "Pendente" if conclusao is None else "Concluída",
    }


@pytest.fixture
def massa_valida() -> list[dict[str, Any]]:
    """Massa perfeita: 7 tarefas (4 concluídas, 3 pendentes) com resultados calculáveis à mão."""
    return [
        _tarefa(1, "Alta", "2026-03-01T08:00", "2026-03-01T18:00", "2026-03-01T16:00"),  # 8h, no prazo
        _tarefa(2, "Alta", "2026-03-02T08:00", "2026-03-02T12:00", "2026-03-02T20:00"),  # 12h, atrasada
        _tarefa(3, "Média", "2026-03-03T09:00", "2026-03-04T09:00", "2026-03-04T09:00"),  # 24h, no limite
        _tarefa(4, "Baixa", "2026-03-05T10:00", "2026-03-06T10:00", "2026-03-07T10:00"),  # 48h, atrasada
        _tarefa(5, "Média", "2026-03-08T09:00", "2026-03-09T09:00", None),
        _tarefa(6, "Baixa", "2026-03-08T09:00", "2026-03-09T09:00", None),
        _tarefa(7, "Alta", "2026-03-08T09:00", "2026-03-09T09:00", None),
    ]


@pytest.fixture
def massa_so_pendentes() -> list[dict[str, Any]]:
    """Massa apenas com tarefas pendentes."""
    return [
        _tarefa(1, "Alta", "2026-03-01T08:00", "2026-03-02T08:00", None),
        _tarefa(2, "Baixa", "2026-03-01T08:00", "2026-03-02T08:00", None),
    ]


@pytest.fixture
def massa_anomalia_temporal() -> list[dict[str, Any]]:
    """Massa com data de conclusão anterior à data de criação."""
    return [_tarefa(1, "Alta", "2026-03-02T08:00", "2026-03-03T08:00", "2026-03-01T08:00")]


# --------------------------- Cenário 1: sucesso ---------------------------


def test_cenario1_totais(massa_valida: list[dict[str, Any]]) -> None:
    resultado = analyze_tasks(massa_valida)
    assert resultado["total_tarefas"] == 7
    assert resultado["total_concluidas"] == 4
    assert resultado["total_pendentes"] == 3


def test_cenario1_tempo_medio_conclusao_horas(massa_valida: list[dict[str, Any]]) -> None:
    tempo = analyze_tasks(massa_valida)["tempo_medio_conclusao_horas"]
    assert tempo == {"geral": 23.0, "Baixa": 48.0, "Média": 24.0, "Alta": 10.0}


def test_cenario1_taxa_atraso_percentual(massa_valida: list[dict[str, Any]]) -> None:
    taxa = analyze_tasks(massa_valida)["taxa_atraso_percentual"]
    assert taxa == {"geral": 50.0, "Baixa": 100.0, "Média": 0.0, "Alta": 50.0}


def test_cenario1_indicadores_por_prioridade(massa_valida: list[dict[str, Any]]) -> None:
    indicadores = analyze_tasks(massa_valida)["indicadores_prioridade"]
    assert indicadores == {"Baixa": 2, "Média": 2, "Alta": 3}


def test_concluir_exatamente_no_prazo_nao_e_atraso() -> None:
    tarefas = [_tarefa(1, "Média", "2026-03-01T08:00", "2026-03-02T08:00", "2026-03-02T08:00")]
    assert analyze_tasks(tarefas)["taxa_atraso_percentual"]["geral"] == 0.0


def test_aceita_datas_em_string_iso_8601() -> None:
    tarefas = [
        {
            "id": 1,
            "titulo": "ISO",
            "prioridade": "Alta",
            "data_criacao": "2026-03-01T08:00:00",
            "prazo_limite": "2026-03-01T18:00:00",
            "data_conclusao": "2026-03-01T10:00:00",
            "status": "Concluída",
        }
    ]
    assert analyze_tasks(tarefas)["tempo_medio_conclusao_horas"]["geral"] == 2.0


def test_aceita_datas_com_fuso_horario() -> None:
    tarefa = _tarefa(1, "Baixa", "2026-03-01T08:00", "2026-03-02T08:00", "2026-03-01T20:00")
    for campo in ("data_criacao", "prazo_limite", "data_conclusao"):
        tarefa[campo] = tarefa[campo].replace(tzinfo=timezone.utc)
    assert analyze_tasks([tarefa])["tempo_medio_conclusao_horas"]["Baixa"] == 12.0


def test_nao_altera_a_entrada(massa_valida: list[dict[str, Any]]) -> None:
    copia = [dict(tarefa) for tarefa in massa_valida]
    analyze_tasks(massa_valida)
    assert massa_valida == copia


# --------------------- Cenário 2: erro de validação -----------------------


def test_cenario2_conclusao_anterior_a_criacao(
    massa_anomalia_temporal: list[dict[str, Any]],
) -> None:
    with pytest.raises(TaskValidationError, match="anterior"):
        analyze_tasks(massa_anomalia_temporal)


def test_task_validation_error_e_um_value_error() -> None:
    assert issubclass(TaskValidationError, ValueError)


def test_cenario2_anomalia_no_meio_de_massa_valida(massa_valida: list[dict[str, Any]]) -> None:
    massa_valida[3]["data_conclusao"] = datetime.fromisoformat("2026-03-01T00:00")
    with pytest.raises(TaskValidationError, match="Tarefa 4"):
        analyze_tasks(massa_valida)


@pytest.mark.parametrize(
    ("campo", "valor", "trecho"),
    [
        ("prioridade", "Urgente", "prioridade inválida"),
        ("status", "Cancelada", "status inválido"),
        ("data_criacao", "não-é-data", "ISO 8601"),
        ("prazo_limite", 12345, "datetime ou string ISO 8601"),
        ("id", "abc", "inteiro"),
    ],
)
def test_cenario2_campos_invalidos(
    massa_valida: list[dict[str, Any]], campo: str, valor: Any, trecho: str
) -> None:
    massa_valida[0][campo] = valor
    with pytest.raises(TaskValidationError, match=trecho):
        analyze_tasks(massa_valida)


def test_cenario2_campo_obrigatorio_ausente(massa_valida: list[dict[str, Any]]) -> None:
    del massa_valida[0]["prazo_limite"]
    with pytest.raises(TaskValidationError, match="prazo_limite"):
        analyze_tasks(massa_valida)


def test_cenario2_concluida_sem_data_conclusao(massa_valida: list[dict[str, Any]]) -> None:
    massa_valida[0]["data_conclusao"] = None
    with pytest.raises(TaskValidationError, match="exige data_conclusao"):
        analyze_tasks(massa_valida)


def test_cenario2_ids_duplicados(massa_valida: list[dict[str, Any]]) -> None:
    massa_valida[1]["id"] = 1
    with pytest.raises(TaskValidationError, match="duplicados"):
        analyze_tasks(massa_valida)


def test_cenario2_datas_com_e_sem_fuso(massa_valida: list[dict[str, Any]]) -> None:
    massa_valida[0]["data_criacao"] = massa_valida[0]["data_criacao"].replace(tzinfo=timezone.utc)
    with pytest.raises(TaskValidationError, match="fuso horário"):
        analyze_tasks(massa_valida)


@pytest.mark.parametrize("entrada", [None, "texto", 42, {"id": 1}])
def test_cenario2_entrada_que_nao_e_lista(entrada: Any) -> None:
    with pytest.raises(TaskValidationError, match="lista de tarefas"):
        analyze_tasks(entrada)


def test_cenario2_item_que_nao_e_dicionario() -> None:
    with pytest.raises(TaskValidationError, match="dicionário"):
        analyze_tasks(["tarefa"])


# ------------------------ Cenário 3: casos de borda -----------------------


def _assert_tudo_zerado(resultado: dict[str, Any]) -> None:
    for chave in ("tempo_medio_conclusao_horas", "taxa_atraso_percentual"):
        assert resultado[chave] == {"geral": 0.0, "Baixa": 0.0, "Média": 0.0, "Alta": 0.0}


def test_borda_entrada_vazia_retorna_zeros() -> None:
    resultado = analyze_tasks([])
    assert resultado["total_tarefas"] == 0
    assert resultado["total_concluidas"] == 0
    assert resultado["total_pendentes"] == 0
    assert resultado["indicadores_prioridade"] == {"Baixa": 0, "Média": 0, "Alta": 0}
    _assert_tudo_zerado(resultado)


def test_borda_apenas_pendentes_retorna_zeros(massa_so_pendentes: list[dict[str, Any]]) -> None:
    resultado = analyze_tasks(massa_so_pendentes)
    assert resultado["total_tarefas"] == 2
    assert resultado["total_concluidas"] == 0
    assert resultado["total_pendentes"] == 2
    assert resultado["indicadores_prioridade"] == {"Baixa": 1, "Média": 0, "Alta": 1}
    _assert_tudo_zerado(resultado)


def test_borda_prioridade_sem_concluidas_retorna_zero() -> None:
    tarefas = [_tarefa(1, "Alta", "2026-03-01T08:00", "2026-03-01T12:00", "2026-03-01T16:00")]
    resultado = analyze_tasks(tarefas)
    assert resultado["tempo_medio_conclusao_horas"] == {
        "geral": 8.0,
        "Baixa": 0.0,
        "Média": 0.0,
        "Alta": 8.0,
    }
    assert resultado["taxa_atraso_percentual"]["geral"] == 100.0
    assert resultado["taxa_atraso_percentual"]["Baixa"] == 0.0


def test_borda_aceita_tupla_de_tarefas(massa_so_pendentes: list[dict[str, Any]]) -> None:
    assert analyze_tasks(tuple(massa_so_pendentes))["total_tarefas"] == 2
