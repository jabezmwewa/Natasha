from flask import Flask, request, jsonify, render_template
import os
import socket
import re
import google.generativeai as genai
from queue import Queue, Empty
from dotenv import load_dotenv

# Load environment variables from .env file (optional)
load_dotenv()

# Set up Flask app
app = Flask(__name__)

# Retrieve the API key from environment variables
gemini_api_key = os.getenv("GEMINI_API_KEY")

# Make sure the API key is available
if gemini_api_key is None:
    raise ValueError("GEMINI_API_KEY environment variable not set")

# Configure the Gemini API client
genai.configure(api_key=gemini_api_key)

# Create the model configuration
generation_config = {
    "temperature": 2,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 500,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    safety_settings=[
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "HIGH"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "HIGH"},
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "HIGH"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "HIGH"},
    ],
    system_instruction=(
        "You are Natasha, an AI assistant and large language model created by J I Technologies to provide comprehensive support on a wide range of topics and give info about J I Technologies. "
        "JI Technologies is an emerging tech company aimed at bridging the gap in underserved regions by fostering individuals with practical skills and knowledge needed to thrive in the tech world, and also to aid a surge in Tech produced in Africa. Including Robotics, Electronics, Software development, AI and many more"
        "J I Technologies is founded by Jabez Mwewa, a Computer Engineer."
        "To find out more about Jabez, you can email jabezmwewa@gmail.com or call +260 769127394"
    ),
)

conversation_history = []
response_queue = Queue()

def net_check():
    try:
        socket.create_connection(("8.8.8.8", 53))
        return True
    except OSError:
        return False

def clean_response(text):
    import re
    def subscriptify(match):
        base, sub = match.groups()
        return f"{base}<sub>{sub}</sub>"

    text = re.sub(r"([A-Za-z])(\d+)", subscriptify, text)  # H2O -> H<sub>2</sub>O

    def superscriptify(match):
        base, super_ = match.groups()
        return f"{base}<sup>{super_}</sup>"

    text = re.sub(r"(\^)(\d+)", lambda m: f"<sup>{m.group(2)}</sup>", text)  # ^2 -> <sup>2</sup>
    text = re.sub(r"([+-]?\d+)([+-])", lambda m: f"{m.group(1)}<sup>{m.group(2)}</sup>", text)  # 3+ -> 3<sup>+</sup>
    text = text.replace("^2", "<sup>2</sup>")  #  x^2 -> x<sup>2</sup>
    text = text.replace("^3", "<sup>3</sup>")  # x^3 -> x<sup>3</sup>

    return text

def gemini_api_call(user_input):
    conversation_history.append({"role": "user", "parts": [user_input + "\n"]})
    try:
        chat_session = model.start_chat(history=conversation_history)
        response = chat_session.send_message(user_input)
        clean_text = clean_response(response.text)
        conversation_history.append({"role": "model", "parts": [clean_text + "\n"]})
        return clean_text
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_input = data.get('user_input', '')

    if not net_check():
        return jsonify({'response': "Network check failed. Please check your connection."})

    gemini_response = gemini_api_call(user_input)
    return jsonify({'response': gemini_response})

if __name__ == '__main__':
    app.run(debug=True)
