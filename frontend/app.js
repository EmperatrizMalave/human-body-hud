// Si abres el HUD con Live Server (puerto 3000), hay que llamar a FastAPI en 8000.
// Si FastAPI sirve el HTML (puerto 8000), basta una ruta relativa.
const API_ORIGIN = window.location.port === "8000" ? "" : "http://127.0.0.1:8000";
const API_URL = `${API_ORIGIN}/api/ejercicios`;
const FEEDBACK_URL = `${API_ORIGIN}/api/feedback`;


let paginaActual = 1;
let terminoBusqueda = "";
let idiomaActual = "ES";
let zonaActiva = "";
let listaEjerciciosActuales = [];
let ejercicioSeleccionado = null;

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
        biocineticaDesc: "Pulsa una zona del cuerpo (frente o espalda) o un chip.",
        bodyFront: "Frente",
        bodyBack: "Espalda",
        catalogoTitle: "CATÁLOGO DE EJERCICIOS",
        safeGreenTitle: "MODO SAFE-GREEN",
        safeGreenDesc: "Inclusión, no “modo fácil”. El primer filtro deja ejercicios cuyo motor no son las piernas (silla, silla de ruedas o tren superior sentado, incluidas poleas). Un press de gemelos sentado sigue siendo de piernas. No sustituye consejo médico. El segundo filtro reduce el golpe articular.",
        chkSentada: "Sin usar las piernas (silla / polea sentada)",
        badgeSentado: "SENTADO",
        badgeSinPiernas: "SIN PIERNAS",
        chkImpacto: "Bajo impacto articular",
        lblZona: "ZONA",
        lblEquipo: "EQUIPO",
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
        biocineticaDesc: "Tap a body zone (front or back) or a chip.",
        bodyFront: "Front",
        bodyBack: "Back",
        catalogoTitle: "EXERCISE CATALOG",
        safeGreenTitle: "SAFE-GREEN MODE",
        safeGreenDesc: "Inclusion, not “easy mode”. The first filter keeps work whose prime movers are not the legs (chair, wheelchair, or seated upper body, including pulleys). A seated calf raise is still a leg drill. This is not medical advice. The second filter reduces joint impact.",
        chkSentada: "No legs required (chair / seated pulley)",
        badgeSentado: "SEATED",
        badgeSinPiernas: "NO LEGS",
        chkImpacto: "Low joint impact",
        lblZona: "ZONE",
        lblEquipo: "EQUIPMENT",
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
    cargarEjercicios(1);
}

function inicializarHUD() {
    pintarZonas();
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
    document.getElementById("btn-es").addEventListener("click", () => cambiarIdioma("ES"));
    document.getElementById("btn-en").addEventListener("click", () => cambiarIdioma("EN"));
    inicializarFeedback();

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

function pintarZonas() {
    const mapa = document.getElementById("muscle-map");
    mapa.replaceChildren();

    ZONAS.forEach((zona) => {
        const btn = document.createElement("button");
        btn.type = "button";
        const activa = zona.id === zonaActiva;
        btn.className = "muscle-btn" + (activa ? " is-active" : "");
        btn.textContent = idiomaActual === "ES" ? zona.es : zona.en;
        btn.setAttribute("aria-pressed", String(activa));
        btn.addEventListener("click", () => seleccionarZona(zona.id));
        mapa.appendChild(btn);
    });

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
    if (document.getElementById("toggle-seated").checked) params.set("no_legs", "true");
    if (document.getElementById("toggle-impact").checked) params.set("low_impact", "true");

    try {
        const respuesta = await fetch(`${API_URL}?${params.toString()}`);
        if (!respuesta.ok) throw new Error(`HTTP ${respuesta.status}`);
        const resultado = await respuesta.json();
        mostrarEstado("", false);
        listaEjerciciosActuales = resultado.data || [];
        if (ejercicioSeleccionado) {
            const clave = idEjercicio(ejercicioSeleccionado);
            ejercicioSeleccionado = listaEjerciciosActuales.find((ej) => idEjercicio(ej) === clave) || null;
        }
        renderizarEjercicios(listaEjerciciosActuales);
        renderizarPaginacion(resultado.pagina_actual || 1, resultado.total_paginas || 1);
        pintarDetalle();
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
    const btnEs = document.getElementById("btn-es");
    const btnEn = document.getElementById("btn-en");
    btnEs.classList.toggle("is-active", nuevoIdioma === "ES");
    btnEn.classList.toggle("is-active", nuevoIdioma === "EN");
    btnEs.setAttribute("aria-pressed", String(nuevoIdioma === "ES"));
    btnEn.setAttribute("aria-pressed", String(nuevoIdioma === "EN"));
    actualizarTextosInterfaz();
    pintarZonas();
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
        const seleccionada = Boolean(
            ejercicioSeleccionado && idEjercicio(ejercicioSeleccionado) === idEjercicio(ej),
        );
        if (seleccionada) tarjeta.classList.add("is-selected");
        tarjeta.setAttribute("aria-pressed", String(seleccionada));
        tarjeta.setAttribute("aria-label", `${t.abrirFicha}: ${titulo || "Ejercicio"}`);

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
            renderizarEjercicios(listaEjerciciosActuales);
            pintarDetalle();
        });
        contenedor.appendChild(tarjeta);
    });
}

function idEjercicio(ej) {
    return [ej.TITLE_EN, ej.TITLE_ES, ej.EQUIPMENT_EN, ej.MUSCLE_ID].join("|");
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
