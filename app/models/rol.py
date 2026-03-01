from app import db
import uuid

class Rol(db.Model):
    __tablename__ = 'rol'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.String(200))
    estado = db.Column(db.Boolean, default=True)

    # Relación 1:N con Cuenta
    cuentas = db.relationship('Cuenta', back_populates='rol')

    external_id = db.Column(
        db.String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False
    )