import re
from app.models.participant import Participant
from app.models.responsible import Responsible
from app.utils.constants.message import (
    REQUIRED_FIELD,
    DNI_ONLY_NUMBERS,
    DNI_LENGTH,
    DNI_ZEROS,
    DNI_SEQUENTIAL,
    DNI_EXISTS,
    EMAIL_INVALID,
    EMAIL_LENGTH,
    EMAIL_EXISTS,
    NAME_MIN,
    NAME_MAX,
    NAME_FORMAT,
    PHONE_NUMBERS,
    PHONE_LENGTH,
    PHONE_ZEROS,
    PHONE_START,
    PHONE_SEQUENTIAL,
)

EMAIL_PATTERN = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
NAME_PATTERN = r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ]+$"


def validate_required_fields(data, fields):
    errors = {}
    for field in fields:
        if field not in data or not str(data[field]).strip():
            errors[field] = REQUIRED_FIELD
    return errors


def validate_dni(dni, is_sequential):
    errors = {}
    dni = str(dni).strip()

    if not dni.isdigit():
        errors["dni"] = DNI_ONLY_NUMBERS
    elif len(dni) != 10:
        errors["dni"] = DNI_LENGTH
    elif dni == "0000000000":
        errors["dni"] = DNI_ZEROS
    elif is_sequential(dni):
        errors["dni"] = DNI_SEQUENTIAL
    elif Participant.query.filter_by(dni=dni).first():
        errors["dni"] = DNI_EXISTS

    return errors


def validate_email(email):
    errors = {}
    email = email.strip()

    if not re.match(EMAIL_PATTERN, email):
        errors["email"] = EMAIL_INVALID
    elif len(email) > 100:
        errors["email"] = EMAIL_LENGTH
    elif Participant.query.filter_by(email=email).first():
        errors["email"] = EMAIL_EXISTS

    return errors


def validate_name(field, value):
    errors = {}
    value = value.strip()

    if len(value) < 2:
        errors[field] = NAME_MIN
    elif len(value) > 50:
        errors[field] = NAME_MAX
    elif not re.match(NAME_PATTERN, value):
        errors[field] = NAME_FORMAT

    return errors


def validate_phone(phone, is_sequential):
    errors = {}
    phone = str(phone).strip()

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
