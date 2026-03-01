from app import db
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

class Cuenta(db.Model):
    __tablename__ = 'cuenta'
    
    id = db.Column(db.Integer, primary_key=True)

    correoElectronico = db.Column(db.String(120), unique=True, nullable=False)
    contrasenia = db.Column(db.String(200), nullable=False)
    estado = db.Column(db.Boolean, default=True)
    
    # FK hacia Usuario (1:1)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id', ondelete='CASCADE'), unique=True, nullable=False)
    usuario = db.relationship('Usuario', back_populates='cuenta')

    # Relación N:1 con Rol
    rol_id = db.Column(db.Integer, db.ForeignKey('rol.id'), nullable=False)
    rol = db.relationship('Rol', back_populates='cuentas')

    external_id = db.Column(
        db.String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False
    )

    def set_password(self, password):
        self.contrasenia = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.contrasenia, password)

    def to_dict(self):
        return {
            'id': self.id,
            'correoElectronico': self.correoElectronico,
            'estado': self.estado,
            'usuario_id': self.usuario_id,
            'usuario_nombre': self.usuario.nombre if self.usuario else None,
            'rol': self.rol.nombre if self.rol else None,
            "external_id": self.external_id
        }