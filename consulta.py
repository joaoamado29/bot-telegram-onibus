from __future__ import annotations

import sqlite3
from dataclasses import dataclass

DB_PATH = "onibus.sqlite3"


@dataclass(frozen=True)
class LinhaOnibus:
    numero: int
    nome: str
    link: str
    created_at: str


def listar_linhas(db_path: str = DB_PATH) -> list[LinhaOnibus]:
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT numero, nome, link, created_at
            FROM linhas
            ORDER BY numero
            """
        ).fetchall()

    return [
        LinhaOnibus(numero=row[0], nome=row[1], link=row[2], created_at=row[3])
        for row in rows
    ]


def formatar_linha(linha: LinhaOnibus) -> str:
    return (
        f"{linha.numero}: {linha.nome}\n"
        f"  link: {linha.link}\n"
        f"  criado em: {linha.created_at}"
    )


def main() -> None:
    linhas = listar_linhas()

    if not linhas:
        print("Nenhuma linha encontrada no banco de dados.")
        return

    print(f"Total de linhas: {len(linhas)}\n")

    for linha in linhas:
        print(formatar_linha(linha))
        print()


if __name__ == "__main__":
    main()
