"""Entry point: crea y calendariza la rutina Push/Pull/Legs en Garmin Connect."""

import argparse
import json
import os
import sys
from datetime import date, datetime

from dotenv import load_dotenv

from config.workouts import WORKOUTS
from src.scheduler import next_monday, schedule_all, session_dates
from src.uploader import build_workout, estimate_duration, upload_all


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--weeks", type=int, help="Semanas a calendarizar (default: WEEKS o 4)"
    )
    parser.add_argument(
        "--start", help="Lunes de arranque YYYY-MM-DD (default: START_DATE o proximo lunes)"
    )
    parser.add_argument(
        "--no-schedule",
        action="store_true",
        help="Sube los workouts pero no toca el calendario",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="No se conecta a Garmin: construye los workouts y los imprime",
    )
    parser.add_argument(
        "--dump-json", action="store_true", help="Con --dry-run, imprime el JSON crudo"
    )
    return parser.parse_args()


def resolve_start(arg: str | None) -> date:
    raw = arg or os.getenv("START_DATE")
    if not raw:
        return next_monday()
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        raise SystemExit(f"START_DATE invalida: {raw!r} (formato esperado YYYY-MM-DD)")


def resolve_weeks(arg: int | None) -> int:
    weeks = arg if arg is not None else int(os.getenv("WEEKS") or 4)
    if weeks < 1:
        raise SystemExit(f"weeks debe ser >= 1, recibido {weeks}")
    return weeks


def dry_run(start: date, weeks: int, dump_json: bool) -> None:
    """Valida la construccion de los workouts sin tocar la red."""
    print("=== DRY RUN (sin conexion a Garmin) ===\n")

    for workout in WORKOUTS:
        built = build_workout(workout)
        mins = estimate_duration(workout) / 60
        total_steps = len(built.workoutSegments[0].workoutSteps)
        print(f"{workout.name}  (~{mins:.0f} min, {total_steps} bloques)")
        for exercise in workout.exercises:
            print(
                f"   {exercise.sets}x{exercise.reps:<3} "
                f"desc {exercise.rest_seconds:>3}s  "
                f"{exercise.label:38} {exercise.category}/{exercise.exercise}"
            )
        if dump_json:
            print(json.dumps(built.to_dict(), indent=2, ensure_ascii=False))
        print()

    print(f"=== Calendario que se crearia ({weeks} semanas desde {start}) ===")
    for day, workout in session_dates(WORKOUTS, start, weeks):
        print(f"   {day} ({day.strftime('%a')})  {workout.name}")


def main() -> int:
    load_dotenv()
    args = parse_args()
    start = resolve_start(args.start)
    weeks = resolve_weeks(args.weeks)

    if args.dry_run:
        dry_run(start, weeks, args.dump_json)
        return 0

    from src.auth import login

    client = login()

    print("\nSubiendo workouts...")
    workout_ids = upload_all(client, WORKOUTS)

    if args.no_schedule:
        print("\n--no-schedule: calendario intacto.")
        return 0

    print(f"\nCalendarizando {weeks} semanas desde {start}...")
    created = schedule_all(client, WORKOUTS, workout_ids, start, weeks)
    print(f"\nListo: {created} sesiones nuevas agendadas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
