<!-- GSD:project-start source:PROJECT.md -->

## Project

**Bot Telegram Ônibus**

Um bot de Telegram para consultar horários de ônibus a partir dos dados do Tonoponto. O usuário inicia com `/start`, escolhe a linha e depois um endereço de ponto daquela linha para consultar as próximas três saídas e receber lembretes.

**Core Value:** Permitir que o passageiro encontre os próximos horários do ponto escolhido e receba avisos antes da saída selecionada, conforme o horário de Brasília e o calendário de operação.

### Constraints

- **Base existente**: Evoluir o coletor Python e o banco SQLite preservando as linhas já armazenadas.
- **Integridade**: `horario_ponto1` e `horario_ponto2` não podem ficar vazios; as tabelas de horários e endereços devem ter relação por chave estrangeira.
- **Tempo**: Consultas e alertas devem usar o horário de Brasília, com calendário automático por data.
- **Origem dos dados**: Endereços e horários devem vir das páginas referenciadas pelas linhas coletadas.
- **Interface**: A interação do passageiro ocorre pelo Telegram em português, começando pela linha e depois pelo endereço.

<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->

## Technology Stack

## Languages

- Python 3.10+ is the documented minimum in `README.md`; application scripts are `scraping.py` and `consulta.py`.
- Python annotations include `list[...]`, `tuple[...]`, and `LinhaOnibus | None`; both scripts enable postponed annotation evaluation.
- SQL is embedded directly in `scraping.py` and `consulta.py` for schema creation, inserts, and ordered reads.
- Markdown documents usage in `README.md`; no product JavaScript or TypeScript package is detected.

## Runtime

- Local Python virtual environment `.venv/pyvenv.cfg` identifies Python 3.11.9 on Windows.
- `scraping.py` and `consulta.py` are synchronous command-line entry points using `if __name__ == "__main__"`.
- pip installs dependencies from `requirements.txt`, following `README.md`.
- Local installed metadata includes pip 26.1.2 under `.venv/Lib/site-packages/`.
- Lockfile: not detected; `requirements.txt` specifies lower bounds rather than a reproducible resolution.

## Frameworks

- No web framework or bot framework is detected in `requirements.txt`, `scraping.py`, or `consulta.py`.
- Beautiful Soup parses downloaded HTML with Python's built-in `html.parser` in `scraping.py`.
- No application test framework, test files, or test configuration is detected among root product files.
- Tests belonging to installed GSD tooling under `.agents/gsd-core/` or `.codex/gsd-core/` are not product tests.
- No product build step is detected; `README.md` runs `python scraping.py` directly.
- `.agents/` and `.codex/` contain installed GSD agent/workflow tooling; their Node tooling is separate from the Python application runtime.

## Key Dependencies

- `requests>=2.32.0` in `requirements.txt` provides HTTP retrieval in `scraping.py`; local metadata reports 2.34.2.
- `beautifulsoup4>=4.12.0` in `requirements.txt` provides `BeautifulSoup` and CSS selection in `scraping.py`; local metadata reports 4.15.0.
- Standard-library `sqlite3` provides embedded database access in both application scripts, without an ORM.
- Standard-library `dataclasses` defines immutable `LinhaOnibus` records separately in `scraping.py` and `consulta.py`.
- `re`, `urllib.parse`, and `datetime` implement title parsing, URL normalization, and UTC timestamps in `scraping.py`.
- Local dependency metadata under `.venv/Lib/site-packages/` includes urllib3 2.7.0, certifi 2026.6.17, charset-normalizer 3.4.7, idna 3.18, soupsieve 2.8.4, and typing-extensions 4.16.0; these are observed installation versions, not declared pins.

## Configuration

- No environment-variable reads are present in `scraping.py` or `consulta.py`.
- `SOURCE_URL` and `DB_PATH` are module constants in `scraping.py`; `consulta.py` has its own `DB_PATH` constant.
- The database defaults to relative path `onibus.sqlite3`, so process working directory determines its location.
- No root `.env` file is present in the inspected root file listing.
- `requirements.txt` is the product dependency manifest.
- No product `pyproject.toml`, setup configuration, container definition, or executable packaging configuration is detected.

## Platform Requirements

