import os
import pickle
import logging
from pathlib import Path
from datetime import datetime
from PyPDF2 import PdfReader

from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CACHE_FILE = 'pdf_chunks_cache.pkl'
TIMESTAMP_FILE = 'pdf_timestamps.pkl'


def load_pdf(data_path):
    """
    Load PDF files from the specified path, which can be either a directory or a single file.

    Args:
        data_path (str): Path to the directory containing PDF files or a single PDF file.

    Returns:
        list: List of loaded documents.
    """
    try:
        if os.path.isdir(data_path):
            logging.info("Loading PDFs from directory: %s", data_path)
            loader = DirectoryLoader(data_path, loader_cls=PyPDFLoader)
            documents = loader.load()
        elif os.path.isfile(data_path) and data_path.endswith('.pdf'):
            logging.info("Loading PDF from file: %s", data_path)
            loader = PyPDFLoader(data_path)
            documents = loader.load()
        else:
            raise ValueError(f"Expected directory or PDF file, got: {data_path}")

        logging.info("Loaded %d documents", len(documents))
        return documents
    except Exception as e:
        logging.error("Failed to load PDFs: %s", e)
        return []


def get_pdf_text(documents):
    """
    Extract text from PDF documents.

    Args:
        documents (list): List of loaded PDF documents.

    Returns:
        str: Concatenated text extracted from all PDF documents.
    """
    text = ""
    for document in documents:
        # Assuming each document has a content attribute with the extracted text
        text += f"page_content={document.page_content}\n"
    return text


def text_split(extracted_data, chunk_size=500, chunk_overlap=20):
    """
    Split extracted text data into chunks using RecursiveCharacterTextSplitter.

    Args:
        extracted_data (str): Extracted text data.
        chunk_size (int): Size of each text chunk.
        chunk_overlap (int): Overlap between consecutive text chunks.

    Returns:
        list: List of text chunks.
    """
    try:
        logging.info("Splitting text into chunks")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        text_chunks = text_splitter.split_text(extracted_data)
        logging.info("Created %d text chunks", len(text_chunks))
        return text_chunks
    except Exception as e:
        logging.error("Failed to split text: %s", e)
        return []


def save_chunks_to_cache(chunks, cache_file=CACHE_FILE):
    """
    Save text chunks to a cache file.

    Args:
        chunks (list): List of text chunks to save.
        cache_file (str): Path to the cache file.
    """
    try:
        with open(cache_file, 'wb') as f:
            pickle.dump(chunks, f)
        logging.info("Saved text chunks to cache file: %s", cache_file)
    except Exception as e:
        logging.error("Failed to save chunks to cache: %s", e)


def load_chunks_from_cache(cache_file=CACHE_FILE):
    """
    Load text chunks from a cache file if it exists.

    Args:
        cache_file (str): Path to the cache file.

    Returns:
        list: List of text chunks, or None if the cache file does not exist.
    """
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'rb') as f:
                chunks = pickle.load(f)
            logging.info("Loaded text chunks from cache file: %s", cache_file)
            return chunks
        except Exception as e:
            logging.error("Failed to load chunks from cache: %s", e)
    else:
        logging.info("Cache file does not exist: %s", cache_file)
    return None


def main(data_directory):
    """
    Main function to load PDFs, split text into chunks, and cache the chunks.

    Args:
        data_directory (str): Path to the directory containing PDF files.

    Returns:
        list: List of text chunks.
    """
    logging.info("New or modified PDF files detected")
    extracted_data = load_pdf(data_directory)
    if extracted_data:
        extracted_text = get_pdf_text(extracted_data)
        text_chunks = text_split(extracted_text)
        save_chunks_to_cache(text_chunks)
    else:
        text_chunks = load_chunks_from_cache()

    if text_chunks:
        logging.info("Length of text chunks: %d", len(text_chunks))
        # print(text_chunks)
        return text_chunks
    else:
        logging.info("No text chunks available")
        return []

