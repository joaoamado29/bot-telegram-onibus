from __future__ import annotations

import sqlite3
import unicodedata
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from onibus.core import conectar


@dataclass(frozen=True)
class PaginaSugestoes:
    """
    O que faz: Armazena o lote atual de sugestões de linhas e o próximo offset de paginação.
    Por que foi feito assim: Permite responder à busca inline do Telegram entregando 10 itens por vez,
    indicando se há mais resultados para carregar durante a rolagem da lista.
    """

    itens: tuple[sqlite3.Row, ...]
    next_offset: str


def normalizar_busca(texto: str) -> str:
    """
    O que faz: Remove acentos e converte o texto para minúsculas usando decomposição Unicode NFKD.
    Por que foi feito assim: Conforme regra D-04, garante que termos digitados como 'joao' encontrem
    'São João', e 'papicu' encontre 'Papicu', tornando a pesquisa rápida e flexível.
    """
    decomposto = unicodedata.normalize("NFKD", texto)
    sem_marcas = "".join(ch for ch in decomposto if unicodedata.category(ch) != "Mn")
    return sem_marcas.casefold().strip()


def buscar_sugestoes(db_path: str | Path, termo: str, offset: int | str, limit: int = 10) -> PaginaSugestoes:
    """
    O que faz: Busca linhas de ônibus no banco que atendem ao número ou nome pesquisado,
    retornando apenas linhas que já possuem pontos de parada cadastrados.
    Por que foi feito assim: Garante que os resultados inline sejam sempre consultáveis pelo passageiro.
    Utiliza paginação controlada (limit + 1) para descobrir se existe uma próxima página de rolagem.
    """
    try:
        offset_int = int(offset)
        if offset_int < 0 or offset_int > 100000:
            return PaginaSugestoes((), "")
    except (ValueError, TypeError):
        return PaginaSugestoes((), "")

    if not 1 <= limit <= 50:
        limit = 10

    termo_limpo = normalizar_busca(termo)

    with closing(conectar(db_path)) as conn:
        # Registra a função de normalização no SQLite para permitir buscas sem acento no banco
        conn.create_function("normalizar_texto", 1, normalizar_busca)

        sql = """
            SELECT l.numero, l.nome, l.link, p.revisao
            FROM linhas l
            JOIN pontos p ON p.numero = l.numero
            WHERE (? = '' OR instr(CAST(l.numero AS TEXT), ?) > 0 OR instr(normalizar_texto(l.nome), ?) > 0)
            ORDER BY l.numero
            LIMIT ? OFFSET ?
        """
        # Buscamos limit + 1 para detectar com precisão se ainda existem itens na próxima página
        rows = conn.execute(sql, (termo_limpo, termo_limpo, termo_limpo, limit + 1, offset_int)).fetchall()

    if len(rows) > limit:
        return PaginaSugestoes(tuple(rows[:limit]), str(offset_int + limit))
    return PaginaSugestoes(tuple(rows), "")
