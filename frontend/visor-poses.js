// Gestos del visor. No reexporta el GLB: parte de la sentadilla ya cargada,
// baja los brazos y arma un ciclo de 2 s por familia. Los huesos se apuntan
// por su eje largo (Y en el mundo). No son límites anatómicos.

import * as THREE from "three";

const BRAZOS = [
    "upperarm01L", "upperarm02L", "lowerarm01L", "lowerarm02L", "wristL",
    "upperarm01R", "upperarm02R", "lowerarm01R", "lowerarm02R", "wristR",
];

const RECTOS = [
    "upperarm02L", "lowerarm01L", "lowerarm02L", "wristL",
    "upperarm02R", "lowerarm01R", "lowerarm02R", "wristR",
];

const ORDEN = [
    ["sentadilla", /sentadilla|\bsquats?\b/i],
    ["zancada", /zancada|\blunges?\b/i],
    ["peso_muerto", /peso muerto|\bdeadlifts?\b|buenos d[ií]as/i],
    ["plancha", /plancha|\bplanks?\b/i],
    ["remo", /\bremo\b|\brows?\b/i],
    ["curl", /\bcurls?\b/i],
    ["press", /\bpress\b/i],
];

const DURACION = 2;
const PASOS = 8;

export function familiaDe(ficha) {
    const texto = ficha
        ? `${ficha.TITLE_ES || ""} ${ficha.TITLE_EN || ""}`
        : "Sentadilla con peso corporal";
    for (const [id, regla] of ORDEN) {
        if (regla.test(texto)) return id;
    }
    return null;
}

export function prepararClips(modelo, clipSentadilla) {
    const mezcla = new THREE.AnimationMixer(modelo);
    const muestra = mezcla.clipAction(clipSentadilla);
    muestra.play();
    muestra.time = 0;
    mezcla.update(0);
    bajarBrazos(modelo);
    const quieta = foto(modelo);
    const suelo = alturaDe(modelo, PIES);
    brazosAlFrente(modelo);
    const frente = foto(modelo);
    restaurar(modelo, quieta);
    brazosSegunBajada(clipSentadilla, quieta, frente);
    mezcla.stopAllAction();
    mezcla.uncacheRoot(modelo);

    const api = crearApi(modelo, suelo);
    const gestos = {
        zancada: gestoZancada,
        peso_muerto: gestoPeso,
        plancha: gestoPlancha,
        remo: gestoRemo,
        curl: gestoCurl,
        press: gestoPress,
    };
    const clips = { sentadilla: clipSentadilla };
    Object.entries(gestos).forEach(([nombre, aplicar]) => {
        restaurar(modelo, quieta);
        aplicar(api);
        clips[nombre] = clipEntre(nombre, quieta, foto(modelo));
    });
    restaurar(modelo, quieta);
    return clips;
}

function crearApi(modelo, suelo) {
    return {
        apuntar(nombre, dir) {
            apuntar(modelo, nombre, dir);
        },
        recto(nombre) {
            const hueso = buscarHueso(modelo, nombre);
            if (hueso) hueso.rotation.set(0, 0, 0);
        },
        brazos() {
            bajarBrazos(modelo);
        },
        alzar(radianes) {
            flexionarHombro(modelo, "upperarm01L", radianes);
            flexionarHombro(modelo, "upperarm01R", radianes);
        },
        suelo(nombres = PIES) {
            apoyarSuelo(modelo, suelo, nombres);
        },
        inclinar(radianes) {
            girarRaiz(modelo, [1, 0, 0], radianes);
        },
        girar(radianes) {
            girarRaiz(modelo, [0, 1, 0], radianes);
        },
    };
}

function gestoZancada(api) {
    api.brazos();
    api.apuntar("upperleg01L", [0.05, -0.48, 0.88]);
    api.apuntar("upperleg02L", [0.04, -0.42, 0.91]);
    api.apuntar("lowerleg01L", [0.02, -0.97, 0.22]);
    api.apuntar("lowerleg02L", [0.01, -0.99, 0.1]);
    api.apuntar("upperleg01R", [-0.03, -0.5, -0.86]);
    api.apuntar("upperleg02R", [-0.03, -0.46, -0.89]);
    api.apuntar("lowerleg01R", [0, -0.98, -0.18]);
    api.apuntar("lowerleg02R", [0, -0.99, -0.08]);
    api.suelo();
}

