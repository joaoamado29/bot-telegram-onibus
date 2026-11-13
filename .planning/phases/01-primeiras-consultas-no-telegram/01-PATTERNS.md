# Phase 1: Primeiras consultas no Telegram - Pattern Map

**Mapped:** 2026-11-13
**Files analyzed:** 17 propostas de arquivos/grupos
**Analogs found:** 0 analogias elegíveis em fonte rastreada; dois módulos existentes fornecem referências observadas condicionadas ao baseline.

## Tracked-source Gate

`git ls-files -- scraping.py consulta.py requirements.txt README.md` não retornou caminhos nesta análise. Esses quatro arquivos existem e contêm o produto, mas ainda não estão rastreados no repositório local recém-inicializado. Isso não os transforma em arquivos gerados ou mirrors: são fontes existentes que precisam de baseline explícito durante a execução.

Nenhum caminho de tooling instalado foi usado como analogia. Antes de promover uma referência observada abaixo a uma atribuição executável, o plano deve prever rastrear somente os arquivos do produto necessários e verificar novamente `git ls-files -- <caminho>`. Não usar `git add .`, não versionar o banco operacional, o virtualenv nem cópias instaladas de GSD.

Os nomes do pacote abaixo são sugestões da pesquisa, não arquivos existentes nem decisões de arquitetura já implementadas. O planner pode reduzir módulos preservando as fronteiras.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `bot.py` | controller/config | event-driven | Nenhum elegível | novo; padrão de entrada observado depende de baseline |
| `onibus/__init__.py` | config | import | Nenhum | novo pacote |
| `onibus/config.py` | config | file-I/O/environment | Nenhum elegível | constantes existentes não cobrem ambiente/fuso |
| `onibus/models.py` | model | transform | Nenhum elegível | dataclass observada depende de baseline |
| `onibus/storage.py` | store | CRUD/file-I/O | Nenhum elegível | SQLite observado depende de baseline |
| `onibus/scraping.py` | service | request-response/batch/transform | Nenhum elegível | parsing e HTTP observados dependem de baseline |
| `onibus/schedules.py` | service | transform/request-response | Nenhum | não há seleção temporal |
| `onibus/telegram_handlers.py` | controller | event-driven/request-response | Nenhum | não há handlers Telegram |
| `onibus/refresh.py` | service | event-driven/batch | Nenhum | não há agendador/retry |
| `scraping.py` | controller/service | batch | Nenhum elegível | fonte existente; preservar uso CLI |
| `consulta.py` | controller/store | CRUD/file-I/O | Nenhum elegível | fonte existente; preservar consulta CLI |
| `requirements.txt` | config | dependency resolution | Nenhum elegível | manifesto existente precisa de baseline |
| `README.md` | config/documentation | operação manual | Nenhum elegível | documentação existente precisa de baseline |
| `tests/test_scraping.py` | test | transform | Nenhum | infraestrutura de produto ausente |
| `tests/test_storage.py` | test | CRUD/file-I/O | Nenhum | usar SQLite temporário |
| `tests/test_schedules.py` | test | transform | Nenhum | relógio/data injetados |
| `tests/test_telegram_handlers.py`, `tests/test_refresh.py`, `tests/fixtures/*.html` | test | event-driven/batch | Nenhum | mocks async, fixtures e scheduler fake |

## Pattern Assignments

Não há atribuição incondicional a analogia rastreada. As referências concretas desta seção são **fontes observadas ainda não rastreadas**; o baseline é pré-condição. Não interpretar a ausência de analogia rastreada como autorização para recriar o produto do zero.

### `onibus/models.py` (model, transform)

**Referência observada condicionada:** `scraping.py`, linhas 1–11 e 18–22.

**Imports e registro imutável:**

```python
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
```

```python
@dataclass(frozen=True)
class LinhaOnibus:
    numero: int
    nome: str
    link: str
```

Reutilizar o estilo de anotações, PascalCase e `frozen=True`; importar em cada módulo somente o que utiliza. O registro de `consulta.py`, linhas 9–14, também tem `created_at`: são representações diferentes, não presumir assinaturas idênticas. Definir deliberadamente a representação compartilhada sem perder campos da consulta atual.

### `onibus/scraping.py` (service, request-response/batch/transform)

**Referência observada condicionada:** `scraping.py`, linhas 51–62.

```python
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
```

Manter timeout explícito e erro HTTP observável. Acrescentar validação de URL/host e redirecionamento conforme a pesquisa: o padrão atual não garante isso. Não colocar retry infinito dentro do fetcher.

**Seleção e transformação**, linhas 65–83:

```python
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
```

Reutilizar funções puras de transformação e entrada HTML explícita. O parser detalhado é novo: seguir blocos de ponto/calendário e `ul.listaHorarios`, não todos os `li` indiscriminadamente. Preservar as listas independentes 26/27, não aplicar `zip` para formar supostas viagens. Falhas estruturais que tornem as duas coleções obrigatórias vazias precisam rejeitar a atualização daquela linha, não parecer importação bem-sucedida com zero resultados.

### `onibus/storage.py` (store, CRUD/file-I/O)

**Referência observada condicionada:** `scraping.py`, linhas 100–113.

```python
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
```

