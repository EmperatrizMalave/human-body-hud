// Live Server (puerto 3000) no tiene la API: se llama a FastAPI en esta computadora.
// En el puerto 8000 y en Render la página y la API salen del mismo sitio.
const API_ORIGIN = window.location.port === "3000" ? "http://127.0.0.1:8000" : "";
const API_URL = `${API_ORIGIN}/api/ejercicios`;
const FEEDBACK_URL = `${API_ORIGIN}/api/feedback`;
const HASH_FICHA = "#ejercicio=";


let paginaActual = 1;
let terminoBusqueda = "";
const CLAVE_IDIOMA = "biocinetica-idioma";

function leerIdiomaGuardado() {
    try {
        return localStorage.getItem(CLAVE_IDIOMA) === "EN" ? "EN" : "ES";
    } catch {
        return "ES";
    }
}

function guardarIdioma(valor) {
    try {
        localStorage.setItem(CLAVE_IDIOMA, valor);
    } catch {
        /* el visor vuelve a español si el navegador bloquea el almacenamiento */
    }
}

let idiomaActual = leerIdiomaGuardado();
let zonaActiva = "";
let equipoActivo = "";
let nivelActivo = "";
let listaEjerciciosActuales = [];
let ejercicioSeleccionado = null;
let catalogoAbort = null;

const ZONAS = [
    { id: "", es: "Todas", en: "All", icon: "todas" },
    { id: "abs_core", es: "Core / abs", en: "Core / abs", icon: "abs" },
    { id: "chest_upper", es: "Pecho", en: "Chest", icon: "chest" },
    { id: "shoulders", es: "Hombros", en: "Shoulders", icon: "shoulders" },
    { id: "biceps", es: "Bíceps", en: "Biceps", icon: "biceps" },
    { id: "triceps", es: "Tríceps", en: "Triceps", icon: "triceps" },
    { id: "lats_back", es: "Dorsales", en: "Lats", icon: "lats" },
    { id: "mid_back", es: "Espalda media", en: "Mid back", icon: "midback" },
    { id: "lower_back", es: "Lumbar", en: "Lower back", icon: "lumbar" },
    { id: "traps", es: "Trapecios", en: "Traps", icon: "traps" },
    { id: "quads", es: "Cuádriceps", en: "Quads", icon: "quads" },
    { id: "hamstrings", es: "Isquios", en: "Hamstrings", icon: "hams" },
    { id: "glutes", es: "Glúteos", en: "Glutes", icon: "glutes" },
    { id: "calves", es: "Gemelos", en: "Calves", icon: "calves" },
    { id: "hip_abductors", es: "Abductores", en: "Abductors", icon: "abductors" },
    { id: "hip_adductors", es: "Aductores", en: "Adductors", icon: "adductors" },
    { id: "forearms", es: "Antebrazos", en: "Forearms", icon: "forearms" },
    { id: "neck", es: "Cuello", en: "Neck", icon: "neck" },
];

const EQUIPOS = [
    { id: "", es: "Todos", en: "All" },
    { id: "Dumbbell", es: "Mancuerna", en: "Dumbbells", rim: true, icon: "dumbbell" },
    { id: "Body Only", es: "Cuerpo", en: "Bodyweight", rim: true, icon: "body" },
    { id: "Barbell", es: "Barra", en: "Barbell", rim: true, icon: "barbell" },
    { id: "Kettlebells", es: "Rusas", en: "Kettlebells", rim: true, icon: "kettle" },
    { id: "Cable", es: "Polea", en: "Cable", rim: true, icon: "cable" },
    { id: "Machine", es: "Máquina", en: "Machine", rim: true, icon: "machine" },
    { id: "Bands", es: "Bandas", en: "Bands", rim: true, icon: "bands" },
    { id: "Medicine Ball", es: "Balón", en: "Med ball", rim: true, icon: "ball" },
    { id: "Exercise Ball", es: "Fitball", en: "Fitball", icon: "ball" },
    { id: "E-Z Curl Bar", es: "Barra EZ", en: "EZ bar", icon: "barbell" },
    { id: "Foam Roll", es: "Foam", en: "Foam roll", icon: "foam" },
    { id: "Other", es: "Otro", en: "Other", icon: "other" },
    { id: "Ninguno", es: "Ninguno", en: "None", icon: "none" },
];

