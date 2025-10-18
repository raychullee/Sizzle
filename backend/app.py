"""
Main FastAPI application module for the Sizzle backend.

This module defines the API endpoints and connects all the 
backend components together.
"""

# Import from standard library
import os
import json
import time
import random
import re
from typing import List, Optional, Dict, Any, Union

# Import from FastAPI framework
from fastapi import FastAPI, HTTPException, Depends, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Import from third-party libraries 
# Pydantic already imported above

# Import local modules
import setup_env
from config import (
    API_CORS_ORIGINS, API_DEBUG, STATIC_DIR, TEMP_DIR,
    OPENAI_API_KEY, OCI_BUCKET_NAME
)
from utils import (
    logger, format_api_response, format_error_response, 
    format_oci_url, log_exception
)
from database import (
    get_database_status, execute_query_dict, 
    execute_query_dict_single_row
)
from recipe_assistant import RecipeAssistant
from oci_storage import OCIObjectStorage

# Create directories for static files if they don't exist
os.makedirs(os.path.join(STATIC_DIR, "animations/actions"), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "animations/ingredients"), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "images/ingredients"), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "images/actions"), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "images/steps"), exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# Initialize the FastAPI application
app = FastAPI(
    title="Sizzle API",
    description="API for Sizzle recipe assistant",
    version="1.0.0",
    debug=API_DEBUG
)

# Set up CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=API_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
recipe_assistant = RecipeAssistant()
oci_storage = OCIObjectStorage()


