# main.py - Entry point for the application
# -- Modified from 'main_working.py' to handle API KEY Validation

import os
import sys
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.security.api_key import APIKeyHeader
from contextlib import asynccontextmanager

# Logger setup
print("Setting up logging...", file=sys.stderr)
logging.basicConfig(
    level=logging.DEBUG, # for testing, change to logging.INFO for production
    # level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # Explicitly log to stderr
)
logger = logging.getLogger(__name__)
logger.info("Logger initialized")

# API Key configuration -- for using the fastapi.security.api_key module
API_KEY_NAME = "X-API-Key"  # The header name clients will need to use
API_KEY = os.getenv("API_KEY")  # This will get the key we just set in Cloud Run
# api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False) # for debugging purposes

# API key validation function (for passed-in google api key)
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
        raise HTTPException(status_code=500, detail="API key not configured -craig")
    
    # Validate the key
    if api_key != expected_key:
        logger.warning("Invalid API key provided")
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    logger.info("API key validated successfully")
    return api_key


# from pydantic import BaseModel
from typing import Dict, Any
from class_RefDataLoader import RefDataLoader
from class_soc_lookup import SOCLookup # for step 6 of calculator
from cis_calculator import calculator_function  # Import the calculator function

print("Starting application...", file=sys.stderr)  # This will go to container logs

# Initialize the lookup tools (one each for corn and soybean)
soc = SOCLookup("corn_soc.csv", "soybean_soc.csv")
logger.info("SOC Lookup tables loaded successfully.")

# Configuration
REF_VARS_PATH = "GREET_ref_vars.csv"
EXCEL_FILE_PATH = "Feedstock CI Calculator 2023 - Standalone Version.xlsm"
global_variables = {}

# Function to initialize GREET Reference global variables
def initialize_global_variables(refData_reader):
    """
    Initialize global variables from the RefDataLoader instance.
    
    Args:
        refData_reader: RefDataLoader instance containing loaded variables.
    """
    variables = refData_reader.get_all_variables()
    
    for var_name, value in variables.items():
        # Create a valid Python variable name (replace any invalid characters)
        python_var_name = var_name.replace('-', '_').replace(' ', '_')
        global_variables[python_var_name] = value
        
    # log the length of created global variables for testing
    logger.info(f"Created {len(global_variables)} global variables")
        
    # global_variables.update(variables)

# Lifespan context manager for FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    try:
        port = os.getenv("PORT", "8080")
        logger.info(f"FastAPI starting up on port {port}")
        logger.info(f"Current working directory: {os.getcwd()}")
        logger.info(f"Environment variables: {dict(os.environ)}")
        
        if not os.path.exists(REF_VARS_PATH):
            raise FileNotFoundError(f"Reference variables file not found: {REF_VARS_PATH}")
        if not os.path.exists(EXCEL_FILE_PATH):
            raise FileNotFoundError(f"Excel file not found: {EXCEL_FILE_PATH}")

        logger.info("line 53, Initializing RefDataLoader...")
        refData_reader = RefDataLoader(REF_VARS_PATH)
        refData_reader.load_from_excel(EXCEL_FILE_PATH)
        
        # Check for any missing variables
        missing = refData_reader.validate_all_variables_present()
        if missing:
            logger.warning(f"Warning: Missing variables: {missing}")
            
        # Initialize global variables from the RefDataLoader instance
        initialize_global_variables(refData_reader)
        logger.info("line 66 Startup completed successfully.")
        yield  # Hand over control to the app
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

    # Shutdown logic (if needed)
    finally:
        logger.info("Application shutdown cleanup (if any).")

# Create FastAPI app with the lifespan context manager
app = FastAPI(lifespan=lifespan)

# Add API key protection to your endpoints
# @app.get("/", dependencies=[Depends(verify_api_key)]) # when using fastapi.security.api_key
@app.get("/")
async def read_root(request: Request):
    await validate_api_key(request)
    return {"message": "Hello, This is the GREET Calculator API!"}

# @app.post("/calculate", dependencies=[Depends(verify_api_key)]) # when using fastapi.security.api_key
@app.post("/calculate") # -- for testing using the google cloud generated api key credential
async def calculate(data: Dict[str, Any], request: Request):
    await validate_api_key(request)
    """
    Endpoint to perform calculations using the calculator function.

    Args:
        data (CalculationInput): Input data from the POST request.

    Returns:
        dict: Calculation results.
    """
    try:
        # set the port number from the environment variable, defaulting to 8080 if not set
        port = os.getenv("PORT", "8080")
        logger.info(f"FastAPI starting up on port {port}")
        
        # *** Log the received input - debugging purposes
        # logger.info(f"Received input: {data}")

        # Call the calculator function
        result = calculator_function(data, global_variables, logger, soc)

        # # Log the result for TEST
        # logger.info(f"Calculation result: {result}") # for debugging

        return result
    except Exception as e:
        logger.error(f"line 107 Calculation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
