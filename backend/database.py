"""
Database connection management module for the Sizzle application.

This module provides a simplified interface for database operations using 
Supabase, with fallback to sample data if not available.
"""

import os
import time
import contextlib
from typing import Dict, List, Optional, Any, Generator, Tuple
import json

# Local imports
from config import SUPABASE_URL, SUPABASE_KEY
from utils import logger, log_exception

# Sample recipe data for when database is not available
SAMPLE_RECIPES = {
    "sushi": {
        "id": 1,
        "title": "Sushi Rice",
        "description": "Perfect sushi rice is the foundation of good sushi",
        "prep_time": "10 minutes",
        "cook_time": "20 minutes",
        "servings": 4,
        "ingredients": [
            {"id": 1, "name": "Japanese short-grain rice", "quantity": "2 cups"},
            {"id": 2, "name": "Water", "quantity": "2 cups"},
            {"id": 3, "name": "Rice vinegar", "quantity": "1/4 cup"},
            {"id": 4, "name": "Sugar", "quantity": "2 tablespoons"},
            {"id": 5, "name": "Salt", "quantity": "1 teaspoon"}
        ],
        "equipment": [
            {"id": 1, "name": "Rice cooker or pot with lid"},
            {"id": 2, "name": "Wooden spoon"}
        ],
        "steps": [
            {
                "id": 1,
                "instruction": "Rinse the rice until water runs clear",
                "action": "rinse",
                "ingredients": [{"id": 1, "name": "Japanese short-grain rice", "quantity": "2 cups"}],
                "equipment": []
            },
            {
                "id": 2,
                "instruction": "Cook the rice according to package instructions",
                "action": "cook",
                "ingredients": [
                    {"id": 1, "name": "Japanese short-grain rice", "quantity": "2 cups"},
                    {"id": 2, "name": "Water", "quantity": "2 cups"}
                ],
                "equipment": [{"id": 1, "name": "Rice cooker or pot with lid"}]
            },
            {
                "id": 3,
                "instruction": "Mix rice vinegar, sugar, and salt in a small bowl until dissolved",
                "action": "mix",
                "ingredients": [
                    {"id": 3, "name": "Rice vinegar", "quantity": "1/4 cup"},
                    {"id": 4, "name": "Sugar", "quantity": "2 tablespoons"},
                    {"id": 5, "name": "Salt", "quantity": "1 teaspoon"}
                ],
                "equipment": []
            },
            {
                "id": 4,
                "instruction": "Fold the vinegar mixture into the hot rice",
                "action": "fold",
                "ingredients": [],
                "equipment": [{"id": 2, "name": "Wooden spoon"}]
            }
        ]
    },
    "chocolate_cake": {
        "id": 2,
        "title": "Chocolate Cake",
        "description": "Rich and moist chocolate cake",
        "prep_time": "15 minutes",
        "cook_time": "35 minutes",
        "servings": 8,
        "ingredients": [
            {"id": 6, "name": "All-purpose flour", "quantity": "2 cups"},
            {"id": 7, "name": "Sugar", "quantity": "2 cups"},
            {"id": 8, "name": "Cocoa powder", "quantity": "3/4 cup"},
            {"id": 9, "name": "Baking powder", "quantity": "2 teaspoons"},
            {"id": 10, "name": "Baking soda", "quantity": "1 1/2 teaspoons"},
            {"id": 11, "name": "Salt", "quantity": "1 teaspoon"},
            {"id": 12, "name": "Eggs", "quantity": "2"},
            {"id": 13, "name": "Milk", "quantity": "1 cup"},
            {"id": 14, "name": "Vegetable oil", "quantity": "1/2 cup"},
            {"id": 15, "name": "Vanilla extract", "quantity": "2 teaspoons"},
            {"id": 16, "name": "Boiling water", "quantity": "1 cup"}
        ],
        "equipment": [
            {"id": 3, "name": "Mixing bowl"},
            {"id": 4, "name": "Cake pan"},
            {"id": 5, "name": "Electric mixer"}
        ],
        "steps": [
            {
                "id": 5,
                "instruction": "Preheat oven to 350°F (175°C). Grease and flour two 9-inch round cake pans.",
                "action": "preheat",
                "ingredients": [],
                "equipment": [{"id": 4, "name": "Cake pan"}]
            },
            {
                "id": 6,
                "instruction": "In a large bowl, combine flour, sugar, cocoa, baking powder, baking soda, and salt.",
                "action": "mix",
                "ingredients": [
                    {"id": 6, "name": "All-purpose flour", "quantity": "2 cups"},
                    {"id": 7, "name": "Sugar", "quantity": "2 cups"},
                    {"id": 8, "name": "Cocoa powder", "quantity": "3/4 cup"},
                    {"id": 9, "name": "Baking powder", "quantity": "2 teaspoons"},
                    {"id": 10, "name": "Baking soda", "quantity": "1 1/2 teaspoons"},
                    {"id": 11, "name": "Salt", "quantity": "1 teaspoon"}
                ],
                "equipment": [{"id": 3, "name": "Mixing bowl"}]
            },
            {
                "id": 7,
                "instruction": "Add eggs, milk, oil, and vanilla. Beat with mixer on medium speed for 2 minutes.",
                "action": "beat",
                "ingredients": [
                    {"id": 12, "name": "Eggs", "quantity": "2"},
                    {"id": 13, "name": "Milk", "quantity": "1 cup"},
                    {"id": 14, "name": "Vegetable oil", "quantity": "1/2 cup"},
                    {"id": 15, "name": "Vanilla extract", "quantity": "2 teaspoons"}
                ],
                "equipment": [{"id": 5, "name": "Electric mixer"}]
            },
            {
                "id": 8,
                "instruction": "Stir in boiling water. The batter will be thin.",
                "action": "stir",
                "ingredients": [{"id": 16, "name": "Boiling water", "quantity": "1 cup"}],
                "equipment": []
            },
            {
                "id": 9,
                "instruction": "Pour batter into prepared pans. Bake for 30-35 minutes or until a toothpick comes out clean.",
                "action": "bake",
                "ingredients": [],
                "equipment": [{"id": 4, "name": "Cake pan"}]
            }
        ]
    }
}

