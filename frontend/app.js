const API_URL = "http://127.0.0.1:8000/api/ejercicios";
let paginaActual = 1;
let terminoBusqueda = "";
let idiomaActual = "ES"; // 'ES' o 'EN'
let listaEjerciciosActuales = []; 

// Diccionario central de textos fijos de la interfaz
const traduccionesUI = {
    ES: {
        placeholderBusq: "// BUSCAR EJERCICIO, ZONA O EQUIPO...",
        biocineticaTitle: "BIOCINÉTICA 3D",
        biocineticaDesc: "Panel de selección corporal y filtros rápidos.",
        catalogoTitle: "CATÁLOGO DE EJERCICIOS",
        safeGreenTitle: "MODO SAFE-GREEN",
        chkSentada: "Solo Postura Sentada",
        chkImpacto: "Bajo Impacto Articular",
        lblZona: "ZONA",
        lblEquipo: "EQUIPO",
        lblNivel: "NIVEL",
        badgeSentado: "SENTADO",
        badgeBajoImpacto: "BAJO IMPACTO",
        sinResultados: "[!] No se encontraron registros biométricos.",
        cargando: "[Consultando red neuronal biométrica...]",
        errorConexion: "⚠️ Error de conexión con el backend."
    },
    EN: {
        placeholderBusq: "// SEARCH EXERCISE, ZONE OR EQUIPMENT...",
        biocineticaTitle: "3D BIOKINETICS",
        biocineticaDesc: "Body selection panel and quick filters.",
        catalogoTitle: "EXERCISE CATALOG",
        safeGreenTitle: "SAFE-GREEN MODE",
        chkSentada: "Seated Posture Only",
        chkImpacto: "Low Joint Impact",
        lblZona: "ZONE",
        lblEquipo: "EQUIPMENT",
        lblNivel: "LEVEL",
        badgeSentado: "SEATED",
        badgeBajoImpacto: "LOW IMPACT",
        sinResultados: "[!] No biometric records found.",
        cargando: "[Querying biometric neural network...]",
        errorConexion: "⚠️ Backend connection error."
    }
};

// ==========================================
// ARRANQUE SEGURO
// ==========================================
console.log("✅ El archivo app.js ha sido leído por el navegador.");

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", arrancarHUD);
} else {
    arrancarHUD();
}

function arrancarHUD() {
    console.log("🚀 Iniciando motores de Cyber-HUD...");
    inicializarHUD();
    console.log("🔍 Buscando base de datos a través de FastAPI...");
    cargarEjercicios(1);
}

// ==========================================
// LÓGICA PRINCIPAL
// ==========================================

// Cargar ejercicios desde FastAPI enviando búsqueda, paginación y filtros Safe-Green
async function cargarEjercicios(pagina = 1) {
    paginaActual = pagina;
    const contenedor = document.getElementById("exercise-feed");
    
    if (contenedor) {
        contenedor.innerHTML = `<p style="text-align: center; color: #00F0FF; font-family: monospace;">${traduccionesUI[idiomaActual].cargando}</p>`;
    }

    try {
        let url = `${API_URL}?page=${pagina}&limit=20`;
        
        if (terminoBusqueda) {
            url += `&search=${encodeURIComponent(terminoBusqueda)}`;
        }

        // IDs del HTML: toggle-seated / toggle-impact (no reescribir otros checkboxes de la plantilla)
        const chkSeated = document.getElementById("toggle-seated");
        const chkImpact = document.getElementById("toggle-impact");

        if (chkSeated && chkSeated.checked) url += `&is_sitting=true`;
        if (chkImpact && chkImpact.checked) url += `&low_impact=true`;

        const respuesta = await fetch(url);
        if (!respuesta.ok) throw new Error(`Error HTTP: ${respuesta.status}`);
        
        const resultado = await respuesta.json();
        
        listaEjerciciosActuales = resultado.data || [];
        renderizarEjercicios(listaEjerciciosActuales);
        renderizarPaginacion(resultado.pagina_actual || 1, resultado.total_paginas || 1);

    } catch (error) {
        console.error("❌ Error de conexión con FastAPI:", error);
        if (contenedor) {
            contenedor.innerHTML = `<p style="color: #ff4d4d; text-align: center; font-family: monospace;">${traduccionesUI[idiomaActual].errorConexion}</p>`;
        }
    }
}

