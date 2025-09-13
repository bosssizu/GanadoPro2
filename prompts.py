# -*- coding: utf-8 -*-

RUBRIC_METRICS = ['Condición corporal (BCS)', 'Conformación general', 'Línea dorsal', 'Angulación costillar', 'Profundidad de pecho', 'Aplomos (patas)', 'Lomo', 'Grupo / muscling posterior', 'Balance anterior-posterior', 'Ancho torácico', 'Inserción de cola']

RUBRIC_SCHEMA = {
  "type": "object",
  "properties": {
    "rubric": {
      "type": "object",
      "properties": {'Condición corporal (BCS)': {"type": "number"}, 'Conformación general': {"type": "number"}, 'Línea dorsal': {"type": "number"}, 'Angulación costillar': {"type": "number"}, 'Profundidad de pecho': {"type": "number"}, 'Aplomos (patas)': {"type": "number"}, 'Lomo': {"type": "number"}, 'Grupo / muscling posterior': {"type": "number"}, 'Balance anterior-posterior': {"type": "number"}, 'Ancho torácico': {"type": "number"}, 'Inserción de cola': {"type": "number"}},
      "required": ['Condición corporal (BCS)', 'Conformación general', 'Línea dorsal', 'Angulación costillar', 'Profundidad de pecho', 'Aplomos (patas)', 'Lomo', 'Grupo / muscling posterior', 'Balance anterior-posterior', 'Ancho torácico', 'Inserción de cola']
    }
  },
  "required": ["rubric"],
  "additionalProperties": False
}

HEALTH_SCHEMA = {
  "type": "object",
  "properties": {
    "health": {
      "type": "object",
      "properties": {
        "flags": {"type": "array", "items": {"type": "string"}},
        "notes": {"type": "string"}
      },
      "required": ["flags", "notes"]
    }
  },
  "required": ["health"],
  "additionalProperties": False
}

BREED_SCHEMA = {
  "type": "object",
  "properties": {
    "breed": {
      "type": "object",
      "properties": {
        "guess": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1}
      },
      "required": ["guess", "confidence"]
    }
  },
  "required": ["breed"],
  "additionalProperties": False
}

PROMPT_1 = (
  "Evalúa morfología de un bovino en 11 métricas de 0.0 a 10.0 (pasos de 0.5). "
  "Usa EXCLUSIVAMENTE estas claves y devuélvelas en JSON bajo 'rubric': "
  "Condición corporal (BCS), Conformación general, Línea dorsal, Angulación costillar, Profundidad de pecho, Aplomos (patas), Lomo, Grupo / muscling posterior, Balance anterior-posterior, Ancho torácico, Inserción de cola. "
  "Sé consistente y conservador. No agregues texto fuera del JSON."
)

PROMPT_3 = (
  "Con base en la rúbrica (0–10 por métrica) y la categoría '{category}', "
  "devuelve JSON con: global_score (0–10), decision_level "
  "(NO_COMPRAR | CONSIDERAR_BAJO | CONSIDERAR_ALTO | COMPRAR), "
  "decision_text (breve) y rationale. Considera 'Rubric JSON' y, si existe, 'LIDAR JSON'."
)

PROMPT_4 = (
  "Detecta banderas de salud visibles (cojeras, lesiones, secreciones, problemas respiratorios, costillas marcadas, "
  "parásitos, heridas, inflamaciones, pelaje irregular, etc.). "
  "Devuelve estrictamente el JSON con la forma del esquema HEALTH_SCHEMA."
)

PROMPT_5 = (
  "Estima la raza o mestizaje más probable visible y la confianza 0..1 (float). "
  "Devuelve estrictamente el JSON con la forma del esquema BREED_SCHEMA."
)
