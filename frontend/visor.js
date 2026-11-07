import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { catalogoVisor } from "./visor-catalogo.js?v=zapatos";
import { zonaMuscular } from "./visor-musculos.js?v=senales";
import { colocarSenales, tieneMascara } from "./visor-senales.js?v=seleccion3";
import { instruccionesDe } from "./visor-instrucciones.js?v=idioma1";
import { familiaDe, prepararClips } from "./visor-poses.js?v=poses9";

const ejercicioMuestra = catalogoVisor.ejercicios[0];
const idFicha = leerIdFicha();
const CLAVE_IDIOMA = "biocinetica-idioma";
const idioma = (() => {
    try {
        return localStorage.getItem(CLAVE_IDIOMA) === "EN" ? "EN" : "ES";
    } catch {
        return "ES";
    }
})();

const textos = {
    ES: {
        cargar: "Cargando el maniquí…",
        volver: "Volver al catálogo",
        mujer: "Mujer",
        hombre: "Hombre",
        restablecer: "Restablecer vista",
        reproducir: "Reproducir",
        pausa: "Pausa",
        progreso: "Progreso",
        velocidad: "Velocidad",
        musculos: "Músculos trabajados",
        verMusculos: "Ver músculos",
        frente: "Frente",
        espalda: "Espalda",
        instrucciones: "Instrucciones",
        sinInstrucciones: "Este ejercicio todavía no tiene instrucciones.",
        panelMusculos: "Músculos del ejercicio",
        cerrar: "Cerrar",
        mostrarTodos: "Mostrar todos",
        sinResaltado: "Sin resaltado",
        verFrente: "Ver frente",
        verEspalda: "Ver espalda",
        sinMusculos: "Este ejercicio no tiene músculos asociados.",
        sinMarca: "sin marca en el avatar",
        noEjercicio: "No se encontró ese ejercicio.",
        noFicha: "No se pudo leer la ficha. Revisa que FastAPI esté en el puerto 8000.",
        noPersonaje: "El catálogo del visor no tiene ese personaje.",
        sinClips: "Este modelo no trae animaciones.",
        sinPista: "No está la animación {pista}.",
        sinAnimacion: "{nombre} todavía no tiene animación.",
        noModelo: "No se pudo cargar el modelo. Abre esta página desde FastAPI, en el puerto 8000.",
        visor: "Visor 3D",
        personaje: "Personaje",
        animacion: "Animación",
        principal: "principal",
        secundario: "secundario",
        muestra: "Sentadilla con peso corporal",
    },
    EN: {
        cargar: "Loading the mannequin…",
        volver: "Back to catalog",
        mujer: "Woman",
        hombre: "Man",
        restablecer: "Reset view",
        reproducir: "Play",
        pausa: "Pause",
        progreso: "Progress",
        velocidad: "Speed",
        musculos: "Muscles worked",
        verMusculos: "View muscles",
        frente: "Front",
        espalda: "Back",
        instrucciones: "Instructions",
        sinInstrucciones: "This exercise does not have instructions yet.",
        panelMusculos: "Exercise muscles",
        cerrar: "Close",
        mostrarTodos: "Show all",
        sinResaltado: "No highlight",
        verFrente: "View front",
        verEspalda: "View back",
        sinMusculos: "This exercise has no linked muscles.",
        sinMarca: "no mark on the avatar",
        noEjercicio: "That exercise was not found.",
        noFicha: "Could not read the exercise. Check that FastAPI is running on port 8000.",
        noPersonaje: "The viewer catalog does not include that character.",
        sinClips: "This model has no animations.",
        sinPista: "Animation {pista} is missing.",
        sinAnimacion: "{nombre} does not have an animation yet.",
        noModelo: "Could not load the model. Open this page from FastAPI, on port 8000.",
        visor: "3D viewer",
        personaje: "Character",
        animacion: "Animation",
        principal: "primary",
        secundario: "secondary",
        muestra: "Bodyweight squat",
    },
};

