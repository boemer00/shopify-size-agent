# Shopify Size Agent - Testing Guide

This guide will help you test your Shopify Size Agent to ensure everything is working correctly.

## Prerequisites

Before testing, ensure you have:

1. Completed all the steps in the `setup_guide.md`
2. Deployed the application as described in `deployment_guide.md`
3. Access to your Shopify store admin
4. Connected your phone to the Twilio WhatsApp sandbox
5. Access to the Supabase dashboard

## Testing Workflow

### 1. Verify API Endpoints

Start by verifying that your API endpoints are accessible:

1. Test the health endpoint:
   ```
   curl https://your-vercel-app.vercel.app/health
   ```
   Expected response: `{"status": "healthy"}`

2. Test the root endpoint:
   ```
   curl https://your-vercel-app.vercel.app/
   ```
   Expected response: `{"message": "Shopify Size Agent API is running"}`

### 2. Testing Locally Before Deployment

For local testing, you can use ngrok to tunnel your local development server:

1. Install ngrok:
   ```bash
   npm install -g ngrok
   ```

2. Start your FastAPI app:
   ```bash
   cd shopify-size-agent
   uvicorn app.main:app --reload
   ```

3. In another terminal, start ngrok:
   ```bash
   ngrok http 8000
   ```

4. Use the ngrok URL as your webhook URL in Shopify and Twilio.

### 3. Test Shopify Order Webhook

#### 3.1 Create a Test Order

1. Log in to your Shopify admin dashboard
2. Go to "Products" > "Add product"
3. Create a test product with size variants (S, M, L, XL)
4. Go to "Orders" > "Create order"
5. Add your test product with a specific size
6. Add a customer with a valid phone number (preferably your own)
7. Complete the order

#### 3.2 Verify Webhook Processing

After creating the order, check the following:

1. Check your application logs in Vercel:
   - Go to your Vercel dashboard > your project > "Deployments"
   - Click on the latest deployment > "Functions" > "webhook/order" > "Logs"
   - Look for any errors or success messages

2. Check Supabase data:
   - Go to your Supabase dashboard > "Table editor"
   - Check the `customers` table - your customer should be added
   - Check the `orders` table - your order should be added
   - Check the `messages` table - there should be an outbound message

### 4. Test WhatsApp Integration

#### 4.1 Receive Initial Message

After creating a test order, you should receive a WhatsApp message from the Twilio sandbox number. The message should:

1. Confirm your purchase
2. Ask if the size you selected is correct

#### 4.2 Test Conversation Flow

Test each path of the conversation:

1. **Confirm Size**:
   - Reply "Yes, that's correct" or similar
   - Expected outcome: Agent thanks you, confirms the order is proceeding for fulfillment
   - Check Supabase: order status should update to "confirmed" with size_confirmed=true

2. **Uncertain About Size**:
   - Reply "I'm not sure" or "No, I think it might be wrong"
   - Expected outcome: Agent asks about your usual size, height, weight
   - Reply with sizing information (e.g., "I usually wear L at H&M and I'm 180cm and 80kg")
   - Expected outcome: Agent recommends a size
   - Confirm or reject recommendation to test both paths

3. **Change Size**:
   - Reply "I'd like to change to size L"
   - Expected outcome: Agent confirms the change
   - Check Supabase and Shopify: order should be updated with the new size

### 5. Verify Shopify Order Updates

After completing the conversation flow:

1. Go to your Shopify admin > "Orders"
2. Find your test order and click on it
3. Check the order notes - there should be a note about size confirmation
4. Check if fulfillment was triggered (if the customer confirmed)

### 6. Check Data in Supabase

Verify all data is properly stored:

1. Check the `customers` table:
   - Customer information should be saved
   - If height/weight/usual size was provided, this should be stored

2. Check the `orders` table:
   - Order status should reflect the conversation outcome
   - `size_confirmed` should be true if confirmed
   - `confirmed_size` should contain the final size

3. Check the `messages` table:
   - All messages (inbound and outbound) should be stored
   - Each message should have the appropriate conversation phase
   - Inbound messages should have intents and entities detected

### 7. Testing Error Scenarios

Test how the system handles errors:

1. **Invalid Webhooks**:
   - Use a tool like Postman to send invalid data to your webhooks
   - Ensure proper error responses are returned

2. **Missing Phone Number**:
   - Create an order with a customer that has no phone number
   - Ensure the system handles this gracefully

3. **Server Downtime**:
   - Temporarily disable your Vercel app
   - Create an order and see if your monitoring detects the failure
   - Re-enable and check if recovery mechanisms work

### 8. Performance Testing

For a complete test, you may want to:

1. Create multiple orders in quick succession
2. Check database latency for high-volume scenarios
3. Monitor Vertex AI API quota usage
4. Check Twilio rate limiting

## Debugging Common Issues

### Webhook Verification Failures

If Shopify webhooks are failing:
- Check your SHOPIFY_WEBHOOK_SECRET value
- Ensure the raw request body is being used for verification
- Check Shopify webhook logs in your Shopify admin

### Twilio Message Failures

If WhatsApp messages aren't being sent:
- Verify your TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER
- Check if your sandbox is active
- Check Twilio logs for errors

### Vertex AI Errors

If AI responses aren't working:
- Verify your GCP credentials are correctly set up
- Check if the Vertex AI API is enabled
- Monitor quota usage in GCP console

### Database Connection Issues

If Supabase operations fail:
- Check your SUPABASE_URL and SUPABASE_KEY
- Verify your IP isn't being blocked
- Check Supabase logs for errors
