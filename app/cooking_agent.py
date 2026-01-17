"""
Cooking AI Agent using Microsoft Agent Framework with GitHub models.
Supports recipe search and ingredient extraction.
"""

import os
from typing import Annotated
from agent_framework import ChatAgent
from agent_framework.openai import OpenAIChatClient
from openai import AsyncOpenAI
import json


# Tool 1: Search for recipes by ingredients
def search_recipes(
    ingredients: Annotated[list[str], "List of ingredients to search for"],
    cuisine: Annotated[str, "Cuisine type (optional, e.g., Italian, Asian, Mexican)"] = "any",
) -> str:
    """Search for recipes based on available ingredients and cuisine preference."""
    # Simulated recipe database
    recipes_db = {
        "Italian": {
            "ingredients": ["tomato", "pasta", "garlic", "olive oil"],
            "recipes": [
                {"name": "Pasta Carbonara", "ingredients": ["pasta", "eggs", "bacon", "parmesan"]},
                {"name": "Tomato Basil Pasta", "ingredients": ["pasta", "tomato", "garlic", "basil"]},
                {"name": "Garlic Pasta", "ingredients": ["pasta", "garlic", "olive oil"]},
            ]
        },
        "Asian": {
            "ingredients": ["soy sauce", "ginger", "garlic", "rice"],
            "recipes": [
                {"name": "Stir Fry", "ingredients": ["soy sauce", "garlic", "ginger", "vegetables"]},
                {"name": "Fried Rice", "ingredients": ["rice", "soy sauce", "eggs", "vegetables"]},
                {"name": "Garlic Ginger Shrimp", "ingredients": ["shrimp", "garlic", "ginger"]},
            ]
        },
        "any": {
            "recipes": [
                {"name": "Vegetable Soup", "ingredients": ["vegetables", "water", "salt"]},
                {"name": "Eggs Scrambled", "ingredients": ["eggs", "butter", "salt"]},
                {"name": "Grilled Chicken", "ingredients": ["chicken", "salt", "pepper"]},
            ]
        }
    }
    
    matching_recipes = []
    cuisine_key = cuisine.capitalize() if cuisine != "any" else "any"
    
    recipes = recipes_db.get(cuisine_key, {}).get("recipes", recipes_db["any"]["recipes"])
    
    for recipe in recipes:
        ingredient_matches = sum(1 for ing in ingredients if ing.lower() in [i.lower() for i in recipe["ingredients"]])
        if ingredient_matches > 0:
            matching_recipes.append({
                "name": recipe["name"],
                "matched_ingredients": ingredient_matches,
                "all_ingredients": recipe["ingredients"]
            })
    
    if matching_recipes:
        result = f"Found {len(matching_recipes)} recipes:\n"
        for recipe in sorted(matching_recipes, key=lambda x: x["matched_ingredients"], reverse=True):
            result += f"- {recipe['name']} (matches {recipe['matched_ingredients']} ingredients: {', '.join(recipe['all_ingredients'])})\n"
        return result
    else:
        return f"No recipes found with {cuisine} cuisine and ingredients: {', '.join(ingredients)}"


# Tool 2: Extract ingredients from recipe description
def extract_ingredients(
    recipe_text: Annotated[str, "The recipe text to extract ingredients from"],
) -> str:
    """Extract ingredients from a recipe description or text."""
    # Common ingredient keywords
    ingredient_keywords = [
        "cup", "tablespoon", "teaspoon", "tbsp", "tsp", "oz", "grams", "g",
        "ml", "liter", "pound", "lb", "kg", "clove", "piece", "slice",
        "flour", "sugar", "salt", "pepper", "butter", "oil", "water",
        "eggs", "milk", "cheese", "tomato", "garlic", "onion", "potato",
        "rice", "pasta", "bread", "chicken", "beef", "fish", "shrimp",
        "vegetables", "herbs", "spices", "vanilla", "chocolate", "nuts"
    ]
    
    extracted = []
    words = recipe_text.lower().split()
    
    for i, word in enumerate(words):
        if any(keyword in word for keyword in ingredient_keywords):
            # Try to capture the ingredient with its quantity
            if i > 0:
                ingredient_phrase = f"{words[i-1]} {word}"
                if len(words) > i + 1:
                    ingredient_phrase += f" {words[i+1]}"
                extracted.append(ingredient_phrase)
            else:
                extracted.append(word)
    
    # Remove duplicates while preserving order
    unique_ingredients = []
    seen = set()
    for ing in extracted:
        if ing not in seen:
            unique_ingredients.append(ing)
            seen.add(ing)
    
    if unique_ingredients:
        return f"Extracted ingredients:\n" + "\n".join(f"- {ing}" for ing in unique_ingredients[:15])
    else:
        return "No ingredients found in the provided text."


