import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { catalogoVisor } from "./visor-catalogo.js?v=base";
import { zonaMuscular } from "./visor-musculos.js";
import { instruccionesDe } from "./visor-instrucciones.js";

const ejercicioMuestra = catalogoVisor.ejercicios[0];
const idFicha = leerIdFicha();

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
    botonVelocidad.setAttribute("aria-label", `Velocidad ${texto}`);
}

function actualizarPlay() {
    botonPlay.setAttribute("aria-pressed", reproduciendo ? "true" : "false");
    botonPlay.setAttribute("aria-label", reproduciendo ? "Pausa" : "Reproducir");
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
}

function encuadrar(objeto) {
    const caja = new THREE.Box3().setFromObject(objeto);
    const centro = caja.getCenter(new THREE.Vector3());
    const tamano = caja.getSize(new THREE.Vector3());
    const fovVertical = THREE.MathUtils.degToRad(camera.fov);
    const aspecto = Math.max(camera.aspect, 0.2);
    const fovHorizontal = 2 * Math.atan(Math.tan(fovVertical / 2) * aspecto);
    const margen = 1.08;
    const distanciaVertical = (tamano.y / 2) / Math.tan(fovVertical / 2);
    const distanciaHorizontal = (tamano.x / 2) / Math.tan(fovHorizontal / 2);
    const distancia = Math.max(distanciaVertical, distanciaHorizontal, 0.4) * margen;
    const mediaVista = distancia * Math.tan(fovVertical / 2);
    const huecoBajo = mediaVista - tamano.y / 2;
    const airePies = tamano.y * 0.03;
    if (huecoBajo > airePies) centro.y += huecoBajo - airePies;
    controls.target.copy(centro);
    controls.minDistance = distancia * 0.55;
    controls.maxDistance = distancia * 2.6;
    camera.near = Math.max(distancia / 100, 0.01);
    camera.far = distancia * 20;
    camera.position.set(centro.x, centro.y, centro.z + distancia);
    camera.updateProjectionMatrix();
    controls.update();
}

function leerIdFicha() {
    const bruto = new URLSearchParams(window.location.search).get("ejercicio");
    if (bruto == null || bruto === "") return null;
    const numero = Number(bruto);
    return Number.isInteger(numero) && numero >= 0 ? numero : null;
}

function tituloDe(ficha) {
    if (!ficha) return ejercicioMuestra.nombre;
    return ficha.TITLE_ES || ficha.TITLE_EN || ejercicioMuestra.nombre;
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
    if (mixer) mixer.update(delta);
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

botonesSexo.forEach((boton) => {
    boton.addEventListener("click", () => {
        if (boton.dataset.sexo === sexo || !fichaLista) return;
        tiempoPendiente = action ? action.time : 0;
        sexo = boton.dataset.sexo;
        marcarSexo();
        cargarModelo(nombreFicha, puedeReproducir);
    });
});

window.addEventListener("resize", ajustar);
ajustar();
cuadro();

let nombreFicha = ejercicioMuestra.nombre;
let puedeReproducir = true;
let fichaLista = false;

bloquearControles(true);
marcarSexo();
if (idFicha != null) volver.href = `/#ejercicio=${idFicha}`;
abrirFicha();

async function abrirFicha() {
    let ficha = null;
    if (idFicha != null) {
        try {
            const respuesta = await fetch(`/api/ejercicios/${idFicha}`);
            if (!respuesta.ok) {
                decir("No se encontró ese ejercicio.");
                return;
            }
            ficha = await respuesta.json();
        } catch (error) {
            decir("No se pudo leer la ficha. Revisa que FastAPI esté en el puerto 8000.");
            return;
        }
    }

    nombreFicha = tituloDe(ficha);
    titulo.textContent = nombreFicha;
    document.title = `${nombreFicha} · Visor 3D`;
    puedeReproducir = ficha == null || tieneSentadilla(ficha);
    fichaLista = true;
    const esSentadilla = ficha == null || tieneSentadilla(ficha);
    pintarMusculos(ficha, esSentadilla);
    pintarInstrucciones(ficha, esSentadilla);
    cargarModelo(nombreFicha, puedeReproducir);
}

function pintarInstrucciones(ficha, esSentadilla) {
    const pasos = instruccionesDe(ficha, esSentadilla);
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

function pintarMusculos(ficha, esSentadilla) {
    const zona = zonaMuscular(ficha, esSentadilla);
    const imagen = document.querySelector("#musculos-imagen");
    const vacio = document.querySelector("#musculos-vacio");
    const leyenda = document.querySelector("#musculos-leyenda");
    leyenda.replaceChildren();

    if (!zona) {
        imagen.hidden = true;
        imagen.removeAttribute("src");
        vacio.hidden = false;
        vacio.textContent = "Esta zona todavía no tiene imagen.";
        return;
    }

    zona.musculos.forEach((musculo) => {
        const item = document.createElement("li");
        const punto = document.createElement("span");
        punto.className = `punto punto-${musculo.papel}`;
        punto.setAttribute("aria-hidden", "true");
        item.append(punto, document.createTextNode(`${musculo.nombre} (${musculo.papel})`));
        leyenda.append(item);
    });

    vacio.hidden = true;
    imagen.hidden = false;
    imagen.alt = "Músculos trabajados, vista frontal y posterior";
    imagen.onerror = () => {
        imagen.hidden = true;
        vacio.hidden = false;
        vacio.textContent = "Imagen pendiente para esta zona.";
    };
    imagen.src = zona.imagen;
}

function cargarModelo(nombre, reproducir) {
    const personaje = personajeActual();
    if (!personaje) {
        decir("El catálogo del visor no tiene ese personaje.");
        return;
    }
    const cargador = new GLTFLoader();
    const pedido = sexo;
    cargador.load(
        personaje.modelo,
        (gltf) => {
            if (pedido !== sexo) return;
            if (modeloActual) {
                scene.remove(modeloActual);
                modeloActual = null;
            }
            const modelo = gltf.scene;
            modeloActual = modelo;
            scene.add(modelo);
            encuadrar(modelo);
            reloj.getDelta();

            const clips = gltf.animations || [];
            const clip = THREE.AnimationClip.findByName(clips, ejercicioMuestra.clips[0].pista);
            window.__visor = { modelo, clips: clips.map((item) => item.name) };
            if (!clips.length) {
                decir("Este modelo no trae animaciones.");
                return;
            }
            if (!clip) {
                decir(`No está la animación ${ejercicioMuestra.clips[0].pista}.`);
                return;
            }

            mixer = new THREE.AnimationMixer(modelo);
            action = mixer.clipAction(clip);
            action.setLoop(THREE.LoopRepeat, Infinity);
            action.timeScale = velocidad;
            action.clampWhenFinished = false;
            action.play();
            action.time = tiempoPendiente;
            tiempoPendiente = 0;
            action.paused = !reproduciendo;
            mixer.update(0);
            if (!reproducir) {
                action.paused = true;
                reproduciendo = false;
                actualizarPlay();
                decir(`${nombre} todavía no tiene animación.`);
                window.__visor.action = action;
                return;
            }
            bloquearControles(false);
            actualizarPlay();
            decir(nombre);
            window.__visor.mixer = mixer;
            window.__visor.action = action;
            window.__visor.controls = controls;
        },
        undefined,
        () => {
            decir("No se pudo cargar el modelo. Abre esta página desde FastAPI, en el puerto 8000.");
        },
    );
}
