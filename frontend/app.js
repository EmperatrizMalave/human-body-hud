const API_URL = "/api/ejercicios";

let paginaActual = 1;
let terminoBusqueda = "";
let idiomaActual = "ES";
let zonaActiva = "";
let listaEjerciciosActuales = [];

const ZONAS = [
    { id: "", es: "Todas", en: "All" },
    { id: "abs_core", es: "Core / abs", en: "Core / abs" },
    { id: "chest_upper", es: "Pecho", en: "Chest" },
    { id: "shoulders", es: "Hombros", en: "Shoulders" },
    { id: "biceps", es: "Bíceps", en: "Biceps" },
    { id: "triceps", es: "Tríceps", en: "Triceps" },
    { id: "lats_back", es: "Dorsales", en: "Lats" },
    { id: "mid_back", es: "Espalda media", en: "Mid back" },
    { id: "lower_back", es: "Lumbar", en: "Lower back" },
    { id: "traps", es: "Trapecios", en: "Traps" },
    { id: "quads", es: "Cuádriceps", en: "Quads" },
    { id: "hamstrings", es: "Isquios", en: "Hamstrings" },
    { id: "glutes", es: "Glúteos", en: "Glutes" },
    { id: "calves", es: "Gemelos", en: "Calves" },
    { id: "hip_abductors", es: "Abductores", en: "Abductors" },
    { id: "hip_adductors", es: "Aductores", en: "Adductors" },
    { id: "forearms", es: "Antebrazos", en: "Forearms" },
    { id: "neck", es: "Cuello", en: "Neck" },
];

const traduccionesUI = {
    ES: {
        placeholderBusq: "// BUSCAR EJERCICIO, ZONA O EQUIPO...",
        biocineticaTitle: "BIOCINÉTICA",
        biocineticaDesc: "Elige una zona muscular para filtrar el catálogo.",
        catalogoTitle: "CATÁLOGO DE EJERCICIOS",
        safeGreenTitle: "MODO SAFE-GREEN",
        safeGreenDesc: "Filtros de accesibilidad. Si marcas uno, solo ves esos ejercicios.",
        chkSentada: "Solo postura sentada",
        chkImpacto: "Bajo impacto articular",
        lblZona: "ZONA",
        lblEquipo: "EQUIPO",
        lblNivel: "NIVEL",
        badgeSentado: "SENTADO",
        badgeBajoImpacto: "BAJO IMPACTO",
        sinResultados: "No se encontraron ejercicios con esos filtros.",
        cargando: "Consultando catálogo…",
        errorConexion: "No hay conexión con la API. Arranca el backend y recarga.",
    },
    EN: {
        placeholderBusq: "// SEARCH EXERCISE, ZONE OR EQUIPMENT...",
        biocineticaTitle: "BIOKINETICS",
        biocineticaDesc: "Pick a muscle zone to filter the catalog.",
        catalogoTitle: "EXERCISE CATALOG",
        safeGreenTitle: "SAFE-GREEN MODE",
        safeGreenDesc: "Accessibility filters. Checking one shows only matching exercises.",
        chkSentada: "Seated posture only",
        chkImpacto: "Low joint impact",
        lblZona: "ZONE",
        lblEquipo: "EQUIPMENT",
        lblNivel: "LEVEL",
        badgeSentado: "SEATED",
        badgeBajoImpacto: "LOW IMPACT",
        sinResultados: "No exercises matched those filters.",
        cargando: "Loading catalog…",
        errorConexion: "API is offline. Start the backend and reload.",
    },
};

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", arrancarHUD);
} else {
    arrancarHUD();
}

function arrancarHUD() {
    inicializarHUD();
    cargarEjercicios(1);
}

function inicializarHUD() {
    pintarZonas();

    const searchInput = document.getElementById("hud-search-input");
    let timeoutId;
    searchInput.addEventListener("input", (e) => {
        clearTimeout(timeoutId);
        terminoBusqueda = e.target.value.trim();
        timeoutId = setTimeout(() => cargarEjercicios(1), 300);
    });

    document.getElementById("toggle-seated").addEventListener("change", () => cargarEjercicios(1));
    document.getElementById("toggle-impact").addEventListener("change", () => cargarEjercicios(1));
    document.getElementById("btn-es").addEventListener("click", () => cambiarIdioma("ES"));
    document.getElementById("btn-en").addEventListener("click", () => cambiarIdioma("EN"));

    actualizarTextosInterfaz();
}

function pintarZonas() {
    const mapa = document.getElementById("muscle-map");
    mapa.replaceChildren();

    ZONAS.forEach((zona) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "muscle-btn" + (zona.id === zonaActiva ? " is-active" : "");
        btn.textContent = idiomaActual === "ES" ? zona.es : zona.en;
        btn.addEventListener("click", () => {
            zonaActiva = zona.id;
            pintarZonas();
            cargarEjercicios(1);
        });
        mapa.appendChild(btn);
    });
}

