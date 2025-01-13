# Deploy to Google Cloud Run

1. **Install the Google Cloud SDK**:
   - If not installed, follow [Google Cloud SDK installation instructions](https://cloud.google.com/sdk/docs/install).

2. **Authenticate with GCP**:

   ```bash
   gcloud auth login
   ```

3. **Enable Required APIs**:

   ```bash
   gcloud services enable run.googleapis.com
   gcloud services enable containerregistry.googleapis.com
   ```

4. **Tag and Push the Image**:  
`Note: ravah-dev.com GCR Project ID = innate-diode-442920-f7  `

   - Tag the Docker image for Google Container Registry (GCR):

     ```bash
     docker tag cis-calculator gcr.io/<YOUR_PROJECT_ID>/cis-calculator
     ```

   - Push the image to GCR:

     ```bash
     docker push gcr.io/<YOUR_PROJECT_ID>/cis-calculator
     ```

5. **Deploy to Cloud Run**:

   ```bash
   gcloud run deploy cis-calculator \
       --image gcr.io/<YOUR_PROJECT_ID>/cis-calculator \
       --platform managed \
       --region <YOUR_REGION> \
       --allow-unauthenticated
   ```

   - Replace `<YOUR_PROJECT_ID>` and `<YOUR_REGION>` with your GCP project ID and desired region.

6. **Test Your API**:
   - Once deployed, GCP will provide a URL to access your API. Use tools like `curl` or Postman to test.  

---
## Python Unbuffered Mode
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