import datetime
import os, json, re
from threading import Timer
import hashlib
from langchain_openai import OpenAI, ChatOpenAI
from .extracter import get_docsearch
from .config import OPENAI_API_KEY
from langchain.chains import RetrievalQA, ConversationalRetrievalChain
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain_core.memory import BaseMemory
from .utlis import correct_spelling, separate_ai_text, replace_newline_tage_with_br
from .prompt import qa_prompt
from pydantic import BaseModel, Field, ValidationError

# --- Constants ---
INDEX_NAME = "rota-flow-bot"
filename = "chat_history.json"

def create_chat_openai_instance():
    return ChatOpenAI(model="gpt-4o", temperature=0.4, openai_api_key=OPENAI_API_KEY) # type: ignore

chat_openai = create_chat_openai_instance()

class MemoryConfig(BaseModel):
    memory_key: str = Field(default="chat_history")
    output_key: str = Field(default="answer")
    return_messages: bool = Field(default=True)

class ConversationBufferMemory(BaseMemory):
    memory_key: str
    output_key: str
    return_messages: bool
    chat_history: list = Field(default_factory=list)
    
    def __init__(self, config: MemoryConfig):
        # Initialize pydantic BaseModel with the provided config
        super().__init__(
            memory_key=config.memory_key, # type: ignore
            output_key=config.output_key, # type: ignore
            return_messages=config.return_messages, # type: ignore
            chat_history=[] # type: ignore
        )
        
        # Check if file exists before loading
        if os.path.exists(filename):
            self.load_chat_history()
        else:
            self.chat_history = []  # Initialize as empty list

        self.schedule_deletion()
        self.delete_unnecessary_entries()

    def load_chat_history(self):
        if os.path.exists(filename):
            with open(filename, "r") as f:
                content = f.read().strip()
                if content:
                    try:
                        self.chat_history = json.loads(content)
                    except json.JSONDecodeError:
                        self.chat_history = []  # Handle invalid JSON by resetting chat history
                else:
                    self.chat_history = []  # Handle empty file

    def save_chat_history(self):
        with open(filename, "w") as f:
            json.dump(self.chat_history, f, indent=4)

    def add_user_message(self, message):
        self.chat_history.append({"User": message})
        self.save_chat_history()

    def add_ai_message(self, message):
        self.chat_history.append({"Bot": message})
        self.save_chat_history()

    def get_chat_history(self):
        if self.return_messages:
            filtered_history = []
            for entry in self.chat_history:
                if 'User' in entry:
                    filtered_history.append(f"User: {entry['User']}")
                # elif 'Bot' in entry:
                #     filtered_history.append(f"Bot: {entry['Bot']}")
            
            # Get the last 10 user queries
            last_10_user_queries = filtered_history[-10:]

            return "\n".join(last_10_user_queries)
        return []
    
    
    def delete_unnecessary_entries(self):
        if not self.chat_history:
            return

        cleaned_history = []
        for entry in self.chat_history:
            if not ('User' in entry and isinstance(entry['User'], dict) and 'question' in entry['User'] and 'chat_history' in entry['User']) and not ('Bot' in entry and isinstance(entry['Bot'], dict) and 'answer' in entry['Bot']):
                cleaned_history.append(entry)
        self.chat_history = cleaned_history
        self.save_chat_history()


    def schedule_deletion(self):
        # Calculate deletion time in 1 hour
        now = datetime.datetime.now()
        deletion_time = now + datetime.timedelta(hours=1)
        # Schedule deletion task
        delay = (deletion_time - now).total_seconds()
        timer = Timer(delay, self.delete_file)
        timer.start()

    def delete_file(self):
        if os.path.exists(filename):
            os.remove(filename)
            print("Chat history deleted")

    # Implement abstract methods from BaseMemory
    def clear(self):
        self.chat_history = []
        if os.path.exists(filename):
            os.remove(filename)

    def load_memory_variables(self, inputs):
        return {self.memory_key: self.get_chat_history()}

    def memory_variables(self):
        return [self.memory_key]

    def save_context(self, inputs, outputs):
        self.add_user_message(inputs)
        self.add_ai_message(outputs)

def ask_question(qa_chain, query, memory):
    print(f"query: {query}")
    chat_history = memory.get_chat_history()
    result = qa_chain.invoke({"question": query, "chat_history": chat_history})
    answer = result["answer"]
    final_answer = replace_newline_tage_with_br(answer)
    return final_answer

def bot(user_input):
    chat_openai = ChatOpenAI(model="gpt-4o",temperature=0.7, openai_api_key=os.getenv("OPENAI_API_KEY")) # type: ignore
    
    user_input = user_input.lower()
    # Handle greetings, gratitude, and goodbyes
    greetings = ["hello", "hi", "hey", "hi bot", "howdy", "greetings", "good morning", "good afternoon", "good evening", "yo"]
    grateful = ["thank you", "thank you for your response", "thanks for response", "Good answer", "much appreciated", "thanks a bunch", "thanks a lot", "thank you so much", "thanks a million", "I'm grateful", "I appreciate it"]
    goodbyes = ["goodbye", "bye", "see you", "see you later", "No thanks bye", "no thanks bye", "farewell", "take care", "have a great day", "have a good one", "until next time", "bye now", "catch you later"]

    # Define regex patterns
    greetings_pattern = re.compile(r'\b(?:' + '|'.join(map(re.escape, greetings)) + r')\b', flags=re.IGNORECASE)
    grateful_pattern = re.compile(r'\b(?:' + '|'.join(map(re.escape, grateful)) + r')\b', flags=re.IGNORECASE)
    goodbyes_pattern = re.compile(r'\b(?:' + '|'.join(map(re.escape, goodbyes)) + r')\b', flags=re.IGNORECASE)

        # Use chat_openai for greetings, goodbyes, or non-movie queries
    if greetings_pattern.search(user_input):
        response = " Hi there! How can I assist you today?"
        # return initial_response
        # print(initial_response)
        return (response)

    elif grateful_pattern.search(user_input):
        response = chat_openai.invoke(user_input)
        content = response.content
        print(content)
        return content

    elif goodbyes_pattern.search(user_input):
        response = chat_openai.invoke(user_input)
        content = response.content
        print(content)
        return content
            # continue
    else:
       
        try:
            # Validate and initialize memory configuration
            config = MemoryConfig()
            memory = ConversationBufferMemory(config)
        except ValidationError as e:
            print(f"Configuration error: {e}")
            return "There was an error with the configuration."
        print(user_input)
        docserach = get_docsearch()
       
        # Question Answering with ConversationalRetrievalChain
        qa = ConversationalRetrievalChain.from_llm(
            llm=ChatOpenAI(model='gpt-4o', openai_api_key=OPENAI_API_KEY, temperature=0.4), # type: ignore
            retriever=docserach.as_retriever(),
            memory=memory,
            combine_docs_chain_kwargs={'prompt': qa_prompt},
            get_chat_history=lambda h: h
        )

        input_corrected = correct_spelling(user_input)
        final_answer = ask_question(qa, input_corrected, memory)
        memory.save_context(input_corrected, final_answer) # type: ignore
        return final_answer

# if __name__ == "__main__":
#     while True:
#         try:
#             user_input = input("User: ")
#             response = bot(user_input)
#             print(f"Bot: {response}")
#         except EOFError:
#              print("No input provided. Exiting...")
   