from flask import request, jsonify
from app import db
from app.models import Usuario, Cuenta, Rol, Perfil, Representante
from datetime import datetime, date


class UserController:

    def listar_usuarios(self):
        try:
            # Obtener todos los usuarios con sus relaciones
            usuarios = Usuario.query.all()

            # Si no hay usuarios
            if not usuarios:
                return (
                    jsonify({"message": "No hay usuarios registrados", "usuarios": []}),
                    200,
                )

            # Construir la lista de usuarios con toda su información
            lista_usuarios = []
            for usuario in usuarios:
                # Obtener la cuenta asociada (correo y rol)
                cuenta = Cuenta.query.filter_by(usuario_id=usuario.id).first()

                # Obtener el perfil
                perfil = Perfil.query.filter_by(usuario_id=usuario.id).first()

                # Obtener información del representante si existe
                representante_info = None
                if usuario.representante_id:
                    representante = Representante.query.get(usuario.representante_id)
                    if representante:
                        representante_info = {
                            "id": representante.id,
                            "tipoIdentificacion": representante.tipoIdentificacion,
                            "numeroIdentificacion": representante.numeroIdentificacion,
                            "nombre": representante.nombre,
                            "celular": representante.celular,
                            "external_id": representante.external_id,
                        }

                estado_texto = "activo" if usuario.estado else "inactivo"

                # Construir objeto del usuario
                usuario_data = {
                    "id": usuario.id,
                    "external_id": usuario.external_id,
                    "tipoIdentificacion": usuario.tipoIdentificacion,
                    "numeroIdentificacion": usuario.numeroIdentificacion,
                    "nombre": usuario.nombre,
                    "apellido": usuario.apellido,
                    "fechaNacimiento": (
                        usuario.fechaNacimiento.strftime("%Y-%m-%d")
                        if usuario.fechaNacimiento
                        else None
                    ),
                    "edad": (
                        usuario.calcular_edad()
                        if hasattr(usuario, "calcular_edad")
                        else None
                    ),
                    "estado": estado_texto,
                    "cuenta": (
                        {
                            "correoElectronico": (
                                cuenta.correoElectronico if cuenta else None
                            ),
                            "rol": cuenta.rol.nombre if cuenta and cuenta.rol else None,
                        }
                        if cuenta
                        else None
                    ),
                    "perfil": (
                        {
                            "fotoURL": perfil.fotoURL if perfil else None,
                            "descripcion": perfil.descripcion if perfil else None,
                            "celular": perfil.celular if perfil else None,
                        }
                        if perfil
                        else None
                    ),
                    "representante": representante_info,
                }

                lista_usuarios.append(usuario_data)

            return (
                jsonify(
                    {
                        "message": "Usuarios listados correctamente",
                        "total": len(lista_usuarios),
                        "usuarios": lista_usuarios,
                    }
                ),
                200,
            )

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def registrar_usuario(self):
        try:
            data = request.get_json()
            errores = {}

            campos_requeridos = [
                "tipoIdentificacion",
                "numeroIdentificacion",
                "nombre",
                "apellido",
                "fechaNacimiento",
                "correoElectronico",
                "password",
                "rol",
            ]

            # Validar campos requeridos
            for campo in campos_requeridos:
                if campo not in data or not data[campo]:
                    errores[campo] = "Campo requerido"

            # Continuar con las demás validaciones
            if data:
                # Validar rol
                rol = None
                if "rol" in data and data["rol"]:
                    rol = Rol.query.filter_by(nombre=data["rol"]).first()
                    if not rol:
                        errores["rol"] = "Rol no válido"

                # Validar fecha de nacimiento
                fecha_nacimiento = None
                if "fechaNacimiento" in data and data["fechaNacimiento"]:
                    try:
                        fecha_nacimiento = datetime.strptime(
                            data["fechaNacimiento"], "%Y-%m-%d"
                        ).date()
                        if fecha_nacimiento > datetime.now().date():
                            errores["fechaNacimiento"] = "La fecha de nacimiento no puede ser futura"
                    except ValueError:
                        errores["fechaNacimiento"] = "Formato de fecha inválido. Use YYYY-MM-DD"

                # Validar correo según rol
                if rol and "correoElectronico" in data and data["correoElectronico"]:
                    correo = data["correoElectronico"]
                    dominio_unl = "@unl.edu.ec"

                    if rol.nombre == "MIEMBRO_EXTERNO":
                        if correo.lower().endswith(dominio_unl):
                            errores["correoElectronico"] = (
                                "Correo @unl.edu.ec no válido para miembros externos"
                            )
                    else:
                        if not correo.lower().endswith(dominio_unl):
                            errores["correoElectronico"] = (
                                "Se requiere correo institucional @unl.edu.ec"
                            )

                # Validar edad y representante
                edad = None
                if rol and fecha_nacimiento and "fechaNacimiento" not in errores:
                    # Crear objeto temporal para calcular edad
                    usuario_temp = Usuario(
                        tipoIdentificacion=data.get("tipoIdentificacion", ""),
                        numeroIdentificacion=data.get("numeroIdentificacion", ""),
                        nombre=data.get("nombre", ""),
                        apellido=data.get("apellido", ""),
                        fechaNacimiento=fecha_nacimiento,
                    )
                    edad = usuario_temp.calcular_edad()

                    roles_mayoria_edad = ["DOCENTE", "ADMINISTRADOR", "ESTUDIANTE"]

                    if rol.nombre in roles_mayoria_edad and edad < 18:
                        errores["fechaNacimiento"] = "Debe ser mayor de 18 años"

                    if rol.nombre == "MIEMBRO_EXTERNO":
                        if edad < 18:
                            rep_data = data.get("representante")

                            if not rep_data:
                                errores["representante"] = "Representante obligatorio para miembros externos menores de edad"
                            else:
                                # Validar campos del representante
                                if "tipoIdentificacion" not in rep_data or not rep_data["tipoIdentificacion"]:
                                    errores["rep_tipoIdentificacion"] = "Campo requerido"

                                if "numeroIdentificacion" not in rep_data or not rep_data["numeroIdentificacion"]:
                                    errores["rep_numeroIdentificacion"] = "Campo requerido"

                                if "nombre" not in rep_data or not rep_data["nombre"]:
                                    errores["rep_nombre"] = "Campo requerido"

                                # Validar que el representante no sea el mismo que el usuario
                                if rep_data.get("numeroIdentificacion") and rep_data["numeroIdentificacion"] == data.get("numeroIdentificacion"):
                                    errores["rep_numeroIdentificacion"] = (
                                        "El representante no puede tener la misma identificación que el usuario"
                                    )

                                # Validar si el representante ya existe
                                if (rep_data.get("numeroIdentificacion") and 
                                    "rep_numeroIdentificacion" not in errores and
                                    rep_data["numeroIdentificacion"] != data.get("numeroIdentificacion")):
                                    
                                    usuario_rep = Usuario.query.filter_by(
                                        numeroIdentificacion=rep_data["numeroIdentificacion"]
                                    ).first()
                                    representante_rep = Representante.query.filter_by(
                                        numeroIdentificacion=rep_data["numeroIdentificacion"]
                                    ).first()
                                    
                                    if usuario_rep or representante_rep:
                                        errores["rep_numeroIdentificacion"] = (
                                            "El número de identificación ya está registrado"
                                        )

                        elif edad >= 18 and "representante" in data:
                            errores["representante"] = "Representante solo para miembros externos menores de edad"

                # Validar correo duplicado
                if (data.get("correoElectronico") and 
                    "correoElectronico" not in errores):
                    
                    cuenta_existente = Cuenta.query.filter_by(
                        correoElectronico=data["correoElectronico"]
                    ).first()
                    if cuenta_existente:
                        errores["correoElectronico"] = "El correo electrónico ya está registrado"

                # Validar identificación duplicada
                if (data.get("numeroIdentificacion") and 
                    "numeroIdentificacion" not in errores):
                    
                    num_identificacion = data["numeroIdentificacion"]

                    usuario_existente = Usuario.query.filter_by(
                        numeroIdentificacion=num_identificacion
                    ).first()

                    representante_existente = Representante.query.filter_by(
                        numeroIdentificacion=num_identificacion
                    ).first()

                    if usuario_existente or representante_existente:
                        errores["numeroIdentificacion"] = "El número de identificación ya está registrado"

                # Validar contraseña
                if (data.get("password") and 
                    "password" not in errores):
                    
                    password = data["password"]
                    if len(password) < 6:
                        errores["password"] = "La contraseña debe tener al menos 6 caracteres"

            # Si hay errores, devolver todos
            if errores:
                return jsonify({"errores": errores}), 400

            # Si llegamos aquí, no hay errores, proceder con el registro
            # Validar que todos los datos necesarios existen
            if not all(campo in data for campo in campos_requeridos):
                return jsonify({"error": "Datos incompletos"}), 400

            # Crear usuario
            usuario = Usuario(
                tipoIdentificacion=data["tipoIdentificacion"],
                numeroIdentificacion=data["numeroIdentificacion"],
                nombre=data["nombre"],
                apellido=data["apellido"],
                fechaNacimiento=fecha_nacimiento,
            )

            db.session.add(usuario)
            db.session.flush()

            # Crear o asociar representante
            representante = None
            if rol.nombre == "MIEMBRO_EXTERNO" and edad < 18:
                rep_data = data["representante"]
                representante_existente = Representante.query.filter_by(
                    numeroIdentificacion=rep_data["numeroIdentificacion"]
                ).first()

                if representante_existente:
                    representante = representante_existente
                else:
                    representante = Representante(
                        tipoIdentificacion=rep_data["tipoIdentificacion"],
                        numeroIdentificacion=rep_data["numeroIdentificacion"],
                        nombre=rep_data["nombre"],
                        celular=rep_data.get("celular"),
                    )
                    db.session.add(representante)
                    db.session.flush()

                usuario.representante_id = representante.id

            # Crear Cuenta
            cuenta = Cuenta(
                correoElectronico=data["correoElectronico"],
                usuario_id=usuario.id,
                rol_id=rol.id,
            )
            cuenta.set_password(data["password"])
            db.session.add(cuenta)

            # Crear Perfil
            perfil = Perfil(
                usuario_id=usuario.id,
                fotoURL=None,
                descripcion="",
                celular=None,
                portafolio=None,
                redesSociales=None,
                habilidades=None,
            )
            db.session.add(perfil)

            db.session.commit()

            return (
                jsonify(
                    {
                        "message": "Usuario registrado correctamente",
                        "usuario_id": usuario.id,
                    }
                ),
                201,
            )

        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500