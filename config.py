import os
from dotenv import load_dotenv

load_dotenv()

EVENTBRITE_TOKEN = os.getenv("EVENTBRITE_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
