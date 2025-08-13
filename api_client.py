import httpx
from typing import Dict, Any, Optional, List

import models
from app_data import _t

# --- Custom Exception for API Errors ---
class APIError(Exception):
    def __init__(self, message: str, status_code: int = 500, detail: Any = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.detail = detail

# --- Real API Client ---
class ApiClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.http_client = httpx.AsyncClient(base_url=base_url)
        self._token: Optional[str] = None

    async def _request(self, method: str, url: str, **kwargs):
        headers = kwargs.pop("headers", {})
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        try:
            response = await self.http_client.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            # Try to parse the detail from the response, otherwise use the reason phrase
            detail = e.response.json().get("detail", e.response.reason_phrase)
            raise APIError(message=detail, status_code=e.response.status_code)
        except httpx.RequestError as e:
            # For connection errors, etc.
            raise APIError(message=f"Error de conexión: {e}", status_code=503)

    async def login(self, username: str, password: str) -> models.LoginResponseData:
        """
        Logs in a user by calling the backend's /token endpoint.
        """
        # FastAPI's OAuth2PasswordRequestForm expects form data
        data = {"username": username, "password": password}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        # We don't use self._request here because login is special (it gets the token)
        try:
            response_json = await self._request("POST", "/api/v1/auth/token", data=data, headers=headers)
            self._token = response_json.get("access_token")

            # After getting the token, we need to fetch the user's details
            user_details_json = await self._request("GET", "/api/v1/auth/users/me")

            # We need to adapt the backend User schema to the frontend's UserDetail model
            # This is a simplification; a more robust solution would be needed.
            user_info = models.UserDetail(
                **user_details_json,
                user_id_sim=user_details_json.get('id'), # Map id to user_id_sim
                paz_salvo_multas=False # This would require another backend call
            )

            return models.LoginResponseData(
                access_token=self._token,
                user_info=user_info
            )
        except APIError as e:
            # Re-raise with a more user-friendly message if desired
            if e.status_code == 401:
                raise APIError("Usuario o contraseña incorrectos.", 401)
            raise e

    # --- Placeholder methods for the rest of the API ---
    # These will be implemented as the backend endpoints are created.

    async def get_my_fines(self) -> List[models.FineUIDetail]:
        """Fetches fines for the currently logged-in user."""
        response_data = await self._request("GET", "/api/v1/users/me/fines")
        return [models.FineUIDetail(**fine) for fine in response_data]

    async def get_my_vehicles(self) -> List[models.VehicleBase]:
        """Fetches vehicles for the currently logged-in user."""
        response_data = await self._request("GET", "/api/v1/users/me/vehicles")
        return [models.VehicleBase(**vehicle) for vehicle in response_data]

    async def get_managed_users(self, entidad_id: int) -> List[models.UserInDB]:
        """Fetches all users managed by the admin for a specific transit entity."""
        response_data = await self._request("GET", f"/api/v1/entities/{entidad_id}/users")
        return [models.UserInDB(**user) for user in response_data]

    async def get_vehicles_by_entity(self, entidad_id: int) -> List[models.VehicleBase]:
        """Fetches all vehicles registered to a specific transit entity."""
        response_data = await self._request("GET", f"/api/v1/entities/{entidad_id}/vehicles")
        return [models.VehicleBase(**vehicle) for vehicle in response_data]

    async def get_fines_by_entity(self, entidad_id: int) -> List[models.FineUIDetail]:
        """Fetches all fines issued by a specific transit entity."""
        response_data = await self._request("GET", f"/api/v1/entities/{entidad_id}/fines")
        return [models.FineUIDetail(**fine) for fine in response_data]

    # ... and so on for all other methods
    # Each would be a call to self._request(...)

    def logout(self):
        self._token = None
        print("User logged out, token cleared.")

    async def send_chat_message(self, message: str, context: Optional[Dict] = None) -> Dict:
        """
        Sends a message to the chat API endpoint and gets a response.
        """
        payload = {"message": message, "context": context or {}}
        response_data = await self._request("POST", "/api/v1/chat/", json=payload)
        return response_data

    async def issue_new_fine(self, username: str, infraction_code: str, placa: str, date: Any, tipo: str):
        """
        Issues a new fine to a user.
        """
        payload = {
            "target_username": username,
            "infraction_code": infraction_code,
            "placa": placa,
            "date": date.isoformat(),
            "tipo": tipo
        }
        await self._request("POST", "/api/v1/fines/", json=payload)

    async def get_my_notification_preferences(self) -> Dict:
        """
        Fetches the current user's notification preferences.
        """
        return await self._request("GET", "/api/v1/users/me/notification-preferences")

    async def update_my_notification_preferences(self, prefs_data: Dict) -> Dict:
        """
        Updates the current user's notification preferences.
        """
        return await self._request("PUT", "/api/v1/users/me/notification-preferences", json=prefs_data)

    async def get_procedures(self) -> List[Dict]:
        """Fetches all available procedures."""
        return await self._request("GET", "/api/v1/procedures/")

    async def create_procedure(self, procedure_data: Dict) -> Dict:
        """Creates a new procedure type (admin only)."""
        return await self._request("POST", "/api/v1/procedures/", json=procedure_data)

    async def get_my_appointments(self) -> List[Dict]:
        """Fetches the current user's booked appointments."""
        return await self._request("GET", "/api/v1/appointments/me")

    async def book_appointment(self, appointment_data: Dict) -> Dict:
        """Books a new appointment for the current user."""
        return await self._request("POST", "/api/v1/appointments/", json=appointment_data)

    async def create_fine_checkout(self, fine_id: int) -> str:
        """
        Creates a checkout session for a fine and returns the redirect URL.
        """
        payload = {"fine_id": fine_id}
        response = await self._request("POST", "/api/v1/payments/create-fine-checkout-session", json=payload)
        return response.get("checkout_url")

    async def get_audit_logs(self) -> List[Dict]:
        """Fetches audit log entries (admin only)."""
        return await self._request("GET", "/api/v1/admin/audit-logs/")

    async def get_my_documents(self) -> List[Dict]:
        """Fetches the current user's uploaded documents."""
        return await self._request("GET", "/api/v1/documents/me")

    async def upload_document(self, file_path: str, document_type: str) -> Dict:
        """Uploads a document file for the current user."""
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f)}
            data = {"document_type": document_type}
            # httpx needs the content-type to be multipart/form-data, but it sets it automatically
            # when `files` are provided. We don't use json= here.
            return await self._request("POST", "/api/v1/documents/upload", data=data, files=files)
