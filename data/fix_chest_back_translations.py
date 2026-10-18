"""Lote pecho / espalda / polea: títulos y fichas con contexto de gym.

No toca NO_LEGS (ya curados en sentados).
No cambia IS_SITTING ni banderas.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
JSON_PATH = ROOT / "ejercicios.json"

ZONAS = {"chest_upper", "lats_back", "mid_back", "lower_back", "traps"}

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

# Frases largas primero. Se aplican sobre TITLE_EN ya limpio.
EN_TO_ES = [
    ("close-grip front lat pulldown", "Jalón al pecho frontal con agarre cerrado"),
    ("standing cable low-to-high twist", "Giro de pie en polea de abajo hacia arriba"),
    ("standing cable high-to-low twist", "Giro de pie en polea de arriba hacia abajo"),
    ("single-arm high-cable side bend", "Flexión lateral a un brazo en polea alta"),
    ("kneeling cable oblique crunch", "Crunch oblicuo de rodillas en polea"),
    ("kneeling cable crunch", "Crunch de rodillas en polea"),
    ("standing cable crunch", "Crunch de pie en polea"),
    ("standing cable wood chop", "Chop (leñador) de pie en polea"),
    ("cable reverse crunch", "Crunch inverso en polea"),
    ("cable judo flip", "Giro tipo judo en polea"),
    ("standing cable twist", "Giro de pie en polea"),
    ("cable rope crunch", "Crunch con cuerda en polea"),
    ("cable rope oblique crunch", "Crunch oblicuo con cuerda en polea"),
    ("cable pallof press", "Pallof press en polea"),
    ("bent-over reverse cable fly", "Aperturas inversas inclinado en polea"),
    ("lat pulldown", "Jalón al pecho"),
    ("straight-arm pulldown", "Jalón con brazos rectos"),
    ("straight-arm pullover", "Pullover a brazos rectos"),
    ("machine high row", "Remo alto en máquina"),
    ("shotgun row", "Remo shotgun (a un brazo en polea)"),
    ("elevated cable rows", "Remo elevado en polea"),
    ("scapular row", "Remo escapular"),
    ("renegade row", "Remo renegade"),
    ("seated cable", "sentado en polea"),
    ("cable chest fly", "Aperturas de pecho en polea"),
    ("cable fly", "Aperturas en polea"),
    ("cable crossover", "Crossover en polea"),
    ("cable row", "Remo en polea"),
    ("upright row", "Remo vertical"),
    ("face pull", "Face pull"),
    ("push-down", "Push-down"),
    ("pushdown", "Push-down"),
    ("bench press", "Press de banca"),
    ("chest press", "Press de pecho"),
    ("floor press", "Press en suelo"),
    ("incline press", "Press inclinado"),
    ("decline press", "Press declinado"),
    ("dumbbell flyes", "Aperturas con mancuernas"),
    ("dumbbell flye", "Aperturas con mancuernas"),
    ("dumbbell fly", "Aperturas con mancuernas"),
    ("chest fly", "Aperturas de pecho"),
    ("pullover", "Pullover"),
    ("deadlift", "Peso muerto"),
    ("good morning", "Buenos días"),
    ("back extension", "Extensión lumbar"),
    ("hyperextension", "Hiperextensión"),
    ("pull-up", "Dominada"),
    ("pull up", "Dominada"),
    ("chin-up", "Dominada supinada"),
    ("chin up", "Dominada supinada"),
    ("pulldown", "Jalón"),
    ("shrug", "Encogimiento de hombros"),
    ("wood chop", "Chop (leñador)"),
    ("woodchop", "Chop (leñador)"),
    ("pallof press", "Pallof press"),
    ("hammer curl", "Curl martillo"),
    ("preacher curl", "Curl predicador"),
    ("concentration curl", "Curl de concentración"),
    ("biceps curl", "Curl de bíceps"),
    ("cable curl", "Curl en polea"),
    ("push-up", "Flexión"),
    ("push up", "Flexión"),
    ("close-grip", "agarre cerrado"),
    ("wide-grip", "agarre ancho"),
    ("reverse-grip", "agarre inverso"),
    ("neutral-grip", "agarre neutro"),
    ("single-arm", "a un brazo"),
    ("one-arm", "a un brazo"),
    ("one arm", "a un brazo"),
    ("two-arm", "a dos brazos"),
    ("straight-arm", "brazos rectos"),
    ("bent-over", "inclinado"),
    ("bent over", "inclinado"),
    ("standing", "de pie"),
    ("kneeling", "de rodillas"),
    ("lying", "tumbado"),
    ("seated", "sentado"),
    ("incline", "inclinado"),
    ("decline", "declinado"),
    ("dumbbell", "mancuerna"),
    ("kettlebell", "pesa rusa"),
    ("barbell", "barra"),
    ("cable", "polea"),
    ("machine", "máquina"),
    ("band", "banda"),
    ("row", "remo"),
    ("flyes", "aperturas"),
    ("flye", "aperturas"),
    ("fly", "aperturas"),
    ("press", "press"),
    ("crunch", "crunch"),
    ("twist", "giro"),
    ("curl", "curl"),
]

PLACEHOLDER = re.compile(
    r"Ejercicio de tipo |Ejercicio enfocado en la zona |Strength exercise focused",
    re.I,
)


def en_lote(ej: dict) -> bool:
    if ej.get("NO_LEGS"):
        return False
    mid = ej.get("MUSCLE_ID") or ""
    eq = f"{ej.get('EQUIPMENT_EN')} {ej.get('EQUIPMENT_ES')}".lower()
    title = f"{ej.get('TITLE_EN')} {ej.get('TITLE_ES')}".lower()
    cable = any(x in eq or x in title for x in ("cable", "polea", "pulley"))
    remo = bool(re.search(r"\brow|\bpulldown|\bpullover|\blat pulldown", title))
    return mid in ZONAS or cable or remo


def clean_title_en(text: str) -> str:
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
    # Capitalizar primera letra si quedó en minúscula por el reemplazo
    if s:
        s = s[0].upper() + s[1:]
    return s


def translate_title_es(en: str) -> str:
    s = en
    for src, dst in EN_TO_ES:
        pat = re.escape(src)
        if " " not in src:
            pat = rf"\b{pat}\b"
        s = re.sub(pat, dst, s, flags=re.I)
    s = re.sub(r"\s+", " ", s).strip(" -")
    s = s.replace(" - variación", "").replace(" - variation", "")
    if s:
        s = s[0].upper() + s[1:]
    return s


def polish_existing_es(es: str) -> str:
    s = es
    s = re.sub(r"^30 repeticiones de ", "", s, flags=re.I)
    s = re.sub(r"^30 (abdominales|cables|brazos|ejercicios)\b", r"\1", s, flags=re.I)
    s = re.sub(r"\b[Ff]ilas de cables\b", "Remos en polea", s)
    s = re.sub(r"\b[Ff]ila alta\b", "Remo alto", s)
    s = re.sub(r"\b[Ff]ila de escopetas\b", "Remo shotgun", s)
    s = re.sub(r"\b[Ff]ilas escapulares\b", "Remos escapulares", s)
    s = re.sub(r"\b[Ff]ila invertida\b", "Remo invertido", s)
    s = re.sub(r"\b[Ff]ila de velocidad\b", "Remo de velocidad", s)
    s = re.sub(r"\b[Ff]ila(s)?\b", "Remo", s)
    s = re.sub(r"\bsolo brazo\b", "un brazo", s, flags=re.I)
    s = re.sub(r"\bVolante de\b", "Aperturas de", s)
    s = re.sub(r"\bVolteo de\b", "Aperturas de", s)
    s = re.sub(r"\bMosca de pecho\b", "Aperturas de pecho", s, flags=re.I)
    s = re.sub(r"\bMosca inclinada\b", "Aperturas inclinadas", s, flags=re.I)
    s = re.sub(r"\bDominada over\b", "Pullover", s, flags=re.I)
    s = re.sub(r" press de banca con mancuernas por la mañana", "Press de banca con mancuernas", s, flags=re.I)
    s = re.sub(r" por la mañana\b", "", s, flags=re.I)
    s = re.sub(r"^Pec Dec$", "Aperturas en máquina (pec-deck)", s, flags=re.I)
    s = re.sub(r"^Pallof press with rotation$", "Pallof press con rotación", s, flags=re.I)
    s = re.sub(r"\bJersey de\b", "Pullover de", s, flags=re.I)
    s = re.sub(r"\bRizador de cable\b", "Curl en polea", s, flags=re.I)
    s = re.sub(r"\bRizado de cable\b", "Curl en polea", s, flags=re.I)
    s = re.sub(r"\bCable de compresión inversa\b", "Crunch inverso en polea", s, flags=re.I)
    s = re.sub(r"\bPrensa pallof de 30 cables\b", "Pallof press en polea", s, flags=re.I)
    s = re.sub(r"\bPrensa de cuello\b", "Press de cuello (guillotina)", s, flags=re.I)
    s = re.sub(r"\bWoodchopper\b", "Chop (leñador)", s, flags=re.I)
    s = re.sub(r"\bcon cable\b", "en polea", s, flags=re.I)
    s = re.sub(r"\bde cable\b", "en polea", s, flags=re.I)
    s = re.sub(r"^Cable ", "Polea: ", s)
    s = re.sub(r"\bcable\b", "polea", s)
    s = re.sub(r"\s+", " ", s).strip(" -")
    if s:
        s = s[0].upper() + s[1:]
    return s


def es_roto(es: str) -> bool:
    return bool(
        re.search(
            r"\bFila|\bVolante|\bVolteo|\bMosca|\bJersey |\bRizado|\bRizador|Dominada over|"
            r"^Cable |compresión inversa|solo brazo|Prensa pallof|30 brazos|"
            r"retorcido|Banda rusin|aéreo rizado",
            es,
            re.I,
        )
    )


def desc_es_para(ej: dict, title_es: str) -> str:
    old = ej.get("DESC_ES") or ""
    body = ej.get("BODYPART_ES") or "la zona indicada"
    eq = ej.get("EQUIPMENT_ES") or ej.get("EQUIPMENT_EN") or "el propio cuerpo"
    if eq == "Cable":
        eq = "polea"
    pie = ""
    blob = f"{ej.get('TITLE_EN')} {title_es}".lower()
    if any(x in blob for x in ("de pie", "standing")):
        pie = " Se realiza de pie, no sentado."
    elif any(x in blob for x in ("de rodillas", "kneeling")):
        pie = " Se realiza de rodillas."
    nuevo = (
        f"{title_es}. Trabajo de {body.lower()} con {eq.lower()}.{pie} "
        "La ficha describe este movimiento, no otro ejercicio del catálogo."
    )
    if PLACEHOLDER.search(old) or es_roto(old[:80]):
        return nuevo.strip()
    # Si el título habla de remo/jalón y el texto de un press de banca, reescribir
    t = title_es.lower()
    d = old.lower()
    if ("remo" in t or "jalón" in t or "apertura" in t) and (
        "press de banca" in d or "elevación de gemelos" in d or "sentadilla" in d
    ):
        return nuevo.strip()
    if "crunch" in t and "press de banca" in d:
        return nuevo.strip()
    return old


def desc_en_para(ej: dict, title_en: str, desc_es: str) -> str:
    old = ej.get("DESC_EN") or ""
    if PLACEHOLDER.search(old) or "Ejercicio enfocado" in old:
        return f"{title_en}. Matches the Spanish card: {desc_es[:180]}"
    return old


def main() -> None:
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    n = 0
    for ej in data:
        if not en_lote(ej):
            continue
        old_en = ej.get("TITLE_EN") or ""
        old_es = ej.get("TITLE_ES") or ""
        new_en = clean_title_en(old_en)
        new_es = polish_existing_es(old_es)
        if es_roto(new_es) or new_es.lower() == old_en.lower():
            new_es = translate_title_es(new_en)
        if re.search(r"\bdecline\b", new_en, re.I) and re.search(r"inclinad", new_es, re.I):
            new_es = translate_title_es(new_en)
        if re.search(r"\bincline\b", new_en, re.I) and re.search(r"declin", new_es, re.I):
            new_es = translate_title_es(new_en)
        if ej.get("EQUIPMENT_EN") == "Cable":
            ej["EQUIPMENT_ES"] = "Polea"
        changed = new_en != old_en or new_es != old_es
        ej["TITLE_EN"] = new_en
        ej["TITLE_ES"] = new_es
        new_desc_es = desc_es_para(ej, new_es)
        if new_desc_es != (ej.get("DESC_ES") or ""):
            ej["DESC_ES"] = new_desc_es
            ej["DESC_EN"] = desc_en_para(ej, new_en, new_desc_es)
            changed = True
        if changed:
            n += 1
    JSON_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"OK {JSON_PATH.name}: {n} fichas del lote pecho/espalda/polea")


if __name__ == "__main__":
    main()