# Mount static files directory
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Setup request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log request information and timing."""
    start_time = time.time()
    
    # Process the request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log request details
    logger.info(
        f"{request.method} {request.url.path} "
        f"- Status: {response.status_code} "
        f"- Time: {process_time:.3f}s"
    )
    
    return response

# API Models
class RecipeQuery(BaseModel):
    query: str = Field(..., description="The recipe query or search term")
    
class IngredientCreate(BaseModel):
    name: str = Field(..., description="Ingredient name")
    url: Optional[str] = Field(None, description="Image URL")
    prompt: Optional[str] = Field(None, description="Image generation prompt")
    
class IngredientResponse(BaseModel):
    id: int
    name: str
    url: Optional[str] = None
    prompt: Optional[str] = None
    
class RecipeResponse(BaseModel):
    id: int
    title: str
    description: str
    prep_time: str
    cook_time: str
    servings: int
    ingredients: List[Dict[str, Any]]
    equipment: List[Dict[str, Any]]
    steps: List[Dict[str, Any]]

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    log_exception(exc, f"Unhandled exception in {request.method} {request.url.path}")
    
    # Determine if this is a known exception type
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=format_error_response(exc.detail, exc.status_code)
        )
    
    # Handle unexpected errors
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=format_error_response(
            "An unexpected error occurred",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            {"type": type(exc).__name__} if API_DEBUG else None
        )
    )

# API Status route
@app.get("/api-status")
async def get_api_status():
    """Get the status of the API and its dependencies."""
    # Check database connection
    db_status = get_database_status()
    
    # Check if OpenAI API key is configured
    openai_configured = bool(OPENAI_API_KEY)
    
    # Check OCI storage
    oci_configured = bool(OCI_BUCKET_NAME)
    
    return format_api_response({
        "status": "online",
        "timestamp": time.time(),
        "version": "1.0.0",
        "dependencies": {
            "database": db_status,
            "openai": {"configured": openai_configured},
            "oci_storage": {"configured": oci_configured}
        }
    })

# Recipe parsing endpoint
@app.post("/recipe/parse")
async def parse_recipe(query: RecipeQuery):
    """Parse a recipe query and return structured recipe data."""
    try:
        # Generate recipe from query
        recipe_data = recipe_assistant.generate_recipe(query.query)
        
        if not recipe_data:
            raise HTTPException(
                status_code=404,
                detail="Could not generate a recipe for the given query"
            )
            
        return format_api_response(recipe_data)
    except Exception as e:
        log_exception(e, "Error parsing recipe")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse recipe: {str(e)}"
        )

# Recipe search endpoint
@app.get("/recipes")
async def list_recipes(
    limit: int = 10, 
    offset: int = 0,
    search: Optional[str] = None
):
    """List recipes with optional search and pagination."""
    try:
        # Build the query
        query = "SELECT * FROM recipes"
        params = []
        
        # Add search condition if provided
        if search:
            query += " WHERE title ILIKE %s OR description ILIKE %s"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])
        
        # Add pagination
        query += " ORDER BY id DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        # Execute the query
        recipes = execute_query_dict(query, tuple(params))
        
        # Get total count for pagination
        count_query = "SELECT COUNT(*) FROM recipes"
        if search:
            count_query += " WHERE title ILIKE %s OR description ILIKE %s"
            count_params = [f"%{search}%", f"%{search}%"]
        else:
            count_params = []
            
        count_result = execute_query_dict_single_row(count_query, tuple(count_params))
        total_count = count_result.get('count', 0) if count_result else 0
        
        return format_api_response({
            "recipes": recipes,
            "total": total_count,
            "limit": limit,
            "offset": offset
        })
    except Exception as e:
        log_exception(e, "Error listing recipes")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list recipes: {str(e)}"
        )
        
# Get recipe by ID
@app.get("/recipes/{recipe_id}")
async def get_recipe(recipe_id: int):
    """Get a recipe by ID with all related data."""
    try:
        # Get the recipe
        recipe_query = "SELECT * FROM recipes WHERE id = %s"
        recipe = execute_query_dict_single_row(recipe_query, (recipe_id,))
        
        if not recipe:
            raise HTTPException(
                status_code=404,
                detail=f"Recipe with ID {recipe_id} not found"
            )
            
        # Get ingredients for the recipe
        ingredients_query = "SELECT * FROM recipe_ingredients WHERE recipe_id = %s"
        ingredients = execute_query_dict(ingredients_query, (recipe_id,))
        
        # Get equipment for the recipe
        equipment_query = "SELECT * FROM recipe_equipment WHERE recipe_id = %s"
        equipment = execute_query_dict(equipment_query, (recipe_id,))
        
        # Get steps for the recipe
        steps_query = "SELECT * FROM recipe_steps WHERE recipe_id = %s ORDER BY id"
        steps = execute_query_dict(steps_query, (recipe_id,))
        
        # For each step, get its ingredients and equipment
        for step in steps:
            step_id = step['id']
            
            # Get step ingredients
            step_ingredients_query = """
                SELECT ri.* FROM step_ingredients si
                JOIN recipe_ingredients ri ON si.ingredient_id = ri.id
                WHERE si.step_id = %s
            """
            step['ingredients'] = execute_query_dict(step_ingredients_query, (step_id,))
            
            # Get step equipment
            step_equipment_query = """
                SELECT re.* FROM step_equipment se
                JOIN recipe_equipment re ON se.equipment_id = re.id
                WHERE se.step_id = %s
            """
            step['equipment'] = execute_query_dict(step_equipment_query, (step_id,))
            
            # Ensure image URLs are properly formatted
            if step.get('action_image'):
                step['action_image'] = format_oci_url(step['action_image'])
            if step.get('step_image'):
                step['step_image'] = format_oci_url(step['step_image'])
        
        # Add the related data to the recipe
        recipe['ingredients'] = ingredients
        recipe['equipment'] = equipment
        recipe['steps'] = steps
        
        return format_api_response(recipe)
    except HTTPException:
        raise
    except Exception as e:
        log_exception(e, f"Error getting recipe {recipe_id}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recipe: {str(e)}"
        )

# Ingredients endpoints
@app.get("/ingredients")
async def list_ingredients(
    limit: int = 10, 
    offset: int = 0,
    search: Optional[str] = None
):
    """List ingredients with optional search and pagination."""
    try:
        # Use supabase client directly
        from database import supabase_client
        
        # Create query on generated_images table with type=ingredient
        query = supabase_client.table("generated_images").select("*").eq("type", "ingredient")
        
        # Add search filter if provided - use case-insensitive search
        if search:
            # Make the search case-insensitive
            query = query.ilike("name", f"%{search}%")
            logger.info(f"Adding search filter: '{search}'")
        
        # For ordering by ID instead of name
        query = query.order("id")
        
        # Get total count for this query (with any search filters)
        count_result = query.execute()
        total_count = len(count_result.data) if count_result.data else 0
        logger.info(f"Total count: {total_count}" + (f" with search filter '{search}'" if search else ""))
        
        # If search is active and no results, try a more flexible search
        if search and total_count == 0:
            # Try with each word in the search query
            search_words = search.split()
            logger.info(f"No results with exact search, trying with individual words: {search_words}")
            
            # Try each word individually
            for word in search_words:
                if len(word) >= 3:  # Only use words with at least 3 characters
                    test_query = supabase_client.table("generated_images").select("id").eq("type", "ingredient").ilike("name", f"%{word}%")
                    test_result = test_query.execute()
                    if test_result.data and len(test_result.data) > 0:
                        logger.info(f"Found {len(test_result.data)} results with word '{word}'")
                        # Use this word for the actual query
                        query = supabase_client.table("generated_images").select("*").eq("type", "ingredient").ilike("name", f"%{word}%")
                        total_count = len(test_result.data)
                        break
        
        # Add pagination to the query
        query_with_pagination = query
        
        if limit:
            query_with_pagination = query_with_pagination.limit(limit)
        if offset:
            end_range = offset + limit - 1
            query_with_pagination = query_with_pagination.range(offset, end_range)
            
        # Execute the query
        result = query_with_pagination.execute()
        ingredients = result.data if result.data else []
        
        # Format URLs if needed
        for ingredient in ingredients:
            if ingredient.get('url'):
                ingredient['url'] = format_oci_url(ingredient['url'])
        
        return format_api_response({
            "ingredients": ingredients,
            "total": total_count,
            "limit": limit,
            "offset": offset
        })
            
    except Exception as e:
        log_exception(e, "Error listing ingredients")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list ingredients: {str(e)}"
        )

@app.get("/ingredients/{ingredient_id}")
async def get_ingredient(ingredient_id: int):
    """Get an ingredient by ID."""
    try:
        from database import supabase_client
        
        # Get ingredient by ID from generated_images table with type=ingredient
        result = supabase_client.table("generated_images").select("*").eq("id", ingredient_id).eq("type", "ingredient").execute()
        
        if not result.data or len(result.data) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Ingredient with ID {ingredient_id} not found"
            )
            
        ingredient = result.data[0]
        
        # Format URL if needed
        if ingredient.get('url'):
            ingredient['url'] = format_oci_url(ingredient['url'])
            
        return format_api_response(ingredient)
    except HTTPException:
        raise
    except Exception as e:
        log_exception(e, f"Error getting ingredient {ingredient_id}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get ingredient: {str(e)}"
        )

# Main entry point
if __name__ == "__main__":
    import uvicorn
    from config import API_HOST, API_PORT
    
    logger.info(f"Starting Sizzle API on {API_HOST}:{API_PORT}")
    uvicorn.run("app:app", host=API_HOST, port=API_PORT, reload=API_DEBUG)