# Supabase client
supabase_client = None
supabase_available = False

def initialize_supabase():
    """Initialize Supabase client"""
    global supabase_client, supabase_available
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.warning("Supabase credentials not found. Using sample data.")
        return False
        
    try:
        from supabase import create_client
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info(f"Connected to Supabase at {SUPABASE_URL}")
        
        # Test connection
        test = supabase_client.table("recipes").select("id").limit(1).execute()
        logger.info("Supabase connection successful!")
        supabase_available = True
        return True
    except Exception as e:
        logger.error(f"Error connecting to Supabase: {str(e)}")
        logger.info("Using sample data instead.")
        return False

# Try to initialize Supabase
try:
    initialize_supabase()
except ImportError:
    logger.warning("Supabase package not installed. Using sample data.")
    supabase_available = False

def execute_query(query: str, params: Optional[Tuple] = None) -> List[Tuple]:
    """
    Executes a database query and returns results as tuples.
    
    Args:
        query: SQL query string
        params: Query parameters
        
    Returns:
        List of tuples representing result rows
    """
    if not supabase_available or not supabase_client:
        logger.warning(f"Database not available. Query was: {query}")
        return []
        
    try:
        # For simple SELECT queries, use Supabase client
        if 'SELECT' in query.upper():
            # Extract table name
            try:
                table_name = query.upper().split('FROM')[1].strip().split()[0].strip('"')
                table_name = table_name.lower()
                
                # Basic parameter parsing
                limit = 100  # Default limit
                offset = 0   # Default offset
                
                if 'LIMIT' in query.upper():
                    try:
                        limit_part = query.upper().split('LIMIT')[1].strip()
                        if 'OFFSET' in limit_part:
                            limit = int(limit_part.split('OFFSET')[0].strip())
                        else:
                            limit = int(limit_part)
                    except:
                        pass
                
                if 'OFFSET' in query.upper():
                    try:
                        offset = int(query.upper().split('OFFSET')[1].strip())
                    except:
                        pass
                
                # Use supabase client to fetch data
                supabase_query = supabase_client.table(table_name).select('*')
                
                if limit:
                    supabase_query = supabase_query.limit(limit)
                if offset:
                    range_end = offset + limit - 1
                    supabase_query = supabase_query.range(offset, range_end)
                
                result = supabase_query.execute()
                
                if 'COUNT(*)' in query.upper():
                    # Handle count queries specially
                    return [(len(result.data),)]
                
                # Convert to tuples
                return [(row,) for row in result.data] if result.data else []
            except Exception as e:
                logger.error(f"Error parsing or executing SELECT: {str(e)}")
                return []
        else:
            # For now, just return empty results for non-SELECT queries
            return []
                
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        logger.error(f"Query was: {query}")
        if params:
            logger.error(f"Params were: {params}")
        return []

