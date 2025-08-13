import flet as ft
from typing import Dict
import datetime

# Project imports
from api_client import ApiClient
from utils import handle_api_error, show_snackbar_async

class OfficerView(ft.UserControl):
    """
    A simplified view for 'Técnico' or Field Officer roles.
    The main purpose is to quickly issue a new fine.
    """
    def __init__(self, api_client: ApiClient, user_info: Dict):
        super().__init__()
        self.api_client = api_client
        self.user_info = user_info

        # --- Control References ---
        self.placa_ref = ft.Ref[ft.TextField]()
        self.infraction_code_ref = ft.Ref[ft.TextField]()
        self.target_username_ref = ft.Ref[ft.TextField]()
        self.issue_button_ref = ft.Ref[ft.ElevatedButton]()

    async def did_mount_async(self):
        # Could potentially pre-load infraction codes to a dropdown here
        pass

    async def issue_fine_click(self, e):
        """Handles the click event for the 'Issue Fine' button."""
        button = self.issue_button_ref.current
        if not all([self.placa_ref.current.value, self.infraction_code_ref.current.value, self.target_username_ref.current.value]):
            await show_snackbar_async(self.page, "Todos los campos son requeridos.", ft.colors.RED)
            return

        button.disabled = True
        button.text = "Procesando..."
        await self.update_async()

        try:
            await self.api_client.issue_new_fine(
                username=self.target_username_ref.current.value,
                infraction_code=self.infraction_code_ref.current.value.upper(),
                placa=self.placa_ref.current.value.upper(),
                date=datetime.date.today(),
                tipo="Económico" # Fines from officers are always economic by default
            )
            await show_snackbar_async(self.page, "Comparendo impuesto exitosamente.", ft.colors.GREEN)
            # Clear fields after success
            self.placa_ref.current.value = ""
            self.infraction_code_ref.current.value = ""
            self.target_username_ref.current.value = ""

        except Exception as ex:
            await handle_api_error(self.page, ex, "officer_issue_fine")
        finally:
            button.disabled = False
            button.text = "Imponer Comparendo"
            await self.update_async()

    def build(self):
        return ft.Column(
            [
                ft.AppBar(
                    title=ft.Text("Portal de Agente de Tránsito"),
                    bgcolor=ft.colors.BLUE_GREY_800
                ),
                ft.Container(
                    padding=20,
                    content=ft.Column(
                        [
                            ft.Text("Imponer Nuevo Comparendo", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                            ft.TextField(ref=self.placa_ref, label="Placa del Vehículo", capitalization=ft.TextCapitalization.CHARACTERS),
                            ft.TextField(ref=self.infraction_code_ref, label="Código de Infracción", capitalization=ft.TextCapitalization.CHARACTERS),
                            ft.TextField(ref=self.target_username_ref, label="Cédula o Username del Ciudadano"),
                            ft.Row(
                                [
                                    ft.IconButton(
                                        icon=ft.icons.CAMERA_ALT,
                                        tooltip="Escanear Placa (Futuro)",
                                        disabled=True
                                    ),
                                    ft.ElevatedButton(
                                        ref=self.issue_button_ref,
                                        text="Imponer Comparendo",
                                        icon=ft.icons.GAVEL,
                                        on_click=self.issue_fine_click,
                                        expand=True
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER
                            )
                        ],
                        spacing=15,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER
                    )
                )
            ],
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
