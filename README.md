# Garmin GYM Sync

Crea y calendariza automáticamente una rutina de fuerza Push / Pull / Legs en
Garmin Connect, para que aparezca en el calendario del reloj cada Lunes (Push),
Miércoles (Pull) y Viernes (Legs).

## Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # y llena tus credenciales
```

## Uso

```bash
# Validar sin conectarse a Garmin (no toca la cuenta)
python main.py --dry-run

# Ver además el JSON crudo que se enviaría
python main.py --dry-run --dump-json

# Subir los workouts pero NO tocar el calendario
python main.py --no-schedule

# Todo: subir + calendarizar
python main.py

# Semanas / fecha de arranque explícitas
python main.py --weeks 4 --start 2026-07-27
```

`--dry-run` es 100% offline y no necesita credenciales. `--no-schedule` **sí**
se conecta y sube los workouts a tu cuenta, solo omite el calendarizado.

## Idempotencia

El script se puede correr varias veces sin duplicar nada:

- **Workouts**: antes de subir, busca por nombre en `get_workouts()` y reusa el
  `workoutId` existente.
- **Calendario**: consulta `get_scheduled_workouts()` de los meses afectados y
  salta las fechas donde ese workout ya está agendado.

## La rutina

| Día | Sesión | Bloques | Duración estimada |
| --- | ------ | ------- | ----------------- |
| Lunes | Push — pecho, hombro, tríceps | 5 | ~28 min |
| Miércoles | Pull — espalda, bíceps | 5 | ~27 min |
| Viernes | Legs — piernas | 5 | ~32 min |

La estimación cuenta trabajo + descansos a 3 s por repetición; el resto de los
60 min se va en calentamiento, transiciones y series de aproximación.

Martes / Jueves / fin de semana quedan libres a propósito para el plan de
running de Garmin Coach.

## Ejercicios y enums de Garmin

Los pares `category` / `exercise` en [config/workouts.py](config/workouts.py)
están verificados contra el catálogo real de la librería (1527 ejercicios en 47
categorías):

| Ejercicio | category / exercise |
| --- | --- |
| Press de pecho en máquina | `BENCH_PRESS` / `BENCH_PRESS` |
| Press de hombro con mancuernas | `SHOULDER_PRESS` / `DUMBBELL_SHOULDER_PRESS` |
| Aperturas en cable cruzado | `FLYE` / `CABLE_CROSSOVER` |
| Elevaciones laterales | `LATERAL_RAISE` / `DUMBBELL_LATERAL_RAISE` |
| Extensiones de tríceps en polea | `TRICEPS_EXTENSION` / `TRICEPS_PRESSDOWN` |
| Jalón al pecho | `PULL_UP` / `LAT_PULLDOWN` |
| Remo sentado en cable | `ROW` / `SEATED_CABLE_ROW` |
| Remo con mancuerna un brazo | `ROW` / `ONE_ARM_BENT_OVER_ROW` |
| Face pull | `ROW` / `FACE_PULL` |
| Curl de bíceps con mancuernas | `CURL` / `DUMBBELL_BICEPS_CURL` |
| Prensa de piernas | `SQUAT` / `LEG_PRESS` |
| Sentadilla goblet | `SQUAT` / `GOBLET_SQUAT` |
| Extensión de pierna | `BANDED_EXERCISES` / `LEG_EXTENSION` ⚠️ |
| Curl femoral | `LEG_CURL` / `LEG_CURL` |
| Elevaciones de talón | `CALF_RAISE` / `STANDING_CALF_RAISE` |

⚠️ **Extensión de pierna**: el catálogo de Garmin no tiene la extensión de
cuádriceps en máquina. Las únicas opciones eran `BANDED_EXERCISES/LEG_EXTENSION`
(mismo movimiento, banda en vez de máquina) y `CRUNCH/LEG_EXTENSIONS` (que es un
abdominal, músculo equivocado). Se usa la primera: en el reloj se lee "Banded Leg
Extension", pero series, reps y descansos son idénticos — hacés la máquina igual.

Para buscar otros ejercicios:

```python
from garminconnect import exercises
exercises.find("cable row")          # búsqueda por substring
exercises.resolve("Seated Cable Row")
```

> La API real del módulo es `find()` / `resolve()` / `EXERCISES` / `CATEGORIES` /
> `BY_NAME`. No existe `list_all()`.

## Autenticación

Los tokens OAuth se cachean en la ruta de `GARMINTOKENS` (por defecto
`~/.garminconnect`), así el MFA se pide solo la primera vez. Si el cache vence,
el script vuelve a loguearse solo.

## Notas

- Garmin no tiene API pública oficial. `garminconnect` hace reverse-engineering
  de los endpoints internos de Garmin Connect: funciona, pero puede romperse si
  Garmin los cambia.
- Los workouts tipados requieren `pydantic`; sin él la librería cae a un stub y
  `upload_strength_workout` falla. Ya está en `requirements.txt`.
