import uuid
from tests.test_integration.base_test import BaseTestCase


class TestDBHealth(BaseTestCase):
    #python -m unittest tests.test_integration.test_integration

    def test_db_connection_ok(self):
        response = self.client.get("/api/health/db")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["db"], "ok")

    def _login_and_get_token(self):
        payload = {"email": "dev@kallpa.com", "password": "xxxxx"}

        response = self.client.post("/api/auth/login", json=payload)

        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        return data["token"]

    def test_list_users_ok(self):
        token = self._login_and_get_token()

        response = self.client.get(
            "/api/users", headers={"Authorization": f"Bearer {token}"}
        )

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertEqual(data["status"], "ok")
        self.assertIn("data", data)

    def test_save_assessment_ok(self):
        token = self._login_and_get_token()

        payload = {
            "participant_external_id": "93bc799d-25ef-45dc-bc5e-3969c79378b2",
            "weight": 70,
            "height": 1.70,
            "date": "2026-01-31",
            "waistPerimeter": 80,
            "armPerimeter": 30,
            "legPerimeter": 50,
            "calfPerimeter": 35
        }

        response = self.client.post(
            "/api/save-assessment",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertEqual(data["status"], "ok")
        self.assertIn("data", data)
        self.assertIn("external_id", data["data"])
        self.assertIn("bmi", data["data"])
        self.assertIn("status", data["data"])

    # TEST EVALUATION

    def test_list_tests_ok(self):
        token = self._login_and_get_token()

        response = self.client.get(
            "/api/list-test",
            headers={"Authorization": f"Bearer {token}"}
        )

        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertEqual(data["status"], "ok")
        self.assertIsInstance(data["data"], list)

    def test_save_test_ok(self):
        token = self._login_and_get_token()

        payload = {
            "name": f"Test RESISTENCIA {uuid.uuid4().hex[:6]}",
            "frequency_months": 3,
            "description": "Evaluación de fuerza",
            "exercises": [
                {"name": "Sentadillas", "unit": "repeticiones"},
                {"name": "Flexiones", "unit": "repetiones"}
            ]
        }

        response = self.client.post(
            "/api/save-test",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        print(response.get_json()) 
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("test_external_id", data["data"])
    
    def test_update_test_ok(self):
        token = self._login_and_get_token()

        payload = {
            "external_id": "cf9d469f-1ff4-4391-9a70-7d4a4c06eb26",
            "name": "test fuerza actualizado",
            "frequency_months": 4,
            "description": "Actualizado",
            "exercises": [
                {"name": "Plancha", "unit": "segundos"}
            ]
        }

        response = self.client.put(
            "/api/update-test",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )

        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertEqual(data["status"], "ok")

    def test_delete_test_ok(self):
        token = self._login_and_get_token()

        test_external_id = "cf9d469f-1ff4-4391-9a70-7d4a4c06eb26"

        response = self.client.delete(
            f"/api/delete-test/{test_external_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertEqual(data["status"], "ok")