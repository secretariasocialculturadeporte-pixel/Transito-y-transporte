# views/admin/admin_view.py
import flet as ft
from typing import Dict
import datetime

# Project imports
from api_client import ApiClient
from app_data import _t
from models import VehicleBase, VehicleHojaDeVida, UserInDB
from utils import handle_api_error, show_snackbar_async
from analysis.data_analyzer import ANALYSIS_QUESTIONS_CATALOG, DataAnalyzer
from views.chat.chat_view import ChatView
from collections import defaultdict

class AdminView(ft.UserControl):
    """
    The main view for 'Admin' roles, for managing municipal data.
    """
    def __init__(self, api_client: ApiClient, user_info: Dict):
        super().__init__()
        self.api_client = api_client
        self.user_info = user_info
        self.mun_code = self.user_info.get("mun")

        # --- UI References ---
        self.nav_rail = ft.Ref[ft.NavigationRail]()
        self.content_area = ft.Ref[ft.Column]()
        self._vehicle_details_view = ft.Ref[ft.Column]()

    async def did_mount_async(self):
        await self._on_nav_change()

    async def _on_nav_change(self, e=None):
        selected_index = e.control.selected_index if e else 0
        self.content_area.current.controls.clear()
        self.content_area.current.controls.append(ft.ProgressRing())
        await self.update_async()

        if selected_index == 0: # Vehicle Fleet
            await self._show_vehicle_fleet_view()
        elif selected_index == 1: # User Management
            await self._show_user_management_view()
        elif selected_index == 2: # Infractions Management
            await self._show_infractions_management_view()
        elif selected_index == 3: # Courses Management
            await self._show_courses_management_view()
        elif selected_index == 4: # Analysis
            await self._show_analysis_view()
        elif selected_index == 5: # Chat
            self._show_chat_view()
        elif selected_index == 6: # Procedure Management
            await self._show_procedures_management_view()

        await self.update_async()

    async def _show_analysis_view(self):
        """Displays the UI for data analysis."""

        results_area = ft.Ref[ft.Column]()

        async def run_analysis(e, function_name: str):
            results_area.current.controls = [ft.ProgressRing()]
            await self.update_async()

            try:
                # 1. Get entidad_id from user info
                entidad_id = self.user_info.get("entidad_id")
                if not entidad_id:
                    results_area.current.controls = [ft.Text("Error: No se pudo determinar la entidad del usuario.", color=ft.colors.RED)]
                    await self.update_async()
                    return

                # 2. Fetch fresh data from the API
                fines = await self.api_client.get_fines_by_entity(entidad_id)
                vehicles = await self.api_client.get_vehicles_by_entity(entidad_id)

                # 3. Convert data for the analyzer
                all_fines_data = [f.dict() for f in fines]
                all_vehicles_data = [v.dict() for v in vehicles]

                # 4. Instantiate analyzer and run analysis
                analyzer = DataAnalyzer(
                    all_fines=all_fines_data,
                    all_vehicles=all_vehicles_data,
                    api_key="dummy-api-key" # Placeholder for API key management
                )

                result_control = analyzer.analyze(function_name)

                # 5. Display the resulting Flet control
                results_area.current.controls = [
                    ft.Text("Resultado del Análisis", style=ft.TextThemeStyle.TITLE_LARGE),
                    result_control
                ]

            except Exception as ex:
                await handle_api_error(self.page, ex, "run_analysis")
                results_area.current.controls = [ft.Text(f"Ocurrió un error al generar el reporte: {ex}", color=ft.colors.RED)]

            await self.update_async()

        # Group questions by category
        grouped_questions = defaultdict(list)
        for q in ANALYSIS_QUESTIONS_CATALOG:
            grouped_questions[q['category']].append(q)

        question_controls = []
        for category, questions in grouped_questions.items():
            question_links = [
                ft.ListTile(
                    title=ft.Text(q['question']),
                    on_click=lambda e, fn=q['analysis_function']: run_analysis(e, fn)
                ) for q in questions
            ]
            question_controls.append(
                ft.ExpansionPanelList(
                    controls=[
                        ft.ExpansionPanel(
                            header=ft.ListTile(title=ft.Text(category)),
                            content=ft.Column(question_links)
                        )
                    ]
                )
            )

        self.content_area.current.controls = [
            ft.Text("Análisis y Reportes", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
            ft.Column(question_controls),
            ft.Divider(),
            ft.Column(ref=results_area)
        ]
        await self.update_async()

    def _show_chat_view(self):
        """Displays the conversational AI chat interface."""
        # The ChatView is a self-contained component, pass user_info for personalization.
        chat_view = ChatView(self.api_client, self.user_info)
        self.content_area.current.controls = [chat_view]

    async def _show_procedures_management_view(self):
        """Displays the UI for managing bookable procedures."""

        async def open_add_procedure_dialog(e):
            name_field = ft.Ref[ft.TextField]()
            desc_field = ft.Ref[ft.TextField]()
            duration_field = ft.Ref[ft.TextField]()

            async def save_procedure_click(e):
                try:
                    # Basic validation
                    if not name_field.current.value or not duration_field.current.value:
                        # You could show an error in the dialog itself
                        return

                    procedure_data = {
                        "name": name_field.current.value,
                        "description": desc_field.current.value,
                        "duration_minutes": int(duration_field.current.value)
                    }
                    await self.api_client.create_procedure(procedure_data)
                    self.page.dialog.open = False
                    await self.page.update_async()
                    await show_snackbar_async(self.page, "Trámite creado exitosamente.", ft.colors.GREEN)
                    await self._show_procedures_management_view() # Refresh the view
                except Exception as ex:
                    await handle_api_error(self.page, ex, "create_procedure")

            self.page.dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Añadir Nuevo Trámite"),
                content=ft.Column([
                    ft.TextField(ref=name_field, label="Nombre del Trámite"),
                    ft.TextField(ref=desc_field, label="Descripción"),
                    ft.TextField(ref=duration_field, label="Duración (minutos)", keyboard_type=ft.KeyboardType.NUMBER),
                ]),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: setattr(self.page.dialog, 'open', False) or self.page.update()),
                    ft.ElevatedButton("Guardar", on_click=save_procedure_click),
                ]
            )
            self.page.dialog.open = True
            await self.page.update_async()

        self.content_area.current.controls = [
            ft.Row([
                ft.Text("Gestión de Trámites Agendables", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                ft.IconButton(icon=ft.icons.REFRESH, on_click=self._show_procedures_management_view)
            ]),
            ft.ElevatedButton("Añadir Trámite", icon=ft.icons.ADD, on_click=open_add_procedure_dialog)
        ]

        try:
            procedures = await self.api_client.get_procedures()

            columns = [
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Nombre")),
                ft.DataColumn(ft.Text("Descripción")),
                ft.DataColumn(ft.Text("Duración (min)")),
                ft.DataColumn(ft.Text("Activo")),
                ft.DataColumn(ft.Text("Acciones")),
            ]

            rows = []
            for proc in procedures:
                rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(proc['id'])),
                    ft.DataCell(ft.Text(proc['name'])),
                    ft.DataCell(ft.Text(proc['description'] or "")),
                    ft.DataCell(ft.Text(str(proc['duration_minutes']))),
                    ft.DataCell(ft.Icon(ft.icons.CHECK_CIRCLE if proc['is_active'] else ft.icons.CANCEL, color=ft.colors.GREEN if proc['is_active'] else ft.colors.RED)),
                    ft.DataCell(ft.Row([
                        ft.IconButton(icon=ft.icons.EDIT, tooltip="Editar Trámite"),
                        ft.IconButton(icon=ft.icons.POWER_SETTINGS_NEW, tooltip="Activar/Desactivar"),
                    ]))
                ]))

            self.content_area.current.controls.append(ft.DataTable(columns=columns, rows=rows))

        except Exception as e:
            await handle_api_error(self.page, e, "load_procedures")

        await self.update_async()


    async def _show_courses_management_view(self):
        """Displays the UI for managing the courses catalog."""
        self.content_area.current.controls = [
            ft.Row([
                ft.Text("Gestión de Cursos Pedagógicos", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                ft.IconButton(icon=ft.icons.REFRESH, on_click=self._show_courses_management_view)
            ]),
        ]

        try:
            courses = await self.api_client.get_courses()

            columns = [
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Nombre")),
                ft.DataColumn(ft.Text("Duración (Horas)")),
                ft.DataColumn(ft.Text("Acciones")),
            ]

            rows = []
            for course in courses:
                rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(course.id)),
                    ft.DataCell(ft.Text(course.name, width=300, max_lines=2)),
                    ft.DataCell(ft.Text(str(course.duration_hours))),
                    ft.DataCell(ft.Row([
                        ft.IconButton(icon=ft.icons.EDIT, tooltip="Editar Curso"),
                        ft.IconButton(icon=ft.icons.DELETE, tooltip="Eliminar Curso", icon_color=ft.colors.RED),
                    ]))
                ]))

            self.content_area.current.controls.append(ft.DataTable(columns=columns, rows=rows))

        except Exception as e:
            await handle_api_error(self.page, e, "load_courses_catalog")

        await self.update_async()

    async def _show_infractions_management_view(self):
        """Displays the UI for managing the infraction catalog."""
        self.content_area.current.controls = [
            ft.Row([
                ft.Text("Gestión de Catálogo de Infracciones", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                ft.IconButton(icon=ft.icons.REFRESH, on_click=self._show_infractions_management_view)
            ]),
        ]

        try:
            catalog = await self.api_client.get_infraction_catalog()

            columns = [
                ft.DataColumn(ft.Text("Código")),
                ft.DataColumn(ft.Text("Categoría")),
                ft.DataColumn(ft.Text("Descripción")),
                ft.DataColumn(ft.Text("Valor (UVB)")),
                ft.DataColumn(ft.Text("Acciones")),
            ]

            rows = []
            for info in catalog:
                rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(info.code)),
                    ft.DataCell(ft.Text(info.category)),
                    ft.DataCell(ft.Text(info.description, width=400, max_lines=2)),
                    ft.DataCell(ft.Text(str(info.uvb_value))),
                    ft.DataCell(ft.Row([
                        ft.IconButton(icon=ft.icons.EDIT, tooltip="Editar Infracción"),
                        ft.IconButton(icon=ft.icons.DELETE, tooltip="Eliminar Infracción", icon_color=ft.colors.RED),
                    ]))
                ]))

            self.content_area.current.controls.append(ft.DataTable(columns=columns, rows=rows))

        except Exception as e:
            await handle_api_error(self.page, e, "load_infraction_catalog")

        await self.update_async()

    async def _show_user_management_view(self):
        """Fetches and displays the list of users for management."""
        self.content_area.current.controls = [
            ft.Row([
                ft.Text("Gestión de Usuarios", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                ft.IconButton(icon=ft.icons.REFRESH, on_click=self._show_user_management_view)
            ]),
        ]

        try:
            users = await self.api_client.get_managed_users(self.mun_code)

            columns = [
                ft.DataColumn(ft.Text("Username")),
                ft.DataColumn(ft.Text("Full Name")),
                ft.DataColumn(ft.Text("Role")),
                ft.DataColumn(ft.Text("Status")),
                ft.DataColumn(ft.Text("Actions")),
            ]

            rows = []
            for user in users:
                rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(user.username)),
                    ft.DataCell(ft.Text(user.full_name or "")),
                    ft.DataCell(ft.Text(user.role)),
                    ft.DataCell(ft.Chip(label=ft.Text(user.status), bgcolor=ft.colors.GREEN if user.status == "Active" else ft.colors.RED)),
                    ft.DataCell(ft.Row([
                        ft.IconButton(icon=ft.icons.EDIT, tooltip="Editar Usuario"),
                        ft.IconButton(icon=ft.icons.DELETE, tooltip="Eliminar Usuario", icon_color=ft.colors.RED),
                        ft.IconButton(
                            icon=ft.icons.GAVEL,
                            tooltip="Imponer Comparendo",
                            icon_color=ft.colors.ORANGE,
                            on_click=lambda e, u=user: self._open_issue_fine_dialog(u)
                        ),
                    ]))
                ]))

            self.content_area.current.controls.append(ft.DataTable(columns=columns, rows=rows))

        except Exception as e:
            await handle_api_error(self.page, e, "load_users")

        await self.update_async()

    def _open_issue_fine_dialog(self, user: UserInDB):
        """Opens a dialog to issue a new fine to a user."""

        # --- Dialog Controls ---
        infraction_code_dd = ft.Ref[ft.Dropdown]()
        placa_tf = ft.Ref[ft.TextField]()
        tipo_dd = ft.Ref[ft.Dropdown]()

        async def issue_fine_click(e):
            try:
                # Basic validation
                if not all([infraction_code_dd.current.value, placa_tf.current.value, tipo_dd.current.value]):
                    await show_snackbar_async(self.page, "Todos los campos son requeridos.", ft.colors.RED)
                    return

                await self.api_client.issue_new_fine(
                    username=user.username,
                    infraction_code=infraction_code_dd.current.value,
                    placa=placa_tf.current.value,
                    date=datetime.date.today(), # For simplicity, use today's date
                    tipo=tipo_dd.current.value
                )

                self.page.dialog.open = False
                await self.page.update_async()
                await show_snackbar_async(self.page, f"Comparendo impuesto a {user.username} exitosamente.", ft.colors.GREEN)

            except Exception as ex:
                await handle_api_error(self.page, ex, "issue_fine")

        # --- Dialog Definition ---
        self.page.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Imponer Comparendo a {user.username}"),
            content=ft.Column([
                ft.Dropdown(
                    ref=infraction_code_dd,
                    label="Código de Infracción",
                    options=[ft.dropdown.Option(code) for code in self.api_client._infractions.keys()]
                ),
                ft.TextField(ref=placa_tf, label="Placa del Vehículo"),
                ft.Dropdown(
                    ref=tipo_dd,
                    label="Tipo de Comparendo",
                    options=[
                        ft.dropdown.Option("Económico"),
                        ft.dropdown.Option("Pedagógico"),
                    ]
                )
            ]),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(self.page.dialog, 'open', False) or self.page.update()),
                ft.ElevatedButton("Imponer", on_click=issue_fine_click),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.dialog.open = True
        self.page.update()


    async def _show_vehicle_fleet_view(self):
        """Fetches and displays the vehicle fleet for the admin's municipality."""
        self.content_area.current.controls = [
            ft.Row([
                ft.Text("Gestión de Parque Automotor", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                ft.IconButton(icon=ft.icons.REFRESH, on_click=self._show_vehicle_fleet_view)
            ]),
            # This column will hold the data table or the details view
            ft.Column(ref=self._vehicle_details_view)
        ]
        await self._show_vehicle_table()

    async def _show_vehicle_table(self, e=None):
        """Displays the main data table of vehicles."""
        vehicle_list_view = self._vehicle_details_view.current
        vehicle_list_view.controls = [ft.ProgressRing()]
        await self.update_async()

        try:
            vehicles = await self.api_client.get_vehicles_by_entity()

            columns = [
                ft.DataColumn(ft.Text("Placa")),
                ft.DataColumn(ft.Text("Marca")),
                ft.DataColumn(ft.Text("Modelo")),
                ft.DataColumn(ft.Text("Año")),
                ft.DataColumn(ft.Text("Propietario")),
                ft.DataColumn(ft.Text("Acciones")),
            ]

            rows = [self._create_vehicle_row(v) for v in vehicles]

            vehicle_list_view.controls = [ft.DataTable(columns=columns, rows=rows)]
        except Exception as ex:
            await handle_api_error(self.page, ex, "load_vehicles")
            vehicle_list_view.controls = [ft.Text(_t("error.internal_error_load", error=str(ex)))]

        await self.update_async()

    def _create_vehicle_row(self, vehicle: VehicleBase) -> ft.DataRow:
        return ft.DataRow(cells=[
            ft.DataCell(ft.Text(vehicle.placa)),
            ft.DataCell(ft.Text(vehicle.marca)),
            ft.DataCell(ft.Text(vehicle.modelo)),
            ft.DataCell(ft.Text(str(vehicle.ano))),
            ft.DataCell(ft.Text(vehicle.propietario_username)),
            ft.DataCell(ft.IconButton(
                icon=ft.icons.INFO_OUTLINE,
                tooltip="Ver Hoja de Vida",
                on_click=lambda e, p=vehicle.placa: self._show_vehicle_details(p)
            )),
        ])

    async def _show_vehicle_details(self, placa: str):
        """Shows the detailed 'Hoja de Vida' for a selected vehicle."""
        details_view = self._vehicle_details_view.current
        details_view.controls = [ft.ProgressRing()]
        await self.update_async()

        try:
            hoja_de_vida = await self.api_client.get_vehicle_details(placa)
            if not hoja_de_vida:
                details_view.controls = [ft.Text("Vehículo no encontrado.")]
            else:
                # Build the detailed view
                details_view.controls = [
                    ft.Row([
                        ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=self._show_vehicle_table),
                        ft.Text(f"Hoja de Vida - {hoja_de_vida.placa}", style=ft.TextThemeStyle.HEADLINE_SMALL)
                    ]),
                    ft.Text(f"Marca/Modelo: {hoja_de_vida.marca} {hoja_de_vida.modelo} ({hoja_de_vida.ano})"),
                    ft.Text(f"Propietario: {hoja_de_vida.propietario_username}"),
                    ft.Text(f"SOAT Vence: {hoja_de_vida.soat_hasta.strftime('%Y-%m-%d')}"),
                    ft.Text(f"Tecnomecánica Vence: {hoja_de_vida.tecno_hasta.strftime('%Y-%m-%d') if hoja_de_vida.tecno_hasta else 'N/A'}"),
                    ft.Divider(),
                    ft.Text("Historial de Revisiones", style=ft.TextThemeStyle.TITLE_MEDIUM),
                    # You would iterate through hoja_de_vida.historial_revisiones here
                    ft.Text("El historial de revisiones se mostrará aquí.")
                ]
        except Exception as e:
            await handle_api_error(self.page, e, "load_vehicle_details")
            details_view.controls = [ft.Text(_t("error.internal_error_load", error=str(e)))]

        await self.update_async()

    def build(self):
        return ft.Row(
            [
                ft.NavigationRail(
                    ref=self.nav_rail,
                    selected_index=0,
                    label_type=ft.NavigationRailLabelType.ALL,
                    destinations=[
                        ft.NavigationRailDestination(icon=ft.icons.DIRECTIONS_CAR, label="Parque Automotor"),
                        ft.NavigationRailDestination(icon=ft.icons.GROUP, label="Gestión Usuarios"),
                        ft.NavigationRailDestination(icon=ft.icons.GAVEL, label="Infracciones"),
                        ft.NavigationRailDestination(icon=ft.icons.SCHOOL, label="Cursos"),
                        ft.NavigationRailDestination(icon=ft.icons.ANALYTICS, label="Análisis"),
                        ft.NavigationRailDestination(icon=ft.icons.CHAT, label="Chat IA"),
                        ft.NavigationRailDestination(icon=ft.icons.CALENDAR_MONTH, label="Trámites"),
                    ],
                    on_change=self._on_nav_change,
                ),
                ft.VerticalDivider(),
                ft.Column(
                    ref=self.content_area,
                    controls=[ft.ProgressRing()],
                    expand=True,
                    scroll=ft.ScrollMode.ADAPTIVE,
                )
            ],
            expand=True,
        )
