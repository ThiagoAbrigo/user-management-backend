from app.models.participant import Participant
from app.models.responsible import Responsible
from app.models.user import User
from flask import request
from app import db
import uuid

from app.utils.validations.user_validation import (
    ALLOWED_ROLES,
    validate_dni,
    validate_email,
    validate_name,
    validate_password,
    validate_phone,
    validate_required_fields,
)


class UserController:
    def _is_sequential(self, number_str):
        """
        Verifica si un número es secuencial (ej: 1234567890, 0987654321).
        Retorna True si es secuencial, False si es válido.
        """
        # Patrones secuenciales comunes
        sequential_patterns = [
            "1234567890",
            "0987654321",
            "0123456789",
            "9876543210",
            "1111111111",
            "2222222222",
            "3333333333",
            "4444444444",
            "5555555555",
            "6666666666",
            "7777777777",
            "8888888888",
            "9999999999",
        ]

        if number_str in sequential_patterns:
            return True

        # Verificar si todos los dígitos son iguales
        if len(set(number_str)) == 1:
            return True

        # Verificar secuencia ascendente o descendente
        is_ascending = all(
            int(number_str[i]) == int(number_str[i - 1]) + 1
            for i in range(1, len(number_str))
        )
        is_descending = all(
            int(number_str[i]) == int(number_str[i - 1]) - 1
            for i in range(1, len(number_str))
        )

        return is_ascending or is_descending

    def get_users(self):
        try:
            participants = Participant.query.all()

            data = [
                {
                    "external_id": p.external_id,
                    "firstName": p.firstName,
                    "lastName": p.lastName,
                    "email": p.email,
                    "dni": p.dni,
                    "age": p.age,
                    "status": p.status,
                    "type": p.type,
                }
                for p in participants
            ]

            return success_response(msg="Usuarios listados correctamente", data=data)
        except Exception:
            return error_response("Error interno del servidor", code=500)

    def create_participant(self, data):
        """
        Crea un nuevo participante y opcionalmente su responsable si es menor de edad.
        Realiza validaciones, verifica duplicados en Java y asegura la consistencia de datos.
        """
        token = self._get_token()

        try:
            has_participant_key = (
                "participant" in data and data.get("participant") is not None
            )

            if has_participant_key:
                participant_data = data.get("participant")
                responsible_data = data.get("responsible")
                age = participant_data.get("age", 0) if participant_data else 0
            else:
                participant_data = data
                responsible_data = data.get("responsible")
                age = data.get("age", 0)

            is_minor = age < 18

            validation_result = self._validate_participant(
                participant_data, responsible_data, is_minor
            )
            if validation_result:
                return validation_result

            valid_programs = ["INICIACION", "FUNCIONAL"]
            program = participant_data.get("program")
            if program and program not in valid_programs:
                return error_response(
                    f"Programa inválido. Use: {valid_programs}", code=400
                )

            # self._check_java_duplicate(participant_data, token)

            # Si el DNI pertenece a un User (docente/pasante), vincular participante a ese usuario
            dni_str = str(participant_data.get("dni", "")).strip()
            existing_user = User.query.filter_by(dni=dni_str).first()
            user_id = existing_user.id if existing_user else None

            participant = self._build_participant(
                participant_data, is_minor, program, user_id=user_id
            )
            db.session.add(participant)
            db.session.commit()

            p_fresh = Participant.query.filter_by(
                external_id=participant.external_id
            ).first()

            try:
                # 5. Responsable (solo iniciación/menores)
                responsible = None
                if is_minor and p_fresh:
                    responsible = self._create_responsible(responsible_data, p_fresh.id)

                if responsible:
                    db.session.commit()

                # try:
                #     self._sync_with_java(participant, participant_data, token, is_minor)
                # except Exception as e:
                #     print(f"[Warning] Error sincronizando con Java: {e}")

                return success_response(
                    msg="Participante registrado correctamente",
                    data={
                        "participant_external_id": participant.external_id,
                        "responsible_external_id": (
                            responsible.external_id if responsible else None
                        ),
                    },
                )

            except Exception as e:
                db.session.delete(p_fresh)
                db.session.commit()
                return error_response(f"Error creando responsable: {str(e)}", 500)

        except Exception as e:
            db.session.rollback()
            return error_response("Error interno del servidor", code=500)

    def _validate_participant(self, participant, responsible, is_minor):
        """
        Valida los datos del participante y del responsable.
        Retorna un error_response si hay errores, o None si todo es válido.
        """
        import re

        errors = {}
        friendly_names = {
            "firstName": "Nombre",
            "lastName": "Apellido",
            "dni": "DNI",
            "age": "Edad",
            "phone": "Teléfono",
            "program": "Programa",
            "email": "Correo electrónico",
            "type": "Tipo",
            # Responsable
            "responsibleName": "Nombre del responsable",
            "responsibleDni": "DNI del responsable",
            "responsiblePhone": "Teléfono del responsable",
        }

        required_fields = [
            "firstName",
            "lastName",
            "dni",
            "age",
            "phone",
            "program",
            "email",
            "type",
        ]
        for field in required_fields:
            value = participant.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                errors[field] = f"{friendly_names.get(field, field)} requerido"
        
        # ========== VALIDACIÓN DE DNI ==========
        dni = participant.get("dni")
        if dni:
            dni_str = str(dni).strip()
            # Debe ser exactamente 10 dígitos numéricos
            if not dni_str.isdigit():
                errors["dni"] = "DNI debe contener solo números"
            elif len(dni_str) != 10:
                errors["dni"] = "DNI debe tener exactamente 10 dígitos"
            elif dni_str == "0000000000":
                errors["dni"] = "DNI no puede ser solo ceros"
            elif self._is_sequential(dni_str):
                errors["dni"] = "DNI no puede ser un número secuencial"
            else:
                # Permitir mismo DNI que un User (docente/pasante): esa persona puede ser también participante
                if (
                    Participant.query.filter_by(dni=dni_str).first()
                    or Responsible.query.filter_by(dni=dni_str).first()
                ):
                    errors["dni"] = "El DNI ya está registrado"
                # Si existe solo en User, no rechazar; en create_participant se vinculará con user_id

        # ========== VALIDACIÓN DE TELÉFONO ==========
        phone = participant.get("phone")
        if phone:
            phone_str = str(phone).strip()
            if not phone_str.isdigit():
                errors["phone"] = (
                    "Teléfono debe contener solo números (sin letras ni caracteres especiales)"
                )
            elif len(phone_str) != 10:
                errors["phone"] = "Teléfono debe tener exactamente 10 dígitos"
            elif phone_str == "0000000000":
                errors["phone"] = "Teléfono no puede ser solo ceros"
            elif phone_str[0] != "0":
                errors["phone"] = "Teléfono debe iniciar con 0"
            elif self._is_sequential(phone_str):
                errors["phone"] = "Teléfono no puede ser un número secuencial"

        # ========== VALIDACIÓN DE EMAIL ==========
        email = participant.get("email")
        if email:
            email_str = str(email).strip()
            email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
            if not re.match(email_pattern, email_str):
                errors["email"] = "Formato de correo electrónico inválido"
            elif len(email_str) > 100:
                errors["email"] = "Email no puede tener más de 100 caracteres"
            elif Participant.query.filter_by(email=email).first():
                errors["email"] = "El correo ya está registrado"

        # ========== VALIDACIÓN DE EDAD (1-80 años) ==========
        age = participant.get("age")
        if age is not None:
            try:
                age_int = int(age)
                if age_int < 5:
                    errors["age"] = "Edad mínima permitida es 5 años"
                elif age_int > 80:
                    errors["age"] = "Edad máxima permitida es 80 años"
            except (ValueError, TypeError):
                errors["age"] = "Edad debe ser un número válido"

        # ========== VALIDACIÓN DE PROGRAMA SEGÚN EDAD ==========
        # Reglas:
        # - Menores de 16 años: solo INICIACIÓN
        # - 16-17 años: puede FUNCIONAL o INICIACIÓN
        # - 18+ años: solo FUNCIONAL
        program = participant.get("program")
        if age is not None and program:
            try:
                age_int = int(age)
                if age_int < 16 and program == "FUNCIONAL":
                    errors["program"] = (
                        "Menores de 16 años solo pueden inscribirse a INICIACIÓN"
                    )
                elif age_int >= 18 and program == "INICIACION":
                    errors["program"] = (
                        "Mayores de 18 años solo pueden inscribirse a FUNCIONAL"
                    )
            except (ValueError, TypeError):
                pass  # Ya se validó arriba

        # ========== VALIDACIÓN DE NOMBRES (sin caracteres especiales ni espacios) ==========
        firstName = participant.get("firstName")
        if firstName:
            firstName_str = str(firstName).strip()
            # Solo letras y acentos permitidos (sin espacios)
            name_pattern = r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ]+$"
            if len(firstName_str) < 2:
                errors["firstName"] = "Nombre debe tener al menos 2 caracteres"
            elif len(firstName_str) > 50:
                errors["firstName"] = "Nombre no puede tener más de 50 caracteres"
            elif not re.match(name_pattern, firstName_str):
                errors["firstName"] = (
                    "Nombre solo puede contener letras (sin espacios) y no puede contener caracteres no permitidos"
                )

        lastName = participant.get("lastName")
        if lastName:
            lastName_str = str(lastName).strip()
            name_pattern = r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ]+$"
            if len(lastName_str) < 2:
                errors["lastName"] = "Apellido debe tener al menos 2 caracteres"
            elif len(lastName_str) > 50:
                errors["lastName"] = "Apellido no puede tener más de 50 caracteres"
            elif not re.match(name_pattern, lastName_str):
                errors["lastName"] = (
                    "Apellido solo puede contener letras (sin espacios) y no puede contener caracteres no permitidos"
                )

        # ========== VALIDACIÓN DE DIRECCIÓN ==========
        address = participant.get("address")
        if address:
            address_str = str(address).strip()
            if len(address_str) > 200:
                errors["address"] = "Dirección no puede tener más de 200 caracteres"
            # No caracteres peligrosos para SQL injection o XSS
            dangerous_pattern = r'[<>"\';{}]'
            if re.search(dangerous_pattern, address_str):
                errors["address"] = "Dirección contiene caracteres no permitidos"

        # ========== VALIDACIÓN DE TYPE ==========
        valid_types = ["ESTUDIANTE", "EXTERNO", "DOCENTE"]
        type_val = participant.get("type")
        if type_val and type_val not in valid_types:
            errors["type"] = f"Tipo inválido. Use: {valid_types}"

        # Validar que menores no sean DOCENTE
        if is_minor and type_val == "DOCENTE":
            errors["type"] = "Menores de edad no pueden ser DOCENTE"

        # ========== VALIDACIÓN DE PROGRAMA ==========
        valid_programs = ["INICIACION", "FUNCIONAL"]
        if program and program not in valid_programs:
            errors["program"] = f"Programa inválido. Use: {valid_programs}"

        # ========== VALIDACIÓN DE RESPONSABLE (MENORES de 18) ==========
        if is_minor:
            responsible_required = ["name", "dni", "phone"]
            if not responsible:
                for field in responsible_required:
                    key = "responsible" + field.capitalize()
                    errors[key] = f"{friendly_names.get(key, key)} requerido"
            else:
                for field in responsible_required:
                    key = "responsible" + field.capitalize()
                    value = responsible.get(field)
                    if value is None or (isinstance(value, str) and not value.strip()):
                        errors[key] = f"{friendly_names.get(key, key)} requerido"

                # Validar nombre del responsable
                resp_name = responsible.get("name")
                if resp_name:
                    name_pattern = r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ ]+$"
                    if len(resp_name.strip()) < 2:
                        errors["responsibleName"] = (
                            "Nombre debe tener al menos 2 caracteres"
                        )
                    elif not re.match(name_pattern, resp_name.strip()):
                        errors["responsibleName"] = "Nombre solo puede contener letras"

                # Validar DNI del responsable
                responsible_dni = responsible.get("dni")
                if responsible_dni:
                    dni_str = str(responsible_dni).strip()
                    if not dni_str.isdigit():
                        errors["responsibleDni"] = "DNI debe contener solo números"
                    elif len(dni_str) != 10:
                        errors["responsibleDni"] = (
                            "DNI debe tener exactamente 10 dígitos"
                        )
                    elif dni_str == "0000000000":
                        errors["responsibleDni"] = "DNI no puede ser solo ceros"
                    elif self._is_sequential(dni_str):
                        errors["responsibleDni"] = (
                            "DNI no puede ser un número secuencial"
                        )
                    else:
                        if Participant.query.filter_by(dni=dni_str).first():
                            errors["responsibleDni"] = "El DNI ya está registrado"

                # Validar teléfono del responsable
                responsible_phone = responsible.get("phone")
                if responsible_phone:
                    phone_str = str(responsible_phone).strip()
                    if not phone_str.isdigit():
                        errors["responsiblePhone"] = (
                            "Teléfono debe contener solo números"
                        )
                    elif len(phone_str) != 10:
                        errors["responsiblePhone"] = (
                            "Teléfono debe tener exactamente 10 dígitos"
                        )
                    elif phone_str == "0000000000":
                        errors["responsiblePhone"] = "Teléfono no puede ser solo ceros"
                    elif phone_str[0] != "0":
                        errors["responsiblePhone"] = "Teléfono debe iniciar con 0"
                    elif self._is_sequential(phone_str):
                        errors["responsiblePhone"] = (
                            "Teléfono no puede ser un número secuencial"
                        )

                # Validar que DNI del responsable sea diferente al del participante
                participant_dni = participant.get("dni")
                if responsible_dni and participant_dni:
                    if str(responsible_dni).strip() == str(participant_dni).strip():
                        errors["responsibleDni"] = (
                            "El DNI del responsable no puede ser igual al del participante"
                        )

        if errors:
            return error_response("Errores de validación", data=errors)

        return None

    def _build_participant(self, data, is_minor, program=None, user_id=None):
        """
        Construye una instancia de Participant con los datos validados.
        user_id: opcional; si la persona es también User (docente/pasante), se vincula aquí.
        """
        return Participant(
            firstName=data.get("firstName"),
            lastName=data.get("lastName"),
            age=data.get("age"),
            dni=data.get("dni"),
            phone=data.get("phone"),
            email=data.get("email") or None,
            address=data.get("address"),
            status="ACTIVO",
            type=data.get("type", "EXTERNO"),
            program=program,
            user_id=user_id,
        )

    def _create_responsible(self, data, participant_id):
        """
        Crea una instancia de Responsible vinculada al participante por su ID.
        """
        responsible = Responsible(
            name=data.get("name"),
            dni=data.get("dni"),
            phone=data.get("phone"),
            participant_id=participant_id,
        )
        db.session.add(responsible)
        return responsible

    def update_participant(self, external_id, data):
        """
        Actualiza los datos básicos de un participante.
        Campos editables del participante: firstName, lastName, phone, email, address, age, dni, type, program

        Si el participante tiene un responsable asociado (menores de edad), también se pueden
        editar sus datos enviando un objeto "responsible" con los campos: name, dni, phone
        """
        import re

        try:
            # Buscar participante
            participant = Participant.query.filter_by(external_id=external_id).first()
            if not participant:
                return error_response("Participante no encontrado", 404)

            errors = {}

            # ========== VALIDAR FIRSTNAME ==========
            if "firstName" in data:
                firstName = str(data["firstName"]).strip()
                name_pattern = r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ]+$"
                if len(firstName) < 2:
                    errors["firstName"] = "Nombre debe tener al menos 2 caracteres"
                elif len(firstName) > 50:
                    errors["firstName"] = "Nombre no puede tener más de 50 caracteres"
                elif not re.match(name_pattern, firstName):
                    errors["firstName"] = (
                        "Nombre solo puede contener letras (sin espacios)"
                    )

            # ========== VALIDAR LASTNAME ==========
            if "lastName" in data:
                lastName = str(data["lastName"]).strip()
                name_pattern = r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ]+$"
                if len(lastName) < 2:
                    errors["lastName"] = "Apellido debe tener al menos 2 caracteres"
                elif len(lastName) > 50:
                    errors["lastName"] = "Apellido no puede tener más de 50 caracteres"
                elif not re.match(name_pattern, lastName):
                    errors["lastName"] = (
                        "Apellido solo puede contener letras (sin espacios)"
                    )

            # ========== VALIDAR PHONE ==========
            if "phone" in data:
                phone_str = str(data["phone"]).strip()
                if phone_str:
                    if not phone_str.isdigit():
                        errors["phone"] = "Teléfono debe contener solo números"
                    elif len(phone_str) != 10:
                        errors["phone"] = "Teléfono debe tener exactamente 10 dígitos"
                    elif phone_str == "0000000000":
                        errors["phone"] = "Teléfono no puede ser solo ceros"
                    elif phone_str[0] != "0":
                        errors["phone"] = "Teléfono debe iniciar con 0"
                    elif self._is_sequential(phone_str):
                        errors["phone"] = "Teléfono no puede ser un número secuencial"

            # ========== VALIDAR EMAIL ==========
            if "email" in data:
                email_str = str(data["email"]).strip()
                email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
                if not re.match(email_pattern, email_str):
                    errors["email"] = "Formato de correo electrónico inválido"
                elif len(email_str) > 100:
                    errors["email"] = "Email no puede tener más de 100 caracteres"
                else:
                    # Verificar unicidad (excluyendo el participante actual)
                    existing = Participant.query.filter(
                        Participant.email == email_str, Participant.id != participant.id
                    ).first()
                    if existing:
                        errors["email"] = "El correo ya está registrado"

            # ========== VALIDAR ADDRESS ==========
            if "address" in data:
                address_str = str(data["address"]).strip()
                if len(address_str) > 200:
                    errors["address"] = "Dirección no puede tener más de 200 caracteres"
                dangerous_pattern = r'[<>"\';\{\}]'
                if re.search(dangerous_pattern, address_str):
                    errors["address"] = "Dirección contiene caracteres no permitidos"

            # ========== VALIDAR AGE ==========
            if "age" in data:
                try:
                    age_int = int(data["age"])
                    if age_int < 1:
                        errors["age"] = "Edad debe ser mayor a 0"
                    elif age_int > 80:
                        errors["age"] = "Edad máxima permitida es 80 años"
                except (ValueError, TypeError):
                    errors["age"] = "Edad debe ser un número válido"

            # ========== VALIDAR DNI ==========
            if "dni" in data:
                dni_str = str(data["dni"]).strip()
                if not dni_str.isdigit():
                    errors["dni"] = "DNI debe contener solo números"
                elif len(dni_str) != 10:
                    errors["dni"] = "DNI debe tener exactamente 10 dígitos"
                elif dni_str == "0000000000":
                    errors["dni"] = "DNI no puede ser solo ceros"
                elif self._is_sequential(dni_str):
                    errors["dni"] = "DNI no puede ser un número secuencial"
                else:
                    # Verificar unicidad (excluyendo el participante actual)
                    existing = Participant.query.filter(
                        Participant.dni == dni_str, Participant.id != participant.id
                    ).first()
                    if existing:
                        errors["dni"] = "El DNI ya está registrado"

            # ========== VALIDAR TYPE ==========
            if "type" in data:
                valid_types = ["ESTUDIANTE", "EXTERNO", "DOCENTE"]
                type_val = str(data["type"]).strip().upper()
                if type_val not in valid_types:
                    errors["type"] = f"Tipo inválido. Use: {valid_types}"

            # ========== VALIDAR PROGRAM ==========
            if "program" in data:
                valid_programs = ["INICIACION", "FUNCIONAL"]
                program_val = str(data["program"]).strip().upper()
                if program_val not in valid_programs:
                    errors["program"] = f"Programa inválido. Use: {valid_programs}"
                else:
                    # Validar restricciones por edad
                    # Usar la edad del data si viene, sino la del participante actual
                    check_age = int(data["age"]) if "age" in data else participant.age
                    if check_age < 16 and program_val == "FUNCIONAL":
                        errors["program"] = (
                            "Menores de 16 años solo pueden inscribirse a INICIACION"
                        )
                    elif check_age >= 18 and program_val == "INICIACION":
                        errors["program"] = (
                            "Mayores de 18 años solo pueden inscribirse a FUNCIONAL"
                        )

            # ========== VALIDAR RESPONSABLE (si viene en data) ==========
            responsible_data = data.get("responsible")
            responsible = None

            # Obtener el responsable del participante (si existe)
            if participant.responsibles:
                responsible = participant.responsibles[0]  # El primero asociado

            if responsible_data:
                if not responsible:
                    errors["responsible"] = (
                        "Este participante no tiene un responsable asociado"
                    )
                else:
                    # Validar nombre del responsable
                    if "name" in responsible_data:
                        resp_name = str(responsible_data["name"]).strip()
                        name_pattern = r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ ]+$"
                        if len(resp_name) < 2:
                            errors["responsibleName"] = (
                                "Nombre debe tener al menos 2 caracteres"
                            )
                        elif len(resp_name) > 100:
                            errors["responsibleName"] = (
                                "Nombre no puede tener más de 100 caracteres"
                            )
                        elif not re.match(name_pattern, resp_name):
                            errors["responsibleName"] = (
                                "Nombre solo puede contener letras"
                            )

                    # Validar DNI del responsable
                    if "dni" in responsible_data:
                        resp_dni_str = str(responsible_data["dni"]).strip()
                        if not resp_dni_str.isdigit():
                            errors["responsibleDni"] = "DNI debe contener solo números"
                        elif len(resp_dni_str) != 10:
                            errors["responsibleDni"] = (
                                "DNI debe tener exactamente 10 dígitos"
                            )
                        elif resp_dni_str == "0000000000":
                            errors["responsibleDni"] = "DNI no puede ser solo ceros"
                        elif self._is_sequential(resp_dni_str):
                            errors["responsibleDni"] = (
                                "DNI no puede ser un número secuencial"
                            )
                        else:
                            # Validar que no sea igual al DNI del participante
                            participant_dni = data.get("dni", participant.dni)
                            if resp_dni_str == str(participant_dni).strip():
                                errors["responsibleDni"] = (
                                    "El DNI del responsable no puede ser igual al del participante"
                                )

                    # Validar teléfono del responsable
                    if "phone" in responsible_data:
                        resp_phone_str = str(responsible_data["phone"]).strip()
                        if resp_phone_str:
                            if not resp_phone_str.isdigit():
                                errors["responsiblePhone"] = (
                                    "Teléfono debe contener solo números"
                                )
                            elif len(resp_phone_str) != 10:
                                errors["responsiblePhone"] = (
                                    "Teléfono debe tener exactamente 10 dígitos"
                                )
                            elif resp_phone_str == "0000000000":
                                errors["responsiblePhone"] = (
                                    "Teléfono no puede ser solo ceros"
                                )
                            elif resp_phone_str[0] != "0":
                                errors["responsiblePhone"] = (
                                    "Teléfono debe iniciar con 0"
                                )
                            elif self._is_sequential(resp_phone_str):
                                errors["responsiblePhone"] = (
                                    "Teléfono no puede ser un número secuencial"
                                )

            # Si hay errores, retornarlos
            if errors:
                return error_response("Errores de validación", code=400, data=errors)

            # ========== ACTUALIZAR CAMPOS DEL PARTICIPANTE ==========
            if "firstName" in data:
                participant.firstName = str(data["firstName"]).strip()
            if "lastName" in data:
                participant.lastName = str(data["lastName"]).strip()
            if "phone" in data:
                participant.phone = str(data["phone"]).strip()
            if "email" in data:
                participant.email = str(data["email"]).strip()
            if "address" in data:
                participant.address = str(data["address"]).strip()
            if "age" in data:
                participant.age = int(data["age"])
            if "dni" in data:
                participant.dni = str(data["dni"]).strip()
            if "type" in data:
                participant.type = str(data["type"]).strip().upper()
            if "program" in data:
                participant.program = str(data["program"]).strip().upper()

            # ========== ACTUALIZAR CAMPOS DEL RESPONSABLE ==========
            if responsible_data and responsible:
                if "name" in responsible_data:
                    responsible.name = str(responsible_data["name"]).strip()
                if "dni" in responsible_data:
                    responsible.dni = str(responsible_data["dni"]).strip()
                if "phone" in responsible_data:
                    responsible.phone = str(responsible_data["phone"]).strip()

            db.session.commit()

            # Preparar datos del responsable para la respuesta
            responsible_response = None
            if responsible:
                responsible_response = {
                    "external_id": responsible.external_id,
                    "name": responsible.name,
                    "dni": responsible.dni,
                    "phone": responsible.phone,
                }

            return success_response(
                msg="Participante actualizado correctamente",
                data={
                    "external_id": participant.external_id,
                    "firstName": participant.firstName,
                    "lastName": participant.lastName,
                    "phone": participant.phone,
                    "email": participant.email,
                    "address": participant.address,
                    "age": participant.age,
                    "dni": participant.dni,
                    "status": participant.status,
                    "type": participant.type,
                    "program": participant.program,
                    "responsible": responsible_response,
                },
            )

        except Exception as e:
            db.session.rollback()
            print(f"[UserController] Error actualizando participante: {str(e)}")
            return error_response(f"Error interno del servidor: {str(e)}", 500)