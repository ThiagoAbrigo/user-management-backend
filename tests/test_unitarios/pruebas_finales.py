import unittest
from unittest.mock import patch, MagicMock
from app.controllers.usercontroller import UserController
from app.controllers.authcontroller import AuthController
from werkzeug.security import check_password_hash


class TestUserController(unittest.TestCase):
    """Clase de prueba unificada para UserController y AuthController"""

    def setUp(self):
        """Configuración común para todas las pruebas"""
        self.user_controller = UserController()
        self.auth_controller = AuthController()

        # Datos válidos para crear usuario
        self.valid_create_data = {
            "name": "Juan Perez",
            "estate": "UNIVERSITARIO",
            "age": "25",
            "dni": "1234567890",
            "email": "juan@unl.edu.ec",
            "password": "123456",
            "address": "Loja"
        }

        # Usuario mock existente para actualización y login
        self.mock_user = MagicMock()
        self.mock_user.id = 1
        self.mock_user.external_id = "ABC123"
        self.mock_user.name = "Juan"
        self.mock_user.estate = "UNIVERSITARIO"
        self.mock_user.age = 25
        self.mock_user.dni = "1234567890"
        self.mock_user.email = "juan@unl.edu.ec"
        self.mock_user.password = "hashed_password_123"
        self.mock_user.address = "Loja"
        self.mock_user.role = "participant"
        self.mock_user.status = True
        self.mock_user.responsibles = []  # Lista vacía de responsables

        # Mock de responsable para pruebas con responsable asignado
        self.mock_responsible = MagicMock()
        self.mock_responsible.name = "Carlos Perez"
        self.mock_responsible.dni = "0987654321"
        self.mock_responsible.phone = "0999999999"

        # Datos válidos para actualizar usuario
        self.valid_update_data = {
            "name": "Juan Updated",
            "estate": "UNIVERSITARIO",
            "age": "26",
            "dni": "1234567890",
            "email": "juan@unl.edu.ec",
            "address": "Quito"
        }

        # Datos válidos para login
        self.valid_login_data = {
            "email": "juan@unl.edu.ec",
            "password": "123456"
        }

    # =====================================
    # PRUEBAS DE CREACIÓN DE USUARIO
    # =====================================

    def test_create_user_missing_required_fields(self):
        """Prueba: Creación con campos obligatorios faltantes"""
        invalid_data = {}

        response, status = self.user_controller.create_user(invalid_data)

        self.assertEqual(status, 400)
        self.assertIn("errors", response)
        self.assertIn("name", response["errors"])

    @patch("app.controllers.usercontroller.Participant")
    @patch("app.controllers.usercontroller.Responsible")
    def test_create_user_invalid_university_email(
        self, mock_responsible, mock_participant
    ):
        """Prueba: Email inválido para usuario universitario"""
        data = self.valid_create_data.copy()
        data["email"] = "juan@gmail.com"

        mock_participant.query.filter_by.return_value.first.return_value = None
        mock_responsible.query.filter_by.return_value.first.return_value = None

        response, status = self.user_controller.create_user(data)

        self.assertEqual(status, 400)
        self.assertIn("email", response["errors"])

    @patch("app.controllers.usercontroller.Participant")
    @patch("app.controllers.usercontroller.Responsible")
    def test_create_user_duplicate_dni(
        self, mock_responsible, mock_participant
    ):
        """Prueba: DNI duplicado al crear usuario"""
        mock_participant.query.filter_by.return_value.first.return_value = MagicMock()

        response, status = self.user_controller.create_user(self.valid_create_data)

        self.assertEqual(status, 400)
        self.assertIn("dni", response["errors"])

    @patch("app.controllers.usercontroller.db")
    @patch("app.controllers.usercontroller.Participant")
    @patch("app.controllers.usercontroller.Responsible")
    def test_create_user_success(
        self, mock_responsible, mock_participant, mock_db
    ):
        """Prueba: Creación exitosa de usuario"""
        mock_participant.query.filter_by.return_value.first.return_value = None
        mock_responsible.query.filter_by.return_value.first.return_value = None

        mock_user_instance = MagicMock()
        mock_user_instance.id = 1
        mock_user_instance.external_id = "ABC123"

        mock_participant.return_value = mock_user_instance

        response, status = self.user_controller.create_user(self.valid_create_data)

        self.assertEqual(status, 201)
        self.assertEqual(response["msg"], "Usuario creado correctamente")
        mock_db.session.add.assert_called()
        mock_db.session.commit.assert_called()

    # =====================================
    # PRUEBAS DE ACTUALIZACIÓN DE USUARIO
    # =====================================

    @patch("app.controllers.usercontroller.db")
    @patch("app.controllers.usercontroller.Responsible")
    @patch("app.controllers.usercontroller.Participant")
    def test_update_user_success(
        self, mock_participant, mock_responsible, mock_db
    ):
        """Prueba: Actualización exitosa de usuario"""
        mock_participant.query.filter_by.return_value.first.return_value = self.mock_user

        mock_participant.query.filter.return_value.first.return_value = None
        mock_responsible.query.filter_by.return_value.first.return_value = None
        mock_responsible.query.filter.return_value.first.return_value = None

        response, status = self.user_controller.update_user("ABC123", self.valid_update_data)

        self.assertEqual(status, 200)
        self.assertEqual(response["msg"], "Usuario actualizado correctamente")
        mock_db.session.commit.assert_called_once()

    @patch("app.controllers.usercontroller.Responsible")
    @patch("app.controllers.usercontroller.Participant")
    def test_update_user_empty_fields(self, mock_participant, mock_responsible):
        """Prueba: Actualización con campos vacíos"""
        mock_participant.query.filter_by.return_value.first.return_value = self.mock_user

        # Evitar que entre a DB real
        mock_participant.query.filter.return_value.first.return_value = None
        mock_responsible.query.filter_by.return_value.first.return_value = None
        mock_responsible.query.filter.return_value.first.return_value = None

        empty_data = {
            "name": "",
            "estate": "",
            "age": "",
            "dni": "",
            "email": ""
        }

        response, status = self.user_controller.update_user("ABC123", empty_data)

        self.assertEqual(status, 400)
        self.assertIn("errors", response)

    @patch("app.controllers.usercontroller.Responsible")
    @patch("app.controllers.usercontroller.Participant")
    def test_update_user_duplicate_dni(
        self, mock_participant, mock_responsible
    ):
        """Prueba: Actualización con DNI ya registrado"""
        mock_participant.query.filter_by.return_value.first.return_value = self.mock_user

        mock_participant.query.filter.return_value.first.return_value = MagicMock()

        data = self.valid_update_data.copy()
        data["dni"] = "9999999999"

        response, status = self.user_controller.update_user("ABC123", data)

        self.assertEqual(status, 400)
        self.assertIn("dni", response["errors"])

    # =====================================
    # PRUEBAS DE LOGIN
    # =====================================

    def test_login_missing_credentials(self):
        """Prueba: Login sin email o contraseña"""
        # Caso: Sin email ni password
        response, status = self.auth_controller.login({})
        self.assertEqual(status, 400)
        self.assertEqual(response["msg"], "Email y contraseña son obligatorios")

        # Caso: Solo email
        response, status = self.auth_controller.login({"email": "test@test.com"})
        self.assertEqual(status, 400)
        self.assertEqual(response["msg"], "Email y contraseña son obligatorios")

        # Caso: Solo password
        response, status = self.auth_controller.login({"password": "123456"})
        self.assertEqual(status, 400)
        self.assertEqual(response["msg"], "Email y contraseña son obligatorios")

    @patch("app.controllers.authcontroller.Participant")
    def test_login_user_not_found(self, mock_participant):
        """Prueba: Login con email no registrado"""
        mock_participant.query.filter_by.return_value.first.return_value = None

        response, status = self.auth_controller.login(self.valid_login_data)

        self.assertEqual(status, 404)
        self.assertEqual(response["msg"], "Usuario no encontrado")

    @patch("app.controllers.authcontroller.check_password_hash")
    @patch("app.controllers.authcontroller.Participant")
    def test_login_incorrect_password(self, mock_participant, mock_check_password):
        """Prueba: Login con contraseña incorrecta"""
        mock_participant.query.filter_by.return_value.first.return_value = self.mock_user
        mock_check_password.return_value = False

        response, status = self.auth_controller.login(self.valid_login_data)

        self.assertEqual(status, 401)
        self.assertEqual(response["msg"], "Contraseña incorrecta")
        mock_check_password.assert_called_once_with(self.mock_user.password, self.valid_login_data["password"])

    @patch("app.controllers.authcontroller.check_password_hash")
    @patch("app.controllers.authcontroller.Participant")
    def test_login_success_without_responsible(self, mock_participant, mock_check_password):
        """Prueba: Login exitoso sin responsable asignado"""
        mock_participant.query.filter_by.return_value.first.return_value = self.mock_user
        mock_check_password.return_value = True

        response, status = self.auth_controller.login(self.valid_login_data)

        self.assertEqual(status, 200)
        self.assertEqual(response["msg"], "Login exitoso")
        
        # Verificar datos del usuario en la respuesta
        user_data = response["data"]
        self.assertEqual(user_data["id"], self.mock_user.id)
        self.assertEqual(user_data["external_id"], self.mock_user.external_id)
        self.assertEqual(user_data["name"], self.mock_user.name)
        self.assertEqual(user_data["email"], self.mock_user.email)
        self.assertEqual(user_data["role"], self.mock_user.role)
        
        # Verificar que los datos del responsable sean None
        self.assertIsNone(user_data["nombreResponsable"])
        self.assertIsNone(user_data["dniResponsable"])
        self.assertIsNone(user_data["telefonoResponsable"])

    @patch("app.controllers.authcontroller.check_password_hash")
    @patch("app.controllers.authcontroller.Participant")
    def test_login_success_with_responsible(self, mock_participant, mock_check_password):
        """Prueba: Login exitoso con responsable asignado"""
        # Configurar usuario con responsable
        self.mock_user.responsibles = [self.mock_responsible]
        mock_participant.query.filter_by.return_value.first.return_value = self.mock_user
        mock_check_password.return_value = True

        response, status = self.auth_controller.login(self.valid_login_data)

        self.assertEqual(status, 200)
        self.assertEqual(response["msg"], "Login exitoso")
        
        # Verificar datos del usuario en la respuesta
        user_data = response["data"]
        self.assertEqual(user_data["id"], self.mock_user.id)
        self.assertEqual(user_data["name"], self.mock_user.name)
        
        # Verificar que los datos del responsable estén presentes
        self.assertEqual(user_data["nombreResponsable"], self.mock_responsible.name)
        self.assertEqual(user_data["dniResponsable"], self.mock_responsible.dni)
        self.assertEqual(user_data["telefonoResponsable"], self.mock_responsible.phone)

    @patch("app.controllers.authcontroller.check_password_hash")
    @patch("app.controllers.authcontroller.Participant")
    def test_login_case_insensitive_email(self, mock_participant, mock_check_password):
        """Prueba: Login con email en mayúsculas/minúsculas"""
        mock_participant.query.filter_by.return_value.first.return_value = self.mock_user
        mock_check_password.return_value = True

        # Probar con email en mayúsculas
        login_data = self.valid_login_data.copy()
        login_data["email"] = "JUAN@UNL.EDU.EC"

        response, status = self.auth_controller.login(login_data)

        self.assertEqual(status, 200)
        self.assertEqual(response["msg"], "Login exitoso")
        
        # Verificar que se buscó con el email exacto (en minúsculas)
        mock_participant.query.filter_by.assert_called_with(email="JUAN@UNL.EDU.EC")


if __name__ == "__main__":
    unittest.main(verbosity=2)