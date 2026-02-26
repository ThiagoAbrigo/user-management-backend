# comando para ejecutar las pruebas
# python -m unittest tests.pruebas_santiago -v
import unittest
from unittest.mock import patch, MagicMock
from app.controllers.usercontroller import UserController


class RegisterControllerUser(unittest.TestCase):

    def setUp(self):
        self.controller = UserController()

        self.valid_data = {
            "name": "Juan Perez",
            "estate": "UNIVERSITARIO",
            "age": "25",
            "dni": "1234567890",
            "email": "juan@unl.edu.ec",
            "password": "123456",
            "address": "Loja"
        }

    # ===============================
    # TEST CREACIÓN EXITOSA
    # ===============================
    @patch("app.controllers.usercontroller.db")
    @patch("app.controllers.usercontroller.Participant")
    @patch("app.controllers.usercontroller.Responsible")
    def test_create_user_success(
        self, mock_responsible, mock_participant, mock_db
    ):
        mock_participant.query.filter_by.return_value.first.return_value = None
        mock_responsible.query.filter_by.return_value.first.return_value = None

        mock_user_instance = MagicMock()
        mock_user_instance.id = 1
        mock_user_instance.external_id = "ABC123"

        mock_participant.return_value = mock_user_instance

        response, status = self.controller.create_user(self.valid_data)

        self.assertEqual(status, 201)
        self.assertEqual(response["msg"], "Usuario creado correctamente")
        mock_db.session.add.assert_called()
        mock_db.session.commit.assert_called()

    # ===============================
    # TEST CAMPOS OBLIGATORIOS
    # ===============================
    def test_missing_required_fields(self):
        invalid_data = {}

        response, status = self.controller.create_user(invalid_data)

        self.assertEqual(status, 400)
        self.assertIn("errors", response)
        self.assertIn("name", response["errors"])

    # ===============================
    # TEST EMAIL INVALIDO UNIVERSITARIO
    # ===============================
    @patch("app.controllers.usercontroller.Participant")
    @patch("app.controllers.usercontroller.Responsible")
    def test_invalid_university_email(
        self, mock_responsible, mock_participant
    ):
        data = self.valid_data.copy()
        data["email"] = "juan@gmail.com"

        mock_participant.query.filter_by.return_value.first.return_value = None
        mock_responsible.query.filter_by.return_value.first.return_value = None

        response, status = self.controller.create_user(data)

        self.assertEqual(status, 400)
        self.assertIn("email", response["errors"])

    # ===============================
    # TEST DNI DUPLICADO
    # ===============================
    @patch("app.controllers.usercontroller.Participant")
    @patch("app.controllers.usercontroller.Responsible")
    def test_duplicate_dni(
        self, mock_responsible, mock_participant
    ):
        mock_participant.query.filter_by.return_value.first.return_value = MagicMock()

        response, status = self.controller.create_user(self.valid_data)

        self.assertEqual(status, 400)
        self.assertIn("dni", response["errors"])


if __name__ == "__main__":
    unittest.main(verbosity=2)