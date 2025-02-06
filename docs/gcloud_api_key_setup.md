# Google Cloud API Key setup

### Allow unauthenticated invocations
In order to use API-Key access, your service must be on a publicly available endpoint, and the service logic must be set up to validate the passed-in API key.  

**In console.cloud.google.com, navigate to Cloud Run Services**
- Select your API service from the list
- On the ‘Security’ tab insure Authentication is set to ‘Allow unauthenticated invocations’
    - This requires correct permissions. 
    - If it fails, you may still need to run the google cloud setup wizard that the account owner/administrator sees when first opening the account.

### Enable API key access:
1. Add logic to your API service to **validate the passed-in API-Key**
    ```python
    # FUNCTION - API key validation (for passed-in google api key)
    async def validate_api_key(request: Request):
        # Get the API key from query parameters
        api_key = request.query_params.get('key')
        if not api_key:
            logger.warning("No API key provided in request")
            raise HTTPException(status_code=403, detail="No API key provided --craig")
        
        # Get the expected API key from environment
        expected_key = os.getenv("GOOGLE_API_KEY")  # We'll need to set this in Cloud Run
        if not expected_key:
            logger.error("API key not configured in environment -craig")
            raise HTTPException(status_code=500, detail="API key not configured --craig")
        
        # Validate the key
        if api_key != expected_key:
            logger.warning("Invalid API key provided")
            raise HTTPException(status_code=403, detail="Invalid API key --craig")
        
        logger.info("API key validated successfully")
        return api_key

    # Add API key protection to your endpoints
    @app.get("/")
    async def read_root(request: Request):
        await validate_api_key(request)
        return {"message": "Hello, This is the GREET Calculator API!"}
    ```

2. **Create API Keys:** Generate API keys within the Google Cloud Console for your cis-calculator-test project.  
    To create API keys for your cis-calculator-test Cloud Run service, you need to navigate to the Google Cloud Console's Credentials page for your project.  

    Here's how:  
    
    1. Go to the Google Cloud Console: Open the Google Cloud Console and select your cis-calculator-test project.  
    2. Navigate to Credentials: In the left-hand navigation menu, go to "APIs & Services" and then select "Credentials".  
    3. Create Credentials: Click the "+ CREATE CREDENTIALS" button, and choose "API key".  
        - Use this key in your application by passing it with the 'key=API_KEY parameter
        - Key name: cis_calculator_test_key
        - AIzaSyCX5S0GwnB-u5APOBbLf0KfTd1TmsZBh_Q  
        - (this key is unrestricted )
        ```bash
        curl "https://cis-calculator-test-690649350627.us-central1.run.app/?key=YOUR-GOOGLE-API-KEY"
        ```

3. **Add API-Key to gcloud service environment variable:**  
- You will need to reference a stored copy of this key in the validation logic of your hosted service. A convenient way is to store the key in a gcloud environment var like so:  
    ```bash
    gcloud run services update cis-calculator-test \
        --update-env-vars GOOGLE_API_KEY="YOUR-GOOGLE-API-KEY" \
        --region us-central1  
    ```  

### Notes  
- You can display logs with the following command:  
    ```bash
        gcloud run services logs read cis-calculator-test --region us-central1
    ```  
- Restrict Key (Recommended): While the key will be generated, immediately restrict its usage for enhanced security. You can do this by specifying API restrictions, IP address restrictions, or both. This is highly recommended, especially for third-party access. Without restrictions, anyone with the key has full access.  
- Download (copy) the Key: Download (or copy) the newly created API key. This is a JSON file containing your key. Keep this file in a secure location; it cannot be retrieved later.  
- API Key Restrictions (Important): If you chose to restrict the key in step 4, define the allowed APIs and/or IP addresses on the next screen. This step is crucial for controlling which parts of your API the third party can access and from which locations they can invoke your API. Carefully select the APIs and IP ranges that are appropriate for the third-party's use.  

- Enable the API: Ensure the API your Cloud Run service is using is enabled in your Google Cloud project. The exact steps depend on the API you're using.  
- Provide the Key: Distribute the JSON file containing the key securely to the third party. Include clear instructions on how to use the key with your API.  

### Important Security Considerations:  

- Rotate Keys Regularly: API keys should be rotated periodically (e.g., every few months) to mitigate the risk of compromise. When rotating, revoke the old key and provide the third party with a new one.  
- Key Management: Treat API keys like passwords. Never hardcode them into client-side code or commit them to version control.  
- Monitoring: Monitor API key usage to detect suspicious activity. Google Cloud provides tools to help you monitor API usage.  
- Method-Level Control (Advanced): If you have granular control over your API's methods (e.g., using Cloud Endpoints or Apigee), consider setting API keys to be required only for certain methods, allowing others to be invoked without authentication. This depends on your API architecture and security requirements.  

    **Remember to replace placeholders like "[YOUR_PROJECT_ID]" with your actual project ID.** The exact steps and terminology might vary slightly based on the Google Cloud Console interface version.

    **Service Configuration (Method-Level Control):**  
    - If you're using Cloud Endpoints or a similar API gateway, you'll edit your service configuration file. This file defines which methods require API keys and which do not. You would specify that certain methods allow allow_unregistered_calls: true in the service configuration to bypass API key requirements for those specific endpoints. If you only want to allow unauthenticated access to a subset of the API's methods, this approach is ideal.  

    **Service Configuration (API-Level Control):**  
    - As an alternative to method-level control, you can make the entire API accessible without API keys. This approach is less secure; exercise caution before employing this. You can achieve this by setting allow_unregistered_calls: true for a wildcard selector ( * ) encompassing all methods in your API within the service configuration.  

## Deploy Your Service:**  
After configuring your service's access rules, redeploy your Cloud Run service to reflect the new settings.  

**Provide API Keys:** Distribute the generated API keys securely to your third-party users, along with instructions on how to use them with your API.  

Your organization ID (372867527428) is relevant for broader organization-wide policies, but it does not directly control the API key access of individual projects within your organization. The access control is handled at the project level (cis-calculator-test) and using API keys and service configuration.