# Tool 3: Get nutritional information estimate
def get_nutrition_info(
    dish_name: Annotated[str, "Name of the dish to get nutrition info for"],
) -> str:
    """Get estimated nutritional information for a dish."""
    nutrition_db = {
        "pasta carbonara": {"calories": 450, "protein": "20g", "carbs": "55g", "fat": "18g"},
        "tomato basil pasta": {"calories": 380, "protein": "12g", "carbs": "65g", "fat": "8g"},
        "stir fry": {"calories": 320, "protein": "25g", "carbs": "35g", "fat": "10g"},
        "fried rice": {"calories": 400, "protein": "15g", "carbs": "50g", "fat": "12g"},
        "vegetable soup": {"calories": 120, "protein": "5g", "carbs": "20g", "fat": "2g"},
        "grilled chicken": {"calories": 280, "protein": "40g", "carbs": "0g", "fat": "12g"},
    }
    
    info = nutrition_db.get(dish_name.lower())
    if info:
        return f"Nutrition info for {dish_name} (per serving):\n" + \
               f"- Calories: {info['calories']}\n" + \
               f"- Protein: {info['protein']}\n" + \
               f"- Carbs: {info['carbs']}\n" + \
               f"- Fat: {info['fat']}"
    else:
        return f"Nutrition data not available for {dish_name}. Please ask about a specific recipe."


class CookingAgent:
    """Cooking AI Agent for recipe search and ingredient extraction."""
    
    def __init__(self, github_token: str = None):
        """Initialize the cooking agent with GitHub model."""
        self.github_token = github_token or os.getenv("GITHUB_TOKEN", "")
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable not set")
        
        self.agent = None
        self.thread = None
    
    async def initialize(self):
        """Initialize the agent asynchronously."""
        try:
            # Create OpenAI client pointing to GitHub models
            openai_client = AsyncOpenAI(
                base_url="https://models.github.ai/inference",
                api_key=self.github_token,
            )
            
            # Create chat client
            chat_client = OpenAIChatClient(
                async_client=openai_client,
                model_id="openai/gpt-4o"  # Free-tier GitHub model
            )
            
            # Create agent with tools
            self.agent = ChatAgent(
                chat_client=chat_client,
                name="CookingChef",
                instructions="""You are an expert cooking assistant AI chef. Help users find recipes, 
                extract ingredients, and provide cooking advice. You have access to:
                1. A recipe search tool to find recipes by ingredients
                2. An ingredient extraction tool to parse recipes
                3. A nutrition information tool
                
                Always be friendly, provide detailed cooking tips, and ask clarifying questions when needed.""",
                tools=[search_recipes, extract_ingredients, get_nutrition_info],
            )
            
            # Create a thread for conversation history
            self.thread = self.agent.get_new_thread()
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize cooking agent: {str(e)}")
    
    async def chat(self, user_message: str) -> str:
        """Process user message and return agent response."""
        if not self.agent or not self.thread:
            await self.initialize()
        
        try:
            response_text = ""
            async for chunk in self.agent.run_stream(user_message, thread=self.thread):
                if chunk.text:
                    response_text += chunk.text
            
            return response_text if response_text else "I'm thinking about that. Could you ask again?"
            
        except Exception as e:
            return f"Error processing request: {str(e)}"
    
    async def get_conversation_history(self) -> list:
        """Get the conversation history from the thread."""
        if self.thread and hasattr(self.thread, 'messages'):
            return self.thread.messages
        return []


# Singleton instance
_agent_instance = None


async def get_cooking_agent() -> CookingAgent:
    """Get or create the cooking agent singleton."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = CookingAgent()
        await _agent_instance.initialize()
    return _agent_instance
