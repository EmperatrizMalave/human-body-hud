// Imágenes estáticas de músculos. Para agregar una zona, pon el PNG en
// frontend/musculos/ y registra aquí la ruta y la leyenda.
// principal y secundario solo describen el papel en el ejercicio.

const piernas = {
    id: "piernas",
    imagen: "/musculos/piernas.png",
    musculos: [
        { nombre: "Cuádriceps", papel: "principal" },
        { nombre: "Glúteos", papel: "principal" },
        { nombre: "Isquiotibiales", papel: "secundario" },
    ],
};

const porZona = {
    quads: piernas,
    glutes: piernas,
    hamstrings: piernas,
    hip_abductors: piernas,
    hip_adductors: piernas,
    calves: piernas,
};

export function zonaMuscular(ficha, esSentadilla) {
    if (!ficha || esSentadilla) return piernas;
    return porZona[ficha.MUSCLE_ID] || null;
}
