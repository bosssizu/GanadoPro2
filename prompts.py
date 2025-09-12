# prompts.py
# Spanish, concise, deterministic, JSON-only outputs

COMMON_INSTRUCTIONS = """Eres un experto en evaluación morfológica bovina. Responde **EXCLUSIVAMENTE** con JSON válido.
No incluyas texto fuera de JSON. Usa decimales (0.0–10.0) con paso de 0.5. No inventes métricas no solicitadas.
Si la imagen no permite ver algo, estima con cautela y explica en 'justification'.
"""

RUBRIC_SCHEMA = {
  "type": "object",
  "properties": {
    "rubric": {
      "type": "object",
      "properties": {
        "Condición corporal (BCS)": {"type":"number"},
        "Conformación general": {"type":"number"},
        "Línea dorsal": {"type":"number"},
        "Angulación costillar": {"type":"number"},
        "Profundidad de pecho": {"type":"number"},
        "Aplomos (patas)": {"type":"number"},
        "Lomo": {"type":"number"},
        "Grupo / muscling posterior": {"type":"number"},
        "Ancho torácico": {"type":"number"},
        "Inserción de cola": {"type":"number"}
      },
      "required": [
        "Condición corporal (BCS)","Conformación general","Línea dorsal","Angulación costillar",
        "Profundidad de pecho","Aplomos (patas)","Lomo","Grupo / muscling posterior","Ancho torácico","Inserción de cola"
      ],
      "additionalProperties": False
    },
    "justification": {"type":"string"}
  },
  "required": ["rubric","justification"],
  "additionalProperties": False
}

# PROMPT_1: Rubric
PROMPT_1 = COMMON_INSTRUCTIONS + """Analiza la morfología del bovino en la(s) imagen(es) y devuelve:
{
  "rubric": {<10 métricas con paso 0.5 entre 0.0 y 10.0>},
  "justification": "<máx 60 palabras con razones observables>"
}
Métricas EXACTAS: 
- Condición corporal (BCS); Conformación general; Línea dorsal; Angulación costillar; Profundidad de pecho;
- Aplomos (patas); Lomo; Grupo / muscling posterior; Ancho torácico; Inserción de cola
"""

# PROMPT_3: Decision per category
PROMPT_3 = COMMON_INSTRUCTIONS + """Con base en 'rubric' y en la categoría '{category}' (levante/engorde/vaca flaca),
calcula un 'global_score' 0.0–10.0 y una 'decision_level' en
{NO_COMPRAR, CONSIDERAR_BAJO, CONSIDERAR_ALTO, COMPRAR}. Devuelve:
{
  "global_score": <number>,
  "decision_level": "<one of>",
  "decision_text": "<máx 40 palabras>",
  "rationale": "<máx 60 palabras>"
}
Reglas guía:
- Levante: prioriza estructura fuerte (Lomo, Aplomos, Línea dorsal) y BCS funcional (≥5.0).
- Engorde: prioriza masa y caja torácica (Grupo posterior, Profundidad/Ancho torácico), BCS≥6.0.
- Vaca flaca: foco en potencial de recuperación (estructura ≥6.5, caja ≥6.0).
Aplica pesos coherentes y no inventes campos.
"""

# PROMPT_4: Health
PROMPT_4 = COMMON_INSTRUCTIONS + """Evalúa salud visible (cojera, lesiones, secreciones, condición del pelaje, parásitos, aspecto ocular/nasal).
Devuelve:
{ "health": { "flags": ["cojera","lesiones","secreciones","parásitos","pelaje_pobre"], "notes": "<máx 60 palabras>" } }
Incluye solo banderas observables.
"""

# PROMPT_5: Breed guess
PROMPT_5 = COMMON_INSTRUCTIONS + """Infiera la posible raza o cruces visibles (ej.: Brahman x, Cebuino, Holstein x, etc.). Devuelve:
{ "breed": { "guess": "<texto corto>", "confidence": 0.0–1.0 } }
Usa 'guess' vacío si no es posible.
"""

# Nota: el servidor puede adjuntar opcionalmente un bloque 'LIDAR JSON' con métricas físicas.
