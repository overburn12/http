from datetime import datetime
import subprocess, openai, json, os
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, send_from_directory
from openai.error import OpenAIError

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app_start_time = int(datetime.utcnow().timestamp())

load_dotenv() 
openai.api_key = os.getenv("MY_API_KEY")

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.root_path, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/chat', methods=['POST'])
def chat():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    ip_counts[ip] = ip_counts.get(ip, 0) + 1

    save_ip_counts()  # Save counts to file after updating them

    user_message = request.json['user_message']
    bot_message = process_message(user_message)
    return jsonify({'bot_message': bot_message})

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
