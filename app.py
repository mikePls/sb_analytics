from fastapi import FastAPI, APIRouter, Depends, HTTPException
from schemas import (
    DailyRequest,
    MonthlyRequest,
    DailyResponse,
    MonthlyResponse,
    DailyKPI,
)
import db
from auth import require_api_key

app = FastAPI(title="Daily/Monthly KPI API", version="1.3.0")

# Protected router (everything here requires the API key)
protected = APIRouter(dependencies=[Depends(require_api_key)])

@protected.post("/daily", response_model=DailyKPI)
async def get_daily(payload: DailyRequest):
    row = await db.fetch_one_by_date(payload.date)
    if not row:
        raise HTTPException(status_code=404, detail="No data for that date.")
    return DailyKPI(**row)

@protected.post("/monthly", response_model=MonthlyResponse)
async def get_monthly(payload: MonthlyRequest):
    rows, _ = await db.fetch_month(payload.year, payload.month)
    return MonthlyResponse(
        year=payload.year,
        month=payload.month,
        rows=[DailyKPI(**r) for r in rows],
    )

# Mount the protected routes
app.include_router(protected)

# Public health check
@app.get("/healthz")
async def healthz():
    return {"ok": True}

#curl -X POST http://127.0.0.1:8080/daily -H "Authorization: Bearer sb2025ABba" -H "Content-Type: application/json" -d '{ "date": "2025-09-05" }'
