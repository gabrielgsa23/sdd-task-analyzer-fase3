"""Módulo TaskAnalyzer: análise em memória de métricas de produtividade de tarefas.

Implementa o contrato definido em ``specs/system_design_document.pdf``. Usa apenas a
biblioteca padrão do Python e não realiza nenhuma operação de persistência.
"""

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Final

logger: Final[logging.Logger] = logging.getLogger(__name__)

PRIORIDADES: Final[tuple[str, ...]] = ("Baixa", "Média", "Alta")
STATUS_PENDENTE: Final[str] = "Pendente"
STATUS_CONCLUIDA: Final[str] = "Concluída"
STATUS_VALIDOS: Final[tuple[str, ...]] = (STATUS_PENDENTE, STATUS_CONCLUIDA)
CAMPOS_OBRIGATORIOS: Final[tuple[str, ...]] = (
    "id",
    "titulo",
    "prioridade",
    "data_criacao",
    "prazo_limite",
    "status",
)
CHAVE_GERAL: Final[str] = "geral"
CASAS_DECIMAIS: Final[int] = 2
SEGUNDOS_POR_HORA: Final[float] = 3600.0


class TaskValidationError(ValueError):
    """Erro de validação de dados de entrada de uma tarefa."""


@dataclass(frozen=True)
class Task:
    """Tarefa validada e normalizada.

    Attributes:
        id: Identificador único da tarefa.
        titulo: Título ou descrição curta.
        prioridade: Uma de ``PRIORIDADES``.
        data_criacao: Data e hora de criação.
        prazo_limite: Data limite para término sem atraso.
        data_conclusao: Data efetiva de término, ou ``None``.
        status: Uma de ``STATUS_VALIDOS``.
    """

    id: int
    titulo: str
    prioridade: str
    data_criacao: datetime
    prazo_limite: datetime
    data_conclusao: datetime | None
    status: str


def _parse_datetime(valor: Any, campo: str, task_id: Any) -> datetime:
    """Converte um valor em ``datetime``, aceitando ``datetime`` ou string ISO 8601.

    Args:
        valor: Valor recebido na entrada.
        campo: Nome do campo, usado na mensagem de erro.
        task_id: Identificador da tarefa, usado na mensagem de erro.

    Returns:
        O valor convertido em ``datetime``.

    Raises:
        TaskValidationError: Se o valor não for ``datetime`` nem string ISO 8601 válida.
    """
    if isinstance(valor, datetime):
        return valor
    if isinstance(valor, str):
        try:
            return datetime.fromisoformat(valor)
        except ValueError as exc:
            raise TaskValidationError(
                f"Tarefa {task_id}: '{campo}' não está em formato ISO 8601 válido: {valor!r}."
            ) from exc
    raise TaskValidationError(
        f"Tarefa {task_id}: '{campo}' deve ser datetime ou string ISO 8601, "
        f"mas recebeu {type(valor).__name__}."
    )


def _validate_required_fields(raw: Mapping[str, Any]) -> None:
    """Garante que todos os campos obrigatórios existam na tarefa.

    Args:
        raw: Tarefa bruta recebida na entrada.

    Raises:
        TaskValidationError: Se algum campo obrigatório estiver ausente.
    """
    faltando = [campo for campo in CAMPOS_OBRIGATORIOS if campo not in raw]
    if faltando:
        raise TaskValidationError(
            f"Tarefa {raw.get('id', '?')}: campos obrigatórios ausentes: {', '.join(faltando)}."
        )


def _validate_enums(raw: Mapping[str, Any]) -> None:
    """Valida os valores permitidos de ``prioridade`` e ``status``.

    Args:
        raw: Tarefa bruta recebida na entrada.

    Raises:
        TaskValidationError: Se ``prioridade`` ou ``status`` tiverem valor não permitido.
    """
    if raw["prioridade"] not in PRIORIDADES:
        raise TaskValidationError(
            f"Tarefa {raw['id']}: prioridade inválida {raw['prioridade']!r}. "
            f"Valores permitidos: {', '.join(PRIORIDADES)}."
        )
    if raw["status"] not in STATUS_VALIDOS:
        raise TaskValidationError(
            f"Tarefa {raw['id']}: status inválido {raw['status']!r}. "
            f"Valores permitidos: {', '.join(STATUS_VALIDOS)}."
        )


