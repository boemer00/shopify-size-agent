# Shopify Size Agent

A post-purchase sizing-confirmation agent for Shopify that uses WhatsApp to confirm customer sizes, provide recommendations, and update orders.

## Overview

This project implements a complete MVP of a post-purchase size-confirmation agent for Shopify that:

1. Immediately after checkout sends a WhatsApp message to the customer to confirm their purchased size
2. Guides a short conversational flow ("Are you sure Medium is right? What's your usual size at Zara/H&M? What's your height/weight?")
3. Parses customer replies, confirms or suggests a new size, and loops until the customer says "OK"
4. Automatically updates the Shopify order (note or line item) to the confirmed size and triggers Shopify fulfillment
5. Stores every inbound and outbound message, plus AI-detected intent, in Supabase for future analysis

## Tech Stack

- **Python**: Core programming language
- **FastAPI**: API framework for webhooks
- **Supabase**: Database for storing orders, customers, and messages
- **Twilio**: WhatsApp API integration
- **Vertex AI**: Chat-bison model for conversational AI
- **Shopify API**: Order management and fulfillment
- **Vercel**: Serverless deployment

## Project Structure

```
shopify-size-agent/
├── app/
│   ├── api/
│   │   ├── shopify_webhook.py   # Shopify webhook endpoints
│   │   └── twilio_webhook.py    # Twilio WhatsApp endpoints
│   ├── models/
│   │   ├── customer.py          # Customer data models
│   │   ├── message.py           # Message data models
│   │   └── order.py             # Order data models
│   ├── services/
│   │   ├── conversation_service.py  # Conversation management
│   │   ├── shopify_service.py    # Shopify API interactions
│   │   ├── supabase_service.py   # Database operations
│   │   ├── twilio_service.py     # WhatsApp messaging
│   │   └── vertex_ai_service.py  # AI conversation
│   ├── utils/
│   │   ├── hmac_verification.py  # Webhook verification
│   │   └── state_machine.py      # Conversation state management
│   ├── __init__.py
│   └── main.py                   # FastAPI app entry point
├── docs/
│   ├── architecture.md           # Architecture overview
│   ├── setup_guide.md            # Service setup instructions
│   ├── deployment_guide.md       # Vercel deployment guide
│   ├── testing_guide.md          # Testing instructions
│   └── supabase_schema.sql       # Database schema
├── tests/                        # Unit tests
├── .env.example                  # Environment variables template
├── requirements.txt              # Python dependencies
├── vercel.json                   # Vercel configuration
└── README.md                     # This file
```

## Conversation Flow

The size confirmation agent follows a state machine approach:

1. **CONFIRMATION PHASE**: After purchase, asks customer "Are you sure [size] is right for you?"
   - If YES → Update order, trigger fulfillment
   - If NO/UNSURE → Move to sizing questions

2. **SIZING QUESTIONS PHASE**: Ask about usual size, height, weight
   - Collect and store sizing information
   - When sufficient info gathered → Move to recommendation

3. **RECOMMENDATION PHASE**: Suggest appropriate size based on collected info
   - If customer confirms → Update order, trigger fulfillment
   - If customer rejects → Return to sizing questions

4. **COMPLETE PHASE**: Confirmation received, order updated and ready for fulfillment

## Setup and Deployment Checklist

Follow these steps to set up and deploy your Shopify Size Agent:

### 1. Prerequisites Setup

- [ ] Create a Shopify Partner account and development store (or use existing test-store-tailor-ai.myshopify.com)
- [ ] Create a Twilio account and set up WhatsApp sandbox
- [ ] Create a Supabase project
- [ ] Create a Google Cloud Platform account and enable Vertex AI
- [ ] Create a Vercel account

### 2. Environment Setup

- [ ] Clone this repository
- [ ] Copy `.env.example` to `.env` for local development
- [ ] Fill in all required credentials from the various services

### 3. Supabase Setup

- [ ] Create the database schema using `docs/supabase_schema.sql`
- [ ] Test database connection with your credentials

### 4. Shopify Setup

- [ ] Create a private app in Shopify with required permissions
- [ ] Set up "Order creation" webhook pointing to your app

### 5. Twilio Setup

- [ ] Set up WhatsApp sandbox
- [ ] Connect your personal WhatsApp to the sandbox
- [ ] Configure webhook for incoming messages

### 6. Vertex AI Setup

- [ ] Create a service account with Vertex AI access
- [ ] Download service account credentials JSON
- [ ] Prepare for Vercel deployment (encode as base64)

### 7. Deployment

- [ ] Push code to GitHub
- [ ] Deploy to Vercel
- [ ] Configure environment variables in Vercel
- [ ] Update webhook URLs in Shopify and Twilio

### 8. Testing

- [ ] Create a test order in Shopify
- [ ] Verify WhatsApp message is received
- [ ] Test different conversation flows
- [ ] Verify Supabase data is correctly stored
- [ ] Check Shopify order updates

## Detailed Documentation

- [Architecture Overview](docs/architecture.md)
- [Setup Guide](docs/setup_guide.md)
- [Deployment Guide](docs/deployment_guide.md)
- [Testing Guide](docs/testing_guide.md)

## Future Enhancements

- Extend to use customers' historical purchases for better recommendations
- Add support for multiple products in a single order
- Implement A/B testing for different conversation flows
- Create an admin dashboard for monitoring conversations
- Add analytics for size change patterns

## License

MIT

## Author

Created by Renato Boemer
