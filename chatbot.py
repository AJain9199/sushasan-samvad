from flask import Flask, request, jsonify
import random

app = Flask(__name__)

responses = [
    "I'm here to help!",
    "How can I assist you?",
    "Feel free to ask me anything.",
    "What's on your mind?",
]

@app.route('/get_response', methods=['POST'])
def get_response():
    user_input = request.json['user_input']
    bot_response = random.choice(responses)
    return jsonify({'bot_response': bot_response})

if __name__ == '__main__':
    app.run(debug=True)
