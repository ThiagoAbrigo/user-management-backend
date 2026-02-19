import unittest
from unittest.mock import patch, MagicMock
from app.controllers.evaluation_controller import EvaluationController


class TestEvaluationController(unittest.TestCase):

    def setUp(self):
        self.controller = EvaluationController()

    # TC-02: Registro de Test - Test creado correctamente
    @patch("app.controllers.evaluation_controller.db.session")
    @patch("app.controllers.evaluation_controller.TestExercise")
    @patch("app.controllers.evaluation_controller.Test")
    @patch("app.controllers.evaluation_controller.validate_exercises")
    @patch("app.controllers.evaluation_controller.validate_test_fields")
    @patch("app.controllers.evaluation_controller.validate_register_input")
    def test_tc_02_registro_test_exitoso(
        self,
        mock_validate_register,
        mock_validate_test_fields,
        mock_validate_exercises,
        mock_test,
        mock_test_exercise,
        mock_session
    ):

        # Validaciones no devuelven errores
        mock_validate_register.return_value = {}
        mock_validate_test_fields.return_value = {}
        mock_validate_exercises.return_value = {}

        fake_test = MagicMock()
        fake_test.id = 1
        fake_test.external_id = "test-123"
        fake_test.name = "test de hipertrofia"
        fake_test.frequency_months = 3
        fake_test.description = "Primer test de hipertrofia"

        mock_test.return_value = fake_test

        data = {
            "name": "Test de hipertrofia",
            "description": "Primer test de hipertrofia",
            "frequency_months": 3,
            "exercises": [
                {"name": "Press Banca", "unit": "repeticiones"},
            ],
        }

        result = self.controller.register(data)

        self.assertEqual(result["code"], 200)
        self.assertEqual(result["status"], "ok")
        self.assertIn("test_external_id", result["data"])

        mock_session.add.assert_called()
        mock_session.commit.assert_called_once()


    # TC-03: Registro de Test - Falla por ejercicios vacíos
    @patch("app.controllers.evaluation_controller.db.session")
    @patch("app.controllers.evaluation_controller.Test")
    def test_tc_03_registro_test_sin_ejercicios(
        self, mock_test, mock_session
    ):
        # ✅ Mockear que no existe un test con ese nombre
        mock_test.query.filter_by.return_value.first.return_value = None

        data = {
            "name": "Test sin ejercicios",
            "description": "Test inválido",
            "frequency_months": 3,
            "exercises": [
                {"name": "", "unit": ""}
            ],
        }

        result = self.controller.register(data)

        print(f"\n=== TC-03 RESULT ===")
        print(f"Code: {result.get('code')}")
        print(f"Status: {result.get('status')}")
        print(f"Msg: {result.get('msg')}")
        print(f"Validation Errors: {result.get('data', {}).get('validation_errors')}")
        print("===================\n")

        self.assertEqual(result["code"], 400)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["msg"], "Error de validación")
        
        # ✅ Verificar los errores específicos de los ejercicios
        validation_errors = result.get("data", {}).get("validation_errors", {})
        
        # El controlador valida cada ejercicio individualmente
        self.assertIn("exercises[0].name", validation_errors)
        self.assertIn("exercises[0].unit", validation_errors)
        
        # Verificar mensajes de error específicos
        self.assertEqual(validation_errors["exercises[0].name"], "Campo requerido")
        self.assertEqual(validation_errors["exercises[0].unit"], "Campo requerido")

        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()