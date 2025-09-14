import os, base64, json, re, statistics, unicodedata
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from openai import AsyncOpenAI
from prompts import (
    JSON_GUARD,EVALUATION_PROMPT_ES,EVALUATION_SCHEMA,
    RUBRIC_ONLY_PROMPT_ES,STRICT_RUBRIC_PROMPT_ES,STRICT_RUBRIC_SCHEMA
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
MODEL = os.getenv("MODEL_NAME","gpt-4o-mini")
client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL) if OPENAI_BASE_URL else AsyncOpenAI(api_key=OPENAI_API_KEY)

app = FastAPI(title="GanadoBravo v4.3.7")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/healthz")
async def healthz():
    return {"ok": True}

@app.exception_handler(Exception)
async def all_err(req, exc):
    return JSONResponse({"error":"server_error","detail":str(exc)}, status_code=200)

def _round05(x): return round(float(x)*2)/2.0
def _norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode().lower().strip()
    s = re.sub(r"[^a-z0-9]+"," ",s); s = re.sub(r"\s+"," ",s).strip()
    return s

CANON = {
    "condicion corporal bcs":"Condición corporal (BCS)",
    "conformacion general":"Conformación general",
    "linea dorsal":"Línea dorsal",
    "angulacion costillar":"Angulación costillar",
    "profundidad de pecho":"Profundidad de pecho",
    "aplomos patas":"Aplomos (patas)",
    "lomo":"Lomo",
    "grupo muscling posterior":"Grupo / muscling posterior",
    "balance anterior posterior":"Balance anterior–posterior",
    "ancho toracico":"Ancho torácico",
    "insercion de cola":"Inserción de cola",
}
ORDER = ["Condición corporal (BCS)","Conformación general","Línea dorsal","Angulación costillar","Profundidad de pecho","Aplomos (patas)","Lomo","Grupo / muscling posterior","Balance anterior–posterior","Ancho torácico","Inserción de cola"]

def canonize(rub):
    out={}
    if not isinstance(rub, dict): return out
    for k,v in rub.items():
        key = CANON.get(_norm(k), None)
        if not key: continue
        try: out[key] = _round05(v)
        except: out[key] = 0.0
    return out

def extract_relaxed(txt):
    if not txt: return {}
    t = txt.strip().replace('```json','```').strip('`')
    m = re.search(r'\{.*\}', t, re.S)
    if not m: return {}
    frag = m.group(0)
    try: return json.loads(frag)
    except: 
        frag = re.sub(r',\s*([}\]])', r'\1', frag)
        return json.loads(frag)

async def run_prompt(prompt, image_b64, schema=None):
    content = [
        {"type":"text","text":JSON_GUARD},
        {"type":"text","text":prompt},
        {"type":"input_image","image_url":{"url":f"data:image/jpeg;base64,{image_b64}"}},
    ]
    # responses.create (si está)
    try:
        resp = await client.responses.create(
            model=MODEL, input=[{"role":"user","content":content}],
            temperature=0,
            response_format={"type":"json_schema","json_schema":{"name":"gb","schema":schema or {"type":"object"},"strict":bool(schema)}}
        )
        txt = getattr(resp, "output_text", None) or getattr(resp, "output", None)
        if not txt and hasattr(resp, "choices"):
            txt = resp.choices[0].message.content
        return json.loads(txt)
    except Exception:
        # fallback chat
        resp = await client.chat.completions.create(
            model=MODEL, temperature=0, response_format={"type":"json_object"},
            messages=[{"role":"system","content":"Devuelve SOLO JSON."},{"role":"user","content":[{"type":"text","text":JSON_GUARD},{"type":"text","text":prompt},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{image_b64}"}}]}]
        )
        txt = resp.choices[0].message.content
        try: return json.loads(txt)
        except: return extract_relaxed(txt)

async def ensure_rubric(image_b64, data):
    rub = canonize(data.get("rubric") or data.get("morphological_rubric") or {})
    if len(rub)<11 or sum(rub.values())==0:
        r = await run_prompt("Devuelve SOLO {\"rubric\":{...}} con las 11 métricas exactas.", image_b64, None)
        rub = canonize(r.get("rubric") or {})
    if len(rub)<11 or sum(rub.values())==0:
        r = await run_prompt( "Devuelve SOLO {\"rubric\":{...}} con las 11 métricas exactas.", image_b64, {"type":"object","properties":{"rubric":{"type":"object","additionalProperties":False}},"required":["rubric"]} )
        rub = canonize(r.get("rubric") or {})
    for k in ORDER: rub.setdefault(k, 0.0)
    return rub

@app.post("/api/evaluate")
async def evaluate(category: str = Form(...), file: UploadFile = File(...), pro: Optional[str] = Form(default="0"), meta_json: Optional[str] = Form(default=None)):
    if not OPENAI_API_KEY: return {"error":"OPENAI_API_KEY no configurada"}
    mode = "pro" if (pro and pro.strip() not in ("0","","false","False")) else "standard"
    img_bytes = await file.read()
    image_b64 = base64.b64encode(img_bytes).decode("utf-8")

    data = await run_prompt(EVALUATION_PROMPT_ES.strip(), image_b64, EVALUATION_SCHEMA)
    rubric = await ensure_rubric(image_b64, data)

    decision = data.get("decision") or {}
    if not decision.get("global_score"):
        decision["global_score"] = round(statistics.mean(list(rubric.values())),1) if rubric else 0.0
    decision.setdefault("decision_level","CONSIDERAR_BAJO")
    decision.setdefault("decision_text","")
    decision.setdefault("rationale","")

    health = data.get("health") or {"flags":[], "notes":""}
    breed  = data.get("breed") or {"guess":"Indeterminado","confidence":0.0}
    return {
        "engine": MODEL, "mode":mode, "category":category.strip().lower(),
        "rubric":rubric, "rubric_notes": data.get("rubric_notes") or {},
        "decision":decision, "health":health, "breed":breed, "lidar_metrics":None
    }
