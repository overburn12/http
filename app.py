import openai
from flask import Flask, render_template, request, jsonify
from openai.error import OpenAIError

app = Flask(__name__)

##############################################
with open("api-key.txt", 'r') as file:
    openai_api_key = file.read()
openai.api_key = openai_api_key

def process_message(chat_history):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=chat_history  
        )
        ai_message = {"role": "assistant", "content": response['choices'][0]['message']['content']}
        return ai_message
    except OpenAIError as e:
        return {"error": str(e)}
##############################################

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