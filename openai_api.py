import openai, requests, json, os
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

#---------------------------------------------------------------

import base64

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

def vision_chat(image_path):
    image_path = "path_to_your_image.jpg"
    base64_image = encode_image(image_path)
    api_key = ""

    headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
    }

    payload = {
    "model": "gpt-4-vision-preview",
    "messages": [
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": "What’s in this image?"
            },
            {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
            }
        ]
        }
    ],
    "max_tokens": 300
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    return(response.json())


def url_vision_chat():
    response = openai.ChatCompletion.create(
        model="gpt-4-vision-preview",
        messages=[
            {
            "role": "user",
            "content": [
                {
                "type": "text",
                "text": "What are in these images? Is there any difference between them?",
                },
                {
                "type": "image_url",
                "image_url": {
                    "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg",
                },
                },
                {
                "type": "image_url",
                "image_url": {
                    "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg",
                },
                },
            ],
            }
        ],
        max_tokens=300,
    )
    return(response.choices[0])