from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder, AIMessagePromptTemplate



prompt_template = """
You are a friendly and personalize chatbot that always make conversation in english. Your primary goal is to provide helpful and accurate inforamtion about pdf data. You are also capable of engaging in lighthearted conversations and responding appropriately to greetings and casual inquiries.
- PRovide a structural and understanble response that will easy to read and understand. 

{context}

{chat_history}

"""

messages = [
        SystemMessagePromptTemplate.from_template(prompt_template),
        ("human", "{question}")
    ]
    
qa_prompt = ChatPromptTemplate.from_messages(messages)