# prompts.py
JSON_GUARD = "IMPORTANTE: responde SOLO en json (application/json) sin texto adicional."
EVALUATION_PROMPT_ES = """
Eres un evaluador técnico de ganado. Analiza UNA imagen del animal.
Responde SOLO en json válido según el schema.

1) Rubrica morfológica (0–10, pasos 0.5) con nombres exactos:
"Condición corporal (BCS)","Conformación general","Línea dorsal","Angulación costillar",
"Profundidad de pecho","Aplomos (patas)","Lomo","Grupo / muscling posterior",
"Balance anterior–posterior","Ancho torácico","Inserción de cola"

2) Decisión por categoría (levante/vaca_flaca/engorde):
- "decision_level": {"CONSIDERAR_ALTO","CONSIDERAR_BAJO","DESCARTAR"}
- "global_score": 0–10
- "decision_text" y "rationale" breves

3) Salud — evalúa exactamente estas 9 banderas:
["lesion_cutanea","claudicacion","secrecion_nasal","conjuntivitis",
 "diarrea","dermatitis","lesion_de_pezuna","parasitos_externos","tos"]
Devuelve "flags": [] si no hay evidencias. Incluye "notes".

4) Raza (estimada): elige de
["Brahman","Nelore","Gyr","Girolando","Holstein","Jersey","Angus","Simmental","Cebú","Mestizo","Indeterminado"]
y pon "confidence" 0–1.

5) (Opcional) "rubric_notes": comentarios breves por métrica.
"""

RUBRIC_ONLY_PROMPT_ES = "Devuelve SOLO {\"rubric\":{...}} en json con las 11 métricas exactas."
STRICT_RUBRIC_PROMPT_ES = "Devuelve SOLO {\"rubric\":{...}} en json con las 11 métricas EXACTAS, valores 0–10 (0.5)."

EVALUATION_SCHEMA = {
    "type":"object",
    "additionalProperties": False,
    "properties": {
        "engine":{"type":"string"},
        "mode":{"type":"string"},
        "category":{"type":"string"},
        "rubric":{
            "type":"object","additionalProperties":False,
            "properties":{
                "Condición corporal (BCS)":{"type":"number"},
                "Conformación general":{"type":"number"},
                "Línea dorsal":{"type":"number"},
                "Angulación costillar":{"type":"number"},
                "Profundidad de pecho":{"type":"number"},
                "Aplomos (patas)":{"type":"number"},
                "Lomo":{"type":"number"},
                "Grupo / muscling posterior":{"type":"number"},
                "Balance anterior–posterior":{"type":"number"},
                "Ancho torácico":{"type":"number"},
                "Inserción de cola":{"type":"number"}
            },
            "required":[
                "Condición corporal (BCS)","Conformación general","Línea dorsal","Angulación costillar",
                "Profundidad de pecho","Aplomos (patas)","Lomo","Grupo / muscling posterior",
                "Balance anterior–posterior","Ancho torácico","Inserción de cola"
            ]
        },
        "rubric_notes":{"type":"object"},
        "decision":{
            "type":"object","additionalProperties":False,
            "properties":{
                "global_score":{"type":"number"},
                "decision_level":{"type":"string"},
                "decision_text":{"type":"string"},
                "rationale":{"type":"string"}
            },
            "required":["global_score","decision_level","decision_text","rationale"]
        },
        "health":{
            "type":"object","additionalProperties":False,
            "properties":{
                "flags":{"type":"array","items":{"type":"string"}},
                "notes":{"type":"string"}
            },
            "required":["flags","notes"]
        },
        "breed":{
            "type":"object","additionalProperties":False,
            "properties":{
                "guess":{"type":"string"},
                "confidence":{"type":"number","minimum":0,"maximum":1}
            },
            "required":["guess","confidence"]
        },
        "lidar_metrics":{"type":["object","null"]}
    },
    "required":["engine","mode","category","rubric","decision","health","breed"]
}
STRICT_RUBRIC_SCHEMA = {
    "type":"object","additionalProperties":False,
    "properties":{
        "rubric":{
            "type":"object","additionalProperties":False,
            "properties":{
                "Condición corporal (BCS)":{"type":"number"},
                "Conformación general":{"type":"number"},
                "Línea dorsal":{"type":"number"},
                "Angulación costillar":{"type":"number"},
                "Profundidad de pecho":{"type":"number"},
                "Aplomos (patas)":{"type":"number"},
                "Lomo":{"type":"number"},
                "Grupo / muscling posterior":{"type":"number"},
                "Balance anterior–posterior":{"type":"number"},
                "Ancho torácico":{"type":"number"},
                "Inserción de cola":{"type":"number"}
            },
            "required":[
                "Condición corporal (BCS)","Conformación general","Línea dorsal","Angulación costillar",
                "Profundidad de pecho","Aplomos (patas)","Lomo","Grupo / muscling posterior",
                "Balance anterior–posterior","Ancho torácico","Inserción de cola"
            ]
        }
    },
    "required":["rubric"]
}
