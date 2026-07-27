# Garmin GYM Sync — Contexto del proyecto

## ¿Qué hace este proyecto?

Script en Python que crea y calendariza automáticamente una rutina de gym de fuerza
(Push / Pull / Legs) en Garmin Connect para 4 semanas, usando la librería
`python-garminconnect` (reverse-engineering de los endpoints internos de Garmin).

Una vez ejecutado, los 3 workouts aparecen en el calendario del reloj Garmin
sincronizados para cada Lunes (Push), Miércoles (Pull) y Viernes (Legs).

---

## Contexto del usuario

- **Dispositivo:** Garmin Forerunner 970
- **Objetivo fitness:** Bajar de peso + ganar fuerza, complementando un plan de
  running con Garmin Coach (Martes / Jueves / fin de semana)
- **Nivel en gym:** Principiante
- **Días de gym:** Lunes / Miércoles / Viernes (tarde-noche)
- **Duración por sesión:** 60 minutos
- **Equipo disponible:** Máquinas guiadas, mancuernas/barras libres, cables/poleas
- **Lesiones:** Ninguna
- **Semanas a calendarizar:** 4

---

## Arquitectura del proyecto

```
.
├── CLAUDE.md               ← Este archivo
├── README.md
├── requirements.txt
├── .env                    ← Credenciales de Garmin (NO commitear)
├── .env.example
├── .gitignore
├── main.py                 ← Entry point: python main.py
├── config/
│   └── workouts.py         ← Definición de los 3 workouts (Push/Pull/Legs)
└── src/
    ├── auth.py             ← Login a Garmin Connect (+ cache de tokens OAuth)
    ├── uploader.py         ← Construye y sube los workouts a Garmin
    └── scheduler.py        ← Calendariza Lun/Mié/Vie por N semanas
```

---

## Rutina completa — Push / Pull / Legs

### LUNES — Push (Empuje)

Músculos: Pecho, hombros, tríceps

| Ejercicio                         | Series | Reps | Descanso |
| --------------------------------- | ------ | ---- | -------- |
| Press de pecho en máquina         | 3      | 12   | 90 seg   |
| Press de hombro con mancuernas    | 3      | 12   | 90 seg   |
| Aperturas en cable cruzado        | 3      | 15   | 60 seg   |
| Elevaciones laterales mancuernas  | 3      | 15   | 60 seg   |
| Extensiones de tríceps polea alta | 3      | 12   | 60 seg   |

### MIÉRCOLES — Pull (Jalón)

Músculos: Espalda, bíceps, hombro posterior

| Ejercicio                     | Series | Reps      | Descanso |
| ----------------------------- | ------ | --------- | -------- |
| Jalón al pecho en polea alta  | 3      | 12        | 90 seg   |
| Remo sentado en cable         | 3      | 12        | 90 seg   |
| Remo con mancuerna un brazo   | 3      | 10 c/lado | 60 seg   |
| Face pull en cable            | 3      | 15        | 60 seg   |
| Curl de bíceps con mancuernas | 3      | 12        | 60 seg   |

### VIERNES — Legs (Piernas)

Músculos: Cuádriceps, isquiotibiales, glúteos, gemelos

| Ejercicio                       | Series | Reps | Descanso |
| ------------------------------- | ------ | ---- | -------- |
| Prensa de piernas en máquina    | 4      | 12   | 90 seg   |
| Sentadilla goblet con mancuerna | 3      | 12   | 90 seg   |
| Extensión de pierna en máquina  | 3      | 15   | 60 seg   |
| Curl femoral tumbado en máquina | 3      | 12   | 60 seg   |
| Elevaciones de talón de pie     | 4      | 20   | 45 seg   |

---

## Dependencias clave

```
garminconnect>=0.3.7   ← API wrapper (no oficial, reverse-engineering)
pydantic>=2.0          ← Modelos tipados de workout que usa garminconnect
python-dotenv>=1.0     ← Para leer .env con credenciales
```

Instalar con:

```bash
pip install -r requirements.txt
```

> La API tipada (`garminconnect.workout.StrengthWorkout`, `create_strength_set`)
> y el catálogo `garminconnect.exercises` existen a partir de 0.3.7. Con
> versiones anteriores el import falla.

---

## Variables de entorno (.env)

```env
GARMIN_EMAIL=tu@email.com
GARMIN_PASSWORD=tu_password
WEEKS=4
START_DATE=YYYY-MM-DD          # Próximo lunes como punto de partida
GARMINTOKENS=~/.garminconnect  # Cache de tokens OAuth (evita repetir MFA)
```

Ver `.env.example`. Los flags de CLI (`--weeks`, `--start`) tienen prioridad
sobre las variables de entorno.

---

## Lógica de calendarización

- Iterar `WEEKS` semanas a partir de `START_DATE`
- `START_DATE` se normaliza al lunes de su semana, así el offset por `weekday`
  cae en el día correcto aunque se pase una fecha a mitad de semana
- Cada semana: calendarizar Push el lunes, Pull el miércoles, Legs el viernes
- Subir con `client.upload_strength_workout(workout)`
- Calendarizar con `client.schedule_workout(workout_id, date_str)`

