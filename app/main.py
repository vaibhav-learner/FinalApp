import os
from fastapi import FastAPI, UploadFile, Request, File
from fastapi.templating import Jinja2Templates
from azure.storage.blob import BlobServiceClient
from .processor import process_pdf # <--- Import your Gemini logic
from dotenv import load_dotenv

import logging
logging.basicConfig(level=logging.INFO)


load_dotenv()
app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload_file(request: Request, file: UploadFile = File(...)):
    logging.info(f"Received file: {file.filename}")

    content = await file.read()
    
    # 1. Save to Local Azure (Azurite)
    conn_str = os.getenv("AZURE_STORAGE_CONN")
    blob_service_client = BlobServiceClient.from_connection_string(conn_str)
    blob_client = blob_service_client.get_blob_client(container="pdf-uploads", blob=file.filename)
    blob_client.upload_blob(content, overwrite=True)

    # 2. Process with Gemini AI
    ai_results = await process_pdf(content)
    
    # 3. Add the filename to the results for the UI
    ai_results["filename"] = file.filename

    # 4. Return to the same page with the AI data
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "result": ai_results}
    )