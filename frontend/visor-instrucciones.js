// Pasos numerados del visor. Cada ficha trae su texto.
// Sin ficha, el visor abre la sentadilla de muestra con estos pasos.

const sentadilla = [
    "Pies al ancho de los hombros.",
    "Espalda recta y core activado.",
    "Desciende controlando el movimiento.",
    "Mantén las rodillas alineadas.",
    "Sube de forma controlada.",
];

const sentadillaEn = [
    "Stand with your feet shoulder-width apart.",
    "Keep your back straight and your core engaged.",
    "Lower yourself while controlling the movement.",
    "Keep your knees aligned over your feet.",
    "Stand back up in a controlled motion.",
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

export function instruccionesDe(ficha, idioma) {
    if (!ficha) return idioma === "EN" ? sentadillaEn : sentadilla;
    const texto = idioma === "EN"
        ? (ficha.DESC_EN || ficha.DESC_ES)
        : (ficha.DESC_ES || ficha.DESC_EN);
    return pasosDeTexto(texto);
}
