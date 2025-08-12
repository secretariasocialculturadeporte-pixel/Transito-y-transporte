from fastapi import APIRouter, Depends
from models import ChatMessageInput, ChatResponse, ChatMessageOutput, UserInDB, ConversationContext, ChatMode
from .auth import get_current_user
import re

router = APIRouter()

@router.post("/", response_model=ChatResponse, summary="Process a chat message")
async def handle_chat(
    chat_input: ChatMessageInput,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Handles incoming chat messages with basic stateful conversation logic.
    """
    user_message = chat_input.message.lower()
    context = chat_input.context or ConversationContext()

    response_text = f"No he entendido tu solicitud. ¿Puedes reformularla?"

    # --- Simple Intent & State Logic ---

    # State 1: Waiting for a license plate after asking for it
    if context.current_mode == ChatMode.AWAITING_CLARIFICATION and context.last_intent == "check_fines":
        # Assume the message is the license plate. Basic validation.
        placa_match = re.match(r"^[a-zA-Z]{3}\s?\d{3}$", user_message.upper())
        if placa_match:
            placa = user_message.upper().replace(" ", "")
            # In a real app, here you would query the database for fines.
            response_text = f"He verificado la placa {placa}. Por ahora, no he encontrado multas pendientes. (Función en desarrollo)."
            # Reset context to be ready for a new conversation
            context = ConversationContext()
        else:
            response_text = "No parece ser un número de placa válido. Por favor, introduce una placa en formato AAA123."
            # We keep the context as is, to give the user another chance.

    # State 0: Default conversational mode
    else:
        # Simple keyword-based intent detection
        if any(keyword in user_message for keyword in ["multas", "comparende", "infracciones"]):
            context.current_mode = ChatMode.AWAITING_CLARIFICATION
            context.last_intent = "check_fines"
            context.history.append(user_message)
            response_text = "Con gusto. Por favor, indícame el número de placa que deseas consultar."
        elif any(keyword in user_message for keyword in ["hola", "buenos dias", "buenas tardes"]):
            response_text = f"Hola {current_user.full_name or current_user.username}, ¿en qué puedo ayudarte hoy?"
        # Add more intent detections here...

    # Create the output data model with the updated context
    output_data = ChatMessageOutput(
        response_text=response_text,
        new_context=context
    )

    # Return the standard API response
    return ChatResponse(
        success=True,
        message="Respuesta generada.",
        data=output_data
    )
