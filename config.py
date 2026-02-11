import os
from dotenv import load_dotenv

load_dotenv()

TICKETMASTER_API_KEY = os.getenv("TICKETMASTER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
