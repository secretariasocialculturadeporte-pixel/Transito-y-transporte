import flet as ft
from api_client import ApiClient, APIError
from models import LoginResponseData
from views.auth.login_view import LoginView
from views.common.my_account_view import MyAccountView
from views.citizen.citizen_content_view import CitizenContentView
from views.admin.admin_view import AdminView
from app_data import _t

async def main(page: ft.Page):
    # --- App Setup ---
    page.title = _t("app_title")
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 500
    page.window_height = 720
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # --- Dependency Injection ---
    # Instantiate the ApiClient, which will be shared across views
    api = ApiClient()

    # --- App State / Session Management ---
    async def on_login_success(login_data: LoginResponseData):
        """Callback executed after a successful login."""
        # Store session token and user info securely
        await page.client_storage.set_async("session.token", login_data.access_token)
        await page.client_storage.set_async("session.user_info", login_data.user_info.dict())
        page.window_width = 1000
        page.window_height = 800
        await page.go_async("/")

    async def logout(e):
        """Clears session and navigates to the login page."""
        await page.client_storage.clear_async()
        page.window_width = 500
        page.window_height = 720
        await page.go_async("/login")

    # --- Routing ---
    async def route_change(route):
        """Handles routing for the entire application."""
        print(f"Route changed to: {page.route}")
        page.views.clear()

        # Check for session to protect routes
        session_token = await page.client_storage.get_async("session.token")
        user_info_dict = await page.client_storage.get_async("session.user_info") or {}

        # Universal AppBar for logged-in users
        appbar = ft.AppBar(
            title=ft.Text(_t("app_title")),
            actions=[
                ft.PopupMenuButton(
                    items=[
                        ft.PopupMenuItem(
                            text=_t("my_account"),
                            icon=ft.icons.PERSON,
                            on_click=lambda _: page.go_async("/account")
                        ),
                        # Conditionally add Admin link
                        ft.PopupMenuItem(
                            text="Admin Panel",
                            icon=ft.icons.ADMIN_PANEL_SETTINGS,
                            on_click=lambda _: page.go_async("/admin"),
                            visible=(user_info_dict.get("role") in ["Admin Municipal", "SuperAdmin"])
                        ),
                        ft.PopupMenuItem(
                            text=_t("logout_button"),
                            icon=ft.icons.EXIT_TO_APP,
                            on_click=logout
                        )
                    ]
                )
            ]
        )

        if page.route == "/login":
            page.views.append(
                ft.View(
                    route="/login",
                    controls=[
                        LoginView(api_client=api, on_login_success=on_login_success)
                    ],
                    vertical_alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )
        # All other routes require a session
        elif session_token:
            if page.route == "/":
                # Placeholder for the main citizen view
                username = user_info_dict.get('username', 'N/A')
                appbar.leading = ft.Icon(ft.icons.HOME)
                appbar.title = ft.Text(_t("citizen_portal"))
                page.views.append(
                    ft.View(
                        route="/",
                        appbar=appbar,
                        controls=[
                            CitizenContentView(api_client=api, user_info=user_info_dict)
                        ]
                    )
                )
            elif page.route == "/account":
                appbar.leading = ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: page.go_async("/"))
                appbar.title = ft.Text(_t("my_account"))
                page.views.append(
                    ft.View(
                        route="/account",
                        appbar=appbar,
                        controls=[MyAccountView(api_client=api, user_info=user_info_dict)],
                        scroll=ft.ScrollMode.ADAPTIVE
                    )
                )
            elif page.route == "/admin":
                appbar.leading = ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda _: page.go_async("/"))
                appbar.title = ft.Text("Admin Panel")
                if user_info_dict.get("role") in ["Admin Municipal", "SuperAdmin"]:
                    page.views.append(
                        ft.View(
                            route="/admin",
                            appbar=appbar,
                            controls=[AdminView(api_client=api, user_info=user_info_dict)]
                        )
                    )
                else:
                    # If a non-admin tries to access, redirect or show error
                    page.views.append(
                        ft.View(
                            route="/",
                            appbar=appbar,
                            controls=[ft.Text("Access Denied. You are not an admin.")]
                        )
                    )
        else:
            # If no session and not on /login, redirect to login
            print("No session found, redirecting to /login")
            await page.go_async("/login")

        await page.update_async()

    page.on_route_change = route_change

    # --- Initial Route ---
    # Start the app by navigating to the root, which will redirect to /login if needed
    await page.go_async("/")

# To run the app
if __name__ == "__main__":
    # PWA Manifest Configuration
    pwa_manifest = ft.PWAManifest(
        name="Portal de Movilidad",
        short_name="Movilidad",
        description="Una aplicación para gestionar trámites y multas de tránsito.",
        start_url="/",
        display=ft.AppView.STANDALONE,
        background_color="#ffffff",
        theme_color="#006400",
        icons=[
            ft.WebAppManifestIcon(src="/icons/icon-192.png", sizes="192x192"),
            ft.WebAppManifestIcon(src="/icons/icon-512.png", sizes="512x512"),
        ],
    )

    ft.app(
        target=main,
        assets_dir="assets",
        pwa_manifest=pwa_manifest
    )