// Inicializar elementos interactivos, búsqueda, paginación y selector en el Header
function inicializarHUD() {
    const exerciseFeed = document.getElementById("exercise-feed");
    if (!exerciseFeed) return;

    const centralColumn = exerciseFeed.parentElement;
    if (document.getElementById("hud-search-input")) return;

    // 1. Crear contenedor de búsqueda
    const searchContainer = document.createElement("div");
    searchContainer.style.marginBottom = "15px";
    searchContainer.innerHTML = `
        <input type="text" id="hud-search-input" placeholder="${traduccionesUI[idiomaActual].placeholderBusq}" 
        style="width: 100%; padding: 12px 18px; background: rgba(10, 15, 30, 0.8); border: 1px solid #00F0FF; border-radius: 6px; color: #00F0FF; outline: none; font-size: 0.85rem; font-family: monospace; box-shadow: 0 0 10px rgba(0, 240, 255, 0.2);">
    `;
    centralColumn.insertBefore(searchContainer, exerciseFeed);

    // 2. Contenedor de paginación numérica
    const paginationContainer = document.createElement("div");
    paginationContainer.id = "hud-pagination";
    paginationContainer.style.cssText = "display: flex; justify-content: center; align-items: center; gap: 5px; margin-top: 20px; flex-wrap: wrap;";
    centralColumn.appendChild(paginationContainer);

    // 3. Insertar interruptor de idioma en el Header
    const headerElement = document.querySelector('header') || document.querySelector('.navbar') || document.querySelector('nav');
    if (headerElement && !document.getElementById("lang-switch")) {
        const rightContainer = headerElement.querySelector('.d-flex') || headerElement.querySelector('div') || headerElement;
        
        const langContainer = document.createElement("div");
        langContainer.id = "lang-switch";
        langContainer.style.cssText = "display: flex; align-items: center; gap: 5px; margin-left: 15px; margin-right: 15px;";
        langContainer.innerHTML = `
            <button id="btn-es" style="background: #00F0FF; color: #0a0f1e; border: 1px solid #00F0FF; padding: 4px 10px; border-radius: 4px; font-family: monospace; font-weight: bold; cursor: pointer; font-size: 0.75rem;">ES</button>
            <button id="btn-en" style="background: rgba(10, 15, 30, 0.9); color: #00F0FF; border: 1px solid #00F0FF; padding: 4px 10px; border-radius: 4px; font-family: monospace; font-weight: bold; cursor: pointer; font-size: 0.75rem;">EN</button>
        `;
        rightContainer.appendChild(langContainer);

        document.getElementById("btn-es").onclick = () => cambiarIdioma("ES");
        document.getElementById("btn-en").onclick = () => cambiarIdioma("EN");
    }

    // Evento de búsqueda con debounce
    const searchInput = document.getElementById("hud-search-input");
    let timeoutId;
    searchInput.addEventListener("input", (e) => {
        clearTimeout(timeoutId);
        terminoBusqueda = e.target.value.trim();
        timeoutId = setTimeout(() => {
            cargarEjercicios(1);
        }, 300);
    });

    const chkSeated = document.getElementById("toggle-seated");
    const chkImpact = document.getElementById("toggle-impact");
    if (chkSeated && !chkSeated.dataset.listener) {
        chkSeated.addEventListener("change", () => cargarEjercicios(1));
        chkSeated.dataset.listener = "true";
    }
    if (chkImpact && !chkImpact.dataset.listener) {
        chkImpact.addEventListener("change", () => cargarEjercicios(1));
        chkImpact.dataset.listener = "true";
    }

    actualizarTextosInterfaz();
}

// Cambiar idioma globalmente
function cambiarIdioma(nuevoIdioma) {
    idiomaActual = nuevoIdioma;
    
    const btnEs = document.getElementById("btn-es");
    const btnEn = document.getElementById("btn-en");
    if (btnEs && btnEn) {
        if (idiomaActual === "ES") {
            btnEs.style.background = "#00F0FF";
            btnEs.style.color = "#0a0f1e";
            btnEn.style.background = "rgba(10, 15, 30, 0.9)";
            btnEn.style.color = "#00F0FF";
        } else {
            btnEn.style.background = "#00F0FF";
            btnEn.style.color = "#0a0f1e";
            btnEs.style.background = "rgba(10, 15, 30, 0.9)";
            btnEs.style.color = "#00F0FF";
        }
    }

    actualizarTextosInterfaz();
    renderizarEjercicios(listaEjerciciosActuales);
}

