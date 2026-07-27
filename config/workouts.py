"""Definicion de la rutina Push / Pull / Legs.

Los pares ``category`` / ``exercise`` salen del catalogo real de Garmin
(``garminconnect.exercises``, 1527 ejercicios / 47 categorias) y estan
verificados con ``exercises.resolve()``. No inventar valores aca: un enum que
no existe en el catalogo hace que el reloj muestre el ejercicio sin nombre.

Para buscar un ejercicio nuevo:

    from garminconnect import exercises
    exercises.find("cable row")      # busqueda por substring
    exercises.resolve("Seated Cable Row")
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Exercise:
    """Un bloque de ejercicio: N series de M reps con descanso entre series."""

    label: str  # Nombre en espaniol, solo para los logs
    category: str  # Enum de categoria de Garmin
    exercise: str  # Enum de variante de Garmin ("" = solo muestra la categoria)
    sets: int
    reps: int
    rest_seconds: int


@dataclass(frozen=True)
class Workout:
    name: str
    weekday: int  # 0 = lunes ... 6 = domingo
    description: str
    exercises: list[Exercise]


# --- LUNES: Push (pecho, hombros, triceps) --------------------------------

PUSH = Workout(
    name="Gym Push (Pecho/Hombro/Triceps)",
    weekday=0,
    description="Empuje: pecho, hombros y triceps. 60 min.",
    exercises=[
        # El catalogo no tiene "chest press machine"; BENCH_PRESS/BENCH_PRESS
        # es el press de pecho generico y es lo que mas se le acerca.
        Exercise(
            "Press de pecho en maquina", 
            "BENCH_PRESS", 
            "BENCH_PRESS", 
            3, 
            12, 
            90
        ),
        Exercise(
            "Press de hombro con mancuernas",
            "SHOULDER_PRESS",
            "DUMBBELL_SHOULDER_PRESS",
            3,
            12,
            90,
        ),
        Exercise(
            "Aperturas en cable cruzado", 
            "FLYE", 
            "CABLE_CROSSOVER", 
            3, 
            15, 
            60
        ),
        Exercise(
            "Elevaciones laterales con mancuernas",
            "LATERAL_RAISE",
            "DUMBBELL_LATERAL_RAISE",
            3,
            15,
            60,
        ),
        Exercise(
            "Extensiones de triceps en polea alta",
            "TRICEPS_EXTENSION",
            "TRICEPS_PRESSDOWN",
            3,
            12,
            60,
        ),
    ],
)


# --- MIERCOLES: Pull (espalda, biceps, hombro posterior) ------------------

PULL = Workout(
    name="Gym Pull (Espalda/Biceps)",
    weekday=2,
    description="Jalon: espalda, biceps y hombro posterior. 60 min.",
    exercises=[
        Exercise("Jalon al pecho en polea alta", "PULL_UP", "LAT_PULLDOWN", 3, 12, 90),
        Exercise("Remo sentado en cable", "ROW", "SEATED_CABLE_ROW", 3, 12, 90),
        # 10 reps por lado: se registran los dos lados como una sola serie de 10.
        Exercise(
            "Remo con mancuerna a un brazo", "ROW", "ONE_ARM_BENT_OVER_ROW", 3, 10, 60
        ),
        Exercise("Face pull en cable", "ROW", "FACE_PULL", 3, 15, 60),
        Exercise(
            "Curl de biceps con mancuernas", "CURL", "DUMBBELL_BICEPS_CURL", 3, 12, 60
        ),
    ],
)


# --- VIERNES: Legs (cuadriceps, isquios, gluteos, gemelos) ----------------

LEGS = Workout(
    name="Gym Legs (Piernas)",
    weekday=4,
    description="Piernas: cuadriceps, isquios, gluteos y gemelos. 60 min.",
    exercises=[
        Exercise("Prensa de piernas en maquina", "SQUAT", "LEG_PRESS", 4, 12, 90),
        Exercise("Sentadilla goblet con mancuerna", "SQUAT", "GOBLET_SQUAT", 3, 12, 90),
        # OJO: Garmin no tiene extension de cuadriceps en maquina. Las unicas
        # opciones del catalogo son BANDED_EXERCISES/LEG_EXTENSION (mismo
        # movimiento, banda en vez de maquina) y CRUNCH/LEG_EXTENSIONS (que es
        # un abdominal, musculo equivocado). Usamos la banded: en el reloj se
        # lee "Banded Leg Extension" pero series/reps/descanso son identicos.
        Exercise(
            "Extension de pierna en maquina",
            "BANDED_EXERCISES",
            "LEG_EXTENSION",
            3,
            15,
            60,
        ),
        Exercise("Curl femoral tumbado en maquina", "LEG_CURL", "LEG_CURL", 3, 12, 60),
        Exercise(
            "Elevaciones de talon de pie", "CALF_RAISE", "STANDING_CALF_RAISE", 4, 20, 45
        ),
    ],
)


WORKOUTS = [PUSH, PULL, LEGS]
