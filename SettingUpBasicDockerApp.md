
# Setting Up The CIS Calculator Project

## Step 1: Set Up a Basic Python Project

1. **Create a New Directory**:
   - Create a directory for your project:  
   `mkdir cis-calculator && cd cis-calculator`.  

2. **Set Up a Virtual Environment**:  
Setting up a virtual environment is an essential step in Python projects, especially when managing dependencies. A **virtual environment** is an isolated Python environment where you can install libraries and packages specific to your project without affecting other Python projects or the system-wide Python installation.  

   - **Isolation**: Keeps dependencies for your project separate from others.
   - **Version Control**: Ensures the versions of libraries you use in one project don’t conflict with versions in other projects.
   - **Reproducibility**: Helps recreate the environment easily, which is essential for collaboration or deployment.

   **Create a Virtual Environment**
   Run the following command in your project directory:

   ```bash
   python3 -m venv venv
   ```

   - **`python3`**: Specifies the Python version to use (you can replace it with `python` if it's your default).
   - **`venv`**: The name of the module used to create the virtual environment.
   - **`venv`**: The name of the virtual environment directory (you can name it anything, but `venv` is conventional).

   This command creates a new directory (`venv`), which contains:

   - A standalone Python interpreter.
   - A `bin` or `Scripts` directory (depending on your OS) with tools like `pip`.
   - A `lib` directory to store project-specific libraries.

   **Activate the Virtual Environment**  
   *On Linux/Mac*:

     ```bash
     source venv/bin/activate
     ```

      Once activated, you’ll notice the virtual environment name in your terminal prompt, like this:

      ```bash
      (venv) user@machine:~/project$
      ```

   ***Example: Installing Dependencies (ref. section 3 below)***  
      Inside the virtual environment, you can install project-specific dependencies using `pip`:

      ```bash
      pip install fastapi uvicorn
      ```

   Installed packages will now be stored in the `venv` directory instead of globally.  

   ***Example: Deactivating the Virtual Environment***  
   To exit the virtual environment and return to the system Python environment:

   ```bash
   deactivate
   ```

   ***Example: Recreating the Environment on Another Machine***
   To ensure others can recreate your environment:
   - Export the dependencies to a `requirements.txt` file:

     ```bash
     pip freeze > requirements.txt
     ```

   - On a different machine or setup, create a virtual environment and install dependencies using:

     ```bash
     pip install -r requirements.txt
     ```  

3. **Install Required Libraries**:
   Add a lightweight web framework like Flask or FastAPI for handling API requests.  Options are:

    *FastAPI:*
    - Modern, fast framework (built on Starlette) that leverages Python type hints for automatic API documentation
    - Great for building REST APIs quickly with excellent performance
    - Built-in support for async/await
    - Automatic OpenAPI (Swagger) documentation generation
    - Excellent for microservices and API-first applications
    - FastAPI's Pydantic models are particularly valuable for use with large data objects.

    *Flask:*
    - Minimalist and flexible framework with a gentle learning curve
    - Requires external library for async/await
    - Very lightweight core with "batteries not included" philosophy
    - Great for small to medium projects and prototypes  

    Using 'pip` *(see 'Setting up a virtual environment above)*, Install FastAPI library inside the virtual environment:

     ```bash
     pip install fastapi uvicorn
     ```

4. **Create a Basic API app**:  
   Create a file `main.py`:

     ```python
     from fastapi import FastAPI

     app = FastAPI()

     @app.get("/")
     def read_root():
         return {"message": "Hello, World!"}

     @app.post("/calculate")
     def calculate(data: dict):
         # Replace this with your actual calculation logic
         result = {"input": data, "output": "calculated metrics"}
         return result
     ```

## Step 2: Create a Dockerfile & Build Docker Image

1. **Add a `Dockerfile`**:

   The file should actually be named Dockerfile (with no file extension). This is the standard name recognized by Docker when building images.

   ```dockerfile
   # Use an official Python runtime as a parent image
   FROM python:3.11-slim

   # Set the working directory in the container
   WORKDIR /app

   # Copy the current directory contents into the container at /app
   COPY . /app

   # Install dependencies
   RUN pip install --no-cache-dir fastapi uvicorn

   # Make port 8080 available to the world outside this container
   EXPOSE 8080

   # Define environment variable for GCP Cloud Run
   ENV PORT=8080

   # Run the application
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
   ```  

2. **Build the Docker Image**:  
   When you run the docker build command, Docker looks for a file named Dockerfile in the directory by default unless you specify a different file name using the -f option  
      e.g., ```docker build -f CustomDockerfile .```

      ```bash
      docker build -t cis-calculator .
      ```

3. **Run Locally to Test**:

   ```bash
   docker run -p 8080:8080 cis-calculator
   ```

   - Test the API by sending requests to `http://localhost:8080`.

## Step 3: Deploy to Google Cloud Run

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

This approach ensures you have a minimal, functional setup for deploying Python services to Google Cloud Run, which you can expand as needed for your application's specific calculations and requirements.
