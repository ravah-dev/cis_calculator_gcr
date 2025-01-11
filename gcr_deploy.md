## Deploy to Google Cloud Run

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