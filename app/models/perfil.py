from app import db
import uuid

class Perfil(db.Model):
    __tablename__ = 'perfil'
    
    id = db.Column(db.Integer, primary_key=True)
    fotoURL = db.Column(db.String(500))
    descripcion = db.Column(db.Text)
    celular = db.Column(db.String(20))
    direccion = db.Column(db.String(255))
    portafolio = db.Column(db.JSON)         
    redesSociales = db.Column(db.JSON)     
    habilidades = db.Column(db.JSON)        
    # Relación 1:1 con Usuario
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id', ondelete='CASCADE'), unique=True, nullable=False)
    usuario = db.relationship('Usuario', back_populates='perfil')
    
    external_id = db.Column(
        db.String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'fotoURL': self.fotoURL,
            'descripcion': self.descripcion,
            'celular': self.celular,
            'portafolio': self.portafolio or [],
            'redesSociales': self.redesSociales or [],
            'habilidades': self.habilidades or [],
            'usuario_id': self.usuario_id,
            "direccion": self.direccion,
            "external_id": self.external_id
        }