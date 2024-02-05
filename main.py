import json, os
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, abort, Response, send_from_directory

from database import track_page, init_db, fix_db_error
from openai_api import init_api, list_models, process_ollama_message, process_openai_message, process_title_message, ollama_models

app = Flask(__name__)

load_dotenv() 
init_db()
init_api()

#-------------------------------------------------------------------
# page routes
#-------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')

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

#-------------------------------------------------------------------
# api routes
#-------------------------------------------------------------------

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
    return json.dumps(list_models())

@app.route('/fix_db_error', methods=['GET'])
def fix_route():
    fix_db_error()
    return jsonify({"Message": "DONE!"})

#-------------------------------------------------------------------

@app.after_request
def after_request(response):
    track_page(request, response)
    return response

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

#-------------------------------------------------------------------

if __name__ == '__main__':
    host = os.environ.get('HOST')
    port = int(os.environ.get('PORT'))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.debug = debug
    app.run(host=host, port=port)
