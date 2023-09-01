import openai
import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from openai.error import OpenAIError

app = Flask(__name__)

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json['user_message']
    bot_message = process_message(user_message)
    return jsonify({ 'bot_message': bot_message })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 
    #app.run(host='0.0.0.0', port=5000, ssl_context=('cert.pem', 'key.pem')) 