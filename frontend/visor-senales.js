// Máscara del cuádriceps pegada a la piel. El GLB trae un UV de cuerpo
// entero: cada muslo es una isla propia y, dentro de ella, el frente queda
// junto a la cara posterior. Por eso la máscara no se difumina en la
// textura: ese desenfoque cruzaría la costura y teñiría los isquiotibiales.
// Se siembra en los vértices de la isla anterior, se suaviza solo entre
// vecinos de la malla y viaja con el esqueleto. No es un borde anatómico
// certificado. C abre la calibración para corregir el límite a mano.

import * as THREE from "three";

const colorTurquesa = new THREE.Color("#13B8A6");
const colorCian = new THREE.Color("#28F0E7");
const colorChispa = new THREE.Color(0.02, 0.62, 0.5);

// Las chispas nacen en la máscara calibrada y se quedan en la piel.
// Si la máscara es válida, una luz turquesa tenue va debajo. No es un óvalo nuevo.
const pintarPiel = false;
const mostrarParticulas = false;
const mostrarChispas = true;
const VIDA_CHISPA = 1.5;
const PROFUNDO_PANTALLA = [0.055, 0.624, 0.573];
const TURQUESA_PANTALLA = [0.078, 0.722, 0.651];
const CIAN_PANTALLA = [0.157, 0.941, 0.906];

const PAPEL = {
    principal: { cupo: 72, brillo: 0.9 },
    secundario: { cupo: 22, brillo: 0.45 },
};

// Solo entran regiones medidas sobre la malla Human. El resto se reporta.
const regiones = {
    mujer: {
        cuadriceps: [
            { hueso: "upperleg02.L", caja: [-0.065, 0.065, 0.035, 0.27, -0.11, -0.03], separacion: 0.0045 },
            { hueso: "upperleg02.R", caja: [-0.065, 0.065, 0.035, 0.27, -0.11, -0.03], separacion: 0.0045 },
        ],
        gluteos: [
            { hueso: "pelvis.L", caja: [0.065, 0.125, 0.02, 0.1, -0.05, 0.04], separacion: 0.008 },
            { hueso: "pelvis.R", caja: [-0.125, -0.065, 0.02, 0.1, -0.05, 0.04], separacion: 0.008 },
        ],
    },
    hombre: {
        cuadriceps: [
            { hueso: "upperleg02.L", caja: [-0.07, 0.07, 0.04, 0.28, -0.125, -0.035], separacion: 0.005 },
            { hueso: "upperleg02.R", caja: [-0.07, 0.07, 0.04, 0.28, -0.125, -0.035], separacion: 0.005 },
        ],
        gluteos: [
            { hueso: "pelvis.L", caja: [0.065, 0.13, 0.02, 0.11, -0.055, 0.045], separacion: 0.006 },
            { hueso: "pelvis.R", caja: [-0.13, -0.065, 0.02, 0.11, -0.055, 0.045], separacion: 0.006 },
        ],
    },
};

const VERTICE = `
attribute float tamano;
attribute float fase;
attribute float brillo;
attribute float capa;
attribute vec3 colorChispa;
uniform float pixelRatio;
varying float vFase;
varying float vBrillo;
varying float vCapa;
varying vec3 vColor;
void main() {
    vFase = fase;
    vBrillo = brillo;
    vCapa = capa;
    vColor = colorChispa;
    vec4 vista = modelViewMatrix * vec4(position, 1.0);
    gl_PointSize = tamano * pixelRatio;
    gl_Position = projectionMatrix * vista;
}
`;

const FRAGMENTO = `
uniform float tiempo;
varying float vFase;
varying float vBrillo;
varying float vCapa;
varying vec3 vColor;
void main() {
    vec2 p = gl_PointCoord * 2.0 - 1.0;
    float d = length(p);
    if (d > 1.0) discard;
    float pulso = 0.8 + 0.2 * sin(tiempo * 1.7 + vFase * 6.28318);
    float alpha = pow(1.0 - d, 1.8) * pulso * vBrillo;
    gl_FragColor = vec4(vColor, alpha);
}
`;

const _p = new THREE.Vector3();
const _q = new THREE.Vector3();
const _base = new THREE.Vector3();
const _normal = new THREE.Vector3();

function reducido() {
    const estrecho = window.matchMedia && window.matchMedia("(max-width: 800px)").matches;
    const pocos = navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 4;
    return Boolean(estrecho || pocos);
}