const MUSCULO_EN = {
    cuadriceps: "Quadriceps",
    gluteos: "Glutes",
    isquiotibiales: "Hamstrings",
    abductores: "Abductors",
    aductores: "Adductors",
    gemelos: "Calves",
    abdominales: "Abs",
    pectorales: "Pectorals",
    deltoides: "Deltoids",
    biceps: "Biceps",
    triceps: "Triceps",
    dorsales: "Lats",
    espalda_media: "Mid back",
    lumbar: "Lower back",
    trapecios: "Traps",
    antebrazos: "Forearms",
    cuello: "Neck",
};

function tx(clave) {
    return textos[idioma][clave];
}

function frase(clave, datos) {
    return tx(clave).replace(/\{(\w+)\}/g, (_, campo) => datos[campo] ?? "");
}

const canvas = document.querySelector("#visor");
const estado = document.querySelector("#estado");
const titulo = document.querySelector("h1");
const volver = document.querySelector("#volver");
const botonPlay = document.querySelector("#play");
const iconoPlay = botonPlay.querySelector(".icono-play");
const iconoPausa = botonPlay.querySelector(".icono-pausa");
const tiempoActual = document.querySelector("#tiempo-actual");
const tiempoTotal = document.querySelector("#tiempo-total");
const progreso = document.querySelector("#progreso");
const botonVelocidad = document.querySelector("#velocidad");
const botonVista = document.querySelector("#restablecer-vista");
const botonesSexo = [...document.querySelectorAll("[data-sexo]")];
const velocidades = [0.5, 1, 1.5];

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.15;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x070b14);

const camera = new THREE.PerspectiveCamera(32, 1, 0.05, 80);
const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.enablePan = false;
controls.minPolarAngle = THREE.MathUtils.degToRad(60);
controls.maxPolarAngle = THREE.MathUtils.degToRad(105);

scene.add(new THREE.HemisphereLight(0xe8eef8, 0x162033, 0.9));
const clave = new THREE.DirectionalLight(0xffffff, 2.3);
clave.position.set(1.6, 2.6, 2.4);
scene.add(clave);
const relleno = new THREE.DirectionalLight(0xc5d4ea, 0.75);
relleno.position.set(-2.4, 1.3, 1.6);
scene.add(relleno);
const contra = new THREE.DirectionalLight(0xffffff, 1.0);
contra.position.set(-0.4, 1.8, -2.6);
scene.add(contra);

let mixer = null;
let action = null;
let modeloActual = null;
let sexo = "mujer";
let reproduciendo = true;
let velocidad = 1;
let indiceVelocidad = 1;
let arrastrando = false;
let tiempoPendiente = 0;
let senal = null;
let musculosActivos = [];
let seleccionMarca = "todos";
let tiempoSenales = 0;
let vistaFrontal = null;
const reloj = new THREE.Clock();

function ajustar() {
    const ancho = canvas.clientWidth;
    const alto = canvas.clientHeight;
    if (!ancho || !alto) return;
    renderer.setSize(ancho, alto, false);
    camera.aspect = ancho / alto;
    camera.updateProjectionMatrix();
}

function decir(texto) {
    estado.textContent = texto;
}

function formatoTiempo(segundos) {
    const total = Math.max(0, Math.floor(segundos));
    const minutos = Math.floor(total / 60);
    const resto = total % 60;
    return `${minutos}:${String(resto).padStart(2, "0")}`;
}

function duracionClip() {
    if (!action) return 0;
    return action.getClip().duration || 0;
}

function aplicarVelocidad(valor) {
    velocidad = valor;
    indiceVelocidad = Math.max(0, velocidades.indexOf(valor));
    if (action) action.timeScale = valor;
    const texto = `${valor}×`;
    botonVelocidad.textContent = texto;
    botonVelocidad.setAttribute("aria-label", `${tx("velocidad")} ${texto}`);
}

function actualizarPlay() {
    botonPlay.setAttribute("aria-pressed", reproduciendo ? "true" : "false");
    botonPlay.setAttribute("aria-label", reproduciendo ? tx("pausa") : tx("reproducir"));
    iconoPlay.style.display = reproduciendo ? "block" : "none";
    iconoPausa.style.display = reproduciendo ? "none" : "block";
}

