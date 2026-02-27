import unittest
from unittest.mock import patch, MagicMock
from app.controllers.usercontroller import UserController


class UpdateControllerUser(unittest.TestCase):

    def setUp(self):
        self.controller = UserController()

        # Usuario mock existente
        self.mock_user = MagicMock()
        self.mock_user.id = 1
        self.mock_user.external_id = "ABC123"
        self.mock_user.name = "Juan"
        self.mock_user.estate = "UNIVERSITARIO"
        self.mock_user.age = 25
        self.mock_user.dni = "1234567890"
        self.mock_user.email = "juan@unl.edu.ec"
        self.mock_user.address = "Loja"

        self.valid_data = {
            "name": "Juan Updated",
            "estate": "UNIVERSITARIO",
            "age": "26",
            "dni": "1234567890",
            "email": "juan@unl.edu.ec",
            "address": "Quito"
        }

    # =====================================
    # ACTUALIZACIÓN EXITOSA
    # =====================================
    @patch("app.controllers.usercontroller.db")
    @patch("app.controllers.usercontroller.Responsible")
    @patch("app.controllers.usercontroller.Participant")
    def test_update_success(
        self, mock_participant, mock_responsible, mock_db
    ):

        mock_participant.query.filter_by.return_value.first.return_value = self.mock_user

        mock_participant.query.filter.return_value.first.return_value = None
        mock_responsible.query.filter_by.return_value.first.return_value = None
        mock_responsible.query.filter.return_value.first.return_value = None

        response, status = self.controller.update_user("ABC123", self.valid_data)

        self.assertEqual(status, 200)
        self.assertEqual(response["msg"], "Usuario actualizado correctamente")
        mock_db.session.commit.assert_called_once()

    # =====================================
    # CAMPOS VACÍOS
    # =====================================
    @patch("app.controllers.usercontroller.Responsible")
    @patch("app.controllers.usercontroller.Participant")
    def test_update_empty_fields(self, mock_participant, mock_responsible):

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

        response, status = self.controller.update_user("ABC123", empty_data)

        self.assertEqual(status, 400)
        self.assertIn("errors", response)

    # =====================================
    # CÉDULA YA REGISTRADA
    # =====================================
    @patch("app.controllers.usercontroller.Responsible")
    @patch("app.controllers.usercontroller.Participant")
    def test_update_duplicate_dni(
        self, mock_participant, mock_responsible
    ):

        mock_participant.query.filter_by.return_value.first.return_value = self.mock_user

        mock_participant.query.filter.return_value.first.return_value = MagicMock()

        data = self.valid_data.copy()
        data["dni"] = "9999999999"

        response, status = self.controller.update_user("ABC123", data)

        self.assertEqual(status, 400)
        self.assertIn("dni", response["errors"])

if __name__ == "__main__":
    unittest.main(verbosity=2)