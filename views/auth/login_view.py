# views/auth/login_view.py

import flet as ft
from typing import Callable, Optional

# Project imports
from api_client import ApiClient, APIError
from app_data import _t, USER_ROLES, dane_data
from models import LoginResponseData
from utils import handle_api_error


class LoginView(ft.UserControl):
    """
    View for user login and territorial context selection.
    """
    def __init__(self, api_client: ApiClient, on_login_success: Callable[[LoginResponseData], None]):
        super().__init__()
        self.api_client = api_client
        self.on_login_success = on_login_success  # Callback to notify main_app on success

        # --- Control References ---
        self.username_field_ref = ft.Ref[ft.TextField]()
        self.password_field_ref = ft.Ref[ft.TextField]()
        self.role_dropdown_ref = ft.Ref[ft.Dropdown]()
        self.dept_dropdown_ref = ft.Ref[ft.Dropdown]()
        self.mun_dropdown_ref = ft.Ref[ft.Dropdown]()
        self.error_text_ref = ft.Ref[ft.Text]()
        self.login_button_ref = ft.Ref[ft.ElevatedButton]()

    async def _login_click(self, e):
        """Handles the login attempt by calling the ApiClient."""
        # Get controls from references
        uname_ctrl = self.username_field_ref.current
        pwd_ctrl = self.password_field_ref.current
        login_btn = self.login_button_ref.current
        error_display = self.error_text_ref.current

        # Reset UI state
        if error_display:
            error_display.value = ""
            error_display.visible = False

        if login_btn:
            login_btn.disabled = True
            login_btn.text = _t("verifying")

        await self.update_async()

        try:
            # Basic frontend validation
            uname = uname_ctrl.value.strip()
            pwd = pwd_ctrl.value
            if not all([uname, pwd]):
                raise ValueError(_t("required_field"))

            # API call
            login_response_data = await self.api_client.login(username=uname, password=pwd)

            # On success, call the callback function passed from main_app
            self.on_login_success(login_response_data)

        except (ValueError, APIError) as err:
            # Display error message on the UI
            if isinstance(err, ValueError):
                error_display.value = str(err)
            else:
                # Use the centralized error handler for API errors
                # We can still show a local message if we want
                error_display.value = err.message

            error_display.visible = True

        except Exception as ex:
            # Handle unexpected errors
            error_display.value = _t("internal_error")
            error_display.visible = True
            print(f"Unexpected login error: {ex}")

        finally:
            # Re-enable the login button if we are still on the login view
            if self.page and self.page.route == "/login" and login_btn:
                login_btn.disabled = False
                login_btn.text = _t("botón_iniciar sesión")
            await self.update_async()

    def _dept_changed(self, e):
        """Updates the municipality dropdown when a department is selected."""
        dept_code = self.dept_dropdown_ref.current.value
        mun_dropdown = self.mun_dropdown_ref.current
        mun_dropdown.options.clear()
        mun_dropdown.value = None

        if dept_code and dane_data and dept_code in dane_data:
            municipalities = dane_data[dept_code].get("municipalities", {})
            sorted_muns = sorted(municipalities.items(), key=lambda item: item[1])
            for code, name in sorted_muns:
                mun_dropdown.options.append(ft.dropdown.Option(key=code, text=name))
            mun_dropdown.disabled = False
        else:
            mun_dropdown.disabled = True
        self.update()

    def _role_changed(self, e):
        """Enables or disables location dropdowns based on the selected role."""
        # For now, we enable it for all roles except the default selection
        role = self.role_dropdown_ref.current.value
        is_location_needed = bool(role)

        self.dept_dropdown_ref.current.disabled = not is_location_needed
        # Municipality dropdown is handled by _dept_changed
        if not is_location_needed:
            self.mun_dropdown_ref.current.disabled = True

        self.update()

    def build(self):
        """Builds the UI for the LoginView."""
        dept_opts = [
            ft.dropdown.Option(k, d["name"])
            for k, d in sorted(dane_data.items(), key=lambda i: i[1]['name'])
            if k and 'name' in d
        ]
        role_opts = [ft.dropdown.Option(r) for r in USER_ROLES]

        return ft.Card(
            elevation=2,
            margin=20,
            content=ft.Container(
                padding=ft.padding.symmetric(horizontal=30, vertical=40),
                width=450,
                content=ft.Column(
                    [
                        ft.Text(_t("login_title"), size=24, weight=ft.FontWeight.BOLD, text_align="center"),
                        ft.Text(_t("login_context_selection"), size=14, color=ft.colors.OUTLINE, text_align="center", italic=True),
                        ft.Divider(height=20, color=ft.colors.TRANSPARENT),
                        ft.TextField(
                            ref=self.username_field_ref,
                            label=_t("username"),
                            autofocus=True,
                            prefix_icon=ft.icons.PERSON_OUTLINE
                        ),
                        ft.TextField(
                            ref=self.password_field_ref,
                            label=_t("password"),
                            password=True,
                            can_reveal_password=True,
                            prefix_icon=ft.icons.LOCK_OUTLINE,
                            on_submit=self._login_click
                        ),
                        ft.Dropdown(
                            ref=self.role_dropdown_ref,
                            label=_t("role"),
                            options=role_opts,
                            hint_text=_t("select_role"),
                            on_change=self._role_changed
                        ),
                        ft.Dropdown(
                            ref=self.dept_dropdown_ref,
                            label=_t("department"),
                            options=dept_opts,
                            hint_text=_t("select_department"),
                            on_change=self._dept_changed,
                            disabled=True
                        ),
                        ft.Dropdown(
                            ref=self.mun_dropdown_ref,
                            label=_t("municipality"),
                            options=[],
                            hint_text=_t("select_municipality"),
                            disabled=True
                        ),
                        ft.Text(ref=self.error_text_ref, color=ft.colors.ERROR, visible=False, size=12, text_align="center"),
                        ft.Divider(height=15, color=ft.colors.TRANSPARENT),
                        ft.Row(
                            [
                                ft.ElevatedButton(
                                    ref=self.login_button_ref,
                                    text=_t("botón_iniciar sesión"),
                                    icon=ft.icons.LOGIN_ROUNDED,
                                    on_click=self._login_click,
                                    expand=True,
                                    style=ft.ButtonStyle(padding=12, shape=ft.StadiumBorder())
                                )
                            ],
                            alignment="center"
                        )
                    ],
                    horizontal_alignment="center",
                    spacing=12
                )
            )
        )
