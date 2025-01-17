# gcloud_buildpacks_deploy.md
**folder: cis-calculator**  
This setup is to try to get a container deployed to gcloud successfully using gcloud Buildpacks deployment.  
- started with the 'minimal.py' app and translated to main.py  

## Deploy main.py app with gcloud Buildpacks method

1. Buildpack required directory structure:
```
📁 fastapi-test/
  ├── main.py
  ├── requirements.txt
  ├── Procfile
  └── ... other files necessary for calculator to run

```

2. `main.py`: this shows the required elements defined in minimal.py
```python
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
```

3. `requirements.txt`: this shows components to be installed in the build
```
fastapi
uvicorn
pydantic
pandas
openpyxl
iPython
```

4. `Procfile`:
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```
---   

*Authetication to gcloud:*
This error occurs because you need to authenticate with Google Cloud before pushing to Google Container Registry (GCR). You can fix this by following these steps:

1. First, ensure you're logged into gcloud:
```bash
gcloud auth login
```

2. Then (for Docker deployments) configure Docker to use gcloud credentials:
```bash
gcloud auth configure-docker
```

3. Make sure you have the correct project set:
```bash
# Check current project
gcloud config get-value project

# If needed, set the correct project
gcloud config set project cis-calculator-test
```

4. Verify you have the necessary permissions:
```bash
# List your current credentials
gcloud auth list
```
---  

Then deploy:  

**Note: If there is a Dockerfile file in the directory, it will be used to build the image. If not, gcloud will use Buildpacks to create the image**
  
Let's try the Buildpacks deployment:  

- We'll try deploying with authentication required, and then we can access it using your Google Cloud credentials:

1. Deploy with authentication:  

```bash
gcloud run deploy cis-calculator-test \
    --source . \
    --platform managed \
    --region us-central1 \
    --no-allow-unauthenticated
```
*Note: this deployment suceeded*

2. Then test with an authenticated request:
```bash
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
    https://cis-calculator-test-690649350627.us-central1.run.app
```
*Here is a curl command to call the calculate function*
```bash
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
-X POST -H "Content-Type: application/json" -d @test_farm_input.json \
https://cis-calculator-test-690649350627.us-central1.run.app/calculate
```
  
**Note: This method worked!**  
This way, we're working within your organization's security policies rather than trying to override them. 

### What Worked with gcloud Buildpack deployment:
We used a simple structure. Buildpack uses 3 files:  
1. main.py (where the app is created)  
2. Procfile - This defines the container invoker  
3. requirements.txt - this references libs needed  

The key is the gcloud run command needs to specify authentication requried and be sure to give the service a descriptive name.  (see #1 above)  

---