function pintarProgreso() {
    const duracion = duracionClip();
    const actual = duracion ? action.time % duracion : 0;
    tiempoActual.textContent = formatoTiempo(actual);
    tiempoTotal.textContent = formatoTiempo(duracion);
    if (!arrastrando) {
        progreso.max = String(duracion || 1);
        progreso.value = String(Math.min(actual, duracion || 1));
    }
    const porcentaje = duracion ? (Number(progreso.value) / duracion) * 100 : 0;
    progreso.style.background = `linear-gradient(to right, #7ee7f0 ${porcentaje}%, #243044 ${porcentaje}%)`;
}

function buscar(segundos) {
    if (!action || !mixer) return;
    const duracion = duracionClip();
    const tiempo = Math.min(Math.max(segundos, 0), duracion);
    const estaba = action.paused;
    action.paused = false;
    action.time = tiempo;
    mixer.update(0);
    action.paused = estaba;
    pintarProgreso();
}

function bloquearControles(bloqueado) {
    botonPlay.disabled = bloqueado;
    progreso.disabled = bloqueado;
    botonVelocidad.disabled = bloqueado;
    botonVista.disabled = bloqueado || !vistaFrontal;
}

function distanciaPara(caja, objetivo) {
    const fovVertical = THREE.MathUtils.degToRad(camera.fov);
    const aspecto = Math.max(camera.aspect, 0.2);
    const fovHorizontal = 2 * Math.atan(Math.tan(fovVertical / 2) * aspecto);
    const tanVertical = Math.tan(fovVertical / 2);
    const tanHorizontal = Math.tan(fovHorizontal / 2);
    const xs = [caja.min.x, caja.max.x];
    const ys = [caja.min.y, caja.max.y];
    const zs = [caja.min.z, caja.max.z];
    let distancia = 0.4;
    xs.forEach((x) => {
        ys.forEach((y) => {
            zs.forEach((z) => {
                const necesaria = Math.max(
                    Math.abs(y - objetivo.y) / tanVertical,
                    Math.abs(x - objetivo.x) / tanHorizontal,
                ) + (z - objetivo.z);
                distancia = Math.max(distancia, necesaria);
            });
        });
    });
    return distancia;
}

function aplicarEncuadre(objetivo, caja, referencia) {
    const distancia = Math.max(distanciaPara(caja, objetivo) * 1.12, 0.4);
    const ancho = Math.max(referencia.x, referencia.z, 0.4);
    controls.target.copy(objetivo);
    controls.minDistance = Math.min(Math.max(ancho * 0.72, 1.05), distancia * 0.82);
    controls.maxDistance = Math.max(distancia * 2.2, controls.minDistance + 1);
    camera.near = Math.max(distancia / 80, 0.02);
    camera.far = distancia * 24;
    camera.position.set(objetivo.x, objetivo.y, objetivo.z + distancia);
    camera.updateProjectionMatrix();
    controls.update();
    vistaFrontal = {
        posicion: camera.position.clone(),
        objetivo: controls.target.clone(),
    };
    botonVista.disabled = false;
    orientarMarca();
}

function encuadrar(objeto) {
    const caja = new THREE.Box3().setFromObject(objeto);
    const tamano = caja.getSize(new THREE.Vector3());
    const centro = caja.getCenter(new THREE.Vector3());
    centro.y = caja.min.y + tamano.y * 0.58;
    aplicarEncuadre(centro, caja, tamano);
}

