import os
import random
import string
import requests
from flask import Flask, request, render_template_string
import json

app = Flask(__name__)


MY_PORT = 5000  # Change this manually for each device (5000 for A, 5001 for B) DO NOT FORGET!!!!######################################
PEER_PORT = 5001 if MY_PORT == 5000 else 5000 
PEER_URL = f"http://localhost:{PEER_PORT}"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


MESSAGE_HISTORY_FILE = os.path.join(BASE_DIR, "message_history.txt")
TEMP_ID_FILE = os.path.join(BASE_DIR, "temp_id.txt")
PEER_TEMP_ID_FILE = os.path.join(BASE_DIR, "peer_temp_id.txt")
ADVERTISEMENT_FILE = os.path.join(BASE_DIR, "advertisement.txt")
WEBPAGE_FILE = os.path.join(BASE_DIR, "webpage.html")
TRANSFER_HISTORY_FILE = os.path.join(BASE_DIR, "transfer_history.json")



STATIC_ID = "Device_A"  # Set manually here ("Device_A" or "Device_B") DO NOT FORGET ####################################################

latest_received_message = "No message yet."
status_message = "No messages sent yet."


def generate_temp_id():
    temp_id = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    with open(TEMP_ID_FILE, "w") as f:
        f.write(temp_id)
    return temp_id

generate_temp_id()

def load_temp_id():
    if os.path.exists(TEMP_ID_FILE):
        with open(TEMP_ID_FILE, "r") as f:
            return f.read().strip()
    return generate_temp_id()

def load_advertisement():
    if os.path.exists(ADVERTISEMENT_FILE):
        with open(ADVERTISEMENT_FILE, "r") as f:
            return f.read().strip()
    return "No advertisement available."

