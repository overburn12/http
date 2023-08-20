from flask import Flask, render_template, request
import openai

openai_api_key = 'YOUR-OPENAI-API-KEY'

openai.api_key = openai_api_key

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.form['user_message']
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=user_message,
        max_tokens=50
    )
    bot_message = response.choices[0].text
    return bot_message

if __name__ == '__main__':
    app.run(debug=True)
