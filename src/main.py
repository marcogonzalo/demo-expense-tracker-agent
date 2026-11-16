"""FastAPI HTTP entrypoint for the expense tracker agent demo."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.agents.analyst import AnalystAgent
from src.agents.evaluator import EvaluatorAgent
from src.agents.ingester import IngesterAgent
from src.config import APP_NAME, APP_VERSION, EXPENSES_CSV, NECESSITY_SCALE, WORKDIR
from src.db import list_movements
from src.metrics import compute_metrics, enrich_movement

print("WORKDIR", WORKDIR)

app = FastAPI(title=APP_NAME, version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe used by Docker and local smoke checks."""
    return {"status": "ok", "service": APP_NAME, "version": APP_VERSION}


@app.get("/")
def root() -> dict[str, str]:
    """Minimal root so the HTTP surface exists from Fase 0 onward."""
    return {
        "message": "Expense tracker agent API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/api/necessity-scale")
def necessity_scale() -> dict[str, dict[str, str]]:
    """Expose NECESSITY_SCALE for the dashboard."""
    return {str(k): v for k, v in NECESSITY_SCALE.items()}


@app.get("/api/movements")
def get_movements() -> dict:
    """List categorized movements with expanded necessity metadata."""
    rows = [enrich_movement(m) for m in list_movements()]
    return {"count": len(rows), "movements": rows}


@app.get("/api/metrics")
def get_metrics() -> dict:
    """Aggregated category percentages and monthly averages."""
    return compute_metrics()


@app.post("/api/ingest")
def run_ingest(csv_path: str = EXPENSES_CSV) -> dict:
    """Run the ingester agent against the seed CSV (idempotent)."""
    try:
        result = IngesterAgent().ingest(csv_path)
    except Exception as exc:  # noqa: BLE001 — surface tool/path errors to client
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result


@app.post("/api/evaluate")
def run_evaluate() -> dict:
    """Assign necessity levels to expense movements."""
    return EvaluatorAgent().evaluate_all()


@app.post("/api/analyze")
def run_analyze() -> dict:
    """Produce the three-block financial analysis report."""
    return AnalystAgent().analyze()


@app.post("/api/pipeline")
def run_pipeline() -> dict:
    """Ingest → evaluate → analyze in one call (demo bootstrap)."""
    ingest = IngesterAgent().ingest()
    evaluate = EvaluatorAgent().evaluate_all()
    analyze = AnalystAgent().analyze()
    return {
        "ingest": ingest,
        "evaluate": evaluate,
        "analyze": analyze,
        "metrics": compute_metrics(),
    }