def load_webpage():
    if os.path.exists(WEBPAGE_FILE):
        with open(WEBPAGE_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>No Webpage Available</h1>"



def save_peer_temp_id(peer_temp_id):
    with open(PEER_TEMP_ID_FILE, "w") as f:
        f.write(peer_temp_id)


def load_peer_temp_id():
    if os.path.exists(PEER_TEMP_ID_FILE):
        with open(PEER_TEMP_ID_FILE, "r") as f:
            return f.read().strip()
    return "Unknown"


def save_message_history(entry):
    with open(MESSAGE_HISTORY_FILE, "a") as f:
        f.write(entry.strip() + "\n")


def load_message_history():
    if os.path.exists(MESSAGE_HISTORY_FILE):
        with open(MESSAGE_HISTORY_FILE, "r") as f:
            return f.read()
    return ""

def save_transfer_record(record):
    if os.path.exists(TRANSFER_HISTORY_FILE):
        with open(TRANSFER_HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
    else:
        history = []

    
    self_temp_id = load_temp_id()
    record['sender_temp_id'] = f"child:{record['sender_temp_id']}" if record['sender_temp_id'] == self_temp_id else record['sender_temp_id']
    record['receiver_temp_id'] = f"child:{record['receiver_temp_id']}" if record['receiver_temp_id'] == self_temp_id else record['receiver_temp_id']

    history.append(record)

    with open(TRANSFER_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)



def load_transfer_history():
    if os.path.exists(TRANSFER_HISTORY_FILE):
        with open(TRANSFER_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def calculate_balance_and_stats():
    history = load_transfer_history()
    net_balance = 0.0
    total_sent = 0.0
    total_received = 0.0
    num_transfers = len(history)

    for record in history:
        amount = float(record['amount']) 
        sender = record['sender_temp_id']
        receiver = record['receiver_temp_id']

        if sender.startswith("child:"):
            net_balance -= amount
            total_sent += amount
        if receiver.startswith("child:"):
            net_balance += amount
            total_received += amount

    return {
        'net_balance': net_balance,
        'total_sent': total_sent,
        'total_received': total_received,
        'num_transfers': num_transfers
    }


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
        peer_temp_id = response.text.strip()
        save_peer_temp_id(peer_temp_id) 
        save_message_history(f"Requested Peer Temp ID. Peer responded: {peer_temp_id}")
        return f"Peer Temp ID: {peer_temp_id}"
    except Exception as e:
        return f"Error requesting Peer Temp ID: {e}"


@app.route('/')
def home():
    return render_template_string("""
        <h1>Static ID: {{ static_id }}</h1>
        <h2>My Temporary ID: {{ temp_id }}</h2>
        <h2>Peer Temporary ID: {{ peer_temp_id }}</h2>

        <a href="/send_message">Send Message</a><br><br>
        <a href="/request_peer_id">Discover Peer Temp ID</a><br><br>
        <a href="/advertisements">Scan Advertisements</a><br><br>
        <a href="/transfer">Transfer</a><br><br>
        <a href="/balance">Balance</a><br><br><br><br>
    """, static_id=STATIC_ID, temp_id=load_temp_id(), peer_temp_id=load_peer_temp_id())


@app.route('/send_message', methods=['GET', 'POST'])
def send_message_page():
    global status_message

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

@app.route('/advertisements', methods=['GET', 'POST'])
def advertisements_page():
    global status_message
    ad_text = None
    webpage_content = None

    if request.method == 'POST':
        if 'scan_ad' in request.form:
            try:
                response = requests.post(f"{PEER_URL}/request_advertisement")
                ad_text = response.text.strip()
                save_message_history(f"Scanned Advertisement: {ad_text}")
                status_message = f"Advertisement: {ad_text}"
            except Exception as e:
                status_message = f"Error scanning Advertisement: {e}"
        elif 'visit_web' in request.form:
            try:
                response = requests.post(f"{PEER_URL}/request_webpage")
                webpage_content = response.text
                save_message_history(f"Visited Advertised Webpage. Received {len(webpage_content)} characters.")
                status_message = "Loaded Webpage Below:"
            except Exception as e:
                status_message = f"Error loading Webpage: {e}"

    return render_template_string("""
        <h1>Scan Peer Advertisements</h1>

        <form method="POST">
            <input type="submit" name="scan_ad" value="Scan Advertisements">
        </form>

        {% if status.startswith('Advertisement:') %}
        <form method="POST">
            <input type="submit" name="visit_web" value="Visit Advertised Page">
        </form>
        {% endif %}

        <h3>Status:</h3>
        <p>{{ status }}</p>

        <h3>Message History:</h3>
        <pre>{{ history }}</pre>

        {% if webpage %}
        <hr>
        <h2>Advertised Webpage:</h2>
        <div style="border:1px solid gray; padding:10px;">
            {{ webpage | safe }}
        </div>
        {% endif %}

        <br><a href="/">Back Home</a>
    """, status=status_message, history=load_message_history(), webpage=webpage_content)

@app.route('/transfer', methods=['GET', 'POST'])
def transfer_page():
    global status_message

    sender_temp_id = load_temp_id()
    receiver_temp_id = load_peer_temp_id()

    if request.method == 'POST':
        amount = request.form['amount']

        payload = {
            "amount": amount,
            "sender_temp_id": sender_temp_id,
            "receiver_temp_id": receiver_temp_id
        }

        try:
            response = requests.post(f"{PEER_URL}/receive_transfer", json=payload)
            save_transfer_record(payload)
            save_message_history(f"Sent Transfer: {payload}")
            status_message = "Transfer Sent!"
        except Exception as e:
            status_message = f"Error sending transfer: {e}"

    return render_template_string("""
        <h1>E-commerce Transfer</h1>

        <p><b>Recipient Temp ID:</b> {{ receiver_temp_id }}</p>

        <form method="POST">
            <label>Select Item:</label><br>
            <select onchange="document.getElementById('amount').value=this.value;">
                <option value="">--Choose--</option>
                <option value="10">Item A ($10)</option>
                <option value="20">Item B ($20)</option>
                <option value="30">Item C ($30)</option>
            </select><br><br>

            <label>Or Enter Amount:</label><br>
            <input type="text" name="amount" id="amount" required><br><br>

            <input type="submit" value="Send Payment">
        </form>

        <h3>Status:</h3>
        <p>{{ status }}</p>

        <br><a href="/">Back Home</a>
    """, status=status_message, receiver_temp_id=receiver_temp_id)



@app.route('/balance')
def balance_page():
    transfer_history = load_transfer_history()
    stats = calculate_balance_and_stats()

    return render_template_string("""
        <h1>Transfer Summary</h1>

        <div style="border:1px solid black; padding:10px; margin-bottom:20px;">
            <p><b>Net Balance:</b> ${{ stats.net_balance | round(2) }}</p>
            <p><b>Total Sent:</b> ${{ stats.total_sent | round(2) }}</p>
            <p><b>Total Received:</b> ${{ stats.total_received | round(2) }}</p>
            <p><b>Number of Transfers:</b> {{ stats.num_transfers }}</p>
        </div>

        <h2>Transfer History</h2>

        {% if transfers %}
            <table border="1" cellpadding="5" cellspacing="0">
                <tr>
                    <th>Sender Temp ID</th>
                    <th>Receiver Temp ID</th>
                    <th>Amount</th>
                </tr>
                {% for record in transfers %}
                <tr>
                    <td style="color: {% if record.sender_temp_id.startswith('child:') %}green{% else %}black{% endif %};">
                        {{ record.sender_temp_id }}
                    </td>
                    <td style="color: {% if record.receiver_temp_id.startswith('child:') %}green{% else %}black{% endif %};">
                        {{ record.receiver_temp_id }}
                    </td>
                    <td>${{ record.amount }}</td>
                </tr>
                {% endfor %}
            </table>
        {% else %}
            <p>No transfers yet.</p>
        {% endif %}

        <br><a href="/">Back Home</a>
    """, transfers=[type('obj', (object,), rec) for rec in transfer_history], stats=stats)


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

@app.route('/request_advertisement', methods=['POST'])
def request_advertisement_route():
    ad_text = load_advertisement()
    save_message_history(f"Peer requested Advertisement. Sent: {ad_text}")
    print(f"Peer requested Advertisement. Sent: {ad_text}")
    return ad_text

@app.route('/request_webpage', methods=['POST'])
def request_webpage_route():
    provider_temp_id = load_temp_id()
    transfer_record = {
        "amount": "0.1",
        "sender_temp_id": "AdVrtR3v9U",
        "receiver_temp_id": provider_temp_id
    }

    try:
        
        payload = transfer_record.copy()
        requests.post(f"{PEER_URL}/receive_transfer", json=payload)
    except Exception as e:
        print(f"Error notifying peer about webpage transfer: {e}")

    save_transfer_record(transfer_record)

    save_message_history(f"Received $0.1 from AdvrtR3v9U for serving webpage.")

    webpage_content = load_webpage()
    save_message_history(f"Peer requested Webpage HTML. Sent {len(webpage_content)} characters.")
    print("Peer requested Webpage HTML. Sent webpage.")

    return webpage_content


@app.route('/receive_transfer', methods=['POST'])
def receive_transfer():
    data = request.get_json()
    if not data:
        return "No transfer data received", 400

    save_transfer_record(data)
    save_message_history(f"Received Transfer: {data}")
    print("Received Transfer:", data)
    return "Transfer received successfully."



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=MY_PORT)
