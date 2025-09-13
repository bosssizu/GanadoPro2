import os, base64, json, unicodedata, statistics, re
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from openai import AsyncOpenAI
from prompts import (
    JSON_GUARD, EVALUATION_PROMPT_ES, EVALUATION_SCHEMA,
    RUBRIC_ONLY_PROMPT_ES, STRICT_RUBRIC_PROMPT_ES, STRICT_RUBRIC_SCHEMA,
    HEALTH_ONLY_PROMPT_ES, BREED_ONLY_PROMPT_ES
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
MODEL = os.getenv("MODEL_NAME", "gpt-4o-mini")

client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL) if OPENAI_BASE_URL else AsyncOpenAI(api_key=OPENAI_API_KEY)

app = FastAPI(title="GanadoBravo IA v4.3.4")
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

def _norm_basic(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower().strip()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

CANON_LIST = [
    "Condición corporal (BCS)",
    "Conformación general",
    "Línea dorsal",
    "Angulación costillar",
    "Profundidad de pecho",
    "Aplomos (patas)",
    "Lomo",
    "Grupo / muscling posterior",
    "Balance anterior–posterior",
    "Ancho torácico",
    "Inserción de cola",
]

def build_canon():
    variants = {}
    for k in CANON_LIST:
        v = [
            k,
            k.replace("–","-"),
            k.replace(" / "," ").replace("/"," ").replace("(","").replace(")",""),
            k.replace("–"," ").replace("-"," "),
        ]
        for a in v:
            variants[_norm_basic(a)] = k
    # manuales + posibles en inglés
    variants[_norm_basic("balance anterior-posterior")] = "Balance anterior–posterior"
    variants[_norm_basic("grupo muscling posterior")] = "Grupo / muscling posterior"
    variants[_norm_basic("condicion corporal")] = "Condición corporal (BCS)"
    variants[_norm_basic("body condition score")] = "Condición corporal (BCS)"
    variants[_norm_basic("general conformation")] = "Conformación general"
    variants[_norm_basic("dorsal line")] = "Línea dorsal"
    variants[_norm_basic("rib angulation")] = "Angulación costillar"
    variants[_norm_basic("chest depth")] = "Profundidad de pecho"
    variants[_norm_basic("legs alignment")] = "Aplomos (patas)"
    variants[_norm_basic("loin")] = "Lomo"
    variants[_norm_basic("hind muscling group")] = "Grupo / muscling posterior"
    variants[_norm_basic("thoracic width")] = "Ancho torácico"
    variants[_norm_basic("tail insertion")] = "Inserción de cola"
    return variants

CANON = build_canon()
ORDER = CANON_LIST[:]

def canonicalize_rubric(rub: dict | None) -> dict:
    out = {}
    if not isinstance(rub, dict):
        return out
    for k, v in rub.items():
        key = CANON.get(_norm_basic(str(k)))
        if not key: 
            continue
        try:
            out[key] = float(_round05(float(v)))
        except Exception:
            out[key] = 0.0
    return out

def extract_json_relaxed(text: str) -> dict:
    if not text: return {}
    t = text.strip().replace('```json', '```').strip('`')
    m = re.search(r'\{.*\}', t, re.S)
    if not m:
        m = re.search(r'\[.*\]', t, re.S)
    if not m: return {}
    frag = m.group(0)
    try:
        return json.loads(frag)
    except Exception:
        frag = re.sub(r',\s*([}\]])', r'\1', frag)
        return json.loads(frag)

async def run_prompt(prompt: str, image_b64: str, schema: dict | None):
    content = [
        {"type": "text", "text": JSON_GUARD},
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
        try:
            resp = await client.responses.create(**kwargs)
            out_text = getattr(resp, "output_text", None) or getattr(resp, "output", None)
            if not out_text and hasattr(resp, "choices"):
                out_text = resp.choices[0].message.content
            return json.loads(out_text)
        except Exception:
            pass

    messages = [
        {"role": "system", "content": "Eres un extractor estricto que devuelve SOLO json."},
        {"role": "user", "content": [
            {"type": "text", "text": JSON_GUARD},
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
        ]}
    ]
    try:
        resp = await client.chat.completions.create(
            model=MODEL, messages=messages, temperature=0, response_format={"type": "json_object"}
        )
        txt = resp.choices[0].message.content
        return json.loads(txt)
    except Exception as e:
        resp = await client.chat.completions.create(model=MODEL, messages=messages, temperature=0)
        txt = resp.choices[0].message.content
        data = extract_json_relaxed(txt)
        if not data:
            raise
        return data

async def refetch_rubric_strict(image_b64: str) -> dict:
    r = await run_prompt(STRICT_RUBRIC_PROMPT_ES, image_b64, STRICT_RUBRIC_SCHEMA)
    rub = r.get("rubric") or {}
    return canonicalize_rubric(rub)

async def ensure_rubric(image_b64: str, data: dict) -> dict:
    rub = canonicalize_rubric(data.get("rubric") or data.get("morphological_rubric"))
    if len(rub) < 11 or sum(rub.values()) == 0:
        # 1er intento: prompt de rúbrica
        r = await run_prompt(RUBRIC_ONLY_PROMPT_ES, image_b64, None)
        rub = canonicalize_rubric(r.get("rubric"))
    if len(rub) < 11 or sum(rub.values()) == 0:
        # 2do intento: súper estricto con JSON Schema exacto
        rub = await refetch_rubric_strict(image_b64)
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
    if isinstance(b, dict) and b.get("guess") is not None:
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

    data = await run_prompt(EVALUATION_PROMPT_ES.strip(), image_b64, EVALUATION_SCHEMA)

    rubric = await ensure_rubric(image_b64, data)
    health = await ensure_health(image_b64, data)
    breed  = await ensure_breed(image_b64, data)

    decision = data.get("decision") or {}
    gs = decision.get("global_score")
    if gs is None or gs == 0:
        try:
            gs = statistics.mean([v for v in rubric.values()]) if rubric else 0.0
        except:
            gs = 0.0
    decision.setdefault("global_score", round(gs, 1))
    decision.setdefault("decision_level", "CONSIDERAR_BAJO")
    decision.setdefault("decision_text", "")
    decision.setdefault("rationale", "")

    return {
        "engine": MODEL,
        "mode": mode,
        "category": category.strip().lower(),
        "rubric": rubric,
        "rubric_notes": data.get("rubric_notes") or {},
        "decision": decision,
        "health": health,
        "breed": breed,
        "lidar_metrics": None,
    }
