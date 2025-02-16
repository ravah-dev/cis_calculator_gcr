# main.py - Entry point for the application
# --- This is the current version (v3.2)

# folder: git-local-d/cis_calculator_gcr
# -- Modified from 'main_working.py' to handle GOOGLE API KEY Validation

"""
    This folder is currently connected to the git repo:  
        `... @github.com/ravah-dev/cis-calculator_gcr.git`
        - see README.md for more details.
        
    main.py creates a FastAPI application with API key validation.
    It defines global functions & sets up the http listener service and exposes two endpoints:
    - one for accessing a resource GET / (root) returns default greeting for testing purposes
    - one for sending a payload POST /calculate returns calculated results
        - checks the API_Key 
        - initializes global variables using the asynccontextmanager
        - then passes request data to the main calculate function imported from cis_calculator.py
        - finally passes the results back to the client in a response
    
    API Key validation can be done using the fastapi.security.api_key module.
    - see section "API Key configuration" for more details.
    This version now uses google generated key & GCR environment variables for API_KEY validation.
    
    GCR deployment
    - see md doc "gcloud_buildpacks_deploy" for more details.
"""

import os
import sys
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.security.api_key import APIKeyHeader
from contextlib import asynccontextmanager

from typing import Dict, Any
from class_RefDataLoader import RefDataLoader
from class_soc_lookup import SOCLookup # for step 6 of calculator
from cis_calculator import calculator_function  # Import the calculator function

print("Starting application...", file=sys.stderr)  # This will go to container logs

# LOGGER SETUP
print("Setting up logging...", file=sys.stderr)
logging.basicConfig(
    level=logging.DEBUG, # for testing, change to logging.INFO for production
    # level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # Explicitly log to stderr
)
logger = logging.getLogger(__name__)
logger.info("Logger initialized")


# Initialize the lookup tools (one each for corn and soybean)
soc = SOCLookup("corn_soc.csv", "soybean_soc.csv")
logger.info("SOC Lookup tables loaded successfully.")

# Configuration
REF_VARS_PATH = "GREET_ref_vars.csv"
EXCEL_FILE_PATH = "Feedstock CI Calculator 2023 - Standalone Version.xlsm"
global_variables = {}

# FUNCTION -- initialize_global_variables
# - initialize GREET Reference global variables
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

# FUNCTION -- lifespan (context manager for FastAPI)
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

# -------------------------------------------------------------------------------------------
# # ====== This section is here to show how to use the fastapi.security.api_key module ======
# # API Key configuration -- for using the fastapi.security.api_key module
# API_KEY_NAME = "X-API-Key"  # The header name clients will need to use
# API_KEY = os.getenv("API_KEY")  # This will get the key we just set in Cloud Run environment
# # api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)
# api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False) # for debugging purposes
# # ------ End of FastAPI Key configuration section -----------------------------------------

# FUNCTION -- validate_api_key
# - API key validation (for passed-in google api key)
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

# ---- / endpoint definition -----------------------------------------------
# FUNCTION -- read_root
# - Endpoint to handle the root path get request
# # <example> Protect root call using fastapi.security.api_key (deprecated)
# @app.get("/", dependencies=[Depends(verify_api_key)]) # when using fastapi.security.api_key

@app.get("/")
async def read_root(request: Request):
    await validate_api_key(request) # check api credential key (google cloud generated api key)
    return {"message": "Hello, This is the GREET Calculator API!"}
# ---- End of / endpoint definition ----------------------------------------

# ---- /calculate endpoint definition -----------------------------------------------
# FUNCTION -- calculate
# - Endpoint to handle the /calculate post request
# # <example> Protect /calculate call using fastapi.security.api_key (deprecated)
# @app.post("/calculate", dependencies=[Depends(verify_api_key)]) # when using fastapi.security.api_key

@app.post("/calculate") # -- for testing using the google cloud generated api key credential
async def calculate(data: Dict[str, Any], request: Request):
    
    # check api credential key (google cloud generated api key)
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

        # ----- Call calculator_function ----
        result = calculator_function(data, global_variables, logger, soc)

        # # Log the result for TEST
        # logger.info(f"Calculation result: {result}") # for debugging

        return result
    except Exception as e:
        logger.error(f"line 107 Calculation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
# ---- End of /calculate endpoint definition -------------------------------------------