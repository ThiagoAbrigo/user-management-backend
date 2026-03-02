from app import create_app, db
from app.models import Usuario, Cuenta, Rol
from werkzeug.security import generate_password_hash
import uuid

app = create_app()

def create_admin():
    with app.app_context():
        # Verifica si ya existe la cuenta del admin
        existing_admin = Cuenta.query.filter_by(correoElectronico="admin@admin.com").first()
        if existing_admin:
            print("El administrador ya existe.")
            return

        # Crea el usuario (datos personales)
        admin_usuario = Usuario(
            tipoIdentificacion="CEDULA",
            numeroIdentificacion="0000000001",
            nombre="Administrador",
            apellido="General",
            fechaNacimiento="1990-01-01",
            estado=True,
            representante_id=None,
            external_id=str(uuid.uuid4())
        )
        db.session.add(admin_usuario)
        db.session.commit()  # Necesario para obtener el ID

        # Obtén el id del rol ADMINISTRADOR
        rol_admin = Rol.query.filter_by(nombre="ADMINISTRADOR").first()

        # Crea la cuenta de login asociada al usuario
        admin_cuenta = Cuenta(
            correoElectronico="admin@admin.com",
            contrasenia=generate_password_hash("admin123"),
            estado=True,
            usuario_id=admin_usuario.id,
            rol_id=rol_admin.id,
            external_id=str(uuid.uuid4())
        )
        db.session.add(admin_cuenta)
        db.session.commit()

        print("Administrador creado correctamente.")

if __name__ == "__main__":
    create_admin()