const NIVELES = [
    { id: "", es: "Todos", en: "All" },
    { id: "Beginner", es: "Principiante", en: "Beginner" },
    { id: "Intermediate", es: "Intermedio", en: "Intermediate" },
    { id: "Expert", es: "Experto", en: "Expert" },
];

const traduccionesUI = {
    ES: {
        placeholderBusq: "// BUSCAR EJERCICIO, ZONA O EQUIPO...",
        biocineticaTitle: "BIOCINÉTICA",
        biocineticaPick: "Selecciona tu grupo muscular",
        biocineticaDesc: "Elige un grupo para filtrar el catálogo. El mapa y las tarjetas van al mismo filtro.",
        muscleSeleccionado: "Seleccionado",
        muscleCount: "{n} opciones · 1 seleccionada",
        bodyFront: "Frente",
        bodyBack: "Espalda",
        catalogoTitle: "CATÁLOGO DE EJERCICIOS",
        safeGreenTitle: "MODO SAFE-GREEN",
        safeGreenDesc: "Inclusión real, no “modo fácil”. El primer filtro está diseñado para personas con movilidad reducida en el tren inferior: aísla 80 ejercicios donde el motor no son las piernas (ideales para silla de ruedas o poleas), eliminando falsos positivos como el press de gemelos sentado. El segundo filtro muestra exclusivamente estiramientos.\nNota: Esta herramienta clasifica datos técnicos y no sustituye el consejo médico profesional.",
        chkSentada: "Sin usar las piernas (silla / polea sentada)",
        badgeSentado: "SENTADO",
        badgeSinPiernas: "SIN PIERNAS",
        chkImpacto: "Solo estiramientos",
        lblZona: "ZONA",
        lblEquipo: "EQUIPO",
        equipTodos: "Seleccionar todo",
        equipReset: "Restablecer",
        lblNivel: "NIVEL",
        badgeBajoImpacto: "BAJO IMPACTO",
        sinResultados: "No se encontraron ejercicios con esos filtros.",
        cargando: "Consultando catálogo…",
        errorConexion: "No hay conexión con la API. Arranca el backend y recarga.",
        detalleTitle: "FICHA",
        detalleVacio: "Elige un ejercicio del catálogo para ver la ficha completa.",
        lblTipo: "TIPO",
        lblRating: "RATING",
        skipCatalog: "Saltar al catálogo",
        langGroup: "Idioma",
        lblBusqueda: "Buscar ejercicios",
        paginationNav: "Paginación",
        pageGo: "Ir a la página",
        pagePrev: "Página anterior",
        pageNext: "Página siguiente",
        abrirFicha: "Abrir ficha",
        feedbackAbrir: "Enviar sugerencia",
        feedbackAbrirCorto: "Opinión",
        feedbackTitle: "Sugerencias",
        feedbackHelp: "Cuéntanos un error o una idea. Se guarda en el servidor local.",
        feedbackTipo: "Tipo",
        feedbackTipoSugerencia: "Sugerencia",
        feedbackTipoError: "Error",
        feedbackTipoOtro: "Otro",
        feedbackNombre: "Nombre (opcional)",
        feedbackMensaje: "Mensaje",
        feedbackEnviar: "Enviar",
        feedbackCerrar: "Cerrar",
        feedbackCorto: "Escribe al menos 10 caracteres.",
        feedbackOk: "Gracias. Guardamos tu mensaje.",
        feedbackFail: "No se pudo enviar. ¿Está el backend en el puerto 8000?",
    },
    EN: {
        placeholderBusq: "// SEARCH EXERCISE, ZONE OR EQUIPMENT...",
        biocineticaTitle: "BIOKINETICS",
        biocineticaPick: "Select your muscle group",
        biocineticaDesc: "Pick one group to filter the catalog. The map and the cards share the same filter.",
        muscleSeleccionado: "Selected",
        muscleCount: "{n} options · 1 selected",
        bodyFront: "Front",
        bodyBack: "Back",
        catalogoTitle: "EXERCISE CATALOG",
        safeGreenTitle: "SAFE-GREEN MODE",
        safeGreenDesc: "Real inclusion, not “easy mode”. The first filter is designed for people with reduced mobility in the lower body: it isolates 80 exercises whose prime movers are not the legs (suited to a wheelchair or pulleys), dropping false positives such as the seated calf raise. The second filter shows stretching only.\nNote: This tool classifies technical data and does not replace professional medical advice.",
        chkSentada: "No legs required (chair / seated pulley)",
        badgeSentado: "SEATED",
        badgeSinPiernas: "NO LEGS",
        chkImpacto: "Stretching only",
        lblZona: "ZONE",
        lblEquipo: "EQUIPMENT",
        equipTodos: "Select All",
        equipReset: "Reset",
        lblNivel: "LEVEL",
        badgeBajoImpacto: "LOW IMPACT",
        sinResultados: "No exercises matched those filters.",
        cargando: "Loading catalog…",
        errorConexion: "API is offline. Start the backend and reload.",
        detalleTitle: "DETAIL",
        detalleVacio: "Pick an exercise from the catalog to open its full card.",
        lblTipo: "TYPE",
        lblRating: "RATING",
        skipCatalog: "Skip to catalog",
        langGroup: "Language",
        lblBusqueda: "Search exercises",
        paginationNav: "Pagination",
        pageGo: "Go to page",
        pagePrev: "Previous page",
        pageNext: "Next page",
        abrirFicha: "Open detail",
        feedbackAbrir: "Send feedback",
        feedbackAbrirCorto: "Feedback",
        feedbackTitle: "Feedback",
        feedbackHelp: "Tell us about a bug or an idea. It is stored on the local server.",
        feedbackTipo: "Type",
        feedbackTipoSugerencia: "Suggestion",
        feedbackTipoError: "Bug",
        feedbackTipoOtro: "Other",
        feedbackNombre: "Name (optional)",
        feedbackMensaje: "Message",
        feedbackEnviar: "Send",
        feedbackCerrar: "Close",
        feedbackCorto: "Please write at least 10 characters.",
        feedbackOk: "Thanks. Your message was saved.",
        feedbackFail: "Could not send. Is the backend running on port 8000?",
    },
};

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", arrancarHUD);
} else {
    arrancarHUD();
}

