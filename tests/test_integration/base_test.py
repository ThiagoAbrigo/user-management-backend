# tests/test_integration/base_test.py
import unittest
import requests


class BaseTestCase(unittest.TestCase):
    """Clase base para pruebas de integración con servidor real"""

    @classmethod
    def setUpClass(cls):
        """Configuración que se ejecuta una vez antes de todas las pruebas"""
        # URL base del servidor real
        cls.base_url = "http://127.0.0.1:5000/api"
        
        # Cliente HTTP para hacer peticiones al servidor real
        cls.client = requests.Session()
        
        # Headers por defecto
        cls.client.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def setUp(self):
        """Configuración antes de cada prueba"""
        # Asegurarnos de que la sesión está activa
        if not hasattr(self.__class__, 'client'):
            self.__class__.setUpClass()

    def tearDown(self):
        """Limpieza después de cada prueba"""
        pass

    @classmethod
    def tearDownClass(cls):
        """Limpieza después de todas las pruebas"""
        if hasattr(cls, 'client'):
            cls.client.close()

    # Métodos auxiliares para hacer peticiones
    def get(self, endpoint, **kwargs):
        """Hacer petición GET al servidor real"""
        url = f"{self.base_url}{endpoint}"
        print(f"\n📤 GET {url}")
        response = self.client.get(url, **kwargs)
        print(f"📥 Status: {response.status_code}")
        return response

    def post(self, endpoint, **kwargs):
        """Hacer petición POST al servidor real"""
        url = f"{self.base_url}{endpoint}"
        print(f"\n📤 POST {url}")
        if 'json' in kwargs:
            print(f"📦 Data: {kwargs['json']}")
        response = self.client.post(url, **kwargs)
        print(f"📥 Status: {response.status_code}")
        return response

    def put(self, endpoint, **kwargs):
        """Hacer petición PUT al servidor real"""
        url = f"{self.base_url}{endpoint}"
        print(f"\n📤 PUT {url}")
        if 'json' in kwargs:
            print(f"📦 Data: {kwargs['json']}")
        response = self.client.put(url, **kwargs)
        print(f"📥 Status: {response.status_code}")
        return response

    def delete(self, endpoint, **kwargs):
        """Hacer petición DELETE al servidor real"""
        url = f"{self.base_url}{endpoint}"
        print(f"\n📤 DELETE {url}")
        response = self.client.delete(url, **kwargs)
        print(f"📥 Status: {response.status_code}")
        return response