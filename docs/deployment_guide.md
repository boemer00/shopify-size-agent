# Shopify Size Agent - Deployment Guide

This guide will walk you through deploying the Shopify Size Agent to Vercel.

## Prerequisites

Before deploying, ensure you have:

1. Completed all the steps in the `setup_guide.md`
2. Created a GitHub repository with your project code
3. A Vercel account connected to your GitHub account
4. All the environment variables collected from the setup guide

## Deployment Steps

### 1. Prepare Your Code for Deployment

1. Clone the repository if you haven't already:
   ```bash
   git clone https://github.com/yourusername/shopify-size-agent.git
   cd shopify-size-agent
   ```

2. Ensure your `requirements.txt` file includes all dependencies.

3. Check that your `vercel.json` file is correctly configured:
   ```json
   {
     "version": 2,
     "builds": [
       {
         "src": "app/main.py",
         "use": "@vercel/python"
       }
     ],
     "routes": [
       {
         "src": "/(.*)",
         "dest": "app/main.py"
       }
     ]
   }
   ```

4. Commit and push your changes:
   ```bash
   git add .
   git commit -m "Prepare for Vercel deployment"
   git push
   ```

### 2. Deploy to Vercel

#### 2.1 Using the Vercel Dashboard

1. Log in to your Vercel account at [vercel.com](https://vercel.com)
2. Click "Add New" > "Project"
3. Import your GitHub repository
4. Configure the project:
   - Framework Preset: Other
   - Root Directory: ./
   - Build Command: Leave empty (uses `vercel.json`)
   - Output Directory: Leave empty

5. Add Environment Variables:
   - Copy all variables from your `.env` file
   - For the `GOOGLE_APPLICATION_CREDENTIALS` variable:
     - You need to encode the JSON file to a string
     - For GCP credentials, set a variable like `GOOGLE_CREDENTIALS` with the full JSON content
     - The app will handle creating a temporary file from this string

6. Click "Deploy"

#### 2.2 Using the Vercel CLI

1. Install the Vercel CLI:
   ```bash
   npm install -g vercel
   ```

2. Log in to Vercel:
   ```bash
   vercel login
   ```

3. Deploy from your project directory:
   ```bash
   vercel
   ```

4. Follow the prompts to configure your project
5. Add environment variables using the Vercel dashboard or using the CLI:
   ```bash
   vercel env add SHOPIFY_API_KEY
   ```
   Repeat for each environment variable

### 3. Update Webhook URLs

After deployment, Vercel will provide you with a production URL (e.g., `https://shopify-size-agent.vercel.app`).

1. Update your Shopify webhook URL:
   - Go to your Shopify app settings > Webhooks
   - Update the URL to `https://your-vercel-app.vercel.app/webhook/order`

2. Update your Twilio webhook URL:
   - Go to your Twilio console > Phone Numbers > Manage > Active numbers
   - Update the webhook URL for "A MESSAGE COMES IN" to `https://your-vercel-app.vercel.app/webhook/reply`

### 4. Handling GCP Credentials in Vercel

Since Vercel doesn't support file uploads for environment variables, you need to handle the GCP credentials in a special way:

1. Convert your GCP JSON credentials file to a base64-encoded string:
   ```bash
   cat your-gcp-credentials.json | base64
   ```

2. Add this as an environment variable in Vercel:
   - Name: `GOOGLE_CREDENTIALS_BASE64`
   - Value: the base64 string from the previous step

3. In your code, add a helper function in `vertex_ai_service.py` to create a temporary file from this string:

```python
import os
import base64
import tempfile

def setup_gcp_credentials():
    """
    Create a temporary credentials file from the base64-encoded credentials
    and set the GOOGLE_APPLICATION_CREDENTIALS environment variable
    """
    credentials_base64 = os.environ.get("GOOGLE_CREDENTIALS_BASE64")
    if credentials_base64:
        # Decode the base64 string
        credentials_json = base64.b64decode(credentials_base64).decode('utf-8')

        # Create a temporary file
        fd, path = tempfile.mkstemp()
        with os.fdopen(fd, 'w') as tmp:
            tmp.write(credentials_json)

        # Set the environment variable
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path
        return path
    return None
```

4. Call this function before initializing Vertex AI in your service:

```python
def __init__(self):
    self.project_id = os.environ.get("VERTEX_AI_PROJECT_ID")
    self.location = os.environ.get("VERTEX_AI_LOCATION", "us-central1")
    self.model_name = "chat-bison"

    # Set up GCP credentials
    self.temp_credentials_path = setup_gcp_credentials()

    # Initialize Vertex AI
    aiplatform.init(project=self.project_id, location=self.location)

    # Load the chat model
    self.chat_model = ChatModel.from_pretrained(self.model_name)
```

### 5. Verify Deployment

1. Visit your Vercel app URL (e.g., `https://shopify-size-agent.vercel.app`)
2. You should see the message: "Shopify Size Agent API is running"
3. Check the health endpoint: `https://your-vercel-app.vercel.app/health`
4. If everything is working, it should return `{"status": "healthy"}`

### 6. Test the Webhooks

1. Create a test order in your Shopify store
2. Check the Vercel logs for any errors
3. Verify the order data is stored in Supabase
4. Check if the WhatsApp message is sent to your phone
