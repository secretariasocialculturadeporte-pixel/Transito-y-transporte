# api_client.py
# This file simulates a client for a backend API.
# It holds the business logic and an in-memory "database" for the prototype.

import asyncio
import datetime
import random
from typing import Dict, Any, Optional, List

from pydantic import ValidationError

# Assuming models and app_data are in the root directory
import models
from app_data import _t

# --- Custom Exception for API Errors ---

class APIError(Exception):
    """Custom exception for API-related errors."""
    def __init__(self, message: str, status_code: int = 500, detail: Any = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.detail = detail

# --- The Simulated API Client ---

class ApiClient:
    """
    A simulated API client that mimics interactions with a real backend.
    """
    def __init__(self):
        self._session_token: Optional[str] = None
        self._users: Dict[str, models.UserInDB] = {}
        self._fines: Dict[str, List[models.FineBase]] = {}
        self._active_tramites: Dict[str, List[models.TramiteActivo]] = {}
        self._load_initial_data()

    async def _simulate_network(self, delay: float = 0.5):
        """Simulates network latency."""
        await asyncio.sleep(delay * random.uniform(0.5, 1.5))

    def _generate_fake_token(self, username: str) -> str:
        """Generates a simple fake token."""
        return f"fake-token-for-{username}-{datetime.datetime.now().timestamp()}"

    def _load_initial_data(self):
        """Loads sample data into the in-memory database."""
        # Create a sample citizen user
        citizen_user = models.UserInDB(
            user_id_sim=101,
            username="ciudadano_test",
            password="test", # In a real app, this MUST be hashed
            role="Ciudadano",
            dept="05",
            mun="05001",
            status="Active",
            full_name="Juan Pérez",
            email="juan.perez@email.com",
            created_at=datetime.datetime.now(datetime.timezone.utc),
            soat_vigente=True,
            tecno_vigente=False,
            impuesto_pago=True,
            paz_salvo_multas=False,
            estar_inscrito_runt=True,
            examen_medico_aprobado=True,
            curso_cea_aprobado=False,
        )
        self._users[citizen_user.username] = citizen_user

        # Create sample fines for the citizen
        self._fines[citizen_user.username] = [
            models.FineBase(
                id="C0MP001",
                date=datetime.date(2023, 10, 20),
                codigo_infraccion="C29",
                description="Conducir a velocidad superior a la máxima permitida.",
                value=980000,
                status="Pendiente"
            ),
            models.FineBase(
                id="C0MP002",
                date=datetime.date(2023, 11, 5),
                codigo_infraccion="D04",
                description="No detenerse ante una luz roja de semáforo.",
                value=1100000,
                status="Pagado",
                paid_date=datetime.date(2023, 11, 15)
            )
        ]

        # Create a sample admin user
        admin_user = models.UserInDB(
            user_id_sim=202,
            username="admin_test",
            password="admin",
            role="Admin Municipal",
            dept="76",
            mun="76001",
            status="Active",
            full_name="Ana García",
            email="ana.garcia@email.com",
            created_at=datetime.datetime.now(datetime.timezone.utc)
        )
        self._users[admin_user.username] = admin_user
        print(f"Initial data loaded. Users: {list(self._users.keys())}")


    async def login(self, username: str, password: str) -> models.LoginResponseData:
        """
        Simulates a user login process.
        """
        await self._simulate_network()

        user = self._users.get(username)

        if not user:
            raise APIError(_t("error.user_not_found", default="User not found."), 404)

        if user.password != password:
            # In a real app, use secure password comparison (e.g., hashing)
            raise APIError(_t("pw_change_fail_old_mismatch", default="Incorrect password."), 401)

        if user.status != "Active":
            raise APIError(_t("error.user_inactive", default="User account is inactive."), 403)

        # Update last login time
        user.last_login = datetime.datetime.now(datetime.timezone.utc)

        # Generate and store a session token
        self._session_token = self._generate_fake_token(username)

        # Prepare user details for the response
        user_detail = models.UserDetail(
            **user.dict(),
            paz_salvo_multas=all(f.status == "Pagado" for f in self._fines.get(username, []))
        )

        login_data = models.LoginResponseData(
            access_token=self._session_token,
            user_info=user_detail
        )

        return login_data

    async def get_my_fines(self) -> List[models.FineUIDetail]:
        """
        Retrieves the fines for the currently logged-in user and calculates UI details.
        """
        await self._simulate_network()

        # Determine current user from token
        if self._session_token and "ciudadano_test" in self._session_token:
            username = "ciudadano_test"
        else: # For now, only the test citizen has fines
            return []

        raw_fines = self._fines.get(username, [])
        ui_fines = []

        for fine in raw_fines:
            # Simulate business logic for calculating discounts, etc.
            days_since_fine = (datetime.date.today() - fine.date).days
            descuento_aplicable = (fine.status == "Pendiente" and days_since_fine <= 5)

            valor_con_descuento = fine.value // 2 if descuento_aplicable else fine.value

            ui_fines.append(
                models.FineUIDetail(
                    **fine.dict(),
                    puntos=3, # Dummy value
                    descuento_aplicable=descuento_aplicable,
                    valor_con_descuento=valor_con_descuento,
                    base_value_formatted=f"${fine.value:,}",
                    final_value_formatted=f"${valor_con_descuento:,}{'*' if descuento_aplicable else ''}",
                    fine_info_tooltip=f"{fine.codigo_infraccion}: {fine.description}"
                )
            )
        return ui_fines

    async def get_user_details(self, username: Optional[str] = None) -> models.UserDetail:
        """
        Gets the full details for a user.
        If username is None, it assumes the currently logged-in user.
        """
        await self._simulate_network()

        if username is None:
            # In a real app, we would decode the token to get the user
            if self._session_token and "ciudadano_test" in self._session_token:
                 username = "ciudadano_test"
            elif self._session_token and "admin_test" in self._session_token:
                 username = "admin_test"
            else:
                raise APIError(_t("error.unauthorized"), 401)

        user = self._users.get(username)
        if not user:
            raise APIError(_t("error.user_not_found"), 404)

        user_detail = models.UserDetail(
            **user.dict(),
            paz_salvo_multas=all(f.status == "Pagado" for f in self._fines.get(username, []))
        )
        return user_detail


    async def change_my_password(self, payload: Dict) -> bool:
        """
        Changes the password for the currently logged-in user.
        """
        await self._simulate_network(1.0)

        # Determine current user from token
        if self._session_token and "ciudadano_test" in self._session_token:
            username = "ciudadano_test"
        elif self._session_token and "admin_test" in self._session_token:
            username = "admin_test"
        else:
            raise APIError(_t("error.unauthorized"), 401)

        user = self._users.get(username)
        if not user:
            raise APIError(_t("error.user_not_found"), 404)

        try:
            data = models.PasswordChangeData.parse_obj(payload)
        except ValidationError as e:
            raise APIError(_t("error.validation_failed_simple"), 422, detail=e.errors())

        if user.password != data.old_password:
            raise APIError(_t("pw_change_fail_old_mismatch"), 400)

        # Update password
        user.password = data.new_password
        user.last_modified = datetime.datetime.now(datetime.timezone.utc)

        print(f"Password changed successfully for user '{username}'")
        return True
