import os
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv

from app.api import shopify_webhook, twilio_webhook

# Load environment variables from .env file (in development)
load_dotenv()

# Create the FastAPI app
app = FastAPI(
    title="Shopify Size Agent",
    description="A WhatsApp-based size confirmation agent for Shopify",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(shopify_webhook.router, tags=["shopify"])
app.include_router(twilio_webhook.router, tags=["twilio"])


@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {"message": "Shopify Size Agent API is running"}


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"}


# Error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler
    """
    return JSONResponse(
        status_code=500,
        content={"message": f"Internal server error: {str(exc)}"},
    )


# Run the app directly if executed as a script
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=True
    )
