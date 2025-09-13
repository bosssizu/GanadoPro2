from __future__ import annotations

import os, json, base64, hashlib, asyncio, math, typing
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI

import prompts
import lidar

app = FastAPI(title="GanadoBravo IA v4.1 Pro")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.exception_handler(Exception)
async def _all_errors(request, exc):
    try:
        detail = str(exc)
    except Exception:
        detail = "unknown"
    return JSONResponse({"error": "server_error", "detail": detail}, status_code=200)
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Caches
RUBRIC_CACHE = {}
HEALTH_BREED_CACHE = {}

def _b64(b: bytes) -> str: return base64.b64encode(b).decode("utf-8")
def _norm_half_steps(x: float) -> float:
    x = max(0.0, min(10.0, float(x)))
    return round(x * 2.0) / 2.0

def coerce_health(obj: dict) -> dict:
    if isinstance(obj, dict) and isinstance(obj.get("health"), dict):
        h = obj["health"]
    else:
        h = {"flags": (obj or {}).get("flags", []), "notes": (obj or {}).get("notes", "")}
    if not isinstance(h.get("flags", []), list): h["flags"] = []
    if not isinstance(h.get("notes", ""), str): h["notes"] = str(h.get("notes", ""))
    return {"flags": h.get("flags", []), "notes": h.get("notes", "")}

def coerce_breed(obj: dict) -> dict:
    if isinstance(obj, dict) and isinstance(obj.get("breed"), dict):
        b = obj["breed"]
    else:
        b = {"guess": (obj or {}).get("guess", ""), "confidence": (obj or {}).get("confidence", 0)}
    guess = b.get("guess", "")
    try: conf = float(b.get("confidence", 0) or 0)
    except Exception: conf = 0.0
    conf = max(0.0, min(1.0, conf))
    if not isinstance(guess, str): guess = str(guess)
    return {"guess": guess, "confidence": conf}

def sha1(b: bytes) -> str: return hashlib.sha1(b).hexdigest()

CATEGORY_WEIGHTS = {
    "levante": {
        "Lomo": 0.13, "Aplomos (patas)": 0.13, "Línea dorsal": 0.11,
        "Grupo / muscling posterior": 0.11, "Conformación general": 0.09,
        "Angulación costillar": 0.07, "Ancho torácico": 0.08,
        "Profundidad de pecho": 0.06, "Condición corporal (BCS)": 0.08,
        "Inserción de cola": 0.08, "Balance anterior-posterior": 0.06
    },
    "engorde": {
        "Grupo / muscling posterior": 0.17, "Profundidad de pecho": 0.13,
        "Ancho torácico": 0.11, "Conformación general": 0.09,
        "Condición corporal (BCS)": 0.09, "Lomo": 0.09,
        "Línea dorsal": 0.08, "Aplomos (patas)": 0.08,
        "Angulación costillar": 0.06, "Inserción de cola": 0.04,
        "Balance anterior-posterior": 0.06
    },
    "vaca flaca": {
        "Lomo": 0.13, "Aplomos (patas)": 0.11, "Línea dorsal": 0.11,
        "Profundidad de pecho": 0.10, "Ancho torácico": 0.10,
        "Conformación general": 0.09, "Condición corporal (BCS)": 0.09,
        "Grupo / muscling posterior": 0.09, "Angulación costillar": 0.08,
        "Inserción de cola": 0.04, "Balance anterior-posterior": 0.06
    }
}
CATEGORY_OFFSETS = {"levante": 0.4, "vaca flaca": 0.8, "engorde": -0.3}

def weighted_score(rubric: dict, category: str) -> float:
    w = CATEGORY_WEIGHTS[category]
    s = 0.0
    for k, wt in w.items():
        s += float(rubric.get(k, 0.0)) * wt
    s = _norm_half_steps(s + CATEGORY_OFFSETS.get(category, 0.0))
    return s

def fallback_decision_from_score(gs: float):
    if gs >= 8.5: return "COMPRAR", "Excelente relación estructura/BCS para el objetivo."
    if gs >= 7.5: return "CONSIDERAR_ALTO", "Muy buen candidato; revisar precio y sanidad."
    if gs >= 6.0: return "CONSIDERAR_BAJO", "Aceptable, pero requiere manejo y precio competitivo."
    return "NO_COMPRAR", "Debilidades relevantes para el objetivo actual."

def adjust_from_lidar(category: str, m: dict) -> float:
    delta = 0.0
    try:
        girth = float(m.get("heart_girth_m", float('nan')))
        length = float(m.get("body_length_m", float('nan')))
        height = float(m.get("withers_height_m", float('nan')))
        stance = float(m.get("stance_asymmetry_idx", float('nan')))
        H_over_L = height/length if (height>0 and length>0) else float('nan')
        if category == "engorde":
            if (girth >= 1.90) and (length >= 1.70): delta += 0.5
        elif category == "levante":
            if (H_over_L >= 0.70 and H_over_L <= 0.80) and (not math.isfinite(stance) or stance <= 0.15): delta += 0.4
        elif category == "vaca flaca":
            if (length >= 1.60) and (height >= 1.25) and (not math.isfinite(girth) or girth < 1.85): delta += 0.3
    except Exception: pass
    delta = max(-1.0, min(1.0, delta))
    return _norm_half_steps(delta)

