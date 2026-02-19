import unittest
from unittest.mock import patch, MagicMock
from app.controllers.usercontroller import UserController
from app.controllers.auth_controller import AuthController

class TestUserController(unittest.TestCase):
  
    

    def setUp(self):
        # Instanciamos los controladores dentro de cada test 
        pass


    @patch("app.controllers.auth_controller.AuthService")
    def test_tc_01_login_success(self, mock_auth_service):
        """TC-01: Inicio de Sesión - Verifica ingreso exitoso con credenciales correctas"""
        mock_auth_service.return_value.login.return_value = ({"token": "valid_token"}, 200)
        
        auth_controller = AuthController()
        response, status_code = auth_controller.login({"email": "admin@kallpa.com", "password": "123456"})

        self.assertEqual(status_code, 200)
        self.assertEqual(response["token"], "valid_token")

    @patch("app.controllers.auth_controller.AuthService")
    def test_tc_02_login_failure(self, mock_auth_service):
        """TC-02: Inicio de Sesión - Verifica fallo con contraseña incorrecta"""
        mock_auth_service.return_value.login.return_value = ({"msg": "Credenciales inválidas"}, 401)
        
        auth_controller = AuthController()
        response, status_code = auth_controller.login({"email": "admin@kallpa.com", "password": "wrong"})

        self.assertEqual(status_code, 401)
        self.assertIn("msg", response)

    @patch("app.controllers.usercontroller.UserController._get_token")
    @patch("app.controllers.usercontroller.Participant")
    def test_tc_06_register_duplicate_dni(self, mock_participant, mock_get_token):
        """TC-06: Registrar Participante - Verifica validación de DNI duplicado"""
        mock_get_token.return_value = "Bearer mock_token"
        mock_participant.query.filter_by.return_value.first.return_value = MagicMock()
        
        data = {
            "firstName": "Ana",
            "lastName": "Loja",
            "dni": "1100000001",
            "age": 22,
            "address": "Calle Test",
            "phone": "0987654321",
            "email": "ana@test.com",
            "program": "FUNCIONAL",
            "type": "ESTUDIANTE"
        }
        
        controller = UserController()
        response = controller.create_participant(data)
        
        self.assertEqual(response["code"], 400)
        self.assertIn("dni", response["data"])
        self.assertEqual(response["data"]["dni"], "El DNI ya está registrado")

    @patch("app.controllers.usercontroller.UserController._get_token")
    @patch("app.controllers.usercontroller.Participant")
    def test_tc_07_register_empty_fields(self, mock_participant, mock_get_token):
        """TC-07: Registrar - Verifica validación cuando faltan campos requeridos"""
        mock_get_token.return_value = "Bearer mock_token"
        data = {}
        controller = UserController()
        response = controller.create_participant(data)
        
        self.assertEqual(response["code"], 400)
        self.assertIn("msg", response) 

    @patch("app.controllers.usercontroller.UserController._get_token")
    @patch("app.controllers.usercontroller.Participant")
    @patch("app.controllers.usercontroller.User")
    def test_tc_14_dni_invalid_validations(self, mock_user, mock_participant, mock_get_token):
        """TC-14, TC-15: Validaciones de DNI - Verifica longitud y ceros"""
        mock_get_token.return_value = "Bearer mock_token"
        mock_participant.query.filter_by.return_value.first.return_value = None
        
        scenarios = [
            ("12345", "DNI debe tener exactamente 10 dígitos"),
            ("0000000000", "DNI no puede ser solo ceros"),
            ("1234567890", "DNI no puede ser un número secuencial") 
        ]
        
        controller = UserController()
        for dni_val, expected_msg in scenarios:
            data = {
                "firstName": "Test",
                "lastName": "Dni",
                "dni": dni_val,
                "age": 25,
                "phone": "0991234567",
                "program": "FUNCIONAL",
                "type": "ESTUDIANTE"
            }
            response = controller.create_participant(data)
            self.assertEqual(response["code"], 400)
            self.assertIn(expected_msg, response["data"]["dni"])

    @patch("app.controllers.usercontroller.db.session")
    @patch("app.controllers.usercontroller.UserController._get_token")
    @patch("app.controllers.usercontroller.Participant")
    def test_tc_16_phone_validations(self, mock_participant, mock_get_token, mock_session):
        """TC-16, TC-21, TC-24: Validaciones de Teléfono - Verifica formato inválido"""
        mock_get_token.return_value = "Bearer mock_token"
        mock_participant.query.filter_by.return_value.first.return_value = None
        
        scenarios = [
            ("1234567890", "Teléfono debe iniciar con 0"),
            ("098abc1234", "Teléfono debe contener solo números"),
            ("0123456789", "Teléfono no puede ser un número secuencial")
        ]
        
        controller = UserController()
        for phone_val, expected_msg in scenarios:
            data = {
                "firstName": "Test",
                "lastName": "Phone",
                "dni": "1100000005",
                "age": 25,
                "phone": phone_val,
                "program": "FUNCIONAL",
                "type": "ESTUDIANTE"
            }
            response = controller.create_participant(data)
            self.assertEqual(response["code"], 400, f"Failed for phone: {phone_val}")
            self.assertIn(expected_msg, response["data"]["phone"])

    @patch("app.controllers.usercontroller.db.session")
    @patch("app.controllers.usercontroller.UserController._get_token")
    @patch("app.controllers.usercontroller.Participant")
    def test_tc_18_program_age_restrictions(self, mock_participant, mock_get_token, mock_session):
        """TC-18: Menor de 16 intentando inscribirse a FUNCIONAL - Verifica restricción de edad"""
        mock_get_token.return_value = "Bearer mock_token"
        mock_participant.query.filter_by.return_value.first.return_value = None
        
        data = {
            "firstName": "Menor",
            "lastName": "Funcional",
            "dni": "1100000006",
            "age": 14,
            "phone": "0991234567",
            "program": "FUNCIONAL",
            "type": "ESTUDIANTE"
        }
        
        controller = UserController()
        response = controller.create_participant(data)
        self.assertEqual(response["code"], 400)
        self.assertIn("Menores de 16 años solo pueden inscribirse a INICIACIÓN", response["data"]["program"])

    @patch("app.controllers.usercontroller.UserController._get_token")
    @patch("app.controllers.usercontroller.java_sync")
    def test_tc_12_search_participant_java(self, mock_java_sync, mock_get_token):
        """TC-12: Buscar Participante en Java - Verifica búsqueda exitosa"""
        mock_get_token.return_value = "Bearer mock_token"
        
        mock_java_sync.search_by_identification.return_value = {
            "found": True, 
            "data": {"name": "Found User"}
        }
        
        controller = UserController()
        response = controller.search_in_java("1100000007")
        
        self.assertEqual(response["code"], 200)
        self.assertEqual(response["msg"], "Participante encontrado en Java")

    @patch("app.controllers.usercontroller.UserController._get_token")
    @patch("app.controllers.usercontroller.java_sync")
    def test_tc_13_search_participant_not_found(self, mock_java_sync, mock_get_token):
        """TC-13: Buscar Participante en Java - Verifica usuario no encontrado"""
        mock_get_token.return_value = "Bearer mock_token"
        
        mock_java_sync.search_by_identification.return_value = {"found": False}
        
        controller = UserController()
        response = controller.search_in_java("1100000008")
        
        self.assertEqual(response["code"], 404)
        self.assertEqual(response["msg"], "Participante no encontrado en Java")

if __name__ == "__main__":
    unittest.main()
