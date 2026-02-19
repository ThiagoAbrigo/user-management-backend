"""
Servicio de sincronización con el microservicio de usuarios Java.
Maneja todas las comunicaciones con la API externa de personas.
"""
import requests
from app.config.config import Config


class JavaSyncService:
    """Sincroniza datos con el microservicio Java de usuarios."""

    def __init__(self):
        self.base_url = Config.PERSON_API_URL
        self.timeout = 5

    def _get_headers(self, token=None):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = token if token.startswith("Bearer") else f"Bearer {token}"
        return headers

    def _map_type_to_java(self, python_type):
        """Mapea tipos de usuario de Python a Java."""
        mapping = {
            "ESTUDIANTE": "ESTUDIANTES",
            "DOCENTE": "DOCENTES",
            "ADMINISTRATIVO": "ADMINISTRATIVOS",
            "TRABAJADOR": "TRABAJADORES",
            "EXTERNO": "EXTERNOS",
            "PASANTE": "EXTERNOS",
            "PARTICIPANTE": "EXTERNOS",
            "INICIACION": "EXTERNOS",
        }
        return mapping.get(python_type, "EXTERNOS")

    def _map_type_from_java(self, java_type):
        """Mapea tipos de usuario de Java a Python."""
        mapping = {
            "ESTUDIANTES": "ESTUDIANTE",
            "DOCENTES": "DOCENTE",
            "ADMINISTRATIVOS": "ADMINISTRATIVO",
            "TRABAJADORES": "TRABAJADOR",
            "EXTERNOS": "EXTERNO",
        }
        return mapping.get(java_type, "EXTERNO")

    def update_person_in_java(self, data, token):
        """
        Envía los datos actualizados a Java.
        Endpoint: POST /api/person/update
        Data esperada: first_name, last_name, external, type_identification, type_stament, direction, phono
        """
        try:
            url = f"{self.base_url}/update"
            response = requests.post(
                url,
                json=data,
                headers=self._get_headers(token),
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"⚠️ Java respondió error {response.status_code}: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error conectando con Java: {e}")
            return None

    def search_by_identification(self, identification, token):
        """Busca persona por cédula/identificación en el microservicio Java."""
        try:
            response = requests.get(
                f"{self.base_url}/search_identification/{identification}",
                headers=self._get_headers(token),
                timeout=self.timeout
            )

            if response.status_code == 200:
                java_data = response.json()
                
                if not java_data:
                    return {"found": False, "data": None}
                
                if isinstance(java_data, dict):
                    if not java_data.get("identification") and not java_data.get("id") and not java_data.get("external"):
                        return {"found": False, "data": None}
                
                return {
                    "found": True,
                    "data": self._map_person_from_java(java_data)
                }
            elif response.status_code == 404:
                return {"found": False, "data": None}
            else:
                return {"found": False, "error": "Error al buscar en Java"}

        except requests.exceptions.RequestException as e:
            print(f"[JavaSync] Error conexión search_by_identification: {e}")
            return {"found": False, "error": str(e)}

    def search_by_external(self, external_id, token):
        """Busca persona por external_id en el microservicio Java."""
        try:
            response = requests.get(
                f"{self.base_url}/search/{external_id}",
                headers=self._get_headers(token),
                timeout=self.timeout
            )

            if response.status_code == 200:
                java_data = response.json()
                
                if not java_data:
                    return {"found": False, "data": None}
                
                if isinstance(java_data, dict):
                    if not java_data.get("identification") and not java_data.get("id") and not java_data.get("external"):
                        return {"found": False, "data": None}
                
                return {
                    "found": True,
                    "data": self._map_person_from_java(java_data)
                }
            elif response.status_code == 404:
                return {"found": False, "data": None}
            else:
                return {"found": False, "error": "Error al buscar en Java"}

        except requests.exceptions.RequestException as e:
            print(f"[JavaSync] Error conexión search_by_external: {e}")
            return {"found": False, "error": str(e)}

    def create_person(self, data, token):
        """Crea una persona en el microservicio Java (sin cuenta)."""
        try:
            java_payload = {
                "first_name": data.get("firstName"),
                "last_name": data.get("lastName"),
                "identification": data.get("dni"),
                "type_identification": data.get("type_identification", "CEDULA"),
                "type_stament": self._map_type_to_java(data.get("type", "EXTERNO")),
                "direction": data.get("address", ""),
                "phono": data.get("phone", ""),
            }

            response = requests.post(
                f"{self.base_url}/save",
                json=java_payload,
                headers=self._get_headers(token),
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "data": result.get("data", {}),
                    "message": result.get("message", "Persona creada en Java")
                }
            else:
                result = response.json() if response.text else {}
                return {
                    "success": False,
                    "error": result.get("message", "Error al crear en Java"),
                    "errors": result.get("errors", [])
                }

        except requests.exceptions.RequestException as e:
            print(f"[JavaSync] Error conexión create_person: {e}")
            return {"success": False, "error": str(e)}

    def create_person_with_account(self, data, token):
        """Crea una persona con cuenta en el microservicio Java."""
        try:
            java_payload = {
                "first_name": data.get("firstName"),
                "last_name": data.get("lastName"),
                "identification": data.get("dni"),
                "type_identification": data.get("type_identification", "CEDULA"),
                "type_stament": self._map_type_to_java(data.get("type", "EXTERNO")),
                "direction": data.get("address", ""),
                "phono": data.get("phone", ""),
                "email": data.get("email"),
                "password": data.get("password"),
            }

            response = requests.post(
                f"{self.base_url}/save-account",
                json=java_payload,
                headers=self._get_headers(token),
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "data": result.get("data", {}),
                    "message": result.get("message", "Persona con cuenta creada en Java")
                }
            else:
                result = response.json() if response.text else {}
                return {
                    "success": False,
                    "error": result.get("message", "Error al crear cuenta en Java"),
                    "errors": result.get("errors", [])
                }

        except requests.exceptions.RequestException as e:
            print(f"[JavaSync] Error conexión create_person_with_account: {e}")
            return {"success": False, "error": str(e)}

    def update_person(self, data, token):
        """Actualiza una persona en el microservicio Java."""
        try:
            java_payload = {
                "external": data.get("external_id"),
                "first_name": data.get("firstName"),
                "last_name": data.get("lastName"),
                "type_identification": data.get("type_identification", "CEDULA"),
                "type_stament": self._map_type_to_java(data.get("type", "EXTERNO")),
                "direction": data.get("address", ""),
                "phono": data.get("phone", ""),
            }

            response = requests.post(
                f"{self.base_url}/update",
                json=java_payload,
                headers=self._get_headers(token),
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "data": result.get("data", {}),
                    "message": result.get("message", "Persona actualizada en Java")
                }
            else:
                result = response.json() if response.text else {}
                return {
                    "success": False,
                    "error": result.get("message", "Error al actualizar en Java"),
                    "errors": result.get("errors", [])
                }

        except requests.exceptions.RequestException as e:
            print(f"[JavaSync] Error conexión update_person: {e}")
            return {"success": False, "error": str(e)}

    def change_state(self, external_id, token):
        """Cambia el estado (activa/desactiva) de una persona en Java."""
        try:
            response = requests.get(
                f"{self.base_url}/change_state/{external_id}",
                headers=self._get_headers(token),
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "data": result.get("data", {}),
                    "message": result.get("message", "Estado cambiado en Java")
                }
            elif response.status_code == 404:
                return {"success": False, "error": "Persona no encontrada en Java"}
            else:
                result = response.json() if response.text else {}
                return {
                    "success": False,
                    "error": result.get("message", "Error al cambiar estado en Java")
                }

        except requests.exceptions.RequestException as e:
            print(f"[JavaSync] Error conexión change_state: {e}")
            return {"success": False, "error": str(e)}

    def get_all_persons(self, token):
        """Obtiene todas las personas del microservicio Java."""
        try:
            response = requests.get(
                f"{self.base_url}/all_filter",
                headers=self._get_headers(token),
                timeout=self.timeout
            )

            if response.status_code == 200:
                java_list = response.json()
                return {
                    "success": True,
                    "data": [self._map_person_from_java(p) for p in java_list]
                }
            else:
                return {"success": False, "error": "Error al obtener personas de Java"}

        except requests.exceptions.RequestException as e:
            print(f"[JavaSync] Error conexión get_all_persons: {e}")
            return {"success": False, "error": str(e)}

    def _map_person_from_java(self, java_data):
        """Mapea datos de persona de Java a formato Python."""
        return {
            "external_id": java_data.get("external"),
            "firstName": java_data.get("first_name"),
            "lastName": java_data.get("last_name"),
            "dni": java_data.get("identification"),
            "type": self._map_type_from_java(java_data.get("type_stament", "")),
            "phone": java_data.get("phono"),
            "address": java_data.get("direction"),
            "email": java_data.get("email"),
            "type_identification": java_data.get("type_identification"),
        }


# Instancia global del servicio
java_sync = JavaSyncService()