function aleatorio(semilla) {
    let valor = semilla >>> 0;
    return () => {
        valor = (valor + 0x6d2b79f5) >>> 0;
        let t = Math.imul(valor ^ (valor >>> 15), 1 | valor);
        t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
}

function mallaCuerpo(raiz) {
    let cuerpo = null;
    let mejor = null;
    let cantidad = 0;
    raiz.traverse((obj) => {
        if (!obj.isSkinnedMesh) return;
        const n = obj.geometry.attributes.position.count;
        if (obj.name === "Human") cuerpo = obj;
        if (n > cantidad) {
            cantidad = n;
            mejor = obj;
        }
    });
    return cuerpo || mejor;
}

function huesoDe(mesh, nombre) {
    const plano = nombre.replaceAll(".", "");
    return mesh.skeleton.bones.find((bone) => bone.name === nombre || bone.name === plano) || null;
}

function verticesEnCaja(mesh, nombre, caja) {
    const bone = huesoDe(mesh, nombre);
    if (!bone) return null;
    const indice = mesh.skeleton.bones.indexOf(bone);
    const mapa = mesh.bindMatrix.clone().premultiply(mesh.skeleton.boneInverses[indice]);
    const pos = mesh.geometry.attributes.position;
    const [x0, x1, y0, y1, z0, z1] = caja;
    const ids = [];
    for (let i = 0; i < pos.count; i += 1) {
        _p.set(pos.getX(i), pos.getY(i), pos.getZ(i)).applyMatrix4(mapa);
        if (_p.x < x0 || _p.x > x1 || _p.y < y0 || _p.y > y1 || _p.z < z0 || _p.z > z1) continue;
        ids.push(i);
    }
    return ids;
}

function recortar(ids, cupo) {
    if (ids.length <= cupo) return ids;
    const paso = ids.length / cupo;
    const salida = [];
    for (let i = 0; i < cupo; i += 1) salida.push(ids[Math.floor(i * paso)]);
    return salida;
}

function crearMaterial() {
    return new THREE.ShaderMaterial({
        uniforms: {
            tiempo: { value: 0 },
            pixelRatio: { value: Math.min(window.devicePixelRatio || 1, 2) },
        },
        vertexShader: VERTICE,
        fragmentShader: FRAGMENTO,
        transparent: true,
        depthWrite: false,
        blending: THREE.NormalBlending,
        toneMapped: true,
    });
}

function pegar(mesh, muestra, separacion, destino, indice) {
    const pos = mesh.geometry.attributes.position;
    const normal = mesh.geometry.attributes.normal;
    _base.set(pos.getX(muestra), pos.getY(muestra), pos.getZ(muestra));
    _normal.set(normal.getX(muestra), normal.getY(muestra), normal.getZ(muestra));
    _p.copy(_base);
    mesh.applyBoneTransform(muestra, _p);
    _q.copy(_base).addScaledVector(_normal, 0.01);
    mesh.applyBoneTransform(muestra, _q);
    _q.sub(_p);
    if (_q.lengthSq() > 1e-8) _p.addScaledVector(_q.normalize(), separacion);
    destino.setXYZ(indice, _p.x, _p.y, _p.z);
}

function mapaHueso(mesh, nombre) {
    const bone = huesoDe(mesh, nombre);
    if (!bone) return null;
    const indice = mesh.skeleton.bones.indexOf(bone);
    return mesh.bindMatrix.clone().premultiply(mesh.skeleton.boneInverses[indice]);
}

function pesoEnHueso(geometry, indice, hueso) {
    const piel = geometry.attributes.skinIndex;
    const peso = geometry.attributes.skinWeight;
    if (!piel || !peso) return 0;
    let suma = 0;
    for (let k = 0; k < piel.itemSize; k += 1) {
        if (piel.getComponent(indice, k) === hueso) suma += peso.getComponent(indice, k);
    }
    return suma;
}

function dobladillo(raiz) {
    let falda = null;
    raiz.traverse((obj) => {
        if (obj.isSkinnedMesh && /skirt/i.test(obj.name)) falda = obj;
    });
    if (!falda) return Infinity;
    const pos = falda.geometry.attributes.position;
    let minimo = Infinity;
    for (let i = 0; i < pos.count; i += 1) minimo = Math.min(minimo, pos.getY(i));
    return minimo;
}

// La isla anterior del UV no es un óvalo: ocupa el frente del muslo,
// se corta antes de la rodilla y, en el lado medial, baja un poco más.
// −Z es el frente del hueso. El signo de X medial está medido en este rig:
// en la pierna izquierda el medial es X negativa y en la derecha, X positiva.
function semillaIsla(local, lado) {
    const medial = lado === "L" ? local.x < 0 : local.x > 0;
    const yMax = medial ? 0.292 : 0.258;
    if (local.y < 0.068 || local.y > yMax) return 0;
    if (local.z > -0.002) return 0;
    return 1;
}

function degradarMascara(pesos, geometry) {
    const suave = suavizar(pesos, geometry, 8);
    let maximo = 0;
    for (let i = 0; i < suave.length; i += 1) maximo = Math.max(maximo, suave[i]);
    if (maximo <= 0) return pesos;
    const salida = new Float32Array(suave.length);
    for (let i = 0; i < salida.length; i += 1) {
        const normalizado = suave[i] / maximo;
        salida[i] = normalizado * normalizado;
    }
    return salida;
}

function suavizar(pesos, geometry, pasos) {
    const index = geometry.index;
    const n = pesos.length;
    const vecinos = Array.from({ length: n }, () => new Set());
    const unir = (a, b) => {
        if (a === b) return;
        vecinos[a].add(b);
        vecinos[b].add(a);
    };
    const total = index ? index.count : n;
    for (let i = 0; i < total; i += 3) {
        const a = index ? index.getX(i) : i;
        const b = index ? index.getX(i + 1) : i + 1;
        const c = index ? index.getX(i + 2) : i + 2;
        unir(a, b);
        unir(b, c);
        unir(c, a);
    }
    let actual = pesos;
    for (let pasoSuave = 0; pasoSuave < pasos; pasoSuave += 1) {
        const siguiente = new Float32Array(n);
        for (let i = 0; i < n; i += 1) {
            let suma = actual[i];
            let cuenta = 1;
            vecinos[i].forEach((j) => {
                suma += actual[j];
                cuenta += 1;
            });
            siguiente[i] = suma / cuenta;
        }
        actual = siguiente;
    }
    return actual;
}

const LADOS_CUADRICEPS = ["upperleg02.L", "upperleg02.R"];
const LADOS_PELVIS = ["pelvis.L", "pelvis.R"];
const LADOS_CADERA = ["upperleg01.L", "upperleg01.R"];

function semillaIsquio(local) {
    if (local.y < 0.06 || local.y > 0.3) return 0;
    if (local.z < 0.008) return 0;
    return 1;
}

function semillaGluteoPelvis(local) {
    if (local.y < 0.02 || local.y > 0.16) return 0;
    if (local.z > 0.01) return 0;
    return 1;
}

function semillaGluteoPierna(local) {
    if (local.y < -0.06 || local.y > 0.05) return 0;
    if (local.z < 0.035) return 0;
    return 1;
}

function mascaraPorHuesos(mesh, grupos, avisos, etiqueta) {
    const huesos = grupos.flatMap((grupo) => grupo.nombres.map((nombre) => {
        const mapa = mapaHueso(mesh, nombre);
        const bone = huesoDe(mesh, nombre);
        if (!mapa || !bone) {
            avisos.push(`No está el hueso ${nombre} para ${etiqueta}.`);
            return null;
        }
        return { mapa, indice: mesh.skeleton.bones.indexOf(bone), semilla: grupo.semilla };
    })).filter(Boolean);
    if (!huesos.length) return null;
    const pos = mesh.geometry.attributes.position;
    const crudo = new Float32Array(pos.count);
    for (let i = 0; i < pos.count; i += 1) {
        _p.set(pos.getX(i), pos.getY(i), pos.getZ(i));
        let mejor = 0;
        huesos.forEach((hueso) => {
            if (pesoEnHueso(mesh.geometry, i, hueso.indice) < 0.25) return;
            _q.copy(_p).applyMatrix4(hueso.mapa);
            mejor = Math.max(mejor, hueso.semilla(_q));
        });
        crudo[i] = mejor;
    }
    const suaveMascara = suavizar(crudo, mesh.geometry, 1);
    let maximo = 0;
    for (let i = 0; i < suaveMascara.length; i += 1) maximo = Math.max(maximo, suaveMascara[i]);
    if (maximo <= 0) {
        avisos.push(`${etiqueta} no cubre vértices de la piel.`);
        return null;
    }
    const salida = new Float32Array(suaveMascara.length);
    for (let i = 0; i < salida.length; i += 1) {
        const normalizado = suaveMascara[i] / maximo;
        salida[i] = normalizado <= 0.12 ? 0 : normalizado;
    }
    return salida;
}

function mascaraGluteos(mesh, avisos) {
    return mascaraPorHuesos(mesh, [
        { nombres: LADOS_PELVIS, semilla: semillaGluteoPelvis },
        { nombres: LADOS_CADERA, semilla: semillaGluteoPierna },
    ], avisos, "gluteos");
}

function mascaraIsquios(mesh, avisos) {
    return mascaraPorHuesos(mesh, [
        { nombres: LADOS_CUADRICEPS, semilla: semillaIsquio },
    ], avisos, "isquiotibiales");
}

const HUESOS_ABDOMEN = ["spine03", "spine04"];

function semillaAbdomen(local) {
    if (local.z < 0.075) return 0;
    if (Math.abs(local.x) > 0.11) return 0;
    return 1;
}

function semillaPectoral(local) {
    if (local.z < 0.095 || local.y > 0.16 || Math.abs(local.x) > 0.14) return 0;
    return 1;
}

function semillaDeltoides(local) {
    if (local.y > 0.09) return 0;
    return 1;
}

function semillaBiceps(local) {
    if (local.z < 0.028 || local.y < -0.01 || local.y > 0.17) return 0;
    return 1;
}

function semillaTriceps(local) {
    if (local.z > -0.005 || local.y < -0.02 || local.y > 0.17) return 0;
    return 1;
}

function semillaTrapecio(local) {
    if (local.z > 0.015 || Math.abs(local.x) > 0.09) return 0;
    return 1;
}

function semillaEspaldaMedia(local) {
    if (local.z > 0.02 || Math.abs(local.x) > 0.08) return 0;
    return 1;
}

function semillaDorsal(local) {
    const lateral = Math.abs(local.x);
    if (local.z > 0.02 || lateral < 0.045 || lateral > 0.16) return 0;
    return 1;
}

function semillaLumbar(local) {
    if (local.z > 0.02 || Math.abs(local.x) > 0.08) return 0;
    return 1;
}

function semillaGemelo(local) {
    if (local.z < 0.012) return 0;
    return 1;
}

function semillaAbductor(local, lado) {
    const lateral = lado === "L" ? local.x > 0.03 : local.x < -0.03;
    if (!lateral || Math.abs(local.z) > 0.045 || local.y < 0.05 || local.y > 0.28) return 0;
    return 1;
}

function semillaAductor(local, lado) {
    const medial = lado === "L" ? local.x < -0.02 : local.x > 0.02;
    if (!medial || local.z > 0.02 || local.y < 0.06 || local.y > 0.26) return 0;
    return 1;
}

const ZONAS_SUPERFICIE = {
    abdominales: { prenda: true, grupos: [{ nombres: HUESOS_ABDOMEN, semilla: semillaAbdomen }] },
    pectorales: { prenda: true, grupos: [{ nombres: ["spine02"], semilla: semillaPectoral }] },
    deltoides: { prenda: true, grupos: [{ nombres: ["upperarm01.L", "upperarm01.R"], semilla: semillaDeltoides }] },
    biceps: { prenda: false, grupos: [{ nombres: ["upperarm02.L", "upperarm02.R"], semilla: semillaBiceps }] },
    triceps: { prenda: false, grupos: [{ nombres: ["upperarm02.L", "upperarm02.R"], semilla: semillaTriceps }] },
    antebrazos: { prenda: false, grupos: [{ nombres: ["lowerarm01.L", "lowerarm01.R", "lowerarm02.L", "lowerarm02.R"], semilla: () => 1 }] },
    trapecios: { prenda: true, grupos: [{ nombres: ["spine01"], semilla: semillaTrapecio }] },
    espalda_media: { prenda: true, grupos: [{ nombres: ["spine02"], semilla: semillaEspaldaMedia }] },
    dorsales: { prenda: true, grupos: [{ nombres: ["spine02", "spine03"], semilla: semillaDorsal }] },
    lumbar: { prenda: true, grupos: [{ nombres: ["spine04", "spine05"], semilla: semillaLumbar }] },
    gemelos: { prenda: false, grupos: [{ nombres: ["lowerleg01.L", "lowerleg01.R", "lowerleg02.L", "lowerleg02.R"], semilla: semillaGemelo }] },
    cuello: { prenda: false, grupos: [{ nombres: ["neck01"], semilla: () => 1 }] },
    abductores: {
        prenda: false,
        grupos: [
            { nombres: ["upperleg02.L"], semilla: (local) => semillaAbductor(local, "L") },
            { nombres: ["upperleg02.R"], semilla: (local) => semillaAbductor(local, "R") },
        ],
    },
    aductores: {
        prenda: false,
        grupos: [
            { nombres: ["upperleg02.L"], semilla: (local) => semillaAductor(local, "L") },
            { nombres: ["upperleg02.R"], semilla: (local) => semillaAductor(local, "R") },
        ],
    },
};

function mallaPrenda(raiz, patron) {
    let prenda = null;
    raiz.traverse((obj) => {
        if (obj.isSkinnedMesh && patron.test(obj.name)) prenda = obj;
    });
    return prenda;
}

function combinarMascaras(partes) {
    const salida = new Float32Array(partes[0].length);
    partes.forEach((pesos) => {
        for (let i = 0; i < salida.length; i += 1) salida[i] = Math.max(salida[i], pesos[i]);
    });
    return salida;
}

function mascaraAutomatica(mesh, raiz, avisos) {
    const huesos = LADOS_CUADRICEPS.map((nombre) => {
        const mapa = mapaHueso(mesh, nombre);
        const bone = huesoDe(mesh, nombre);
        if (!mapa || !bone) avisos.push(`No está el hueso ${nombre} para cuadriceps.`);
        return mapa && bone ? { mapa, indice: mesh.skeleton.bones.indexOf(bone), lado: nombre.endsWith("L") ? "L" : "R" } : null;
    }).filter(Boolean);
    if (!huesos.length) return null;
    const pos = mesh.geometry.attributes.position;
    const falda = dobladillo(raiz);
    const crudo = new Float32Array(pos.count);
    for (let i = 0; i < pos.count; i += 1) {
        if (pos.getY(i) > falda - 0.012) continue;
        _p.set(pos.getX(i), pos.getY(i), pos.getZ(i));
        let mejor = 0;
        huesos.forEach((hueso) => {
            if (pesoEnHueso(mesh.geometry, i, hueso.indice) < 0.22) return;
            _q.copy(_p).applyMatrix4(hueso.mapa);
            mejor = Math.max(mejor, semillaIsla(_q, hueso.lado));
        });
        crudo[i] = mejor;
    }
    const suaveMascara = suavizar(crudo, mesh.geometry, 1);
    let maximo = 0;
    for (let i = 0; i < suaveMascara.length; i += 1) maximo = Math.max(maximo, suaveMascara[i]);
    if (maximo <= 0) {
        avisos.push("cuadriceps no cubre vértices de la piel. Hay que calibrarlo.");
        return null;
    }
    const salida = new Float32Array(suaveMascara.length);
    for (let i = 0; i < salida.length; i += 1) {
        const normalizado = suaveMascara[i] / maximo;
        salida[i] = normalizado <= 0.12 ? 0 : normalizado;
    }
    return salida;
}

function mascaraValida(pesos) {
    let fuertes = 0;
    for (let i = 0; i < pesos.length; i += 1) {
        if (pesos[i] > 0.45) fuertes += 1;
    }
    return fuertes >= 24;
}

function claveMascara(sexoAvatar) {
    return `biocinetica-cuadriceps-uv1-${sexoAvatar}`;
}

function mascaraGuardada(sexoAvatar, cantidad) {
    try {
        const texto = localStorage.getItem(claveMascara(sexoAvatar));
        if (!texto) return null;
        const datos = JSON.parse(texto);
        if (!Array.isArray(datos) || datos.length !== cantidad) return null;
        return Float32Array.from(datos);
    } catch {
        return null;
    }
}

function guardarMascara(sexoAvatar, atributo) {
    try {
        localStorage.setItem(claveMascara(sexoAvatar), JSON.stringify(Array.from(atributo.array)));
    } catch {
        console.info("No se pudo guardar la calibración de cuadriceps.");
    }
}

function materialPiel(mesh, raiz) {
    const original = Array.isArray(mesh.material) ? mesh.material[0] : mesh.material;
    if (!original || (!original.isMeshStandardMaterial && !original.isMeshPhysicalMaterial)) return null;
    let usos = 0;
    raiz.traverse((obj) => {
        if (!obj.isMesh || !obj.material) return;
        const lista = Array.isArray(obj.material) ? obj.material : [obj.material];
        if (lista.includes(original)) usos += 1;
    });
    const destino = usos > 1 ? original.clone() : original;
    if (destino !== original) {
        if (Array.isArray(mesh.material)) mesh.material[0] = destino;
        else mesh.material = destino;
    }
    return { destino, propio: destino !== original };
}

function pesosCuadriceps(mesh, raiz, sexoAvatar, avisos) {
    const cantidad = mesh.geometry.attributes.position.count;
    const guardada = mascaraGuardada(sexoAvatar, cantidad);
    let pesos = guardada || mascaraAutomatica(mesh, raiz, avisos);
    if (pesos && !mascaraValida(pesos)) {
        if (guardada) avisos.push("La calibración guardada no cubre el cuádriceps. Se usa la máscara de la isla.");
        pesos = mascaraAutomatica(mesh, raiz, avisos);
    }
    if (guardada && pesos) avisos.push("cuadriceps usa la calibración guardada en este navegador.");
    return pesos && mascaraValida(pesos) ? pesos : null;
}

function aplicarMarca(mesh, raiz, pesos, avisos, yaDegradada) {
    const piel = materialPiel(mesh, raiz);
    if (!piel) {
        avisos.push("El material de la piel no admite la marca muscular.");
        return null;
    }
    if (!pesos || !mascaraValida(pesos)) {
        avisos.push("No hay máscara válida para los músculos de este ejercicio.");
        return null;
    }
    if (!yaDegradada) pesos = degradarMascara(pesos, mesh.geometry);
    const atributo = new THREE.BufferAttribute(pesos, 1);
    mesh.geometry.setAttribute("aCuadriceps", atributo);
    const { destino, propio } = piel;
    const compilarAntes = destino.onBeforeCompile;
    const claveAntes = destino.customProgramCacheKey;
    destino.onBeforeCompile = (shader) => {
        if (compilarAntes) compilarAntes(shader);
        shader.uniforms.uTurquesa = { value: colorTurquesa };
        shader.uniforms.uCian = { value: colorCian };
        shader.vertexShader = shader.vertexShader
            .replace("#include <common>", "#include <common>\nattribute float aCuadriceps;\nvarying float vCuadriceps;")
            .replace("#include <begin_vertex>", "#include <begin_vertex>\nvCuadriceps = aCuadriceps;");
        shader.fragmentShader = shader.fragmentShader
            .replace("#include <common>", "#include <common>\nvarying float vCuadriceps;\nuniform vec3 uTurquesa;\nuniform vec3 uCian;")
            .replace(
                "#include <color_fragment>",
                `#include <color_fragment>
                float t = smoothstep(0.12, 0.92, vCuadriceps);
                t = t * t;
                diffuseColor.rgb = mix(diffuseColor.rgb, uTurquesa, t * 0.42);`,
            )
            .replace(
                "#include <emissivemap_fragment>",
                `#include <emissivemap_fragment>
                totalEmissiveRadiance += uTurquesa * t * 0.05 + uCian * t * t * 0.03;`,
            );
    };
    destino.customProgramCacheKey = function claveCuadriceps() {
        return "cuadriceps-degradado";
    };
    destino.needsUpdate = true;
    return {
        atributo,
        quitar() {
            mesh.geometry.deleteAttribute("aCuadriceps");
            destino.onBeforeCompile = compilarAntes;
            destino.customProgramCacheKey = claveAntes;
            destino.needsUpdate = true;
            if (propio) destino.dispose();
        },
    };
}

function impactoSobrePiel(mesh, ray) {
    mesh.updateMatrixWorld(true);
    const index = mesh.geometry.index;
    const total = index ? index.count : mesh.geometry.attributes.position.count;
    const a = new THREE.Vector3();
    const b = new THREE.Vector3();
    const c = new THREE.Vector3();
    const candidato = new THREE.Vector3();
    const idDe = (n) => (index ? index.getX(n) : n);
    let mejor = Infinity;
    let punto = null;
    for (let i = 0; i < total; i += 3) {
        mesh.getVertexPosition(idDe(i), a).applyMatrix4(mesh.matrixWorld);
        mesh.getVertexPosition(idDe(i + 1), b).applyMatrix4(mesh.matrixWorld);
        mesh.getVertexPosition(idDe(i + 2), c).applyMatrix4(mesh.matrixWorld);
        if (!ray.intersectTriangle(a, b, c, false, candidato)) continue;
        const distancia = ray.origin.distanceToSquared(candidato);
        if (distancia >= mejor) continue;
        mejor = distancia;
        punto = candidato.clone();
    }
    return punto;
}

function pintarCerca(mesh, atributo, punto, suma) {
    mesh.updateMatrixWorld(true);
    const radio = 0.038;
    const pos = mesh.geometry.attributes.position;
    const marca = new THREE.Vector3();
    for (let i = 0; i < pos.count; i += 1) {
        mesh.getVertexPosition(i, marca).applyMatrix4(mesh.matrixWorld);
        const distancia = marca.distanceTo(punto);
        if (distancia > radio) continue;
        const caida = 1 - distancia / radio;
        const peso = THREE.MathUtils.clamp(atributo.getX(i) + suma * caida * caida, 0, 1);
        atributo.setX(i, peso);
    }
    atributo.needsUpdate = true;
}

function instalarCalibracion(mesh, sexoAvatar, atributo, regenerar) {
    const canvas = document.querySelector("#visor");
    if (!canvas) return () => {};
    const raycaster = new THREE.Raycaster();
    const puntero = new THREE.Vector2();
    let activo = false;
    let origen = null;
    const aviso = document.createElement("p");
    aviso.hidden = true;
    aviso.textContent = "Máscara del cuádriceps: clic suma, Mayús+clic resta, R restaura la isla. Pulsa C para salir y guardar. Conviene estar de pie.";
    aviso.style.cssText = "position:fixed;left:16px;bottom:16px;z-index:50;margin:0;max-width:300px;padding:8px 12px;border-radius:10px;background:rgba(12,22,38,.96);border:1px solid rgba(30,200,212,.55);color:#d7fbff;font:600 0.82rem/1.35 Segoe UI,sans-serif;";
    document.body.append(aviso);

    function alTecla(evento) {
        const etiqueta = evento.target && evento.target.tagName;
        if (etiqueta === "INPUT" || etiqueta === "TEXTAREA") return;
        if ((evento.key === "r" || evento.key === "R") && activo && regenerar) {
            const nueva = regenerar();
            if (!nueva) return;
            atributo.array.set(nueva);
            atributo.needsUpdate = true;
            guardarMascara(sexoAvatar, atributo);
            return;
        }
        if (evento.key !== "c" && evento.key !== "C") return;
        activo = !activo;
        aviso.hidden = !activo;
        if (!activo) guardarMascara(sexoAvatar, atributo);
    }

    function alAbajo(evento) {
        origen = { x: evento.clientX, y: evento.clientY };
    }

    function alArriba(evento) {
        if (!activo || !origen) return;
        const dx = evento.clientX - origen.x;
        const dy = evento.clientY - origen.y;
        origen = null;
        if (dx * dx + dy * dy > 16) return;
        const camara = window.__visor && window.__visor.controls && window.__visor.controls.object;
        if (!camara) return;
        const rect = canvas.getBoundingClientRect();
        puntero.x = ((evento.clientX - rect.left) / rect.width) * 2 - 1;
        puntero.y = -((evento.clientY - rect.top) / rect.height) * 2 + 1;
        raycaster.setFromCamera(puntero, camara);
        const punto = impactoSobrePiel(mesh, raycaster.ray);
        if (!punto) return;
        pintarCerca(mesh, atributo, punto, evento.shiftKey ? -0.85 : 0.85);
        guardarMascara(sexoAvatar, atributo);
    }

    window.addEventListener("keydown", alTecla);
    canvas.addEventListener("pointerdown", alAbajo);
    canvas.addEventListener("pointerup", alArriba);
    return () => {
        window.removeEventListener("keydown", alTecla);
        canvas.removeEventListener("pointerdown", alAbajo);
        canvas.removeEventListener("pointerup", alArriba);
        aviso.remove();
    };
}

const CHISPA_VERTICE = `
attribute float tamano;
attribute float vida;
attribute float brillo;
attribute vec3 colorChispa;
uniform float pixelRatio;
varying float vVida;
varying float vBrillo;
varying vec3 vColor;
void main() {
    vVida = vida;
    vBrillo = brillo;
    vColor = colorChispa;
    vec4 vista = modelViewMatrix * vec4(position, 1.0);
    float perspectiva = clamp(52.0 / max(-vista.z, 0.45), 2.8, 7.2);
    gl_PointSize = tamano * perspectiva * pixelRatio;
    gl_Position = projectionMatrix * vista;
}
`;

const CHISPA_FRAGMENTO = `
varying float vVida;
varying float vBrillo;
varying vec3 vColor;
void main() {
    vec2 p = gl_PointCoord * 2.0 - 1.0;
    float d = dot(p, p);
    if (d > 1.0) discard;
    float glow = exp(-d * 2.35);
    float nucleo = exp(-d * 7.5);
    float vida = clamp(vVida, 0.0, 1.0);
    float alpha = glow * mix(0.62, 0.92, vBrillo) * mix(0.45, 1.0, vida);
    if (alpha < 0.04) discard;
    vec3 turquesa = vec3(0.078, 0.722, 0.651);
    vec3 cian = vec3(0.157, 0.941, 0.906);
    vec3 color = mix(turquesa, cian, nucleo * 0.42 * vBrillo);
    gl_FragColor = vec4(color, min(alpha, 0.82));
}
`;

function mapasMuslo(mesh) {
    return LADOS_CUADRICEPS.map((nombre) => {
        const mapa = mapaHueso(mesh, nombre);
        const bone = huesoDe(mesh, nombre);
        if (!mapa || !bone) return null;
        return { mapa, indice: mesh.skeleton.bones.indexOf(bone) };
    }).filter(Boolean);
}

function candidatosChispa(mesh, pesos) {
    const mapas = mapasMuslo(mesh);
    const pos = mesh.geometry.attributes.position;
    const lista = [];
    for (let i = 0; i < pesos.length; i += 1) {
        const base = pesos[i];
        if (base < 0.38) continue;
        let altura = null;
        let mejor = 0.2;
        _p.set(pos.getX(i), pos.getY(i), pos.getZ(i));
        mapas.forEach((hueso) => {
            const peso = pesoEnHueso(mesh.geometry, i, hueso.indice);
            if (peso < mejor) return;
            mejor = peso;
            _q.copy(_p).applyMatrix4(hueso.mapa);
            altura = _q.y;
        });
        const rodilla = altura == null ? 1 : 1 - THREE.MathUtils.smoothstep(altura, 0.15, 0.22);
        const borde = THREE.MathUtils.smoothstep(base, 0.32, 0.72);
        const peso = base * rodilla * borde;
        if (peso < 0.16) continue;
        lista.push({ id: i, peso });
    }
    return lista;
}

function elegirLejos(candidatos, ocupados, pos, rng, separacion) {
    const limite = separacion * separacion;
    let total = 0;
    candidatos.forEach((item) => {
        total += item.peso;
    });
    if (total <= 0) return null;
    for (let intento = 0; intento < 28; intento += 1) {
        let marca = rng() * total;
        let elegido = candidatos[candidatos.length - 1];
        for (let i = 0; i < candidatos.length; i += 1) {
            marca -= candidatos[i].peso;
            if (marca <= 0) {
                elegido = candidatos[i];
                break;
            }
        }
        if (ocupados.has(elegido.id)) continue;
        let cerca = false;
        ocupados.forEach((id) => {
            const dx = pos.getX(elegido.id) - pos.getX(id);
            const dy = pos.getY(elegido.id) - pos.getY(id);
            const dz = pos.getZ(elegido.id) - pos.getZ(id);
            if (dx * dx + dy * dy + dz * dz < limite) cerca = true;
        });
        if (!cerca) return elegido.id;
    }
    return null;
}

function pintarColorChispa(rng, destino, indice) {
    const mezcla = rng() * 0.55;
    const desde = rng() < 0.35 ? PROFUNDO_PANTALLA : TURQUESA_PANTALLA;
    destino[indice * 3] = desde[0] + (CIAN_PANTALLA[0] - desde[0]) * mezcla;
    destino[indice * 3 + 1] = desde[1] + (CIAN_PANTALLA[1] - desde[1]) * mezcla;
    destino[indice * 3 + 2] = desde[2] + (CIAN_PANTALLA[2] - desde[2]) * mezcla;
}

function instalarChispas(mesh, raiz, atributo, avisos) {
    const candidatos = candidatosChispa(mesh, atributo.array);
    if (candidatos.length < 12) {
        avisos.push("La máscara no deja sitio suficiente para chispas separadas.");
        return null;
    }
    const cupo = Math.min(reducido() ? 28 : 52, candidatos.length);
    const rng = aleatorio(candidatos.length * 131 + cupo);
    const pos = mesh.geometry.attributes.position;
    const ocupados = new Set();
    const chispas = [];
    for (let i = 0; i < cupo; i += 1) {
        const id = elegirLejos(candidatos, ocupados, pos, rng, 0.028);
        if (id == null) break;
        ocupados.add(id);
        chispas.push({
            id,
            edad: rng() * VIDA_CHISPA,
            separacion: 0.003 + rng() * 0.003,
            tamano: 0.62 + rng() * 0.48,
            brillo: 0.58 + rng() * 0.42,
        });
    }
    if (!chispas.length) return null;
    const posiciones = new Float32Array(chispas.length * 3);
    const tamanos = new Float32Array(chispas.length);
    const vidas = new Float32Array(chispas.length);
    const brillos = new Float32Array(chispas.length);
    const colores = new Float32Array(chispas.length * 3);
    chispas.forEach((chispa, i) => {
        tamanos[i] = chispa.tamano;
        brillos[i] = chispa.brillo;
        vidas[i] = 1 - chispa.edad / VIDA_CHISPA;
        pintarColorChispa(rng, colores, i);
    });
    const geometria = new THREE.BufferGeometry();
    geometria.setAttribute("position", new THREE.BufferAttribute(posiciones, 3));
    geometria.setAttribute("tamano", new THREE.BufferAttribute(tamanos, 1));
    geometria.setAttribute("vida", new THREE.BufferAttribute(vidas, 1));
    geometria.setAttribute("brillo", new THREE.BufferAttribute(brillos, 1));
    geometria.setAttribute("colorChispa", new THREE.BufferAttribute(colores, 3));
    const material = new THREE.ShaderMaterial({
        uniforms: { pixelRatio: { value: Math.min(window.devicePixelRatio || 1, 2) } },
        vertexShader: CHISPA_VERTICE,
        fragmentShader: CHISPA_FRAGMENTO,
        transparent: true,
        depthWrite: false,
        blending: THREE.NormalBlending,
        toneMapped: false,
    });
    const puntos = new THREE.Points(geometria, material);
    puntos.frustumCulled = false;
    puntos.renderOrder = 3;
    mesh.add(puntos);
    let ultimo = 0;
    return {
        actualizar(tiempo) {
            const dt = Math.min(Math.max(tiempo - ultimo, 0), 0.05);
            ultimo = tiempo;
            raiz.updateMatrixWorld(true);
            const destino = geometria.attributes.position;
            const atributoVida = geometria.attributes.vida;
            chispas.forEach((chispa, i) => {
                chispa.edad += dt;
                if (chispa.edad >= VIDA_CHISPA) {
                    ocupados.delete(chispa.id);
                    const id = elegirLejos(candidatos, ocupados, pos, rng, 0.028);
                    if (id != null) {
                        chispa.id = id;
                        ocupados.add(id);
                        chispa.edad = 0;
                        chispa.separacion = 0.003 + rng() * 0.003;
                    } else {
                        ocupados.add(chispa.id);
                        chispa.edad = 0;
                    }
                }
                pegar(mesh, chispa.id, chispa.separacion, destino, i);
                const pulso = 0.82 + 0.18 * Math.sin(tiempo * 2.1 + i);
                atributoVida.setX(i, (1 - chispa.edad / VIDA_CHISPA) * pulso);
            });
            destino.needsUpdate = true;
            atributoVida.needsUpdate = true;
        },
        quitar() {
            puntos.parent?.remove(puntos);
            geometria.dispose();
            material.dispose();
        },
    };
}

export function colocarSenales(raiz, musculos, sexoAvatar) {
    const avisos = [];
    const mesh = mallaCuerpo(raiz);
    const tabla = regiones[sexoAvatar] || {};
    const factor = reducido() ? 0.5 : 1;
    const muestras = [];
    let limpiarLuz = () => {};
    let limpiarCalibracion = () => {};
    let chispas = null;
    const pedidos = musculos || [];
    const conMascara = new Set(["cuadriceps", "gluteos", "isquiotibiales", ...Object.keys(ZONAS_SUPERFICIE)]);
    pedidos.forEach((musculo) => {
        if (!musculo || conMascara.has(musculo.id)) return;
        avisos.push(`${musculo.id} no tiene máscara de superficie. El ejercicio lo lista y el avatar no marca esa zona.`);
    });
    const quiere = (id) => pedidos.some((musculo) => musculo && musculo.id === id);

    if (!mesh || typeof mesh.getVertexPosition !== "function") {
        avisos.push("Este modelo no tiene una malla con piel deformable.");
    } else if (mostrarChispas && pedidos.some((musculo) => musculo && conMascara.has(musculo.id))) {
        const partes = [];
        if (quiere("cuadriceps")) {
            const pesos = pesosCuadriceps(mesh, raiz, sexoAvatar, avisos);
            if (pesos) partes.push(pesos);
            else avisos.push("No hay máscara válida de cuadriceps.");
        }
        if (quiere("gluteos")) {
            const pesos = mascaraGluteos(mesh, avisos);
            if (pesos) partes.push(pesos);
        }
        if (quiere("isquiotibiales")) {
            const pesos = mascaraIsquios(mesh, avisos);
            if (pesos) partes.push(pesos);
        }
        const degradadas = partes.map((pesos) => degradarMascara(pesos, mesh.geometry));
        const luz = degradadas.length ? aplicarMarca(mesh, raiz, degradadas.length === 1 ? degradadas[0] : combinarMascaras(degradadas), avisos, true) : null;
        if (luz) {
            limpiarLuz = luz.quitar;
            if (quiere("cuadriceps")) {
                limpiarCalibracion = instalarCalibracion(mesh, sexoAvatar, luz.atributo, () => mascaraAutomatica(mesh, raiz, avisos));
            }
            chispas = instalarChispas(mesh, raiz, luz.atributo, avisos);
        }
        const lucesZona = [];
        let visible = null;
        Object.entries(ZONAS_SUPERFICIE).forEach(([id, zona]) => {
            if (!quiere(id)) return;
            const superficies = [mesh];
            const prenda = zona.prenda ? mallaPrenda(raiz, /shirt/i) : null;
            if (prenda && prenda !== mesh) superficies.push(prenda);
            superficies.forEach((superficie) => {
                const pesos = mascaraPorHuesos(superficie, zona.grupos, avisos, id);
                if (!pesos) return;
                const luzZona = aplicarMarca(superficie, raiz, degradarMascara(pesos, superficie.geometry), avisos, true);
                if (!luzZona) return;
                lucesZona.push(luzZona);
                const esVisible = prenda && superficie === prenda;
                if (esVisible || !visible) visible = { superficie, luz: luzZona };
            });
        });
        if (lucesZona.length) {
            const quitarPiernas = limpiarLuz;
            limpiarLuz = () => {
                quitarPiernas();
                lucesZona.forEach((luzZona) => luzZona.quitar());
            };
            if (!chispas && visible) chispas = instalarChispas(visible.superficie, raiz, visible.luz.atributo, avisos);
        }
    }

    if (mostrarParticulas && mesh && typeof mesh.getVertexPosition === "function") {
        (musculos || []).forEach((musculo) => {
            if (musculo.id !== "cuadriceps") return;
            const anclas = tabla[musculo.id];
            if (!anclas) {
                avisos.push(`${musculo.id} no está calibrado en ${sexoAvatar}.`);
                return;
            }
            const cupo = Math.max(6, Math.round(10 * factor));
            anclas.forEach((ancla) => {
                const ids = verticesEnCaja(mesh, ancla.hueso, ancla.caja);
                if (ids == null) {
                    avisos.push(`No está el hueso ${ancla.hueso} para ${musculo.id}.`);
                    return;
                }
                if (!ids.length) {
                    avisos.push(`${musculo.id} (${ancla.hueso}) no cubre vértices. Hay que calibrar la caja.`);
                    return;
                }
                const rng = aleatorio(ids[0] + ids.length * 17);
                recortar(ids, cupo).forEach((id, orden) => {
                    muestras.push({
                        id,
                        separacion: ancla.separacion,
                        capa: 0,
                        tamano: 3.4 + rng() * 1.6,
                        fase: rng(),
                        brillo: 0.72 + rng() * 0.28,
                        color: orden % 2 === 0 ? colorChispa : colorTurquesa,
                    });
                });
            });
        });
    }

    const material = mostrarParticulas ? crearMaterial() : null;
    let puntos = null;
    if (mostrarParticulas && mesh && muestras.length) {
        const posiciones = new Float32Array(muestras.length * 3);
        const tamanos = new Float32Array(muestras.length);
        const fases = new Float32Array(muestras.length);
        const brillos = new Float32Array(muestras.length);
        const capas = new Float32Array(muestras.length);
        const colores = new Float32Array(muestras.length * 3);
        muestras.forEach((muestra, i) => {
            tamanos[i] = muestra.tamano;
            fases[i] = muestra.fase;
            brillos[i] = muestra.brillo;
            capas[i] = muestra.capa;
            colores[i * 3] = muestra.color.r;
            colores[i * 3 + 1] = muestra.color.g;
            colores[i * 3 + 2] = muestra.color.b;
        });
        const geometria = new THREE.BufferGeometry();
        geometria.setAttribute("position", new THREE.BufferAttribute(posiciones, 3));
        geometria.setAttribute("tamano", new THREE.BufferAttribute(tamanos, 1));
        geometria.setAttribute("fase", new THREE.BufferAttribute(fases, 1));
        geometria.setAttribute("brillo", new THREE.BufferAttribute(brillos, 1));
        geometria.setAttribute("capa", new THREE.BufferAttribute(capas, 1));
        geometria.setAttribute("colorChispa", new THREE.BufferAttribute(colores, 3));
        puntos = new THREE.Points(geometria, material);
        puntos.frustumCulled = false;
        puntos.renderOrder = 2;
        mesh.add(puntos);
    } else if (material) {
        material.dispose();
    }

    if (avisos.length) console.info(avisos.join(" "));

    function actualizar(tiempo) {
        if (chispas) chispas.actualizar(tiempo);
        if (!mostrarParticulas || !puntos || !mesh || !material) return;
        material.uniforms.tiempo.value = tiempo;
        raiz.updateMatrixWorld(true);
        const destino = puntos.geometry.attributes.position;
        muestras.forEach((muestra, i) => pegar(mesh, muestra.id, muestra.separacion, destino, i));
        destino.needsUpdate = true;
    }

    if (mostrarParticulas || chispas) actualizar(0);

    return {
        avisos,
        actualizar,
        quitar() {
            limpiarCalibracion();
            limpiarLuz();
            if (chispas) {
                chispas.quitar();
                chispas = null;
            }
            if (!puntos) return;
            puntos.parent?.remove(puntos);
            puntos.geometry.dispose();
            material.dispose();
            puntos = null;
        },
    };
}
