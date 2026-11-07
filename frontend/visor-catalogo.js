// Catálogo del visor. Hoy hay un solo personaje y una sola animación.
// Más adelante cada ejercicio puede traer varios clips, un personaje
// femenino o masculino, y zonas para las partículas turquesa.
// La ficha del HUD y la base SQLite no se leen desde aquí.

export const catalogoVisor = {
  personajes: [
    {
      id: "mpfb-mujer",
      etiqueta: "Mujer",
      sexo: "mujer",
      modelo: "/modelos/mujer/squat_bodyweight_colores.glb?v=zapatos",
    },
    {
      id: "mpfb-hombre",
      etiqueta: "Hombre",
      sexo: "hombre",
      modelo: "/modelos/hombre/squat_bodyweight.glb",
    },
  ],
  ejercicios: [
    {
      id: "squat_bodyweight",
      nombre: "Sentadilla con peso corporal",
      personaje: "mpfb-mujer",
      clips: [
        {
          id: "squat_bodyweight",
          nombre: "Sentadilla",
          pista: "squat_bodyweight",
        },
      ],
      zonas: [],
    },
  ],
};
