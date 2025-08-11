# views/citizen/citizen_content_view.py
import flet as ft
from typing import Dict, List

# Project imports
from api_client import ApiClient, APIError
from app_data import _t
from models import FineUIDetail
from utils import handle_api_error

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
        elif selected_index == 2: # My Procedures
            self.content_area.current.controls = [ft.Text(_t("my_tramites", default="My Procedures"))]
        elif selected_index == 3: # Programs
            self.content_area.current.controls = [ft.Text(_t("programs", default="Programs"))]

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

        card_content = ft.Container(
            padding=15,
            content=ft.Column([
                ft.Row([
                    ft.Text(f"ID: {fine.id}", weight=ft.FontWeight.BOLD),
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
                )
            ])
        )
        return ft.Card(content=card_content)

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
                        ft.NavigationRailDestination(icon=ft.icons.DESCRIPTION_OUTLINED, selected_icon=ft.icons.DESCRIPTION, label=_t("my_tramites")),
                        ft.NavigationRailDestination(icon=ft.icons.EVENT_OUTLINED, selected_icon=ft.icons.EVENT, label=_t("programs")),
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
