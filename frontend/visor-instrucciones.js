// Pasos numerados del visor. Cada ejercicio puede traer su propia lista.
// La sentadilla usa los pasos de la ficha visual.

const sentadilla = [
    "Pies al ancho de los hombros.",
    "Espalda recta y core activado.",
    "Desciende controlando el movimiento.",
    "Mantén las rodillas alineadas.",
    "Sube de forma controlada.",
];

export function instruccionesDe(ficha, esSentadilla) {
    if (!ficha || esSentadilla) return sentadilla;
    return [];
}
