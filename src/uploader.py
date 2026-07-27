"""Construccion y subida de los workouts de fuerza a Garmin Connect."""

from typing import Any

from garminconnect.workout import (
    StrengthWorkout,
    WorkoutSegment,
    create_strength_set,
)

from config.workouts import Workout

# Segundos por repeticion, para estimar la duracion que muestra Garmin.
SECONDS_PER_REP = 3


def estimate_duration(workout: Workout) -> int:
    """Duracion estimada en segundos (trabajo + descansos)."""
    return sum(
        e.sets * (e.reps * SECONDS_PER_REP + e.rest_seconds) for e in workout.exercises
    )


def build_workout(workout: Workout) -> StrengthWorkout:
    """Traduce un Workout del config al modelo tipado de garminconnect."""
    steps = []
    step_order = 1
    for exercise in workout.exercises:
        steps.append(
            create_strength_set(
                exercise.category,
                step_order=step_order,
                sets=exercise.sets,
                reps=exercise.reps,
                rest_seconds=exercise.rest_seconds,
                exercise_name=exercise.exercise,
            )
        )
        # create_strength_set usa step_order, +1 (ejercicio) y +2 (descanso).
        step_order += 3

    return StrengthWorkout(
        workoutName=workout.name,
        description=workout.description,
        estimatedDurationInSecs=estimate_duration(workout),
        workoutSegments=[
            WorkoutSegment(
                segmentOrder=1,
                sportType={
                    "sportTypeId": 5,
                    "sportTypeKey": "strength_training",
                    "displayOrder": 5,
                },
                workoutSteps=steps,
            )
        ],
    )


def find_existing(client: Any, name: str) -> int | None:
    """Devuelve el workoutId de un workout ya subido con ese nombre, o None."""
    for existing in client.get_workouts(limit=100):
        if existing.get("workoutName") == name:
            return existing.get("workoutId")
    return None


def upload_all(client: Any, workouts: list[Workout]) -> dict[str, int]:
    """Sube los workouts que falten y devuelve {nombre: workoutId}.

    Idempotente: si ya existe uno con el mismo nombre, lo reusa en vez de
    crear un duplicado.
    """
    ids: dict[str, int] = {}

    for workout in workouts:
        existing_id = find_existing(client, workout.name)
        if existing_id is not None:
            print(f"  = {workout.name} ya existe (id {existing_id}), se reusa")
            ids[workout.name] = existing_id
            continue

        result = client.upload_strength_workout(build_workout(workout))
        workout_id = result.get("workoutId")
        print(f"  + {workout.name} subido (id {workout_id})")
        ids[workout.name] = workout_id

    return ids
