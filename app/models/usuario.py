from app import db
import uuid
from datetime import date

class Usuario(db.Model):
    __tablename__ = 'usuario'
    
    id = db.Column(db.Integer, primary_key=True)
    tipoIdentificacion = db.Column(db.String(50), nullable=False)
    numeroIdentificacion = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    fechaNacimiento = db.Column(db.Date, nullable=False)
    estado = db.Column(db.Boolean, default=True)
    
    # FK opcional hacia Representante (1 Representante -> muchos Usuarios)
    representante_id = db.Column(
        db.Integer,
        db.ForeignKey('representante.id'),
        nullable=True
    )

    # Relaciones
    perfil = db.relationship('Perfil', back_populates='usuario', uselist=False, cascade='all, delete-orphan')
    representante = db.relationship('Representante', back_populates='usuarios')
    cuenta = db.relationship('Cuenta', back_populates='usuario', uselist=False, cascade='all, delete-orphan')

    external_id = db.Column(
        db.String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False
    )
    
    def calcular_edad(self):
        hoy = date.today()
        edad = hoy.year - self.fechaNacimiento.year

        if (hoy.month, hoy.day) < (self.fechaNacimiento.month, self.fechaNacimiento.day):
            edad -= 1

        return edad

    def to_dict(self):
        return {
            'id': self.id,
            'tipoIdentificacion': self.tipoIdentificacion,
            'nombre': self.nombre,
            'apellido': self.apellido,
            'fechaNacimiento': self.fechaNacimiento.isoformat() if self.fechaNacimiento else None,
            'edad': self.calcular_edad(),
            'estado': self.estado,
            'roles': [rol.to_dict_basic() for rol in self.roles] if self.roles else [],
            "external_id": self.external_id
        }