function encuadrarEjercicio(modelo, clipAction) {
    const duracion = clipAction.getClip().duration || 0;
    const previo = clipAction.time;
    const pausa = clipAction.paused;
    clipAction.paused = false;
    const momentos = duracion ? [0, 0.25, 0.5, 0.75, 1].map((parte) => parte * duracion) : [0];
    let quieto = null;
    const union = new THREE.Box3();
    momentos.forEach((tiempo) => {
        clipAction.time = tiempo;
        mixer.update(0);
        modelo.updateMatrixWorld(true);
        const caja = new THREE.Box3().setFromObject(modelo);
        if (!quieto) quieto = caja.clone();
        union.union(caja);
    });
    clipAction.time = previo;
    mixer.update(0);
    clipAction.paused = pausa;
    modelo.updateMatrixWorld(true);
    const tamano = quieto.getSize(new THREE.Vector3());
    const centro = quieto.getCenter(new THREE.Vector3());
    const objetivo = new THREE.Vector3(centro.x, quieto.min.y + tamano.y * 0.58, centro.z);
    aplicarEncuadre(objetivo, union, tamano);
}

function leerIdFicha() {
    const bruto = new URLSearchParams(window.location.search).get("ejercicio");
    if (bruto == null || bruto === "") return null;
    const numero = Number(bruto);
    return Number.isInteger(numero) && numero >= 0 ? numero : null;
}

function tituloDe(ficha) {
    if (!ficha) return tx("muestra");
    if (idioma === "EN") return ficha.TITLE_EN || ficha.TITLE_ES || tx("muestra");
    return ficha.TITLE_ES || ficha.TITLE_EN || tx("muestra");
}

function tieneSentadilla(ficha) {
    const texto = `${ficha.TITLE_ES || ""} ${ficha.TITLE_EN || ""}`.toLowerCase();
    return texto.includes("sentadilla") || texto.includes("squat");
}

function personajeActual() {
    return catalogoVisor.personajes.find((item) => item.sexo === sexo) || null;
}

function marcarSexo() {
    botonesSexo.forEach((boton) => {
        boton.setAttribute("aria-pressed", boton.dataset.sexo === sexo ? "true" : "false");
    });
}

function cuadro() {
    const delta = reloj.getDelta();
    tiempoSenales += delta;
    if (mixer) mixer.update(delta);
    if (senal) senal.actualizar(tiempoSenales);
    if (action) pintarProgreso();
    controls.update();
    renderer.render(scene, camera);
    requestAnimationFrame(cuadro);
}

botonPlay.addEventListener("click", () => {
    if (!action) return;
    reproduciendo = !reproduciendo;
    action.paused = !reproduciendo;
    actualizarPlay();
});

progreso.addEventListener("pointerdown", () => {
    arrastrando = true;
});

window.addEventListener("pointerup", () => {
    arrastrando = false;
});

progreso.addEventListener("input", () => {
    buscar(Number(progreso.value));
});

botonVelocidad.addEventListener("click", () => {
    indiceVelocidad = (indiceVelocidad + 1) % velocidades.length;
    aplicarVelocidad(velocidades[indiceVelocidad]);
});

botonVista.addEventListener("click", () => {
    if (!vistaFrontal) return;
    camera.position.copy(vistaFrontal.posicion);
    controls.target.copy(vistaFrontal.objetivo);
    controls.update();
});

botonesSexo.forEach((boton) => {
    boton.addEventListener("click", () => {
        if (boton.dataset.sexo === sexo || !fichaLista) return;
        tiempoPendiente = action ? action.time : 0;
        sexo = boton.dataset.sexo;
        marcarSexo();
        pintarVistas();
        cargarModelo(nombreFicha, puedeReproducir, familiaActiva);
    });
});

window.addEventListener("resize", ajustar);
ajustar();
cuadro();

let nombreFicha = tx("muestra");
let puedeReproducir = true;
let familiaActiva = "sentadilla";
let fichaLista = false;

function ponerTexto(selector, clave) {
    const el = document.querySelector(selector);
    if (el) el.textContent = tx(clave);
}

function ponerTextoFinal(selector, clave) {
    const el = document.querySelector(selector);
    if (!el) return;
    const nodo = [...el.childNodes].reverse().find((item) => item.nodeType === Node.TEXT_NODE && item.textContent.trim());
    if (nodo) nodo.textContent = ` ${tx(clave)}`;
}

