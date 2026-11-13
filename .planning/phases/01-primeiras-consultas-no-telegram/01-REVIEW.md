---
phase: 01-primeiras-consultas-no-telegram
reviewed: 2026-11-13T18:20:00Z
depth: standard
files_reviewed: 19
files_reviewed_list:
  - .gitignore
  - README.md
  - bot.py
  - consulta.py
  - onibus/core.py
  - onibus/refresh.py
  - onibus/search.py
  - onibus/telegram_handlers.py
  - requirements.txt
  - scraping.py
  - tests/fixtures/horarios.html
  - tests/test_application.py
  - tests/test_refresh.py
  - tests/test_schedules.py
  - tests/test_scraping.py
  - tests/test_search.py
  - tests/test_storage.py
  - tests/test_telegram_handlers.py
  - tests/test_tracer.py
findings:
  critical: 0
  warning: 3
  info: 0
  total: 3
  necessity: 0
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-11-13T18:20:00Z  
**Depth:** standard  
**Files Reviewed:** 19  
**Status:** issues_found

## Summary

Reviewed the phase's 19 source-scope files, including current uncommitted edits in `bot.py` and `onibus/core.py`. The evaluation-scope resolver returned a usable but degraded `phase-range` scope because task-commit rows are missing; its file list was used, with the two dirty source files read in their current state. The review found defects in production catalog refresh/recovery and in the one-shot collection CLI. No tests were run as part of this review.

## Warnings

### WR-01: Production refresh never downloads the line catalog

**File:** `onibus/refresh.py:151-159`  
**Issue:** `_sincronizar_catalogo()` downloads the catalog only when `self.fetcher` is explicitly provided. The production `CoordenadorColeta(DB_PATH)` is constructed without one in `bot.py`, so initial and weekly jobs skip `SOURCE_URL` and simply return existing `linhas`. A clean database therefore has no routes for the initial job to detail-scrape, and newly added source routes never enter the catalog.
**Fix:** Use the production catalog fetcher (`scraping.fetch_page(SOURCE_URL)`) when no injected fetcher is supplied, while retaining injection for tests.

### WR-02: Catalog failures are swallowed without retry

**File:** `onibus/refresh.py:151-159`  
**Issue:** Catalog retrieval/parsing/insertion errors are logged and then converted into a normal return of whatever rows already exist. When the catalog is empty, `refresh_all()` sees no per-line failures and schedules no retry; after the one-shot bootstrap fails, collection waits until the weekly job. This also contradicts plan 01-04, which requires bounded retry for an initial catalog failure.
**Fix:** Return or raise an explicit catalog failure to the coordinator and schedule a bounded catalog retry. Preserve existing catalog entries and continue serving their schedules when they are available.

### WR-03: `--coletar-linha` continues into Telegram polling

**File:** `bot.py:43-73`  
**Issue:** After collecting and printing success for `--coletar-linha`, `main()` continues to require `TELEGRAM_BOT_TOKEN` and starts `run_polling()`. The documented manual collection command therefore exits with an error when no token is configured, or hangs in the bot when one is configured, instead of acting as a one-shot CLI command.
**Fix:** Return from `main()` after successful one-line collection, or make the CLI operation mutually exclusive and terminate after completing it.

---

_Reviewed: 2026-11-13T18:20:00Z_  
_Reviewer: the agent (gsd-code-reviewer)_  
_Depth: standard_
