import os
import ssl
import asyncpg



DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")

if not DB_PASSWORD:
    raise RuntimeError("DB_PASSWORD must be set in the environment")


_SSL_CTX = ssl.create_default_context()

async def fetch_one_by_date(day_iso: str):
    conn = await asyncpg.connect(
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    ssl=_SSL_CTX,
    )
    try:
        row = await conn.fetchrow(
            """
            SELECT day,
            attendance,
            transactions,
            items_sold,
            total_gross_gbp,
            all_four,
            show_book,
            comments
            FROM public.daily_kpis
            WHERE day = $1::date
            LIMIT 1
            """,
            day_iso,
            )
        return dict(row) if row else None
    finally:
        await conn.close()

async def fetch_month(year: int, month: int):
    conn = await asyncpg.connect(
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    ssl=_SSL_CTX,
    )
    try:
        rows = await conn.fetch(
        """
        SELECT day,
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
        SELECT COUNT(*)::int AS days,
        SUM(attendance)::int AS attendance_sum,
        SUM(transactions)::int AS transactions_sum,
        SUM(items_sold)::int AS items_sold_sum,
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