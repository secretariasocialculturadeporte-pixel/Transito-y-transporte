# views/common/my_account_view.py
import flet as ft
from typing import Dict, Optional, List

# Project imports
from api_client import ApiClient, APIError
from app_data import _t
from models import PasswordChangeData, UserDetail
from utils import handle_api_error, show_snackbar_async

class MyAccountView(ft.UserControl):
    """
    View for the user to manage their own account, primarily changing the password.
    """
    def __init__(self, api_client: ApiClient, user_info: Dict):
        super().__init__()
        self.api_client = api_client
        self.user_info = user_info
        self._current_user_detail: Optional[UserDetail] = None

        # --- Control References ---
        self.old_password_ref = ft.Ref[ft.TextField]()
        self.new_password_ref = ft.Ref[ft.TextField]()
        self.confirm_password_ref = ft.Ref[ft.TextField]()
        self.pw_form_error_text_ref = ft.Ref[ft.Text]()
        self.change_pw_button_ref = ft.Ref[ft.ElevatedButton]()
        self.user_details_area_ref = ft.Ref[ft.Column]()

    async def did_mount_async(self):
        """Load the user's full details when the view is mounted."""
        await self._load_user_details()

    async def _load_user_details(self):
        """Fetches user details from the API and builds the display."""
        if not self.user_details_area_ref.current:
            return

        self.user_details_area_ref.current.controls = [ft.ProgressRing(width=20, height=20)]
        await self.user_details_area_ref.current.update_async()

        try:
            # The API endpoint /users/me should be handled by get_user_details(username=None)
            user_detail_model = await self.api_client.get_user_details()
            self._current_user_detail = user_detail_model
            self.user_details_area_ref.current.controls = self._build_user_info_display()
        except Exception as e:
            await handle_api_error(self.page, e, "my_account_load")
            self.user_details_area_ref.current.controls = [ft.Text(_t("error.internal_error_load", error=str(e)))]

        await self.user_details_area_ref.current.update_async()

    def _build_user_info_display(self) -> List[ft.Control]:
        """Constructs the user information display section."""
        if not self._current_user_detail:
            return [ft.Text(_t("details_not_available"))]

        ud = self._current_user_detail

        def create_status_chip(status: str) -> ft.Chip:
            color = ft.colors.GREEN if status == "Active" else ft.colors.RED
            return ft.Chip(label=ft.Text(status), bgcolor=color, label_style=ft.TextStyle(color=ft.colors.WHITE))

        return [
            ft.Text(_t("user_details"), weight=ft.FontWeight.BOLD, size=18),
            ft.Text(f"{_t('username')}: {ud.username}", selectable=True),
            ft.Text(f"{_t('role')}: {_t(ud.role.lower(), default=ud.role)}"),
            ft.Text(f"{_t('full_name')}: {ud.full_name or '-'}"),
            ft.Text(f"{_t('email')}: {ud.email or '-'}"),
            ft.Row([ft.Text(f"{_t('status')}:"), create_status_chip(ud.status)]),
            ft.Divider(height=10),
        ]

    async def _change_password_click(self, e):
        """Handles the password change attempt."""
        # Get controls
        old_pw_ctrl = self.old_password_ref.current
        new_pw_ctrl = self.new_password_ref.current
        confirm_pw_ctrl = self.confirm_password_ref.current
        error_ctrl = self.pw_form_error_text_ref.current
        button = self.change_pw_button_ref.current

        if not button or button.disabled:
            return

        # Update button to show loading state
        button.disabled = True
        orig_text = button.text
        button.text = _t("saving")
        error_ctrl.value = ""
        error_ctrl.visible = False
        await self.update_async()

        try:
            old_pw = old_pw_ctrl.value
            new_pw = new_pw_ctrl.value
            confirm_pw = confirm_pw_ctrl.value

            # --- Frontend Validations ---
            if not all([old_pw, new_pw, confirm_pw]):
                raise ValueError(_t("required_field"))
            if new_pw != confirm_pw:
                raise ValueError(_t("error.pw_mismatch", default="Passwords do not match."))
            if len(new_pw) < 4:
                raise ValueError(_t("pw_change_fail_too_short"))

            # --- API Call ---
            payload = {"old_password": old_pw, "new_password": new_pw}
            success = await self.api_client.change_my_password(payload)

            if success:
                await show_snackbar_async(self.page, _t("pw_change_success"), ft.colors.GREEN)
                # Clear fields on success
                old_pw_ctrl.value = ""
                new_pw_ctrl.value = ""
                confirm_pw_ctrl.value = ""

        except (ValueError, APIError) as err:
            error_ctrl.value = str(err) if isinstance(err, ValueError) else err.message
            error_ctrl.visible = True
        except Exception as ex:
            await handle_api_error(self.page, ex, "change_password")
            error_ctrl.value = _t("internal_error")
            error_ctrl.visible = True
        finally:
            # Restore button state
            if button:
                button.disabled = False
                button.text = orig_text
            await self.update_async()

    def build(self):
        pw_change_form = ft.Column([
            ft.Text(_t("password_change"), weight=ft.FontWeight.BOLD, size=18),
            ft.TextField(ref=self.old_password_ref, label=_t("old_password"), password=True, can_reveal_password=True),
            ft.TextField(ref=self.new_password_ref, label=_t("new_password"), password=True, can_reveal_password=True),
            ft.TextField(ref=self.confirm_password_ref, label=_t("confirm_password"), password=True, can_reveal_password=True, on_submit=self._change_password_click),
            ft.Text(ref=self.pw_form_error_text_ref, color=ft.colors.ERROR, visible=False, size=12),
            ft.Row([
                ft.ElevatedButton(
                    ref=self.change_pw_button_ref,
                    text=_t("save"),
                    icon=ft.icons.SAVE,
                    on_click=self._change_password_click
                )
            ], alignment=ft.MainAxisAlignment.END)
        ], spacing=12)

        return ft.Column(
            [
                ft.Card(
                    elevation=1,
                    margin=ft.margin.symmetric(vertical=5),
                    content=ft.Container(
                        ref=self.user_details_area_ref,
                        padding=20,
                        content=ft.ProgressRing() # Initial loading indicator
                    )
                ),
                ft.Card(
                    elevation=1,
                    margin=ft.margin.symmetric(vertical=5),
                    content=ft.Container(pw_change_form, padding=20)
                ),
            ],
            spacing=15,
            expand=True,
            scroll=ft.ScrollMode.ADAPTIVE
        )
