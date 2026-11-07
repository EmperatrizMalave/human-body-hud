// Qué músculos enciende cada ejercicio.
// La base solo guarda un MUSCLE_ID. Ese id elige la lista de aquí.
// La sentadilla es aparte: el movimiento trabaja más de un músculo.
// Para afinar un ejercicio, cambia su lista. El id tiene que existir
// en visor-senales.js; si no, la leyenda aparece y el avatar no brilla.

const imagenPiernas = "/musculos/piernas.png";

function zona(id, imagen, musculos) {
    return { id, imagen, musculos };
}

function musculo(id, nombre, papel) {
    return { id, nombre, papel };
}

const porZona = {
    quads: zona("quads", imagenPiernas, [
        musculo("cuadriceps", "Cuádriceps", "principal"),
    ]),
    glutes: zona("glutes", imagenPiernas, [
        musculo("gluteos", "Glúteos", "principal"),
    ]),
    hamstrings: zona("hamstrings", imagenPiernas, [
        musculo("isquiotibiales", "Isquiotibiales", "principal"),
    ]),
    hip_abductors: zona("hip_abductors", imagenPiernas, [
        musculo("abductores", "Abductores", "principal"),
    ]),
    hip_adductors: zona("hip_adductors", imagenPiernas, [
        musculo("aductores", "Aductores", "principal"),
    ]),
    calves: zona("calves", imagenPiernas, [
        musculo("gemelos", "Gemelos", "principal"),
    ]),
    abs_core: zona("abs_core", "/musculos/core.png", [
        musculo("abdominales", "Abdominales", "principal"),
    ]),
    chest_upper: zona("chest_upper", "/musculos/pecho.png", [
        musculo("pectorales", "Pectorales", "principal"),
    ]),
    shoulders: zona("shoulders", "/musculos/hombros.png", [
        musculo("deltoides", "Deltoides", "principal"),
    ]),
    biceps: zona("biceps", "/musculos/brazos.png", [
        musculo("biceps", "Bíceps", "principal"),
    ]),
    triceps: zona("triceps", "/musculos/brazos.png", [
        musculo("triceps", "Tríceps", "principal"),
    ]),
    lats_back: zona("lats_back", "/musculos/espalda.png", [
        musculo("dorsales", "Dorsales", "principal"),
    ]),
    mid_back: zona("mid_back", "/musculos/espalda.png", [
        musculo("espalda_media", "Espalda media", "principal"),
    ]),
    lower_back: zona("lower_back", "/musculos/espalda.png", [
        musculo("lumbar", "Lumbares", "principal"),
    ]),
    traps: zona("traps", "/musculos/espalda.png", [
        musculo("trapecios", "Trapecios", "principal"),
    ]),
    forearms: zona("forearms", "/musculos/brazos.png", [
        musculo("antebrazos", "Antebrazos", "principal"),
    ]),
    neck: zona("neck", "/musculos/cuello.png", [
        musculo("cuello", "Cuello", "principal"),
    ]),
};

const sentadilla = zona("sentadilla", imagenPiernas, [
    musculo("cuadriceps", "Cuádriceps", "principal"),
    musculo("gluteos", "Glúteos", "principal"),
    musculo("isquiotibiales", "Isquiotibiales", "secundario"),
]);

export function zonaMuscular(ficha, esSentadilla) {
    if (!ficha || esSentadilla) return sentadilla;
    return porZona[ficha.MUSCLE_ID] || null;
}
