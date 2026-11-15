from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Callable
from urllib.parse import urljoin, urlparse
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from onibus.holidays import feriados_em
from scraping import LinhaOnibus, ensure_schema

BRT = ZoneInfo("America/Sao_Paulo")
_TIME_RE = re.compile(r"(?:[01]\d|2[0-3]):[0-5]\d")
_CALENDARIOS = {"Dias úteis": "uteis", "Sábados": "sabados", "Domingos e feriados": "domingos_feriados"}


@dataclass(frozen=True)
class PontoHorario:
    endereco: str
    calendarios: dict[str, tuple[str, ...]]


@dataclass(frozen=True)
class HorariosLinha:
    numero: int
    nome: str
    pontos: tuple[PontoHorario, ...]


@dataclass(frozen=True)
class ConsultaSaidas:
    data: date
    calendario: str
    endereco: str
    horarios: tuple[str, ...]
    status: str
    numero: int = 0
    nome: str = ""
    feriados: tuple[str, ...] = ()
    todos_horarios: tuple[str, ...] = ()


def _validar_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "tonoponto.com" or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError("Link de origem não permitido")
    return url


def _fetch_page(url: str) -> str:
    """Valida cada redirecionamento antes de acessar a próxima origem."""
    for _ in range(6):
        _validar_url(url)
        response = requests.get(url, timeout=30, allow_redirects=False, headers={"User-Agent": "Mozilla/5.0"})
        try:
            if response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get("Location")
                if not location:
                    raise ValueError("Redirecionamento sem destino")
                url = urljoin(url, location)
                continue
            response.raise_for_status()
            return response.text
        finally:
            response.close()
    raise ValueError("Limite de redirecionamentos excedido")


def coletar_linha(linha: LinhaOnibus, fetcher: Callable[[str], str] = _fetch_page) -> HorariosLinha:
    """
    O que faz: Baixa a página web de uma linha específica e extrai seus pontos e horários.
    Por que foi feito assim: Centraliza o download e o parsing, permitindo injetar um buscador
    simulado durante testes sem depender de rede.
    """
    url = linha.link if "://" in linha.link else "https://" + linha.link
    return parse_horarios(fetcher(_validar_url(url)), linha.numero, linha.nome)


def parse_horarios(html: str, numero: int, nome: str) -> HorariosLinha:
    """
    O que faz: Lê o HTML de horários, agrupando horários por ponto e por calendário (dias úteis,
    sábados e domingos/feriados).
    Por que foi feito assim: As páginas do Tonoponto organizam horários sob títulos h2 (pontos),
    subtítulos p.title_p (calendários) e listas ul.listaHorarios. Descartamos itens de publicidade
    (li.adInList) e normalizamos cada horário no formato estrito HH:MM.
    """
    soup = BeautifulSoup(html, "html.parser")
    pontos: list[PontoHorario] = []
    endereco: str | None = None
    calendarios: dict[str, tuple[str, ...]] = {}
    calendario: str | None = None
    for element in soup.find_all(["h2", "p", "ul"]):
        if element.name == "h2":
            if endereco is not None and calendarios:
                pontos.append(PontoHorario(endereco, calendarios))
            endereco = element.get_text(" ", strip=True)
            calendarios = {}
            calendario = None
        elif element.name == "p" and "title_p" in element.get("class", []):
            calendario = _CALENDARIOS.get(element.get_text(" ", strip=True))
        elif element.name == "ul" and "listaHorarios" in element.get("class", []) and endereco and calendario:
            if calendario in calendarios:
                raise ValueError("Calendário repetido no mesmo ponto")
            horarios = []
            for item in element.find_all("li", recursive=False):
                value = item.get_text(" ", strip=True)
                if "adInList" not in item.get("class", []) and _TIME_RE.fullmatch(value):
                    horarios.append(value)
            calendarios[calendario] = tuple(sorted(set(horarios)))
    if endereco is not None and calendarios:
        pontos.append(PontoHorario(endereco, calendarios))
    result = HorariosLinha(numero, nome, tuple(pontos))
    _validar_horarios(result)
    return result


