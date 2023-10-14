from datetime import datetime
import subprocess, openai, json, os, requests
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, abort, Response
from openai.error import OpenAIError

app = Flask(__name__)

#-------------------------------------------------------------------
# app variables 
#-------------------------------------------------------------------

load_dotenv() 
openai.api_key = os.getenv('MY_API_KEY')
openai_api_key = os.getenv('MY_API_KEY')
secret_password = os.getenv('SECRET_PASSWORD')
running_ollama = os.getenv('RUNNING_OLLAMA')
ollama_api_url = os.getenv('OLLAMA_API_URL')
ollama_models = [
        'everythinglm',
        'llama2',
        'llama2-uncensored',
        'orca-mini',
        'wizardlm-uncensored']
openai_models = [
        'gpt-3.5-turbo-16k',
        'gpt-3.5-turbo',
        'gpt-3.5-turbo-0301',
        'gpt-3.5-turbo-0613',
        'gpt-3.5-turbo-16k-0613',
        'gpt-4',
        'gpt-4-0314',
        'gpt-4-0613']
default_model = 'gpt-3.5-turbo-16k'
images = {}
app_start_time = int(datetime.utcnow().timestamp())

#-------------------------------------------------------------------
# chat functions 
#-------------------------------------------------------------------

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

#-------------------------------------------------------------------
# functions 
#-------------------------------------------------------------------

def save_ip_counts():
    with open('data/ip_counts.json', 'w') as f:
        json.dump(ip_counts, f)

def load_ip_counts():
    try:
        with open('data/ip_counts.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

ip_counts = load_ip_counts()

def load_images_to_memory():
    image_folder = 'img/'
    image_filenames = os.listdir(image_folder)
    
    for filename in image_filenames:
        with app.open_resource(os.path.join(image_folder, filename), 'rb') as f:
            images[filename] = f.read()

load_images_to_memory()

#-------------------------------------------------------------------
# page routes
#-------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about', methods=['GET'])
def about_page():
    return render_template('about.html')

@app.route('/view_count', methods=['GET'])
def view_count_page():
    return render_template('count.html')

#-------------------------------------------------------------------

@app.route('/update', methods=['GET', 'POST'])
def update_server():
    if request.method == 'POST':
        if request.form.get('secret_word') == secret_password:
            subprocess.run('python3 updater.py', shell=True)

    with open('data/update.log', 'r') as logfile:
        log_content = logfile.read()

    return render_template('update.html', log_content=log_content, app_start_time=app_start_time)

#-------------------------------------------------------------------
# api routes
#-------------------------------------------------------------------

@app.route('/<path:image_name>')
def serve_image(image_name):
    name, extension = os.path.splitext(image_name)
    mime_map = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.ico': 'image/x-icon',
        '.gif': 'image/gif',
    }
    
    mime_type = mime_map.get(extension.lower())
    image_file = images.get(f'{name}{extension}')
    
    if image_file and mime_type:
        return Response(image_file, content_type=mime_type)
    else:
        abort(404)  # Return a 404 error if the image or MIME type is not found

@app.route('/title', methods=['POST'])
def get_title():
    user_message = request.json['user_message']
    model = request.json.get('model')
    title_model = 'gpt-3.5-turbo-16k'

    if model in ollama_models:
        return jsonify({'bot_message': {'role': 'assistant', 'content': 'ollama'}})
    else:
        bot_message = process_title_message(user_message, title_model)
        return jsonify({'bot_message': bot_message})

@app.route('/chat', methods=['POST'])
def chat():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    ip_counts[ip] = ip_counts.get(ip, 0) + 1
    save_ip_counts()

    user_message = request.json['user_message']
    model = request.json.get('model', 'gpt-3.5-turbo-16k')

    def generate(user_message, model):
        processor = process_ollama_message if model in ollama_models else process_openai_message
        
        for bot_message_chunk in processor(user_message, model):
            yield json.dumps({'bot_message': bot_message_chunk})

    return Response(generate(user_message,model), content_type='text/event-stream')

@app.route('/models', methods=['GET'])
def return_models():
    if running_ollama:
        return '<br>'.join(openai_models + ollama_models)
    return '<br>'.join(openai_models)

@app.route('/count', methods=['GET'])
def count_connections():
    return jsonify(ip_counts)

@app.route('/gallery')
def image_gallery():
    html_content = '<!DOCTYPE html><html><body><center>'
    
    for filename in images.keys():
        # Extract the name and extension of the file
        name, extension = os.path.splitext(filename)
        
        html_content += f'<figure><img src="/{name}{extension}" alt="{filename}">'
        html_content += f'<figcaption>{filename}</figcaption></figure>'
        
    html_content += '</center></body></html>'
    
    return html_content

#-------------------------------------------------------------------

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
