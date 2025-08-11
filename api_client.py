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
from app_data import _t, UVB_VALUE_2025, INFRACTIONS_CATALOG, COURSES_CATALOG

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
        self._infractions: Dict[str, models.InfractionInfo] = {} # {code: InfractionInfo}
        self._courses: Dict[str, models.CourseInfo] = {} # {id: CourseInfo}
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

        # Load infractions catalog into a searchable dictionary
        for info in INFRACTIONS_CATALOG:
            self._infractions[info['code']] = models.InfractionInfo(**info)

        # Create sample fines for the citizen using the new structure
        self._fines[citizen_user.username] = [
            models.FineBase(
                id="C0MP001",
                date=datetime.date(2023, 10, 20),
                infraction_code="C29",
                placa="ABC-123",
                status="Pendiente",
                tipo="Pedagógico", # This one requires a course
                curso_completado=False
            ),
            models.FineBase(
                id="C0MP002",
                date=datetime.date(2023, 11, 5),
                infraction_code="D04",
                placa="ABC-123",
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

        # Load courses catalog
        for course_info in COURSES_CATALOG:
            self._courses[course_info['id']] = models.CourseInfo(**course_info)

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
            infraction_info = self._infractions.get(fine.infraction_code)
            if not infraction_info:
                continue # Skip fines with no matching infraction info

            base_value = int(infraction_info.uvb_value * UVB_VALUE_2025)

            # Updated business logic for discounts
            days_since_fine = (datetime.date.today() - fine.date).days
            descuento_aplicable = False
            if fine.status == "Pendiente":
                if fine.tipo == "Pedagógico":
                    # Discount only applies if the course is completed
                    if fine.curso_completado and days_since_fine <= 5:
                        descuento_aplicable = True
                else: # For economic fines, discount is direct
                    if days_since_fine <= 5:
                        descuento_aplicable = True

            valor_con_descuento = base_value // 2 if descuento_aplicable else base_value

            ui_fines.append(
                models.FineUIDetail(
                    **fine.dict(),
                    description=infraction_info.description,
                    base_value=base_value,
                    puntos=3, # Dummy value, could be added to InfractionInfo
                    descuento_aplicable=descuento_aplicable,
                    valor_con_descuento=valor_con_descuento,
                    base_value_formatted=f"${base_value:,}",
                    final_value_formatted=f"${valor_con_descuento:,}{'*' if descuento_aplicable else ''}",
                    fine_info_tooltip=f"{infraction_info.code}: {infraction_info.description}"
                )
            )
        return ui_fines

    async def mark_course_as_completed(self, fine_id: str) -> bool:
        """Finds a fine and marks its pedagogical course as completed."""
        await self._simulate_network()

        # Find the fine across all users
        for user_fines in self._fines.values():
            for fine in user_fines:
                if fine.id == fine_id:
                    if fine.tipo != "Pedagógico":
                        raise APIError("Esta multa no es pedagógica.", 400)
                    fine.curso_completado = True
                    print(f"Course marked as completed for fine {fine_id}")
                    return True

        raise APIError("Multa no encontrada.", 404)

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

    # --- Infraction Catalog Management ---

    async def get_infraction_catalog(self) -> List[models.InfractionInfo]:
        """Returns the entire list of infraction types."""
        await self._simulate_network()
        return list(self._infractions.values())

    async def add_infraction_info(self, infraction_data: models.InfractionInfo) -> models.InfractionInfo:
        """Adds a new infraction type to the catalog."""
        await self._simulate_network()
        if infraction_data.code in self._infractions:
            raise APIError(f"Infraction code '{infraction_data.code}' already exists.", 409)
        self._infractions[infraction_data.code] = infraction_data
        return infraction_data

    async def update_infraction_info(self, code: str, infraction_data: models.InfractionInfo) -> models.InfractionInfo:
        """Updates an existing infraction type in the catalog."""
        await self._simulate_network()
        if code not in self._infractions:
            raise APIError(f"Infraction code '{code}' not found.", 404)
        # If the code itself is being changed, we need to handle that
        if code != infraction_data.code:
            if infraction_data.code in self._infractions:
                 raise APIError(f"New infraction code '{infraction_data.code}' already exists.", 409)
            del self._infractions[code] # remove old entry
        self._infractions[infraction_data.code] = infraction_data
        return infraction_data

    async def delete_infraction_info(self, code: str) -> bool:
        """Deletes an infraction type from the catalog."""
        await self._simulate_network()
        if code not in self._infractions:
            raise APIError(f"Infraction code '{code}' not found.", 404)
        del self._infractions[code]
        return True

    # --- Courses Catalog Management ---

    async def get_courses(self) -> List[models.CourseInfo]:
        """Returns the entire list of courses."""
        await self._simulate_network()
        return list(self._courses.values())

    async def add_course(self, course_data: models.CourseInfo) -> models.CourseInfo:
        """Adds a new course to the catalog."""
        await self._simulate_network()
        if course_data.id in self._courses:
            raise APIError(f"Course ID '{course_data.id}' already exists.", 409)
        self._courses[course_data.id] = course_data
        return course_data

    async def update_course(self, course_id: str, course_data: models.CourseInfo) -> models.CourseInfo:
        """Updates an existing course in the catalog."""
        await self._simulate_network()
        if course_id not in self._courses:
            raise APIError(f"Course ID '{course_id}' not found.", 404)
        if course_id != course_data.id:
            if course_data.id in self._courses:
                 raise APIError(f"New course ID '{course_data.id}' already exists.", 409)
            del self._courses[course_id]
        self._courses[course_data.id] = course_data
        return course_data

    async def delete_course(self, course_id: str) -> bool:
        """Deletes a course from the catalog."""
        await self._simulate_network()
        if course_id not in self._courses:
            raise APIError(f"Course ID '{course_id}' not found.", 404)
        del self._courses[course_id]
        return True

    # --- Fine Issuing ---

    async def issue_new_fine(self, username: str, infraction_code: str, placa: str, date: datetime.date, tipo: str) -> models.FineBase:
        """Issues a new fine to a specific user."""
        await self._simulate_network()

        if username not in self._users:
            raise APIError(_t("error.user_not_found"), 404)
        if infraction_code not in self._infractions:
            raise APIError("Código de infracción inválido.", 404)

        new_fine = models.FineBase(
            id=f"COMP-{random.randint(1000, 9999)}",
            date=date,
            infraction_code=infraction_code,
            placa=placa,
            tipo=tipo,
            status="Pendiente"
        )

        if username not in self._fines:
            self._fines[username] = []

        self._fines[username].append(new_fine)
        print(f"Issued new fine {new_fine.id} to user {username}")
        return new_fine

    async def contest_fine(self, fine_id: str) -> bool:
        """Finds a fine and marks it as contested."""
        await self._simulate_network()

        for user_fines in self._fines.values():
            for fine in user_fines:
                if fine.id == fine_id:
                    if fine.status != "Pendiente":
                        raise APIError("Solo se pueden impugnar multas pendientes.", 400)
                    fine.contested = True
                    fine.status = "Impugnado"
                    print(f"Fine {fine_id} has been contested.")
                    return True

        raise APIError("Multa no encontrada.", 404)
