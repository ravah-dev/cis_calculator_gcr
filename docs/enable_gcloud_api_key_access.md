# Setting up secure access to your gcloud API  
There are several approaches we can use depending on your requirements:

## 1. Service Accounts (Most Secure)
This is the recommended approach for service-to-service authentication:
```bash
# Create a service account
gcloud iam service-accounts create client-service-account \
    --display-name="Client Service Account"

# Generate a key file for the service account
gcloud iam service-accounts keys create key.json \
    --iam-account=client-service-account@cis-calculator-test.iam.gserviceaccount.com
```

Then grant the service account permission to invoke your Cloud Run service:
```bash
gcloud run services add-iam-policy-binding cis-calculator-test \
    --member="serviceAccount:client-service-account@cis-calculator-test.iam.gserviceaccount.com" \
    --role="roles/run.invoker" \
    --region=us-central1
```

Your clients can then use the key.json file to authenticate their requests:
```bash
# Example using curl with service account authentication
curl -H "Authorization: Bearer $(gcloud auth print-identity-token --impersonate-service-account=client-service-account@cis-calculator-test.iam.gserviceaccount.com)" \
    https://cis-calculator-test-690649350627.us-central1.run.app
```

## 2. OAuth2 Authentication
For web applications or scenarios where you want to authenticate individual users:

```bash
# Create OAuth2 credentials in Google Cloud Console
gcloud alpha services identity-platform oauth-idp-configs create \
    --display-name="API Client" \
    --client-id=YOUR_CLIENT_ID \
    --client-secret=YOUR_CLIENT_SECRET
```

## 3. Public Access with API Keys
If you want to make the service public but control access:

First, make the service public:
```bash
gcloud run services set-iam-policy cis-calculator-test \
    --region=us-central1 \
    policy.yaml
```

Where policy.yaml contains:
```yaml
bindings:
- members:
  - allUsers
  role: roles/run.invoker
```

Then you can implement API key validation in your FastAPI application:

```python
from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKeyHeader

API_KEY_NAME = "X-API-Key"
API_KEY = "your-api-key"  # Store this securely

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid API Key"
        )
    return api_key

@app.get("/", dependencies=[Depends(verify_api_key)])
def read_root():
    return {"Hello": "This is the FastAPI World"}
```

Each has different trade-offs:
- Service Accounts: Most secure, best for service-to-service communication
- OAuth2: Best for web applications and user-specific authentication
- API Keys: Simplest but less secure, good for basic access control

### Setting up API Keys access (Details)
#### 1. Make the service public using the instructions above  
In case of ERROR: (gcloud.run.services.set-iam-policy) FAILED_PRECONDITION: One or more users named in the policy do not belong to a permitted customer,  perhaps due to an organization policy:
Let's try these steps:

1. First, verify your current permissions:  
    ```bash
    # Check current account
    gcloud auth list

    # Check current project
    gcloud config get-value project
    ```
    **output**
    ```
    # Check current project
    gcloud config get-value project
            Credentialed Accounts
    ACTIVE  ACCOUNT
            craig.cunningham@ogd.com
    *       craig.cunningham@ravah-dev.com

    To set the active account, run:
        $ gcloud config set account `ACCOUNT`

    Your active configuration is: [ravah-dev]
    cis-calculator-test
    ```

2. You'll need to add the specific IAM binding for your account to manage policies:
    ```bash
    gcloud projects add-iam-policy-binding cis-calculator-test \
        --member="user:craig.cunningham@ravah-dev.com" \
        --role="roles/run.admin"
    ```  
    **output**
    ```
    Updated IAM policy for project [cis-calculator-test].
    bindings:
    - members:
        - serviceAccount:service-690649350627@gcp-sa-artifactregistry.iam.gserviceaccount.com
        role: roles/artifactregistry.serviceAgent
    - members:
        - serviceAccount:690649350627@cloudbuild.gserviceaccount.com
        role: roles/cloudbuild.builds.builder
    - members:
        - serviceAccount:service-690649350627@gcp-sa-cloudbuild.iam.gserviceaccount.com
        role: roles/cloudbuild.serviceAgent
    - members:
        - serviceAccount:service-690649350627@containerregistry.iam.gserviceaccount.com
        role: roles/containerregistry.ServiceAgent
    - members:
        - user:craig.cunningham@ravah-dev.com
        role: roles/iam.serviceAccountUser
    - members:
        - serviceAccount:690649350627-compute@developer.gserviceaccount.com
        role: roles/logging.logWriter
    - members:
        - user:craig.cunningham@ravah-dev.com
        - user:david.loving@ravah-dev.com
        role: roles/owner
    - members:
        - serviceAccount:service-690649350627@gcp-sa-pubsub.iam.gserviceaccount.com
        role: roles/pubsub.serviceAgent
    - members:
        - user:craig.cunningham@ravah-dev.com
        role: roles/run.admin
    - members:
        - serviceAccount:690649350627-compute@developer.gserviceaccount.com
        - serviceAccount:service-690649350627@serverless-robot-prod.iam.gserviceaccount.com
        role: roles/run.serviceAgent
    etag: BwYtaaRCJgM=
    version: 1
    ```

