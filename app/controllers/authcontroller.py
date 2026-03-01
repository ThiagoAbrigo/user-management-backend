from flask import jsonify
from app.models.cuenta import Cuenta

class AuthController:
    def login(self, data):
        """
        data: dict con 'correoElectronico' y 'contrasenia'
        Retorna JSON con éxito o error
        """
        correo = data.get('correoElectronico')
        contrasenia = data.get('contrasenia')

        if not correo or not contrasenia:
            return jsonify({'error': 'Correo y contraseña son requeridos'}), 400

        cuenta = Cuenta.query.filter_by(correoElectronico=correo).first()

        if not cuenta or not cuenta.estado or not cuenta.check_password(contrasenia):
            return jsonify({'error': 'Credenciales incorrectas'}), 401

        return jsonify({
            'message': 'Login exitoso',
            'cuenta': cuenta.to_dict()
        }), 200