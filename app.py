from datetime import datetime
import subprocess, openai, json, os
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, abort, Response
from openai.error import OpenAIError

app = Flask(__name__)
#app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app_start_time = int(datetime.utcnow().timestamp())

load_dotenv() 
openai.api_key = os.getenv("MY_API_KEY")

images = {}

#-------------------------------------------------------------------
# functions 
#-------------------------------------------------------------------

def generate_model_list():
    response = ''
    model_list = openai.Model.list()
    sorted_models = sorted(model_list['data'], key=lambda x: x['id'])
    for model in sorted_models:
        response += model['id'] + '<br>'
    return response

def process_message(chat_history):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            messages=chat_history  
        )
        ai_message = {"role": "assistant", "content": response['choices'][0]['message']['content']}
        return ai_message
    except OpenAIError as e:
        return {"error": str(e)}

def save_ip_counts():
    with open('ip_counts.json', 'w') as f:
        json.dump(ip_counts, f)

def load_ip_counts():
    try:
        with open('ip_counts.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

ip_counts = load_ip_counts()

#-------------------------------------------------------------------
# image handling
#-------------------------------------------------------------------

def load_images_to_memory():
    """Load images and store them in the images dictionary."""
    with app.open_resource('Overburn.png', 'rb') as f:
        images['overburn.png'] = f.read()

    with app.open_resource('GPT.png', 'rb') as f:
        images['gpt.png'] = f.read()

    #with app.open_resource('chat_img.png', 'rb') as f:
    #    images['chat_img.png'] = f.read()

    with app.open_resource('favicon.ico', 'rb') as f:
        images['favicon.ico'] = f.read()

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
    return Response(images['favicon.ico'], content_type='image/vnd.microsoft.icon')

#-------------------------------------------------------------------
# page routes
#-------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    ip_counts[ip] = ip_counts.get(ip, 0) + 1
    save_ip_counts()  # Save counts to file after updating them

    user_message = request.json['user_message']
    bot_message = process_message(user_message)
    return jsonify({'bot_message': bot_message})

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
        secret_password = os.getenv("SECRET_PASSWORD")
        if request.form.get("secret_word") == secret_password:
            subprocess.run('python3 updater.py', shell=True)
            return 'Server updated successfully'
        else:
            return 'Invalid secret word. Update aborted.'

    with open('update.log', 'r') as logfile:
        log_content = logfile.read()

    return render_template('update.html', log_content=log_content, app_start_time=app_start_time)

#-------------------------------------------------------------------

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