async function cargarEjercicios(pagina = 1) {
    paginaActual = pagina;
    const t = traduccionesUI[idiomaActual];
    mostrarEstado(t.cargando, false);

    const params = new URLSearchParams({
        page: String(pagina),
        limit: "20",
    });
    if (terminoBusqueda) params.set("search", terminoBusqueda);
    if (zonaActiva) params.set("muscle_id", zonaActiva);
    if (document.getElementById("toggle-seated").checked) params.set("is_sitting", "true");
    if (document.getElementById("toggle-impact").checked) params.set("low_impact", "true");

    try {
        const respuesta = await fetch(`${API_URL}?${params.toString()}`);
        if (!respuesta.ok) throw new Error(`HTTP ${respuesta.status}`);
        const resultado = await respuesta.json();
        mostrarEstado("", false);
        listaEjerciciosActuales = resultado.data || [];
        renderizarEjercicios(listaEjerciciosActuales);
        renderizarPaginacion(resultado.pagina_actual || 1, resultado.total_paginas || 1);
    } catch (error) {
        console.error(error);
        listaEjerciciosActuales = [];
        document.getElementById("exercise-feed").replaceChildren();
        document.getElementById("hud-pagination").replaceChildren();
        mostrarEstado(t.errorConexion, true);
    }
}

function mostrarEstado(texto, esError) {
    const status = document.getElementById("hud-status");
    if (!texto) {
        status.hidden = true;
        status.textContent = "";
        return;
    }
    status.hidden = false;
    status.textContent = texto;
    status.classList.toggle("is-error", esError);
}

function cambiarIdioma(nuevoIdioma) {
    idiomaActual = nuevoIdioma;
    document.getElementById("btn-es").classList.toggle("is-active", nuevoIdioma === "ES");
    document.getElementById("btn-en").classList.toggle("is-active", nuevoIdioma === "EN");
    actualizarTextosInterfaz();
    pintarZonas();
    renderizarEjercicios(listaEjerciciosActuales);
}

function actualizarTextosInterfaz() {
    const t = traduccionesUI[idiomaActual];
    document.querySelectorAll("[data-i18n]").forEach((el) => {
        const clave = el.getAttribute("data-i18n");
        if (t[clave]) el.textContent = t[clave];
    });
    document.getElementById("hud-search-input").placeholder = t.placeholderBusq;
    document.documentElement.lang = idiomaActual === "ES" ? "es" : "en";
}

function renderizarEjercicios(lista) {
    const contenedor = document.getElementById("exercise-feed");
    const t = traduccionesUI[idiomaActual];
    contenedor.replaceChildren();

    if (lista.length === 0) {
        mostrarEstado(t.sinResultados, false);
        return;
    }

    lista.forEach((ej) => {
        const titulo = pick(ej, "TITLE");
        const zona = pick(ej, "BODYPART") || "N/A";
        const equipo = pick(ej, "EQUIPMENT") || "N/A";
        const nivel = pick(ej, "LEVEL") || "N/A";
        const descripcion = pick(ej, "DESC") || (idiomaActual === "ES"
            ? "Sin descripción disponible."
            : "No description available.");

        const tarjeta = document.createElement("article");
        tarjeta.className = "exercise-card";

        const h = document.createElement("h4");
        h.className = "card-title";
        h.textContent = titulo || "Ejercicio";

        const meta = document.createElement("div");
        meta.className = "card-meta";
        meta.append(
            badge(`${t.lblZona}: ${zona}`, "card-badge--zone"),
            badge(`${t.lblEquipo}: ${equipo}`, "card-badge--equip"),
            badge(`${t.lblNivel}: ${nivel}`, "card-badge--level"),
        );
        if (ej.IS_SITTING || ej.SENTADO_SITTING) {
            meta.append(badge(t.badgeSentado, "card-badge--safe"));
        }
        if (ej.LOW_IMPACT) {
            meta.append(badge(t.badgeBajoImpacto, "card-badge--safe"));
        }

        const p = document.createElement("p");
        p.className = "card-desc";
        p.textContent = descripcion;

        tarjeta.append(h, meta, p);
        contenedor.appendChild(tarjeta);
    });
}

function pick(ej, campo) {
    const primario = idiomaActual === "ES" ? `${campo}_ES` : `${campo}_EN`;
    const respaldo = idiomaActual === "ES" ? `${campo}_EN` : `${campo}_ES`;
    return ej[primario] || ej[respaldo] || "";
}

function badge(texto, extraClass) {
    const span = document.createElement("span");
    span.className = `card-badge ${extraClass}`;
    span.textContent = texto;
    return span;
}

function renderizarPaginacion(pagina, totalPaginas) {
    const box = document.getElementById("hud-pagination");
    box.replaceChildren();
    if (totalPaginas <= 1) return;

    const inicio = Math.max(1, pagina - 2);
    const fin = Math.min(totalPaginas, pagina + 2);

    if (pagina > 1) box.appendChild(crearBotonPagina("«", pagina - 1));
    if (inicio > 1) {
        box.appendChild(crearBotonPagina("1", 1));
        if (inicio > 2) box.appendChild(spanPuntos());
    }
    for (let i = inicio; i <= fin; i += 1) {
        box.appendChild(crearBotonPagina(String(i), i, i === pagina));
    }
    if (fin < totalPaginas) {
        if (fin < totalPaginas - 1) box.appendChild(spanPuntos());
        box.appendChild(crearBotonPagina(String(totalPaginas), totalPaginas));
    }
    if (pagina < totalPaginas) box.appendChild(crearBotonPagina("»", pagina + 1));
}

function crearBotonPagina(texto, numeroPagina, esActivo = false) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "page-btn" + (esActivo ? " is-active" : "");
    btn.textContent = texto;
    btn.addEventListener("click", () => cargarEjercicios(numeroPagina));
    return btn;
}

function spanPuntos() {
    const span = document.createElement("span");
    span.className = "page-ellipsis";
    span.textContent = "...";
    return span;
}
