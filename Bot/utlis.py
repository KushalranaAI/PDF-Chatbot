import openai
import re


def separate_ai_text(response):
    # Split the response at the first occurrence of ":"
    index = response.find(":")
    if index != -1:
        ai_text = response[:index+1]  # Include ":" in AI text
        user_text = response[index+1:].strip()  # Remove leading/trailing whitespace
        return user_text
    else:
        return None, response
    
    
    
    
def correct_spelling(user_input):

    # Prompt OpenAI to suggest corrections
    Prompt = f"Only return correct input not other text. Correct any misspellings in the user input: {user_input}. "
    response = openai.completions.create(
        model="gpt-3.5-turbo-instruct",  # Adjust engine as needed
        prompt=Prompt,
        max_tokens=100,  # Limit output to 1 suggestion
        n=1,
        stop=None,
        temperature=0.7  # Controls randomness (adjust as needed)
    )

    # Check if OpenAI's response indicates no misspellings
    if "no misspellings" in response.choices[0].text.lower():
        return user_input
    else:
        # Extract and return the corrected input
        corrected_input = response.choices[0].text.strip()
        return corrected_input
    
    
def replace_newline_tage_with_br(message):
    replace = message.replace("\n", "<br>")
    
    return replace


def remove_special_characters(message):
    # Define the regex pattern to match * and #
    pattern = r'[\*#]'
    # Use re.sub to replace * and # with an empty string
    cleaned_message = re.sub(pattern, '', message)
    return cleaned_message