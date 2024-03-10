import json, os
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, abort, Response, send_from_directory

from database import track_page
from openai_api import init_api, list_models, process_openai_message, process_title_message

app = Flask(__name__)

load_dotenv() 
init_api()

#-------------------------------------------------------------------
# page routes
#-------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/img/<path:image_name>')
def serve_image(image_name):
    image_dir = 'img/'
    try:
        return send_from_directory(image_dir, image_name)
    except FileNotFoundError:
        abort(404)

#-------------------------------------------------------------------
# file routes
#-------------------------------------------------------------------

@app.route('/favicon.ico')
def serve_favicon():
    favicon_dir = 'img/'
    try:
        return send_from_directory(favicon_dir, 'favicon.ico')
    except FileNotFoundError:
        abort(404)

@app.route('/robots.txt')
def robots_txt():
    content = "User-agent: *\nDisallow: /"
    return Response(content, mimetype='text/plain')

@app.route('/sitemap.xml')
def sitemap():
    xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
   <url>
      <loc>https://overburn.org/</loc>
      <lastmod>2024-02-10</lastmod>
      <changefreq>never</changefreq>
      <priority>1.0</priority>
   </url>
</urlset>'''
    return Response(xml_content, mimetype='application/xml')

#-------------------------------------------------------------------
# api routes
#-------------------------------------------------------------------

@app.route('/title', methods=['POST','GET'])
def get_title():
    user_message = request.json['user_message']
    title_model = 'gpt-3.5-turbo-16k' # = request.json.get('model')

    bot_message = process_title_message(user_message, title_model)
    return jsonify({'bot_message': bot_message})

@app.route('/chat', methods=['POST','GET'])
def chat():
    user_message = request.json['user_message']
    model = request.json.get('model', 'gpt-3.5-turbo-16k')

    def generate(user_message, model):
        for bot_message_chunk in process_openai_message(user_message, model):
            yield json.dumps({'bot_message': bot_message_chunk})

    return Response(generate(user_message,model), content_type='text/event-stream')

@app.route('/models', methods=['GET'])
def return_models():
    return json.dumps(list_models())

#-------------------------------------------------------------------
# aux. routes
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
    app.run(host='0.0.0.0', port=8080)
