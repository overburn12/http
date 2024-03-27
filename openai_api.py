import openai, os
from openai.error import OpenAIError

def init_api():   
    if not os.getenv('MY_API_KEY'):
        print("Warning: OpenAI API key missing from .env file")
    else:
        openai.api_key = os.getenv('MY_API_KEY')

#-------------------------------------------------------------------
# chat functions 
#-------------------------------------------------------------------

def list_models():
    response = openai.Model.list()
    chat_model_keywords = ['gpt']
    
    # Include models with chat_model_keywords and exclude those with chat_model_exclude
    chat_models = [model for model in response['data'] 
                   if any(keyword in model['id'] for keyword in chat_model_keywords)]
    
    models = [model['id'] for model in chat_models] 
    models.sort()
    return models

def process_openai_message(chat_history, model):
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=chat_history,
            stream=True
        )
        for message in response:
            yield message
    except OpenAIError as e:
        yield {'error': str(e)}

def process_title_message(chat_history, model):
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=chat_history  
        )
        ai_message = {'role': 'assistant', 'content': response['choices'][0]['message']['content']}
        return ai_message
    except OpenAIError as e:
        return {'error': str(e)}