function gestoPeso(api) {
    api.apuntar("spine05", [0, 0.86, 0.51]);
    api.apuntar("upperleg01L", [0.1, -0.86, 0.5]);
    api.apuntar("upperleg02L", [0.08, -0.88, 0.46]);
    api.apuntar("lowerleg01L", [0.04, -0.95, -0.3]);
    api.apuntar("lowerleg02L", [0.02, -0.98, -0.16]);
    api.apuntar("upperleg01R", [-0.1, -0.86, 0.5]);
    api.apuntar("upperleg02R", [-0.08, -0.88, 0.46]);
    api.apuntar("lowerleg01R", [-0.04, -0.95, -0.3]);
    api.apuntar("lowerleg02R", [-0.02, -0.98, -0.16]);
    api.brazos();
    api.suelo();
}

function gestoPress(api) {
    // Abrirlos a los lados, o subirlos más, rompe la sisa. Este giro los lleva al frente.
    api.alzar(-1.2);
}

function gestoRemo(api) {
    api.apuntar("spine05", [0, 0.72, 0.69]);
    api.brazos();
    api.apuntar("lowerarm01L", [0.22, 0.28, -0.93]);
    api.apuntar("lowerarm02L", [0.16, 0.22, -0.96]);
    api.recto("wristL");
    api.apuntar("lowerarm01R", [-0.22, 0.28, -0.93]);
    api.apuntar("lowerarm02R", [-0.16, 0.22, -0.96]);
    api.recto("wristR");
    api.suelo();
}

function gestoPlancha(api) {
    api.inclinar(Math.PI / 2);
    api.girar(Math.PI / 2);
    api.apuntar("upperarm01L", [0.08, -1, 0.02]);
    api.apuntar("upperarm01R", [-0.08, -1, 0.02]);
    RECTOS.forEach((nombre) => api.recto(nombre));
    api.apuntar("upperleg01L", [-0.82, -0.55, 0.05]);
    api.apuntar("upperleg02L", [-0.86, -0.5, 0.04]);
    api.apuntar("lowerleg01L", [-0.9, -0.42, 0.02]);
    api.apuntar("lowerleg02L", [-0.93, -0.35, 0.02]);
    api.apuntar("upperleg01R", [-0.82, -0.55, -0.05]);
    api.apuntar("upperleg02R", [-0.86, -0.5, -0.04]);
    api.apuntar("lowerleg01R", [-0.9, -0.42, -0.02]);
    api.apuntar("lowerleg02R", [-0.93, -0.35, -0.02]);
    api.suelo(APOYOS_PLANCHA);
}

function gestoCurl(api) {
    api.brazos();
    api.apuntar("lowerarm01L", [0.12, 0.55, 0.83]);
    api.apuntar("lowerarm02L", [0.1, 0.5, 0.86]);
    api.recto("wristL");
    api.apuntar("lowerarm01R", [-0.12, 0.55, 0.83]);
    api.apuntar("lowerarm02R", [-0.1, 0.5, 0.86]);
    api.recto("wristR");
}

function bajarBrazos(modelo) {
    // Bajar más el brazo, o enderezar el antebrazo, abre dos picos en el escote.
    orientar(modelo, "upperarm01L", [0.472, -0.881, -0.007], [0.045, 0.016, 0.999]);
    orientar(modelo, "upperarm01R", [-0.472, -0.881, -0.007], [-0.045, 0.016, 0.999]);
}

function brazosAlFrente(modelo) {
    // Un giro mayor vuelve a abrir el escote. Este apenas lleva el brazo adelante.
    flexionarHombro(modelo, "upperarm01L", -0.1);
    flexionarHombro(modelo, "upperarm01R", -0.1);
    modelo.updateMatrixWorld(true);
}

function flexionarHombro(modelo, nombre, radianes) {
    const hueso = buscarHueso(modelo, nombre);
    if (!hueso || !hueso.parent) return;
    hueso.parent.updateMatrixWorld(true);
    const padre = new THREE.Quaternion();
    hueso.parent.getWorldQuaternion(padre);
    const mundo = padre.clone().multiply(hueso.quaternion);
    const extra = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1, 0, 0), radianes);
    hueso.quaternion.copy(padre.clone().invert().multiply(extra.multiply(mundo)));
}

