from app import db
import uuid

class Representante(db.Model):
    __tablename__ = 'representante'
    
    id = db.Column(db.Integer, primary_key=True)
    tipoIdentificacion = db.Column(db.String(50), nullable=False)
    numeroIdentificacion = db.Column(db.String(50), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    celular = db.Column(db.String(20))
    
    # Relación 1:N con Usuario
    usuarios = db.relationship('Usuario', back_populates='representante')

    external_id = db.Column(
        db.String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'tipoIdentificacion': self.tipoIdentificacion,
            'nombre': self.nombre,
            'celular': self.celular,
            'usuario_id': self.usuario_id,
            'usuario_nombre': self.usuario.nombre_completo if self.usuario else None,
            "external_id": self.external_id
        }