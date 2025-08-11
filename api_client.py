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
        self._vehicles: Dict[str, Dict[str, models.VehicleHojaDeVida]] = {} # {mun_code: {placa: Vehicle}}
        self._procedures: List[models.ProgramInfo] = []
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

        # Create sample vehicles for the citizen user in municipality 05001
        vehicle1 = models.VehicleHojaDeVida(
            placa="ABC-123",
            marca="Chevrolet",
            modelo="Spark GT",
            ano=2020,
            tipo="Automóvil",
            propietario_username="ciudadano_test",
            color="Rojo",
            cilindraje=1200,
            fecha_matricula=datetime.date(2020, 5, 10),
            soat_hasta=datetime.date(2025, 5, 10),
            tecno_hasta=datetime.date(2026, 5, 10),
            historial_revisiones=[
                models.RevisionHistorial(
                    fecha=datetime.date(2022, 6, 15),
                    taller="AutoExpress",
                    descripcion="Cambio de aceite y filtros.",
                    costo=150000
                )
            ]
        )

        vehicle2 = models.VehicleHojaDeVida(
            placa="XYZ-78D",
            marca="Yamaha",
            modelo="NMAX",
            ano=2022,
            tipo="Motocicleta",
            propietario_username="ciudadano_test",
            color="Negro",
            cilindraje=155,
            fecha_matricula=datetime.date(2022, 2, 20),
            soat_hasta=datetime.date(2025, 2, 20),
            # No tecno yet for new motorcycles
        )

        if "05001" not in self._vehicles:
            self._vehicles["05001"] = {}
        self._vehicles["05001"][vehicle1.placa] = vehicle1
        self._vehicles["05001"][vehicle2.placa] = vehicle2

        # Create sample available procedures/programs
        self._procedures = [
            models.ProgramInfo(id="P001", nombre="Licencia de Conducción Primera Vez", categoria="Licencias", descripcion="Obtén tu licencia de conducción para carro o moto."),
            models.ProgramInfo(id="P002", nombre="Renovación de Licencia", categoria="Licencias", descripcion="Renueva tu licencia de conducción antes de que expire."),
            models.ProgramInfo(id="T001", nombre="Traspaso de Propiedad", categoria="Trámites", descripcion="Realiza el traspaso de propiedad de tu vehículo."),
            models.ProgramInfo(id="C001", nombre="Campaña de Seguridad Vial", categoria="Campañas", descripcion="Participa en nuestras campañas para una movilidad más segura."),
        ]

        # Create sample active tramites for the citizen user
        self._active_tramites[citizen_user.username] = [
            models.TramiteActivo(
                id_tramite="T001-12345",
                nombre="Traspaso de Propiedad - ABC-123",
                estado="En Revisión de Documentos",
                fecha_inicio=datetime.date(2023, 11, 10)
            )
        ]

        print(f"Initial data loaded. Users: {list(self._users.keys())}, Vehicles: {len(self._vehicles.get('05001', {}))}")


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

    async def get_vehicles_by_municipality(self, mun_code: str) -> List[models.VehicleBase]:
        """
        Retrieves a list of basic vehicle info for a given municipality.
        """
        await self._simulate_network()

        vehicles_in_mun = self._vehicles.get(mun_code, {})

        # Return a list of VehicleBase models, not the full HojaDeVida
        return [models.VehicleBase.parse_obj(v) for v in vehicles_in_mun.values()]

    async def get_vehicle_details(self, placa: str) -> Optional[models.VehicleHojaDeVida]:
        """
        Retrieves the full details (Hoja de Vida) for a specific vehicle by its license plate.
        """
        await self._simulate_network()

        # Search for the vehicle across all municipalities
        for mun_vehicles in self._vehicles.values():
            if placa in mun_vehicles:
                return mun_vehicles[placa]

        return None

    async def get_my_active_tramites(self) -> List[models.TramiteActivo]:
        """
        Retrieves the active procedures for the currently logged-in user.
        """
        await self._simulate_network()

        # Determine current user from token
        if self._session_token and "ciudadano_test" in self._session_token:
            username = "ciudadano_test"
        else:
            return []

        return self._active_tramites.get(username, [])

    async def get_available_procedures(self) -> List[models.ProgramInfo]:
        """
        Retrieves all available procedures and programs.
        """
        await self._simulate_network()
        return self._procedures

    async def get_my_vehicles(self) -> List[models.VehicleBase]:
        """
        Retrieves a list of vehicles owned by the currently logged-in user.
        """
        await self._simulate_network()

        # Determine current user from token
        if self._session_token and "ciudadano_test" in self._session_token:
            username = "ciudadano_test"
        else:
            return []

        user_vehicles = []
        for mun_vehicles in self._vehicles.values():
            for vehicle in mun_vehicles.values():
                if vehicle.propietario_username == username:
                    user_vehicles.append(models.VehicleBase.parse_obj(vehicle))

        return user_vehicles

    async def update_my_vehicle_data(self, placa: str, revision: models.RevisionHistorial) -> models.VehicleHojaDeVida:
        """
        Updates a vehicle's data, for now, by adding a maintenance record.
        """
        await self._simulate_network()

        # Find the vehicle
        vehicle_to_update = None
        for mun_vehicles in self._vehicles.values():
            if placa in mun_vehicles:
                vehicle_to_update = mun_vehicles[placa]
                break

        if not vehicle_to_update:
            raise APIError("Vehículo no encontrado.", 404)

        # In a real app, you would also check if the logged-in user owns this vehicle

        vehicle_to_update.historial_revisiones.append(revision)
        print(f"Added new revision to vehicle {placa}")

        return vehicle_to_update

    async def get_managed_users(self, mun_code: str) -> List[models.UserInDB]:
        """
        Retrieves a list of users for a specific municipality.
        In a real app, this would be a proper filtered query.
        """
        await self._simulate_network()
        # This is a simple simulation. A real implementation would query the DB.
        return [user for user in self._users.values() if user.mun == mun_code]

    async def add_user(self, user_data: models.UserCreateData) -> models.UserInDB:
        """
        Adds a new user to the system.
        """
        await self._simulate_network()

        if user_data.username in self._users:
            raise APIError(_t("username_exists"), 409) # 409 Conflict

        new_user = models.UserInDB(
            **user_data.dict(),
            user_id_sim=random.randint(1000, 9999),
            status="Active",
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )
        self._users[new_user.username] = new_user
        return new_user

    async def update_user(self, username: str, user_data: models.UserUpdateData) -> models.UserInDB:
        """
        Updates an existing user's data.
        """
        await self._simulate_network()

        user = self._users.get(username)
        if not user:
            raise APIError(_t("error.user_not_found"), 404)

        update_data = user_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)

        user.last_modified = datetime.datetime.now(datetime.timezone.utc)
        return user

    async def delete_user(self, username: str) -> bool:
        """
        Deletes a user from the system.
        """
        await self._simulate_network()

        if username not in self._users:
            raise APIError(_t("error.user_not_found"), 404)

        # Prevent deleting the main test users for demo stability
        if username in ["ciudadano_test", "admin_test"]:
            raise APIError("Cannot delete core test users.", 403)

        del self._users[username]
        return True
