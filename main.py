import os, base64, json, unicodedata
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from openai import AsyncOpenAI
from prompts import (
    EVALUATION_PROMPT_ES, EVALUATION_SCHEMA,
    RUBRIC_ONLY_PROMPT_ES, HEALTH_ONLY_PROMPT_ES, BREED_ONLY_PROMPT_ES
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")  # opcional
MODEL = os.getenv("MODEL_NAME", "gpt-4o-mini")

client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL) if OPENAI_BASE_URL else AsyncOpenAI(api_key=OPENAI_API_KEY)

app = FastAPI(title="GanadoBravo IA v4.3")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/healthz")
async def healthz():
    return {"ok": True}

@app.exception_handler(Exception)
async def _all_errors(request, exc):
    detail = str(exc) if exc else "unknown"
    return JSONResponse({"error": "server_error", "detail": detail}, status_code=200)

def _round05(x: float) -> float:
    return round(x*2)/2.0

def _norm(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower().strip()

CANON = {
    _norm("Condición corporal (BCS)"): "Condición corporal (BCS)",
    _norm("Conformación general"): "Conformación general",
    _norm("Línea dorsal"): "Línea dorsal",
    _norm("Angulación costillar"): "Angulación costillar",
    _norm("Profundidad de pecho"): "Profundidad de pecho",
    _norm("Aplomos (patas)"): "Aplomos (patas)",
    _norm("Lomo"): "Lomo",
    _norm("Grupo / muscling posterior"): "Grupo / muscling posterior",
    _norm("Balance anterior–posterior"): "Balance anterior–posterior",
    _norm("Ancho torácico"): "Ancho torácico",
    _norm("Inserción de cola"): "Inserción de cola",
}

ORDER = list(CANON.values())

def canonicalize_rubric(rub: dict | None) -> dict:
    out = {}
    if not isinstance(rub, dict): 
        return out
    for k, v in rub.items():
        key = CANON.get(_norm(str(k)))
        if not key:
            continue
        try:
            out[key] = float(_round05(float(v)))
        except Exception:
            out[key] = 0.0
    return out

async def run_prompt(prompt: str, image_b64: str, schema: dict | None):
    content = [
        {"type": "text", "text": prompt},
        {"type": "input_image", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
    ]
    use_responses = hasattr(client, "responses") and callable(getattr(getattr(client, "responses"), "create", None))
    if use_responses:
        kwargs = {"model": MODEL, "input": [{"role": "user", "content": content}], "temperature": 0}
        if schema:
            kwargs["response_format"] = {"type":"json_schema","json_schema":{"name":"gb_schema","schema":schema,"strict":True}}
        else:
            kwargs["response_format"] = {"type":"json_object"}
        resp = await client.responses.create(**kwargs)
        out_text = getattr(resp, "output_text", None) or getattr(resp, "output", None)
        if not out_text and hasattr(resp, "choices"):
            out_text = resp.choices[0].message.content
        return json.loads(out_text)

    # Fallback a chat.completions
    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
        ]
    }]
    resp = await client.chat.completions.create(
        model=MODEL, messages=messages, temperature=0, response_format={"type": "json_object"}
    )
    txt = resp.choices[0].message.content
    return json.loads(txt)

async def ensure_rubric(image_b64: str, data: dict) -> dict:
    rub = data.get("rubric") or data.get("morphological_rubric")
    rub = canonicalize_rubric(rub)
    if len(rub) >= 9:  # aceptamos si llegó casi completo
        return rub
    # pedir solo rubric
    r = await run_prompt(RUBRIC_ONLY_PROMPT_ES, image_b64, None)
    rub2 = canonicalize_rubric(r.get("rubric"))
    # merge preferente a rub2
    rub.update(rub2)
    # rellenar faltantes con 0 para no dejar celdas vacías
    for key in ORDER:
        rub.setdefault(key, 0.0)
    return rub

async def ensure_health(image_b64: str, data: dict) -> dict:
    h = data.get("health") or {}
    if isinstance(h, dict) and "flags" in h and "notes" in h:
        return {"flags": h.get("flags") or [], "notes": h.get("notes") or ""}
    r = await run_prompt(HEALTH_ONLY_PROMPT_ES, image_b64, None)
    h2 = r.get("health") or {}
    return {"flags": h2.get("flags") or [], "notes": h2.get("notes") or ""}

async def ensure_breed(image_b64: str, data: dict) -> dict:
    b = data.get("breed") or {}
    if isinstance(b, dict) and b.get("guess"):
        return {"guess": b.get("guess") or "Indeterminado", "confidence": float(b.get("confidence") or 0.0)}
    r = await run_prompt(BREED_ONLY_PROMPT_ES, image_b64, None)
    b2 = r.get("breed") or {}
    return {"guess": b2.get("guess") or "Indeterminado", "confidence": float(b2.get("confidence") or 0.0)}

@app.post("/api/evaluate")
async def evaluate(
    category: str = Form(...),
    file: UploadFile = File(...),
    pro: Optional[str] = Form(default="0"),
    meta_json: Optional[str] = Form(default=None),
):
    if not OPENAI_API_KEY:
        return {"error": "OPENAI_API_KEY no configurada en el servidor"}

    mode = "pro" if (pro and pro.strip() not in ("0", "", "false", "False")) else "standard"

    img_bytes = await file.read()
    image_b64 = base64.b64encode(img_bytes).decode("utf-8")

    # 1) Llamado principal
    data = await run_prompt(EVALUATION_PROMPT_ES.strip(), image_b64, EVALUATION_SCHEMA)

    # 2) Normalizaciones + fallbacks garantizados
    rubric = await ensure_rubric(image_b64, data)
    health = await ensure_health(image_b64, data)
    breed  = await ensure_breed(image_b64, data)

    # Top-level
    out = {
        "engine": MODEL,
        "mode": mode,
        "category": category.strip().lower(),
        "rubric": rubric,
        "rubric_notes": data.get("rubric_notes") or {},
        "decision": data.get("decision") or {
            "global_score": 0.0,
            "decision_level": "CONSIDERAR_BAJO",
            "decision_text": "",
            "rationale": ""
        },
        "health": health,
        "breed": breed,
        "lidar_metrics": None,
    }
    return out
