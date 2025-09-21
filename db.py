import os
import ssl
import asyncpg
from pathlib import Path
from datetime import date
from typing import Union

# Load .env for local dev if present
if Path(".env").exists():
    from dotenv import load_dotenv
    load_dotenv()

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")

if not DB_PASSWORD:
    raise RuntimeError("DB_PASSWORD must be set in the environment")

def _build_ssl_context() -> ssl.SSLContext:
    """
    Build an SSL context that:
      - Uses system trust store by default (works on your Windows box).
      - If DO_PG_CA_CERT (PEM text) is set, load that (for DO App Platform).
      - If DO_PG_CA_CERT_PATH is set, load from that file.
      - If ALLOW_INSECURE_PG=1, disable verification (DEV ONLY).
    """
    # Dev-only escape hatch
    if os.getenv("ALLOW_INSECURE_PG") == "1":
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    # Start with system trust (works locally if you installed the CA)
    ctx = ssl.create_default_context()

    pem_text = os.getenv("DO_PG_CA_CERT")          # full PEM content as env var
    cafile = os.getenv("DO_PG_CA_CERT_PATH")       # path to a .crt/.pem file

    if pem_text:
        try:
            ctx.load_verify_locations(cadata=pem_text)
        except Exception as e:
            raise RuntimeError("Failed to load DO_PG_CA_CERT PEM from env") from e
    elif cafile:
        if not Path(cafile).exists():
            raise RuntimeError(f"DO_PG_CA_CERT_PATH points to a non-existent file: {cafile}")
        try:
            ctx.load_verify_locations(cafile=cafile)
        except Exception as e:
            raise RuntimeError(f"Failed to load CA file from DO_PG_CA_CERT_PATH: {cafile}") from e

    return ctx

_SSL_CTX = _build_ssl_context()

async def _connect():
    return await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        ssl=_SSL_CTX,
    )

async def fetch_one_by_date(day_iso: Union[date, str]):
    conn = await _connect()
    try:
        row = await conn.fetchrow(
            """
            SELECT
                day,
                attendance,
                transactions,
                items_sold,
                total_gross_gbp,
                all_four,
                show_book,
                comments
            FROM public.daily_kpis
            WHERE day = $1
            LIMIT 1
            """,
            day_iso,
        )
        return dict(row) if row else None
    finally:
        await conn.close()

async def fetch_month(year: int, month: int):
    conn = await _connect()
    try:
        rows = await conn.fetch(
            """
            SELECT
                day,
                attendance,
                transactions,
                items_sold,
                total_gross_gbp,
                all_four,
                show_book,
                comments
            FROM public.daily_kpis
            WHERE EXTRACT(YEAR FROM day) = $1
              AND EXTRACT(MONTH FROM day) = $2
            ORDER BY day ASC
            """,
            year,
            month,
        )
        summary = await conn.fetchrow(
            """
            SELECT
                COUNT(*)::int              AS days,
                SUM(attendance)::int       AS attendance_sum,
                SUM(transactions)::int     AS transactions_sum,
                SUM(items_sold)::int       AS items_sold_sum,
                SUM(total_gross_gbp)::float8 AS total_gross_gbp_sum
            FROM public.daily_kpis
            WHERE EXTRACT(YEAR FROM day) = $1
              AND EXTRACT(MONTH FROM day) = $2
            """,
            year,
            month,
        )
        return [dict(r) for r in rows], (dict(summary) if summary else None)
    finally:
        await conn.close()