Copiar vinculação de valores por parâmetros, SQL com colunas explícitas, anotações e conexão injetada. **Não copiar** `INSERT OR IGNORE` como semântica de atualização dos horários nem `commit()` por item: publicar endereços e todos os calendários válidos da linha na mesma transação, com rollback preservando last-good. Ativar FK antes da transação em cada conexão. Manter o catálogo existente intacto. `NOT NULL` sozinho não impede JSON `[]` e strings vazias: aplicar validação efetiva em código e restrições verificadas no SQLite.

**Leitura e materialização**, `consulta.py`, linhas 17–30:

```python
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
```

Reutilizar `db_path` explícito e seleção de colunas, preservando ordem determinística para paginação. Busca normalizada e paginação são novas capacidades; a consulta atual apenas lista tudo. Nunca interpolar nomes de coluna recebidos de callback; mapear as cinco posições por conjunto fechado.

### `bot.py` e wrappers CLI (controller, event-driven/batch)

**Referência observada condicionada:** `scraping.py`, linhas 131–142.

```python
def main() -> None:
    html = fetch_page(SOURCE_URL)
    linhas = extract_linhas(html, base_url=SOURCE_URL)
    inserted, skipped = upsert_batch(DB_PATH, linhas)

    print(f"Encontradas: {len(linhas)}")
    print(f"Inseridas:   {inserted}")
    print(f"Ignoradas:   {skipped}")


if __name__ == "__main__":
    main()
```

Preservar importação sem efeitos e separar bootstrap de funções de domínio. O bootstrap PTB, handlers async, token em ambiente e ciclo de vida são novos; usar a pesquisa como referência, sem tratar `main()` síncrono atual como analogia de event loop.

## Shared Patterns

### Tipagem, nomes e saída

Fontes observadas: `scraping.py:18-22`, `consulta.py:33-38`. Usar snake_case e domínio em português (`numero`, `nome`, `ponto`), funções anotadas e helpers de apresentação que retornam strings. Conservar nomes originais para exibição; a chave normalizada sem acentos/caixa serve apenas à comparação.

```python
def formatar_linha(linha: LinhaOnibus) -> str:
    return (
        f"{linha.numero}: {linha.nome}\n"
        f"  link: {linha.link}\n"
        f"  criado em: {linha.created_at}"
    )
```

Adaptar o formato de sugestão ao aprovado `123 - Nome`; o formato CLI acima não é requisito visual do bot.

### Erros e transações

Fonte observada: `scraping.py:61` e `consulta.py:18`. Erros HTTP/SQLite hoje propagam. O serviço de coleta novo deve capturar por linha na fronteira de orquestração, mantendo falha observável, rollback e retry limitado; funções de parsing/storage não devem imprimir sucesso nem suprimir erro silenciosamente.

### Banco e fuso

Fonte observada: `scraping.py:14-15`, `consulta.py:6`. Há constantes relativas duplicadas. Resolver caminho consistente no módulo de configuração antes de integrar scheduler e threads. Instantes de consulta em Brasília e relógio injetado são novos, não herdar UTC de `created_at` como regra de consulta de ônibus.

### Autenticação e Telegram

Não há analogia no produto. Configurar token por ambiente sem registrar seu valor. Não introduzir login de passageiro nesta fase. O resultado inline já contém endereços e teclado; callback usa caminho compatível com `inline_message_id`, sem depender de `chosen_inline_result`, `effective_chat.id` ou `query.message` presentes. Estas orientações vêm de `01-RESEARCH.md`, não de um handler existente.

## No Analog Found

| File / capability | Role | Data Flow | Reason |
|-------------------|------|-----------|--------|
| `onibus/telegram_handlers.py` | controller | event-driven | Nenhuma integração Telegram existente |
| `onibus/refresh.py` | service | event-driven/batch | Sem scheduler, retry ou exclusão de coleta |
| `onibus/schedules.py` | service | transform | Sem seleção por data/calendário/fuso |
| `onibus/config.py` | config | environment/file-I/O | Sem token em ambiente ou caminho estável compartilhado |
| Testes e fixtures propostos | test | integração/async | Nenhuma suíte do produto; testes do GSD não são analogia do aplicativo |
| `onibus/__init__.py` | config | import | Código atual é composto por módulos de raiz |

Usar as APIs e exemplos oficiais citados em `01-RESEARCH.md` para capacidades sem analogia, com testes comportamentais que cubram inline sem `message`, paginação dez, busca sem acentos, calendário ausente, minuto exato, FK, coleções vazias, rollback, domingo 01h e retry sem superposição.

## Metadata

**Analog search scope:** arquivos de produto na raiz e caminhos novos propostos pela pesquisa; nenhuma inspeção de segredos, banco operacional ou virtualenv.
**Files scanned:** quatro fontes/documentos de produto (`scraping.py`, `consulta.py`, `requirements.txt`, `README.md`), além dos três arquivos obrigatórios de contexto.
**Project skills:** diretórios locais contêm o catálogo de comandos GSD; não foi identificado um skill de convenções específico do produto. GSD é infraestrutura de workflow, não biblioteca de implementação do bot.
**Pattern extraction date:** 2026-11-13.
**Source baseline prerequisite:** confirmar o rastreamento dos arquivos existentes na execução antes de afirmar uma atribuição elegível de analogia.
