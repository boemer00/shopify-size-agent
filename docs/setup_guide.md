# Shopify Size Agent - Setup Guide

This guide will walk you through setting up all the required services and credentials for the Shopify Size Agent.

## Prerequisites

Before you begin, you'll need:

- A Shopify Partner account (for development store access)
- A Twilio account (free trial is sufficient)
- A Google Cloud Platform account (free trial with credits)
- A Supabase account (free tier is sufficient)
- A Vercel account (free tier is sufficient)
- Git (for deploying to Vercel)
- Python 3.8+ (for local development)

## Step-by-Step Setup

### 1. Shopify Setup

#### 1.1 Create a Shopify Development Store
1. Log in to your Shopify Partner account
2. Go to "Stores" > "Add store" > "Development store"
3. Fill in the details and create the store
4. If using the existing store (test-store-tailor-ai.myshopify.com), request access from the store owner

#### 1.2 Create a Private App
1. In your Shopify admin, go to "Apps" > "Develop apps"
2. Click "Create an app"
3. Name your app (e.g., "Size Confirmation Agent")
4. Set "App URL" to your Vercel app URL (or ngrok URL for testing)
5. Under "API credentials" select the following scopes:
   - `read_orders`, `write_orders` (for accessing and updating orders)
   - `read_customers`, `write_customers` (for accessing customer information)
   - `read_fulfillments`, `write_fulfillments` (for creating fulfillments)
6. Click "Create app"
7. Note down the API key and API secret key

#### 1.3 Set Up Webhook
1. In your Shopify app settings, go to "Webhooks"
2. Click "Add webhook"
3. Select "Order creation" as the event
4. Set the URL to `https://your-vercel-app.vercel.app/webhook/order`
5. Select JSON as the format
6. Click "Save webhook"
7. Note down the webhook secret key

### 2. Twilio WhatsApp Sandbox Setup

#### 2.1 Create a Twilio Account
1. Sign up for a Twilio account at [twilio.com](https://www.twilio.com/)
2. Verify your email and phone number

#### 2.2 Set Up WhatsApp Sandbox
1. In your Twilio console, navigate to "Messaging" > "Try it out" > "Send a WhatsApp message"
2. Follow the instructions to connect your personal WhatsApp to the Twilio sandbox
3. Note down your Twilio sandbox WhatsApp number

#### 2.3 Configure Webhook for Incoming Messages
1. In your Twilio console, go to "Phone Numbers" > "Manage" > "Active numbers"
2. Click on your WhatsApp sandbox number
3. Under "Messaging", set the webhook URL for "A MESSAGE COMES IN" to `https://your-vercel-app.vercel.app/webhook/reply`
4. Save your changes

#### 2.4 Get Twilio Credentials
1. In your Twilio console, go to the Dashboard
2. Note down your Account SID and Auth Token

### 3. Supabase Setup

#### 3.1 Create a Supabase Project
1. Sign up for Supabase at [supabase.com](https://supabase.com/)
2. Create a new project with a name like "shopify-size-agent"
3. Choose the free tier and a region close to your target audience
4. Wait for the project to be created

#### 3.2 Set Up Database Schema
1. Open the SQL Editor in your Supabase dashboard
2. Copy the contents of `docs/supabase_schema.sql` from this repository
3. Paste the SQL into the editor and run the queries
4. Verify the tables were created correctly

#### 3.3 Get Supabase Credentials
1. In your Supabase project dashboard, go to "Settings" > "API"
2. Note down the Project URL and the anon public key

### 4. Google Cloud Platform (GCP) Setup

#### 4.1 Create a GCP Project
1. Sign up for GCP at [cloud.google.com](https://cloud.google.com/)
2. Create a new project (e.g., "shopify-size-agent")
3. Enable billing (you'll need to add a credit card, but there's a free tier and initial credits)

#### 4.2 Enable Vertex AI API
1. In the GCP Console, go to "APIs & Services" > "Library"
2. Search for "Vertex AI API"
3. Click on it and then click "Enable"

#### 4.3 Create Service Account
1. In the GCP Console, go to "IAM & Admin" > "Service Accounts"
2. Click "Create Service Account"
3. Name it (e.g., "vertex-ai-client")
4. Grant it the "Vertex AI User" role
5. Create a JSON key for the service account and download it
6. Store this JSON file securely - you'll need it for authentication

### 5. Environment Variables

After completing the setup steps above, you should have collected the following information for your environment variables:

```
# Shopify credentials
SHOPIFY_STORE_URL=test-store-tailor-ai.myshopify.com
SHOPIFY_API_KEY=your_shopify_api_key
SHOPIFY_API_SECRET=your_shopify_api_secret
SHOPIFY_API_VERSION=2023-07
SHOPIFY_WEBHOOK_SECRET=your_shopify_webhook_secret

# Twilio credentials
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_whatsapp_number

# Supabase credentials
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Google Cloud Vertex AI
GOOGLE_APPLICATION_CREDENTIALS=path_to_your_credentials_json_file
VERTEX_AI_PROJECT_ID=your_gcp_project_id
VERTEX_AI_LOCATION=us-central1

# Application settings
WEBHOOK_BASE_URL=https://your-vercel-app.vercel.app
DEBUG=False
```

Fill in each value with the information you collected from the respective services.