// Sincronizar textos fijos y vincular checkboxes de Safe-Green
function actualizarTextosInterfaz() {
    const t = traduccionesUI[idiomaActual];

    const searchInput = document.getElementById("hud-search-input");
    if (searchInput) searchInput.placeholder = t.placeholderBusq;

    document.querySelectorAll('h3, h4, h5, p, label').forEach(el => {
        // Ignorar los labels que tienen checkboxes dentro para no duplicar ni sobreescribir
        if (el.querySelector('input[type="checkbox"]')) return;

        const txt = el.innerText.trim();
        if (["BIOCINÉTICA 3D", "3D BIOKINETICS"].includes(txt)) el.innerText = t.biocineticaTitle;
        if (["Panel de selección corporal y filtros rápidos.", "Body selection panel and quick filters."].includes(txt)) el.innerText = t.biocineticaDesc;
        if (["CATÁLOGO DE EJERCICIOS", "EXERCISE CATALOG"].includes(txt)) el.innerText = t.catalogoTitle;
        if (["MODO SAFE-GREEN", "SAFE-GREEN MODE"].includes(txt)) el.innerText = t.safeGreenTitle;
    });

    // Actualizar texto del checkbox 1 limpiando el HTML residual
    const chk1 = document.getElementById("toggle-seated");
    if (chk1 && chk1.parentElement) {
        // 1. Destruir el texto original que viene pegado en el HTML
        Array.from(chk1.parentElement.childNodes).forEach(nodo => {
            if (nodo.nodeType === Node.TEXT_NODE) nodo.textContent = "";
        });
        
        // 2. Crear o actualizar el span controlable
        let labelSpan = chk1.parentElement.querySelector('.chk-label-1');
        if (!labelSpan) {
            labelSpan = document.createElement("span");
            labelSpan.className = "chk-label-1";
            chk1.parentElement.appendChild(labelSpan);
        }
        labelSpan.innerText = " " + t.chkSentada;
    }

    // Actualizar texto del checkbox 2 limpiando el HTML residual
    const chk2 = document.getElementById("toggle-impact");
    if (chk2 && chk2.parentElement) {
        // 1. Destruir el texto original que viene pegado en el HTML
        Array.from(chk2.parentElement.childNodes).forEach(nodo => {
            if (nodo.nodeType === Node.TEXT_NODE) nodo.textContent = "";
        });

        // 2. Crear o actualizar el span controlable
        let labelSpan = chk2.parentElement.querySelector('.chk-label-2');
        if (!labelSpan) {
            labelSpan = document.createElement("span");
            labelSpan.className = "chk-label-2";
            chk2.parentElement.appendChild(labelSpan);
        }
        labelSpan.innerText = " " + t.chkImpacto;
    }
}

