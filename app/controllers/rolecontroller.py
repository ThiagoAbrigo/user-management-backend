from flask import jsonify
from app.models import Rol
from app import db

class RolController:

    def listar_roles(self):
        try:
            roles = Rol.query.all()

            data = []
            for rol in roles:
                data.append({
                    "id": rol.id,
                    "external_id": rol.external_id,
                    "nombre": rol.nombre,
                    "descripcion": rol.descripcion,
                    "estado": rol.estado
                })

            return jsonify({
                "message": "Roles listados correctamente",
                "total": len(data),
                "roles": data
            }), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500