function arrancarHUD() {
    inicializarHUD();
    cargarEjercicios(1).then(() => restaurarFichaDesdeHash());
}

function inicializarHUD() {
    pintarZonas();
    pintarEquipos();
    pintarNiveles();
    inicializarMapaCorporal();

    const searchInput = document.getElementById("hud-search-input");
    let timeoutId;
    searchInput.addEventListener("input", (e) => {
        clearTimeout(timeoutId);
        terminoBusqueda = e.target.value.trim();
        timeoutId = setTimeout(() => cargarEjercicios(1), 300);
    });

    document.getElementById("toggle-seated").addEventListener("change", () => cargarEjercicios(1));
    document.getElementById("toggle-impact").addEventListener("change", () => cargarEjercicios(1));
    document.getElementById("equip-select-all").addEventListener("click", () => seleccionarEquipo(""));
    document.getElementById("equip-reset").addEventListener("click", () => seleccionarEquipo(""));
    document.getElementById("muscle-select-all").addEventListener("click", () => seleccionarZona(""));
    document.getElementById("muscle-reset").addEventListener("click", () => seleccionarZona(""));
    document.getElementById("btn-es").addEventListener("click", () => cambiarIdioma("ES"));
    document.getElementById("btn-en").addEventListener("click", () => cambiarIdioma("EN"));
    inicializarFeedback();

    document.getElementById("btn-es").classList.toggle("is-active", idiomaActual === "ES");
    document.getElementById("btn-en").classList.toggle("is-active", idiomaActual === "EN");
    document.getElementById("btn-es").setAttribute("aria-pressed", String(idiomaActual === "ES"));
    document.getElementById("btn-en").setAttribute("aria-pressed", String(idiomaActual === "EN"));
    actualizarTextosInterfaz();
}

