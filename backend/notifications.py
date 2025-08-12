import logging

# Configure a simple logger for this module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_email(to: str, subject: str, body: str):
    """
    Simulates sending an email by logging the details to the console.
    In a real production environment, this function would use a library like
    `smtplib` or a third-party service (e.g., SendGrid, Mailgun) to send actual emails.
    """
    logger.info("--- SIMULATING EMAIL SEND ---")
    logger.info(f"To: {to}")
    logger.info(f"Subject: {subject}")
    logger.info(f"Body: {body}")
    logger.info("--- END OF EMAIL SIMULATION ---")

    # In a real implementation, you might return True/False based on success.
    return True

# Example of a more specific notification function
def send_new_fine_notification(user_email: str, fine_details: dict):
    """
    Sends a notification to a user about a new fine.
    """
    subject = f"Nueva Multa Registrada - Placa {fine_details.get('placa')}"
    body = f"""
    Hola,

    Se ha registrado un nuevo comparendo en nuestro sistema asociado a su cuenta.

    Detalles:
    - Placa del vehículo: {fine_details.get('placa')}
    - Código de infracción: {fine_details.get('infraction_code')}
    - Fecha: {fine_details.get('date')}

    Puede ver más detalles e iniciar el proceso de pago o impugnación ingresando a nuestro portal.

    Atentamente,
    El Equipo del Portal de Movilidad
    """
    send_email(to=user_email, subject=subject, body=body)

# You could add more functions for other notification types, e.g.:
# def send_soat_expiration_reminder(...)
# def send_appointment_confirmation(...)
