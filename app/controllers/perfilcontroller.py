import datetime
from app.models.cuenta import Cuenta
from flask import jsonify, request
from app import db
from app.models.perfil import Perfil
from app.models.representante import Representante
from app.models.usuario import Usuario
from datetime import datetime


class PerfilController:
    def get_profile(self, external_id: str):
        if not external_id:
            return jsonify({"error": "external_id es requerido"}), 400

        cuenta = Cuenta.query.filter_by(external_id=external_id).first()
        if not cuenta or not cuenta.usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404

        usuario = cuenta.usuario
        perfil = usuario.perfil
        representante = usuario.representante

        def estado_str(estado: bool | None):
            return "activo" if estado else "inactivo"

        return (
            jsonify(
                {
                    "cuenta": {
                        "correoElectronico": cuenta.correoElectronico,
                        "rol": cuenta.rol.nombre if cuenta.rol else None,
                        "external_id": cuenta.external_id,
                        "estado": estado_str(cuenta.estado),
                    },
                    "usuario": {
                        "nombre": usuario.nombre,
                        "apellido": usuario.apellido,
                        "tipoIdentificacion": usuario.tipoIdentificacion,
                        "numeroIdentificacion": usuario.numeroIdentificacion,
                        "fechaNacimiento": (
                            usuario.fechaNacimiento.isoformat()
                            if usuario.fechaNacimiento
                            else None
                        ),
                        "edad": usuario.calcular_edad(),
                        "external_id": usuario.external_id,
                    },
                    "perfil": {
                        "celular": perfil.celular if perfil else None,
                        "portafolio": perfil.portafolio if isinstance(perfil.portafolio, list) else [],
                        "redesSociales": perfil.redesSociales if isinstance(perfil.redesSociales, list) else [],
                        "direccion": perfil.direccion if perfil else None,
                        "habilidades": perfil.habilidades if isinstance(perfil.habilidades, list) else [],
                        "descripcion": perfil.descripcion if perfil else None,
                        "external_id": perfil.external_id if perfil else None,
                    },
                    "representante": {
                        "nombre": representante.nombre if representante else None,
                        "celular": representante.celular if representante else None,
                        "tipoIdentificacion": (
                            representante.tipoIdentificacion if representante else None
                        ),
                        "numeroIdentificacion": (
                            representante.numeroIdentificacion
                            if representante
                            else None
                        ),
                        "external_id": (
                            representante.external_id if representante else None
                        ),
                    },
                }
            ),
            200,
        )

    def update_profile(self, external_id: str):
        """
        Actualiza la información del perfil de usuario
        """
        if not external_id:
            return (
                jsonify({"errores": {"external_id": "external_id es requerido"}}),
                400,
            )

        cuenta = Cuenta.query.filter_by(external_id=external_id).first()
        if not cuenta or not cuenta.usuario:
            return jsonify({"errores": {"usuario": "Usuario no encontrado"}}), 404

        data = request.get_json()
        if not data:
            return (
                jsonify(
                    {"errores": {"datos": "No se proporcionaron datos para actualizar"}}
                ),
                400,
            )

        usuario = cuenta.usuario
        perfil = usuario.perfil
        representante = usuario.representante

        try:
            errores = {}

            campos_requeridos = [
                "numeroIdentificacion",
                "nombre",
                "apellido",
                "fechaNacimiento",
                "correoElectronico",
            ]

            mapeo_campos = {
                "numeroIdentificacion": {
                    "seccion": "usuario",
                    "objeto": usuario,
                    "atributo": "numeroIdentificacion",
                },
                "nombre": {
                    "seccion": "usuario",
                    "objeto": usuario,
                    "atributo": "nombre",
                },
                "apellido": {
                    "seccion": "usuario",
                    "objeto": usuario,
                    "atributo": "apellido",
                },
                "fechaNacimiento": {
                    "seccion": "usuario",
                    "objeto": usuario,
                    "atributo": "fechaNacimiento",
                },
                "correoElectronico": {
                    "seccion": "cuenta",
                    "objeto": cuenta,
                    "atributo": "correoElectronico",
                },
            }

            for campo in campos_requeridos:
                info = mapeo_campos[campo]
                seccion = info["seccion"]
                valor_actual = getattr(info["objeto"], info["atributo"])

                if seccion in data and campo in data[seccion]:
                    valor_enviado = data[seccion][campo]
                    if not valor_enviado or (
                        isinstance(valor_enviado, str)
                        and len(valor_enviado.strip()) == 0
                    ):
                        errores[campo] = "Campo requerido"
                else:
                    if not valor_actual:
                        errores[campo] = "Campo requerido"

            if "cuenta" in data and "correoElectronico" in data["cuenta"] and "correoElectronico" not in errores:
                nuevo_correo = data["cuenta"]["correoElectronico"].strip()
                
                # Normalizar rol
                rol_nombre = getattr(cuenta.rol, "nombre", str(cuenta.rol)).strip().upper()
                
                if nuevo_correo:
                    existing_cuenta = Cuenta.query.filter(
                        Cuenta.correoElectronico == nuevo_correo, Cuenta.id != cuenta.id
                    ).first()
                    if existing_cuenta:
                        errores["correoElectronico"] = "El correo electrónico ya está en uso"
                    else:
                        dominio_unl = "@unl.edu.ec"
                        if rol_nombre == "MIEMBRO_EXTERNO":
                            if nuevo_correo.lower().endswith(dominio_unl):
                                errores["correoElectronico"] = "Correo @unl.edu.ec no válido para miembros externos"
                        else:
                            if not nuevo_correo.lower().endswith(dominio_unl):
                                errores["correoElectronico"] = "Se requiere correo institucional @unl.edu.ec"

            if (
                "usuario" in data
                and "numeroIdentificacion" in data["usuario"]
                and "numeroIdentificacion" not in errores
            ):
                nuevo_numero = data["usuario"]["numeroIdentificacion"].strip()

                if nuevo_numero:
                    existing_usuario = Usuario.query.filter(
                        Usuario.numeroIdentificacion == nuevo_numero,
                        Usuario.id != usuario.id,
                    ).first()

                    existing_representante = Representante.query.filter(
                        Representante.numeroIdentificacion == nuevo_numero
                    ).first()

                    if existing_usuario or existing_representante:
                        errores["numeroIdentificacion"] = (
                            "El número de identificación ya está registrado"
                        )

            if "usuario" in data and "fechaNacimiento" in data["usuario"] and "fechaNacimiento" not in errores:
                fecha_str = data["usuario"]["fechaNacimiento"]
                if fecha_str:
                    try:
                        fecha_nacimiento = datetime.strptime(fecha_str, "%Y-%m-%d").date()
                        fecha_actual = datetime.now().date()
                        if fecha_nacimiento > fecha_actual:
                            errores["fechaNacimiento"] = "La fecha de nacimiento no puede ser futura"
                        else:
                            edad = fecha_actual.year - fecha_nacimiento.year
                            if (fecha_actual.month, fecha_actual.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
                                edad -= 1

                            # Normalizar rol
                            rol_nombre = getattr(cuenta.rol, "nombre", str(cuenta.rol)).strip().upper()
                            roles_mayoria_edad = ["DOCENTE", "ADMINISTRADOR", "ESTUDIANTE"]

                            if rol_nombre in roles_mayoria_edad and edad < 18:
                                errores["fechaNacimiento"] = "Debe ser mayor de 18 años"

                            if rol_nombre == "MIEMBRO_EXTERNO" and edad < 18:
                                # Validar representante
                                rep_data = data.get("representante")
                                if not rep_data:
                                    errores["representante_general"] = "Representante obligatorio para menores de edad"
                                else:
                                    if not rep_data.get("tipoIdentificacion"):
                                        errores["representante_tipoIdentificacion"] = "Campo requerido"
                                    if not rep_data.get("numeroIdentificacion"):
                                        errores["representante_identificacion"] = "Campo requerido"  # Cambiado
                                    if not rep_data.get("nombre"):
                                        errores["representante_nombre"] = "Campo requerido"  # Cambiado
                                    if rep_data.get("numeroIdentificacion") == data["usuario"].get("numeroIdentificacion"):
                                        errores["representante_identificacion"] = "El número de identificación ya está registrado"  
                    except ValueError:
                        errores["fechaNacimiento"] = "Formato de fecha inválido. Use YYYY-MM-DD"

            if errores:
                db.session.rollback()
                return jsonify({"errores": errores}), 400

            if "cuenta" in data and "correoElectronico" in data["cuenta"]:
                cuenta.correoElectronico = data["cuenta"]["correoElectronico"].strip()

            if "usuario" in data:
                usuario_data = data["usuario"]

                if "nombre" in usuario_data:
                    usuario.nombre = usuario_data["nombre"].strip()

                if "apellido" in usuario_data:
                    usuario.apellido = usuario_data["apellido"].strip()

                if "numeroIdentificacion" in usuario_data:
                    usuario.numeroIdentificacion = usuario_data[
                        "numeroIdentificacion"
                    ].strip()

                if "fechaNacimiento" in usuario_data:
                    try:
                        fecha = datetime.fromisoformat(
                            usuario_data["fechaNacimiento"]
                        ).date()
                        usuario.fechaNacimiento = fecha
                    except ValueError:
                        pass

            if "perfil" in data:
                perfil_data = data["perfil"]

                if not perfil and any(perfil_data.values()):
                    perfil = Perfil(usuario_id=usuario.id)
                    db.session.add(perfil)

                if perfil:
                    perfil.celular = perfil_data.get("celular")
                    # Garantizar siempre array
                    portafolio = perfil_data.get("portafolio") or []
                    if not isinstance(portafolio, list):
                        portafolio = [portafolio] if portafolio else []
                    perfil.portafolio = portafolio

                    redes = perfil_data.get("redesSociales") or []
                    if not isinstance(redes, list):
                        redes = [redes] if redes else []
                    perfil.redesSociales = redes

                    habilidades = perfil_data.get("habilidades") or []
                    if not isinstance(habilidades, list):
                        habilidades = [habilidades] if habilidades else []
                    perfil.habilidades = habilidades

                    perfil.direccion = perfil_data.get("direccion")
                    perfil.descripcion = perfil_data.get("descripcion")

            if "representante" in data:
                representante_data = data["representante"]

                if not representante and any(representante_data.values()):
                    representante = Representante(usuario_id=usuario.id)
                    db.session.add(representante)

                if representante:
                    if "nombre" in representante_data:
                        representante.nombre = representante_data["nombre"]
                    if "celular" in representante_data:
                        representante.celular = representante_data["celular"]
                    if "numeroIdentificacion" in representante_data:
                        representante.numeroIdentificacion = representante_data[
                            "numeroIdentificacion"
                        ]

            db.session.commit()

            return self.get_profile(external_id)

        except Exception as e:
            db.session.rollback()
            return (
                jsonify(
                    {"errores": {"general": f"Error al actualizar el perfil: {str(e)}"}}
                ),
                500,
            )