import unittest
import requests
import json
import uuid
import random
import string
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000/api"

class TestAttendanceScenarios(unittest.TestCase):
    
    def setUp(self):
        self.headers = {"Content-Type": "application/json"}
        self.admin_email = "admin@kallpa.com"
        self.admin_password = "123456" 
        self.token = None
        self.created_participant_id = None
        self.created_schedule_id = None

    def _generate_numeric_string(self, length):
        return ''.join(random.choices(string.digits, k=length))

    def _get_auth_headers(self):
        if not self.token:
             payload = {"email": self.admin_email, "password": self.admin_password}
             resp = requests.post(f"{BASE_URL}/auth/login", json=payload)
             if resp.status_code == 200:
                 self.token = resp.json()["token"]
        
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }

    def _create_participant(self):
        """Helper to create a participant and return external_id"""
        unique_id = str(uuid.uuid4())[:8]
        dni = f"15{self._generate_numeric_string(8)}" # Different prefix
        payload = {
            "firstName": "Elias",
            "lastName": "Poma",
            "dni": dni,
            "age": 22,
            "program": "FUNCIONAL",
            "type": "ESTUDIANTE",
            "phone": "0991122334",
            "email": f"elias.{unique_id}@test.com",
            "address": "Calle Loja"
        }
        resp = requests.post(f"{BASE_URL}/save-participants", json=payload, headers=self._get_auth_headers())
        if resp.status_code in [200, 201]:
            return resp.json()["data"]["participant_external_id"]
        return None

    def test_tc_01_create_schedule(self):
        """TC-01: Crear Horario/Sesión"""
        unique_suffix = str(uuid.uuid4())[:4]
        payload = {
            "name": f"Sesión Test {unique_suffix}",
            "startTime": "08:00",
            "endTime": "10:00",
            "program": "FUNCIONAL",
            "maxSlots": 20,
            "description": "Sesión de prueba automatizada",
            "dayOfWeek": "MONDAY"
        }
        
        resp = requests.post(
            f"{BASE_URL}/attendance/v2/public/schedules", 
            json=payload, 
            headers=self._get_auth_headers()
        )
        
        self.assertIn(resp.status_code, [200, 201], f"Fallo al crear horario: {resp.text}")
        data = resp.json()
        self.assertIn("data", data)
        # Note: The response structure depends on the controller. Assuming it returns the created object or ID.
        print(f"TC-01: Horario creado -> {data}")
        
        # Save for cleanup or other tests if needed (though independent tests are better)
        if "external_id" in data.get("data", {}):
             self.__class__.created_schedule_id = data["data"]["external_id"]

    def test_tc_02_register_attendance(self):
        """TC-02: Registrar Asistencia de Participante"""
        day, start, end = self._get_random_time_slot()
        participant_payload = {
            "firstName": "Juan", "lastName": "Perez", "dni": f"11{self._generate_numeric_string(8)}",
            "age": 30, "program": "FUNCIONAL", "type": "ESTUDIANTE",
            "phone": "0991234567", "email": f"test.atte.{uuid.uuid4()}@mail.com", "address": "Loja"
        }
        part_resp = requests.post(f"{BASE_URL}/save-participants", json=participant_payload, headers=self._get_auth_headers())
        participant_id = part_resp.json()["data"]["participant_external_id"]

        # Retry logic for TC-02 schedule
        schedule_id = None
        for i in range(10):
            day, start, end = self._get_random_time_slot()
            schedule_payload = {
                "name": f"Sesión Asistencia {uuid.uuid4().hex[:4]}",
                "startTime": start,
                "endTime": end,
                "program": "FUNCIONAL",
                "maxSlots": 20,
                "dayOfWeek": day
            }
            schedule_resp = requests.post(f"{BASE_URL}/attendance/v2/public/schedules", json=schedule_payload, headers=self._get_auth_headers())
            if schedule_resp.status_code in [200, 201]:
                schedule_id = schedule_resp.json()["data"]["external_id"]
                break
        
        self.assertIsNotNone(schedule_id, "No se pudo crear horario para TC-02 por solapamientos")
        
        # 3. Register Attendance
        today = datetime.now().strftime("%Y-%m-%d")
        attendance_payload = {
            "participant_external_id": participant_id,
            "schedule_external_id": schedule_id,
            "date": today,
            "status": "present"
        }
        
        resp = requests.post(
            f"{BASE_URL}/attendance", 
            json=attendance_payload, 
            headers=self._get_auth_headers()
        )
        
        self.assertIn(resp.status_code, [200, 201], f"Fallo registro asistencia: {resp.text}")
        print(f"TC-02: Asistencia registrada -> {resp.json()}")

    def test_tc_03_attendance_history(self):
        """TC-03: Verificar Historial de Asistencia"""
        # 1. Create & Register (reuse logic)
        participant_id = self._create_participant()
        
        schedule_id = None
        for i in range(10):
            day, start, end = self._get_random_time_slot()
            schedule_payload = {
                "name": f"Sesión Historial {uuid.uuid4().hex[:4]}",
                "startTime": start,
                "endTime": end,
                "program": "FUNCIONAL",
                "maxSlots": 10,
                "dayOfWeek": day
            }
            schedule_resp = requests.post(f"{BASE_URL}/attendance/v2/public/schedules", json=schedule_payload, headers=self._get_auth_headers())
            if schedule_resp.status_code in [200, 201]:
                schedule_id = schedule_resp.json()["data"]["external_id"]
                break
        
        self.assertIsNotNone(schedule_id, "No se pudo crear horario para TC-03 por solapamientos")
        
        today = datetime.now().strftime("%Y-%m-%d")
        attendance_payload = {
            "participant_external_id": participant_id,
            "schedule_external_id": schedule_id,
            "date": today,
            "status": "present"
        }
        requests.post(f"{BASE_URL}/attendance", json=attendance_payload, headers=self._get_auth_headers())
        
        # 2. Get History
        params = {
            "participant_external_id": participant_id
        }
        resp = requests.get(f"{BASE_URL}/attendance/history", params=params, headers=self._get_auth_headers())
        
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(len(data.get("data", [])) > 0, "El historial debería tener registros")
        
        # Verify the record matches
        found = False
        for record in data["data"]:
            if record["participant"]["external_id"] == participant_id and record["schedule"]["external_id"] == schedule_id:
                found = True
                break
        
        self.assertTrue(found, "No se encontró el registro de asistencia en el historial")
        print("TC-03: Historial verificado correctamente")

    def test_tc_04_create_schedule_missing_fields(self):
        """TC-04: Crear Horario - Faltan campos (Negativo)"""
        # Missing startTime and endTime
        payload = {
            "name": "Sesión Incompleta",
            "program": "FUNCIONAL",
            "dayOfWeek": "MONDAY"
        }
        resp = requests.post(
            f"{BASE_URL}/attendance/v2/public/schedules", 
            json=payload, 
            headers=self._get_auth_headers()
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Faltan campos requeridos", resp.text)
        print("TC-04: Validación de campos faltantes correcta")

    def test_tc_05_create_schedule_invalid_program(self):
        """TC-05: Crear Horario - Programa Inválido (Negativo)"""
        payload = {
            "name": "Sesión Programa Malo",
            "startTime": "08:00",
            "endTime": "10:00",
            "program": "INVALIDO",
            "maxSlots": 20,
            "dayOfWeek": "MONDAY"
        }
        resp = requests.post(
            f"{BASE_URL}/attendance/v2/public/schedules", 
            json=payload, 
            headers=self._get_auth_headers()
        )
        self.assertEqual(resp.status_code, 400)
        # Validate message handling unicode response
        self.assertIn("Programa inv\\u00e1lido", resp.text)
        # Validate message handling unicode response
        self.assertIn("Programa inv\\u00e1lido", resp.text)
        print("TC-05: Validación de programa inválido correcta")

    def test_tc_06_create_schedule_invalid_time_format(self):
        """TC-06: Crear Horario - Formato de Hora Inválido (Negativo)"""
        payload = {
            "name": "Sesión Hora Mala",
            "startTime": "25:00", # Invalid hour
            "endTime": "10:00",
            "program": "FUNCIONAL",
            "maxSlots": 20,
            "dayOfWeek": "MONDAY"
        }
        resp = requests.post(f"{BASE_URL}/attendance/v2/public/schedules", json=payload, headers=self._get_auth_headers())
        if resp.status_code == 200:
             print("TC-06 FAILURE: El sistema aceptó hora 25:00")
        self.assertEqual(resp.status_code, 400, "Debería fallar con hora inválida")
        
    def test_tc_07_create_schedule_start_after_end(self):
        """TC-07: Crear Horario - Inicio después de Fin (Negativo)"""
        payload = {
            "name": "Sesión Tiempo Ilógico",
            "startTime": "10:00",
            "endTime": "09:00", # End before start
            "program": "FUNCIONAL",
            "maxSlots": 20,
            "dayOfWeek": "MONDAY"
        }
        resp = requests.post(f"{BASE_URL}/attendance/v2/public/schedules", json=payload, headers=self._get_auth_headers())
        if resp.status_code == 200:
             print("TC-07 FAILURE: El sistema aceptó fin antes de inicio")
        self.assertEqual(resp.status_code, 400, "Debería fallar si fin < inicio")

    def _generate_numeric_string(self, length):
        return ''.join(random.choices(string.digits, k=length))

    def _get_random_time_slot(self):
        """Genera un slot de tiempo aleatorio para evitar solapamientos en tests"""
        days = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
        day = random.choice(days)
        # Random start hour and MINUTE to minimize collisions
        start_h = random.randint(7, 21)
        start_m = random.randint(0, 59)
        
        # End time = Start + 1 hour (approx)
        end_h = start_h + 1
        return day, f"{start_h:02d}:{start_m:02d}", f"{end_h:02d}:{start_m:02d}"

    def test_tc_08_create_schedule_invalid_day(self):
        """TC-08: Crear Horario - Día Inválido (Negativo)"""
        payload = {
            "name": "Sesión Día Malo",
            "startTime": "08:00",
            "endTime": "10:00",
            "program": "FUNCIONAL",
            "maxSlots": 20,
            "dayOfWeek": "INVALIDDAY"
        }
        resp = requests.post(f"{BASE_URL}/attendance/v2/public/schedules", json=payload, headers=self._get_auth_headers())
        if resp.status_code == 200:
             print("TC-08 FAILURE: El sistema aceptó día inválido")
        self.assertEqual(resp.status_code, 400, "Debería fallar con día inválido")

    # ============= STRESS & SECURITY TESTS =============

    def test_tc_09_sql_injection_schedule_name(self):
        """TC-09: SQL Injection en nombre de sesión - Intento básico"""
        payload = {
            "name": "'; DROP TABLE schedules; --",
            "startTime": "08:00",
            "endTime": "10:00",
            "program": "FUNCIONAL",
            "maxSlots": 20,
            "dayOfWeek": "MONDAY"
        }
        resp = requests.post(f"{BASE_URL}/attendance/v2/public/schedules", json=payload, headers=self._get_auth_headers())
        # Ideally should sanitize, but definitely shouldn't crash (500)
        self.assertNotEqual(resp.status_code, 500, "SQL Injection causó error interno")
        print(f"TC-09: SQL Injection handled with status {resp.status_code}")

    def test_tc_11_negative_max_slots(self):
        """TC-11: Slots máximos negativos"""
        payload = {
            "name": "Negative Slots",
            "startTime": "08:00",
            "endTime": "10:00",
            "program": "FUNCIONAL",
            "maxSlots": -10,
            "dayOfWeek": "MONDAY"
        }
        resp = requests.post(f"{BASE_URL}/attendance/v2/public/schedules", 
                           json=payload, headers=self._get_auth_headers())
        self.assertEqual(resp.status_code, 400, "Should reject negative slots")

    def test_tc_21_expired_or_invalid_token(self):
        """TC-21: Token inválido o expirado"""
        payload = {
            "name": "Invalid Token Test",
            "startTime": "08:00",
            "endTime": "10:00",
            "program": "FUNCIONAL",
            "maxSlots": 20,
            "dayOfWeek": "MONDAY"
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer INVALID_TOKEN_12345"
        }
        # Note: If endpoint is public by design, this test might need adjustment or endpoint secured
        resp = requests.post(f"{BASE_URL}/attendance/v2/public/schedules", 
                           json=payload, headers=headers)
        
        # Checking if it accepts or rejects. If it's a "public" endpoint internally but we want it secured:
        self.assertIn(resp.status_code, [401, 403], "Endpoint debería requerir auth válida")

    def test_tc_24_invalid_date_formats(self):
        """TC-24: Formatos de fecha inválidos en asistencia"""
        participant_id = self._create_participant()
        schedule_id = self.__class__.created_schedule_id or self._create_schedule_helper()
        
        invalid_dates = ["2024-13-01", "not-a-date", "01/01/2024"]
        
        for date_val in invalid_dates:
            payload = {
                "participant_external_id": participant_id,
                "schedule_external_id": schedule_id,
                "date": date_val,
                "status": "present"
            }
            resp = requests.post(f"{BASE_URL}/attendance", json=payload, headers=self._get_auth_headers())
            self.assertEqual(resp.status_code, 400, f"Debería rechazar fecha {date_val}")

    def test_tc_01_create_schedule(self):
        """TC-01: Crear Horario/Sesión - Con reintento por solapamiento"""
        max_retries = 10
        for i in range(max_retries):
            day, start, end = self._get_random_time_slot()
            payload = {
                "name": f"Sesión Test {uuid.uuid4().hex[:4]}",
                "startTime": start,
                "endTime": end,
                "program": "FUNCIONAL",
                "maxSlots": 20,
                "dayOfWeek": day
            }
            resp = requests.post(f"{BASE_URL}/attendance/v2/public/schedules", json=payload, headers=self._get_auth_headers())
            if resp.status_code in [200, 201]:
                data = resp.json().get("data")
                self.__class__.created_schedule_id = data["external_id"]
                print(f"TC-01: Horario creado -> {resp.json()}")
                return
            
            # If overlap, retry
            if resp.status_code == 400 and "solapa" in resp.text:
                continue
            
            # If other error, fail
            self.fail(f"Fallo al crear horario: {resp.text}")
        
        self.fail(f"No se pudo crear horario tras {max_retries} intentos por solapamientos")
    def _create_schedule_helper(self):
        """Helper local para crear schedule con reintento"""
        for i in range(10):
            day, start, end = self._get_random_time_slot()
            payload = {
                "name": f"Helper Schedule {uuid.uuid4()}",
                "startTime": start,
                "endTime": end,
                "program": "FUNCIONAL",
                "maxSlots": 20,
                "dayOfWeek": day
            }
            resp = requests.post(f"{BASE_URL}/attendance/v2/public/schedules", json=payload, headers=self._get_auth_headers())
            if resp.status_code in [200, 201]:
                return resp.json()["data"]["external_id"]
        return None

    # ============= BUSINESS LOGIC TESTS =============

    def test_tc_18_duplicate_attendance_same_day(self):
        """TC-18: Registrar asistencia duplicada mismo día"""
        participant_id = self._create_participant()
        # Create fresh schedule to ensure clean state
        schedule_id = self._create_schedule_helper()
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Primera asistencia
        payload = {
            "participant_external_id": participant_id,
            "schedule_external_id": schedule_id,
            "date": today,
            "status": "present"
        }
        resp1 = requests.post(f"{BASE_URL}/attendance", json=payload, headers=self._get_auth_headers())
        self.assertEqual(resp1.status_code, 200, f"Primera asistencia falló: {resp1.text}")

        # Intentar duplicar
        resp2 = requests.post(f"{BASE_URL}/attendance", json=payload, headers=self._get_auth_headers())
        self.assertNotEqual(resp2.status_code, 200, "No debería permitir duplicados exactos")
        print(f"TC-18: Duplicate check -> {resp2.status_code}")

    def test_tc_19_overlapping_schedules(self):
        """TC-19: Crear horarios solapados"""
        # We need a schedule that SUCCEEDS first, so rely on helper or retry
        s1_id = None
        s1_payload = None
        for i in range(10):
            day, start, end = self._get_random_time_slot()
            payload = {
                "name": f"Overlap Base {uuid.uuid4()}",
                "startTime": start,
                "endTime": end,
                "program": "FUNCIONAL",
                "maxSlots": 20,
                "dayOfWeek": day
            }
            resp = requests.post(f"{BASE_URL}/attendance/v2/public/schedules", json=payload, headers=self._get_auth_headers())
            if resp.status_code in [200, 201]:
                s1_id = resp.json()["data"]["external_id"]
                s1_payload = payload
                break
        self.assertIsNotNone(s1_id, "No se pudo crear horario base para TC-19")

        # Now try to overlap it
        s2 = {
            "name": f"Overlap Conflict {uuid.uuid4()}",
            "startTime": s1_payload["startTime"], # Same times
            "endTime": s1_payload["endTime"],
            "program": "FUNCIONAL",
            "maxSlots": 20,
            "dayOfWeek": s1_payload["dayOfWeek"]
        }
        resp2 = requests.post(f"{BASE_URL}/attendance/v2/public/schedules", 
                             json=s2, headers=self._get_auth_headers())
        
        self.assertNotEqual(resp2.status_code, 200, "No debería permitir horarios solapados")

    def test_tc_26_exceed_max_slots(self):
        """TC-26: Exceder capacidad máxima de slots"""
        # Create tiny class with retries
        schedule_id = None
        for i in range(10):
            day, start, end = self._get_random_time_slot()
            s_data = {
                "name": f"Tiny Class {uuid.uuid4()}",
                "startTime": start,
                "endTime": end,
                "program": "FUNCIONAL",
                "maxSlots": 1,
                "dayOfWeek": day
            }
            resp = requests.post(f"{BASE_URL}/attendance/v2/public/schedules", 
                            json=s_data, headers=self._get_auth_headers())
            if resp.status_code in [200, 201]:
                schedule_id = resp.json()["data"]["external_id"]
                break
        self.assertIsNotNone(schedule_id, "No se pudo crear Tiny Class para TC-26")

        today = datetime.now().strftime("%Y-%m-%d")
        
        # Participant 1 (OK)
        p1 = self._create_participant()
        # ... rest of test
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Participant 1 (OK)
        p1 = self._create_participant()
        req1 = requests.post(f"{BASE_URL}/attendance", json={
            "participant_external_id": p1, "schedule_external_id": schedule_id, "date": today, "status": "present"
        }, headers=self._get_auth_headers())
        self.assertEqual(req1.status_code, 200, f"P1 failed: {req1.text}")

        # Participant 2 (Should Fail)
        p2 = self._create_participant()
        req2 = requests.post(f"{BASE_URL}/attendance", json={
            "participant_external_id": p2, "schedule_external_id": schedule_id, "date": today, "status": "present"
        }, headers=self._get_auth_headers())
        
        self.assertNotEqual(req2.status_code, 200, "Debería rechazar por cupo lleno")


if __name__ == "__main__":
    unittest.main(verbosity=2)
