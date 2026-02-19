REQUIRED_FIELD_MSG = "Campo requerido"
from datetime import datetime, date as date_cls

def validate_required_fields(data):
    errors = {}

    if not data.get("participant_external_id"):
        errors["participant_external_id"] = "Selecciona un participante"

    for field in ["weight", "height", "date"]:
        if data.get(field) is None:
            errors[field] = REQUIRED_FIELD_MSG

    return errors


def validate_numeric_fields(fields):
    errors = {}

    for field, value in fields.items():
        if value is not None and not isinstance(value, (int, float)):
            errors[field] = "Debe ser numérico"

    return errors


def validate_ranges(weight, height, waist, arm, leg, calf):
    errors = {}

    if isinstance(weight, (int, float)) and not 0.5 <= weight <= 500:
        errors["weight"] = "El peso debe estar entre 0.5 y 500 kg"

    if isinstance(height, (int, float)) and not 0.3 <= height <= 2.5:
        errors["height"] = "La altura debe estar entre 0.3 y 2.5 metros"

    if waist is not None and not 0 <= waist <= 200:
        errors["waistPerimeter"] = "Debe estar entre 0 y 200 cm"

    if arm is not None and not 0 <= arm <= 80:
        errors["armPerimeter"] = "Debe estar entre 10 y 80 cm"

    if leg is not None and not 0 <= leg <= 120:
        errors["legPerimeter"] = "Debe estar entre 20 y 120 cm"

    if calf is not None and not 0 <= calf <= 70:
        errors["calfPerimeter"] = "Debe estar entre 15 y 70 cm"

    return errors
