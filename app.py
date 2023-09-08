import subprocess, openai, json, os, logging
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, send_from_directory
from openai.error import OpenAIError

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


# Custom log format
log_format = '[%(levelname)s] - Client IP: %(client_ip)s - Request Info - %s %s'

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

# Custom log format
log_format = (
    '%(asctime)s [%(levelname)s] - ' 
    'Client IP: %(client_ip)s - ' 
    '%(message)s'
)

with app.app_context():
    # Remove the default handler
    for handler in app.logger.handlers:
        app.logger.removeHandler(handler)

    # Create a new handler with the custom format
    handler = logging.StreamHandler()
    formatter = logging.Formatter(log_format)
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)  # Ensure our logger captures INFO level logs
    # Optionally, if you want to suppress the default Werkzeug logs:
    logging.getLogger('werkzeug').setLevel(logging.ERROR) 

# Update the logger to include client_ip
@app.before_request
def count_misc_requests():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    if ip not in ip_counts:
        ip_counts[ip] = {"chats": 0, "pageviews": 0, "misc": 0}

    if request.endpoint not in ["chat", "index", "count_connections", "view_count_page", "favicon", "static"]:  # Add other known endpoints if needed
        ip_counts[ip]["misc"] += 1

@app.before_request        
def before_request():
    client_ip = request.headers.get('X-Real-IP', request.remote_addr)
    request._client_ip = client_ip  # Attach IP to the request object


# Inject client_ip into the logger's extra parameter
@app.after_request
def log_request_info(response):
    app.logger.info('Request Info - %s %s', request.method, request.url, extra={'client_ip': request._client_ip})
    return response


@app.route('/')
def index():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    if ip not in ip_counts:
        ip_counts[ip] = {"chats": 0, "pageviews": 0, "misc": 0}
    
    ip_counts[ip]["pageviews"] += 1

    save_ip_counts()
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.root_path, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/chat', methods=['POST'])
def chat():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    if ip not in ip_counts:
        ip_counts[ip] = {"chats": 0, "pageviews": 0, "misc": 0}
    
    ip_counts[ip]["chats"] += 1

    save_ip_counts()  # Save counts to file after updating them

    user_message = request.json['user_message']
    bot_message = process_message(user_message)
    return jsonify({ 'bot_message': bot_message })

@app.route('/count', methods=['GET'])
def count_connections():
    return jsonify(ip_counts)

@app.route('/view_count', methods=['GET'])
def view_count_page():
    return render_template('count.html')

@app.route('/update', methods=['GET', 'POST'])
def update_server():
    # Execute 'git pull' command
    subprocess.run('git pull', shell=True)

    # Restart the server
    subprocess.run('sudo systemctl restart flask.service', shell=True)

    return 'Server updated successfully'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080) 