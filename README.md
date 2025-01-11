# CIS-calculator  

GREET CI Score calculator - python service  

**Note for GIT**
This folder is currently connected to the git repo:  
`... @github.com/ravah-dev/CIS-calculator.git`

You can check this by command line:  

```bash
git remote -v
```

You can change this using:  
`git remote set-url origin <url of new origin>`

## Basic Project Setup

1. **Directory cis-calculator**:  

2. **Virtual Environment**:  
    A **virtual environment** is an isolated Python environment where you can install libraries and packages specific to your project without affecting other Python projects or the system-wide Python installation.  
   - Create a virtual environment: `python3 -m venv venv`.
   - Activate it: `source venv/bin/activate`.

3. **Web Framework Libraries**:  
   Install the FastAPI web framework for handling API requests.  
    FastAPI:
    - Modern, fast framework leverages Python type hints for automatic API documentation
    - Great for building REST APIs quickly with excellent performance
    - Built-in support for async/await
    - Automatic OpenAPI (Swagger) documentation generation
    - Excellent for microservices and API-first applications
    - FastAPI's Pydantic models are particularly valuable for use with large data objects.  

     ```bash
     pip install fastapi uvicorn
     ```

4. **'main.py' Basic API app**:
   - Create a file `main.py`:

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

### 'Dockerfile' (no file extension)  

   ```dockerfile
   # Use an official Python runtime as a parent image
   FROM python:3.11-slim

   # Set the working directory in the container
   WORKDIR /app

   # Copy the current directory contents into the container at /app
   COPY . /app

   # Install dependencies
   RUN pip install --no-cache-dir -r requirements.txt

   # Make port 8080 available to the world outside this container
   EXPOSE 8080

   # Define environment variable for GCP Cloud Run
   ENV PORT=8080

   # Run the application
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
   ```

**Build the Docker Image**:

   ```bash
   docker build -t cis-calculator .
   ```

**Run Locally to Test**:

   ```bash
   docker run -p 8080:8080 cis-calculator
   ```

- Test the API by sending requests to `http://localhost:8080`.  

## Deploy to Google Cloud Run  

See 'gcr_deploy.md' for instructions...  

1. **Install the Google Cloud SDK**
2. **Authenticate with GCP**
3. **Enable Required APIs**
4. **Tag and Push the Image**:
5. **Deploy to Cloud Run**:
6. **Test Your API**  
  