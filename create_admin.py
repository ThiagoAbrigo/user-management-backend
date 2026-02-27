from app import create_app, db
from app.models import Participant
from werkzeug.security import generate_password_hash
import uuid

app = create_app()

def create_admin():
    with app.app_context():
        existing_admin = Participant.query.filter_by(email="admin@admin.com").first()

        if existing_admin:
            print("El administrador ya existe.")
            return

        admin = Participant(
            external_id=str(uuid.uuid4()),
            name="Administrador",
            estate="UNIVERSITARIO",
            age=38,
            dni="1150691804", 
            email="admin@admin.com",
            role="ADMINISTRADOR",
            password=generate_password_hash("admin123"),
            address="Dirección Administrador",
            status="ACTIVO",
        )

        db.session.add(admin)
        db.session.commit()
        print("Administrador creado correctamente.")

if __name__ == "__main__":
    create_admin()