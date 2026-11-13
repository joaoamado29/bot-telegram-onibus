from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


SOURCE_URL = "https://tonoponto.com/itinerario-horarios-de-onibus/ce-fortaleza-etufor/"
DB_PATH = "onibus.sqlite3"


@dataclass(frozen=True)
class LinhaOnibus:
    numero: int
    nome: str
    link: str


_HORARIO_RE = re.compile(r"^\s*Hor[áa]rio\s+(\d+)\s+(.+?)\s*$", re.IGNORECASE)


def _normalize_link(href: str, base_url: str) -> str:
    absolute = urljoin(base_url, href)
    parsed = urlparse(absolute)
    # Formato pedido no exemplo: "tonoponto.com/itinerario-.../"
    return f"{parsed.netloc}{parsed.path}"


def parse_horlink(text: str, href: str, base_url: str) -> LinhaOnibus | None:
    """
    Exemplo de entrada:
      text="Horário 855 Bezerra De Menezes / Washington Soares"
      href="/itinerario-horarios-de-onibus/ce-etufor-855-bezerra-de-menezes-washington-soares/"
    """
    match = _HORARIO_RE.match(text or "")
    if not match:
        return None

    numero = int(match.group(1))
    nome = match.group(2).strip()
    link = _normalize_link(href, base_url)
    return LinhaOnibus(numero=numero, nome=nome, link=link)


def fetch_page(url: str) -> str:
    resp = requests.get(
        url,
        timeout=30,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        },
    )
    resp.raise_for_status()
    return resp.text


def extract_linhas(html: str, base_url: str) -> list[LinhaOnibus]:
    soup = BeautifulSoup(html, "html.parser")
    anchors = soup.select("a.horLink")

    linhas: list[LinhaOnibus] = []
    seen: set[int] = set()

    for a in anchors:
        text = a.get_text(" ", strip=True)
        href = a.get("href") or ""
        linha = parse_horlink(text=text, href=href, base_url=base_url)
        if not linha:
            continue
        if linha.numero in seen:
            continue
        seen.add(linha.numero)
        linhas.append(linha)

    return linhas


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS linhas (
            numero INTEGER PRIMARY KEY,
            nome TEXT NOT NULL,
            link TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()


def insert_if_new(conn: sqlite3.Connection, linha: LinhaOnibus) -> bool:
    """
    Retorna True se inseriu; False se já existia (mesmo numero).
    """
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        """
        INSERT OR IGNORE INTO linhas (numero, nome, link, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (linha.numero, linha.nome, linha.link, now),
    )
    conn.commit()
    return cur.rowcount == 1


def upsert_batch(db_path: str, linhas: Iterable[LinhaOnibus]) -> tuple[int, int]:
    inserted = 0
    skipped = 0

    with sqlite3.connect(db_path) as conn:
        ensure_schema(conn)
        for linha in linhas:
            if insert_if_new(conn, linha):
                inserted += 1
            else:
                skipped += 1

    return inserted, skipped


def main() -> None:
    html = fetch_page(SOURCE_URL)
    linhas = extract_linhas(html, base_url=SOURCE_URL)
    inserted, skipped = upsert_batch(DB_PATH, linhas)

    print(f"Encontradas: {len(linhas)}")
    print(f"Inseridas:   {inserted}")
    print(f"Ignoradas:   {skipped}")


if __name__ == "__main__":
    main()

