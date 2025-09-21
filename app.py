from pathlib import Path
from fastapi import FastAPI, HTTPException
from schemas import (
    DailyRequest,
    MonthlyRequest,
    DailyResponse,
    MonthlyResponse,
    DailyKPI,
)
import db
if Path(".env").exists():
    from dotenv import load_dotenv
    load_dotenv()

app = FastAPI(title="Daily/Monthly KPI API", version="1.0.1")


@app.post("/daily", response_model=DailyResponse)
async def get_daily(payload: DailyRequest):
    """
    Fetch KPIs for a specific date.
    Expects: { "db_password": "...", "date": "YYYY-MM-DD" }
    """
    row = await db.fetch_one_by_date(payload.db_password, payload.date.isoformat())
    if not row:
        raise HTTPException(status_code=404, detail="No data for that date.")
    return DailyResponse(**row)


@app.post("/monthly", response_model=MonthlyResponse)
async def get_monthly(payload: MonthlyRequest):
    """
    Fetch ALL daily KPIs for a given year+month (no summary).
    Expects: { "db_password": "...", "year": 2025, "month": 9 }
    """
    # If your db layer already returns (rows, summary), just ignore the summary:
    try:
        rows, _summary = await db.fetch_month(payload.db_password, payload.year, payload.month)
    except TypeError:
        # If you changed db.py to return only rows (e.g., fetch_month_rows), fall back to that:
        rows = await db.fetch_month_rows(payload.db_password, payload.year, payload.month)

    return MonthlyResponse(
        year=payload.year,
        month=payload.month,
        rows=[DailyKPI(**r) for r in rows],
    )


@app.get("/healthz")
async def healthz():
    return {"ok": True}
