import re
from app.models.participant import Participant
from app.models.responsible import Responsible
from app.models.user import User
from app.utils.constants.message import (
    DNI_EXISTS,
    DNI_LENGTH,
    DNI_ONLY_NUMBERS,
    DNI_SEQUENTIAL,
    DNI_ZEROS,
    EMAIL_EXISTS,
    EMAIL_INVALID,
    EMAIL_LENGTH,
    NAME_FORMAT,
    PASSWORD_MAX,
    PASSWORD_MIN,
    PHONE_LENGTH,
    PHONE_NUMBERS,
    PHONE_SEQUENTIAL,
    PHONE_START,
    PHONE_ZEROS,
    REQUIRED_FIELD,
)

EMAIL_PATTERN = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
NAME_PATTERN = r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ]+$"
ALLOWED_ROLES = ["DOCENTE", "PASANTE", "ADMINISTRADOR"]


def validate_required_fields(data, required_fields):
    field_names = {
        "firstName": "Nombre",
        "lastName": "Apellido",
        "dni": "DNI",
        "phone": "Teléfono",
        "email": "Correo electrónico",
        "password": "Contraseña",
        "role": "Rol",
        "address": "Dirección"
    }
    errors = {}
    for field in required_fields:
        value = data.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            friendly_name = field_names.get(field, field)
            errors[field] = f"{friendly_name} requerido"
    return errors


def validate_dni(dni, is_sequential, check_participant=True):
    """
    Valida formato y unicidad del DNI.
    - check_participant=True (default): DNI no debe existir en User, Participant ni Responsible.
    - check_participant=False: solo rechaza si existe en User o Responsible.
      Usado en create_user para permitir que un participante sea también docente/pasante (mismo DNI).
    """
    errors = {}
    if not dni.isdigit():
        errors["dni"] = DNI_ONLY_NUMBERS
    elif len(dni) != 10:
        errors["dni"] = DNI_LENGTH
    elif dni == "0000000000":
        errors["dni"] = DNI_ZEROS
    elif is_sequential(dni):
        errors["dni"] = DNI_SEQUENTIAL
    else:
        exists_user = User.query.filter_by(dni=dni).first()
        exists_responsible = Responsible.query.filter_by(dni=dni).first()
        exists_participant = Participant.query.filter_by(dni=dni).first() if check_participant else None
        if exists_user or exists_responsible or exists_participant:
            errors["dni"] = DNI_EXISTS
    return errors


def validate_email(email):
    errors = {}
    if not re.match(EMAIL_PATTERN, email):
        errors["email"] = EMAIL_INVALID
    elif len(email) > 100:
        errors["email"] = EMAIL_LENGTH
    elif User.query.filter_by(email=email).first():
        errors["email"] = EMAIL_EXISTS
    return errors


def validate_name(field, value, min_msg, max_msg):
    errors = {}
    if len(value) < 2:
        errors[field] = min_msg
    elif len(value) > 50:
        errors[field] = max_msg
    elif not re.match(NAME_PATTERN, value):
        errors[field] = NAME_FORMAT
    return errors


def validate_password(password):
    errors = {}
    if len(password) < 6:
        errors["password"] = PASSWORD_MIN
    elif len(password) > 50:
        errors["password"] = PASSWORD_MAX
    return errors


def validate_phone(phone, is_sequential):
    errors = {}
    if phone and phone != "NINGUNA":
        if not phone.isdigit():
            errors["phone"] = PHONE_NUMBERS
        elif len(phone) != 10:
            errors["phone"] = PHONE_LENGTH
        elif phone == "0000000000":
            errors["phone"] = PHONE_ZEROS
        elif phone[0] != "0":
            errors["phone"] = PHONE_START
        elif is_sequential(phone):
            errors["phone"] = PHONE_SEQUENTIAL
    return errors
