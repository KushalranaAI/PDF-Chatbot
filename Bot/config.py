import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv('PINECONE_ENVIRONMENTS')

# OpenAI Settings
DEFAULT_OPENAI_MODEL = "gpt-4o"
MAX_TOKENS = 500  # Or another suitable value for your use case