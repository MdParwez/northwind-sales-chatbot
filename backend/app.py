import os, time, json
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from db import run_query, ensure_db, get_schema, schema_json
from forecast import maybe_forecast
from sqlgen import generate_sql_and_chart
from llm_groq import USE_LLM, parse_intent, make_sql, write_insight, repair_sql

load_dotenv()

ROW_LIMIT = int(os.getenv("ROW_LIMIT", "2000"))
DEFAULT_PERIODS = int(os.getenv("FORECAST_PERIODS", "3"))

app = FastAPI(title="Northwind Sales Chatbot API", version="2.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatReq(BaseModel):
    question: str

@app.get("/healthz")
def health():
    ensure_db()
    return {"status":"ok"}

@app.get("/schema")
def schema():
    return get_schema()

@app.get("/examples")
def examples():
    return [
        "Top 5 products by revenue in 1997",
        "Monthly sales 1997 and forecast next 3 months",
        "Sales share by country this year",
        "Top 3 employees by sales in 1997",
    ]

def select_only(sql: str):
    if not sql.strip().lower().startswith("select"):
        raise HTTPException(status_code=400, detail="Only SELECT queries are allowed.")

def exec_sql(sql: str):
    select_only(sql)
    start = time.time()
    cols, rows = run_query(sql)
    truncated = False
    if len(rows) > ROW_LIMIT:
        rows = rows[:ROW_LIMIT]
        truncated = True
    elapsed_ms = int((time.time() - start) * 1000)
    return cols, rows, elapsed_ms, truncated

def choose_chart(plan: Dict[str, Any], columns: List[str]) -> Dict[str, Any]:
    intent = (plan or {}).get("intent") or "aggregate"
    group_by = (plan or {}).get("group_by") or "none"
    lower = [c.lower() for c in columns]
    chart = {"kind":"bar","xField":"","yField":"","title":"","subtitle":"Northwind • USD"}
    if "month" in lower or "date" in lower or intent in ("timeseries","forecast"):
        chart["kind"] = "line"
        chart["xField"] = "month" if "month" in lower else (columns[lower.index("date")] if "date" in lower else columns[0])
        chart["yField"] = "revenue" if "revenue" in lower else columns[-1]
        chart["title"] = "Monthly Sales"
        return chart
    key = group_by.lower()
    if key in ("country","category","employee","product") and key in lower:
        chart["xField"] = columns[lower.index(key)]
        chart["yField"] = "revenue" if "revenue" in lower else columns[-1]
        chart["title"] = f"Sales by {key.capitalize()}"
        chart["kind"] = "bar"
        return chart
    chart["xField"] = columns[0]; chart["yField"] = columns[-1]; chart["title"] = f"{chart['yField']} by {chart['xField']}"
    return chart

def rows_to_chartdata(columns: List[str], rows: List[List[Any]], x: str, y: str):
    idx = {c.lower(): i for i, c in enumerate(columns)}
    if x.lower() not in idx or y.lower() not in idx:
        raise HTTPException(status_code=400, detail=f"Chart fields not in result. Got columns: {columns}")
    data = []
    for r in rows:
        data.append({x: r[idx[x.lower()]], y: r[idx[y.lower()]]})
    return data

def compute_metrics(chart_data, x, y):
    total = sum(float(d.get(y,0) or 0) for d in chart_data)
    ranked = sorted(chart_data, key=lambda d: float(d.get(y,0) or 0), reverse=True)
    top = ranked[0] if ranked else None
    out = {"total": total, "top": top, "k": len(chart_data)}
    if top and total>0:
        out["top_share_pct"] = round(100.0*float(top[y])/total, 1)
    return out

class ChartSpec(BaseModel):
    kind: str
    xField: str
    yField: str
    data: list
    title: str | None = None
    subtitle: str | None = None

class ApiReply(BaseModel):
    chart: ChartSpec
    insight: str
    table: dict | None = None
    meta: dict | None = None

@app.post("/chat", response_model=ApiReply)
def chat(req: ChatReq):
    ensure_db()
    scheme = schema_json()
    used_llm = False

    if os.getenv("USE_LLM", "false").lower() in ("1","true","yes"):
        try:
            plan = parse_intent(req.question, scheme)
            sql = make_sql(plan, scheme).strip()
            try:
                cols, rows, elapsed, truncated = exec_sql(sql)
            except Exception as e:
                fixed = repair_sql(str(e), sql, scheme).strip()
                cols, rows, elapsed, truncated = exec_sql(fixed)
                sql = fixed
            used_llm = True
            chart = choose_chart(plan, cols)
            data = rows_to_chartdata(cols, rows, chart["xField"], chart["yField"])
            if str(plan.get("intent")) == "forecast":
                periods = int(plan.get("periods") or os.getenv("FORECAST_PERIODS","3"))
                data = maybe_forecast(data, chart["xField"], chart["yField"], periods=periods)
            metrics = compute_metrics(data, chart["xField"], chart["yField"])
            try:
                insight = write_insight(json.dumps(metrics), json.dumps(rows[:5]))
            except Exception:
                insight = f"Returned {len(rows)} rows."
            return {
                "chart": {**chart, "data": data},
                "insight": insight,
                "table": {"columns": cols, "rows": rows},
                "meta": {"sql": sql, "elapsed_ms": elapsed, "row_count": len(rows), "forecast": plan.get("intent")=="forecast", "used_llm": used_llm, "truncated": truncated},
            }
        except Exception:
            pass

    # Heuristic fallback
    plan = generate_sql_and_chart(req.question)
    sql = plan["sql"].strip()
    cols, rows, elapsed, truncated = exec_sql(sql)
    chart = plan["chart"]
    data = rows_to_chartdata(cols, rows, chart["xField"], chart["yField"])
    if plan.get("forecast"):
        data = maybe_forecast(data, chart["xField"], chart["yField"], periods=plan.get("periods", 3))
    insight = plan.get("insight") or f"Returned {len(rows)} rows."
    return {
        "chart": {**chart, "data": data},
        "insight": insight,
        "table": {"columns": cols, "rows": rows},
        "meta": {"sql": sql, "elapsed_ms": elapsed, "row_count": len(rows), "forecast": plan.get("forecast", False), "used_llm": used_llm, "truncated": truncated},
    }