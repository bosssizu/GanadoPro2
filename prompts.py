# prompts.py
JSON_GUARD = "IMPORTANTE: responde SOLO en json (application/json) sin texto adicional."

EVALUATION_PROMPT_ES = """
Eres un evaluador técnico de ganado de carne/leche. Analiza UNA sola imagen del animal.
Responde SOLO en json válido según el schema. Usa valores estables (determinista; NO inventes).

1) Rubrica morfológica (0–10, pasos de 0.5) con estos nombres exactos:
- "Condición corporal (BCS)"
- "Conformación general"
- "Línea dorsal"
- "Angulación costillar"
- "Profundidad de pecho"
- "Aplomos (patas)"
- "Lomo"
- "Grupo / muscling posterior"
- "Balance anterior–posterior"
- "Ancho torácico"
- "Inserción de cola"

2) Decisión por categoría (levante / vaca_flaca / engorde), con racional:
- "decision_level" ∈ { "CONSIDERAR_ALTO", "CONSIDERAR_BAJO", "DESCARTAR" }
- "global_score" 0–10 (coherente con la rúbrica, puede ser el promedio)
- "decision_text" breve
- "rationale" breve

3) Salud — evalúa EXPLÍCITAMENTE cada una de estas 9 banderas y marca solo si ves evidencia:
   ["lesion_cutanea","claudicacion","secrecion_nasal","conjuntivitis",
    "diarrea","dermatitis","lesion_de_pezuna","parasitos_externos","tos"]
   Devuelve "flags": [] si no hay evidencias. Incluye "notes" (o "").

4) Raza (estimada) — elige la más probable (mejor esfuerzo) de:
   ["Brahman","Nelore","Gyr","Girolando","Holstein","Jersey","Angus","Simmental","Cebú","Mestizo","Indeterminado"]
   Si la evidencia es baja, puedes usar "Mestizo" o "Indeterminado"; ajusta "confidence" (0–1) en consecuencia.

5) (Opcional) Comentarios por métrica en "rubric_notes": frases muy breves (≤12 palabras).

Reglas:
- No inventes: si algo no se ve, no lo marques.
- Métricas medias ~5–7 si la imagen es aceptable; extremos solo con evidencia clara.
- Devuelve EXACTAMENTE las claves pedidas, sin extras.
"""

RUBRIC_ONLY_PROMPT_ES = """
Devuelve SOLO {"rubric":{...}} en json con las 11 métricas (0–10, pasos 0.5) y nombres exactos.
Responde en json puro sin texto adicional.
"""

# Súper estricto: fuerza EXACTAMENTE las 11 claves españolas y solo números.
STRICT_RUBRIC_PROMPT_ES = """
Devuelve SOLO {"rubric":{...}} en json con las 11 métricas y ESTOS nombres exactos (sin variantes):
"Condición corporal (BCS)","Conformación general","Línea dorsal","Angulación costillar","Profundidad de pecho",
"Aplomos (patas)","Lomo","Grupo / muscling posterior","Balance anterior–posterior","Ancho torácico","Inserción de cola".
Cada valor debe ser un número (0 a 10) con incrementos de 0.5. No incluyas texto adicional.
"""

HEALTH_ONLY_PROMPT_ES = """
Devuelve SOLO {"health":{"flags":[...],"notes":""}} en json evaluando las 9 banderas indicadas.
Responde en json puro sin texto adicional.
"""

BREED_ONLY_PROMPT_ES = """
Devuelve SOLO {"breed":{"guess":"...","confidence":0-1}} en json seleccionando la raza más probable de la lista dada.
Responde en json puro sin texto adicional.
"""

EVALUATION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "engine": {"type": "string"},
        "mode": {"type": "string"},
        "category": {"type": "string"},
        "rubric": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "Condición corporal (BCS)": {"type": "number"},
                "Conformación general": {"type": "number"},
                "Línea dorsal": {"type": "number"},
                "Angulación costillar": {"type": "number"},
                "Profundidad de pecho": {"type": "number"},
                "Aplomos (patas)": {"type": "number"},
                "Lomo": {"type": "number"},
                "Grupo / muscling posterior": {"type": "number"},
                "Balance anterior–posterior": {"type": "number"},
                "Ancho torácico": {"type": "number"},
                "Inserción de cola": {"type": "number"},
            },
            "required": [
                "Condición corporal (BCS)","Conformación general","Línea dorsal","Angulación costillar",
                "Profundidad de pecho","Aplomos (patas)","Lomo","Grupo / muscling posterior",
                "Balance anterior–posterior","Ancho torácico","Inserción de cola"
            ],
        },
        "rubric_notes": {"type":"object", "additionalProperties": True},
        "decision": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "global_score": {"type": "number"},
                "decision_level": {"type": "string","enum": ["CONSIDERAR_ALTO","CONSIDERAR_BAJO","DESCARTAR"]},
                "decision_text": {"type": "string"},
                "rationale": {"type": "string"},
            },
            "required": ["global_score", "decision_level", "decision_text", "rationale"],
        },
        "health": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "flags": {
                    "type": "array",
                    "items": {"type": "string","enum": [
                        "lesion_cutanea","claudicacion","secrecion_nasal","conjuntivitis",
                        "diarrea","dermatitis","lesion_de_pezuna","parasitos_externos","tos"
                    ]},
                },
                "notes": {"type": "string"},
            },
            "required": ["flags", "notes"],
        },
        "breed": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "guess": {"type": "string"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            },
            "required": ["guess", "confidence"],
        },
        "lidar_metrics": {"type": ["object", "null"]},
    },
    "required": ["engine", "mode", "category", "rubric", "decision", "health", "breed"],
}

STRICT_RUBRIC_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "rubric": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "Condición corporal (BCS)": {"type": "number", "minimum": 0, "maximum": 10},
                "Conformación general": {"type": "number", "minimum": 0, "maximum": 10},
                "Línea dorsal": {"type": "number", "minimum": 0, "maximum": 10},
                "Angulación costillar": {"type": "number", "minimum": 0, "maximum": 10},
                "Profundidad de pecho": {"type": "number", "minimum": 0, "maximum": 10},
                "Aplomos (patas)": {"type": "number", "minimum": 0, "maximum": 10},
                "Lomo": {"type": "number", "minimum": 0, "maximum": 10},
                "Grupo / muscling posterior": {"type": "number", "minimum": 0, "maximum": 10},
                "Balance anterior–posterior": {"type": "number", "minimum": 0, "maximum": 10},
                "Ancho torácico": {"type": "number", "minimum": 0, "maximum": 10},
                "Inserción de cola": {"type": "number", "minimum": 0, "maximum": 10},
            },
            "required": [
                "Condición corporal (BCS)","Conformación general","Línea dorsal","Angulación costillar",
                "Profundidad de pecho","Aplomos (patas)","Lomo","Grupo / muscling posterior",
                "Balance anterior–posterior","Ancho torácico","Inserción de cola"
            ],
        }
    },
    "required": ["rubric"]
}
