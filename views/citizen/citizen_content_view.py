# views/citizen/citizen_content_view.py
import flet as ft
from typing import Dict, List

# Project imports
from api_client import ApiClient, APIError
from app_data import _t
from models import FineUIDetail, TramiteActivo, ProgramInfo, VehicleBase, VehicleHojaDeVida
from utils import handle_api_error, show_snackbar_async
from collections import defaultdict
import flet_map as flet_map

class CitizenContentView(ft.UserControl):
    """
    The main view for the 'Citizen' role, containing navigation and content display.
    """
    def __init__(self, api_client: ApiClient, user_info: Dict):
        super().__init__()
        self.api_client = api_client
        self.user_info = user_info
        self.username = user_info.get("username", "N/A")

        # --- UI References ---
        self.nav_rail = ft.Ref[ft.NavigationRail]()
        self.content_area = ft.Ref[ft.Column]()

    async def did_mount_async(self):
        """Called when the control is added to the page."""
        # Load the initial view (Home)
        await self._on_nav_change()

    async def _on_nav_change(self, e=None):
        """Handles navigation changes from the NavigationRail."""
        selected_index = e.control.selected_index if e else 0
        self.content_area.current.controls.clear()

        # Show a loading indicator
        self.content_area.current.controls.append(ft.ProgressRing())
        await self.update_async()

        if selected_index == 0: # Home
            self.content_area.current.controls = [self._create_home_view()]
        elif selected_index == 1: # My Fines
            await self._show_fines_view()
        elif selected_index == 2: # My Vehicles
            await self._show_my_vehicles_view()
        elif selected_index == 3: # My Procedures
            await self._show_tramites_view()
        elif selected_index == 4: # Programs
            await self._show_programs_view()
        elif selected_index == 5: # Offices Map
            await self._show_offices_map_view()
        elif selected_index == 6: # My Documents
            await self._show_documents_view()

        await self.update_async()

    def _create_home_view(self) -> ft.Control:
        """Creates the content for the Home view."""
        return ft.Column([
            ft.Text(f"{_t('welcome', default='Welcome')}, {self.user_info.get('full_name', self.username)}!", size=24),
            ft.Text(_t("home_page_intro", default="Select an option from the menu to get started."))
        ])

    async def _show_fines_view(self):
        """Fetches and displays the user's fines."""
        try:
            fines = await self.api_client.get_my_fines()
            if not fines:
                self.content_area.current.controls = [
                    ft.Column([
                        ft.Icon(ft.icons.CHECK_CIRCLE_OUTLINE, color=ft.colors.GREEN, size=40),
                        ft.Text(_t("no_fines_found"))
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)
                ]
            else:
                self.content_area.current.controls = [
                    ft.Text(_t("my_fines"), style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                    ft.ListView(controls=[self._create_fine_card(f) for f in fines], expand=True, spacing=10)
                ]
        except Exception as e:
            await handle_api_error(self.page, e, "load_fines")
            self.content_area.current.controls = [ft.Text(_t("error.internal_error_load", error=str(e)))]

    def _create_fine_card(self, fine: FineUIDetail) -> ft.Card:
        """Creates a Card control for a single fine."""
        status_color = ft.colors.GREEN if fine.status == "Pagado" else (ft.colors.ORANGE if fine.status == "Pendiente" else ft.colors.GREY)

        async def complete_course_click(e, fine_id=fine.id):
            try:
                await self.api_client.mark_course_as_completed(fine_id)
                # Refresh the view to show updated status and potential new discount
                await self._show_fines_view()
            except Exception as ex:
                await handle_api_error(self.page, ex, "mark_course_completed")

        async def pay_fine_click(e, fine_id=fine.id):
            e.control.disabled = True
            e.control.text = "Procesando..."
            await self.update_async()
            try:
                checkout_url = await self.api_client.create_fine_checkout(fine_id)
                if checkout_url:
                    await self.page.launch_url_async(checkout_url)
                else:
                    await show_snackbar_async(self.page, "No se pudo obtener la URL de pago.", ft.colors.RED)
            except Exception as ex:
                await handle_api_error(self.page, ex, "pay_fine")
            finally:
                e.control.disabled = False
                e.control.text = "Pagar Multa"
                await self.update_async()

        card_content = ft.Container(
            padding=15,
            content=ft.Column([
                ft.Row([
                    ft.Text(f"ID: {fine.id}", weight=ft.FontWeight.BOLD),
                    ft.Chip(label=ft.Text(fine.tipo), bgcolor=ft.colors.BLUE_GREY),
                    ft.Chip(
                        label=ft.Text(fine.status),
                        bgcolor=status_color,
                        label_style=ft.TextStyle(color=ft.colors.WHITE, size=11)
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Text(fine.description),
                ft.Divider(height=5, color=ft.colors.TRANSPARENT),
                ft.Row([
                    ft.Text(f"{_t('date', default='Date')}: {fine.date.strftime('%Y-%m-%d')}"),
                    ft.Text(f"{_t('value', default='Value')}: {fine.final_value_formatted}", weight=ft.FontWeight.BOLD)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Text(
                    _t("discount_applied", default="*Discount applied!"),
                    color=ft.colors.GREEN,
                    italic=True,
                    visible=fine.descuento_aplicable
                ),
                ft.ElevatedButton(
                    text="Marcar Curso como Completado",
                    icon=ft.icons.SCHOOL,
                    on_click=complete_course_click,
                    visible=(fine.tipo == "Pedagógico" and not fine.curso_completado and fine.status == "Pendiente")
                ),
                ft.TextButton(
                    text="Impugnar Comparendo",
                    icon=ft.icons.GAVEL,
                    on_click=lambda e, f_id=fine.id: self._contest_fine_click(f_id),
                    visible=(fine.status == "Pendiente")
                ),
                ft.ElevatedButton(
                    text="Pagar Multa",
                    icon=ft.icons.PAYMENT,
                    on_click=pay_fine_click,
                    visible=(fine.status == "Pendiente" and fine.tipo == "Económico"),
                    bgcolor=ft.colors.GREEN,
                    color=ft.colors.WHITE
                )
            ], alignment=ft.MainAxisAlignment.SPACE_AROUND)
        )
        return ft.Card(content=card_content)

    async def _contest_fine_click(self, fine_id: str):
        """Handles the click event for contesting a fine."""
        try:
            await self.api_client.contest_fine(fine_id)
            await show_snackbar_async(self.page, "El comparendo ha sido marcado como impugnado.", ft.colors.BLUE)
            await self._show_fines_view()
        except Exception as e:
            await handle_api_error(self.page, e, "contest_fine")

    async def _show_my_vehicles_view(self):
        """Fetches and displays the user's vehicles."""
        try:
            # This method will be implemented in the next phase in the ApiClient
            # For now, we expect it to exist.
            vehicles = await self.api_client.get_my_vehicles()
            if not vehicles:
                self.content_area.current.controls = [
                    ft.Column([
                        ft.Icon(ft.icons.DIRECTIONS_CAR_OUTLINED, opacity=0.5, size=40),
                        ft.Text("No tienes vehículos registrados.")
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)
                ]
            else:
                self.content_area.current.controls = [
                    ft.Text("Mis Vehículos", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                    ft.ListView(controls=[self._create_vehicle_card(v) for v in vehicles], expand=True, spacing=10)
                ]
        except AttributeError:
             self.content_area.current.controls = [ft.Text("La función get_my_vehicles() aún no está implementada en el API client.")]
        except Exception as e:
            await handle_api_error(self.page, e, "load_my_vehicles")
            self.content_area.current.controls = [ft.Text(_t("error.internal_error_load", error=str(e)))]

        await self.update_async()

    def _create_vehicle_card(self, vehicle: VehicleBase) -> ft.Card:
        """Creates a Card control for a single vehicle."""
        return ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Column([
                    ft.Text(f"{vehicle.marca} {vehicle.modelo} ({vehicle.ano})", weight=ft.FontWeight.BOLD),
                    ft.Text(f"Placa: {vehicle.placa}"),
                    ft.Row([
                        ft.TextButton(
                            text="Ver Hoja de Vida",
                            on_click=lambda e, p=vehicle.placa: self._show_my_vehicle_details(p)
                        )
                    ], alignment=ft.MainAxisAlignment.END)
                ])
            )
        )

    async def _show_my_vehicle_details(self, placa: str):
        """Shows the detailed 'Hoja de Vida' for one of the user's vehicles."""
        self.content_area.current.controls = [ft.ProgressRing()]
        await self.update_async()

        try:
            hoja_de_vida = await self.api_client.get_vehicle_details(placa)
            if not hoja_de_vida:
                self.content_area.current.controls = [ft.Text("Vehículo no encontrado.")]
            else:
                # Build the detailed view
                history_cards = [
                    ft.ListTile(
                        leading=ft.Icon(ft.icons.BUILD),
                        title=ft.Text(f"{rev.fecha.strftime('%Y-%m-%d')}: {rev.taller}"),
                        subtitle=ft.Text(f"{rev.descripcion} - ${rev.costo:,}")
                    ) for rev in hoja_de_vida.historial_revisiones
                ] if hoja_de_vida.historial_revisiones else [ft.Text("No hay historial de revisiones.")]

                self.content_area.current.controls = [
                    ft.Row([
                        ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda e: self._show_my_vehicles_view()),
                        ft.Text(f"Hoja de Vida - {hoja_de_vida.placa}", style=ft.TextThemeStyle.HEADLINE_SMALL)
                    ]),
                    ft.Text(f"Marca/Modelo: {hoja_de_vida.marca} {hoja_de_vida.modelo} ({hoja_de_vida.ano})"),
                    ft.Text(f"SOAT Vence: {hoja_de_vida.soat_hasta.strftime('%Y-%m-%d')}"),
                    ft.Divider(),
                    ft.Text("Historial de Revisiones", style=ft.TextThemeStyle.TITLE_MEDIUM),
                    ft.Column(controls=history_cards),
                    ft.ElevatedButton(text="Añadir Registro de Mantenimiento") # Placeholder
                ]
        except Exception as e:
            await handle_api_error(self.page, e, "load_vehicle_details")

        await self.update_async()

    async def _show_tramites_view(self):
        """Fetches and displays the user's scheduled appointments."""
        try:
            appointments = await self.api_client.get_my_appointments()
            if not appointments:
                self.content_area.current.controls = [
                    ft.Column([
                        ft.Icon(ft.icons.EVENT_BUSY_OUTLINED, opacity=0.5, size=40),
                        ft.Text("No tienes citas agendadas.")
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)
                ]
            else:
                self.content_area.current.controls = [
                    ft.Text("Mis Citas Agendadas", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                    ft.ListView(controls=[self._create_appointment_card(a) for a in appointments], expand=True, spacing=10)
                ]
        except Exception as e:
            await handle_api_error(self.page, e, "load_appointments")
            self.content_area.current.controls = [ft.Text(_t("error.internal_error_load", error=str(e)))]

    def _create_appointment_card(self, appointment: Dict) -> ft.Card:
        """Creates a Card control for a single scheduled appointment."""
        # Note: The appointment time from the backend will be a string.
        # We can parse it for better formatting if needed.
        return ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Column([
                    ft.Text(f"Cita ID: {appointment['id']}", weight=ft.FontWeight.BOLD),
                    ft.Text(f"Trámite ID: {appointment['procedure_id']}"),
                    ft.Text(f"Fecha y Hora: {appointment['appointment_time']}"),
                    ft.Chip(label=ft.Text(appointment['status'])),
                ])
            )
        )

    async def _show_programs_view(self):
        """Fetches and displays available programs and procedures."""
        try:
            programs = await self.api_client.get_available_procedures()

            # Group programs by category
            grouped_programs = defaultdict(list)
            for prog in programs:
                grouped_programs[prog.categoria].append(prog)

            if not grouped_programs:
                self.content_area.current.controls = [ft.Text(_t("no_programs_found"))]
            else:
                program_list_controls = []
                for category, items in grouped_programs.items():
                    program_list_controls.append(ft.Text(category, style=ft.TextThemeStyle.HEADLINE_SMALL))
                    for item in items:
                        program_list_controls.append(self._create_program_card(item))
                    program_list_controls.append(ft.Divider(height=20))

                self.content_area.current.controls = [
                    ft.Text(_t("programs"), style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                    ft.ListView(controls=program_list_controls, expand=True, spacing=10)
                ]
        except Exception as e:
            await handle_api_error(self.page, e, "load_programs")
            self.content_area.current.controls = [ft.Text(_t("error.internal_error_load", error=str(e)))]

    def _create_program_card(self, program: ProgramInfo) -> ft.Card:
        """Creates a Card control for a single program or procedure."""

        async def open_booking_dialog(e):
            # For simplicity, we use a text field for date. A real app would use a DatePicker.
            datetime_field = ft.Ref[ft.TextField]()

            async def book_click(e):
                try:
                    if not datetime_field.current.value:
                        return # Add user feedback here

                    # Basic parsing, assumes "YYYY-MM-DD HH:MM"
                    dt_str = datetime_field.current.value

                    appointment_data = {
                        "procedure_id": program.id,
                        "appointment_time": dt_str
                    }
                    await self.api_client.book_appointment(appointment_data)
                    self.page.dialog.open = False
                    await self.page.update_async()
                    await show_snackbar_async(self.page, "Cita agendada exitosamente. Verifícala en 'Mis Trámites'.", ft.colors.GREEN)
                    await self._show_tramites_view() # Refresh appointments list
                except Exception as ex:
                    await handle_api_error(self.page, ex, "book_appointment")

            self.page.dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text(f"Agendar Cita para: {program.nombre}"),
                content=ft.Column([
                    ft.Text("Por favor, ingrese la fecha y hora deseada (YYYY-MM-DD HH:MM):"),
                    ft.TextField(ref=datetime_field, hint_text="Ej: 2025-12-24 14:30"),
                ]),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: setattr(self.page.dialog, 'open', False) or self.page.update()),
                    ft.ElevatedButton("Confirmar Cita", on_click=book_click),
                ]
            )
            self.page.dialog.open = True
            await self.page.update_async()

        return ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Column([
                    ft.Text(program.nombre, weight=ft.FontWeight.BOLD),
                    ft.Text(program.descripcion, italic=True, color=ft.colors.OUTLINE),
                    ft.Row([
                        ft.ElevatedButton(
                            text="Agendar Cita",
                            icon=ft.icons.CALENDAR_MONTH,
                            on_click=open_booking_dialog
                        )
                    ], alignment=ft.MainAxisAlignment.END)
                ])
            )
        )

    async def _show_offices_map_view(self):
        """Fetches and displays all transit authority offices on a map."""
        self.content_area.current.controls = [ft.ProgressRing()]
        await self.update_async()
        try:
            authorities = await self.api_client.get_all_authorities()

            markers = [
                flet_map.Marker(
                    latitude=auth.latitude,
                    longitude=auth.longitude,
                    tooltip=auth.name
                ) for auth in authorities if auth.latitude and auth.longitude
            ]

            if not markers:
                self.content_area.current.controls = [ft.Text("No se encontraron sedes con geolocalización.")]
            else:
                map_control = flet_map.FletMap(
                    latitude=4.60971, # Centered on Bogotá initially
                    longitude=-74.08175,
                    zoom=6,
                    markers=markers,
                    expand=True
                )
                self.content_area.current.controls = [
                    ft.Text("Sedes de Tránsito", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                    ft.Container(content=map_control, expand=True, border_radius=10)
                ]

        except Exception as e:
            await handle_api_error(self.page, e, "load_offices_map")

        await self.update_async()

    async def _show_documents_view(self):
        """Fetches and displays the user's documents, and provides an upload UI."""

        async def on_file_picker_result(e: ft.FilePickerResultEvent):
            if not e.files:
                return # User cancelled

            # For simplicity, we handle one file at a time
            file = e.files[0]
            document_type = doc_type_dropdown.current.value
            if not document_type:
                await show_snackbar_async(self.page, "Por favor, seleccione un tipo de documento.", ft.colors.RED)
                return

            upload_button.current.disabled = True
            upload_button.current.text = "Subiendo..."
            await self.update_async()

            try:
                await self.api_client.upload_document(file.path, document_type)
                await show_snackbar_async(self.page, "Documento subido exitosamente.", ft.colors.GREEN)
                await self._show_documents_view() # Refresh the view
            except Exception as ex:
                await handle_api_error(self.page, ex, "upload_document")
            finally:
                upload_button.current.disabled = False
                upload_button.current.text = "Subir Documento Seleccionado"
                await self.update_async()

        file_picker = ft.FilePicker(on_result=on_file_picker_result)
        self.page.overlay.append(file_picker)
        await self.page.update_async()

        doc_type_dropdown = ft.Ref[ft.Dropdown]()
        upload_button = ft.Ref[ft.ElevatedButton]()

        upload_ui = ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Column([
                    ft.Text("Subir Nuevo Documento", style=ft.TextThemeStyle.TITLE_MEDIUM),
                    ft.Dropdown(
                        ref=doc_type_dropdown,
                        label="Tipo de Documento",
                        options=[
                            ft.dropdown.Option("SOAT"),
                            ft.dropdown.Option("LICENSE", "Licencia de Conducir"),
                            ft.dropdown.Option("ID", "Cédula de Ciudadanía"),
                            ft.dropdown.Option("OTHER", "Otro"),
                        ]
                    ),
                    ft.ElevatedButton(
                        "Seleccionar Archivo...",
                        icon=ft.icons.UPLOAD_FILE,
                        on_click=lambda _: file_picker.pick_files(
                            allow_multiple=False,
                            allowed_extensions=["pdf", "png", "jpg"]
                        )
                    ),
                    ft.ElevatedButton(
                        ref=upload_button,
                        text="Subir Documento Seleccionado",
                        icon=ft.icons.UPLOAD,
                        # This button is implicitly handled by the on_result callback
                    )
                ])
            )
        )

        self.content_area.current.controls = [
            ft.Text("Billetera de Documentos", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
            upload_ui,
            ft.Divider(),
            ft.Text("Mis Documentos Cargados", style=ft.TextThemeStyle.TITLE_MEDIUM),
            ft.ProgressRing() # Placeholder for the list
        ]
        await self.update_async()

        try:
            documents = await self.api_client.get_my_documents()
            if not documents:
                doc_list_view = ft.Text("No tienes documentos guardados.")
            else:
                doc_list_view = ft.Column(
                    controls=[
                        ft.ListTile(
                            leading=ft.Icon(ft.icons.DESCRIPTION),
                            title=ft.Text(doc['document_type']),
                            subtitle=ft.Text(f"Subido: {doc['upload_date']}"),
                            trailing=ft.IconButton(
                                icon=ft.icons.OPEN_IN_NEW,
                                url=f"{self.api_client.base_url}{doc['file_path']}",
                                url_target="_blank"
                            )
                        ) for doc in documents
                    ]
                )

            # Replace the progress ring with the actual list
            self.content_area.current.controls[-1] = doc_list_view

        except Exception as e:
            await handle_api_error(self.page, e, "load_documents")
            self.content_area.current.controls[-1] = ft.Text("Error al cargar documentos.")

        await self.update_async()


    def build(self):
        """Builds the UI for the CitizenContentView."""
        return ft.Row(
            [
                ft.NavigationRail(
                    ref=self.nav_rail,
                    selected_index=0,
                    label_type=ft.NavigationRailLabelType.ALL,
                    min_width=100,
                    min_extended_width=400,
                    leading=ft.Icon(ft.icons.CAR_CRASH),
                    group_alignment=-0.9,
                    destinations=[
                        ft.NavigationRailDestination(icon=ft.icons.HOME_OUTLINED, selected_icon=ft.icons.HOME, label=_t("home")),
                        ft.NavigationRailDestination(icon=ft.icons.RECEIPT_LONG_OUTLINED, selected_icon=ft.icons.RECEIPT_LONG, label=_t("my_fines")),
                        ft.NavigationRailDestination(icon=ft.icons.DIRECTIONS_CAR_OUTLINED, selected_icon=ft.icons.DIRECTIONS_CAR, label="Mis Vehículos"),
                        ft.NavigationRailDestination(icon=ft.icons.DESCRIPTION_OUTLINED, selected_icon=ft.icons.DESCRIPTION, label=_t("my_tramites")),
                        ft.NavigationRailDestination(icon=ft.icons.EVENT_OUTLINED, selected_icon=ft.icons.EVENT, label=_t("programs")),
                        ft.NavigationRailDestination(icon=ft.icons.MAP_OUTLINED, selected_icon=ft.icons.MAP, label="Sedes"),
                        ft.NavigationRailDestination(icon=ft.icons.FOLDER_SHARED_OUTLINED, selected_icon=ft.icons.FOLDER_SHARED, label="Documentos"),
                    ],
                    on_change=self._on_nav_change,
                ),
                ft.VerticalDivider(),
                ft.Column(
                    ref=self.content_area,
                    controls=[ft.ProgressRing()], # Initial loading state
                    expand=True,
                    scroll=ft.ScrollMode.ADAPTIVE,
                    alignment=ft.MainAxisAlignment.START,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                )
            ],
            expand=True,
        )