- Python 3.10+ and pip, with virtual-environment installation documented in `README.md`.
- Windows activation syntax is documented in `README.md`; the scripts themselves use Python standard libraries and portable third-party packages.
- No hosting or deployment target is declared in root product files.
- Scraping requires outbound HTTPS access to the source configured in `scraping.py` and write access to the database directory.
- Reading with `consulta.py` requires an existing `linhas` table populated by `scraping.py`.

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

## Naming Patterns

- Application modules use lowercase Python filenames: `scraping.py` and `consulta.py`.
- `tempCodeRunnerFile.py` is an editor scratch artifact containing a standalone identifier; do not use it as a module pattern.
- Use snake_case, as in `extract_linhas`, `insert_if_new`, and `formatar_linha` in `scraping.py` and `consulta.py`.
- Prefix internal helpers with an underscore, following `_normalize_link` in `scraping.py`.
- Portuguese domain words coexist with English technical verbs: `listar_linhas`, `parse_horlink`, and `upsert_batch`.
- Use snake_case locals and uppercase module constants (`SOURCE_URL`, `DB_PATH`, `_HORARIO_RE`) in `scraping.py`.
- Preserve domain names such as `numero`, `nome`, `linha`, and `linhas` in both application modules.
- Use PascalCase immutable dataclasses, following `LinhaOnibus` in both `scraping.py` and `consulta.py`.
- The two dataclasses have different shapes: the query model in `consulta.py` includes `created_at`.

## Code Style

- No application formatter configuration is detected alongside `requirements.txt`.
- Follow the four-space indentation, double-quoted strings, blank lines between top-level definitions, and multiline calls in `scraping.py`.
- Use multiline triple-quoted SQL with explicit column names, following `ensure_schema` in `scraping.py` and `listar_linhas` in `consulta.py`.
- No application lint configuration or lint command is detected in `README.md` or `requirements.txt`.
- `.agents/` and `.codex/` contain installed GSD tooling; their checks do not establish application lint rules.

## Import Organization

- None detected; `scraping.py` and `consulta.py` are standalone root modules and do not import each other.

## Error Handling

- Return `None` for unmatched link text in `scraping.py:parse_horlink`; callers skip that item.
- Use `raise_for_status()` after HTTP requests in `scraping.py:fetch_page`; request errors propagate to the caller.
- SQLite exceptions propagate from persistence/query helpers; neither `scraping.py:main` nor `consulta.py:main` wraps them.
- Use bound SQL parameters, following `scraping.py:insert_if_new`, rather than interpolating row values.
- Use SQLite connection context managers, following `upsert_batch` and `listar_linhas`.

## Logging

- Keep console reporting in `main()`; parsing and persistence functions return values instead of printing.
- Scraping prints discovered, inserted, and skipped counts; querying prints a total and formatted rows.
- User-facing messages in both modules are Portuguese.

## Comments

- `scraping.py:_normalize_link` explains the intended scheme-free link format.
- `scraping.py:parse_horlink` uses a docstring with representative input text and href.
- `scraping.py:insert_if_new` documents the boolean return contract.
- Not applicable to the Python product; use Python docstrings as demonstrated in `scraping.py`.

## Function Design

- Annotate parameters and return values, following both application modules.
- Pass external input explicitly: `html` and `base_url` to `extract_linhas`, a connection to `insert_if_new`, and a database path to `upsert_batch`.
- `consulta.py:listar_linhas` supplies `DB_PATH` as a default while permitting explicit database injection.
- Return typed records and lists for data, booleans for insertion outcome, and `(inserted, skipped)` counts for batching in `scraping.py`.
- Return strings from presentation helpers, following `consulta.py:formatar_linha`.

## Module Design

- No explicit `__all__` is defined in `scraping.py` or `consulta.py`.
- Keep executable behavior behind `if __name__ == "__main__": main()` so importing helpers does not fetch pages or print rows.
- Application configuration is held in module constants in both modules.
- None detected; no application package initializer exists alongside `scraping.py` and `consulta.py`.

<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

## System Overview

```text

```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| Fetcher | Download the bus listing page with a timeout and HTTP status validation | `scraping.py:51` |
| Parser | Select `a.horLink`, parse bus number/name and normalize links | `scraping.py:25`, `scraping.py:65` |
| Persistence | Create the SQLite table and insert previously unseen numbers | `scraping.py:86`, `scraping.py:116` |
| Query reader | Select stored lines ordered by number | `consulta.py:17` |
| CLI presenter | Render line details and totals to standard output | `consulta.py:33`, `consulta.py:41` |

