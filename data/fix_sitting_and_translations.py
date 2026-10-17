"""Corrige sentados, poleas sentadas y traducciones de ficha.

IS_SITTING = se hace sentado (banco, máquina o silla).
NO_LEGS    = el tren inferior no es el motor; usable desde silla / silla de ruedas
             (aproximación de catálogo, no criterio médico).
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
JSON_PATH = ROOT / "ejercicios.json"

# id -> dict de campos a sobreescribir
FIXES: dict[int, dict] = {}


def add(
    eid: int,
    title_en: str,
    title_es: str,
    desc_en: str,
    desc_es: str,
    sitting: bool,
    no_legs: bool,
    equipment_es: str | None = None,
) -> None:
    row = {
        "TITLE_EN": title_en,
        "TITLE_ES": title_es,
        "DESC_EN": desc_en,
        "DESC_ES": desc_es,
        "IS_SITTING": sitting,
        "NO_LEGS": no_legs,
    }
    if equipment_es is not None:
        row["EQUIPMENT_ES"] = equipment_es
    FIXES[eid] = row


# --- Abdominales / core ---
add(
    13,
    "Seated bar twist",
    "Giro de torso sentado con barra",
    "Sit tall holding a barbell across the upper back or in front of the chest and rotate the torso from side to side. The work is in the obliques; the hips stay planted on the bench.",
    "Siéntate erguido con una barra sobre la parte alta de la espalda o delante del pecho y gira el torso de un lado a otro. Trabajan los oblicuos; las caderas se quedan en el banco.",
    True,
    True,
)
add(
    58,
    "Seated dumbbell leg tuck",
    "Elevación de rodillas sentado con mancuerna",
    "Sit on the edge of a bench holding a dumbbell at the chest or between the feet and tuck the knees toward the torso. This is a seated hip-flexor and abs drill that still uses the legs.",
    "Siéntate al borde del banco con una mancuerna al pecho o entre los pies y lleva las rodillas hacia el torso. Es un trabajo de flexores de cadera y abdomen que sí usa las piernas.",
    True,
    False,
)
add(
    66,
    "Weighted seated killer abs to Russian twist",
    "Abdominales sentados con peso y giro ruso",
    "Sit with the torso leaned back, hold a dumbbell at the chest for crunch-style abs, then rotate side to side (Russian twist). Stay seated; do not stand between reps.",
    "Siéntate con el torso reclinado, sujeta una mancuerna al pecho para el trabajo de abdomen y luego gira de lado a lado (giro ruso). Permanece sentado; no te pongas de pie entre repeticiones.",
    True,
    True,
)
add(
    95,
    "Captain's chair knee raise",
    "Elevación de rodillas en silla de capitán",
    "Support yourself on the captain's chair pads, hang with the torso tall, and raise the knees toward the chest. This is a hanging core movement, not a seated exercise.",
    "Apóyate en los pads de la silla de capitán, cuelga con el torso erguido y sube las rodillas al pecho. Es un movimiento de core colgado, no un ejercicio sentado.",
    False,
    False,
)
add(
    104,
    "Captain's chair leg raise",
    "Elevación de piernas en silla de capitán",
    "On the captain's chair, keep the legs straight and raise them until they approach horizontal. Hip flexors and abs work; you are hanging, not sitting.",
    "En la silla de capitán, mantén las piernas extendidas y elévalas hasta acercarlas a la horizontal. Trabajan flexores de cadera y abdomen; estás colgado, no sentado.",
    False,
    False,
)
add(
    112,
    "Seated twist with PVC pipe",
    "Giro de torso sentado con tubo de PVC",
    "Sit upright with a PVC pipe across the upper back and rotate the ribcage left and right. A simple seated oblique drill.",
    "Siéntate erguido con un tubo de PVC sobre la parte alta de la espalda y gira la caja torácica a izquierda y derecha. Un trabajo sencillo de oblicuos sentado.",
    True,
    True,
)
add(
    143,
    "Seated killer abs overhead press",
    "Abdominales sentados con press por encima de la cabeza",
    "From a seated lean-back position, brace the core and press a light load overhead. The abs stay tight so the lower back does not dump.",
    "Desde una posición sentada reclinada, activa el core y empuja una carga ligera por encima de la cabeza. El abdomen se mantiene firme para no hundir la lumbar.",
    True,
    True,
)
add(
    161,
    "Cable seated crunch",
    "Crunch sentado en polea",
    "Sit facing away from a high pulley, hold the rope behind the head, and crunch the ribcage toward the pelvis. Fully seated cable core work.",
    "Siéntate de espaldas a una polea alta, sujeta la cuerda detrás de la cabeza y lleva las costillas hacia la pelvis. Trabajo de core en polea totalmente sentado.",
    True,
    True,
    "Polea",
)
add(
    224,
    "Seated overhead stretch",
    "Estiramiento sentado por encima de la cabeza",
    "Sit tall and reach both arms overhead, lengthening the sides of the torso. A chair-friendly stretch, not a loaded lift.",
    "Siéntate erguido y estira ambos brazos por encima de la cabeza, alargando los laterales del torso. Un estiramiento usable en silla, no un levantamiento con carga.",
    True,
    True,
)
add(
    226,
    "Seated scissor kick",
    "Tijeras de piernas sentado",
    "Sit on the floor or a bench, lean the torso back, and scissor the legs. Abs work, but the legs are the moving parts.",
    "Siéntate en el suelo o en un banco, reclina el torso y abre y cierra las piernas en tijera. Trabaja el abdomen, pero las piernas son lo que se mueve.",
    True,
    False,
)
add(
    294,
    "Seated leg lift",
    "Elevación de piernas sentado",
    "Sit tall and lift one or both legs off the floor by flexing the hips. A seated abs drill that still trains the legs.",
    "Siéntate erguido y eleva una o ambas piernas flexionando las caderas. Un abdominal sentado que sigue entrenando las piernas.",
    True,
    False,
)
add(
    310,
    "Roman chair side bend",
    "Flexión lateral en silla romana",
    "On a Roman chair or hyperextension bench, lock the hips and bend sideways to train the obliques. You are braced on the pad, not sitting in a chair.",
    "En una silla romana o banco de hiperextensiones, fija las caderas y flexiona el torso hacia el lado para trabajar oblicuos. Vas sujeto al pad, no sentado en una silla.",
    False,
    False,
)
add(
    350,
    "Seated twist",
    "Giro de torso sentado",
    "Sit with the chest up and rotate the torso left and right. No equipment; the hips stay on the seat.",
    "Siéntate con el pecho alto y gira el torso a izquierda y derecha. Sin equipo; las caderas se quedan en el asiento.",
    True,
    True,
)
add(
    453,
    "Seated pike",
    "Pike sentado (abdominales en V)",
    "Sit on the floor, keep the legs straight, and fold the torso toward the thighs. Strong hip-flexor and abs demand; the legs are active.",
    "Siéntate en el suelo, mantén las piernas extendidas y lleva el torso hacia los muslos. Exige flexores de cadera y abdomen; las piernas están activas.",
    True,
    False,
)
add(
    497,
    "Seated knee tuck in series",
    "Serie de encogimientos de rodilla sentado",
    "Sit and repeatedly tuck the knees toward the chest in a series. Core work that still uses the legs.",
    "Siéntate y acerca las rodillas al pecho de forma repetida en serie. Trabajo de core que sigue usando las piernas.",
    True,
    False,
)
add(
    513,
    "Seated killer abs",
    "Abdominales sentados (killer abs)",
    "Sit with a slight lean, brace the midsection, and pulse or hold the torso. Stay on the seat; this version is trunk-focused.",
    "Siéntate con una ligera reclina, activa el centro y pulsa o mantén el torso. Quédate en el asiento; esta versión se centra en el tronco.",
    True,
    True,
)
add(
    575,
    "Alternating sit-through with crunch",
    "Sit-through alternado con crunch",
    "From a quadruped or crab position, thread one leg through to the opposite side, then add a crunch. It is a ground transition, not a seated lift.",
    "Desde cuadrupedia o posición de cangrejo, pasa una pierna al lado contrario y añade un crunch. Es una transición en el suelo, no un ejercicio sentado.",
    False,
    False,
)
add(
    1616,
    "Spine twist",
    "Giro de columna sentado (spine twist)",
    "Sit tall, often with the legs extended in a Pilates setup, and rotate the spine. The classic seated version can be done in a chair without kicking the legs.",
    "Siéntate erguido, a menudo con las piernas extendidas en estilo Pilates, y rota la columna. La versión clásica sentada también se puede hacer en silla sin patear las piernas.",
    True,
    True,
)

# --- Bíceps ---
add(711, "Seated close-grip concentration barbell curl", "Curl de concentración sentado con barra y agarre cerrado",
    "Sit and brace the upper arms; curl a barbell with a close grip. A seated isolation curl, not a standing cheat curl.",
    "Siéntate y fija los brazos; flexiona una barra con agarre cerrado. Un curl de aislamiento sentado, no un curl de pie con impulso.", True, True)
add(716, "Seated wide-grip curl to close-grip curl", "Curl sentado de agarre ancho a agarre cerrado",
    "Sit and curl a barbell, changing from a wide grip to a close grip between sets or reps. Both positions stay seated.",
    "Siéntate y haz curl con barra, pasando de agarre ancho a cerrado entre series o repeticiones. Ambas posiciones se mantienen sentadas.", True, True)
add(717, "Seated straight-bar curl superset", "Superserie de curl con barra recta sentado",
    "Sit and curl a straight bar, then immediately follow with a second biceps movement without standing up.",
    "Siéntate y haz curl con barra recta; encadena enseguida un segundo movimiento de bíceps sin ponerte de pie.", True, True)
add(725, "Seated barbell curl", "Curl de bíceps con barra sentado",
    "Sit on a bench and curl a barbell. Sitting reduces lower-body drive compared with a standing curl.",
    "Siéntate en un banco y flexiona una barra. Ir sentado reduce el impulso de las piernas respecto al curl de pie.", True, True)
add(744, "Seated dumbbell biceps curl", "Curl de bíceps con mancuernas sentado",
    "Sit upright and curl a pair of dumbbells, palms up. Keep the elbows by the ribs.",
    "Siéntate erguido y flexiona un par de mancuernas con las palmas arriba. Los codos se quedan junto a las costillas.", True, True)
add(752, "Seated dumbbell inner biceps curl", "Curl de bíceps interno sentado con mancuernas",
    "Sit and curl the dumbbells with a path that emphasizes the inner biceps, without swinging the torso.",
    "Siéntate y flexiona las mancuernas con una trayectoria que enfatiza la porción interna del bíceps, sin balancear el torso.", True, True)
add(754, "Seated hammer curl", "Curl martillo sentado",
    "Sit and curl dumbbells with a neutral grip, as if swinging a hammer. Forearms and brachialis share the work.",
    "Siéntate y flexiona mancuernas con agarre neutro, como si clavaras un martillo. Comparten el trabajo antebrazos y braquial.", True, True)
add(770, "Seated dumbbell curl", "Curl de bíceps con mancuernas sentado",
    "A standard seated dumbbell curl on a bench. No standing, no leg drive.",
    "Curl estándar de mancuernas sentado en banco. Sin ponerte de pie ni impulsar con las piernas.", True, True)
add(772, "Single-arm seated dumbbell curl", "Curl de bíceps a un brazo sentado con mancuerna",
    "Sit and curl one dumbbell at a time so each arm works without help from the other.",
    "Siéntate y flexiona una mancuerna cada vez para que cada brazo trabaje sin ayuda del otro.", True, True)
add(775, "Seated biceps hammer curl", "Curl martillo de bíceps sentado",
    "Seated hammer curl with a neutral grip. Same pattern as standing hammers, done on a bench.",
    "Curl martillo sentado con agarre neutro. El mismo patrón que de pie, pero en el banco.", True, True)
add(778, "Seated hammer curls", "Curls martillo sentados",
    "Sit and perform hammer curls with both arms. Keep the wrists neutral throughout.",
    "Siéntate y haz curls martillo con ambos brazos. Las muñecas se mantienen neutras todo el tiempo.", True, True)
add(779, "Seated alternating biceps curl", "Curl de bíceps alterno sentado",
    "Sit and curl one dumbbell while the other arm waits, alternating sides.",
    "Siéntate y flexiona una mancuerna mientras el otro brazo espera, alternando lados.", True, True)
add(804, "Seated dumbbell concentration curl", "Curl de concentración sentado con mancuerna",
    "Sit, brace the working elbow on the inner thigh, and curl a dumbbell. Classic seated isolation.",
    "Siéntate, apoya el codo de trabajo en el muslo interno y flexiona una mancuerna. Aislamiento clásico sentado.", True, True)
add(805, "Seated biceps curl", "Curl de bíceps sentado",
    "Sit on a bench and curl dumbbells. A basic seated biceps pattern.",
    "Siéntate en un banco y flexiona mancuernas. Un patrón básico de bíceps sentado.", True, True)
add(806, "Seated alternating biceps curl", "Curl de bíceps alterno sentado",
    "Seated alternating dumbbell curls. Stay on the bench between arms.",
    "Curls alternos con mancuernas sentado. Quédate en el banco entre un brazo y el otro.", True, True)
add(832, "Seated cable biceps curl", "Curl de bíceps sentado en polea",
    "Sit in front of a low pulley and curl the handle. Fully seated cable biceps work; no standing cheat.",
    "Siéntate frente a una polea baja y flexiona el agarre. Bíceps en polea totalmente sentado; sin trampa de pie.", True, True, "Polea")
add(852, "Seated biceps", "Trabajo de bíceps sentado",
    "A seated biceps hold or light curl using body position rather than a machine. Stay sitting.",
    "Un trabajo de bíceps sentado (isométrico o curl ligero) sin máquina. Permanece sentado.", True, True)

# --- Gemelos / piernas (sentado, pero usa piernas) ---
add(874, "Barbell seated calf raise", "Elevación de gemelos sentado con barra",
    "Sit with a barbell on the thighs and raise the heels. Seated calf work: the legs are the prime movers.",
    "Siéntate con una barra sobre los muslos y eleva los talones. Gemelos sentado: las piernas son el motor.", True, False)
add(885, "Single-leg machine seated calf raise", "Elevación de gemelos sentado a una pierna en máquina",
    "On a seated calf machine, work one leg at a time. Still a calf exercise.",
    "En la máquina de gemelos sentado, trabaja una pierna cada vez. Sigue siendo un ejercicio de gemelos.", True, False)
add(888, "Seated calf raise", "Elevación de gemelos sentado",
    "The classic seated calf-raise machine, targeting the soleus with bent knees.",
    "La máquina clásica de gemelos sentado; enfatiza el sóleo con las rodillas flexionadas.", True, False)
add(892, "Seated single-leg calf press", "Prensa de gemelos a una pierna sentado",
    "Press through the ball of one foot on a seated calf or press station. Leg-driven.",
    "Empuja con la planta de un pie en una estación de gemelos o prensa sentado. Lo mueven las piernas.", True, False)
add(893, "Seated calf raise", "Elevación de gemelos sentado",
    "Seated calf raise on a machine. Knees bent, heels up and down.",
    "Elevación de gemelos sentado en máquina. Rodillas flexionadas, talones arriba y abajo.", True, False)
add(899, "Seated calf press", "Prensa de gemelos sentado",
    "A seated press focused on the calves rather than a full leg press stroke.",
    "Una prensa sentada centrada en los gemelos, no una prensa de piernas completa.", True, False)
add(901, "Machine seated calf raise", "Elevación de gemelos sentado en máquina",
    "Machine seated calf raise for the soleus. Sitting does not make this a no-legs drill.",
    "Elevación de gemelos en máquina sentado, enfocada al sóleo. Ir sentado no lo convierte en un ejercicio sin piernas.", True, False)
add(902, "Seated calf raise", "Elevación de gemelos sentado",
    "Another seated calf-raise variation. Prime movers are still the calves.",
    "Otra variación de gemelos sentado. Los motores siguen siendo las pantorrillas.", True, False)
add(908, "Seated calf stretch", "Estiramiento de gemelos sentado",
    "Sit and flex the ankle to stretch the calf. The stretched tissue is the lower leg.",
    "Siéntate y flexiona el tobillo para estirar el gemelo. El tejido que se estira es la pierna.", True, False)

# --- Pecho / silla ---
add(999, "Incline push-up on chair", "Flexión inclinada con apoyo en silla",
    "Hands on a chair, body in a plank, and push. You are standing on the feet, not sitting.",
    "Manos en una silla, cuerpo en plancha, y empuja. Estás apoyado en los pies, no sentado.", False, False)
add(1061, "Machine seated chest press", "Press de pecho sentado en máquina",
    "Sit on the chest-press machine, back against the pad, and press the handles forward. A true seated upper-body press.",
    "Siéntate en la máquina de press de pecho, espalda contra el pad, y empuja los agarres hacia adelante. Un press de tren superior realmente sentado.", True, True)
add(1086, "Seated cable chest fly", "Aperturas de pecho sentado en polea",
    "Sit between cables or on a seated fly machine and bring the handles together in a hugging path. Fully seated chest isolation on pulleys.",
    "Siéntate entre poleas o en una máquina de aperturas y junta los agarres como si abrazaras. Aislamiento de pecho en polea totalmente sentado.", True, True, "Polea")

# --- Antebrazos ---
add(1182, "Seated finger curl", "Curl de dedos sentado",
    "Sit, rest the forearms on the thighs, and curl the bar with the fingers to load the grip.",
    "Siéntate, apoya los antebrazos en los muslos y enrolla la barra con los dedos para cargar el agarre.", True, True)
add(1183, "Seated palms-up wrist curl", "Curl de muñeca sentado con palmas arriba",
    "Sit, forearms on the thighs, palms up, and curl the wrists. Forearm flexors.",
    "Siéntate, antebrazos en los muslos, palmas arriba, y flexiona las muñecas. Flexores de antebrazo.", True, True)
add(1185, "Seated one-arm dumbbell palms-up wrist curl", "Curl de muñeca a una mano sentado, palmas arriba",
    "Same seated wrist curl, one dumbbell at a time, palms up.",
    "El mismo curl de muñeca sentado, una mancuerna cada vez, palmas arriba.", True, True)
add(1187, "Seated palms-down wrist curl", "Curl de muñeca sentado con palmas abajo",
    "Sit and curl the wrists with palms down to train the forearm extensors.",
    "Siéntate y flexiona las muñecas con las palmas abajo para trabajar los extensores de antebrazo.", True, True)
add(1189, "Seated one-arm dumbbell palms-down wrist curl", "Curl de muñeca a una mano sentado, palmas abajo",
    "One-arm seated reverse wrist curl with a dumbbell.",
    "Curl de muñeca inverso a una mano sentado con mancuerna.", True, True)
add(1190, "Seated dumbbell palms-up wrist curl", "Curl de muñeca con mancuernas sentado, palmas arriba",
    "Seated dumbbell wrist curls, both arms, palms up.",
    "Curls de muñeca con mancuernas sentado, ambos brazos, palmas arriba.", True, True)
add(1203, "Seated two-arm palms-up low-pulley wrist curl", "Curl de muñeca a dos manos en polea baja, sentado",
    "Sit facing a low pulley, rest the forearms, and curl the handle with both hands. Fully seated cable forearm work.",
    "Siéntate frente a una polea baja, apoya los antebrazos y flexiona el agarre con ambas manos. Antebrazo en polea totalmente sentado.", True, True, "Polea")

# --- Glúteos / silla / isquios ---
add(1239, "Seated glute squeeze", "Activación de glúteos sentado",
    "Sit tall and squeeze the glutes isometrically. No standing or stepping.",
    "Siéntate erguido y aprieta los glúteos de forma isométrica. Sin ponerte de pie ni dar pasos.", True, True)
add(1242, "Seated glute stretch", "Estiramiento de glúteos sentado",
    "Sit and cross one ankle over the opposite knee (figure-four) to stretch the glute. Chair-friendly.",
    "Siéntate y cruza un tobillo sobre la rodilla contraria (figura cuatro) para estirar el glúteo. Se puede hacer en silla.", True, True)
add(1257, "Alternating slow step-down with chair", "Step-down lento alternado con silla",
    "Stand on a chair or step and lower one foot to the floor slowly. This is a standing single-leg drill.",
    "Ponte de pie sobre una silla o cajón y baja un pie al suelo despacio. Es un trabajo de una pierna de pie.", False, False)
add(1339, "Chair extended-leg stretch", "Estiramiento de isquios con pierna extendida en silla",
    "Sit and extend one leg to stretch the hamstring. The stretch uses the leg even though you are sitting.",
    "Siéntate y extiende una pierna para estirar el isquio. El estiramiento usa la pierna aunque estés sentado.", True, False)
add(1343, "Seated hamstring and calf stretch", "Estiramiento sentado de isquios y gemelos",
    "Sit with a leg extended and hinge to stretch hamstrings and calves. Lower-body stretch.",
    "Siéntate con una pierna extendida e inclínate para estirar isquios y gemelos. Estiramiento de tren inferior.", True, False)
add(1345, "Seated band hamstring curl", "Curl femoral sentado con banda",
    "Sit and curl the heel toward the glute against a band. Hamstrings are the prime movers.",
    "Siéntate y lleva el talón al glúteo contra una banda. Los isquios son el motor.", True, False)
add(1351, "Seated leg curl", "Curl femoral sentado",
    "On the seated leg-curl machine, pad against the calves, curl the heels under the seat.",
    "En la máquina de femoral sentado, el pad contra las pantorrillas, lleva los talones debajo del asiento.", True, False)
add(1357, "Seated hamstring curl", "Curl femoral sentado",
    "Seated hamstring curl on a machine. Sitting, but the work is in the legs.",
    "Curl femoral sentado en máquina. Vas sentado, pero el trabajo está en las piernas.", True, False)
add(1363, "Seated hamstring curl", "Curl femoral sentado",
    "Another seated hamstring-curl machine setup. Not a no-legs movement.",
    "Otra máquina de curl femoral sentado. No es un movimiento sin piernas.", True, False)
add(1366, "Seated leg curl", "Curl femoral sentado",
    "Seated leg curl. Compare with lying curl: here the hips stay flexed on the seat.",
    "Curl femoral sentado. Comparado con el tumbado: aquí las caderas se quedan flexionadas en el asiento.", True, False)
add(1394, "Alternating step with chair", "Step alternado con silla",
    "Step onto or off a chair, alternating legs. Standing locomotion, not a seated lift.",
    "Sube o baja de una silla alternando piernas. Es un desplazamiento de pie, no un ejercicio sentado.", False, False)
add(1405, "Seated hamstring stretch", "Estiramiento de isquios sentado",
    "Sit and reach toward an extended leg to stretch the hamstrings.",
    "Siéntate y alcanza una pierna extendida para estirar los isquiotibiales.", True, False)

# --- Espalda / polea sentada ---
add(1495, "Machine seated row", "Remo sentado en máquina",
    "Sit on the row machine, chest or hips braced, and pull the handles to the torso. A seated back row.",
    "Siéntate en la máquina de remo, pecho o caderas fijos, y lleva los agarres al torso. Un remo de espalda sentado.", True, True)
add(1501, "Seated machine row", "Remo sentado en máquina",
    "Seated machine row for the lats and mid-back. Stay against the pad.",
    "Remo sentado en máquina para dorsales y espalda media. Mantén el contacto con el pad.", True, True)
add(1532, "Chair lower-back stretch", "Estiramiento lumbar en silla",
    "Sit in a chair and hinge or rotate gently to stretch the lower back. Upper-body / trunk stretch from a seat.",
    "Siéntate en una silla e inclínate o gira con suavidad para estirar la lumbar. Estiramiento de tronco desde el asiento.", True, True)
add(1543, "Seated good mornings", "Buenos días sentado con barra",
    "Sit with a barbell on the upper back and hinge the torso forward, then return tall. Seated hip hinge; trunk work, not a squat.",
    "Siéntate con una barra sobre la parte alta de la espalda, flexiona el torso hacia adelante y vuelve a erguirte. Bisagra de cadera sentada: trabajo de tronco, no una sentadilla.", True, True)
add(1588, "Seated cable deadlift", "Peso muerto sentado en polea baja",
    "Sit on a seated-row station, hold a low handle, and hinge then extend the hips. Fully seated on a cable, but the hips and hamstrings drive the lift, so it is not a no-legs drill.",
    "Siéntate en el remo con polea, sujeta un agarre bajo y haz bisagra de cadera para luego extender. Vas del todo sentado en la polea, pero caderas e isquios empujan: no cuenta como sin piernas.", True, False, "Polea")
add(1592, "Seated back extension", "Extensión lumbar sentado",
    "Sit on a back-extension machine and extend the torso against the pad. Trunk extensors, seated.",
    "Siéntate en una máquina de extensión lumbar y extiende el torso contra el pad. Extensores de tronco, sentado.", True, True)
add(1698, "Seated cable rows", "Remo sentado con polea",
    "Sit at a cable row, hold the handle, and pull to the torso while the shoulders stay packed. The classic fully seated pulley row.",
    "Siéntate en el remo con polea, sujeta el agarre y tira hacia el torso con los hombros firmes. El remo en polea clásico, totalmente sentado.", True, True, "Polea")
add(1709, "Seated cable rows (wide grip)", "Remo sentado con polea y agarre ancho",
    "Same seated cable row with a wider handle to bias the upper back. Stay seated for the whole set.",
    "El mismo remo sentado en polea con un agarre más ancho para enfatizar la espalda alta. Permanece sentado en toda la serie.", True, True, "Polea")
add(1710, "Single-arm cable seated row", "Remo sentado a un brazo con polea",
    "Seated cable row one arm at a time. Fully seated pulley work; rotate the torso only as far as the ribcage allows.",
    "Remo en polea sentado a un brazo. Trabajo de polea totalmente sentado; gira el torso solo lo que permita la caja torácica.", True, True, "Polea")
add(1714, "Seated cable row", "Remo sentado con polea",
    "Standard seated cable row on a low pulley. Do not turn this into a standing row.",
    "Remo sentado estándar en polea baja. No lo conviertas en un remo de pie.", True, True, "Polea")
add(1717, "Close-grip seated cable row", "Remo sentado con polea y agarre cerrado",
    "Seated cable row with a close or V-grip. Elbows stay close to the ribs.",
    "Remo sentado en polea con agarre cerrado o en V. Los codos se quedan cerca de las costillas.", True, True, "Polea")
add(1728, "Wide-grip seated cable row", "Remo sentado con polea y agarre ancho",
    "Seated cable row with a wide bar. Pull toward the lower chest / upper abs.",
    "Remo sentado en polea con barra ancha. Tira hacia el pecho bajo / abdomen alto.", True, True, "Polea")
add(1730, "Seated cable rows", "Remo sentado con polea",
    "Another seated cable-row listing. Same pattern: sit, pull, control the return.",
    "Otra ficha de remo sentado con polea. El mismo patrón: siéntate, tira, controla la vuelta.", True, True, "Polea")
add(1735, "Machine seated row", "Remo sentado en máquina",
    "Seated row on a selectorized machine. Chest or seat pad keeps you sitting.",
    "Remo sentado en máquina de pin. El pad de pecho o el asiento te mantienen sentado.", True, True)
add(1750, "Band seated row", "Remo sentado con banda",
    "Sit, loop a band around the feet or a low anchor, and row. Seated pulling; the band is not a standing row.",
    "Siéntate, pasa una banda por los pies o un anclaje bajo y rema. Tirón sentado; no es un remo de pie.", True, True)
add(1764, "Seated head-harness neck resistance", "Resistencia de cuello sentado con arnés",
    "Sit and nod or turn against a head harness. Neck work from a seated position.",
    "Siéntate e inclina o gira la cabeza contra un arnés. Trabajo de cuello desde una posición sentada.", True, True)

# --- Cuádriceps / saltos / silla ---
add(1921, "Dumbbell seated box jump", "Salto al cajón partiendo sentado, con mancuernas",
    "Start seated, then explode onto a box while holding dumbbells. It begins on a seat but is a jump: legs are required.",
    "Empiezas sentado y explotas hacia un cajón con mancuernas. Parte del asiento, pero es un salto: hacen falta las piernas.", False, False)
add(2081, "Seated leg press", "Prensa de piernas sentado",
    "Sit in the leg-press sled and extend the knees. Seated, but the legs do all the work.",
    "Siéntate en la prensa y extiende las rodillas. Vas sentado, pero las piernas hacen todo el trabajo.", True, False)
add(2087, "Seated leg press", "Prensa de piernas sentado",
    "Another seated leg-press variation. Not a no-legs movement.",
    "Otra variación de prensa de piernas sentado. No es un movimiento sin piernas.", True, False)
add(2219, "Seated quad contraction", "Contracción isométrica de cuádriceps sentado",
    "Sit and tense the quadriceps without standing. The target muscle is still the thigh.",
    "Siéntate y tensa los cuádriceps sin ponerte de pie. El músculo objetivo sigue siendo el muslo.", True, False)
add(2236, "Bulgarian split squat on chair", "Sentadilla búlgara con apoyo en silla",
    "Rear foot on a chair, front foot on the floor, and squat. Standing single-leg work; the chair is only a rear support.",
    "Pie de atrás en una silla, pie de adelante en el suelo, y baja. Trabajo de una pierna de pie; la silla solo es apoyo trasero.", False, False)
add(2246, "Single-leg squat on chair", "Sentadilla a una pierna con silla",
    "Pistol-style squat using a chair as depth or support. You are standing on one leg.",
    "Sentadilla tipo pistol usando la silla como profundidad o apoyo. Estás de pie sobre una pierna.", False, False)

# --- Hombros + polea ---
add(2439, "Seated banded barbell shoulder press", "Press de hombros sentado con barra y banda",
    "Sit and press a barbell overhead with bands for accommodating resistance. Stay on the bench.",
    "Siéntate y empuja una barra por encima de la cabeza con bandas. Quédate en el banco.", True, True)
add(2451, "Seated barbell shoulder press", "Press de hombros con barra sentado",
    "Sit and press a barbell overhead. A classic seated military / shoulder press.",
    "Siéntate y empuja una barra por encima de la cabeza. Un press militar / de hombros clásico sentado.", True, True)
add(2470, "Seated EZ-bar shrug", "Encogimiento de hombros sentado con barra EZ",
    "Sit and shrug an EZ-bar. Traps, seated, no calf or squat pattern.",
    "Siéntate y encoge los hombros con una barra EZ. Trapecios sentado, sin patrón de gemelo ni sentadilla.", True, True)
add(2471, "Seated military press", "Press militar sentado con barra",
    "Strict seated barbell press. No knee dip.",
    "Press con barra sentado y estricto. Sin impulso de rodillas.", True, True)
add(2484, "Seated dumbbell shoulder press", "Press de hombros sentado con mancuernas",
    "Sit and press dumbbells overhead. Upper body only.",
    "Siéntate y empuja mancuernas por encima de la cabeza. Solo tren superior.", True, True)
add(2496, "Seated kettlebell press", "Press sentado con pesa rusa",
    "Sit and press one or two kettlebells overhead.",
    "Siéntate y empuja una o dos pesas rusas por encima de la cabeza.", True, True)
add(2528, "Seated dumbbell press", "Press de hombros sentado con mancuernas",
    "Seated dumbbell overhead press. Keep the ribs down.",
    "Press de mancuernas sentado por encima de la cabeza. Costillas abajo.", True, True)
add(2534, "Seated dumbbell shoulder press", "Press de hombros sentado con mancuernas",
    "Another seated dumbbell shoulder press. Do not stand between reps.",
    "Otro press de hombros con mancuernas sentado. No te pongas de pie entre repeticiones.", True, True)
add(2548, "Seated rear-delt fly", "Aperturas de deltoides posterior sentado",
    "Sit, hinge the torso slightly, and raise dumbbells out to the sides for the rear delts.",
    "Siéntate, inclina un poco el torso y abre las mancuernas a los lados para el deltoides posterior.", True, True)
add(2550, "Seated side lateral raise", "Elevación lateral sentado",
    "Sit and raise dumbbells out to the sides. Sitting cuts the usual standing swing.",
    "Siéntate y eleva las mancuernas a los lados. Ir sentado corta el balanceo típico de pie.", True, True)
add(2585, "Seated lateral raise", "Elevación lateral sentado",
    "Seated lateral raise for the middle delts.",
    "Elevación lateral sentado para el deltoides medio.", True, True)
add(2593, "Seated dumbbell lateral raise", "Elevación lateral sentado con mancuernas",
    "Lateral raises performed on a bench. Elbows slightly bent, no leg drive.",
    "Elevaciones laterales en banco. Codos ligeramente flexionados, sin impulso de piernas.", True, True)
add(2598, "Seated dumbbell overhead press", "Press por encima de la cabeza sentado con mancuernas",
    "Seated overhead press with dumbbells. Wrists stacked over the elbows at the top.",
    "Press sentado con mancuernas por encima de la cabeza. Muñecas alineadas con los codos arriba.", True, True)
add(2636, "Seated dumbbell front raise", "Elevación frontal sentado con mancuernas",
    "Sit and raise dumbbells in front of the body to shoulder height.",
    "Siéntate y eleva las mancuernas delante del cuerpo hasta la altura de los hombros.", True, True)
add(2637, "Seated dumbbell side raise", "Elevación lateral sentado con mancuernas",
    "Sit and raise the dumbbells to the sides. Same family as seated laterals.",
    "Siéntate y eleva las mancuernas a los lados. La misma familia que las laterales sentadas.", True, True)
add(2644, "Alternating seated dumbbell lateral raise", "Elevación lateral sentado alternando mancuernas",
    "Seated laterals, one arm at a time.",
    "Laterales sentado, un brazo cada vez.", True, True)
add(2645, "Seated dumbbell shoulder press", "Press de hombros sentado con mancuernas",
    "Seated dumbbell shoulder press. Controlled tempo.",
    "Press de hombros con mancuernas sentado. Tempo controlado.", True, True)
add(2658, "Seated rear-delt fly", "Aperturas de deltoides posterior sentado",
    "Seated rear-delt fly with dumbbells. Do not turn it into a standing bent-over raise.",
    "Aperturas de deltoides posterior sentado con mancuernas. No lo conviertas en una elevación de pie inclinado.", True, True)
add(2663, "Chair upper-body stretch", "Estiramiento de tren superior en silla",
    "Sit in a chair and stretch the chest, shoulders, or lats. Chair-based, no standing required.",
    "Siéntate en una silla y estira pecho, hombros o dorsales. Desde la silla, sin necesidad de ponerte de pie.", True, True)
add(2684, "Seated face pull", "Face pull sentado en polea",
    "Sit facing a cable at face height and pull the rope toward the face, elbows high. Fully seated pulley rear-delt / upper-back work.",
    "Siéntate frente a una polea a la altura de la cara y tira de la cuerda hacia el rostro, con los codos altos. Deltoides posterior y espalda alta en polea, totalmente sentado.", True, True, "Polea")
add(2686, "Seated cable shoulder press", "Press de hombros sentado en polea",
    "Sit and press a cable handle or bar overhead. Fully seated pulley press.",
    "Siéntate y empuja un agarre o barra de polea por encima de la cabeza. Press en polea totalmente sentado.", True, True, "Polea")
add(2693, "Cable seated lateral raise", "Elevación lateral sentado en polea",
    "Sit beside a low pulley and raise the handle out to the side. Seated cable lateral.",
    "Siéntate junto a una polea baja y eleva el agarre hacia el lado. Lateral en polea sentado.", True, True, "Polea")
add(2700, "Cable seated row", "Remo sentado con polea",
    "Cable seated row. Same family as the seated pulley row: sit, pull to the torso, control the stack.",
    "Remo sentado con polea. La misma familia del remo en polea: siéntate, tira al torso, controla la torre.", True, True, "Polea")
add(2731, "Seated front-delt stretch", "Estiramiento de deltoides anterior sentado",
    "Sit and stretch the front of the shoulder, typically by clasping the hands behind the back or across the body.",
    "Siéntate y estira la parte anterior del hombro, normalmente enlazando las manos detrás de la espalda o cruzando el brazo.", True, True)

# --- Tríceps ---
add(2792, "Seated triceps press", "Press de tríceps sentado por encima de la cabeza",
    "Sit and extend a dumbbell (or two) overhead to train the triceps. Elbows stay close to the head.",
    "Siéntate y extiende una mancuerna (o dos) por encima de la cabeza para el tríceps. Los codos se quedan cerca de la cabeza.", True, True)
add(2801, "Seated bent-over two-arm dumbbell triceps extension", "Extensión de tríceps a dos brazos sentado e inclinado",
    "Sit, hinge the torso, and kick both dumbbells back to extend the elbows.",
    "Siéntate, inclina el torso y extiende ambos codos hacia atrás con mancuernas.", True, True)
add(2804, "Seated bent-over one-arm dumbbell triceps extension", "Extensión de tríceps a un brazo sentado e inclinado",
    "Same seated kickback, one arm at a time.",
    "La misma extensión de tríceps sentado, un brazo cada vez.", True, True)
add(2829, "Seated triceps push-down", "Extensión de tríceps sentado (push-down)",
    "A seated push-down or machine triceps extension. Stay sitting; do not turn it into a standing cable push-down.",
    "Un push-down sentado o extensión de tríceps en máquina. Quédate sentado; no lo conviertas en un push-down de pie.", True, True)
add(2899, "Chair dip", "Fondos de tríceps en silla",
    "Hands on a chair, hips off the seat, and dip. You support yourself with the arms and usually the feet; it is not a seated press.",
    "Manos en una silla, caderas fuera del asiento, y baja. Te sostienes con los brazos y suele haber apoyo de pies; no es un press sentado.", False, False)
add(2902, "Chair triceps dip", "Fondos de tríceps en silla",
    "Triceps dips using a chair as the support. Standing/braced on the feet, not a no-legs lift.",
    "Fondos de tríceps usando una silla de apoyo. Vas apoyado en los pies; no es un ejercicio sin piernas.", False, False)


def main() -> None:
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    by_id = {int(ej["Unnamed: 0"]): ej for ej in data}

    missing = [i for i in FIXES if i not in by_id]
    if missing:
        raise SystemExit(f"IDs no encontrados: {missing}")

    for ej in data:
        if "NO_LEGS" not in ej:
            ej["NO_LEGS"] = False

    for eid, patch in FIXES.items():
        ej = by_id[eid]
        ej.update(patch)

    JSON_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    sitting = sum(1 for ej in data if ej.get("IS_SITTING"))
    no_legs = sum(1 for ej in data if ej.get("NO_LEGS"))
    print(f"OK {JSON_PATH.name}: {len(FIXES)} fichas tocadas, IS_SITTING={sitting}, NO_LEGS={no_legs}")


if __name__ == "__main__":
    main()
