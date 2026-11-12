"""Clasificador por léxico con negación (compartido por mapper y por validación)."""
import re

POSITIVE = {"bueno", "excelente", "genial", "fantástico", "increíble", "perfecto", "rápido", "útil",
            "bien", "encantó", "recomiendo"}
NEGATIVE = {"malo", "terrible", "horrible", "pésimo", "lento", "defectuoso", "decepcionante", "frágil"}
NEGATORS = {"no", "nunca", "tampoco", "nada", "ni"}
TOKEN = re.compile(r"[a-záéíóúñü]+")


def classify(text):
    toks = TOKEN.findall(text.lower())
    score = 0
    for i, t in enumerate(toks):
        s = 1 if t in POSITIVE else -1 if t in NEGATIVE else 0
        if s and any(x in NEGATORS for x in toks[max(0, i - 2):i]):
            s = -s                      # negación en las 2 palabras previas invierte la polaridad
        score += s
    return "positivo" if score > 0 else "negativo" if score < 0 else "neutral"
