"""Pase global: quita español metido en TITLE_EN y calcos típicos en TITLE_ES.

No reescribe descripciones ni flags (NO_LEGS / IS_SITTING).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
JSON_PATH = ROOT / "ejercicios.json"

EN_LEAKS = [
    (r"pesa rusa", "kettlebell"),
    (r"mancuerna", "dumbbell"),
    (r"dominada\s+down", "pulldown"),
    (r"dominada\s+over", "pullover"),
    (r"dominada\s+Ups", "pull-ups"),
    (r"dominada", "pull"),
    (r"\bespalda\b", "back"),
    (r"\bpecho\b", "chest"),
    (r"bíceps", "biceps"),
    (r"tríceps", "triceps"),
    (r"\bhombros\b", "shoulders"),
    (r"\bcuello\b", "neck"),
    (r"\bbarra\b", "barbell"),
    (r"glúteos", "glutes"),
    (r"isquiotibiales", "hamstrings"),
    (r"cuádriceps", "quads"),
]


def clean_en(text: str) -> str:
    s = text.strip()
    s = re.sub(r"^30 (?!\d|-|degree)", "", s, flags=re.I)
    s = re.sub(
        r"\b30 (shoulders|back|arms|chest|hombros|espalda|brazos|pecho)\s+",
        "",
        s,
        flags=re.I,
    )
    for pat, repl in EN_LEAKS:
        s = re.sub(pat, repl, s, flags=re.I)
    s = re.sub(r"\s+", " ", s).strip()
    if s:
        s = s[0].upper() + s[1:]
    return s


def polish_es(text: str) -> str:
    s = text
    s = re.sub(r"\b[Ff]ila invertida\b", "Remo invertido", s)
    s = re.sub(r"\b[Ff]ila de velocidad\b", "Remo de velocidad", s)
    s = re.sub(r"\b[Ff]ilas de cables\b", "Remos en polea", s)
    s = re.sub(r"\b[Ff]ila(s)?\b", "Remo", s)
    s = re.sub(r"\bsolo brazo\b", "un brazo", s, flags=re.I)
    s = re.sub(r"\bMosca inclinada\b", "Aperturas inclinadas", s, flags=re.I)
    s = re.sub(r"\bMosca de pecho\b", "Aperturas de pecho", s, flags=re.I)
    s = re.sub(r"\bDominada over\b", "Pullover", s, flags=re.I)
    s = re.sub(r"\bVolante de\b", "Aperturas de", s)
    s = re.sub(r"\bVolteo de\b", "Aperturas de", s)
    s = re.sub(r"\s+", " ", s).strip()
    if s:
        s = s[0].upper() + s[1:]
    return s


def main() -> None:
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    n_en = n_es = 0
    no_legs = 0
    for ej in data:
        if ej.get("NO_LEGS"):
            no_legs += 1
        en = ej.get("TITLE_EN") or ""
        es = ej.get("TITLE_ES") or ""
        new_en = clean_en(en)
        new_es = polish_es(es)
        if new_en != en:
            ej["TITLE_EN"] = new_en
            n_en += 1
        if new_es != es:
            ej["TITLE_ES"] = new_es
            n_es += 1
    JSON_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"OK TITLE_EN {n_en} | TITLE_ES {n_es} | NO_LEGS intactos {no_legs}")


if __name__ == "__main__":
    main()
