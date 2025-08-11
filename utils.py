import flet as ft
from typing import Optional, List, Callable

# Import APIError safely to avoid circular dependencies if utils is imported by api_client
# This is a common pattern in Python applications.
try:
    from api_client import APIError
except ImportError:
    # Define a dummy class if api_client is not available at import time.
    # The type hint 'APIError' will still work.
    class APIError(Exception):
        def __init__(self, message: str, status_code: int = 500, detail: any = None):
            self.message = message
            self.status_code = status_code
            self.detail = detail

from app_data import _t

async def show_snackbar_async(page: ft.Page, message: str, color: str = ft.colors.RED, duration: int = 4000):
    """Safely shows a SnackBar on the page."""
    if not page:
        return
    page.snack_bar = ft.SnackBar(
        content=ft.Text(message),
        bgcolor=color,
        duration=duration
    )
    page.snack_bar.open = True
    await page.update_async()


async def handle_api_error(
    page: ft.Page,
    e: Exception,
    context_key: str,
    retry_callback: Optional[Callable] = None
):
    """
    A centralized handler for API errors to display user-friendly feedback.

    Args:
        page: The Flet Page object to display the SnackBar on.
        e: The exception that was caught.
        context_key: A key to provide context for the error message (e.g., "login", "load_fines").
        retry_callback: An optional async function to call when a "Retry" action is clicked.
    """
    if not page:
        print(f"Error occurred but page context was not available. Context: {context_key}, Error: {e}")
        return

    error_title = _t(f"error.title.{context_key}", default=_t("error", "Error"))
    error_message = _t("internal_error")
    error_color = page.theme.color_scheme.error if page.theme else ft.colors.RED

    if isinstance(e, APIError):
        # Handle specific API errors
        status = e.status_code
        if status == 401:
            error_message = _t("error.unauthorized_expired")
            # In a real app, you might trigger a logout sequence here.
            # Example: await logout_user(page)
        elif status == 403:
            error_message = _t("error.forbidden")
        elif status == 404:
            error_message = _t("error.not_found")
        elif status == 409:
            error_message = _t("error.conflict", default=e.message)
            error_color = page.theme.color_scheme.secondary if page.theme else ft.colors.ORANGE
        elif status == 422 and e.detail and isinstance(e.detail, list):
            # Pydantic validation errors
            error_message = _t("error.validation_failed_api_summary")
            # For a SnackBar, we might not show all details, but we could log them.
            print(f"Validation errors: {e.detail}")
        else:
            # Generic API error from the client's message
            error_message = e.message
    else:
        # Generic Python exception
        error_message = f"{_t('internal_error')}: {e}"
        print(f"An unexpected error occurred in context '{context_key}': {e}")

    # Prepare SnackBar
    page.snack_bar = ft.SnackBar(
        content=ft.Row(
            [
                ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color=ft.colors.WHITE),
                ft.Column([
                    ft.Text(error_title, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                    ft.Text(error_message, color=ft.colors.WHITE),
                ])
            ]
        ),
        bgcolor=error_color,
        duration=5000,
        action=_t("retry") if retry_callback else _t("close"),
        on_action= (lambda _: retry_callback()) if retry_callback else None
    )
    page.snack_bar.open = True
    await page.update_async()
