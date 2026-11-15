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
    fonte="https://www2.al.ce.gov.br/legislativo/tramit2011/ec73.htm",
)


_LEI_662 = "https://www2.camara.leg.br/legin/fed/lei/1940-1949/lei-662-6-abril-1949-347136-normaatualizada-pl.html"
_LEI_MUNICIPAL = "https://legislacao.pgm.fortaleza.ce.gov.br/images/6/6d/Lei8796-03.pdf"

# Lei 662/1949, art. 1º, na redação da Lei 10.607/2002.
_FERIADOS_FIXOS = (
    (1, 1, Feriado("Confraternização Universal", "Brasil", "1 de janeiro, recorrente", _LEI_662)),
    (4, 21, Feriado("Tiradentes", "Brasil", "21 de abril, recorrente", _LEI_662)),
    (5, 1, Feriado("Dia do Trabalho", "Brasil", "1 de maio, recorrente", _LEI_662)),
    (9, 7, Feriado("Independência do Brasil", "Brasil", "7 de setembro, recorrente", _LEI_662)),
    (10, 12, Feriado("Nossa Senhora Aparecida", "Brasil", "12 de outubro, recorrente",
                     "https://www.planalto.gov.br/ccivil_03/leis/l6802.htm")),
    (11, 2, Feriado("Finados", "Brasil", "2 de novembro, recorrente", _LEI_662)),
    (11, 15, Feriado("Proclamação da República", "Brasil", "15 de novembro, recorrente", _LEI_662)),
    (11, 20, Feriado("Dia Nacional de Zumbi e da Consciência Negra", "Brasil",
                     "20 de novembro, recorrente (Lei 14.759/2023)",
                     "https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2023/lei/l14759.htm")),
    (12, 25, Feriado("Natal", "Brasil", "25 de dezembro, recorrente", _LEI_662)),
    (3, 25, DATA_MAGNA_CEARA),
    (3, 19, Feriado("Dia de São José", "Fortaleza", "19 de março, recorrente", _LEI_MUNICIPAL)),
    (8, 15, Feriado("Nossa Senhora da Assunção", "Fortaleza", "15 de agosto, recorrente", _LEI_MUNICIPAL)),
)

_FERIADOS_MOVEIS = (
    (-2, Feriado("Sexta-feira da Paixão", "Fortaleza", "Páscoa menos 2 dias, recorrente", _LEI_MUNICIPAL)),
    (60, Feriado("Corpus Christi", "Fortaleza", "Páscoa mais 60 dias, recorrente", _LEI_MUNICIPAL)),
)

# Lei 11.649/2026: exceção exclusiva de 2026; aniversário não é regra anual.
_EXCECOES_ANUAIS = (
    (date(2026, 4, 13), Feriado(
        "Aniversário da Cidade de Fortaleza", "Fortaleza", "13 de abril de 2026, excepcional",
        "https://sapl.fortaleza.ce.leg.br/norma/14390", ano=2026,
    )),
)


def _pascoa(ano: int) -> date:
    """Calcula a Páscoa gregoriana pelo algoritmo aritmético de Meeus/Jones/Butcher."""
    a = ano % 19
    b, c = divmod(ano, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes, dia = divmod(h + l - 7 * m + 114, 31)
    return date(ano, mes, dia + 1)


def feriados_em(data: date) -> tuple[Feriado, ...]:
    """Retorna os feriados locais reconhecidos para a data, sem acesso à rede."""
    if not isinstance(data, date):
        raise TypeError("data deve ser datetime.date")
    fixos = tuple(feriado for mes, dia, feriado in _FERIADOS_FIXOS
                  if (data.month, data.day) == (mes, dia))
    pascoa = _pascoa(data.year)
    moveis = tuple(feriado for dias, feriado in _FERIADOS_MOVEIS
                   if (data - pascoa).days == dias)
    excepcionais = tuple(feriado for dia, feriado in _EXCECOES_ANUAIS if data == dia)
    return fixos + moveis + excepcionais
