import flet as ft
from api_client import ApiClient, APIError
from models import ConversationContext
import speech_recognition as sr
import threading

class ChatMessage(ft.Row):
    """A chat message with a user icon and text."""
    def __init__(self, message: str, is_user: bool):
        super().__init__()
        self.vertical_alignment = ft.CrossAxisAlignment.START
        self.controls = [
            ft.Icon(
                name=ft.icons.PERSON if is_user else ft.icons.ASSISTANT,
                size=30,
                color=ft.colors.BLUE_GREY_200 if is_user else ft.colors.CYAN_200,
            ),
            ft.Column([
                ft.Text(
                    "Tú" if is_user else "Asistente IA",
                    weight=ft.FontWeight.BOLD
                ),
                ft.Text(message, selectable=True, width=500),
            ]),
        ]

class ChatView(ft.UserControl):
    def __init__(self, api_client: ApiClient, user_info: dict):
        super().__init__()
        self.api_client = api_client
        self.user_info = user_info
        self.context = ConversationContext() # Manages conversation state

        # UI Controls
        self.chat_list = ft.Ref[ft.ListView]()
        self.message_field = ft.Ref[ft.TextField]()
        self.send_button = ft.Ref[ft.IconButton]()
        self.mic_button = ft.Ref[ft.IconButton]()
        self.status_text = ft.Ref[ft.Text]()
        self.recognizer = sr.Recognizer()
        self.is_listening = threading.Event()

    async def did_mount_async(self):
        # Add a personalized, proactive welcome message
        user_name = self.user_info.get('full_name', 'usuario').split(' ')[0]
        entidad_id = self.user_info.get('entidad_id', 'tu entidad')

        welcome_message = f"Buenos días, {user_name}. En nombre de la secretaría de tránsito de la entidad {entidad_id}, te damos la bienvenida. ¿En qué podemos ayudarte hoy?"

        self.add_message(welcome_message, is_user=False)
        await self.update_async()

    def add_message(self, message: str, is_user: bool):
        """Adds a message to the chat list."""
        self.chat_list.current.controls.append(ChatMessage(message, is_user))

    async def send_message_click(self, e):
        """Handles the send button click event."""
        user_message = self.message_field.current.value
        if not user_message:
            return

        # Disable input while processing
        self.message_field.current.value = ""
        self.message_field.current.disabled = True
        self.send_button.current.disabled = True
        await self.update_async()

        # Add user message to UI
        self.add_message(user_message, is_user=True)

        # Add a thinking indicator
        thinking_indicator = ChatMessage("...", is_user=False)
        self.chat_list.current.controls.append(thinking_indicator)
        await self.update_async()

        try:
            # Send message to API and get response
            response_data = await self.api_client.send_chat_message(
                message=user_message,
                context=self.context.dict()
            )

            # Extract data from response
            output_data = response_data.get("data", {})
            ai_response = output_data.get("response_text", "No he podido obtener una respuesta.")
            new_context_dict = output_data.get("new_context")

            # Update local context if the server sent a new one back
            if new_context_dict:
                self.context = ConversationContext.parse_obj(new_context_dict)

            # Replace "thinking" message with the actual response
            thinking_indicator.controls[1].controls[1].value = ai_response

        except APIError as ex:
            thinking_indicator.controls[1].controls[1].value = f"Error de API: {ex.message}"
            thinking_indicator.controls[1].controls[1].color = ft.colors.RED
        except Exception as ex:
            thinking_indicator.controls[1].controls[1].value = f"Ha ocurrido un error inesperado: {ex}"
            thinking_indicator.controls[1].controls[1].color = ft.colors.RED
        finally:
            # Re-enable input
            self.message_field.current.disabled = False
            self.send_button.current.disabled = False
            await self.update_async()
            self.page.update() # Ensure UI updates are flushed

    def build(self):
        return ft.Column(
            [
                ft.Text("Chat con Asistente IA", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                ft.Container(
                    content=ft.ListView(
                        ref=self.chat_list,
                        expand=True,
                        spacing=10,
                        auto_scroll=True,
                    ),
                    border=ft.border.all(1, ft.colors.OUTLINE),
                    border_radius=ft.border_radius.all(5),
                    padding=10,
                    expand=True,
                ),
                ft.Row(
                    [
                        ft.TextField(
                            ref=self.message_field,
                            hint_text="Escribe tu mensaje...",
                            expand=True,
                            on_submit=self.send_message_click,
                        ),
                        ft.IconButton(
                            ref=self.send_button,
                            icon=ft.icons.SEND,
                            tooltip="Enviar Mensaje",
                            on_click=self.send_message_click,
                        ),
                    ],
                ),
            ],
            expand=True,
        )
