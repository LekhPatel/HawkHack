from flask import Flask, request, render_template_string
import requests

app = Flask(__name__)

RECIPIENT_URL = "http://localhost:5001"  # A's address

latest_received_message = "No message yet."
status_message = "No messages sent yet."

@app.route('/')
def home():
    return render_template_string("""
        <h2>Device B Interface</h2>
        <form method="POST" action="/send">
            <input name="message" type="text" placeholder="Enter message">
            <input type="submit" value="Send Message">
        </form>
        <h3>Status:</h3>
        <p>{{status}}</p>
        <h3>Latest Received:</h3>
        <p>{{latest}}</p>
    """, status=status_message, latest=latest_received_message)

@app.route('/send', methods=['POST'])
def send():
    global status_message
    message = request.form['message']
    try:
        res = requests.post(f"{RECIPIENT_URL}/receive", data={"text": message})
        status_message = f"Sent! Response: {res.text}"
    except Exception as e:
        status_message = f"Error: {e}"
    return home()

@app.route('/receive', methods=['POST'])
def receive():
    global latest_received_message
    latest_received_message = request.form.get('text', '[No message]')
    print("Device B received:", latest_received_message)
    return "Message received by B"

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5002)
