# Stripe Payment Integration - Quick Reference Guide

## Overview
This guide provides instructions for setting up and using the Stripe payment integration for subscription management.

## Prerequisites
- Stripe account (create at https://stripe.com)
- Stripe API keys (test and live)
- Webhook endpoint configured in Stripe Dashboard

## Setup Instructions

### 1. Stripe Account Setup

1. **Create Stripe Account:**
   - Go to https://stripe.com and sign up
   - Complete account verification
   - Enable test mode for development

2. **Get API Keys:**
   - Navigate to Developers > API keys
   - Copy the following keys:
     - Publishable key (starts with `pk_test_` or `pk_live_`)
     - Secret key (starts with `sk_test_` or `sk_live_`)

3. **Create Products and Prices:**
   - Navigate to Products > Add product
   - Create two products:
     
     **Basic Plan:**
     - Name: "Basic Plan"
     - Description: "20 job posts per month, 2 featured listings, application tracking"
     - Pricing: $49/month (recurring)
     - Copy the Price ID (starts with `price_`)
     
     **Premium Plan:**
     - Name: "Premium Plan"
     - Description: "Unlimited job posts, 10 featured listings, analytics"
     - Pricing: $149/month (recurring)
     - Copy the Price ID (starts with `price_`)

4. **Configure Webhook:**
   - Navigate to Developers > Webhooks
   - Click "Add endpoint"
   - Endpoint URL: `https://your-domain.com/api/stripe/webhook`
   - Select events to listen for:
     - `checkout.session.completed`
     - `invoice.payment_succeeded`
     - `invoice.payment_failed`
     - `customer.subscription.deleted`
   - Copy the Webhook signing secret (starts with `whsec_`)

### 2. Environment Configuration

Update your `.env` file with the Stripe keys:

```bash
# Stripe Payment
STRIPE_SECRET_KEY=sk_test_your_actual_secret_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_actual_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_actual_webhook_secret
```

### 3. Code Configuration

Update the price IDs in `backend/app/api/stripe_payment.py`:

```python
STRIPE_PRICE_IDS = {
    SubscriptionTier.BASIC: "price_your_basic_price_id",
    SubscriptionTier.PREMIUM: "price_your_premium_price_id",
}
```

### 4. Frontend Configuration

Update `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_actual_publishable_key
```

## API Endpoints

### 1. Create Checkout Session
**Endpoint:** `POST /api/stripe/create-checkout-session?tier={tier}`

**Description:** Creates a Stripe checkout session for subscription upgrade.

**Authentication:** Required (Bearer token)

**Parameters:**
- `tier` (query): Subscription tier (`basic` or `premium`)

**Response:**
```json
{
  "checkout_url": "https://checkout.stripe.com/pay/cs_test_...",
  "session_id": "cs_test_..."
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/stripe/create-checkout-session?tier=premium" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 2. Webhook Handler
**Endpoint:** `POST /api/stripe/webhook`

**Description:** Handles Stripe webhook events.

**Authentication:** None (signature-protected)

**Headers:**
- `stripe-signature`: Webhook signature from Stripe

**Events Handled:**
- `checkout.session.completed`: Updates subscription after initial payment
- `invoice.payment_succeeded`: Extends subscription for recurring payment
- `invoice.payment_failed`: Logs failure and triggers notification
- `customer.subscription.deleted`: Maintains access until period end

**Response:**
```json
{
  "status": "success"
}
```

### 3. Cancel Subscription
**Endpoint:** `POST /api/stripe/cancel-subscription`

**Description:** Cancels the employer's Stripe subscription.

**Authentication:** Required (Bearer token)

**Response:**
```json
{
  "message": "Subscription cancelled. Access maintained until 2024-02-15",
  "end_date": "2024-02-15T10:30:00"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/stripe/cancel-subscription" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Testing

### Local Testing with Stripe CLI

1. **Install Stripe CLI:**
   ```bash
   # macOS
   brew install stripe/stripe-cli/stripe
   
   # Linux
   wget https://github.com/stripe/stripe-cli/releases/download/v1.19.0/stripe_1.19.0_linux_x86_64.tar.gz
   tar -xvf stripe_1.19.0_linux_x86_64.tar.gz
   ```

2. **Login to Stripe:**
   ```bash
   stripe login
   ```

3. **Forward Webhooks to Local Server:**
   ```bash
   stripe listen --forward-to localhost:8000/api/stripe/webhook
   ```
   
   This will output a webhook signing secret. Update your `.env` file with this secret.

4. **Trigger Test Events:**
   ```bash
   # Test successful checkout
   stripe trigger checkout.session.completed
   
   # Test successful payment
   stripe trigger invoice.payment_succeeded
   
   # Test failed payment
   stripe trigger invoice.payment_failed
   
   # Test subscription cancellation
   stripe trigger customer.subscription.deleted
   ```

### Test Cards

Use these test card numbers in Stripe checkout:

**Successful Payment:**
- Card: `4242 4242 4242 4242`
- Expiry: Any future date
- CVC: Any 3 digits
- ZIP: Any 5 digits

**Payment Failure:**
- Card: `4000 0000 0000 0341`
- Expiry: Any future date
- CVC: Any 3 digits
- ZIP: Any 5 digits

**Requires Authentication (3D Secure):**
- Card: `4000 0025 0000 3155`
- Expiry: Any future date
- CVC: Any 3 digits
- ZIP: Any 5 digits

### Manual Testing Flow

1. **Test Subscription Upgrade:**
   - Login as employer (free tier)
   - Navigate to `/employer/subscription`
   - Click "Upgrade to Basic" or "Upgrade to Premium"
   - Complete Stripe checkout with test card
   - Verify redirect to success page
   - Check database: `subscription_tier` should be updated
   - Check logs for webhook processing

2. **Test Recurring Payment:**
   - Wait for next billing cycle (or trigger webhook manually)
   - Verify `subscription_end_date` extended by 30 days
   - Verify usage counters reset to 0

3. **Test Payment Failure:**
   - Use failing test card for subscription
   - Verify payment failure logged
   - Verify notification task triggered
   - Check that subscription remains active (grace period)
   - Wait for `subscription_end_date` to pass
   - Verify automatic downgrade to free tier

4. **Test Subscription Cancellation:**
   - Login as employer with paid subscription
   - Navigate to `/employer/subscription`
   - Click "Cancel Subscription"
   - Confirm cancellation
   - Verify message shows access until period end
   - Verify Stripe subscription marked for cancellation
   - Wait for period end
   - Verify automatic downgrade to free tier

## Monitoring and Debugging

### Check Webhook Logs

**Stripe Dashboard:**
- Navigate to Developers > Webhooks
- Click on your webhook endpoint
- View "Recent events" to see webhook deliveries
- Check for failed deliveries and retry them

**Application Logs:**
```bash
# View webhook processing logs
tail -f logs/app.log | grep "Stripe webhook"

# View payment processing logs
tail -f logs/app.log | grep "payment"
```

### Common Issues

**Issue: Webhook signature verification fails**
- **Cause:** Incorrect `STRIPE_WEBHOOK_SECRET`
- **Solution:** Copy the correct webhook secret from Stripe Dashboard

**Issue: Checkout session creation fails**
- **Cause:** Invalid price ID or Stripe API key
- **Solution:** Verify price IDs in code match Stripe Dashboard

**Issue: Subscription not updated after payment**
- **Cause:** Webhook not received or failed
- **Solution:** Check webhook logs in Stripe Dashboard, retry failed webhooks

**Issue: Payment failure not triggering notification**
- **Cause:** Email service not configured
- **Solution:** Configure SMTP settings in `.env` file

## Production Deployment

### Pre-Deployment Checklist

- [ ] Replace test API keys with live keys
- [ ] Update webhook endpoint URL to production domain
- [ ] Configure webhook secret for production
- [ ] Update price IDs to production prices
- [ ] Test webhook delivery to production endpoint
- [ ] Configure email service for notifications
- [ ] Set up monitoring for payment failures
- [ ] Enable Stripe Radar for fraud prevention
- [ ] Review Stripe Dashboard settings

### Security Best Practices

1. **Never commit API keys to version control**
   - Use environment variables
   - Add `.env` to `.gitignore`

2. **Always verify webhook signatures**
   - Already implemented in code
   - Never skip signature verification

3. **Use HTTPS in production**
   - Required for webhook endpoints
   - Stripe will not send webhooks to HTTP endpoints

4. **Monitor for suspicious activity**
   - Enable Stripe Radar
   - Set up alerts for unusual patterns
   - Review failed payments regularly

5. **Handle PCI compliance**
   - Never store credit card numbers
   - Use Stripe.js for card collection
   - Let Stripe handle all payment data

## Troubleshooting

### Webhook Not Received

1. Check webhook endpoint is accessible:
   ```bash
   curl -X POST https://your-domain.com/api/stripe/webhook \
     -H "Content-Type: application/json" \
     -d '{"test": true}'
   ```

2. Check Stripe Dashboard for failed deliveries

3. Verify webhook secret is correct

4. Check firewall/security group settings

### Payment Not Processing

1. Check Stripe Dashboard > Payments for payment status

2. Review application logs for errors

3. Verify API keys are correct

4. Check customer has valid payment method

### Subscription Not Updating

1. Check webhook was received and processed

2. Review database for subscription updates

3. Check Redis cache was invalidated

4. Verify employer record exists

## Support

**Stripe Documentation:**
- https://stripe.com/docs

**Stripe Support:**
- https://support.stripe.com

**Application Support:**
- Check application logs
- Review error messages in Stripe Dashboard
- Contact development team

## Additional Resources

- [Stripe Testing Guide](https://stripe.com/docs/testing)
- [Stripe Webhooks Guide](https://stripe.com/docs/webhooks)
- [Stripe Subscriptions Guide](https://stripe.com/docs/billing/subscriptions/overview)
- [Stripe Security Best Practices](https://stripe.com/docs/security/guide)