function inicializarFeedback() {
    const dialogo = document.getElementById("feedback-dialog");
    const form = document.getElementById("feedback-form");
    const abrir = document.getElementById("btn-feedback");
    const cancelar = document.getElementById("feedback-cancel");
    const estado = document.getElementById("feedback-status");

    abrir.addEventListener("click", () => {
        estado.hidden = true;
        estado.textContent = "";
        dialogo.showModal();
        document.getElementById("feedback-mensaje").focus();
    });

    cancelar.addEventListener("click", () => dialogo.close());

    dialogo.addEventListener("click", (evento) => {
        if (evento.target === dialogo) dialogo.close();
    });

    form.addEventListener("submit", async (evento) => {
        evento.preventDefault();
        const t = traduccionesUI[idiomaActual];
        const mensaje = document.getElementById("feedback-mensaje").value.trim();
        if (mensaje.length < 10) {
            estado.hidden = false;
            estado.classList.add("is-error");
            estado.textContent = t.feedbackCorto;
            return;
        }

        try {
            const respuesta = await fetch(FEEDBACK_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    nombre: document.getElementById("feedback-nombre").value.trim(),
                    tipo: document.getElementById("feedback-tipo").value,
                    mensaje,
                }),
            });
            if (!respuesta.ok) throw new Error(`HTTP ${respuesta.status}`);
            estado.hidden = false;
            estado.classList.remove("is-error");
            estado.textContent = t.feedbackOk;
            form.reset();
            setTimeout(() => dialogo.close(), 900);
        } catch (error) {
            console.error(error);
            estado.hidden = false;
            estado.classList.add("is-error");
            estado.textContent = t.feedbackFail;
        }
    });
}

function inicializarMapaCorporal() {
    const board = document.getElementById("body-board");
    if (!board || board.dataset.ready) return;
    board.dataset.ready = "true";

    board.addEventListener("click", (evento) => {
        const parte = evento.target.closest("[data-muscle]");
        if (!parte) return;
        seleccionarZona(parte.getAttribute("data-muscle"));
    });

    board.addEventListener("keydown", (evento) => {
        if (evento.key !== "Enter" && evento.key !== " ") return;
        const parte = evento.target.closest("[data-muscle]");
        if (!parte) return;
        evento.preventDefault();
        seleccionarZona(parte.getAttribute("data-muscle"));
    });
}

function seleccionarZona(id) {
    zonaActiva = id;
    pintarZonas();
    cargarEjercicios(1);
}

function seleccionarEquipo(id) {
    equipoActivo = id;
    pintarEquipos();
    cargarEjercicios(1);
}

function seleccionarNivel(id) {
    nivelActivo = id;
    pintarNiveles();
    cargarEjercicios(1);
}

function pintarChips(contenedorId, opciones, valorActivo, alElegir) {
    const caja = document.getElementById(contenedorId);
    if (!caja) return;
    caja.replaceChildren();
    opciones.forEach((opcion) => {
        const btn = document.createElement("button");
        btn.type = "button";
        const activa = opcion.id === valorActivo;
        btn.className = "muscle-btn" + (activa ? " is-active" : "");
        btn.textContent = idiomaActual === "ES" ? opcion.es : opcion.en;
        btn.setAttribute("aria-pressed", String(activa));
        btn.addEventListener("click", () => alElegir(opcion.id));
        caja.appendChild(btn);
    });
}

function nombreEquipo(opcion) {
    return idiomaActual === "ES" ? opcion.es : opcion.en;
}

