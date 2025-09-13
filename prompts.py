RUBRIC_SCHEMA = {
  "type":"object",
  "properties": {
    "rubric": {
      "type":"object",
      "properties": {
        "Lomo":{"type":"number"},
        "Aplomos (patas)":{"type":"number"},
        "Línea dorsal":{"type":"number"},
        "Grupo / muscling posterior":{"type":"number"},
        "Conformación general":{"type":"number"},
        "Angulación costillar":{"type":"number"},
        "Ancho torácico":{"type":"number"},
        "Profundidad de pecho":{"type":"number"},
        "Condición corporal (BCS)":{"type":"number"},
        "Inserción de cola":{"type":"number"}
      },
      "required": ["Lomo","Aplomos (patas)","Línea dorsal","Grupo / muscling posterior","Conformación general","Angulación costillar","Ancho torácico","Profundidad de pecho","Condición corporal (BCS)","Inserción de cola"]
    }
  },
  "required":["rubric"],
  "additionalProperties": False
}

PROMPT_1 = (
  "Evalúa morfología de bovino en 10 criterios de 0.0 a 10.0 con pasos de 0.5. "
  "Devuelve JSON en 'rubric' con esas claves exactas. Sé consistente y conservador. "
  "Considera estructura, masa muscular, BCS, y proporciones. NO agregues texto fuera del JSON."
)

PROMPT_3 = (
  "Decide para la categoría '{category}' -> devolverá JSON con: "
  "global_score (0-10), decision_level (NO_COMPRAR | CONSIDERAR_BAJO | CONSIDERAR_ALTO | COMPRAR), "
  "decision_text (breve) y rationale. Considera 'Rubric JSON' y opcionalmente 'LIDAR JSON' si está presente."
)

PROMPT_4 = (
  "Detecta banderas de salud (cojeras, lesiones, secreciones, pelaje irregular, costillas marcadas, etc.). "
  "Devuelve JSON {\"health\": {\"flags\": [...], \"notes\": \"...\"}}"
)

PROMPT_5 = (
  "Estima raza/mestizaje visible y confianza 0..1. Devuelve JSON {\"breed\": {\"guess\": \"\", \"confidence\": 0.0}}"
)