def _validate_id(raw: Mapping[str, Any]) -> int:
    """Valida o identificador da tarefa.

    Args:
        raw: Tarefa bruta recebida na entrada.

    Returns:
        O identificador como inteiro.

    Raises:
        TaskValidationError: Se o ``id`` não for um inteiro.
    """
    task_id = raw["id"]
    if isinstance(task_id, bool) or not isinstance(task_id, int):
        raise TaskValidationError(f"Tarefa {task_id!r}: 'id' deve ser um inteiro.")
    return task_id


def _validate_chronology(task: Task) -> None:
    """Valida a coerência temporal e de status de uma tarefa.

    Args:
        task: Tarefa já convertida.

    Raises:
        TaskValidationError: Se houver mistura de datas com e sem fuso horário,
            conclusão anterior à criação, ou tarefa concluída sem ``data_conclusao``.
    """
    datas = [task.data_criacao, task.prazo_limite]
    if task.data_conclusao is not None:
        datas.append(task.data_conclusao)
    if len({data.tzinfo is None for data in datas}) > 1:
        raise TaskValidationError(
            f"Tarefa {task.id}: as datas misturam valores com e sem fuso horário."
        )
    if task.data_conclusao is not None and task.data_conclusao < task.data_criacao:
        raise TaskValidationError(
            f"Tarefa {task.id}: data_conclusao ({task.data_conclusao.isoformat()}) é anterior "
            f"a data_criacao ({task.data_criacao.isoformat()}). Corrija as datas de entrada."
        )
    if task.status == STATUS_CONCLUIDA and task.data_conclusao is None:
        raise TaskValidationError(
            f"Tarefa {task.id}: status 'Concluída' exige data_conclusao preenchida."
        )


def _build_task(raw: Any) -> Task:
    """Valida uma tarefa bruta e a converte em ``Task``.

    Args:
        raw: Tarefa bruta (dicionário) recebida na entrada.

    Returns:
        A tarefa validada.

    Raises:
        TaskValidationError: Se a tarefa violar qualquer regra do contrato.
    """
    if not isinstance(raw, Mapping):
        raise TaskValidationError(
            f"Cada tarefa deve ser um dicionário, mas recebeu {type(raw).__name__}."
        )
    _validate_required_fields(raw)
    task_id = _validate_id(raw)
    _validate_enums(raw)
    conclusao_bruta = raw.get("data_conclusao")
    task = Task(
        id=task_id,
        titulo=str(raw["titulo"]),
        prioridade=raw["prioridade"],
        data_criacao=_parse_datetime(raw["data_criacao"], "data_criacao", task_id),
        prazo_limite=_parse_datetime(raw["prazo_limite"], "prazo_limite", task_id),
        data_conclusao=(
            None
            if conclusao_bruta is None
            else _parse_datetime(conclusao_bruta, "data_conclusao", task_id)
        ),
        status=raw["status"],
    )
    _validate_chronology(task)
    return task


def _build_tasks(tasks: Sequence[Mapping[str, Any]]) -> list[Task]:
    """Valida todas as tarefas da entrada e garante ``id`` único.

    Args:
        tasks: Lista de tarefas brutas.

    Returns:
        Lista de tarefas validadas.

    Raises:
        TaskValidationError: Se a entrada não for lista/tupla, se alguma tarefa
            for inválida ou se houver ``id`` duplicado.
    """
    if not isinstance(tasks, (list, tuple)):
        raise TaskValidationError(
            f"A entrada deve ser uma lista de tarefas, mas recebeu {type(tasks).__name__}."
        )
    validadas = [_build_task(raw) for raw in tasks]
    ids = [task.id for task in validadas]
    duplicados = sorted({task_id for task_id in ids if ids.count(task_id) > 1})
    if duplicados:
        raise TaskValidationError(f"Identificadores de tarefa duplicados: {duplicados}.")
    return validadas


def _horas(delta: timedelta) -> float:
    """Converte um intervalo de tempo em horas.

    Args:
        delta: Intervalo de tempo.

    Returns:
        O intervalo em horas.
    """
    return delta.total_seconds() / SEGUNDOS_POR_HORA


