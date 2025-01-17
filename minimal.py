# minimal.py
# used to test calculator gcr deployment
# Note for gcloud Buildpack deployment, 
# - make sure no Dockerfile is present
# - make sure you have a Procfile 
# - make sure you have a requirements.txt file

# Note: this example is working with gcloud Buildpack deployment
# You can test this with a curl command:
# curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
#     https://test-app-690649350627.us-central1.run.app
# Note: replace 'test-app-690649350627.us-central1.run.app' with your actual app URL

# Note that the current version of FastAPI is 0.115 
# - which requires 'lifespan' decorator to inject startup logic
# - this also requires asynccontextmanager for compatibility

import os
import sys
import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Set up logging to stderr
logging.basicConfig(
    level=logging.DEBUG,
    stream=sys.stderr,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.info("Starting FastAPI application...")

# Lifespan context manager for FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    try:
        port = os.getenv("PORT", "8080")
        logger.info(f"FastAPI starting up on port {port}")
        logger.info(f"Current working directory: {os.getcwd()}")
        logger.info(f"Environment variables: {dict(os.environ)}")

        yield  # Hand over control to the app
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise
    finally:
        # Cleanup logic (if needed)
        logger.info("FastAPI shutting down...")
        
# Create FastAPI app with the lifespan context manager
app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root():
    return {"Hello": "This is the FastAPI World"}