function orientar(modelo, nombre, dirY, dirZ) {
    const hueso = buscarHueso(modelo, nombre);
    if (!hueso || !hueso.parent) return;
    hueso.parent.updateMatrixWorld(true);
    const y = new THREE.Vector3(dirY[0], dirY[1], dirY[2]).normalize();
    const z = new THREE.Vector3(dirZ[0], dirZ[1], dirZ[2]);
    z.addScaledVector(y, -z.dot(y));
    if (z.lengthSq() < 1e-8) return;
    z.normalize();
    const x = new THREE.Vector3().crossVectors(y, z).normalize();
    z.crossVectors(x, y);
    const mundo = new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(x, y, z));
    const padre = new THREE.Quaternion();
    hueso.parent.getWorldQuaternion(padre);
    hueso.quaternion.copy(padre.invert().multiply(mundo));
    hueso.updateMatrixWorld(true);
}

function brazosSegunBajada(clip, quieta, frente) {
    const raiz = clip.tracks.find((item) => item.name === "root.position");
    if (!raiz) return;
    const times = Array.from(raiz.times);
    const alturas = times.map((tiempo) => componenteEn(raiz, tiempo, 1, 3));
    const alta = Math.max(...alturas);
    const baja = Math.min(...alturas);
    const rango = Math.max(alta - baja, 0.001);
    BRAZOS.forEach((nombre) => {
        const abajo = quieta.get(nombre);
        const alFrente = frente.get(nombre);
        if (!abajo || !alFrente) return;
        const values = [];
        alturas.forEach((altura) => {
            const peso = (alta - altura) / rango;
            const giro = abajo.q.clone().slerp(alFrente.q, peso);
            values.push(giro.x, giro.y, giro.z, giro.w);
        });
        ponerPista(clip, new THREE.QuaternionKeyframeTrack(`${nombre}.quaternion`, times, values));
    });
}

function componenteEn(pista, tiempo, componente, ancho) {
    const times = pista.times;
    const values = pista.values;
    const leer = (indice) => values[indice * ancho + componente];
    if (tiempo <= times[0]) return leer(0);
    const ultimo = times.length - 1;
    if (tiempo >= times[ultimo]) return leer(ultimo);
    let indice = 0;
    while (indice < ultimo && times[indice + 1] < tiempo) indice += 1;
    const tramo = times[indice + 1] - times[indice] || 1;
    const peso = (tiempo - times[indice]) / tramo;
    return leer(indice) + (leer(indice + 1) - leer(indice)) * peso;
}

function ponerPista(clip, pista) {
    const indice = clip.tracks.findIndex((item) => item.name === pista.name);
    if (indice >= 0) clip.tracks.splice(indice, 1, pista);
    else clip.tracks.push(pista);
}

function apuntar(modelo, nombre, dir) {
    const hueso = buscarHueso(modelo, nombre);
    if (!hueso || !hueso.parent) return;
    hueso.updateMatrixWorld(true);
    const mundo = new THREE.Quaternion();
    hueso.getWorldQuaternion(mundo);
    const arriba = new THREE.Vector3(0, 1, 0).applyQuaternion(mundo).normalize();
    const destino = new THREE.Vector3(dir[0], dir[1], dir[2]).normalize();
    const giro = new THREE.Quaternion();
    const alineado = arriba.dot(destino);
    if (alineado > 0.9995) return;
    if (alineado < -0.9995) {
        const eje = Math.abs(arriba.x) < 0.9 ? new THREE.Vector3(1, 0, 0) : new THREE.Vector3(0, 0, 1);
        eje.cross(arriba).normalize();
        giro.setFromAxisAngle(eje, Math.PI);
    } else {
        giro.setFromUnitVectors(arriba, destino);
    }
    const nuevoMundo = giro.multiply(mundo);
    const padre = new THREE.Quaternion();
    hueso.parent.getWorldQuaternion(padre);
    hueso.quaternion.copy(padre.invert().multiply(nuevoMundo));
    hueso.updateMatrixWorld(true);
}

