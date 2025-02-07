from loguru import logger
import sys
import os
import argparse
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import aiohttp
import json

# Load environment variables from .env file
load_dotenv(override=True)
default_port = int(os.getenv("FAST_API_PORT", "7870"))

# Initialize logger
logger.remove()  # Removing default handler, it's safe since we're resetting the handler
logger.add(sys.stderr, level="DEBUG")

# Fetch API keys from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
WEATHER_API_URL = "http://api.weatherapi.com/v1/current.json"

# Ensure API keys are loaded
if not OPENAI_API_KEY:
    raise ValueError("OpenAI API key is missing from environment variables.")
if not WEATHER_API_KEY:
    raise ValueError("Weather API key is missing from environment variables.")

# Initialize FastAPI app
app = FastAPI()

# Enable CORS for your frontend (e.g., localhost:5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Specify the origin(s) you want to allow
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

class OpenAILLMService:
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.openai.com/v1/chat/completions"

    async def generate_response(self, message: str):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": message}],
            "temperature": 0.7,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, headers=headers, data=json.dumps(data)) as response:
                if response.status == 200:
                    response_json = await response.json()
                    return response_json.get("choices", [{}])[0].get("message", {}).get("content", "No response")
                else:
                    logger.error(f"Error calling OpenAI API: {response.status}")
                    return "Error contacting OpenAI API"

async def is_weather_query(text):
    """Ask OpenAI if the message is related to weather."""
    prompt = f"Is this message about the weather? \"{text}\""
    llm_service = OpenAILLMService(api_key=OPENAI_API_KEY, model="gpt-4")
    response = await llm_service.generate_response(prompt)
    return "yes" in response.lower()

async def extract_location_from_query(text):
    """Use OpenAI to extract the location from the weather-related query."""
    prompt = f"Please extract the city name from this weather query: \"{text}\""
    llm_service = OpenAILLMService(api_key=OPENAI_API_KEY, model="gpt-4")
    response = await llm_service.generate_response(prompt)
    return response.strip()

async def fetch_weather(location):
    """Fetch weather data from the Weather API."""
    logger.debug(f"Fetching weather for location: {location}")
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{WEATHER_API_URL}?key={WEATHER_API_KEY}&q={location}") as response:
            if response.status == 200:
                data = await response.json()
                logger.debug(f"Weather data received: {data}")
                return data
            logger.error(f"Error fetching weather: {response.status}")
            return None

async def process_user_message(message, llm_service):
    """Process the user's message and provide an appropriate response."""
    logger.debug(f"Processing user message: {message}")
    if await is_weather_query(message):
        # Extract the location from the prompt using OpenAI
        location = await extract_location_from_query(message)
        logger.debug(f"Extracted location: {location}")
        
        # Fetch weather data
        weather_data = await fetch_weather(location)
        if weather_data:
            # Refine the weather response with OpenAI
            refined_prompt = f"The weather in {location} is currently {weather_data['current']['condition']['text']} " \
                             f"with a temperature of {weather_data['current']['temp_c']}°C. Can you provide a more insightful response?"
            refined_response = await llm_service.generate_response(refined_prompt)
            return refined_response
        else:
            return f"Sorry, I couldn't find the weather information for {location}."
    else:
        refined_prompt = f"Answer as a helpful assistant"
        refined_response = await llm_service.generate_response(refined_prompt)
        return refined_response

@app.post("/chat")
async def chat(request: Request):
    """Handle chat queries, including weather-related questions."""
    body = await request.json()
    user_message = body.get("message", "").lower()

    llm_service = OpenAILLMService(api_key=OPENAI_API_KEY, model="gpt-4")
    
    response = await process_user_message(user_message, llm_service)
    return {"response": response}

@app.get("/weather")
async def get_weather(city: str):
    """Fetch and return weather data for a specified city."""
    weather_data = await fetch_weather(city)
    return weather_data

@app.get("/")
async def root():
    """Root endpoint to check if the server is running."""    
    return {"message": "Welcome to the Chat API!"}

if __name__ == "__main__":
    import uvicorn

    # Default values for host and port
    default_host = os.getenv("HOST", "0.0.0.0")
    default_port = int(os.getenv("FAST_API_PORT", "7860"))
    
    # Argument parser for custom host/port settings
    parser = argparse.ArgumentParser(description="FastAPI Chatbot server")
    parser.add_argument("--host", type=str, default=default_host, help="Host address")
    parser.add_argument("--port", type=int, default=default_port, help="Port number")
    parser.add_argument("--reload", action="store_true", help="Reload code on change")

    # Parse arguments and run the server
    config = parser.parse_args()

    # Start the FastAPI server
    uvicorn.run(
        "server:app",
        host=config.host,
        port=config.port,
        reload=config.reload,
    )