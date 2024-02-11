import openai, requests, json, os
from openai.error import OpenAIError

ollama_models = [
        'everythinglm',
        'llama2',
        'llama2-uncensored',
        'orca-mini',
        'wizardlm-uncensored']
running_ollama = False
ollama_api_url = ""

def init_api():
    global running_ollama, ollama_api_url
    
    openai.api_key = os.getenv('MY_API_KEY')
    running_ollama = os.getenv('RUNNING_OLLAMA').lower()
    ollama_api_url = os.getenv('OLLAMA_API_URL')

#-------------------------------------------------------------------
# chat functions 
#-------------------------------------------------------------------

def list_models():
    response = openai.Model.list()
    # Filtering for models with specific keywords in their IDs
    chat_model_keywords = ['gpt']
    chat_model_exclude = ['vision', 'instruct']
    
    # Include models with chat_model_keywords and exclude those with chat_model_exclude
    chat_models = [model for model in response['data'] 
                   if any(keyword in model['id'] for keyword in chat_model_keywords)
                   and not any(exclude in model['id'] for exclude in chat_model_exclude)]
    
    models = [model['id'] for model in chat_models]  # Extracting model ids into a list
    models.sort()

    if running_ollama == 'true':
        models.extend(ollama_models)
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

def process_ollama_message(chat_history, model):
    prompt = chat_history[-1]['content']

    response = requests.post(
        ollama_api_url,
        headers={'Authorization': 'Bearer YOUR_API_TOKEN'},
        json={
            'model': model,
            'prompt': prompt
        },
        stream=True
    )
    
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            json_data = json.loads(decoded_line)
            generated_text = json_data.get('response', '')
            done = json_data.get('done', False)

            yield {
                'choices': [{
                    'delta': {
                        'content': generated_text
                    },
                    'finish_reason': 'stop' if done else None
                }]
            }

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