function aplicarInterfaz() {
    document.documentElement.lang = idioma === "EN" ? "en" : "es";
    ponerTexto("#estado", "cargar");
    ponerTexto("#volver", "volver");
    ponerTexto("#restablecer-vista", "restablecer");
    ponerTexto("#musculos-titulo", "musculos");
    ponerTexto("#instrucciones-titulo", "instrucciones");
    ponerTexto("#instrucciones-vacio", "sinInstrucciones");
    ponerTexto("#musculos-panel-titulo", "panelMusculos");
    ponerTexto("#musculos-todos", "mostrarTodos");
    ponerTexto("#musculos-ninguno", "sinResaltado");
    ponerTexto("#mirar-frente", "verFrente");
    ponerTexto("#mirar-espalda", "verEspalda");
    ponerTexto("#musculos-vacio", "sinMusculos");
    document.querySelectorAll(".musculos-vistas figcaption").forEach((el, indice) => {
        el.textContent = tx(indice === 0 ? "frente" : "espalda");
    });
    ponerTextoFinal("[data-sexo='mujer']", "mujer");
    ponerTextoFinal("[data-sexo='hombre']", "hombre");
    ponerTextoFinal("#ver-musculos", "verMusculos");
    document.querySelector(".sexos")?.setAttribute("aria-label", tx("personaje"));
    document.querySelector(".controles")?.setAttribute("aria-label", tx("animacion"));
    progreso.setAttribute("aria-label", tx("progreso"));
    document.querySelector("#cerrar-musculos")?.setAttribute("aria-label", tx("cerrar"));
    aplicarVelocidad(velocidad);
    actualizarPlay();
}

bloquearControles(true);
marcarSexo();
aplicarInterfaz();
if (idFicha != null) volver.href = `/#ejercicio=${idFicha}`;
abrirFicha();

async function abrirFicha() {
    let ficha = null;
    if (idFicha != null) {
        try {
            const respuesta = await fetch(`/api/ejercicios/${idFicha}`);
            if (!respuesta.ok) {
                decir(tx("noEjercicio"));
                return;
            }
            ficha = await respuesta.json();
        } catch (error) {
            decir(tx("noFicha"));
            return;
        }
    }

    nombreFicha = tituloDe(ficha);
    titulo.textContent = nombreFicha;
    document.title = `${nombreFicha} · ${tx("visor")}`;
    familiaActiva = familiaDe(ficha);
    puedeReproducir = familiaActiva != null;
    fichaLista = true;
    const esSentadilla = ficha == null || tieneSentadilla(ficha);
    pintarMusculos(ficha, esSentadilla);
    pintarInstrucciones(ficha);
    cargarModelo(nombreFicha, puedeReproducir, familiaActiva);
}

function pintarInstrucciones(ficha) {
    const pasos = instruccionesDe(ficha, idioma);
    const lista = document.querySelector("#instrucciones-lista");
    const vacio = document.querySelector("#instrucciones-vacio");
    lista.replaceChildren();
    if (!pasos.length) {
        vacio.hidden = false;
        return;
    }
    vacio.hidden = true;
    pasos.forEach((texto, indice) => {
        const item = document.createElement("li");
        const numero = document.createElement("span");
        numero.className = "paso";
        numero.textContent = String(indice + 1);
        item.append(numero, document.createTextNode(texto));
        lista.append(item);
    });
}

const vistasFigura = {
    mujer: {
        frente: "/musculos/mujer-frente.jpg",
        espalda: "/musculos/mujer-espalda.jpg",
    },
    hombre: {
        frente: "/musculos/hombre-frente.jpg",
        espalda: "/musculos/hombre-espalda.jpg",
    },
};

function pintarVistas() {
    const par = vistasFigura[sexo] || vistasFigura.mujer;
    const frente = document.querySelector("#vista-frente");
    const espalda = document.querySelector("#vista-espalda");
    const etiqueta = tx(sexo === "hombre" ? "hombre" : "mujer");
    frente.src = par.frente;
    frente.alt = idioma === "EN" ? `${etiqueta}, front view` : `${etiqueta} de frente`;
    espalda.src = par.espalda;
    espalda.alt = idioma === "EN" ? `${etiqueta}, back view` : `${etiqueta} de espalda`;
}

