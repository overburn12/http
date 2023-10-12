from datetime import datetime
import subprocess, openai, json, os, requests, httpx
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, abort, Response
from openai.error import OpenAIError

app = Flask(__name__)

#-------------------------------------------------------------------
# app variables 
#-------------------------------------------------------------------

load_dotenv() 
openai.api_key = os.getenv("MY_API_KEY")
openai_api_key = os.getenv("MY_API_KEY")
secret_password = os.getenv("SECRET_PASSWORD")
running_ollama = os.getenv("RUNNING_OLLAMA")
ollama_model = os.getenv("OLLAMA_MODEL")
OLLAMA_API_URL = "http://localhost:11434/api/generate"

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
            #print(message)#--------------------------------------------------------------------------------
    except OpenAIError as e:
        yield {"error": str(e)}

def process_ollama_message(chat_history):
    prompt = chat_history[-1]["content"]

    response = requests.post(
        OLLAMA_API_URL,
        headers={"Authorization": "Bearer YOUR_API_TOKEN"},
        json={
            "model": ollama_model,
            "prompt": prompt
        },
        stream=True
    )
    
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            json_data = json.loads(decoded_line)
            #print(json_data) #---------------------------------------------------------------------------------------------
            generated_text = json_data.get("response", "")
            done = json_data.get("done", False)

            yield {
                "choices": [{
                    "delta": {
                        "content": generated_text
                    },
                    "finish_reason": "stop" if done else None
                }]
            }


    
def process_ollama_message_VERY_OLD(chat_history):
    prompt = chat_history[-1]["content"]
    
    response = requests.post(
        OLLAMA_API_URL,
        headers={"Authorization": "Bearer YOUR_API_TOKEN"},
        json={
            "model": ollama_model,
            "prompt": prompt
        },
        stream=True
    )
    
    generated_text = ''
    done = False
    
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            json_data = json.loads(decoded_line)
            generated_text += json_data.get("response", "")
            done = json_data.get("done", False)
            
            if done:
                break
                
    if done:
        return {"role": "assistant", "content": generated_text}
    else:
        return {"error": "An error occurred while generating the response."}

#-------------------------------------------------------------------
# functions 
#-------------------------------------------------------------------

def generate_model_list():
    sorted_models = ['gpt-3.5-turbo-16k','gpt-3.5-turbo','gpt-3.5-turbo-0301','gpt-3.5-turbo-0613','gpt-3.5-turbo-16k-0613','gpt-4']
    response = ''

    if running_ollama == 'true':
        sorted_models.append('LOCALHOST')

    for i, model in enumerate(sorted_models):
        response += model
        if i != len(sorted_models) - 1:  # Check if current model is not the last one
            response += '<br>'
    return response


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

#-------------------------------------------------------------------
# image handling
#-------------------------------------------------------------------

def load_images_to_memory():
    image_folder = 'img/'
    image_filenames = os.listdir(image_folder)
    
    for filename in image_filenames:
        with app.open_resource(os.path.join(image_folder, filename), 'rb') as f:
            images[filename] = f.read()

load_images_to_memory()

@app.route('/<image_name>.png')
def serve_image(image_name):
    image_file = images.get(f"{image_name}.png")
    if image_file:
        return Response(image_file, content_type='image/png')
    else:
        abort(404)  # Return a 404 error if the image is not found

@app.route('/favicon.ico')
def favicon():
    return Response(images['favicon.ico'], content_type='image/x-icon')

#-------------------------------------------------------------------
# page routes
#-------------------------------------------------------------------

@app.route('/chat', methods=['POST'])
def chat():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    ip_counts[ip] = ip_counts.get(ip, 0) + 1
    save_ip_counts()

    user_message = request.json['user_message']
    model = request.json.get('model', 'gpt-3.5-turbo-16k')

    def generate(user_message, model):
        if model == 'LOCALHOST':
            for bot_message_chunk in process_ollama_message(user_message):
                yield json.dumps({'bot_message': bot_message_chunk})
        else:
            for bot_message_chunk in process_openai_message(user_message, model):
                yield json.dumps({'bot_message': bot_message_chunk})


    return Response(generate(user_message,model), content_type='text/event-stream')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about', methods=['GET'])
def about_page():
    return render_template('about.html')

@app.route('/models', methods=['GET'])
def return_models():
    return generate_model_list()

@app.route('/count', methods=['GET'])
def count_connections():
    return jsonify(ip_counts)

@app.route('/view_count', methods=['GET'])
def view_count_page():
    return render_template('count.html')

@app.route('/update', methods=['GET', 'POST'])
def update_server():
    if request.method == 'POST':
        if request.form.get("secret_word") == secret_password:
            subprocess.run('python3 updater.py', shell=True)

    with open('data/update.log', 'r') as logfile:
        log_content = logfile.read()

    return render_template('update.html', log_content=log_content, app_start_time=app_start_time)

#-------------------------------------------------------------------

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