// Renderizar tarjetas con soporte bilingüe estricto
function renderizarEjercicios(lista) {
    const contenedor = document.getElementById("exercise-feed");
    if (!contenedor) return;

    contenedor.innerHTML = "";
    const t = traduccionesUI[idiomaActual];

    if (lista.length === 0) {
        contenedor.innerHTML = `<p style="text-align: center; color: #a5f3fc; margin-top: 20px; font-family: monospace;">${t.sinResultados}</p>`;
        return;
    }

    lista.forEach(ej => {
        const tarjeta = document.createElement("div");
        tarjeta.style.cssText = `
            background: linear-gradient(135deg, rgba(14, 20, 38, 0.95) 0%, rgba(8, 11, 20, 0.95) 100%);
            border: 1px solid rgba(0, 240, 255, 0.4);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 15px;
            color: #ffffff;
            box-shadow: inset 0 0 15px rgba(0, 240, 255, 0.05), 0 0 12px rgba(0, 240, 255, 0.15);
        `;
        
        const titulo = idiomaActual === "ES" ? (ej.TITLE_ES || ej.TITLE_EN) : (ej.TITLE_EN || ej.TITLE_ES);
        const zona = idiomaActual === "ES" ? (ej.BODYPART_ES || ej.BODYPART_EN || "N/A") : (ej.BODYPART_EN || ej.BODYPART_ES || "N/A");
        const equipo = idiomaActual === "ES" ? (ej.EQUIPMENT_ES || ej.EQUIPMENT_EN || "N/A") : (ej.EQUIPMENT_EN || ej.EQUIPMENT_ES || "N/A");
        const nivel = idiomaActual === "ES" ? (ej.LEVEL_ES || ej.LEVEL_EN || "N/A") : (ej.LEVEL_EN || ej.LEVEL_ES || "N/A");
        const descripcion = idiomaActual === "ES" ? (ej.DESC_ES || ej.DESC_EN || "Sin descripción disponible.") : (ej.DESC_EN || ej.DESC_ES || "No description available.");
        const esSentado = Boolean(ej.IS_SITTING ?? ej.SENTADO_SITTING);
        const esBajoImpacto = Boolean(ej.LOW_IMPACT);
        const badgesSafe = [
            esSentado ? `<span style="font-size: 0.7rem; background: rgba(57, 255, 20, 0.2); color: #39FF14; padding: 3px 8px; border: 1px solid rgba(57,255,20,0.45); border-radius: 4px; font-family: monospace;">${t.badgeSentado}</span>` : "",
            esBajoImpacto ? `<span style="font-size: 0.7rem; background: rgba(57, 255, 20, 0.2); color: #39FF14; padding: 3px 8px; border: 1px solid rgba(57,255,20,0.45); border-radius: 4px; font-family: monospace;">${t.badgeBajoImpacto}</span>` : "",
        ].join("");

        tarjeta.innerHTML = `
            <h4 style="color: #00F0FF; margin-bottom: 8px; font-size: 1.05rem; letter-spacing: 0.5px;">${titulo || "EJERCICIO"}</h4>
            <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 10px;">
                <span style="font-size: 0.7rem; background: rgba(0, 240, 255, 0.15); color: #00F0FF; padding: 3px 8px; border: 1px solid rgba(0,240,255,0.3); border-radius: 4px; font-family: monospace;">${t.lblZona}: ${zona}</span>
                <span style="font-size: 0.7rem; background: rgba(168, 85, 247, 0.15); color: #c084fc; padding: 3px 8px; border: 1px solid rgba(168,85,247,0.3); border-radius: 4px; font-family: monospace;">${t.lblEquipo}: ${equipo}</span>
                <span style="font-size: 0.7rem; background: rgba(57, 255, 20, 0.15); color: #39FF14; padding: 3px 8px; border: 1px solid rgba(57,255,20,0.3); border-radius: 4px; font-family: monospace;">${t.lblNivel}: ${nivel}</span>
                ${badgesSafe}
            </div>
            <p style="font-size: 0.82rem; color: #94a3b8; line-height: 1.4;">${descripcion}</p>
        `;
        
        contenedor.appendChild(tarjeta);
    });
}

// Paginación numérica
function renderizarPaginacion(paginaActual, totalPaginas) {
    const paginationContainer = document.getElementById("hud-pagination");
    if (!paginationContainer) return;

    paginationContainer.innerHTML = "";
    if (totalPaginas <= 1) return;

    let inicio = Math.max(1, paginaActual - 2);
    let fin = Math.min(totalPaginas, paginaActual + 2);

    if (paginaActual > 1) {
        paginationContainer.appendChild(crearBotonPagina("«", paginaActual - 1));
    }

    if (inicio > 1) {
        paginationContainer.appendChild(crearBotonPagina(1, 1));
        if (inicio > 2) paginationContainer.appendChild(spanPuntos());
    }

    for (let i = inicio; i <= fin; i++) {
        paginationContainer.appendChild(crearBotonPagina(i, i, i === paginaActual));
    }

    if (fin < totalPaginas) {
        if (fin < totalPaginas - 1) paginationContainer.appendChild(spanPuntos());
        paginationContainer.appendChild(crearBotonPagina(totalPaginas, totalPaginas));
    }

    if (paginaActual < totalPaginas) {
        paginationContainer.appendChild(crearBotonPagina("»", paginaActual + 1));
    }
}

function crearBotonPagina(texto, numeroPagina, esActivo = false) {
    const btn = document.createElement("button");
    btn.innerText = texto;
    btn.style.cssText = `
        background: ${esActivo ? '#00F0FF' : 'rgba(10, 15, 30, 0.9)'};
        color: ${esActivo ? '#0a0f1e' : '#00F0FF'};
        border: 1px solid #00F0FF;
        border-radius: 4px;
        padding: 5px 10px;
        font-family: monospace;
        font-size: 0.85rem;
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: ${esActivo ? '0 0 10px rgba(0, 240, 255, 0.6)' : 'none'};
    `;
    
    if (!esActivo) {
        btn.onmouseover = () => btn.style.background = 'rgba(0, 240, 255, 0.2)';
        btn.onmouseout = () => btn.style.background = 'rgba(10, 15, 30, 0.9)';
    }

    btn.onclick = () => cargarEjercicios(numeroPagina);
    return btn;
}

function spanPuntos() {
    const span = document.createElement("span");
    span.innerText = "...";
    span.style.cssText = "color: #00F0FF; font-family: monospace; padding: 0 5px;";
    return span;
}