def _validar_horarios(horarios: HorariosLinha) -> None:
    """
    O que faz: Valida se a linha possui de 2 a 5 pontos e se os calendários contêm as listas obrigatórias.
    Por que foi feito assim: Garante a integridade dos dados antes de qualquer escrita no banco,
    impedindo que coletas incompletas ou corrompidas substituam os dados válidos anteriores.
    """
    if not 2 <= len(horarios.pontos) <= 5 or not horarios.nome.strip():
        raise ValueError("A linha precisa de dois a cinco pontos")
    calendarios = set().union(*(p.calendarios for p in horarios.pontos))
    if not calendarios or not calendarios.issubset(set(_CALENDARIOS.values())):
        raise ValueError("Calendário ausente ou desconhecido")
    for ponto in horarios.pontos:
        if not ponto.endereco.strip():
            raise ValueError("Endereço vazio")
        for valores in ponto.calendarios.values():
            if not isinstance(valores, (list, tuple)) or any(not isinstance(v, str) or not _TIME_RE.fullmatch(v) for v in valores):
                raise ValueError("Lista de horários inválida")
    for calendario in calendarios:
        if any(not ponto.calendarios.get(calendario) for ponto in horarios.pontos[:2]):
            raise ValueError("As duas primeiras coleções são obrigatórias em cada calendário")


