"""Pase de revisión: títulos cortados y fichas que hablan de otro ejercicio."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
JSON_PATH = ROOT / "ejercicios.json"

# id -> campos a forzar (los que viste en el HUD + cola "de la")
OVERRIDES: dict[int, dict] = {
    39: {
        "TITLE_ES": "Jab cruzado en V-sit con mancuernas",
        "DESC_ES": "Siéntate en V (cadera y torso en equilibrio), sujeta mancuernas y lanza jabs cruzados. Trabaja core y hombros; no es una sentadilla.",
        "DESC_EN": "Hold a V-sit, keep the hips off the floor, and throw cross jabs with dumbbells. Core and shoulders work; this is not a squat.",
    },
    40: {
        "TITLE_ES": "Spell caster con mancuernas",
        "DESC_ES": "De pie, lleva las mancuernas de un lado de la cadera hacia el lado contrario por encima de la cabeza, como un lanzamiento. Gira el torso; no es un curl de bíceps.",
        "DESC_EN": "Stand and sweep the dumbbells from one hip to the opposite side overhead. Rotate the torso; this is not a biceps curl.",
    },
    41: {
        "TITLE_ES": "Flexión lateral con mancuernas",
        "DESC_ES": "De pie, una mancuerna en una mano, inclina el torso hacia ese lado y vuelve al centro. Trabaja oblicuos. No es una sentadilla en V.",
        "DESC_EN": "Stand with a dumbbell in one hand, bend sideways toward that hand, and return tall. Obliques work. Not a V-squat.",
    },
    385: {
        "TITLE_ES": "Elevación de piernas",
        "DESC_ES": "Tumbado o colgado, eleva las piernas extendidas hacia el torso. Abdominales y flexores de cadera. No es un good morning.",
        "DESC_EN": "Lying or hanging, raise the straight legs toward the torso. Abs and hip flexors. Not a good morning.",
    },
    386: {
        "TITLE_ES": "Abdominales en banco declinado",
        "DESC_ES": "En banco declinado, flexiona el torso hacia las caderas. Es un crunch declinado, no un good morning.",
        "DESC_EN": "On a decline bench, curl the torso toward the hips. A decline crunch, not a good morning.",
    },
    394: {
        "TITLE_ES": "Remo invertido",
        "DESC_ES": "Bajo una barra, cuerpo en plancha invertida, tira el pecho hacia la barra. Es un remo con el propio peso, no un molino con pesa rusa.",
        "DESC_EN": "Hang under a bar in a reverse plank and pull the chest to the bar. A bodyweight row, not a kettlebell windmill.",
        "MUSCLE_ID": "mid_back",
        "BODYPART_EN": "Middle Back",
        "BODYPART_ES": "Espalda media",
    },
    396: {
        "TITLE_ES": "Rotación torácica en cuadrupedia",
        "DESC_ES": "A cuatro patas, una mano detrás de la cabeza, rota el codo hacia el techo y de vuelta al suelo. Movilidad de columna torácica.",
        "DESC_EN": "On all fours, one hand behind the head, rotate the elbow toward the ceiling and back down. Thoracic mobility.",
    },
    397: {
        "TITLE_ES": "Estiramiento de pectorales",
        "DESC_ES": "Abre el pecho (marco de puerta o suelo) hasta notar el pectoral. Es un estiramiento, no un abdominal.",
        "DESC_EN": "Open the chest (doorway or floor) until you feel the pecs. A stretch, not an abs drill.",
        "MUSCLE_ID": "chest_upper",
        "BODYPART_EN": "Chest",
        "BODYPART_ES": "Pecho",
    },
    398: {
        "TITLE_ES": "Estiramiento de dorsales",
        "DESC_ES": "Lleva un brazo por encima de la cabeza o agárrate a un soporte y estira el costado / dorsal. No es un abdominal.",
        "DESC_EN": "Reach overhead or hold a support and lengthen the side / lat. Not an abs crunch.",
        "MUSCLE_ID": "lats_back",
        "BODYPART_EN": "Lats",
        "BODYPART_ES": "Dorsales",
    },
    399: {
        "TITLE_ES": "Liberación con rodillo (foam roll)",
        "DESC_ES": "Pasa un rodillo de espuma por el tejido indicado. Es movilidad / recuperación, no un crunch.",
        "DESC_EN": "Roll a foam roller over the target tissue. Recovery work, not a crunch.",
    },
    400: {
        "TITLE_EN": "Foam roll lats",
        "TITLE_ES": "Rodillo de espuma para dorsales",
        "DESC_ES": "Con el rodillo, recorre el dorsal de axila a costilla. No es un abdominal.",
        "DESC_EN": "Roll along the lat from armpit to ribcage. Not an abs exercise.",
        "MUSCLE_ID": "lats_back",
        "BODYPART_EN": "Lats",
        "BODYPART_ES": "Dorsales",
    },
    401: {
        "TITLE_ES": "Estiramiento de aductores con balanceo",
        "DESC_ES": "En posición de sumo o rodilla al suelo, balancea el peso para abrir la ingle. Estiramiento de aductores.",
        "DESC_EN": "In a sumo or kneeling stance, rock the hips to open the groin. Adductor stretch.",
        "MUSCLE_ID": "hip_adductors",
        "BODYPART_EN": "Adductors",
        "BODYPART_ES": "Aductores",
    },
    402: {
        "TITLE_ES": "Bird-dog",
        "DESC_ES": "A cuatro patas, extiende el brazo contrario y la pierna contraria, y vuelve. Estabilidad de core; no es un salto.",
        "DESC_EN": "On all fours, reach the opposite arm and leg, then return. Core stability; not a jump.",
    },
    403: {
        "TITLE_ES": "Jumping jack (salto de tijera)",
        "DESC_ES": "De pie, abre piernas y brazos a la vez y vuelve. Es un jumping jack, no un salto de trampolín.",
        "DESC_EN": "Jump the feet out while the arms go overhead, then return. A jumping jack, not a trampoline drill.",
    },
    659: {
        "TITLE_ES": "Stir the pot en fitball (círculos en plancha)",
        "DESC_ES": "Antebrazos sobre el fitball, cuerpo en plancha, dibuja círculos con los codos. El core evita que la pelvis se mueva. No es una plancha lateral.",
        "DESC_EN": "Forearms on a stability ball, body in a plank, draw circles with the elbows. The core keeps the hips still. Not a side plank.",
    },
    726: {
        "TITLE_ES": "Curl de bíceps con barra de pie",
        "DESC_ES": "De pie, flexiona una barra hacia los hombros. Curl de bíceps, no un good morning.",
        "DESC_EN": "Stand and curl a barbell to the shoulders. A biceps curl, not a good morning.",
    },
    777: {
        "TITLE_ES": "Curl martillo",
        "DESC_ES": "Curl con mancuernas y agarre neutro, como si clavaras un clavo. Bíceps y braquial.",
        "DESC_EN": "Curl dumbbells with a neutral grip, as if swinging a hammer. Biceps and brachialis.",
    },
}

EN_DESC_LEAKS = [
    (r"pesa rusa", "kettlebell"),
    (r"mancuerna", "dumbbell"),
    (r"\bhombros\b", "shoulders"),
    (r"\bespalda\b", "back"),
    (r"bíceps", "biceps"),
    (r"tríceps", "triceps"),
    (r"cuádriceps", "quads"),
    (r"antebrazos", "forearms"),
    (r"calentamiento", "warmup"),
    (r"\bAvanzado\b", "advanced"),
    (r"Nivel recomendado", "Recommended level"),
]


def clean_desc_en(text: str) -> str:
    s = text
    for pat, repl in EN_DESC_LEAKS:
        s = re.sub(pat, repl, s, flags=re.I)
    return s


def polish_es_title(text: str) -> str:
    s = re.sub(r"\s+de la\s*$", "", text.strip(), flags=re.I)
    s = re.sub(r"\s+por la mañana\s*$", "", s, flags=re.I)
    return s


def soften_robot_desc(ej: dict) -> None:
    es = ej.get("DESC_ES") or ""
    if "La ficha describe este movimiento" not in es:
        return
    title = ej.get("TITLE_ES") or ej.get("TITLE_EN") or "Este ejercicio"
    body = (ej.get("BODYPART_ES") or "la zona indicada").lower()
    eq = ej.get("EQUIPMENT_ES") or "el propio cuerpo"
    if eq == "Cable":
        eq = "polea"
    ej["DESC_ES"] = f"{title}. Trabajo de {body} con {eq.lower()}."
    en_title = ej.get("TITLE_EN") or title
    ej["DESC_EN"] = f"{en_title}. {body} work with {eq.lower()}."


def main() -> None:
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    n = 0
    for ej in data:
        eid = int(ej.get("Unnamed: 0"))
        changed = False
        if eid in OVERRIDES:
            ej.update(OVERRIDES[eid])
            changed = True
        es = ej.get("TITLE_ES") or ""
        new_es = polish_es_title(es)
        if new_es != es:
            ej["TITLE_ES"] = new_es
            changed = True
        en_desc = ej.get("DESC_EN") or ""
        new_en_desc = clean_desc_en(en_desc)
        if new_en_desc != en_desc:
            ej["DESC_EN"] = new_en_desc
            changed = True
        before = ej.get("DESC_ES")
        soften_robot_desc(ej)
        if ej.get("DESC_ES") != before:
            changed = True
        if changed:
            n += 1
    JSON_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"OK review pass: {n} fichas")


if __name__ == "__main__":
    main()
