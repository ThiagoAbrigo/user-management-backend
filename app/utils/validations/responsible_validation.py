import re
from app.utils.constants.message import (
    REQUIRED_FIELD,
    DNI_ONLY_NUMBERS,
    DNI_LENGTH,
    DNI_ZEROS,
    DNI_SEQUENTIAL,
    PHONE_NUMBERS,
    PHONE_LENGTH,
    PHONE_ZEROS,
    PHONE_START,
    PHONE_SEQUENTIAL,
    NAME_MIN,
    NAME_MAX,
    NAME_FORMAT,
)

NAME_PATTERN = r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ ]+$"


def validate_responsible(responsible, participant_dni, is_sequential):
    errors = {}

    # ========= CAMPOS REQUERIDOS =========
    required_fields = ["name", "dni", "phone"]
    for field in required_fields:
        if not responsible.get(field):
            errors[f"responsible{field.capitalize()}"] = REQUIRED_FIELD

    # ========= NOMBRE =========
    name = responsible.get("name")
    if name:
        name = name.strip()
        if len(name) < 2:
            errors["responsibleName"] = NAME_MIN
        elif len(name) > 50:
            errors["responsibleName"] = NAME_MAX
        elif not re.match(NAME_PATTERN, name):
            errors["responsibleName"] = NAME_FORMAT

    # ========= DNI =========
    dni = responsible.get("dni")
    if dni:
        dni_str = str(dni).strip()

        if not dni_str.isdigit():
            errors["responsibleDni"] = DNI_ONLY_NUMBERS
        elif len(dni_str) != 10:
            errors["responsibleDni"] = DNI_LENGTH
        elif dni_str == "0000000000":
            errors["responsibleDni"] = DNI_ZEROS
        elif is_sequential(dni_str):
            errors["responsibleDni"] = DNI_SEQUENTIAL
        elif participant_dni and dni_str == str(participant_dni).strip():
            errors["responsibleDni"] = (
                "El DNI del responsable no puede ser igual al del participante"
            )

    # ========= TELÉFONO =========
    phone = responsible.get("phone")
    if phone:
        phone_str = str(phone).strip()

        if not phone_str.isdigit():
            errors["responsiblePhone"] = PHONE_NUMBERS
        elif len(phone_str) != 10:
            errors["responsiblePhone"] = PHONE_LENGTH
        elif phone_str == "0000000000":
            errors["responsiblePhone"] = PHONE_ZEROS
        elif phone_str[0] != "0":
            errors["responsiblePhone"] = PHONE_START
        elif is_sequential(phone_str):
            errors["responsiblePhone"] = PHONE_SEQUENTIAL

    return errors
