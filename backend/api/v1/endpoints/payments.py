from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date, timedelta

from .... import crud, models_db
from ..auth import get_current_user, get_db

router = APIRouter()

# --- Pydantic Schemas for Payments ---

class CreateCheckoutSessionRequest(BaseModel):
    plan_id: str # e.g., "profesional_mensual" or "profesional_anual"

class CreateFineCheckoutSessionRequest(BaseModel):
    fine_id: int

class CreateCheckoutSessionResponse(BaseModel):
    checkout_url: str

# --- Payment Endpoints ---

@router.post(
    "/create-checkout-session",
    response_model=CreateCheckoutSessionResponse,
    summary="Create a new payment checkout session"
)
async def create_checkout_session(
    request_data: CreateCheckoutSessionRequest,
    db: Session = Depends(get_db),
    current_user: models_db.User = Depends(get_current_user)
):
    """
    This endpoint simulates creating a checkout session with a payment provider.
    In a real application, this would involve:
    1. Calling the payment provider's API (e.g., Stripe, PayU) with plan details.
    2. Getting a unique session ID and checkout URL from the provider.
    3. Storing the session ID to verify against the webhook later.
    """
    # For this simulation, we'll just generate a redirect URL to our own success page.
    # We'll pass the plan and user info in the URL query params for the success page to use.

    # Basic validation
    if request_data.plan_id not in ["profesional_mensual", "profesional_anual"]:
        raise HTTPException(status_code=400, detail="Invalid plan_id")

    # The success URL will trigger the webhook simulation
    # In a real app, this would be the URL the payment provider redirects to.
    success_url = f"/payment_success.html?plan_id={request_data.plan_id}&entidad_id={current_user.entidad_id}"

    return CreateCheckoutSessionResponse(checkout_url=success_url)

@router.post(
    "/create-fine-checkout-session",
    response_model=CreateCheckoutSessionResponse,
    summary="Create a checkout session for a specific fine"
)
async def create_fine_checkout_session(
    request_data: CreateFineCheckoutSessionRequest,
    db: Session = Depends(get_db),
    current_user: models_db.User = Depends(get_current_user)
):
    """
    Simulates creating a checkout session for a citizen to pay a specific fine.
    """
    fine = crud.get_fine_by_id(db, fine_id=request_data.fine_id)

    # Validation
    if not fine:
        raise HTTPException(status_code=404, detail="Fine not found.")
    if fine.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only pay your own fines.")
    if fine.status == "Pagado":
        raise HTTPException(status_code=400, detail="This fine has already been paid.")

    success_url = f"/payment_success.html?type=fine&fine_id={fine.id}"

    return CreateCheckoutSessionResponse(checkout_url=success_url)


@router.post("/webhook", summary="Handle payment provider webhooks")
async def handle_payment_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    This endpoint simulates receiving a webhook from a payment provider after a successful payment.
    In a real application, this endpoint would need to be publicly accessible and should be secured
    by verifying a signature header from the provider.
    """
    try:
        # For this simulation, we expect the client to send the data directly.
        # In a real webhook, you would parse the provider's specific event payload.
        payload = await request.json()
        event_type = payload.get("event_type")

        if event_type == "subscription_payment_succeeded":
            entidad_id = payload.get("entidad_id")
            plan_id = payload.get("plan_id")

            if not all([entidad_id, plan_id]):
                raise HTTPException(status_code=400, detail="Missing entidad_id or plan_id in subscription webhook payload")

            # Determine subscription duration
            start_date = date.today()
            if plan_id == "profesional_anual":
                end_date = start_date + timedelta(days=365)
            else: # "profesional_mensual"
                end_date = start_date + timedelta(days=30)

            # Create the subscription in the database
            crud.create_subscription(
                db=db,
                entidad_id=entidad_id,
                plan_name=plan_id,
                start_date=start_date,
                end_date=end_date
            )
            print(f"Subscription created for entity {entidad_id} for plan {plan_id}")
            return {"status": "success", "message": "Webhook processed and subscription created."}

        elif event_type == "fine_payment_succeeded":
            fine_id = payload.get("fine_id")
            if not fine_id:
                raise HTTPException(status_code=400, detail="Missing fine_id in fine payment webhook payload")

            # Update the fine status in the database
            crud.update_fine_status(db=db, fine_id=fine_id, new_status="Pagado")
            print(f"Fine {fine_id} marked as paid.")
            return {"status": "success", "message": "Webhook processed and fine status updated."}

        return {"status": "ignored", "message": f"Event type '{event_type}' not handled."}

    except Exception as e:
        print(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error processing webhook.")
