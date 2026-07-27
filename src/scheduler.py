"""Calendarizacion de los workouts en Lunes / Miercoles / Viernes."""

from datetime import date, timedelta
from typing import Any

from config.workouts import Workout


def next_monday(today: date | None = None) -> date:
    """Proximo lunes. Si hoy es lunes, devuelve hoy."""
    today = today or date.today()
    return today + timedelta(days=(0 - today.weekday()) % 7)


def session_dates(workouts: list[Workout], start: date, weeks: int) -> list[tuple[date, Workout]]:
    """Genera (fecha, workout) para cada sesion, ordenado cronologicamente.

    ``start`` se normaliza al lunes de su semana, asi el offset por weekday
    cae siempre en el dia correcto aunque se pase una fecha a mitad de semana.
    """
    monday = start - timedelta(days=start.weekday())
    sessions = [
        (monday + timedelta(weeks=week, days=w.weekday), w)
        for week in range(weeks)
        for w in workouts
    ]
    return sorted(sessions, key=lambda s: s[0])


def _scheduled_index(client: Any, sessions: list[tuple[date, Workout]]) -> set[tuple[str, int]]:
    """Set de (fecha_iso, workoutId) ya presentes en el calendario de Garmin.

    Solo consulta los meses que tocan las sesiones a calendarizar.
    """
    months = {(d.year, d.month) for d, _ in sessions}
    index: set[tuple[str, int]] = set()

    for year, month in sorted(months):
        try:
            payload = client.get_scheduled_workouts(year, month)
        except Exception as exc:  # noqa: BLE001 - sin indice solo perdemos idempotencia
            print(f"  Aviso: no se pudo leer el calendario {year}-{month:02d}: {exc}")
            continue

        for item in payload.get("calendarItems") or []:
            workout_id = item.get("workoutId")
            item_date = item.get("date")
            if workout_id and item_date:
                index.add((item_date, workout_id))

    return index


def schedule_all(
    client: Any,
    workouts: list[Workout],
    workout_ids: dict[str, int],
    start: date,
    weeks: int,
) -> int:
    """Calendariza cada workout N semanas. Devuelve cuantas sesiones creo.

    Idempotente: salta las fechas donde ese workout ya esta agendado.
    """
    sessions = session_dates(workouts, start, weeks)
    already = _scheduled_index(client, sessions)
    created = 0

    for day, workout in sessions:
        workout_id = workout_ids.get(workout.name)
        if workout_id is None:
            print(f"  ! {day} {workout.name}: sin workoutId, se salta")
            continue

        day_str = day.isoformat()
        if (day_str, workout_id) in already:
            print(f"  = {day_str} {workout.name} ya agendado")
            continue

        client.schedule_workout(workout_id, day_str)
        print(f"  + {day_str} {workout.name}")
        created += 1

    return created
