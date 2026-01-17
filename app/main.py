import os
import asyncio
from fastapi import FastAPI, UploadFile, Request, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from azure.storage.blob import BlobServiceClient
from .processor import process_pdf # <--- Import your Gemini logic
from .cooking_agent import get_cooking_agent
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


# Cooking Agent Endpoints
@app.post("/api/cooking/chat")
async def cooking_chat(request: Request):
    """Chat with the cooking AI agent."""
    try:
        data = await request.json()
        user_message = data.get("message", "").strip()
        
        if not user_message:
            return JSONResponse({"error": "Message cannot be empty"}, status_code=400)
        
        logging.info(f"Cooking agent received message: {user_message}")
        
        try:
            # Get the cooking agent
            agent = await get_cooking_agent()
            
            # Process the message with timeout
            import asyncio
            response = await asyncio.wait_for(agent.chat(user_message), timeout=30.0)
            
            return JSONResponse({
                "response": response,
                "status": "success"
            })
        except asyncio.TimeoutError:
            logging.error("Cooking agent timeout - GitHub API may be slow")
            return JSONResponse({
                "error": "Agent response timed out. Please try again. Make sure GITHUB_TOKEN is set correctly.",
                "status": "error"
            }, status_code=504)
        
    except Exception as e:
        logging.error(f"Error in cooking chat: {str(e)}")
        return JSONResponse({
            "error": f"Error processing request: {str(e)}",
            "status": "error"
        }, status_code=500)


@app.get("/api/cooking/recipes")
async def get_recipes(ingredients: str = "", cuisine: str = "any"):
    """Get recipes based on ingredients and cuisine."""
    try:
        ingredient_list = [ing.strip() for ing in ingredients.split(",") if ing.strip()]
        
        if not ingredient_list:
            return JSONResponse({"error": "At least one ingredient is required"}, status_code=400)
        
        from .cooking_agent import search_recipes
        result = search_recipes(ingredient_list, cuisine)
        
        return JSONResponse({
            "recipes": result,
            "ingredients": ingredient_list,
            "cuisine": cuisine,
            "status": "success"
        })
    except Exception as e:
        logging.error(f"Error getting recipes: {str(e)}")
        return JSONResponse({
            "error": str(e),
            "status": "error"
        }, status_code=500)


@app.post("/api/cooking/extract-ingredients")
async def extract_ingredients_endpoint(request: Request):
    """Extract ingredients from recipe text."""
    try:
        data = await request.json()
        recipe_text = data.get("recipe_text", "").strip()
        
        if not recipe_text:
            return JSONResponse({"error": "Recipe text cannot be empty"}, status_code=400)
        
        from .cooking_agent import extract_ingredients
        result = extract_ingredients(recipe_text)
        
        return JSONResponse({
            "ingredients": result,
            "status": "success"
        })
    except Exception as e:
        logging.error(f"Error extracting ingredients: {str(e)}")
        return JSONResponse({
            "error": str(e),
            "status": "error"
        }, status_code=500)
