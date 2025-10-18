import os
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

class RecipeAssistant:
    def __init__(self, api_key: str = None):
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
        elif "OPENAI_API_KEY" not in os.environ:
            raise ValueError("OpenAI API key is required. Set it as an environment variable or pass it to the constructor.")
        
        self.llm = ChatOpenAI(model="gpt-3.5-turbo")
        self.chat_history = []
        
        self.recipe_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert chef and cooking instructor who can provide detailed information about any recipe.
            
            When asked about a recipe, provide:
            1. Complete list of ingredients with measurements
            2. Step-by-step cooking instructions
            3. Possible substitutions for ingredients

            If the user asks follow-up questions about the recipe, answer them thoroughly with expert knowledge.
            """),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        
        self.recipe_chain = self.recipe_prompt | self.llm
    
    def get_recipe(self, user_query: str) -> str:
        """Process a user query about a recipe and return the response"""
        response = self.recipe_chain.invoke({
            "input": user_query,
            "chat_history": self.chat_history
        })
        
        self.chat_history.append(HumanMessage(content=user_query))
        self.chat_history.append(AIMessage(content=response.content))
        
        return response.content
    
    def ask_followup(self, question: str) -> str:
        """Ask a follow-up question about the current recipe"""
        return self.get_recipe(question)
    
    def reset_conversation(self):
        """Reset the chat history to start a new recipe conversation"""
        self.chat_history = []


if __name__ == "__main__":
    
    assistant = RecipeAssistant()
    
    print("🍲 Welcome to the Recipe Assistant! 🍲")
    print("Ask about any recipe, and I'll provide you with detailed instructions.")
    print("Type 'exit' to quit or 'reset' to start a new recipe conversation.")
    
    while True:
        user_input = input("\nYou: ")
        
        if user_input.lower() == "exit":
            print("Goodbye! Happy cooking!")
            break
        elif user_input.lower() == "reset":
            assistant.reset_conversation()
            print("Conversation reset. What recipe would you like to learn about?")
            continue
        
        response = assistant.get_recipe(user_input)
        print(f"\nChef: {response}")
