import uvicorn
import string, os
import logging
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from Bot.main import bot
from Bot.utlis import remove_special_characters
from Bot.extracter import handle_uploaded_pdf

# Initialize FastAPI app
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")  # Adjust the directory path



# Allow requests from localhost
origins = ["http://localhost:5002", "http://localhost:8000"]
app.add_middleware(
    CORSMiddleware, allow_origins=origins, allow_methods=["*"], allow_headers=["*"]
)

# Template setup (if you need it)
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    print("######")
    return templates.TemplateResponse("index.html", {"request": request})  

# Function to save uploaded PDF and return its filename
def save_pdf(pdf_file: UploadFile):
    filename = pdf_file.filename
    with open(f"uploads/{filename}", "wb") as buffer:
        contents =  pdf_file.read()
        buffer.write(contents)
    return filename

@app.post("/upload-pdf")
async def upload_pdf(pdf_file: UploadFile = File(...)):
    """Uploads a PDF file and processes it."""
    try:
        # Save the uploaded PDF to a temporary directory
        
        upload_directory = os.path.join("uploads", f"{pdf_file.filename}")  # Modify as needed
        with open(upload_directory, "wb") as buffer:
            contents = await pdf_file.read()
            buffer.write(contents)

        # Process the uploaded PDF and update vector store
        handle_uploaded_pdf(upload_directory)

        return {"message": f"PDF uploaded successfully to {upload_directory}."}
    except Exception as e:
        return {"error": str(e)}


@app.api_route("/chatbot", methods=["POST"])
async def chatbot_response(request: Request):
    """Interact with the chatbot using text input."""
    print("Chatbot request received.")
    try:
        data = await request.json()
        user_input = data.get("message")
        if not user_input:
            return {"error": "Missing 'message' field in request body."}

        # Assuming you have access to the uploaded PDF filename (e.g., stored in a variable)
        # Modify chatbot logic to use the uploaded PDF content
        bot_response = bot(user_input)  # Use uploaded PDF content here
        response = remove_special_characters(bot_response)
        return {"response": response}
    except Exception as e:
        return {"error": str(e)}


def start_server():
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    try:
        logger.info('Starting Server...')
        uvicorn.run(
            "app:app",
            host="0.0.0.0",
            port=5002,
            reload= True
        )
    except Exception as e:
        logger.error(f"Failed to start the server: {e}")

if __name__ == "__main__":
    start_server()  # Use uvicorn to run