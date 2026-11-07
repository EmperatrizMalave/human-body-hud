// Pasos numerados del visor. Cada ejercicio puede traer su propia lista.
// La sentadilla usa los pasos de la ficha visual.

const sentadilla = [
    "Pies al ancho de los hombros.",
    "Espalda recta y core activado.",
    "Desciende controlando el movimiento.",
    "Mantén las rodillas alineadas.",
    "Sube de forma controlada.",
];

function pasosDeTexto(texto) {
    const limpio = (texto || "").replace(/\s+/g, " ").trim();
    if (!limpio) return [];
    const frases = limpio
        .split(/(?<=[.!?])\s+/)
        .map((frase) => frase.trim())
        .filter((frase) => frase.length > 20);
    if (!frases.length) return [limpio];
    return frases.slice(0, 5);
}

export function instruccionesDe(ficha, esSentadilla) {
    if (!ficha || esSentadilla) return sentadilla;
    return pasosDeTexto(ficha.DESC_ES);
}