pintarVistas();

function musculosMarcados() {
    if (seleccionMarca === "ninguno") return [];
    if (seleccionMarca === "todos") return musculosActivos;
    return musculosActivos.filter((musculo) => musculo.id === seleccionMarca);
}

function pintarSeleccion() {
    const todos = document.querySelector("#musculos-todos");
    const ninguno = document.querySelector("#musculos-ninguno");
    if (todos) todos.setAttribute("aria-pressed", String(seleccionMarca === "todos"));
    if (ninguno) ninguno.setAttribute("aria-pressed", String(seleccionMarca === "ninguno"));
    document.querySelectorAll("[data-musculo]").forEach((boton) => {
        boton.setAttribute("aria-pressed", String(boton.dataset.musculo === seleccionMarca));
    });
}

function refrescarMarca() {
    if (!modeloActual) return;
    if (senal) senal.quitar();
    senal = colocarSenales(modeloActual, musculosMarcados(), sexo);
    window.__visorAvisos = senal.avisos;
}

const MUSCULOS_ESPALDA = new Set([
    "gluteos",
    "isquiotibiales",
    "gemelos",
    "triceps",
    "dorsales",
    "espalda_media",
    "lumbar",
    "trapecios",
]);

function ladoDeMarca() {
    const grupo = seleccionMarca === "todos" || seleccionMarca === "ninguno";
    const ids = grupo ? musculosActivos.map((musculo) => musculo.id) : [seleccionMarca];
    if (!ids.length) return null;
    if (ids.every((id) => MUSCULOS_ESPALDA.has(id))) return "espalda";
    if (!grupo && ids.every((id) => !MUSCULOS_ESPALDA.has(id))) return "frente";
    return null;
}

function orientarMarca() {
    const lado = ladoDeMarca();
    if (lado) mirarLado(lado);
}

function elegirMarca(valor) {
    seleccionMarca = valor;
    pintarSeleccion();
    refrescarMarca();
    orientarMarca();
}

function mirarLado(lado) {
    if (!vistaFrontal) return;
    const delta = vistaFrontal.posicion.clone().sub(vistaFrontal.objetivo);
    if (lado === "espalda") delta.multiplyScalar(-1);
    camera.position.copy(vistaFrontal.objetivo).add(delta);
    controls.target.copy(vistaFrontal.objetivo);
    controls.update();
}

function pintarMusculos(ficha, esSentadilla) {
    const zona = zonaMuscular(ficha, esSentadilla);
    musculosActivos = zona ? zona.musculos : [];
    seleccionMarca = "todos";
    const leyenda = document.querySelector("#musculos-leyenda");
    const vacio = document.querySelector("#musculos-vacio");
    leyenda.replaceChildren();
    if (!zona || !zona.musculos.length) {
        leyenda.hidden = true;
        vacio.hidden = false;
        pintarSeleccion();
        return;
    }
    vacio.hidden = true;
    leyenda.hidden = false;

    zona.musculos.forEach((musculo) => {
        const item = document.createElement("li");
        const boton = document.createElement("button");
        boton.type = "button";
        boton.className = "musculo-opcion";
        boton.dataset.musculo = musculo.id;
        const punto = document.createElement("span");
        punto.className = `punto punto-${musculo.papel}`;
        punto.setAttribute("aria-hidden", "true");
        const texto = document.createElement("span");
        const nombre = idioma === "EN" ? (MUSCULO_EN[musculo.id] || musculo.nombre) : musculo.nombre;
        const papel = tx(musculo.papel === "secundario" ? "secundario" : "principal");
        texto.textContent = tieneMascara(musculo.id)
            ? `${nombre} (${papel})`
            : `${nombre} (${papel}) · ${tx("sinMarca")}`;
        if (!tieneMascara(musculo.id)) boton.disabled = true;
        boton.append(punto, texto);
        item.append(boton);
        leyenda.append(item);
    });
    pintarSeleccion();
}

