# Full plan → running app

Objective: Implement README phases 0–4 until backend + frontend run successfully via Docker.
Branch: `feature/full-plan-implementation`
Delivery: ask-on-risk
Test runner: `docker compose --profile test run --rm backend-test` / `python -m unittest discover -s tests -v`

## Specs

- S1: Docker multi-stage (dev/test/prod) with debugpy on `:5678`; FastAPI skeleton with `/health`.
- S2: `data/expenses_log.csv` seed June–November; `date,concept,amount`; November anomaly without "Black Friday"/"Oferta".
- S3: OpenRouter chat client (`src/llm.py`) + base `Agent` loop with message memory, `max_iterations`, `max_tool_calls`.
- S4: CSV tools confined to `WORKDIR=/data`; reject path traversal (`../`, absolute external paths).
- S5: TinyDB idempotent persistence with deterministic unique keys; Jev Choice categorization (fallback when no API key).
- S6: FastAPI endpoints: list categorized movements + aggregated metrics (category %, monthly averages).
- S7: React+Vite+Tailwind dashboard via pnpm; dark mode default + light toggle; category %, Nov vs average, transaction list; `pnpm build` passes.
- S8: `NECESSITY_SCALE` 1–5 in config; evaluator uses Jev Score; stores `necessity_level`.
- S9: Analyst reads TinyDB and produces structured report (patterns / excesses / actions) via reasoning LLM (fallback when no key).
- S10: `docker compose --profile dev up` serves API on `:8000` and frontend on `:5173` successfully.

## Tasks

- T1 [S1-S2] inline — verify/complete Fase 0 — done (pre-existing + verified)
- T2 [S3-S5] inline — Fase 1 agents/core — done (24 unittest suite green in Docker)
- T3 [S6-S7] inline — Fase 2 API + dashboard — done (`pnpm build` OK)
- T4 [S8] inline — Fase 3 evaluator — done
- T5 [S9] inline — Fase 4 analyst — done (fallback report without API key)
- T6 [S10] inline — Docker smoke run — done (health 200, frontend 200, pipeline 136 rows)

## Log

- L1: Implement the plan from README.md until the application is successfully running.
- L2: Fase 0 largely present (Docker, FastAPI skeleton, CSV). Missing phases 1–4 and frontend sources. No OPENROUTER_API_KEY in env — deterministic fallbacks required so app runs without key.
- L3: Implemented phases 1–4 with Jev/OpenRouter clients + keyword/LLM fallbacks. Live pipeline: 136 inserted, 121 evaluated, November delta +1104.36 EUR. Stack: `:8000` + `:5173`.
