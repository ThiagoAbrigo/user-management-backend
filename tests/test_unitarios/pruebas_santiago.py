import unittest
from unittest.mock import patch, MagicMock
from app.controllers.assessment_controller import AssessmentController


class TestAssessmentController(unittest.TestCase):
    # comando para ejecutar las pruebas
    # python -m unittest tests.pruebas_santiago -v

    def setUp(self):
        self.controller = AssessmentController()

    @patch("app.controllers.assessment_controller.db.session")
    @patch("app.controllers.assessment_controller.log_activity")
    @patch("app.controllers.assessment_controller.Participant")
    def test_register_success(self, mock_participant, mock_log_activity, mock_session):
        fake_participant = MagicMock()
        fake_participant.id = 1
        fake_participant.firstName = "Carlos"
        fake_participant.lastName = "Lopez"
        fake_participant.external_id = "abc123"

        mock_participant.query.filter_by.return_value.first.return_value = (
            fake_participant
        )

        data = {
            "participant_external_id": "abc123",
            "weight": 70,  # valor válido
            "height": 1.75,
            "waistPerimeter": 0.8,
            "wingspan": 1.7,
            "date": "2025-01-05",
        }

        result = self.controller.register(data)

        print(result["msg"])
        self.assertEqual(result["code"], 200)
        self.assertEqual(result["status"], "ok")
        self.assertIn("bmi", result["data"])

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_log_activity.assert_called_once()

    @patch("app.controllers.assessment_controller.db.session")
    @patch("app.controllers.assessment_controller.log_activity")
    @patch("app.controllers.assessment_controller.Participant")
    def test_register_negative_weight(
        self, mock_participant, mock_log_activity, mock_session
    ):
        fake_participant = MagicMock()
        fake_participant.id = 1
        fake_participant.firstName = "Carlos"
        fake_participant.lastName = "Lopez"
        fake_participant.external_id = "abc123"

        mock_participant.query.filter_by.return_value.first.return_value = (
            fake_participant
        )

        data = {
            "participant_external_id": "abc123",
            "weight": -80,  # valor inválido
            "height": -1.76,
            "waistPerimeter": 0.1,  # numérico pero no obligatorio
            "armPerimeter": -1,  # inválido
            "calfPerimeter": None,  # permitido
            "date": None,
        }

        result = self.controller.register(data)

        self.assertEqual(result["code"], 400)
        self.assertEqual(result["status"], "error")
        self.assertIn("weight", result["errors"])
        self.assertIn("armPerimeter", result["errors"])
        self.assertIn("date", result["errors"])
        print(result["errors"]["weight"])

    @patch("app.controllers.assessment_controller.db.session")
    @patch("app.controllers.assessment_controller.log_activity")
    @patch("app.controllers.assessment_controller.Participant")
    def test_register_validate_all_fields(
        self, mock_participant, mock_log_activity, mock_session
    ):
        fake_participant = MagicMock()
        fake_participant.id = 1
        fake_participant.firstName = "Carlos"
        fake_participant.lastName = "Lopez"
        fake_participant.external_id = "abc123"
        mock_participant.query.filter_by.return_value.first.return_value = (
            fake_participant
        )

        data = {
            "participant_external_id": None,  # obligatorio faltante
            "weight": -5,  # inválido
            "height": 3.0,  # fuera de rango
            "waistPerimeter": 0.1,  # numérico pero no obligatorio
            "armPerimeter": -1,  # inválido
            "legPerimeter": 5.0,  # fuera de rango
            "calfPerimeter": None,  # permitido
            "date": None,  # obligatorio faltante
        }

        result = self.controller.register(data)

        self.assertEqual(result["code"], 400)
        self.assertEqual(result["status"], "error")
        self.assertIn("participant_external_id", result["errors"])
        self.assertIn("weight", result["errors"])
        self.assertIn("height", result["errors"])
        self.assertIn("armPerimeter", result["errors"])
        self.assertIn("date", result["errors"])

        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()
        mock_log_activity.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
