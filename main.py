from fastapi import FastAPI, HTTPException
import uvicorn
from contextlib import asynccontextmanager
import logging
import os
# from pydantic import BaseModel
from typing import Dict, Any
from class_RefDataLoader import RefDataLoader
from class_soc_lookup import SOCLookup # for step 6 of calculator
from cis_calculator import calculator_function  # Import the calculator function

# app = FastAPI()

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

@app.get("/")
def read_root():
    return {"message": "Hello, This is the GREET Calculator API!"}

@app.post("/calculate")
async def calculate(data: Dict[str, Any]):
    """
    Endpoint to perform calculations using the calculator function.

    Args:
        data (CalculationInput): Input data from the POST request.

    Returns:
        dict: Calculation results.
    """
    try:
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
