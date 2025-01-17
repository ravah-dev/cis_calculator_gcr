import sys
import os
from fastapi import FastAPI

# Write to stderr immediately on startup
sys.stderr.write("Container starting...\n")
sys.stderr.flush()

# Print environment variables
sys.stderr.write(f"Environment variables: {dict(os.environ)}\n")
sys.stderr.flush()

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

# Add an on_startup event handler
@app.on_startup
async def startup_event():
    sys.stderr.write("FastAPI startup event triggered\n")
    sys.stderr.flush()