function trazoIcono(nombre) {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("aria-hidden", "true");
    const trazos = {
        dumbbell: "M4 10h2v4H4zM18 10h2v4h-2zM6 12h12",
        barbell: "M3 9v6M6 8v8M18 8v8M21 9v6M6 12h12",
        kettle: "M8 8h8l1 3v6a3 3 0 0 1-3 3h-4a3 3 0 0 1-3-3v-6l1-3zM10 8V6h4v2",
        bands: "M5 7c4 0 4 10 10 10M5 17c4 0 4-10 10-10",
        cable: "M12 3v18M7 8h10M7 16h10",
        machine: "M5 4h14v16H5zM9 8v8M15 8v8",
        body: "M12 5a2 2 0 1 0 0-4 2 2 0 0 0 0 4zM8 9h8l-1 12H9L8 9z",
        ball: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM4 12h16M12 4c3 3 3 13 0 16M12 4c-3 3-3 13 0 16",
        foam: "M4 10h16v4H4zM6 10v4M18 10v4",
        other: "M5 12h14M12 5v14",
        none: "M5 5l14 14M19 5L5 19",
    };
    const d = trazos[nombre] || trazos.other;
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", d);
    svg.appendChild(path);
    return svg;
}

function pintarEquipos() {
    const aro = document.getElementById("equip-map");
    const iconos = document.getElementById("equip-icons");
    const actual = document.getElementById("equip-current");
    if (!aro || !iconos || !actual) return;

    const elegido = EQUIPOS.find((eq) => eq.id === equipoActivo) || EQUIPOS[0];
    actual.textContent = nombreEquipo(elegido);

    const delAro = EQUIPOS.filter((eq) => eq.rim);
    aro.replaceChildren();
    delAro.forEach((opcion, indice) => {
        const angulo = (360 / delAro.length) * indice;
        const activa = opcion.id === equipoActivo;
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "equip-dial__label" + (activa ? " is-active" : "");
        btn.textContent = nombreEquipo(opcion);
        btn.setAttribute("role", "option");
        btn.setAttribute("aria-selected", String(activa));
        btn.setAttribute("aria-label", nombreEquipo(opcion));
        btn.style.setProperty("--a", `${angulo}deg`);
        btn.addEventListener("click", () => seleccionarEquipo(opcion.id));
        aro.appendChild(btn);
    });

    iconos.replaceChildren();
    EQUIPOS.filter((eq) => eq.id).forEach((opcion) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "equip-icon" + (opcion.id === equipoActivo ? " is-active" : "");
        const etiqueta = nombreEquipo(opcion);
        btn.setAttribute("aria-pressed", String(opcion.id === equipoActivo));
        btn.setAttribute("aria-label", etiqueta);
        btn.setAttribute("data-nombre", etiqueta);
        btn.appendChild(trazoIcono(opcion.icon));
        btn.addEventListener("click", () => seleccionarEquipo(opcion.id));
        iconos.appendChild(btn);
    });
}

function pintarNiveles() {
    pintarChips("nivel-map", NIVELES, nivelActivo, seleccionarNivel);
}

function iconoMusculo(nombre) {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 48 48");
    svg.setAttribute("class", "muscle-card__svg");
    svg.setAttribute("aria-hidden", "true");
    const trazos = {
        todas: '<circle cx="24" cy="24" r="14"/><circle cx="24" cy="24" r="5"/><path d="M24 6v7M24 35v7M6 24h7M35 24h7"/>',
        abs: '<circle cx="24" cy="8" r="3.2"/><path d="M16 18h16l-2 16H18z"/><path d="M20 22h8M20 27h8M20 32h8"/>',
        chest: '<path d="M10 22c4-8 24-8 28 0v6c-5 6-23 6-28 0z"/><path d="M24 16v14"/>',
        shoulders: '<path d="M12 28c0-8 5-14 12-14s12 6 12 14"/><path d="M8 26c2-6 6-9 10-9M40 26c-2-6-6-9-10-9"/>',
        biceps: '<path d="M10 30c0-6 4-10 9-10 3 0 4 3 8 3 5 0 9 4 9 9v4H18"/><path d="M19 20c0-5 3-9 7-9"/>',
        triceps: '<path d="M38 30c0-6-4-10-9-10-3 0-4 3-8 3-5 0-9 4-9 9v4h18"/><path d="M29 20c0-5-3-9-7-9"/>',
        lats: '<path d="M24 12v22"/><path d="M24 16c-8 4-12 12-12 20M24 16c8 4 12 12 12 20"/><path d="M16 38h16"/>',
        midback: '<path d="M24 10v26"/><path d="M16 16c4 2 8 2 8 8s-4 6-8 8M32 16c-4 2-8 2-8 8s4 6 8 8"/>',
        lumbar: '<path d="M24 8v32"/><path d="M18 14h12M18 20h12"/><path d="M16 28c8 6 16 6 16 0"/>',
        traps: '<path d="M10 28l14-16 14 16"/><path d="M16 28h16"/><path d="M24 12v20"/>',
        quads: '<path d="M16 8h6l2 22-4 12M32 8h-6l-2 22 4 12"/><path d="M18 20h4M26 20h4"/>',
        hams: '<path d="M16 10h6v20l-3 12M32 10h-6v20l3 12"/>',
        glutes: '<path d="M14 18c0-6 4-10 10-10s10 4 10 10c0 8-4 14-10 14s-10-6-10-14z"/><path d="M24 12v20"/>',
        calves: '<path d="M18 8l2 18-4 16M30 8l-2 18 4 16"/><path d="M16 26h6M26 26h6"/>',
        abductors: '<path d="M18 10v28M30 10v28"/><path d="M18 22H8l4-4M18 22H8l4 4M30 22h10l-4-4M30 22h10l-4 4"/>',
        adductors: '<path d="M12 10v28M36 10v28"/><path d="M18 22h12M22 18l-4 4 4 4M26 18l4 4-4 4"/>',
        forearms: '<path d="M14 12h8v10l-3 18M34 12h-8v10l3 18"/>',
        neck: '<circle cx="24" cy="10" r="5"/><path d="M18 16h12l-1 10H19z"/><path d="M16 30h16"/>',
    };
    svg.innerHTML = trazos[nombre] || trazos.todas;
    return svg;
}

