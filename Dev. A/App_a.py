import os
import random
import string
import requests
from flask import Flask, request, render_template_string

app = Flask(__name__)

# Configuration
MY_PORT = 5000  # Change this manually for each device (5000 on A, 5001 on B)
PEER_PORT = 5001 if MY_PORT == 5000 else 5000  # Opposite port
PEER_URL = f"http://localhost:{PEER_PORT}"

# Files
URL_FILE = "recipient_url.txt"
MESSAGE_HISTORY_FILE = "message_history.txt"
TEMP_ID_FILE = "temp_id.txt"

# IDs
STATIC_ID = ''.join(random.choices(string.ascii_letters + string.digits, k=10))  # Permanent ID

# Session Variables
latest_received_message = "No message yet."
status_message = "No messages sent yet."


def generate_temp_id():
    temp_id = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    with open(TEMP_ID_FILE, "w") as f:
        f.write(temp_id)
    return temp_id


def load_temp_id():
    if os.path.exists(TEMP_ID_FILE):
        with open(TEMP_ID_FILE, "r") as f:
            return f.read().strip()
    return generate_temp_id()


def save_message_history(entry):
    with open(MESSAGE_HISTORY_FILE, "a") as f:
        f.write(entry.strip() + "\n")


def load_message_history():
    if os.path.exists(MESSAGE_HISTORY_FILE):
        with open(MESSAGE_HISTORY_FILE, "r") as f:
            return f.read()
    return ""


def send_message_to_peer(message):
    try:
        response = requests.post(f"{PEER_URL}/receive", data={"text": message})
        save_message_history(f"Sent to {PEER_URL}: {message}")
        return f"Sent to {PEER_URL} — Response: {response.text}"
    except Exception as e:
        return f"Error sending message: {e}"


def request_peer_id():
    try:
        response = requests.post(f"{PEER_URL}/request_temp_id")
        save_message_history(f"Requested Peer Temp ID. Peer responded: {response.text}")
        return f"Peer Temp ID: {response.text}"
    except Exception as e:
        return f"Error requesting Peer Temp ID: {e}"


@app.route('/')
def home():
    return render_template_string("""
        <h1>Static ID: {{ static_id }}</h1>
        <h2>Temporary ID: {{ temp_id }}</h2>

        <a href="/send_message">Send Message</a><br><br>
        <a href="/request_peer_id">Discover Peer Temp ID</a>
    """, static_id=STATIC_ID, temp_id=load_temp_id())


@app.route('/send_message', methods=['GET', 'POST'])
def send_message_page():
    global status_message

    temp_id = load_temp_id()

    if request.method == 'POST':
        message = request.form['message']
        status_message = send_message_to_peer(message)

    return render_template_string("""
        <h1>Send Message</h1>

        <form method="POST">
            <label>Peer URL:</label><br>
            <input type="text" name="url" size="50" value="{{ peer_url }}" disabled><br><br>

            <label>Message:</label><br>
            <input type="text" name="message" size="50" required><br><br>

            <input type="submit" value="Send">
        </form>

        <h3>Status:</h3>
        <p>{{ status }}</p>

        <h3>Message History:</h3>
        <pre>{{ history }}</pre>

        <br><a href="/">Back Home</a>
    """, status=status_message, history=load_message_history(), peer_url=PEER_URL)


@app.route('/request_peer_id', methods=['GET', 'POST'])
def request_peer_id_page():
    global status_message

    if request.method == 'POST':
        status_message = request_peer_id()

    return render_template_string("""
        <h1>Discover Peer Temp ID</h1>

        <form method="POST">
            <input type="submit" value="Discover Peer Temp ID">
        </form>

        <h3>Status:</h3>
        <p>{{ status }}</p>

        <h3>Message History:</h3>
        <pre>{{ history }}</pre>

        <br><a href="/">Back Home</a>
    """, status=status_message, history=load_message_history())


@app.route('/receive', methods=['POST'])
def receive_message():
    global latest_received_message

    message = request.form.get('text', '[No message]')
    latest_received_message = message
    save_message_history(f"Received: {message}")
    print("Received Message:", message)
    return "Message received."


@app.route('/request_temp_id', methods=['POST'])
def request_temp_id_route():
    temp_id = load_temp_id()
    save_message_history(f"Peer requested Temp ID. Sent: {temp_id}")
    print(f"Peer requested Temp ID. My Temp ID: {temp_id}")
    return temp_id


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=MY_PORT)
