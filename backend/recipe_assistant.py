"""
Recipe Assistant module for generating structured recipes.

This module provides functionality to generate detailed, structured recipes
from user queries using large language models.
"""

import os
import json
import re
from typing import List, Dict, Any, Optional

# Local imports
from setup_env import setup_virtual_env
setup_virtual_env()

# Import from third-party libraries
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

# Local imports
from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TIMEOUT
from utils import logger, log_exception, parse_json_safely

class RecipeAssistant:
    """Assistant for generating structured recipe data."""
    
    def __init__(self, api_key: str = None):
        """
        Initialize the recipe assistant.
        
        Args:
            api_key: Optional OpenAI API key (defaults to environment variable)
        """
        # Use provided API key or environment variable
        self.api_key = api_key or OPENAI_API_KEY
        
        if not self.api_key:
            logger.warning("OpenAI API key is not set. Recipe generation will not work.")
            
        # Initialize the language model
        self.llm = ChatOpenAI(
            model=OPENAI_MODEL,
            openai_api_key=self.api_key,
            request_timeout=OPENAI_TIMEOUT
        )
        
        # Initialize chat history
        self.chat_history = []
        
        # Setup the recipe generation prompt
        self.recipe_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert chef and cooking instructor who provides detailed, structured recipes.

            When asked about a recipe, always respond with this exact format (without any introduction or conclusion):

            # [Recipe Title]

            ## Equipment
            - [Equipment item 1]
            - [Equipment item 2]
            - ...

            ## Ingredients
            - [Quantity] [Ingredient 1]
            - [Quantity] [Ingredient 2]
            - ...

            ## Preparation Time
            [Time in minutes or hours]

            ## Cooking Time
            [Time in minutes or hours]

            ## Servings
            [Number of servings]

            ## Instructions
            1. [Step 1 instruction]
               Action: [Main cooking action]
               Ingredients: [Ingredients used in step]
               Equipment: [Equipment used in step]
            
            2. [Step 2 instruction]
               Action: [Main cooking action]
               Ingredients: [Ingredients used in step]
               Equipment: [Equipment used in step]
            
            ...and so on for all steps.

            ## Description
            [Brief description of the dish and its origins or characteristics]
            
            Remember, actions should be concise (single word or short phrase) like "chop", "mix", "bake", "stir", etc. Each step should only include ingredients and equipment actually used in that step.
            """),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{recipe_query}")
        ])
        
        # Setup the JSON conversion prompt
        self.json_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful AI assistant that converts recipe text into JSON format.
            
            Convert the recipe text into a valid JSON object with this structure:
            
            {{
              "title": "Recipe Title",
              "equipment": [
                {{"name": "Equipment item 1"}},
                {{"name": "Equipment item 2"}}
              ],
              "ingredients": [
                {{"name": "Ingredient 1", "quantity": "Amount"}},
                {{"name": "Ingredient 2", "quantity": "Amount"}}
              ],
              "prep_time": "Preparation time",
              "cook_time": "Cooking time",
              "servings": 4,
              "steps": [
                {{
                  "id": 1,
                  "instruction": "Step instruction",
                  "action": "Main cooking action (single word or short phrase)",
                  "ingredients": [
                    {{"name": "Ingredient used", "quantity": "Amount used (if specified)"}}
                  ],
                  "equipment": [
                    {{"name": "Equipment used"}}
                  ]
                }}
              ],
              "description": "Recipe description"
            }}
            
            Important notes:
            1. Only include ingredients and equipment actually used in each step
            2. Actions should be concise verbs like "chop", "mix", "bake"
            3. For servings, convert text to an integer
            4. Make sure all nested arrays have the correct structure
            5. Ensure the JSON is valid - use double quotes for keys and string values
            6. Output ONLY the JSON object with no additional text or explanation
            """),
            ("human", "{recipe_text}\n\nTitle: {title}")
        ])
    
    def generate_recipe(self, query: str) -> Dict[str, Any]:
        """
        Generate a structured recipe from a user query.
        
        Args:
            query: User query for a recipe
            
        Returns:
            Structured recipe data as a dictionary
        """
        if not self.api_key:
            logger.error("Cannot generate recipe: OpenAI API key is not set")
            return None
            
        try:
            # Generate the recipe in markdown format
            recipe_chain = self.recipe_prompt | self.llm
            recipe_text = recipe_chain.invoke({
                "recipe_query": query,
                "chat_history": self.chat_history
            }).content
            
            # Extract title from recipe text
            title_match = re.search(r'^# (.+?)$', recipe_text, re.MULTILINE)
            title = title_match.group(1) if title_match else "Recipe"
            
            # Convert the markdown to JSON
            json_chain = self.json_prompt | self.llm
            json_text = json_chain.invoke({
                "recipe_text": recipe_text,
                "title": title
            }).content
            
            # Parse the JSON
            try:
                # Clean up the response to ensure it's valid JSON
                # Remove any markdown code block markers
                json_text = re.sub(r'^```json\s*', '', json_text)
                json_text = re.sub(r'\s*```$', '', json_text)
                
                # Parse the JSON
                recipe_data = json.loads(json_text)
                
                # Ensure the data has the required structure
                self._validate_recipe_data(recipe_data)
                
                # Search for matching recipes (for demo purposes, return one recipe)
                return {
                    "matching_recipes": [recipe_data]
                }
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse recipe JSON: {str(e)}")
                logger.debug(f"Raw JSON: {json_text}")
                return None
        except Exception as e:
            log_exception(e, "Error generating recipe")
            return None
    
    def _validate_recipe_data(self, data: Dict[str, Any]) -> None:
        """
        Validate and clean up recipe data.
        
        Args:
            data: Recipe data dictionary to validate
            
        Raises:
            ValueError: If the data is missing required fields
        """
        # Ensure required top-level fields exist
        required_fields = ["title", "ingredients", "steps", "description"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Recipe data missing required field: {field}")
                
        # Ensure servings is an integer
        if "servings" in data and not isinstance(data["servings"], int):
            try:
                data["servings"] = int(data["servings"])
            except (ValueError, TypeError):
                data["servings"] = 4  # Default value
                
        # Ensure steps have required fields
        for i, step in enumerate(data.get("steps", [])):
            if "id" not in step:
                step["id"] = i + 1
            if "instruction" not in step:
                raise ValueError(f"Step {i+1} missing required field: instruction")
            if "action" not in step:
                raise ValueError(f"Step {i+1} missing required field: action")
            
            # Ensure step has ingredients and equipment lists
            if "ingredients" not in step:
                step["ingredients"] = []
            if "equipment" not in step:
                step["equipment"] = []
