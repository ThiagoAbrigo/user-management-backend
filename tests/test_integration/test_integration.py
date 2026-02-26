# tests/test_integration/test_integration.py
import uuid
import random
from tests.test_integration.base_test import BaseTestCase


class TestUserEndpoints(BaseTestCase):
    """Pruebas de integración para endpoints de usuarios y autenticación"""

    def setUp(self):
        """Configuración específica para pruebas de endpoints"""
        super().setUp()
        
        # Generar DNI de EXACTAMENTE 10 dígitos
        # Primero generamos 10 dígitos aleatorios
        self.valid_dni = ''.join([str(random.randint(0, 9)) for _ in range(10)])
        
        # Generar un identificador único para emails
        self.test_id = str(random.randint(10000, 99999))
        
        # Datos de prueba con valores válidos
        self.test_user = {
            "name": "Juan Perez",
            "estate": "UNIVERSITARIO",
            "age": 25,  # Enviar como entero
            "dni": self.valid_dni,  # DNI de 10 dígitos numéricos
            "email": f"juan.{self.test_id}@unl.edu.ec",  # Email único con dominio universitario
            "password": "123456",
            "address": "Loja"
        }
        
        print(f"\nID de prueba: {self.test_id}")
        print(f"Email: {self.test_user['email']}")
        print(f"DNI: {self.test_user['dni']} (10 dígitos) - Longitud: {len(self.test_user['dni'])}")

    def debug_response(self, response, message=""):
        """Método auxiliar para debuggear respuestas"""
        print(f"\n === DEBUG: {message} ===")
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        try:
            data = response.json()
            print(f"📦 Response data: {data}")
            return data
        except Exception as e:
            print(f"❌ Error parsing JSON: {e}")
            print(f"📦 Response text: {response.text}")
            return None

    # =====================================
    # HEALTH CHECK
    # =====================================

    def test_health_db_endpoint(self):
        """Prueba: Verificar que el endpoint de health funciona"""
        response = self.get("/health/db")
        data = self.debug_response(response, "Health check")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["db"], "ok")

    # =====================================
    # ENDPOINTS DE USUARIOS
    # =====================================

    def test_create_user_endpoint(self):
        """Prueba: POST /save-user - Crear usuario exitosamente"""
        print(f"\nProbando creación de usuario con DNI válido...")
        print(f"Longitud del DNI: {len(self.test_user['dni'])} dígitos")
        
        response = self.post("/save-user", json=self.test_user)
        data = self.debug_response(response, "Crear usuario")
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(data["msg"], "Usuario creado correctamente")
        self.assertIn("external_id", data)
        print(f"✅ Usuario creado con external_id: {data['external_id']}")

    def test_create_user_invalid_dni(self):
        """Prueba: POST /save-user - DNI inválido (debe dar error 400)"""
        print(f"\nProbando DNI inválido...")
        
        invalid_user = self.test_user.copy()
        invalid_user["dni"] = "12345"  # DNI con menos de 10 dígitos
        invalid_user["email"] = f"invalid.{self.test_id}@unl.edu.ec"
        
        print(f"DNI inválido: {invalid_user['dni']} (longitud: {len(invalid_user['dni'])})")
        
        response = self.post("/save-user", json=invalid_user)
        data = self.debug_response(response, "DNI inválido")
        
        self.assertEqual(response.status_code, 400)
        self.assertIn("errors", data)
        self.assertIn("dni", data["errors"])

    def test_create_user_duplicate_dni_endpoint(self):
        """Prueba: POST /save-user - DNI duplicado"""
        print(f"\nProbando DNI duplicado...")
        print(f"DNI original: {self.test_user['dni']} (longitud: {len(self.test_user['dni'])})")
        
        # Crear primer usuario
        response1 = self.post("/save-user", json=self.test_user)
        self.assertEqual(response1.status_code, 201)
        print(f"✅ Primer usuario creado")
        
        # Intentar crear segundo usuario con mismo DNI
        duplicate_data = {
            "name": "Otro Usuario",
            "estate": "UNIVERSITARIO",
            "age": 30,
            "dni": self.test_user["dni"],  # Mismo DNI (válido)
            "email": f"otro.{self.test_id}@unl.edu.ec",  # Email diferente
            "password": "123456",
            "address": "Quito"
        }
        
        print(f"Intentando crear usuario con mismo DNI: {duplicate_data['dni']}")
        response2 = self.post("/save-user", json=duplicate_data)
        data2 = self.debug_response(response2, "DNI duplicado")
        
        self.assertEqual(response2.status_code, 400)
        self.assertIn("errors", data2)
        self.assertIn("dni", data2["errors"])
        print(f"✅ Validación de DNI duplicado funcionó correctamente")

    def test_create_user_duplicate_email_endpoint(self):
        """Prueba: POST /save-user - Email duplicado"""
        print(f"\nProbando email duplicado...")
        print(f"Email original: {self.test_user['email']}")
        
        # Crear primer usuario
        response1 = self.post("/save-user", json=self.test_user)
        self.assertEqual(response1.status_code, 201)
        print(f"✅ Primer usuario creado")
        
        # Crear un DNI diferente válido para el segundo usuario
        second_dni = ''.join([str(random.randint(0, 9)) for _ in range(10)])
        
        # Intentar crear segundo usuario con mismo email
        duplicate_data = {
            "name": "Otro Usuario",
            "estate": "UNIVERSITARIO",
            "age": 30,
            "dni": second_dni,  # DNI diferente
            "email": self.test_user["email"],  # Mismo email
            "password": "123456",
            "address": "Quito"
        }
        
        print(f"Intentando crear usuario con mismo email: {duplicate_data['email']}")
        response2 = self.post("/save-user", json=duplicate_data)
        data2 = self.debug_response(response2, "Email duplicado")
        
        self.assertEqual(response2.status_code, 400)
        self.assertIn("errors", data2)
        self.assertIn("email", data2["errors"])
        print(f"✅ Validación de email duplicado funcionó correctamente")

    # =====================================
    # ENDPOINTS DE AUTENTICACIÓN
    # =====================================

    def test_login_endpoint_success(self):
        """Prueba: POST /auth/login - Login exitoso"""
        print(f"\nProbando login exitoso...")
        
        # Crear usuario
        create_response = self.post("/save-user", json=self.test_user)
        self.assertEqual(create_response.status_code, 201)
        print(f"✅ Usuario creado para login")
        
        # Login
        login_data = {
            "email": self.test_user["email"],
            "password": self.test_user["password"]
        }
        response = self.post("/auth/login", json=login_data)
        data = self.debug_response(response, "Login exitoso")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["msg"], "Login exitoso")
        self.assertIn("data", data)
        
        user_data = data["data"]
        self.assertEqual(user_data["email"], self.test_user["email"])
        self.assertEqual(user_data["name"], self.test_user["name"])
        print(f"✅ Login exitoso para: {user_data['name']}")

    def test_login_endpoint_wrong_password(self):
        """Prueba: POST /auth/login - Contraseña incorrecta"""
        print(f"\nProbando login con contraseña incorrecta...")
        
        # Crear usuario
        create_response = self.post("/save-user", json=self.test_user)
        self.assertEqual(create_response.status_code, 201)
        print(f"✅ Usuario creado para prueba de contraseña incorrecta")
        
        # Login con contraseña incorrecta
        login_data = {
            "email": self.test_user["email"],
            "password": "wrongpassword"
        }
        response = self.post("/auth/login", json=login_data)
        data = self.debug_response(response, "Contraseña incorrecta")
        
        self.assertEqual(response.status_code, 401)
        self.assertEqual(data["msg"], "Contraseña incorrecta")
        print(f"✅ Validación de contraseña incorrecta funcionó")


if __name__ == "__main__":
    import unittest
    unittest.main(verbosity=2)