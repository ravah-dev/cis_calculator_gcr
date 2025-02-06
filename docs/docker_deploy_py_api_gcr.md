# Google Cloud Run Docker Deployment  
How to deploy your Python API app to Google Cloud Run with Docker file. Here's a step-by-step guide:

**1. Containerize your application using Docker.**  
Create a Dockerfile in your project root:  
*Note: This is an example from Claude.ai - actual docker file may be different*

```dockerfile
# Use official Python runtime as base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt

# Copy the rest of the application
COPY . .

# Configure container to run in unbuffered mode
ENV PYTHONUNBUFFERED True

# Define environment variable for GCP Cloud Run
ENV PORT=8080

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```
  
*Note about CMD invocation*
1. **`CMD`**:
  - The `CMD` instruction in a `Dockerfile` specifies the default command to execute when a container starts.
  - It runs the specified command only when the container starts and is **overridable** by the user at runtime.

2. **`uvicorn`**:
  - `uvicorn` is an ASGI (Asynchronous Server Gateway Interface) server for running Python web applications like FastAPI.
  - It acts as the server that handles incoming HTTP requests to your FastAPI app.

3. **`main:app`**:
  - This tells `uvicorn` which application to run.
  - **`main`**: Refers to the Python module `main.py` (the file where your FastAPI app is defined).
  - **`app`**: Refers to the `FastAPI` instance created in `main.py` (`app = FastAPI()`).

4. **`--host 0.0.0.0`**:
  - By default, `uvicorn` binds to `127.0.0.1` (localhost), which means it is only accessible from inside the container.
  - `0.0.0.0` binds the server to all available network interfaces, allowing access from outside the container (e.g., your machine or the cloud).

5. **`--port 8080`**:
  - Specifies the port number on which the server will listen for incoming requests.
  - **`8080`**: A common choice for HTTP servers. This should match the port you expose in the Docker container and the one your cloud platform uses to route traffic (e.g., Google Cloud Run defaults to port `8080`).

---
**2. Ensure your app listens on port 8080 and gets the port from environment:**

```python
import os

port = int(os.getenv("PORT", 8080))
# If using Flask:
app.run(host='0.0.0.0', port=port)
```

**3. Install and set up Google Cloud CLI:**
   - Install from https://cloud.google.com/sdk/docs/install
   - Run `gcloud init` to initialize
   - Run `gcloud auth configure-docker` to configure Docker authentication

**4. Enable Required APIs:**

   ```bash
   gcloud services enable run.googleapis.com
   gcloud services enable containerregistry.googleapis.com
   ```

**5. GCR Permissions (IAM)**  
An error that typically occurs when there are IAM permission issues in Google Cloud:   
"One or more users named in the policy do not belong to a permitted customer, perhaps due to an organization policy."  
Let's fix this by ensuring you have the correct permissions:

*First, verify your current account and project:*
```bash
# Check current account
gcloud auth list

# Check current project
gcloud config get-value project
```

*Make sure you have the necessary IAM roles. You'll need:*
```bash
# Add the Cloud Run Admin role
# gcloud projects add-iam-policy-binding cis-calculator-test \
#     --member="user:YOUR_EMAIL@domain.com" \
#     --role="roles/run.admin"
gcloud projects add-iam-policy-binding cis-calculator-test \
    --member="user:craig.cunningham@ravah-dev.com" \
    --role="roles/run.admin"

# Add the Service Account User role
# gcloud projects add-iam-policy-binding cis-calculator-test \
#     --member="user:YOUR_EMAIL@domain.com" \
#     --role="roles/iam.serviceAccountUser"
gcloud projects add-iam-policy-binding cis-calculator-test \
    --member="user:craig.cunningham@ravah-dev.com" \
    --role="roles/iam.serviceAccountUser"
```

*You might also need to add permissions for the default compute service account:*
```bash
gcloud projects add-iam-policy-binding cis-calculator-test \
    --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/run.serviceAgent"
```
Note: you'll need to replace the PROJECT_NUMBER with your actual Google Cloud project number.  
Here's how to find it:

```bash
# Get your project number
gcloud projects describe cis-calculator-test --format='value(projectNumber)'
```
This will return a number.  
Then substitute that number in the command, so it would look like:
```bash
gcloud projects add-iam-policy-binding cis-calculator-test \
    --member="serviceAccount:690649350627-compute@developer.gserviceaccount.com" \
    --role="roles/run.serviceAgent"
```
Where "690649350627" would be replaced with your actual project number.  


---
**5. Tag and Push the Image:**  
`Note: ravah-dev.com GCR Project ID = innate-diode-442920-f7  `

   - Tag the Docker image for Google Container Registry (GCR):

     ```bash
     docker tag cis-calculator gcr.io/<YOUR_PROJECT_ID>/cis-calculator
     docker tag cis-calculator gcr.io/cis-calculator-test/cis-calculator
     ```

**6. Build and push your container:**
```bash
# Build the container
docker build -t gcr.io/[PROJECT-ID]/[APP-NAME] .
docker build -t gcr.io/cis-calculator-test/cis-calculator .

# Push to Google Container Registry
docker push gcr.io/[PROJECT-ID]/[APP-NAME]
docker push gcr.io/cis-calculator-test/cis-calculator
```