function girarRaiz(modelo, eje, radianes) {
    const raiz = buscarHueso(modelo, "root");
    if (!raiz || !raiz.parent) return;
    raiz.updateMatrixWorld(true);
    const padre = new THREE.Quaternion();
    raiz.parent.getWorldQuaternion(padre);
    const mundo = new THREE.Quaternion();
    raiz.getWorldQuaternion(mundo);
    const extra = new THREE.Quaternion().setFromAxisAngle(
        new THREE.Vector3(eje[0], eje[1], eje[2]),
        radianes,
    );
    const nuevoMundo = extra.multiply(mundo);
    raiz.quaternion.copy(padre.invert().multiply(nuevoMundo));
    raiz.updateMatrixWorld(true);
}

const PIES = ["footL", "footR", "toe1-1L", "toe1-1R"];
const APOYOS_PLANCHA = ["wristL", "wristR", "toe1-1L", "toe1-1R"];

function alturaDe(modelo, nombres) {
    const punto = new THREE.Vector3();
    let bajo = Infinity;
    nombres.forEach((nombre) => {
        const hueso = buscarHueso(modelo, nombre);
        if (!hueso) return;
        hueso.updateMatrixWorld(true);
        bajo = Math.min(bajo, hueso.getWorldPosition(punto).y);
    });
    return bajo;
}

function apoyarSuelo(modelo, suelo, nombres) {
    const raiz = buscarHueso(modelo, "root");
    if (!raiz || !raiz.parent) return;
    const ahora = alturaDe(modelo, nombres);
    if (!Number.isFinite(ahora)) return;
    const delta = suelo - ahora;
    if (Math.abs(delta) < 0.004) return;
    raiz.parent.updateWorldMatrix(true, false);
    const padre = new THREE.Quaternion();
    raiz.parent.getWorldQuaternion(padre);
    raiz.position.add(new THREE.Vector3(0, delta, 0).applyQuaternion(padre.invert()));
    raiz.updateMatrixWorld(true);
}

function clipEntre(nombre, quieta, gesto) {
    const times = [];
    for (let i = 0; i <= PASOS; i += 1) times.push((i / PASOS) * DURACION);
    const pistas = [];
    quieta.forEach((inicio, nombreHueso) => {
        const fin = gesto.get(nombreHueso);
        if (!fin) return;
        const mueveGiro = inicio.q.angleTo(fin.q) > 0.02;
        const muevePos = inicio.p.distanceTo(fin.p) > 0.002;
        const fijo = BRAZOS.includes(nombreHueso);
        if (!mueveGiro && !muevePos && !fijo) return;
        if (mueveGiro || fijo) {
            const values = [];
            for (let i = 0; i <= PASOS; i += 1) {
                const peso = idaVuelta(i / PASOS);
                const q = inicio.q.clone().slerp(fin.q, peso);
                values.push(q.x, q.y, q.z, q.w);
            }
            pistas.push(new THREE.QuaternionKeyframeTrack(`${nombreHueso}.quaternion`, times.slice(), values));
        }
        if (muevePos) {
            const values = [];
            for (let i = 0; i <= PASOS; i += 1) {
                const peso = idaVuelta(i / PASOS);
                values.push(
                    inicio.p.x + (fin.p.x - inicio.p.x) * peso,
                    inicio.p.y + (fin.p.y - inicio.p.y) * peso,
                    inicio.p.z + (fin.p.z - inicio.p.z) * peso,
                );
            }
            pistas.push(new THREE.VectorKeyframeTrack(`${nombreHueso}.position`, times.slice(), values));
        }
    });
    return new THREE.AnimationClip(nombre, DURACION, pistas);
}

function idaVuelta(t) {
    const tri = t < 0.5 ? t * 2 : (1 - t) * 2;
    return tri * tri * (3 - 2 * tri);
}

function foto(modelo) {
    const pose = new Map();
    modelo.traverse((obj) => {
        if (!obj.isBone) return;
        pose.set(obj.name, { q: obj.quaternion.clone(), p: obj.position.clone() });
    });
    return pose;
}

function restaurar(modelo, pose) {
    modelo.traverse((obj) => {
        if (!obj.isBone) return;
        const guarda = pose.get(obj.name);
        if (!guarda) return;
        obj.quaternion.copy(guarda.q);
        obj.position.copy(guarda.p);
    });
    modelo.updateMatrixWorld(true);
}

function buscarHueso(modelo, nombre) {
    let hallado = null;
    modelo.traverse((obj) => {
        if (obj.isBone && obj.name === nombre) hallado = obj;
    });
    return hallado;
}