def conectar(db_path: str | Path) -> sqlite3.Connection:
    """
    O que faz: Abre conexão com o banco SQLite e garante que as tabelas 'pontos' e 'horarios' existam.
    Por que foi feito assim: Habilita chaves estrangeiras (PRAGMA foreign_keys = ON) e regras CHECK
    para garantir que nenhum dado órfão ou JSON inválido seja gravado.
    """
    conn = sqlite3.connect(str(db_path), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    ensure_schema(conn)
    conn.execute("""CREATE TABLE IF NOT EXISTS pontos (
        numero INTEGER PRIMARY KEY REFERENCES linhas(numero), nome TEXT NOT NULL,
        ponto1 TEXT NOT NULL, ponto2 TEXT NOT NULL, ponto3 TEXT, ponto4 TEXT, ponto5 TEXT,
        revisao INTEGER NOT NULL, updated_at TEXT NOT NULL
    )""")

    checks = []
    
    for posicao in range(1, 6):
        coluna = f"horario_ponto{posicao}"
        check = f"json_valid({coluna}) AND json_type({coluna}) = 'array'"
        if posicao <= 2:
            checks.append(f"{coluna} TEXT NOT NULL CHECK ({check} AND json_array_length({coluna}) > 0)")
        else:
            checks.append(f"{coluna} TEXT CHECK ({coluna} IS NULL OR ({check}))")
    conn.execute(f"""CREATE TABLE IF NOT EXISTS horarios (
        numero INTEGER NOT NULL REFERENCES pontos(numero), nome TEXT NOT NULL,
        calendario TEXT NOT NULL, {', '.join(checks)}, PRIMARY KEY (numero, calendario)
    )""")
    conn.commit()
    return conn


def publicar_linha(conn: sqlite3.Connection, horarios: HorariosLinha) -> None:
    """
    O que faz: Salva ou atualiza todos os pontos e horários de uma linha no banco de forma atômica.
    Por que foi feito assim: Conforme regra D-08, uma nova publicação substitui os horários antigos
    e remove calendários que não existem mais. A operação ocorre dentro de uma transação (with conn)
    para reverter tudo caso ocorra qualquer erro no meio do processo.
    """
    _validar_horarios(horarios)
    enderecos = [p.endereco for p in horarios.pontos] + [None] * (5 - len(horarios.pontos))
    calendarios = sorted(set().union(*(p.calendarios for p in horarios.pontos)))
    with conn:
        conn.execute("""INSERT INTO pontos (numero,nome,ponto1,ponto2,ponto3,ponto4,ponto5,revisao,updated_at)
            VALUES (?,?,?,?,?,?,?,1,?) ON CONFLICT(numero) DO UPDATE SET
            nome=excluded.nome,ponto1=excluded.ponto1,ponto2=excluded.ponto2,ponto3=excluded.ponto3,
            ponto4=excluded.ponto4,ponto5=excluded.ponto5,revisao=pontos.revisao+1,updated_at=excluded.updated_at""",
            (horarios.numero, horarios.nome, *enderecos, datetime.now(timezone.utc).isoformat()))
        conn.execute("DELETE FROM horarios WHERE numero = ?", (horarios.numero,))
        for calendario in calendarios:
            listas = [json.dumps(sorted(set(p.calendarios[calendario]))) if calendario in p.calendarios else None for p in horarios.pontos]
            listas += [None] * (5 - len(listas))
            conn.execute("""INSERT INTO horarios
                (numero,nome,calendario,horario_ponto1,horario_ponto2,horario_ponto3,horario_ponto4,horario_ponto5)
                VALUES (?,?,?,?,?,?,?,?)""", (horarios.numero, horarios.nome, calendario, *listas))


def buscar_linhas(conn: sqlite3.Connection, termo: str, offset: int, limit: int = 10) -> list[sqlite3.Row]:
    """
    O que faz: Busca linhas no banco por número ou nome com suporte a paginação.
    Por que foi feito assim: Permite responder à busca inline do Telegram de forma rápida
    e estável, retornando os resultados ordenados pelo número da linha.
    """
    if not 0 <= offset <= 100000 or not 1 <= limit <= 50:
        raise ValueError("Paginação inválida")
    return conn.execute("""SELECT l.numero,l.nome,l.link,p.revisao FROM linhas l JOIN pontos p ON p.numero=l.numero
        WHERE instr(CAST(l.numero AS TEXT), ?) > 0 OR instr(lower(l.nome),lower(?)) > 0
        ORDER BY l.numero LIMIT ? OFFSET ?""", (termo, termo, limit, offset)).fetchall()


def carregar_pontos(conn: sqlite3.Connection, numero: int) -> sqlite3.Row | None:
    """
    O que faz: Obtém os endereços dos pontos e a revisão atual de uma linha.
    Por que foi feito assim: Usado na renderização dos botões do Telegram e na validação
    de que a mensagem inline ainda é compatível com os dados do banco.
    """
    return conn.execute("SELECT * FROM pontos WHERE numero = ?", (numero,)).fetchone()


def proximas_saidas(conn: sqlite3.Connection, numero: int, ponto: int, agora: datetime) -> ConsultaSaidas:
    """
    O que faz: Retorna até 3 próximas saídas de hoje para o ponto selecionado no fuso de Brasília.
    Por que foi feito assim: Regra D-13: compara o horário atual estritamente com os horários de hoje.
    Se não houver mais saídas hoje, retorna status 'encerrado' sem misturar com saídas de amanhã.
    """
    if ponto not in range(1, 6) or agora.tzinfo is None:
        raise ValueError("Ponto ou relógio inválido")
    local = agora.astimezone(BRT)
    feriados = feriados_em(local.date())
    calendario = (
        "domingos_feriados"
        if feriados
        else "uteis" if local.weekday() < 5 else "sabados" if local.weekday() == 5 else "domingos_feriados"
    )
    nomes_feriados = tuple(feriado.nome for feriado in feriados)
    pontos = carregar_pontos(conn, numero)
    endereco = pontos[f"ponto{ponto}"] if pontos else None
    nome_linha = pontos["nome"] if pontos else ""
    row = conn.execute(f"SELECT horario_ponto{ponto} FROM horarios WHERE numero=? AND calendario=?", (numero, calendario)).fetchone()
    if not endereco or row is None or row[0] is None:
        return ConsultaSaidas(
            local.date(), calendario, endereco or "", (), "indisponivel",
            numero=numero, nome=nome_linha, feriados=nomes_feriados,
        )
    try:
        publicados = tuple(sorted(set(json.loads(row[0]))))
    except (json.JSONDecodeError, TypeError):
        publicados = ()
    if not publicados:
        return ConsultaSaidas(
            local.date(), calendario, endereco, (), "indisponivel",
            numero=numero, nome=nome_linha, feriados=nomes_feriados,
        )
    futuros = tuple(
        valor for valor in publicados
        if datetime.combine(local.date(), time.fromisoformat(valor), tzinfo=BRT) > local
    )[:3]
    return ConsultaSaidas(
        local.date(), calendario, endereco, futuros, "disponivel" if futuros else "encerrado",
        numero=numero, nome=nome_linha, feriados=nomes_feriados, todos_horarios=publicados,
    )