## Pattern Overview

- Functions in `scraping.py` separate fetching, parsing, extraction, storage, and orchestration.
- `consulta.py` is independently executable and shares data through `onibus.sqlite3`; it does not import the scraper.
- Both scripts use `if __name__ == "__main__"` guards, so importing them does not start their CLI flows.
- `.agents/` and `.codex/` contain development workflow infrastructure, not application services.

## Layers

- Purpose: Retrieve HTML synchronously.
- Location: `scraping.py:51`.
- Depends on: `requests` and the source URL constant in `scraping.py:14`.
- Used by: `scraping.py:131`.
- Purpose: Convert matching anchors into immutable `LinhaOnibus` records.
- Location: `scraping.py:18`, `scraping.py:28`, `scraping.py:35`, `scraping.py:65`.
- Depends on: BeautifulSoup, regular expressions, URL parsing, and an in-memory set of bus numbers.
- Used by: The scraper's main function.
- Purpose: Initialize schema and persist records using parameterized SQL.
- Location: `scraping.py:86`, `scraping.py:100`, `scraping.py:116`.
- Depends on: Python `sqlite3` and `onibus.sqlite3`.
- Used by: The scraper; `consulta.py:17` reads the same schema directly.
- Purpose: Show ingestion counts or formatted stored records.
- Location: `scraping.py:136`, `consulta.py:33`, `consulta.py:41`.
- Depends on: Standard output; there is no HTTP API or graphical interface in the application files.

## Data Flow

### Primary Request Path

### Database Listing

- Durable state lives in the `linhas` table of `onibus.sqlite3`.
- The schema defined in `scraping.py:89` uses `numero INTEGER PRIMARY KEY` and non-null `nome`, `link`, and `created_at` fields.
- `seen` in `scraping.py:70` deduplicates one extraction run only.
- Database connections are local to function calls. Module-level constants provide default paths and URLs.
- Existing records retain their original data because `INSERT OR IGNORE` does not update matching numbers (`scraping.py:107`).

## Key Abstractions

- Purpose: Parsed number, name, and normalized link.
- Example: `scraping.py:18`.
- Pattern: Frozen dataclass with typed fields.
- Purpose: Query result including creation timestamp.
- Example: `consulta.py:9`.
- Pattern: A separate frozen dataclass with the same class name and an additional `created_at` field.
- Purpose: Report inserted and skipped totals.
- Example: `scraping.py:116`.
- Pattern: Two-element integer tuple, not a shared service or repository class.

## Entry Points

- Location: `scraping.py:141`.
- Trigger: `python scraping.py` as documented in `README.md`.
- Responsibilities: Fetch, transform, store, print counts.
- Location: `consulta.py:55`.
- Trigger: `python consulta.py`.
- Responsibilities: Read persisted records and print details.

## Architectural Constraints

- **Threading:** Synchronous execution; no workers, event loop, or scheduler in `scraping.py` or `consulta.py`.
- **Global state:** `SOURCE_URL`, `DB_PATH`, and compiled `_HORARIO_RE` in `scraping.py`; a second `DB_PATH` constant in `consulta.py`.
- **Circular imports:** None between the two application modules; their shared contract is the SQLite schema.
- **Working directory:** The default relative `onibus.sqlite3` path resolves against the process working directory in both scripts.
- **Source contract:** Parsing depends on the `horLink` CSS class and a `Horário <number> <name>` text shape in `scraping.py:25` and `scraping.py:67`.
- **Stored URL contract:** `_normalize_link()` stores host plus path, excluding scheme, query, and fragment (`scraping.py:28`).

## Anti-Patterns

### Misleading update abstraction

### Duplicated storage defaults

## Error Handling

- `fetch_page()` uses `raise_for_status()` and a 30-second request timeout (`scraping.py:51`).
- Unrecognized anchor text returns `None` and is skipped (`scraping.py:41`, `scraping.py:76`).
- Duplicate numbers are ignored in memory and by the database primary key (`scraping.py:78`, `scraping.py:107`).
- The reader handles an empty result set with a message, but does not initialize a missing table (`consulta.py:44`).
- Each insert explicitly commits, so the whole batch is not atomic (`scraping.py:112`).

## Cross-Cutting Concerns

<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.agents/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-fast` for a trivial task inline, with no subagents and no PLAN.md
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
