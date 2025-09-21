import os
from fastapi import Header, HTTPException
from typing import Optional
from pathlib import Path

if Path(".env").exists():
    from dotenv import load_dotenv
    load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    raise RuntimeError("API_TOKEN must be set in the environment")

async def require_api_key(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    # Accept either "Authorization: Bearer <token>" or "X-API-Key: <token>"
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    elif x_api_key:
        token = x_api_key.strip()

    if token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
