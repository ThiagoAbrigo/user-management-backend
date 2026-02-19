from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()

def create_admin():
    with app.app_context():

        existing_admin = User.query.filter_by(email="admin@admin.com").first()

        if existing_admin:
            print("El administrador ya existe.")
            return

        admin = User(
            email="admin@admin.com",
            password=generate_password_hash("Admin123"),
            role="ADMINISTRADOR"
        )

        db.session.add(admin)
        db.session.commit()

        print("Administrador creado correctamente.")

if __name__ == "__main__":
    create_admin()
