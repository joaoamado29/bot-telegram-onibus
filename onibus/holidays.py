"""Catálogo local de feriados civis aplicáveis à operação de ônibus em Fortaleza."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Feriado:
    nome: str
    jurisdicao: str
    regra: str
    fonte: str
    ano: int | None = None


DATA_MAGNA_CEARA = Feriado(
    nome="Data Magna do Ceará",
    jurisdicao="Ceará",
    regra="25 de março, recorrente",
    fonte="Emenda Constitucional estadual 73/2011",
)


def feriados_em(data: date) -> tuple[Feriado, ...]:
    """Retorna os feriados locais reconhecidos para a data, sem acesso à rede."""
    if not isinstance(data, date):
        raise TypeError("data deve ser datetime.date")
    if data.month == 3 and data.day == 25:
        return (DATA_MAGNA_CEARA,)
    return ()
