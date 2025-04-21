# Shopify Size Agent - Architecture Overview

## High-Level Architecture

The Shopify Size Agent is a serverless application that enables post-purchase size confirmation via WhatsApp. The system connects Shopify with customers through WhatsApp, using AI to guide the conversation and update order information.

```
                                 ┌───────────────┐
                                 │               │
                                 │    Shopify    │
                                 │    Store      │
                                 │               │
                                 └───────┬───────┘
                                         │
                                         │ Order Webhook
                                         ▼
┌───────────────┐              ┌───────────────────┐              ┌───────────────┐
│               │              │                   │              │               │
│   Supabase    │◄─────────────┤   FastAPI App     │─────────────►│  Vertex AI    │
│   Database    │              │   (on Vercel)     │              │   (GCP)       │
│               │              │                   │              │               │
└───────────────┘              └─────────┬─────────┘              └───────────────┘
                                         │
                                         │ WhatsApp API
                                         ▼
                               ┌───────────────────┐
                               │                   │
                               │      Twilio       │
                               │   (WhatsApp API)  │
                               │                   │
                               └─────────┬─────────┘
                                         │
                                         │
                                         ▼
                               ┌───────────────────┐
                               │                   │
                               │     Customer      │
                               │    (WhatsApp)     │
                               │                   │
                               └───────────────────┘
```

## Components and Data Flow

### 1. Shopify Integration
- **Trigger**: Order creation webhook from Shopify
- **Flow**: When a customer completes checkout, Shopify sends an order webhook to our FastAPI endpoint
- **Action**: The app extracts order and customer information, stores it in Supabase, and initiates the WhatsApp conversation

### 2. FastAPI Application
- **Endpoints**:
  - `/webhook/order`: Receives Shopify order webhooks
  - `/webhook/reply`: Receives Twilio WhatsApp message webhooks
- **Services**:
  - `ShopifyService`: Handles Shopify API operations
  - `TwilioService`: Manages WhatsApp messaging
  - `VertexAIService`: Manages AI conversation
  - `SupabaseService`: Handles database operations
  - `ConversationService`: Manages conversation flow
- **Deployment**: Serverless on Vercel

### 3. WhatsApp Integration via Twilio
- **Outbound**: Send initial message to customer after purchase
- **Inbound**: Receive and process customer responses
- **Flow**: Messages pass through Twilio to our webhook, processed by the conversation service

### 4. AI Conversation Flow with Vertex AI
- **Model**: chat-bison on Google Cloud Vertex AI
- **Functions**:
  - Intent detection
  - Size recommendation
  - Natural conversation management
- **Phases**:
  1. Confirmation: "Are you sure Medium is right for you?"
  2. Sizing Questions: "What's your usual size at Zara/H&M? What's your height/weight?"
  3. Recommendation: "Based on your info, we recommend size Large"
  4. Completion: Update order and trigger fulfillment

### 5. Data Storage with Supabase
- **Tables**:
  - `customers`: Store customer info including sizing preferences
  - `orders`: Track order details and sizing confirmation status
  - `messages`: Log all conversation messages with intent detection

### 6. Shopify Order Update
- After size confirmation, update the order in Shopify
- Add confirmed size as order note and/or metadata
- Trigger order fulfillment

## Implementation Notes

- **Serverless Architecture**: The entire application runs as serverless functions on Vercel
- **Stateless Design**: All state is stored in Supabase, allowing scaling without maintaining server state
- **Webhook Verification**: All webhooks use proper signature verification for security
- **Error Handling**: Robust error handling with failsafes to prevent lost messages
- **Monitoring**: Health endpoint for monitoring

## Future Extensions

- Integration with customer purchase history
- Support for multiple products in a single order
- A/B testing of different conversation flows
- Admin dashboard for monitoring conversations