### Idempotencia (dos niveles)

1. **Subida:** `find_existing()` busca por `workoutName` en
   `client.get_workouts()`; si ya existe, reusa ese `workoutId` en vez de crear
   un duplicado.
2. **Calendario:** `_scheduled_index()` lee `client.get_scheduled_workouts(year,
   month)` solo de los meses afectados y arma un set de `(fecha_iso, workoutId)`
   ya agendados; esas fechas se saltan.

---

## Mapeo de ejercicios a enums de Garmin

Cada ejercicio necesita un par **category / exercise** que exista en el catálogo
real de Garmin (1527 ejercicios / 47 categorías). Un enum inventado hace que el
reloj muestre el ejercicio sin nombre.

```python
from garminconnect import exercises
exercises.find("cable row")            # búsqueda por substring
exercises.resolve("Seated Cable Row")
# → {'name': 'Seated Cable Row', 'category': 'ROW', 'exercise': 'SEATED_CABLE_ROW'}
```

> El catálogo vive en `exercises.EXERCISES` / `exercises.CATEGORIES`
> (no hay `list_all()`).

Mapeo ya verificado y en uso (`config/workouts.py`):

| Ejercicio                         | category           | exercise                 |
| --------------------------------- | ------------------ | ------------------------ |
| Press de pecho en máquina         | `BENCH_PRESS`      | `BENCH_PRESS`            |
| Press de hombro con mancuernas    | `SHOULDER_PRESS`   | `DUMBBELL_SHOULDER_PRESS`|
| Aperturas en cable cruzado        | `FLYE`             | `CABLE_CROSSOVER`        |
| Elevaciones laterales mancuernas  | `LATERAL_RAISE`    | `DUMBBELL_LATERAL_RAISE` |
| Extensiones de tríceps polea alta | `TRICEPS_EXTENSION`| `TRICEPS_PRESSDOWN`      |
| Jalón al pecho en polea alta      | `PULL_UP`          | `LAT_PULLDOWN`           |
| Remo sentado en cable             | `ROW`              | `SEATED_CABLE_ROW`       |
| Remo con mancuerna un brazo       | `ROW`              | `ONE_ARM_BENT_OVER_ROW`  |
| Face pull en cable                | `ROW`              | `FACE_PULL`              |
| Curl de bíceps con mancuernas     | `CURL`             | `DUMBBELL_BICEPS_CURL`   |
| Prensa de piernas en máquina      | `SQUAT`            | `LEG_PRESS`              |
| Sentadilla goblet con mancuerna   | `SQUAT`            | `GOBLET_SQUAT`           |
| Extensión de pierna en máquina    | `BANDED_EXERCISES` | `LEG_EXTENSION`          |
| Curl femoral tumbado en máquina   | `LEG_CURL`         | `LEG_CURL`               |
| Elevaciones de talón de pie       | `CALF_RAISE`       | `STANDING_CALF_RAISE`    |

Dos compromisos que el catálogo obligó (no "arreglarlos" sin verificar antes):

- **Press de pecho en máquina:** no existe un "chest press machine" en el
  catálogo; `BENCH_PRESS/BENCH_PRESS` es el press genérico y es lo más cercano.
- **Extensión de pierna:** las únicas opciones son
  `BANDED_EXERCISES/LEG_EXTENSION` (mismo movimiento con banda) y
  `CRUNCH/LEG_EXTENSIONS` (que es un abdominal, músculo equivocado). Se usa la
  banded: en el reloj se lee "Banded Leg Extension", pero series, reps y
  descanso son idénticos.

---

## Notas importantes

- Garmin no tiene API pública oficial para uso personal. Esta librería hace
  reverse-engineering de los endpoints internos de Garmin Connect. Funciona en
  la práctica pero puede romperse si Garmin cambia sus endpoints.
- El Garmin Coach de running ya ocupa Martes/Jueves/fin de semana — NO
  calendarizar nada en esos días para evitar conflictos.
- El script es idempotente: correrlo dos veces no duplica workouts ni sesiones
  del calendario (ver "Idempotencia" arriba).
- Autenticación: Garmin usa MFA en algunas cuentas. El MFA se pide por stdin
  solo la primera vez; después se reusan los tokens OAuth cacheados en
  `GARMINTOKENS`. Si el cache está vencido, se hace login limpio y se reescribe.
- La duración que muestra Garmin es una estimación:
  `sets * (reps * 3s + descanso)` (ver `SECONDS_PER_REP` en `src/uploader.py`).
- `create_strength_set()` consume 3 slots de `step_order` por ejercicio
  (bloque + ejercicio + descanso); por eso el contador avanza de 3 en 3.

---

## Comandos de referencia

```bash
# Correr el script completo
python main.py

# Validar los workouts y el calendario sin conectarse a Garmin
python main.py --dry-run

# Igual que arriba, pero imprime el JSON crudo que se enviaría
python main.py --dry-run --dump-json

# Solo subir workouts sin calendarizar (útil para debug)
python main.py --no-schedule

# Calendarizar semanas específicas
python main.py --weeks 4 --start 2026-07-27
```
