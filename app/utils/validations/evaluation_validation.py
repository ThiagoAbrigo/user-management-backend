from app.models import Test
from app import db
from app.utils.constants.message import (
    DATE_FORMAT,
    ERROR_DATE_FORMAT,
    ERROR_INVALID_DATA,
    ERROR_SELECT_PARTICIPANT,
    ERROR_SELECT_TEST,
    INVALID_DATA,
    REQUIRED_FIELD,
)
from datetime import datetime


def validate_register_input(data):
    if not isinstance(data, dict):
        return {"_error": INVALID_DATA}
    return {}


def validate_test_fields(name, frequency):
    friendly_names = {
        "name": "Nombre",
        "frequency_months": "Frecuencia",
    }
    errors = {}

    if not name:
        errors["name"] = f"{friendly_names['name']} requerido"
    elif Test.query.filter(db.func.lower(Test.name) == name.lower()).first():
        errors["name"] = "La Evaluación ya existe"

    if frequency is None:
        errors["frequency_months"] = f"{friendly_names['frequency_months']} requerido"
    elif not isinstance(frequency, int):
        errors["frequency_months"] = "La frecuencia debe ser un número entero"
    elif frequency < 1 or frequency > 12:
        errors["frequency_months"] = "La frecuencia debe estar entre 1 y 12 meses"

    return errors


def validate_exercises(exercises):
    errors = {}

    if not exercises:
        errors["exercises"] = "Se requiere al menos un ejercicio"
        return errors

    for i, ex in enumerate(exercises):
        name = ex.get("name", "").strip() if ex.get("name") else ""
        unit = ex.get("unit", "").strip() if ex.get("unit") else ""

        if not name:
            errors[f"exercises[{i}].name"] = REQUIRED_FIELD
        if not unit:
            errors[f"exercises[{i}].unit"] = REQUIRED_FIELD

    return errors


def validate_update_input(data, test):
    errors = {}

    name = data.get("name", "").strip() if data.get("name") else ""
    frequency = data.get("frequency_months")
    exercises = data.get("exercises", [])

    if not name:
        errors["name"] = REQUIRED_FIELD
    else:
        existing_test = Test.query.filter(
            db.func.lower(Test.name) == name.lower(),
            Test.id != test.id,
        ).first()
        if existing_test:
            errors["name"] = "El test con ese nombre ya existe"

    if frequency is None:
        errors["frequency_months"] = REQUIRED_FIELD
    elif not isinstance(frequency, int):
        errors["frequency_months"] = "Debe ser un número entero"
    elif frequency < 1 or frequency > 12:
        errors["frequency_months"] = "Debe estar entre 1 y 12 meses"

    errors.update(validate_exercises(exercises))

    return errors


def validate_apply_test_input(data):
    if not isinstance(data, dict):
        return ERROR_INVALID_DATA

    if "participant_external_id" not in data:
        return ERROR_SELECT_PARTICIPANT

    if "test_external_id" not in data:
        return ERROR_SELECT_TEST

    return None


def parse_evaluation_date(date_str):
    if not date_str:
        return None, None

    try:
        return datetime.strptime(date_str, DATE_FORMAT).date(), None
    except ValueError:
        return None, ERROR_DATE_FORMAT
