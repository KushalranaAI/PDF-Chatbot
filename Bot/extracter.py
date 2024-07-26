import os
import hashlib
from openai import OpenAI
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone as PineconeClient, ServerlessSpec
from .config import PINECONE_API_KEY, PINECONE_ENVIRONMENT, OPENAI_API_KEY
from .loader import main

# --- Constants ---
INDEX_NAME = "pdf-chatbot" 
namespace = "pdf-books"
DOCS_HASH_FILENAME = "docs_hash.txt" 

# --- Hash Function to Track Changes ---
def calculate_docs_hash(docs):
    """
    Calculates a hash of the document contents to check for changes.

    Args:
        docs (list): List of document texts.

    Returns:
        str: MD5 hash of the concatenated document contents.
    """
    all_text = "".join(docs)
    return hashlib.md5(all_text.encode()).hexdigest()

class Document:
    def __init__(self, text, metadata=None):
        self.page_content = text
        self.metadata = metadata or {}


# --- Pinecone Setup ---
pc = PineconeClient(api_key=PINECONE_API_KEY)

# Load or Create Index
if INDEX_NAME not in pc.list_indexes().names():
    pc.create_index(INDEX_NAME, dimension=1536)   # type: ignore
index = pc.Index(INDEX_NAME)


# --- Load/Update Documents ---

def handle_uploaded_pdf(pdf_directory):
    """Processes uploaded PDF and updates vector store if necessary."""
    docs_str = main(pdf_directory)  # Call main with the directory path
    # print(docs)
    # Check if documents have changed
    current_hash = calculate_docs_hash(docs_str)
    try:
        with open(DOCS_HASH_FILENAME, "r") as f:
            previous_hash = f.read()
    except FileNotFoundError:
        previous_hash = ""  # No previous hash
 
    # Update index if documents are new or have changed
    if current_hash != previous_hash:
        print("Documents have changed. Updating the index...")
      
        # Call the provided function to get the document search object
        # Given docs is a list with a single string containing multiple documents
        single_string = docs_str[0]

        # Split the single string into multiple documents based on newline
        texts = single_string.split('\n')  # Use the appropriate delimiter

        # Create Document objects for each piece of text
        documents = [Document(text.strip()) for text in texts if text.strip()]

        get_docsearch(documents)

        # Save the new hash
        with open(DOCS_HASH_FILENAME, "w") as f:
            f.write(current_hash)
    else:
        print("Documents haven't changed. Loading existing vectorstore...")

        # Call the provided function to get the document search object
        get_docsearch()

        
def get_docsearch(documents=None):
    """
    Creates or loads the document search object.

    Args:
        docs (list, optional): List of documents (used for creating the index). Defaults to None.

    Returns:
        PineconeVectorStore: The document search object.
    """
 
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)  # type: ignore
    pc = PineconeClient(api_key=PINECONE_API_KEY)

    # Check if index exists
    if INDEX_NAME not in pc.list_indexes().names():
      
        pc.create_index(INDEX_NAME, dimension=1536)  # type: ignore

    index = pc.Index(INDEX_NAME)

    if documents:
        # Create document search object from documents (for initial population)
        docsearch = PineconeVectorStore.from_documents(
            documents, embeddings, index_name=INDEX_NAME
        )
    else:
        # Load existing document search object
        docsearch = PineconeVectorStore(embedding=embeddings, index_name=INDEX_NAME)

    return docsearch