# Scraper ETUFOR (Tonoponto) + SQLite

Automação para coletar os links de horários (classe `horLink`) da página da ETUFOR no Tonoponto, tratar o texto (número + nome) e armazenar em SQLite, ignorando números já existentes.

## Requisitos

- Python 3.10+

## Instalação

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Uso

Executa o scraping e persiste no banco `onibus.sqlite3`:

```bash
python scraping.py
```

## Banco de dados

- **Arquivo**: `onibus.sqlite3`
- **Tabela**: `linhas`
  - `numero` (INTEGER, UNIQUE)
  - `nome` (TEXT)
  - `link` (TEXT)
  - `created_at` (TEXT)

