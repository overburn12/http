from datetime import datetime
import subprocess, openai, json, os, requests
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, abort, Response, session, redirect, url_for, flash
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import NotFound
from werkzeug.routing import RequestRedirect
from openai.error import OpenAIError
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import subprocess, json, os, random, re
from flask import Flask, render_template, request, jsonify, abort, Response, g, send_from_directory, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from werkzeug.utils import safe_join
from werkzeug.exceptions import NotFound
from werkzeug.routing import RequestRedirect
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
from dotenv import load_dotenv
from PIL import Image
import random
from werkzeug.utils import secure_filename

app = Flask(__name__)

#-------------------------------------------------------------------
# app variables 
#-------------------------------------------------------------------

load_dotenv() 
openai.api_key = os.getenv('MY_API_KEY')
openai_api_key = os.getenv('MY_API_KEY')
running_ollama = os.getenv('RUNNING_OLLAMA').lower()
ollama_api_url = os.getenv('OLLAMA_API_URL')
app.secret_key = os.getenv('SECRET_KEY')
admin_username = os.getenv('ADMIN_NAME')
admin_password = os.getenv('ADMIN_PASSWORD')
admin_password_hash = generate_password_hash(admin_password)  
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

class PageHit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page_url = db.Column(db.String(500))
    hit_type = db.Column(db.String(50)) # 'image', 'valid', 'invalid'
    visit_datetime = db.Column(db.DateTime, default=datetime.utcnow)
    visitor_id = db.Column(db.String(100)) # IP or session ID

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('logged_in'):
            return f(*args, **kwargs)
        else:
            flash('You need to be logged in to view this page.')
            return redirect(url_for('admin_login'))
    return decorated_function


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
    hit_type = 'none'
    visitor_id = request.headers.get('X-Forwarded-For', request.remote_addr)
    ignore_list = ['thumbnail', 'icons']

    for item in ignore_list:
        if item in page:
            return
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
        print(f"Page: {page}, Hit Type: {hit_type}, Visitor ID: {visitor_id}, endpoint: {request.endpoint}")
        db.session.add(new_hit)
        db.session.commit()

#-------------------------------------------------------------------
# page routes
#-------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/count', methods=['GET', 'POST'])
def count_page():

    # Query and tally the valid page hits
    exclude_words = ['exclude-nothing']
    valid_hits = db.session.query(
        PageHit.page_url,
        func.count(PageHit.id)
    ).filter(
        PageHit.hit_type == 'valid',
        ~PageHit.page_url.ilike(f'%{exclude_words[0]}%') if exclude_words else False,
        *[
            ~PageHit.page_url.ilike(f'%{word}%') for word in exclude_words[1:]
        ]
    ).group_by(PageHit.page_url).all()

    # Query and tally the image page hits
    image_hits = db.session.query(
        PageHit.page_url, 
        func.count(PageHit.id)
    ).filter(
        PageHit.hit_type == 'image',
        ~PageHit.page_url.ilike(f'%{exclude_words[0]}%') if exclude_words else False,
        *[
            ~PageHit.page_url.ilike(f'%{word}%') for word in exclude_words[1:]
        ]
    ).group_by(PageHit.page_url).all()

    # Query and tally the invalid page hits
    invalid_hits = db.session.query(
        PageHit.page_url, 
        func.count(PageHit.id)
    ).filter(PageHit.hit_type == 'invalid').group_by(PageHit.page_url).all()

    total_unique = db.session.query(func.count(PageHit.visitor_id.distinct()))\
                        .filter(PageHit.hit_type.in_(['valid', 'image']))\
                        .scalar()
    
    #unique_ips = PageHit.query.filter((PageHit.hit_type == 'valid') | (PageHit.hit_type == 'image')) \
    #                      .distinct(PageHit.visitor_id) \
    #                      .with_entities(PageHit.visitor_id) \
    #                      .all()

    # Pass the tallied hits to the template
    return render_template('count.html',
                           page_hits=valid_hits,
                           page_hits_images=image_hits,
                           page_hits_invalid=invalid_hits,
                           total_unique=total_unique)

#-------------------------------------------------------------------
# admin routes
#-------------------------------------------------------------------

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if 'logged_in' in session and session['logged_in']:
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == admin_username and check_password_hash(admin_password_hash, password):
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials')
    return render_template('admin_login.html')  # Your login page template

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    with open('data/update.log', 'r') as logfile:
        log_content = logfile.read()
    return render_template('admin_dashboard.html', log_content=log_content, app_start_time=app_start_time)

@app.route('/admin/update', methods=['GET', 'POST'])
@admin_required
def update_server():
    subprocess.run('python3 updater.py', shell=True)
    return '<html>Updated!</html>'

# Example endpoint to call the reset_database function
@app.route("/admin/reset", methods=['GET'])
@admin_required
def reset():
    # Drop all tables
    db.reflect()
    db.drop_all()

    # Recreate the tables
    db.create_all()
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))

#-------------------------------------------------------------------
# api routes
#-------------------------------------------------------------------

@app.route('/img/<path:image_name>')
def serve_image(image_name):
    image_dir = 'img/'
    try:
        return send_from_directory(image_dir, image_name)
    except FileNotFoundError:
        abort(404)

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