function pintarZonas() {
    const mapa = document.getElementById("muscle-map");
    const t = traduccionesUI[idiomaActual];
    mapa.replaceChildren();

    ZONAS.forEach((zona) => {
        const btn = document.createElement("button");
        btn.type = "button";
        const activa = zona.id === zonaActiva;
        const nombre = idiomaActual === "ES" ? zona.es : zona.en;
        btn.className = "muscle-card" + (activa ? " is-active" : "");
        btn.setAttribute("aria-pressed", String(activa));
        btn.setAttribute("aria-label", activa ? `${nombre}. ${t.muscleSeleccionado}` : nombre);
        btn.appendChild(iconoMusculo(zona.icon));
        const etiqueta = document.createElement("span");
        etiqueta.className = "muscle-card__label";
        etiqueta.textContent = nombre;
        btn.appendChild(etiqueta);
        const badge = document.createElement("span");
        badge.className = "muscle-card__badge";
        badge.textContent = `✓ ${t.muscleSeleccionado}`;
        btn.appendChild(badge);
        btn.addEventListener("click", () => seleccionarZona(zona.id));
        mapa.appendChild(btn);
    });

    const cuenta = document.getElementById("muscle-count");
    if (cuenta) cuenta.textContent = t.muscleCount.replace("{n}", String(ZONAS.length));

    document.querySelectorAll("[data-muscle]").forEach((el) => {
        const id = el.getAttribute("data-muscle");
        const zona = ZONAS.find((z) => z.id === id);
        const nombre = zona ? (idiomaActual === "ES" ? zona.es : zona.en) : id;
        const activa = id === zonaActiva && zonaActiva !== "";
        el.classList.toggle("is-active", activa);
        el.setAttribute("aria-pressed", String(activa));
        el.setAttribute("aria-label", nombre);
        let title = el.querySelector("title");
        if (!title) {
            title = document.createElementNS("http://www.w3.org/2000/svg", "title");
            el.insertBefore(title, el.firstChild);
        }
        title.textContent = nombre;
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
    if (equipoActivo) params.set("equipment", equipoActivo);
    if (nivelActivo) params.set("level", nivelActivo);
    if (document.getElementById("toggle-seated").checked) params.set("no_legs", "true");
    if (document.getElementById("toggle-impact").checked) params.set("low_impact", "true");

    if (catalogoAbort) catalogoAbort.abort();
    catalogoAbort = new AbortController();
    const { signal } = catalogoAbort;

    try {
        const respuesta = await fetch(`${API_URL}?${params.toString()}`, { signal });
        if (!respuesta.ok) throw new Error(`HTTP ${respuesta.status}`);
        const resultado = await respuesta.json();
        mostrarEstado("", false);
        listaEjerciciosActuales = resultado.data || [];
        if (ejercicioSeleccionado) {
            const clave = idEjercicio(ejercicioSeleccionado);
            const enPagina = listaEjerciciosActuales.find((ej) => mismaFicha(ej, ejercicioSeleccionado));
            ejercicioSeleccionado = enPagina || (clave != null ? ejercicioSeleccionado : null);
        }
        renderizarEjercicios(listaEjerciciosActuales);
        renderizarPaginacion(resultado.pagina_actual || 1, resultado.total_paginas || 1);
        pintarDetalle();
    } catch (error) {
        if (error.name === "AbortError") return;
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
    guardarIdioma(nuevoIdioma);
    const btnEs = document.getElementById("btn-es");
    const btnEn = document.getElementById("btn-en");
    btnEs.classList.toggle("is-active", nuevoIdioma === "ES");
    btnEn.classList.toggle("is-active", nuevoIdioma === "EN");
    btnEs.setAttribute("aria-pressed", String(nuevoIdioma === "ES"));
    btnEn.setAttribute("aria-pressed", String(nuevoIdioma === "EN"));
    actualizarTextosInterfaz();
    pintarZonas();
    pintarEquipos();
    pintarNiveles();
    renderizarEjercicios(listaEjerciciosActuales);
    pintarDetalle();
}

function actualizarTextosInterfaz() {
    const t = traduccionesUI[idiomaActual];
    document.querySelectorAll("[data-i18n]").forEach((el) => {
        const clave = el.getAttribute("data-i18n");
        if (t[clave]) el.textContent = t[clave];
    });
    document.querySelectorAll("[data-i18n-aria]").forEach((el) => {
        const clave = el.getAttribute("data-i18n-aria");
        if (t[clave]) el.setAttribute("aria-label", t[clave]);
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

        const tarjeta = document.createElement("button");
        tarjeta.type = "button";
        tarjeta.className = "exercise-card";
        const seleccionada = mismaFicha(ejercicioSeleccionado, ej);
        if (seleccionada) tarjeta.classList.add("is-selected");
        tarjeta.setAttribute("aria-pressed", String(seleccionada));
        tarjeta.setAttribute("aria-label", `${t.abrirFicha}: ${titulo || "Ejercicio"}`);
        const idFicha = idEjercicio(ej);
        if (idFicha != null) tarjeta.dataset.exerciseId = String(idFicha);

        const h = document.createElement("span");
        h.className = "card-title";
        h.textContent = titulo || "Ejercicio";

        const meta = document.createElement("div");
        meta.className = "card-meta";
        meta.append(
            badge(`${t.lblZona}: ${zona}`, "card-badge--zone"),
            badge(`${t.lblEquipo}: ${equipo}`, "card-badge--equip"),
            badge(`${t.lblNivel}: ${nivel}`, "card-badge--level"),
        );
        if (ej.NO_LEGS) {
            meta.append(badge(t.badgeSinPiernas, "card-badge--safe"));
        } else if (ej.IS_SITTING || ej.SENTADO_SITTING) {
            meta.append(badge(t.badgeSentado, "card-badge--safe"));
        }
        if (ej.LOW_IMPACT) {
            meta.append(badge(t.badgeBajoImpacto, "card-badge--safe"));
        }

        const p = document.createElement("p");
        p.className = "card-desc";
        p.textContent = descripcion;

        tarjeta.append(h, meta, p);
        tarjeta.addEventListener("click", () => {
            ejercicioSeleccionado = ej;
            const id = idEjercicio(ej);
            escribirHashFicha(id);
            if (id != null) {
                window.location.href = `/visor.html?ejercicio=${id}`;
                return;
            }
            renderizarEjercicios(listaEjerciciosActuales);
            pintarDetalle();
        });
        contenedor.appendChild(tarjeta);
    });
}

function idEjercicio(ej) {
    if (!ej) return null;
    const numero = Number(ej.id);
    return Number.isInteger(numero) ? numero : null;
}

function mismaFicha(a, b) {
    const idA = idEjercicio(a);
    const idB = idEjercicio(b);
    return idA != null && idA === idB;
}

function escribirHashFicha(id) {
    if (id == null) return;
    const siguiente = `${HASH_FICHA}${id}`;
    if (window.location.hash !== siguiente) {
        history.replaceState(null, "", siguiente);
    }
}

function leerHashFicha() {
    const hash = window.location.hash || "";
    if (!hash.startsWith(HASH_FICHA)) return null;
    const numero = Number(hash.slice(HASH_FICHA.length));
    return Number.isInteger(numero) ? numero : null;
}

async function restaurarFichaDesdeHash() {
    const id = leerHashFicha();
    if (id == null) return;
    const enPagina = listaEjerciciosActuales.find((ej) => idEjercicio(ej) === id);
    if (enPagina) {
        ejercicioSeleccionado = enPagina;
        renderizarEjercicios(listaEjerciciosActuales);
        pintarDetalle();
        return;
    }
    try {
        const respuesta = await fetch(`${API_URL}/${id}`);
        if (!respuesta.ok) return;
        ejercicioSeleccionado = await respuesta.json();
        pintarDetalle();
    } catch (error) {
        console.error(error);
    }
}

function pintarDetalle() {
    const panel = document.getElementById("exercise-detail");
    const t = traduccionesUI[idiomaActual];
    panel.replaceChildren();

    if (!ejercicioSeleccionado) {
        const vacio = document.createElement("p");
        vacio.className = "hud-help";
        vacio.textContent = t.detalleVacio;
        panel.appendChild(vacio);
        return;
    }

    const ej = ejercicioSeleccionado;
    const titulo = document.createElement("h5");
    titulo.className = "card-title";
    titulo.textContent = pick(ej, "TITLE") || "Ejercicio";

    const meta = document.createElement("div");
    meta.className = "card-meta";
    meta.append(
        badge(`${t.lblZona}: ${pick(ej, "BODYPART") || "N/A"}`, "card-badge--zone"),
        badge(`${t.lblEquipo}: ${pick(ej, "EQUIPMENT") || "N/A"}`, "card-badge--equip"),
        badge(`${t.lblNivel}: ${pick(ej, "LEVEL") || "N/A"}`, "card-badge--level"),
        badge(`${t.lblTipo}: ${pick(ej, "TYPE") || "N/A"}`, "card-badge--equip"),
    );
    if (ej.NO_LEGS) meta.append(badge(t.badgeSinPiernas, "card-badge--safe"));
    else if (ej.IS_SITTING || ej.SENTADO_SITTING) meta.append(badge(t.badgeSentado, "card-badge--safe"));
    if (ej.LOW_IMPACT) meta.append(badge(t.badgeBajoImpacto, "card-badge--safe"));

    const rating = document.createElement("p");
    rating.className = "detail-rating";
    const nota = ej.RATING != null ? ej.RATING : "—";
    const notaTxt = pick(ej, "RATINGDESC");
    rating.textContent = `${t.lblRating}: ${nota}${notaTxt ? ` · ${notaTxt}` : ""}`;

    const desc = document.createElement("p");
    desc.className = "detail-desc";
    desc.textContent = pick(ej, "DESC") || (idiomaActual === "ES"
        ? "Sin descripción disponible."
        : "No description available.");

    panel.append(titulo, meta, rating, desc);
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
    const t = traduccionesUI[idiomaActual];
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "page-btn" + (esActivo ? " is-active" : "");
    btn.textContent = texto;
    if (texto === "«") btn.setAttribute("aria-label", t.pagePrev);
    else if (texto === "»") btn.setAttribute("aria-label", t.pageNext);
    else btn.setAttribute("aria-label", `${t.pageGo} ${numeroPagina}`);
    if (esActivo) btn.setAttribute("aria-current", "page");
    btn.addEventListener("click", () => cargarEjercicios(numeroPagina));
    return btn;
}

function spanPuntos() {
    const span = document.createElement("span");
    span.className = "page-ellipsis";
    span.textContent = "...";
    return span;
}