function iniciarPanelMusculos() {
    const boton = document.querySelector("#ver-musculos");
    const panel = document.querySelector("#musculos-panel");
    const fondo = document.querySelector("#musculos-fondo");
    const cerrar = document.querySelector("#cerrar-musculos");
    let focoPrevio = null;

    function abierto() {
        return !panel.hidden;
    }

    function focosDelPanel() {
        return [...panel.querySelectorAll("button, a, [href], input, [tabindex]")].filter((el) => !el.disabled && el.tabIndex !== -1);
    }

    function colocarPanel() {
        panel.classList.remove("es-hoja");
        panel.style.top = "";
        panel.style.left = "";
        fondo.hidden = true;
        const margen = 8;
        const ancho = panel.offsetWidth;
        const alto = panel.offsetHeight;
        const rect = boton.getBoundingClientRect();
        const abajo = window.innerHeight - rect.bottom - margen;
        const arriba = rect.top - margen;
        const estrecho = window.innerWidth <= 640;
        if (estrecho || (abajo < alto && arriba < alto)) {
            panel.classList.add("es-hoja");
            fondo.hidden = false;
            return;
        }
        const top = abajo >= alto || abajo >= arriba ? rect.bottom + margen : rect.top - alto - margen;
        let left = rect.right - ancho;
        left = Math.max(margen, Math.min(left, window.innerWidth - ancho - margen));
        panel.style.top = `${Math.max(margen, top)}px`;
        panel.style.left = `${left}px`;
    }

    function abrir() {
        if (abierto()) return;
        focoPrevio = document.activeElement;
        panel.hidden = false;
        boton.setAttribute("aria-expanded", "true");
        colocarPanel();
        cerrar.focus();
    }

    function ocultar(devolverFoco) {
        if (!abierto()) return;
        panel.hidden = true;
        fondo.hidden = true;
        panel.classList.remove("es-hoja");
        boton.setAttribute("aria-expanded", "false");
        if (devolverFoco && focoPrevio && document.contains(focoPrevio)) focoPrevio.focus();
    }

    function alternar() {
        if (abierto()) ocultar();
        else abrir();
    }

    boton.addEventListener("click", alternar);
    document.querySelector("#musculos-todos").addEventListener("click", () => elegirMarca("todos"));
    document.querySelector("#musculos-ninguno").addEventListener("click", () => elegirMarca("ninguno"));
    document.querySelector("#mirar-frente").addEventListener("click", () => mirarLado("frente"));
    document.querySelector("#mirar-espalda").addEventListener("click", () => mirarLado("espalda"));
    document.querySelector("#musculos-leyenda").addEventListener("click", (evento) => {
        const opcion = evento.target.closest("[data-musculo]");
        if (!opcion || opcion.disabled) return;
        elegirMarca(opcion.dataset.musculo);
    });
    cerrar.addEventListener("click", () => ocultar(true));
    fondo.addEventListener("click", () => ocultar(true));
    document.addEventListener("pointerdown", (evento) => {
        if (!abierto()) return;
        if (panel.contains(evento.target) || boton.contains(evento.target) || fondo.contains(evento.target)) return;
        ocultar(false);
    });
    document.addEventListener("keydown", (evento) => {
        if (!abierto()) return;
        if (evento.key === "Escape") {
            evento.preventDefault();
            ocultar(true);
            return;
        }
        if (evento.key !== "Tab") return;
        const focos = focosDelPanel();
        if (!focos.length) return;
        const primero = focos[0];
        const ultimo = focos[focos.length - 1];
        if (evento.shiftKey && document.activeElement === primero) {
            evento.preventDefault();
            ultimo.focus();
        } else if (!evento.shiftKey && document.activeElement === ultimo) {
            evento.preventDefault();
            primero.focus();
        }
    });
    window.addEventListener("resize", () => {
        if (abierto()) colocarPanel();
    });
}

iniciarPanelMusculos();

