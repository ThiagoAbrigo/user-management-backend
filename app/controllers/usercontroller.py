from werkzeug.security import generate_password_hash
from app.models.participant import Participant
from app.models.responsible import Responsible
from flask import request
from app import db
import uuid


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
        campo_esp = {
            "name": "nombre",
            "estate": "estamento",
            "age": "edad",
            "dni": "DNI",
            "email": "correo electrónico",
            "password": "contraseña",
            "address": "dirección",
            "phone": "teléfono",
        }

        # ==============================
        # VALIDAR CAMPOS OBLIGATORIOS DEL PARTICIPANTE
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
        # VALIDAR ESTAMENTO
        # ==============================

        if data["estate"] not in ["UNIVERSITARIO", "MIEMBRO EXTERNO"]:
            errores["estate"] = "Estamento inválido"

        # ==============================
        # VALIDAR EMAIL SEGÚN ESTAMENTO
        # ==============================

        email = data["email"].strip().lower()

        import re
        email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        
        # Validar formato básico primero
        if not re.match(email_regex, email):
            errores["email"] = "Formato de correo electrónico inválido"
        else:
            # Validar según el estamento
            if data["estate"] == "UNIVERSITARIO":
                if not email.endswith("@unl.edu.ec"):
                    errores["email"] = "El correo debe pertenecer al dominio @unl.edu.ec"
            elif data["estate"] == "MIEMBRO EXTERNO":
                if email.endswith("@unl.edu.ec"):
                    errores["email"] = "El dominio @unl.edu.ec no está permitido"

        # ==============================
        # VALIDAR EDAD PERMITIDA
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
        # VALIDAR CÉDULA
        # ==============================

        dni = data["dni"]
        if not dni.isdigit() or len(dni) != 10:
            errores["dni"] = "La cédula debe tener 10 dígitos numéricos"

        # ==============================
        # VALIDAR DNI Y EMAIL ÚNICOS GLOBALMENTE
        # ==============================

        # -------- DNI PARTICIPANTE --------
        if Participant.query.filter_by(dni=data["dni"]).first():
            errores["dni"] = "El DNI ya está registrado"

        if Responsible.query.filter_by(dni=data["dni"]).first():
            errores["dni"] = "El DNI ya está registrado"

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
        # VALIDAR REGLA DE MENOR DE EDAD
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
                        "El DNI ya está registrado "
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
        # CREAR PARTICIPANTE
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
        # CREAR RESPONSABLE SOLO SI APLICA
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

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {"msg": f"Error al registrar usuario: {str(e)}"}, 500

        return {
            "msg": "Usuario creado correctamente",
            "external_id": new_user.external_id,
        }, 201
    
    def get_responsible_by_dni(self, dni):
        try:
            # Buscamos al responsable por su DNI/Cédula
            responsible = Responsible.query.filter_by(dni=dni).first()

            if not responsible:
                return {"msg": "Responsable no encontrado", "data": None}, 404

            # Devolvemos la data que el frontend necesita para autorrellenar
            data = {
                "name": responsible.name,
                "dni": responsible.dni,
                "phone": responsible.phone
            }

            return {"msg": "Responsable encontrado", "data": data}, 200

        except Exception as e:
            return {"msg": "Error al buscar responsable", "error": str(e)}, 500

    def update_user(self, external_id, data):
            errores = {}

            user = Participant.query.filter_by(external_id=external_id).first()

            if not user:
                return {"msg": "Usuario no encontrado"}, 404

            campo_esp = {
                "name": "nombre",
                "estate": "estamento",
                "age": "edad",
                "dni": "DNI",
                "email": "correo electrónico",
                "password": "contraseña",
                "address": "dirección",
                "phone": "teléfono",
            }
            # ==============================
            # VALIDAR CAMPOS OBLIGATORIOS DEL PARTICIPANTE
            # ==============================

            required_fields = [
                "name",
                "age",
                "dni",
                "email",
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
            # VALIDAR ESTAMENTO
            # ==============================

            estate = data.get("estate", user.estate)

            if estate not in ["UNIVERSITARIO", "MIEMBRO EXTERNO"]:
                errores["estate"] = "Estamento inválido"

            # ==============================
            # VALIDAR EMAIL
            # ==============================

            email = data["email"].strip().lower()

            import re
            email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
            
            # Validar formato básico primero
            if not re.match(email_regex, email):
                errores["email"] = "Formato de correo electrónico inválido"
            else:
                # Validar según el estamento
                if data["estate"] == "UNIVERSITARIO":
                    if not email.endswith("@unl.edu.ec"):
                        errores["email"] = "El correo debe pertenecer al dominio @unl.edu.ec"
                elif data["estate"] == "MIEMBRO EXTERNO":
                    if email.endswith("@unl.edu.ec"):
                        errores["email"] = "El dominio @unl.edu.ec no está permitido"

            # ==============================
            # VALIDAR EDAD
            # ==============================

            try:
                age = int(data.get("age", user.age))

                if age < 5 or age > 60:
                    errores["age"] = "La edad debe estar entre 5 y 60 años"

                if estate == "UNIVERSITARIO" and age < 18:
                    errores["age"] = "Deben ser mayores de edad"

            except ValueError:
                errores["age"] = "Edad inválida"
                age = user.age

            # ==============================
            # VALIDAR DNI
            # ==============================

            dni = data.get("dni", user.dni)

            if not dni.isdigit() or len(dni) != 10:
                errores["dni"] = "La cédula debe tener 10 dígitos numéricos"

            # ==============================
            # VALIDAR UNICIDAD (EXCLUYENDO AL MISMO USUARIO)
            # ==============================

            # DNI
            existing_dni = Participant.query.filter(
                Participant.dni == dni,
                Participant.id != user.id
            ).first()

            if existing_dni:
                errores["dni"] = "El DNI ya está registrado"

            existing_responsible_dni = Responsible.query.filter_by(dni=dni).first()
            if existing_responsible_dni:
                errores["dni"] = "El DNI ya está registrado"

            # EMAIL
            existing_email = Participant.query.filter(
                Participant.email == email,
                Participant.id != user.id
            ).first()

            if existing_email:
                errores["email"] = "El correo electrónico ya está registrado"

            # ==============================
            # VALIDAR REGLA DE MENOR
            # ==============================

            is_minor = age < 18
            needs_responsible = is_minor and estate == "MIEMBRO EXTERNO"

            responsible_data = data.get("responsible")

            existing_responsible = Responsible.query.filter_by(
                participant_id=user.id
            ).first()

            if needs_responsible:

                if not responsible_data and not existing_responsible:
                    errores["responsible"] = (
                        "Los menores MIEMBRO EXTERNO requieren representante"
                    )

                if responsible_data:

                    responsible_dni = responsible_data.get("dni", "").strip()

                    # No puede ser igual al participante
                    if responsible_dni == dni:
                        errores["responsibleDni"] = (
                            "El DNI del responsable no puede ser igual al del participante"
                        )

                    # Debe tener 10 dígitos numéricos
                    if not responsible_dni.isdigit() or len(responsible_dni) != 10:
                        errores["responsibleDni"] = (
                            "La cédula del representante debe tener 10 dígitos numéricos"
                        )

                    # No puede existir como PARTICIPANTE
                    existing_participant_dni = Participant.query.filter_by(
                        dni=responsible_dni
                    ).first()

                    if existing_participant_dni:
                        errores["responsibleDni"] = (
                            "El DNI ya está registrado"
                        )

                    # No puede existir como OTRO RESPONSABLE
                    existing_other_responsible = Responsible.query.filter(
                        Responsible.dni == responsible_dni,
                        Responsible.participant_id != user.id
                    ).first()

                    if existing_other_responsible:
                        errores["responsibleDni"] = (
                            "El DNI ya está registrado"
                        )

                    # Validar campos obligatorios
                    required_fields = ["name", "dni", "phone"]

                    for field in required_fields:
                        if not responsible_data.get(field):
                            nombre_campo = campo_esp.get(field, field)
                            errores[f"responsible{field.capitalize()}"] = (
                                f"El campo {nombre_campo} del representante es obligatorio"
                            )

            # Si hay errores
            if errores:
                return {"errors": errores, "msg": "Errores de validación"}, 400

            # ==============================
            # ACTUALIZAR USUARIO
            # ==============================

            user.name = data.get("name", user.name)
            user.estate = estate
            user.age = age
            user.dni = dni
            user.email = email
            user.address = data.get("address", user.address)

            if data.get("password"):
                user.password = generate_password_hash(data["password"])

            # ==============================
            # MANEJAR RESPONSABLE
            # ==============================

            if needs_responsible:

                if existing_responsible:
                    existing_responsible.name = responsible_data.get(
                        "name", existing_responsible.name
                    )
                    existing_responsible.dni = responsible_data.get(
                        "dni", existing_responsible.dni
                    )
                    existing_responsible.phone = responsible_data.get(
                        "phone", existing_responsible.phone
                    )
                else:
                    new_responsible = Responsible(
                        name=responsible_data["name"],
                        dni=responsible_data["dni"],
                        phone=responsible_data["phone"],
                        participant_id=user.id,
                    )
                    db.session.add(new_responsible)

            else:
                if existing_responsible:
                    db.session.delete(existing_responsible)

            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                return {"msg": f"Error al actualizar usuario: {str(e)}"}, 500

            return {"msg": "Usuario actualizado correctamente"}, 200