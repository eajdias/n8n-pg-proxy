from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
import os

app = FastAPI()

if "PG_PASSWORD" not in os.environ:
    raise SystemExit("PG_PASSWORD is required (set via env)")

DB_CONFIG = {
    "host": os.getenv("PG_HOST", "databases-central"),
    "port": int(os.getenv("PG_PORT", "5432")),
    "user": os.getenv("PG_USER", "postgres"),
    "password": os.environ["PG_PASSWORD"],
    "database": os.getenv("PG_DATABASE", "zscan_app"),
}


class QueryRequest(BaseModel):
    sql: str
    params: list = []
    database: str = None


class BatchQueryRequest(BaseModel):
    queries: list[QueryRequest]


def _execute(conn, sql, params):
    cur = conn.cursor()
    cur.execute(sql, params or None)
    if cur.description:
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        return {"columns": cols, "rows": [list(r) for r in rows], "rowcount": len(rows)}
    conn.commit()
    return {"columns": [], "rows": [], "rowcount": cur.rowcount}


@app.post("/query")
def execute_query(req: QueryRequest):
    db = req.database or DB_CONFIG["database"]
    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=db,
        )
        return _execute(conn, req.sql, req.params)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if conn:
            conn.close()


@app.post("/batch")
def execute_batch(req: BatchQueryRequest):
    results = []
    for q in req.queries:
        db = q.database or DB_CONFIG["database"]
        conn = None
        try:
            conn = psycopg2.connect(
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                database=db,
            )
            results.append({**_execute(conn, q.sql, q.params), "ok": True})
        except Exception as e:
            results.append({"error": str(e), "ok": False})
        finally:
            if conn:
                conn.close()
    return {"results": results}


@app.get("/health")
def health():
    return {"status": "ok"}