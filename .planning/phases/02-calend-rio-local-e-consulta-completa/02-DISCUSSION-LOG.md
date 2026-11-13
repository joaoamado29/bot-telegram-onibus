# Phase 2: Calendário local e consulta completa - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `02-CONTEXT.md` — this log preserves the alternatives considered.

**Date:** 2026-11-13
**Phase:** 2-calendario-local-e-consulta-completa
**Areas discussed:** Calendar precedence on weekend holidays, Holiday label in response

---

## Calendar precedence on weekend holidays

| Option | Description | Selected |
|--------|-------------|----------|
| Use Sundays/holidays for every holiday | A recognized holiday uses `domingos_feriados` regardless of weekday or weekend. | ✓ |
| Keep Saturday or Sunday calendar | Weekend classification takes precedence even if the date is a holiday. | |
| Apply the source-published calendar for that date | Use the calendar indicated by the schedule source for the date. | |

**User's choice:** Use Sundays/holidays for every holiday.
**Notes:** Applies to recognized national, Ceará, and Fortaleza holidays; optional holidays are excluded per prior approved project decisions.

---

## Holiday label in response

| Option | Description | Selected |
|--------|-------------|----------|
| Show holiday name and date | Identify the holiday and date in the response. | ✓ |
| Show only “Domingos/feriados” | Identify the selected schedule category without the holiday name. | |
| Do not highlight the holiday | Show the date and schedule only. | |

**User's choice:** Show the holiday name and date.
**Notes:** The user selected the recommended option.

---

## the agent's Discretion

- The verified official sources and technical maintenance approach for holiday data.
- Message splitting or formatting needed to show the complete schedule within Telegram limits.

## Deferred Ideas

None.