const coloresAvatar = {
    mujer: {
        Piel_maniqui: { color: "#F1F3F6", rugosidad: 0.62 },
        "Human.elvs_male_muscle_shirt1": { color: "#6E7785", rugosidad: 0.72 },
        "Human.frankyaye_mini_skirt_01": { color: "#858E9A", rugosidad: 0.74 },
        "Human.culturalibre_sneakers": { color: "#D9E1E9", rugosidad: 0.48 },
    },
    hombre: {},
};

function aplicarColoresAvatar(raiz, sexoAvatar) {
    const tabla = coloresAvatar[sexoAvatar];
    if (!tabla) return;
    const usos = new Map();
    raiz.traverse((obj) => {
        if (!obj.isMesh || !obj.material) return;
        const lista = Array.isArray(obj.material) ? obj.material : [obj.material];
        lista.forEach((mat) => usos.set(mat.uuid, (usos.get(mat.uuid) || 0) + 1));
    });
    raiz.traverse((obj) => {
        if (!obj.isMesh || !obj.material) return;
        const lista = Array.isArray(obj.material) ? obj.material : [obj.material];
        const siguientes = lista.map((mat) => {
            const ajuste = tabla[mat.name];
            if (!ajuste) return mat;
            const destino = usos.get(mat.uuid) > 1 ? mat.clone() : mat;
            destino.color.set(ajuste.color);
            destino.metalness = 0;
            if ("roughness" in destino) destino.roughness = ajuste.rugosidad;
            destino.map = null;
            destino.transparent = false;
            destino.depthWrite = true;
            destino.needsUpdate = true;
            return destino;
        });
        obj.material = Array.isArray(obj.material) ? siguientes : siguientes[0];
    });
}

function cargarModelo(nombre, reproducir, familia) {
    const personaje = personajeActual();
    if (!personaje) {
        decir(tx("noPersonaje"));
        return;
    }
    const cargador = new GLTFLoader();
    const pedido = sexo;
    cargador.load(
        personaje.modelo,
        (gltf) => {
            if (pedido !== sexo) return;
            if (senal) {
                senal.quitar();
                senal = null;
            }
            if (modeloActual) {
                scene.remove(modeloActual);
                modeloActual = null;
            }
            const modelo = gltf.scene;
            modeloActual = modelo;
            scene.add(modelo);
            aplicarColoresAvatar(modelo, pedido);
            senal = colocarSenales(modelo, musculosMarcados(), pedido);
            if (senal.avisos.length) window.__visorAvisos = senal.avisos;
            encuadrar(modelo);
            reloj.getDelta();

            const clips = gltf.animations || [];
            const clip = THREE.AnimationClip.findByName(clips, ejercicioMuestra.clips[0].pista);
            window.__visor = { modelo, clips: clips.map((item) => item.name) };
            if (!clips.length) {
                decir(tx("sinClips"));
                return;
            }
            if (!clip) {
                decir(frase("sinPista", { pista: ejercicioMuestra.clips[0].pista }));
                return;
            }

            const preparados = prepararClips(modelo, clip);
            const elegido = (familia && preparados[familia]) || preparados.sentadilla;
            mixer = new THREE.AnimationMixer(modelo);
            action = mixer.clipAction(elegido);
            action.setLoop(THREE.LoopRepeat, Infinity);
            action.timeScale = velocidad;
            action.clampWhenFinished = false;
            action.play();
            action.time = tiempoPendiente;
            tiempoPendiente = 0;
            action.paused = !reproduciendo;
            mixer.update(0);
            encuadrarEjercicio(modelo, action);
            if (senal) senal.actualizar(tiempoSenales);
            window.__visor.mixer = mixer;
            window.__visor.action = action;
            window.__visor.controls = controls;
            window.__visor.familia = familia || null;
            window.__visor.clipsPreparados = preparados;
            if (!reproducir) {
                action.paused = true;
                reproduciendo = false;
                actualizarPlay();
                decir(frase("sinAnimacion", { nombre }));
                return;
            }
            bloquearControles(false);
            actualizarPlay();
            decir(nombre);
        },
        undefined,
        () => {
            decir(tx("noModelo"));
        },
    );
}
