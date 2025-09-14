import os, json
from typing import Dict, Any
from groq import Groq

GROQ_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
USE_LLM = os.getenv("USE_LLM", "false").lower() in ("1","true","yes")

def get_client():
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY not set")
    return Groq(api_key=key)

def chat_json(system: str, user: str, temperature: float = 0.2) -> Dict[str, Any]:
    client = get_client()
    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        temperature=temperature,
        messages=[{"role":"system","content":system},{"role":"user","content":user}],
        response_format={"type":"json_object"},
    )
    txt = resp.choices[0].message.content
    return json.loads(txt)

def chat_text(system: str, user: str, temperature: float = 0.2) -> str:
    client = get_client()
    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        temperature=temperature,
        messages=[{"role":"system","content":system},{"role":"user","content":user}],
    )
    return resp.choices[0].message.content or ""

def parse_intent(question: str, schema_json: str) -> Dict[str, Any]:
    system = ("You are a strict planner for Northwind SQLite analytics. "
              "Return ONLY JSON: {intent, group_by, metric, filters, top_n, periods?}. "
              "intent∈{aggregate,timeseries,forecast}; group_by∈{month,country,category,employee,product,none}. "
              "metric defaults to revenue.")
    user = f"SCHEMA:\\n{schema_json}\\n\\nQUESTION:\\n{question}"
    return chat_json(system, user)

def make_sql(plan: Dict[str, Any], schema_json: str) -> str:
    rules = ("Generate a SINGLE SQLite SELECT for Northwind. Use ONLY these tables/columns. "
             "Use STRFTIME('%Y', Orders.OrderDate) for YEAR filters. "
             "Revenue = SUM(OrderDetails.UnitPrice*OrderDetails.Quantity*(1-OrderDetails.Discount)). "
             "Return ONLY SQL, no prose.")
    system = rules + "\\n\\nALLOWED SCHEMA:\\n" + schema_json
    from json import dumps
    return chat_text(system, dumps(plan, ensure_ascii=False))

def write_insight(metrics_json: str, top_rows_json: str) -> str:
    system = "Write 1–3 concise sentences with exact numbers and % where possible. No fluff."
    user = f"METRICS:\\n{metrics_json}\\n\\nTOP_ROWS:\\n{top_rows_json}"
    return chat_text(system, user, temperature=0.1)

def repair_sql(error: str, bad_sql: str, schema_json: str) -> str:
    system = ("You fix SQLite SELECT queries. Return ONLY the corrected SQL. "
              "Use only given schema; no DDL/DML.")
    user = f"SCHEMA:\\n{schema_json}\\n\\nERROR:\\n{error}\\n\\nSQL:\\n{bad_sql}"
    return chat_text(system, user)