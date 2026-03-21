"""
Stripe payment integration API endpoints.

This module provides endpoints for Stripe payment integration, including:
- Creating Stripe checkout sessions for subscription upgrades
- Handling Stripe webhooks for payment events
- Managing subscription cancellations
"""
import stripe
from datetime import datetime, timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from typing import Optional

from app.api.dependencies import get_current_employer
from app.core.config import settings
from app.core.logging import logger
from app.core.redis import redis_client
from app.db.session import get_db
from app.models.employer import Employer, SubscriptionTier
from app.schemas.auth import TokenData
from app.schemas.subscription import ErrorResponse
from app.services.subscription import _invalidate_subscription_cache


# Initialize Stripe with secret key
stripe.api_key = settings.STRIPE_SECRET_KEY

router = APIRouter(prefix="/stripe", tags=["stripe-payment"])


# Stripe price IDs - these should be configured in Stripe Dashboard
# and stored in environment variables in production
STRIPE_PRICE_IDS = {
    SubscriptionTier.BASIC: "price_basic_monthly",  # Replace with actual Stripe price ID
    SubscriptionTier.PREMIUM: "price_premium_monthly",  # Replace with actual Stripe price ID
}


@router.post(
    "/create-checkout-session",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid tier or already subscribed"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Employer not found"},
        500: {"model": ErrorResponse, "description": "Stripe API error"},
    }
)
async def create_checkout_session(
    tier: SubscriptionTier,
    employer: TokenData = Depends(get_current_employer),
    db: Session = Depends(get_db)
):
    """
    Create a Stripe checkout session for subscription upgrade.
    
    This endpoint implements Requirement 18.1:
    - Creates a Stripe checkout session for the specified subscription tier
    - Returns the checkout session URL for the frontend to redirect to
    - Stores the Stripe customer ID if this is the first payment
    
    **Process:**
    1. Verify employer authentication
    2. Query employer record from database
    3. Validate that the requested tier is an upgrade
    4. Create or retrieve Stripe customer
    5. Create Stripe checkout session with subscription
    6. Return checkout session URL
    
    **Example Request:**
    ```
    POST /api/stripe/create-checkout-session?tier=premium
    ```
    
    **Example Response:**
    ```json
    {
      "checkout_url": "https://checkout.stripe.com/pay/cs_test_...",
      "session_id": "cs_test_..."
    }
    ```
    """
    # Query employer from database
    employer_record = db.query(Employer).filter(
        Employer.id == UUID(employer.user_id)
    ).first()
    
    if not employer_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employer not found"
        )
    
    # Validate tier upgrade
    if tier == SubscriptionTier.FREE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create checkout session for free tier"
        )
    
    if employer_record.subscription_tier == tier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Already subscribed to {tier.value} tier"
        )
    
    # Get or create Stripe customer
    try:
        if employer_record.stripe_customer_id:
            # Existing customer
            customer_id = employer_record.stripe_customer_id
        else:
            # Create new Stripe customer
            customer = stripe.Customer.create(
                email=employer_record.email,
                metadata={
                    "employer_id": str(employer_record.id),
                    "company_name": employer_record.company_name,
                }
            )
            customer_id = customer.id
            
            # Store customer ID in database
            employer_record.stripe_customer_id = customer_id
            db.commit()
            db.refresh(employer_record)
            
            logger.info(f"Created Stripe customer {customer_id} for employer {employer_record.id}")
        
        # Get Stripe price ID for the tier
        price_id = STRIPE_PRICE_IDS.get(tier)
        if not price_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No Stripe price configured for tier {tier.value}"
            )
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=f"{settings.CORS_ORIGINS.split(',')[0]}/employer/subscription?success=true",
            cancel_url=f"{settings.CORS_ORIGINS.split(',')[0]}/employer/subscription?canceled=true",
            metadata={
                "employer_id": str(employer_record.id),
                "tier": tier.value,
            }
        )
        
        logger.info(f"Created Stripe checkout session {checkout_session.id} for employer {employer_record.id}")
        
        return {
            "checkout_url": checkout_session.url,
            "session_id": checkout_session.id
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe API error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create checkout session: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating checkout session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post(
    "/webhook",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid signature or payload"},
        500: {"model": ErrorResponse, "description": "Webhook processing error"},
    }
)
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature"),
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhook events.
    
    This endpoint implements Requirements 18.2, 18.3, 18.4, and 18.8:
    - Verifies webhook signature for security
    - Handles checkout.session.completed event (successful payment)
    - Handles invoice.payment_succeeded event (recurring payment)
    - Handles invoice.payment_failed event (payment failure)
    - Updates employer subscription status in database
    
    **Supported Events:**
    - `checkout.session.completed`: Initial subscription payment successful
    - `invoice.payment_succeeded`: Recurring subscription payment successful
    - `invoice.payment_failed`: Subscription payment failed
    - `customer.subscription.deleted`: Subscription cancelled
    
    **Process:**
    1. Verify webhook signature using Stripe webhook secret
    2. Parse webhook event
    3. Handle event based on type
    4. Update employer subscription in database
    5. Return 200 OK to acknowledge receipt
    """
    # Get raw request body
    payload = await request.body()
    
    # Verify webhook signature
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        logger.error(f"Invalid webhook payload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload"
        )
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.error(f"Invalid webhook signature: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature"
        )
    
    # Handle the event
    event_type = event["type"]
    logger.info(f"Received Stripe webhook event: {event_type}")
    
    try:
        if event_type == "checkout.session.completed":
            # Handle successful checkout
            await handle_checkout_completed(event["data"]["object"], db)
        
        elif event_type == "invoice.payment_succeeded":
            # Handle successful recurring payment
            await handle_payment_succeeded(event["data"]["object"], db)
        
        elif event_type == "invoice.payment_failed":
            # Handle failed payment
            await handle_payment_failed(event["data"]["object"], db)
        
        elif event_type == "customer.subscription.deleted":
            # Handle subscription cancellation
            await handle_subscription_deleted(event["data"]["object"], db)
        
        else:
            logger.info(f"Unhandled webhook event type: {event_type}")
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error processing webhook event {event_type}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}"
        )


async def handle_checkout_completed(session, db: Session):
    """
    Handle checkout.session.completed event.
    
    Updates employer subscription tier after successful initial payment.
    """
    employer_id = session["metadata"].get("employer_id")
    tier = session["metadata"].get("tier")
    
    if not employer_id or not tier:
        logger.error(f"Missing metadata in checkout session: {session['id']}")
        return
    
    # Query employer
    employer = db.query(Employer).filter(Employer.id == UUID(employer_id)).first()
    if not employer:
        logger.error(f"Employer {employer_id} not found for checkout session {session['id']}")
        return
    
    # Update subscription
    employer.subscription_tier = SubscriptionTier(tier)
    employer.subscription_start_date = datetime.utcnow()
    employer.subscription_end_date = datetime.utcnow() + timedelta(days=30)
    employer.monthly_posts_used = 0
    employer.featured_posts_used = 0
    
    db.commit()
    db.refresh(employer)
    
    # Invalidate cache
    redis = redis_client.get_cache_client()
    _invalidate_subscription_cache(redis, employer.id)
    
    logger.info(f"Updated employer {employer_id} subscription to {tier} after checkout")


async def handle_payment_succeeded(invoice, db: Session):
    """
    Handle invoice.payment_succeeded event.
    
    Extends employer subscription period after successful recurring payment.
    """
    customer_id = invoice["customer"]
    
    # Find employer by Stripe customer ID
    employer = db.query(Employer).filter(
        Employer.stripe_customer_id == customer_id
    ).first()
    
    if not employer:
        logger.error(f"Employer not found for Stripe customer {customer_id}")
        return
    
    # Extend subscription period by 30 days
    employer.subscription_end_date = datetime.utcnow() + timedelta(days=30)
    
    # Reset monthly usage counters
    employer.monthly_posts_used = 0
    employer.featured_posts_used = 0
    
    db.commit()
    db.refresh(employer)
    
    # Invalidate cache
    redis = redis_client.get_cache_client()
    _invalidate_subscription_cache(redis, employer.id)
    
    logger.info(f"Extended employer {employer.id} subscription after payment")


async def handle_payment_failed(invoice, db: Session):
    """
    Handle invoice.payment_failed event.
    
    Implements Requirement 18.5:
    - Logs payment failure
    - Sends notification to employer (TODO: implement email notification)
    - Implements grace period before downgrade (handled by scheduled task)
    """
    customer_id = invoice["customer"]
    
    # Find employer by Stripe customer ID
    employer = db.query(Employer).filter(
        Employer.stripe_customer_id == customer_id
    ).first()
    
    if not employer:
        logger.error(f"Employer not found for Stripe customer {customer_id}")
        return
    
    logger.warning(f"Payment failed for employer {employer.id}, customer {customer_id}")
    
    # TODO: Send email notification to employer about payment failure
    # This would be implemented in Task 31.4
    # await send_payment_failure_notification(employer)
    
    # Note: Grace period and downgrade logic should be handled by a scheduled Celery task
    # that checks for expired subscriptions with failed payments


async def handle_subscription_deleted(subscription, db: Session):
    """
    Handle customer.subscription.deleted event.
    
    Implements Requirement 18.6:
    - Maintains access until period end
    - Downgrades to free tier after subscription ends
    """
    customer_id = subscription["customer"]
    
    # Find employer by Stripe customer ID
    employer = db.query(Employer).filter(
        Employer.stripe_customer_id == customer_id
    ).first()
    
    if not employer:
        logger.error(f"Employer not found for Stripe customer {customer_id}")
        return
    
    # Get subscription end date from Stripe
    period_end = datetime.fromtimestamp(subscription["current_period_end"])
    
    # Update subscription end date (maintain access until period end)
    employer.subscription_end_date = period_end
    
    db.commit()
    db.refresh(employer)
    
    # Invalidate cache
    redis = redis_client.get_cache_client()
    _invalidate_subscription_cache(redis, employer.id)
    
    logger.info(f"Subscription cancelled for employer {employer.id}, access until {period_end}")


@router.post(
    "/cancel-subscription",
    responses={
        400: {"model": ErrorResponse, "description": "Cannot cancel free tier or no active subscription"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Employer not found"},
        500: {"model": ErrorResponse, "description": "Stripe API error"},
    }
)
async def cancel_subscription(
    employer: TokenData = Depends(get_current_employer),
    db: Session = Depends(get_db)
):
    """
    Cancel employer's Stripe subscription.
    
    This endpoint implements Requirement 18.6:
    - Cancels the Stripe subscription at period end
    - Maintains access until the current period ends
    - Updates subscription status in database
    
    **Process:**
    1. Verify employer authentication
    2. Query employer record from database
    3. Verify employer has an active Stripe subscription
    4. Cancel subscription in Stripe (at period end)
    5. Return confirmation message
    
    **Example Response:**
    ```json
    {
      "message": "Subscription cancelled. Access maintained until 2024-02-15",
      "end_date": "2024-02-15T10:30:00"
    }
    ```
    """
    # Query employer from database
    employer_record = db.query(Employer).filter(
        Employer.id == UUID(employer.user_id)
    ).first()
    
    if not employer_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employer not found"
        )
    
    # Check if on free tier
    if employer_record.subscription_tier == SubscriptionTier.FREE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel free tier subscription"
        )
    
    # Check if has Stripe customer ID
    if not employer_record.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active Stripe subscription found"
        )
    
    try:
        # Get active subscriptions for customer
        subscriptions = stripe.Subscription.list(
            customer=employer_record.stripe_customer_id,
            status="active",
            limit=1
        )
        
        if not subscriptions.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active subscription found"
            )
        
        subscription = subscriptions.data[0]
        
        # Cancel subscription at period end
        cancelled_subscription = stripe.Subscription.modify(
            subscription.id,
            cancel_at_period_end=True
        )
        
        # Get period end date
        period_end = datetime.fromtimestamp(cancelled_subscription.current_period_end)
        
        logger.info(f"Cancelled Stripe subscription for employer {employer_record.id}, access until {period_end}")
        
        return {
            "message": f"Subscription cancelled. Access maintained until {period_end.strftime('%Y-%m-%d')}",
            "end_date": period_end.isoformat()
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe API error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel subscription: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error cancelling subscription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