3. Instead of making the service completely public, let's try a more controlled approach by creating a specific binding for the service:
    ```bash
    gcloud run services add-iam-policy-binding cis-calculator-test \
        --member="serviceAccount:690649350627-compute@developer.gserviceaccount.com" \
        --role="roles/run.invoker" \
        --region=us-central1
    ```  
      
    **output**
    ```
    Updated IAM policy for service [cis-calculator-test].
    bindings:
    - members:
        - serviceAccount:690649350627-compute@developer.gserviceaccount.com
        role: roles/run.invoker
    etag: BwYtab-c3-k=
    version: 1
    ```  
   
#### 2. Now let's modify your FastAPI application to implement API key validation.

Since you currently have a working `main.py`, let's modify it to add API key security. Here's the updated version that includes your existing lifespan context manager and logging while adding the API key validation:

```python
import os
import sys
import logging
from fastapi import FastAPI, Security, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader
from contextlib import asynccontextmanager

# Set up logging to stderr
logging.basicConfig(
    level=logging.DEBUG,
    stream=sys.stderr,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.info("Starting FastAPI application...")

# API Key configuration
API_KEY_NAME = "X-API-Key"
# In production, this should be stored securely (e.g., environment variable)
API_KEY = os.getenv("API_KEY", "your-secret-api-key")  

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        logger.warning(f"Invalid API key attempt: {api_key[:6]}...")
        raise HTTPException(
            status_code=403,
            detail="Invalid API Key"
        )
    return api_key

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

# Add API key dependency to routes
@app.get("/", dependencies=[Depends(verify_api_key)])
def read_root():
    return {"Hello": "This is the FastAPI World"}

# Add protection to any other endpoints you have
# Example:
# @app.post("/calculate", dependencies=[Depends(verify_api_key)])
# def calculate():
#     return {"result": "calculation"}
```
  
#### 3. To deploy this:  

1. First you will need to establish an API key.  
When establishing an API key, you want to create a secure, random string that's difficult to guess. Here are a few good ways to generate one:

    a. Using Python's secrets module (recommended approach):  

    ```python
    import secrets
    api_key = secrets.token_urlsafe(32)  # Generates a 32-byte random URL-safe string
    print(api_key)  # This will output something like: 'Uj1w9jMu8JxHEx3g4vJ_iPPkBgFhXQtGF3UHyqnGqB4'
    ```  
  
    b. - Or - Using the Python command line:  

    ```bash  
    python3 -c 'import secrets; print(secrets.token_urlsafe(32))'  
    ```  
    **output**  
    ```
    0RyCH_mKxN90cbPiSZ4nQGb_K4Uqesxf5dQuZQEr7ec
    ```  


2. Once you have generated your API key:

    a. Save it somewhere secure (you'll need to share it with your API users)

    b. Add it to your Cloud Run environment:  
    ```bash
    gcloud run services update cis-calculator-test \
        --set-env-vars API_KEY="0RyCH_mKxN90cbPiSZ4nQGb_K4Uqesxf5dQuZQEr7ec" \
        --region=us-central1
    ```
   c. You can check this env var with the following command:  
   ```bash
   gcloud run services describe cis-calculator-test \
    --region us-central1 \
    --format='get(spec.template.spec.containers[0].env)'
   ```  
   **output**  
   ```bash
   {'name': 'API_KEY', 'value': '0RyCH_mKxN90cbPiSZ4nQGb_K4Uqesxf5dQuZQEr7ec'}
   ```  

3. Deploy the updated application:
```bash
gcloud run deploy cis-calculator-test \
    --source . \
    --platform managed \
    --region us-central1
```

4. Test the protected endpoint:
```bash
# This should fail
curl https://cis-calculator-test-690649350627.us-central1.run.app

# This is the format of the curl request using the api key
curl -H "X-API-Key: your-chosen-secret-key" \
    https://cis-calculator-test-690649350627.us-central1.run.app

# This should succeed
curl -H "X-API-Key: 0RyCH_mKxN90cbPiSZ4nQGb_K4Uqesxf5dQuZQEr7ec" \
    https://cis-calculator-test-690649350627.us-central1.run.app
```

5. You can check the logs with this command:  
```bash
gcloud run services logs read cis-calculator-test --region us-central1
```  

Would you like me to also show you how to set up multiple API keys or add any other security features to this implementation?

Would you like to try these steps, or should we pivot to implementing API key validation while keeping the service authenticated through Google Cloud IAM?