**7. Deploy to Cloud Run:**
```bash
gcloud run deploy [SERVICE-NAME] \
  --image gcr.io/[PROJECT-ID]/[APP-NAME] \
  --platform managed \
  --region [REGION] \
  --allow-unauthenticated
```  

Replace the placeholders:
- `[PROJECT-ID]`: Your Google Cloud project ID
- `[APP-NAME]`: Name for your container image
- `[SERVICE-NAME]`: Name for your Cloud Run service
- `[REGION]`: Your desired region (e.g., us-central1)  
*Note: To set default region:*  
`gcloud config set run/region us-central1`
  
```bash
gcloud run deploy cis-calculator-test \
  --image gcr.io/cis-calculator-test/cis-calculator \
  --platform managed \
  --region us-central1 \
  --timeout 300 \
  --memory 1Gi \
  --no-allow-unauthenticated
```
---
## Python's Unbufferred Mode 
Python's unbuffered mode (set by `PYTHONUNBUFFERED=True`) is particularly important in containerized environments for a few key reasons:

1. Output Immediacy:
- In buffered mode (default), Python buffers stdout and stderr output
- This means log messages might not appear immediately in your container logs
- In unbuffered mode, output is written directly to the stream without waiting for the buffer to fill
- This ensures you see logs in real-time, which is crucial for monitoring and debugging containerized applications

2. Container Log Management:
- Container orchestration platforms like Cloud Run expect applications to log to stdout/stderr
- Buffered output could mean losing important logs if your container crashes or restarts
- Unbuffered mode ensures all logs are captured before any potential container termination

3. Cloud Run Specifics:
- Cloud Run collects logs from your container's stdout/stderr streams
- These logs are then available in Google Cloud Console
- Without unbuffered mode, you might experience delays in log visibility or miss critical errors

Here's a practical example of the difference:

```python
# With buffered output (default)
print("Starting application...")  # Might not appear immediately
time.sleep(1)
print("Processing request...")    # Both messages might appear together
                                # after some delay

# With unbuffered output (PYTHONUNBUFFERED=True)
print("Starting application...")  # Appears immediately
time.sleep(1)
print("Processing request...")    # Appears exactly when executed
```

There are a few ways to enable unbuffered mode:
1. Environment variable (what we used in the Dockerfile):
```dockerfile
ENV PYTHONUNBUFFERED True
```

2. Python flag when running the script:
```dockerfile
CMD ["python", "-u", "main.py"]
```

3. In your Python code:
```python
import sys
import io
sys.stdout = io.TextIOWrapper(open(sys.stdout.fileno(), 'wb', 0), write_through=True)
```

The environment variable approach is preferred because it's cleaner and works consistently across different Python entry points.

For handling the port environment variable in Cloud Run, you actually don't need to create an environment file. This is because Cloud Run automatically injects the `PORT` environment variable when it runs your container.

However, there are a few different scenarios to consider:

1. Local Development:
- When running locally, the app will use the default value (8080) since no PORT env var is set
- You can override it by setting the PORT environment variable when running Docker:
```bash
docker run -p 8080:8080 -e PORT=8080 your-image-name
```

2. Cloud Run Deployment:
- Cloud Run automatically sets the PORT environment variable
- You don't need to configure anything - it just works

3. If you have other environment variables:
- For other config values, you can add them during deployment:
```bash
gcloud run deploy [SERVICE-NAME] \
  --image gcr.io/[PROJECT-ID]/[APP-NAME] \
  --platform managed \
  --region [REGION] \
  --set-env-vars "DB_URL=example.com,API_KEY=xyz"
```

- Or through the Google Cloud Console:
  1. Go to Cloud Run
  2. Select your service
  3. Click "Edit & Deploy New Revision"
  4. Add variables under "Variables & Secrets"

If you want to use environment variables during local development, you have a few options:

1. Create a `.env` file (but don't commit it to source control):
```
DB_URL=localhost:5432
API_KEY=dev-key
```

2. Load it in your Python code:
```python
from dotenv import load_dotenv
import os

load_dotenv()  # This loads the .env file if it exists
port = int(os.getenv("PORT", 8080))
db_url = os.getenv("DB_URL")
```

Remember to add `.env` to your `.gitignore` file to keep sensitive information out of version control:
```
.env
*.pyc
__pycache__/
```
--- 
  
## Using .env
When you use `load_dotenv()`, it reads the `.env` file and makes all the properties defined there available through `os.getenv()`. 

Here's a practical example:

`.env` file:
```
DATABASE_URL=postgresql://localhost:5432/mydb
API_KEY=my-secret-key
DEBUG=True
MAX_CONNECTIONS=5
```

Python code:
```python
from dotenv import load_dotenv
import os

load_dotenv()

# Get values with defaults
database_url = os.getenv("DATABASE_URL", "sqlite:///default.db")
api_key = os.getenv("API_KEY", "default-key")
debug = os.getenv("DEBUG", False)
max_conn = int(os.getenv("MAX_CONNECTIONS", 10))  # Convert string to int

# Get values without defaults (will return None if not found)
some_value = os.getenv("NON_EXISTENT_VALUE")
```

A few important points:
- `os.getenv()` always returns strings (or None if the variable isn't found)
- You'll need to convert to other types (int, bool, etc.) as needed
- The default value is used if the environment variable isn't found in the `.env` file or system environment
- System environment variables take precedence over values in the `.env` file  

---
**- end of file -**