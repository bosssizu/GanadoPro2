import os, base64, json
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from openai import AsyncOpenAI
from prompts import EVALUATION_PROMPT_ES, EVALUATION_SCHEMA

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")  # opcional
MODEL = os.getenv("MODEL_NAME", "gpt-4o-mini")

client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL) if OPENAI_BASE_URL else AsyncOpenAI(api_key=OPENAI_API_KEY)

app = FastAPI(title="GanadoBravo IA v4.2 (prompt único)")
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

    prompt = EVALUATION_PROMPT_ES.strip()
    data = await run_prompt(prompt=prompt, image_b64=image_b64, schema=EVALUATION_SCHEMA)

    data["engine"] = MODEL
    data["mode"] = mode
    data["category"] = category.strip().lower()

    data.setdefault("health", {"flags": [], "notes": ""})
    data.setdefault("breed", {"guess": "Indeterminado", "confidence": 0.0})
    data.setdefault("lidar_metrics", None)

    if isinstance(data.get("rubric"), dict):
        for k, v in list(data["rubric"].items()):
            try:
                data["rubric"][k] = float(_round05(float(v)))
            except Exception:
                data["rubric"][k] = 0.0

    allowed = {"lesion_cutanea","claudicacion","secrecion_nasal","conjuntivitis","diarrea","dermatitis","lesion_de_pezuna","parasitos_externos","tos"}
    flags = data.get("health", {}).get("flags", [])
    if not isinstance(flags, list): flags = []
    data["health"]["flags"] = [f for f in flags if f in allowed]

    return data
