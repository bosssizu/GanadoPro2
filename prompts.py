# prompts.py
EVALUATION_PROMPT_ES = """
Eres un evaluador técnico de ganado de carne/leche. Analiza UNA sola imagen del animal.
Responde SOLO en JSON válido según el schema. Usa valores estables (determinista; NO inventes).

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
Devuelve SOLO {"rubric":{...}} con las 11 métricas numéricas (0–10, pasos 0.5) y nombres exactos.
"""

HEALTH_ONLY_PROMPT_ES = """
Devuelve SOLO {"health":{"flags":[...],"notes":""}} evaluando las 9 banderas indicadas.
"""

BREED_ONLY_PROMPT_ES = """
Devuelve SOLO {"breed":{"guess":"...","confidence":0-1}} seleccionando la raza más probable de la lista dada.
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