def _media(valores: Sequence[float]) -> float:
    """Calcula a média arredondada, retornando 0.0 para lista vazia.

    Args:
        valores: Valores numéricos.

    Returns:
        A média arredondada ou ``0.0`` se não houver valores.
    """
    if not valores:
        return 0.0
    return round(sum(valores) / len(valores), CASAS_DECIMAIS)


def _percentual(parte: int, total: int) -> float:
    """Calcula um percentual arredondado, retornando 0.0 quando ``total`` é zero.

    Args:
        parte: Quantidade do subconjunto.
        total: Quantidade total.

    Returns:
        O percentual arredondado ou ``0.0`` se ``total`` for zero.
    """
    if total == 0:
        return 0.0
    return round(parte / total * 100, CASAS_DECIMAIS)


def _por_prioridade(tasks: Sequence[Task]) -> dict[str, list[Task]]:
    """Agrupa tarefas por prioridade, incluindo a chave geral.

    Args:
        tasks: Tarefas a agrupar.

    Returns:
        Dicionário com as chaves ``geral``, ``Baixa``, ``Média`` e ``Alta``.
    """
    grupos: dict[str, list[Task]] = {CHAVE_GERAL: list(tasks)}
    for prioridade in PRIORIDADES:
        grupos[prioridade] = [task for task in tasks if task.prioridade == prioridade]
    return grupos


def _tempo_medio_horas(concluidas: Sequence[Task]) -> dict[str, float]:
    """Calcula o tempo médio de conclusão em horas (geral e por prioridade).

    Args:
        concluidas: Tarefas com status ``Concluída``.

    Returns:
        Mapa de chave (geral/prioridade) para tempo médio em horas.
    """
    return {
        chave: _media([_horas(t.data_conclusao - t.data_criacao) for t in grupo])
        for chave, grupo in _por_prioridade(concluidas).items()
    }


def _taxa_atraso(concluidas: Sequence[Task]) -> dict[str, float]:
    """Calcula a taxa de atraso percentual (geral e por prioridade).

    Args:
        concluidas: Tarefas com status ``Concluída``.

    Returns:
        Mapa de chave (geral/prioridade) para percentual de tarefas atrasadas.
    """
    return {
        chave: _percentual(sum(1 for t in grupo if t.data_conclusao > t.prazo_limite), len(grupo))
        for chave, grupo in _por_prioridade(concluidas).items()
    }


def _indicadores_prioridade(tasks: Sequence[Task]) -> dict[str, int]:
    """Conta o total de tarefas por prioridade.

    Args:
        tasks: Todas as tarefas validadas.

    Returns:
        Mapa de prioridade para quantidade de tarefas.
    """
    return {prioridade: sum(1 for t in tasks if t.prioridade == prioridade) for prioridade in PRIORIDADES}


def analyze_tasks(tasks: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Analisa tarefas e retorna métricas de produtividade.

    Tempo médio e taxa de atraso consideram exclusivamente tarefas com status
    ``Concluída``. Categorias sem tarefas concluídas retornam ``0.0``.

    Args:
        tasks: Lista de dicionários com os campos ``id``, ``titulo``, ``prioridade``,
            ``data_criacao``, ``prazo_limite``, ``data_conclusao`` e ``status``.
            As datas podem ser ``datetime`` ou strings ISO 8601.

    Returns:
        Dicionário com ``total_tarefas``, ``total_concluidas``, ``total_pendentes``,
        ``tempo_medio_conclusao_horas``, ``taxa_atraso_percentual`` e
        ``indicadores_prioridade``.

    Raises:
        TaskValidationError: Se a entrada ou alguma tarefa violar o contrato.
    """
    validadas = _build_tasks(tasks)
    concluidas = [t for t in validadas if t.status == STATUS_CONCLUIDA]
    resultado: dict[str, Any] = {
        "total_tarefas": len(validadas),
        "total_concluidas": len(concluidas),
        "total_pendentes": len(validadas) - len(concluidas),
        "tempo_medio_conclusao_horas": _tempo_medio_horas(concluidas),
        "taxa_atraso_percentual": _taxa_atraso(concluidas),
        "indicadores_prioridade": _indicadores_prioridade(validadas),
    }
    logger.info(
        "Análise concluída: %d tarefas (%d concluídas).",
        resultado["total_tarefas"],
        resultado["total_concluidas"],
    )
    return resultado
