# cis_calculator_gcr

GREET CI Score calculator - python service  
This version is set up for Google Cloud Run (GCR) deployment  

**Note for GIT**
This folder is currently connected to the git repo:  
`... @github.com/ravah-dev/cis-calculator_gcr.git`

You can check this by command line:  

```bash
git remote -v
```

You can change this using:  
`git remote set-url origin <url of new origin>`

## Basic Project Setup

1. **Directory cis_calculator_gcr**:  

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
   FROM python:3.9-slim

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

---

#### **Explanation of CMD[xx]**

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

#### **How It Works in Docker**
1. When the container starts, Docker runs the `CMD` instruction.
2. `uvicorn` starts the FastAPI application defined in `main.py` and makes it accessible on `http://0.0.0.0:8080` within the container.
3. If you’ve mapped the container port to a host port (e.g., `-p 8080:8080` in Docker run), you can access the application from your machine using `http://localhost:8080`.

---

### **Example Usage**
#### Building the Image:
```bash
docker build -t my-fastapi-app .
```

#### Running the Container:
```bash
docker run -p 8080:8080 my-fastapi-app
```

#### Accessing the Application:
Open your browser or use a tool like `curl` or Postman to access:
```bash
http://localhost:8080
```

---

### **Customizing the Command**
You can override the `CMD` in your `Dockerfile` when running the container:
```bash
docker run -p 8080:8080 my-fastapi-app uvicorn main:app --host 0.0.0.0 --port 9090
```
This runs the app on port `9090` instead of the default `8080`.

---

Let me know if you need more details or further clarification! 😊


**Build the Docker Image**:

   ```bash
   docker build -t cis-calculator .
   ```

**Run Locally to Test**:

   ```bash
   docker run -p 8080:8080 cis-calculator
   ```

- Test the API by sending requests to `http://localhost:8080`.  
  
# Deploy to Google Cloud Run  

See 'gcr_deploy.md' for instructions...  

1. **Install the Google Cloud SDK**
2. **Authenticate with GCP**
3. **Enable Required APIs**
4. **Tag and Push the Image**:
5. **Deploy to Cloud Run**:
6. **Test Your API**  
  