async def run_prompt(prompt: str, image_b64: str, schema: dict | None):
    content = [
        {"type": "text", "text": prompt},
        {"type": "input_image", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
    ]
    # Prefer Responses API if available
    use_responses = hasattr(client, "responses") and callable(getattr(getattr(client, "responses"), "create", None))
    if use_responses:
        kwargs = {
            "model": "gpt-4o-mini",
            "input": [{"role": "user", "content": content}],
            "temperature": 0,
        }
        if schema:
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "schema", "schema": schema, "strict": True},
            }
        else:
            kwargs["response_format"] = {"type": "json_object"}
        resp = await client.responses.create(**kwargs)
        try:
            out_text = resp.output_text
        except Exception:
            out_text = getattr(resp, "output", None) or ""
            if not out_text and hasattr(resp, "choices"):
                out_text = resp.choices[0].message.content
        return json.loads(out_text)

    # Fallback to Chat Completions
    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
        ]
    }]
    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0,
        response_format={"type": "json_object"},
    )
    txt = resp.choices[0].message.content
    return json.loads(txt)

@app.get("/")
async def root_index():
    return FileResponse("static/index.html")

@app.post("/api/evaluate")
async def evaluate(
    category: str = Form(...),
    file: UploadFile = File(...),
    pro: str | None = Form(None),
    mesh_file: UploadFile | None = File(None),
    meta_json: str | None = Form(None),
):
    try:
        category = category.strip().lower()
        if not os.getenv('OPENAI_API_KEY'):
            return {"error":"OPENAI_API_KEY no configurada en el servidor"}
        if category not in CATEGORY_WEIGHTS:
            return JSONResponse({"error":"Categoría inválida"}, status_code=400)

        img_bytes = await file.read()
        if len(img_bytes) < 1024:
            return JSONResponse({"error":"Imagen demasiado pequeña/corrupta"}, status_code=400)
        b64 = _b64(img_bytes)
        key = sha1(img_bytes)

        # Pro mode (optional)
        lidar_metrics = None
        if pro and mesh_file is not None:
            try:
                mesh_bytes = await mesh_file.read()
                meta = json.loads(meta_json) if meta_json else {}
                lidar_metrics = lidar.extract_lidar_metrics(mesh_bytes, mesh_file.filename, meta)
            except Exception as ex:
                lidar_metrics = {"error": str(ex)}

        # 1) Rubric (cache)
        rubric = RUBRIC_CACHE.get(key)
        if not rubric:
            r = await run_prompt(prompts.PROMPT_1, b64, prompts.RUBRIC_SCHEMA)
            rubric = r.get("rubric", {})
            # clamp & 0.5 steps
            normed = {}
            for k in prompts.RUBRIC_METRICS:
                try: v = float(rubric.get(k, 0.0))
                except Exception: v = 0.0
                normed[k] = _norm_half_steps(v)
            rubric = normed
            RUBRIC_CACHE[key] = rubric

        # 2) Salud + Raza (cache)
        hb = HEALTH_BREED_CACHE.get(key)
        if not hb:
            health_task = asyncio.create_task(run_prompt(prompts.PROMPT_4, b64, prompts.HEALTH_SCHEMA))
            breed_task  = asyncio.create_task(run_prompt(prompts.PROMPT_5,  b64, prompts.BREED_SCHEMA))
            res4, res5 = await asyncio.gather(health_task, breed_task)
            hb = {"health": coerce_health(res4), "breed": coerce_breed(res5)}
            HEALTH_BREED_CACHE[key] = hb

        # 3) Decisión
        prompt3 = (
            prompts.PROMPT_3.replace("{category}", category)
            + "\nRubric JSON:\n" + json.dumps({"rubric": rubric}, ensure_ascii=False)
            + ( "\nLIDAR JSON:\n" + json.dumps(lidar_metrics, ensure_ascii=False) if lidar_metrics else "" )
        )
        res3 = await run_prompt(prompt3, b64, None)

        global_score = float(res3.get("global_score", weighted_score(rubric, category)))
        global_score = _norm_half_steps(global_score)

        # Ajuste con LiDAR
        if isinstance(lidar_metrics, dict) and "error" not in lidar_metrics:
            global_score = _norm_half_steps(global_score + adjust_from_lidar(category, lidar_metrics))

        decision_level = res3.get("decision_level")
        decision_text  = res3.get("decision_text", "")
        rationale      = res3.get("rationale", "")
        if decision_level not in {"NO_COMPRAR","CONSIDERAR_BAJO","CONSIDERAR_ALTO","COMPRAR"}:
            dl, txt = fallback_decision_from_score(global_score)
            decision_level, decision_text = dl, txt
            if not rationale:
                rationale = "Ajustado automáticamente desde 'global_score' por pesos/offsets."

        return {
            "engine": "gpt-4o-mini",
            "mode": ("pro" if lidar_metrics else "standard"),
            "category": category,
            "rubric": rubric,
            "decision": {
                "global_score": global_score,
                "decision_level": decision_level,
                "decision_text": decision_text,
                "rationale": rationale
            },
            "health": hb["health"],
            "breed": hb["breed"],
            "lidar_metrics": lidar_metrics
        }
    except Exception as e:
        return {"error": str(e)}
