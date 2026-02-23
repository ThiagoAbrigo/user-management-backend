from werkzeug.security import generate_password_hash
from app.models.participant import Participant
from app.models.responsible import Responsible
from flask import request
from app import db
import uuid

from app.utils.responses import error_response, success_response
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

    def get_users(self):
        try:
            participants = Participant.query.all()

            data = []

            for p in participants:
                responsible_name = None

                if hasattr(p, "responsibles") and p.responsibles:
                    responsible_name = p.responsibles[0].name

                data.append(
                    {
                        "external_id": p.external_id,
                        "name": p.name,
                        "email": p.email,
                        "estate": p.estate,
                        "dni": p.dni,
                        "age": p.age,
                        "status": p.status,
                        "responsible_name": responsible_name,
                    }
                )

            return {"msg": "Usuarios listados correctamente", "data": data}, 200

        except Exception as e:
            return {"msg": "Error interno del servidor", "error": str(e)}, 500

    def create_user(self, data):
        errores = {}

        # Diccionario de traducción de campos (para participante y responsable)
        campo_esp = {
            # Campos del participante
            "name": "nombre",
            "estate": "estamento",
            "age": "edad",
            "dni": "DNI",
            "email": "correo electrónico",
            "password": "contraseña",
            "address": "dirección",
            # Campos del responsable
            "phone": "teléfono",
        }

        # ==============================
        # 1️⃣ VALIDAR CAMPOS OBLIGATORIOS DEL PARTICIPANTE
        # ==============================

        required_fields = [
            "name",
            "estate",
            "age",
            "dni",
            "email",
            "password",
            "address",
        ]

        for field in required_fields:
            if not data.get(field):
                nombre_campo = campo_esp.get(field, field)
                errores[field] = f"El campo {nombre_campo} es obligatorio"

        # Si ya hay errores de campos obligatorios, no seguir validando
        if errores:
            return {"errors": errores, "msg": "Errores de validación"}, 400

        # ==============================
        # 2️⃣ VALIDAR ESTAMENTO
        # ==============================

        if data["estate"] not in ["UNIVERSITARIO", "MIEMBRO EXTERNO"]:
            errores["estate"] = "Estamento inválido"

        # ==============================
        # 2️⃣d VALIDAR EMAIL SEGÚN ESTAMENTO
        # ==============================

        email = data["email"].strip().lower()

        if data["estate"] == "UNIVERSITARIO":
            if not email.endswith("@unl.edu.ec"):
                errores["email"] = "El correo debe pertenecer al dominio @unl.edu.ec"

        elif data["estate"] == "MIEMBRO EXTERNO":
            import re

            email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
            if not re.match(email_regex, email):
                errores["email"] = "Formato de correo electrónico inválido"

        # ==============================
        # 2️⃣b VALIDAR EDAD PERMITIDA
        # ==============================

        try:
            age = int(data["age"])
            if age < 5 or age > 60:
                errores["age"] = "La edad debe estar entre 5 y 60 años"
            if data["estate"] == "UNIVERSITARIO" and age < 18:
                errores["age"] = "Deben ser mayores de edad"
        except ValueError:
            errores["age"] = "Edad inválida"

        # ==============================
        # 2️⃣c VALIDAR CÉDULA
        # ==============================

        dni = data["dni"]
        if not dni.isdigit() or len(dni) != 10:
            errores["dni"] = "La cédula debe tener exactamente 10 dígitos numéricos"

        # ==============================
        # 3️⃣ VALIDAR DNI Y EMAIL ÚNICOS GLOBALMENTE
        # ==============================

        # -------- DNI PARTICIPANTE --------
        if Participant.query.filter_by(dni=data["dni"]).first():
            errores["dni"] = "El DNI ya está registrado"

        if Responsible.query.filter_by(dni=data["dni"]).first():
            errores["dni"] = "El DNI ya está registrado como representante"

        # -------- EMAIL PARTICIPANTE --------
        if Participant.query.filter_by(email=data["email"]).first():
            errores["email"] = "El correo electrónico ya está registrado"

        # Solo si Responsible tiene email en su modelo
        if hasattr(Responsible, "email"):
            if Responsible.query.filter_by(email=data["email"]).first():
                errores["email"] = (
                    "El correo electrónico ya está registrado como representante"
                )

        # ==============================
        # 4️⃣ VALIDAR REGLA DE MENOR DE EDAD
        # ==============================

        age = int(data["age"])
        is_minor = age < 18

        needs_responsible = is_minor and data["estate"] == "MIEMBRO EXTERNO"

        # Si necesita representante, validar datos
        if needs_responsible:
            responsible_data = data.get("responsible")

            if responsible_data:
                # Validación DNI igual al participante
                if responsible_data.get("dni") == data["dni"]:
                    errores["responsibleDni"] = (
                        "El DNI del responsable no puede ser igual al del participante"
                    )

            if not responsible_data:
                errores["responsible"] = (
                    "Los menores MIEMBRO EXTERNO requieren representante"
                )
            else:
                responsible_required = ["name", "dni", "phone"]

                for field in responsible_required:
                    if not responsible_data.get(field):
                        nombre_campo = campo_esp.get(field, field)
                        errores[f"responsible{field.capitalize()}"] = (
                            f"El campo {nombre_campo} del representante es obligatorio"
                        )

                # -------- DNI RESPONSABLE --------
                if Participant.query.filter_by(dni=responsible_data["dni"]).first():
                    errores["responsibleDni"] = (
                        "El DNI del representante no puede ser de un participante"
                    )

                # -------- EMAIL RESPONSABLE (si existe en modelo) --------
                if hasattr(Responsible, "email") and responsible_data.get("email"):
                    if Participant.query.filter_by(
                        email=responsible_data["email"]
                    ).first():
                        errores["responsibleEmail"] = (
                            "El correo electrónico del representante ya pertenece a un participante"
                        )

                    if Responsible.query.filter_by(
                        email=responsible_data["email"]
                    ).first():
                        errores["responsibleEmail"] = (
                            "El correo electrónico del representante ya está registrado"
                        )

        # Si hay errores, devolver todos
        if errores:
            return {"errors": errores, "msg": "Errores de validación"}, 400

        # ==============================
        # 5️⃣ CREAR PARTICIPANTE
        # ==============================

        new_user = Participant(
            name=data["name"],
            estate=data["estate"],
            age=age,
            dni=data["dni"],
            email=data["email"],
            role="USUARIO",
            password=generate_password_hash(data["password"]),
            address=data["address"],
            status="ACTIVO",
        )

        db.session.add(new_user)
        db.session.flush()

        # ==============================
        # 6️⃣ CREAR RESPONSABLE SOLO SI APLICA
        # ==============================

        if needs_responsible:
            responsible_data = data["responsible"]

            new_responsible = Responsible(
                name=responsible_data["name"],
                dni=responsible_data["dni"],
                phone=responsible_data["phone"],
                participant_id=new_user.id,
            )

            db.session.add(new_responsible)

        # ==============================
        # 7️⃣ COMMIT
        # ==============================

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {"msg": f"Error al registrar usuario: {str(e)}"}, 500

        return {
            "msg": "Usuario creado correctamente",
            "external_id": new_user.external_id,
        }, 201

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