def execute_query_dict(query: str, params: Optional[Tuple] = None) -> List[Dict]:
    """
    Executes a database query and returns results as dictionaries.
    
    Args:
        query: SQL query string
        params: Query parameters
        
    Returns:
        List of dictionaries representing result rows
    """
    if not supabase_available:
        # Just return an empty list if Supabase is not available
        return []
    
    try:
        # Simply extract table name and use Supabase directly
        if "FROM" in query.upper():
            table_name = query.upper().split("FROM")[1].strip().split()[0].strip('"').lower()
            
            # Handle COUNT queries
            if "COUNT(*)" in query.upper():
                # Just do a select and count the results
                result = supabase_client.table(table_name).select('id').execute()
                return [{"count": len(result.data) if result.data else 0}]
            
            # Basic parameter parsing
            limit = 100  # Default limit
            offset = 0   # Default offset
            
            if "LIMIT" in query.upper():
                try:
                    limit_part = query.upper().split("LIMIT")[1].strip()
                    if "OFFSET" in limit_part:
                        limit = int(limit_part.split("OFFSET")[0].strip())
                    else:
                        limit = int(limit_part)
                except:
                    pass
                    
            if "OFFSET" in query.upper():
                try:
                    offset = int(query.upper().split("OFFSET")[1].strip())
                except:
                    pass
            
            # Handle WHERE clauses
            where_condition = None
            if "WHERE" in query.upper():
                where_clause = query.upper().split("WHERE")[1].strip()
                if "LIMIT" in where_clause:
                    where_clause = where_clause.split("LIMIT")[0].strip()
                if "ORDER" in where_clause:
                    where_clause = where_clause.split("ORDER")[0].strip()
                
                # Only handle simple equals conditions for now
                if "=" in where_clause:
                    parts = where_clause.split("=")
                    if len(parts) == 2:
                        col_name = parts[0].strip().lower()
                        val = parts[1].strip()
                        # Remove quotes
                        if val.startswith("'") and val.endswith("'"):
                            val = val[1:-1]
                        where_condition = (col_name, val)
            
            # Construct and execute the query
            supabase_query = supabase_client.table(table_name).select('*')
            
            # Apply WHERE if present
            if where_condition:
                supabase_query = supabase_query.eq(where_condition[0], where_condition[1])
            
            # Apply LIMIT and OFFSET
            if limit:
                supabase_query = supabase_query.limit(limit)
            if offset:
                # In Supabase, range is inclusive
                end_range = offset + limit - 1
                supabase_query = supabase_query.range(offset, end_range)
            
            # Execute and return
            result = supabase_query.execute()
            return result.data if result.data else []
            
        # If we couldn't parse the query, return empty result
        return []
        
    except Exception as e:
        logger.error(f"Error executing dictionary query: {str(e)}")
        # Use sample data as fallback
        if "ingredients" in query.lower():
            return [
                {"id": 1, "name": "Salt", "url": "/static/images/ingredients/salt.png", "prompt": "2D flat icon of cooking salt, emoji style"},
                {"id": 2, "name": "Pepper", "url": "/static/images/ingredients/pepper.png", "prompt": "2D flat icon of black pepper, emoji style"},
                {"id": 3, "name": "Garlic", "url": "/static/images/ingredients/garlic.png", "prompt": "2D flat icon of cooking garlic, emoji style"}
            ]
        elif "recipes" in query.lower():
            return list(SAMPLE_RECIPES.values())
        else:
            return []

def execute_query_dict_single_row(query: str, params: Optional[Tuple] = None) -> Optional[Dict]:
    """
    Executes a database query and returns the first row as a dictionary or None.
    
    Args:
        query: SQL query string
        params: Query parameters
        
    Returns:
        Dictionary representing first result row or None
    """
    results = execute_query_dict(query, params)
    return results[0] if results else None

def get_database_status() -> Dict[str, Any]:
    """
    Checks the status of the database connection.
    
    Returns:
        A dictionary with database status information
    """
    if supabase_available and supabase_client:
        return {
            "status": "connected",
            "type": "supabase",
            "url": SUPABASE_URL[:20] + "..." if SUPABASE_URL else None,
            "error": None
        }
    else:
        return {
            "status": "using_sample_data",
            "type": "memory",
            "error": None
        }
