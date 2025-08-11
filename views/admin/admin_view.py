# views/admin/admin_view.py
import flet as ft
from typing import Dict

# Project imports
from api_client import ApiClient
from app_data import _t
from models import VehicleBase, VehicleHojaDeVida
from utils import handle_api_error

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
                        ft.IconButton(icon=ft.icons.EDIT, tooltip="Edit User"),
                        ft.IconButton(icon=ft.icons.DELETE, tooltip="Delete User", icon_color=ft.colors.RED),
                    ]))
                ]))

            self.content_area.current.controls.append(ft.DataTable(columns=columns, rows=rows))

        except Exception as e:
            await handle_api_error(self.page, e, "load_users")

        await self.update_async()


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
            vehicles = await self.api_client.get_vehicles_by_municipality(self.mun_code)

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
