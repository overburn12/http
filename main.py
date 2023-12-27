import subprocess, openai, json, os, requests
from openai.error import OpenAIError
from datetime import datetime
from dotenv import load_dotenv
from functools import wraps
from flask import Flask, render_template, request, jsonify, abort, Response, session, redirect, url_for, flash, send_from_directory
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import NotFound
from werkzeug.routing import RequestRedirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_migrate import Migrate

app = Flask(__name__)

#-------------------------------------------------------------------
# app variables 
#-------------------------------------------------------------------

load_dotenv() 
openai.api_key = os.getenv('MY_API_KEY')
running_ollama = os.getenv('RUNNING_OLLAMA').lower()
ollama_api_url = os.getenv('OLLAMA_API_URL')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///overburn.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

ollama_models = [
        'everythinglm',
        'llama2',
        'llama2-uncensored',
        'orca-mini',
        'wizardlm-uncensored']
openai_models = [
        'gpt-3.5-turbo',
        'gpt-3.5-turbo-0301',
        'gpt-3.5-turbo-0613',
        'gpt-3.5-turbo-1106',
        'gpt-3.5-turbo-16k',
        'gpt-3.5-turbo-16k-0613',
        'gpt-4',
        'gpt-4-0314',
        'gpt-4-0613',
        'gpt-4-1106-preview']

app_start_time = int(datetime.utcnow().timestamp())
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class PageHit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page_url = db.Column(db.String(500))
    hit_type = db.Column(db.String(50))  # 'image', 'valid', 'invalid', 'suspicious'
    visit_datetime = db.Column(db.DateTime, default=datetime.utcnow)
    visitor_id = db.Column(db.String(100))  # IP or session ID
    referrer_url = db.Column(db.String(500))  # URL of the referring page
    user_agent = db.Column(db.String(500))  # String representing the client's user agent

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
# page count
#-------------------------------------------------------------------

@app.before_request
def before_request():
    page = request.path
    hit_type = 'invalid'
    visitor_id = request.headers.get('X-Forwarded-For', request.remote_addr)

    try:
        app.url_map.bind('').match(page)
        if page.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            hit_type = 'image'
        else:
            hit_type = 'valid'
    except (NotFound, RequestRedirect):
        hit_type = 'invalid'
    finally:
        new_hit = PageHit(page_url=page, hit_type=hit_type, visitor_id=visitor_id)
        db.session.add(new_hit)
        db.session.commit()

#-------------------------------------------------------------------
# page routes
#-------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/linda', methods=['GET', 'POST'])
def linda():
    return render_template("linda.html")

#-------------------------------------------------------------------
# api routes
#-------------------------------------------------------------------

@app.route('/favicon.ico')
def serve_favicon():
    favicon_dir = 'img/'
    try:
        return send_from_directory(favicon_dir, 'favicon.ico')
    except FileNotFoundError:
        abort(404)

@app.route('/img/<path:image_name>')
def serve_image(image_name):
    image_dir = 'img/'
    try:
        return send_from_directory(image_dir, image_name)
    except FileNotFoundError:
        abort(404)

@app.route('/title', methods=['POST','GET'])
def get_title():
    user_message = request.json['user_message']
    model = request.json.get('model')
    title_model = 'gpt-3.5-turbo-16k'

    if model in ollama_models:
        return jsonify({'bot_message': {'role': 'assistant', 'content': 'ollama'}})
    else:
        bot_message = process_title_message(user_message, title_model)
        return jsonify({'bot_message': bot_message})

@app.route('/chat', methods=['POST','GET'])
def chat():

    user_message = request.json['user_message']
    model = request.json.get('model', 'gpt-3.5-turbo-16k')

    def generate(user_message, model):
        processor = process_ollama_message if model in ollama_models else process_openai_message
        
        for bot_message_chunk in processor(user_message, model):
            yield json.dumps({'bot_message': bot_message_chunk})

    return Response(generate(user_message,model), content_type='text/event-stream')

@app.route('/models', methods=['GET'])
def return_models():
    models = openai_models
    if running_ollama == 'true':
        models.extend(ollama_models)
    return json.dumps(models)

#-------------------------------------------------------------------
# Error handlers
#-------------------------------------------------------------------

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

#-------------------------------------------------------------------

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    host = os.environ.get('HOST')
    port = int(os.environ.get('PORT'))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.debug = debug
    app.run(host=host, port=port)
