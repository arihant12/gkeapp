from flask import Flask, request, jsonify, redirect, session
from flask_socketio import SocketIO, emit, join_room
from flask_cors import CORS
from sqlalchemy import create_engine, text
import os
import pymysql
import requests

# ✅ Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="*")

# ✅ Cloud SQL Connection
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Test%40123")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")  # Change to Cloud SQL host if needed
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "userbio_db")

# ✅ MySQL Connection String
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

MAIN_BACKEND_URL = "http://localhost:8080"  # ✅ Update to main backend running on port 8080

# ✅ Test Cloud SQL Connection
try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT DATABASE();"))
        print("✅ Connected to DB:", result.fetchone()[0])
except Exception as e:
    print("❌ Database connection failed:", str(e))


# ✅ Store Messages in Cloud SQL
@socketio.on('send_message')  # ✅ WebSocket Handler
def handle_send_message_socket(data):
    """Handles message sending via WebSocket"""
    sender = data.get('sender')
    receiver = data.get('receiver')
    message = data.get('message')

    if not sender or not receiver or not message:
        print("❌ Missing required fields:", data)
        return  # WebSocket cannot send HTTP responses

    print(f"📩 {sender} → {receiver}: {message}")

    # ✅ Insert message into MySQL
    try:
        with engine.connect() as conn:
            conn.execute(
                text("INSERT INTO messages (sender, receiver, message) VALUES (:sender, :receiver, :message)"),
                {"sender": sender, "receiver": receiver, "message": message}
            )
            conn.commit()

        # ✅ Emit the message to both users
        room = f"{sender}-{receiver}" if sender < receiver else f"{receiver}-{sender}"
        emit("receive_message", data, room=room)

    except Exception as e:
        print("❌ Error saving message:", str(e))


@app.route('/send_message', methods=['POST', 'OPTIONS'])  # ✅ HTTP Handler
def handle_send_message_http():
    """Handles message sending via HTTP API"""
    if request.method == "OPTIONS":
        response = jsonify({"message": "CORS Preflight OK"})
        response.headers.add("Access-Control-Allow-Origin", "http://localhost:3000")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
        response.headers.add("Access-Control-Allow-Credentials", "true")
        return response, 200

    try:
        data = request.get_json()
        sender = data.get('sender')
        receiver = data.get('receiver')
        message = data.get('message')

        if not sender or not receiver or not message:
            print("❌ Missing required fields:", data)
            response = jsonify({"error": "Missing required fields"})
            response.headers.add("Access-Control-Allow-Origin", "http://localhost:3000")
            response.headers.add("Access-Control-Allow-Credentials", "true")
            return response, 400

        print(f"📩 {sender} → {receiver}: {message}")

        # ✅ Insert Message into MySQL
        with engine.connect() as conn:
            conn.execute(
                text("INSERT INTO messages (sender, receiver, message) VALUES (:sender, :receiver, :message)"),
                {"sender": sender, "receiver": receiver, "message": message}
            )
            conn.commit()

        # ✅ Return Success Response
        response = jsonify({"message": "Message sent successfully"})
        response.headers.add("Access-Control-Allow-Origin", "http://localhost:3000")
        response.headers.add("Access-Control-Allow-Credentials", "true")
        return response, 200

    except Exception as e:
        print("❌ Error saving message:", str(e))
        response = jsonify({"error": "Database error", "details": str(e)})
        response.headers.add("Access-Control-Allow-Origin", "http://localhost:3000")
        response.headers.add("Access-Control-Allow-Credentials", "true")
        return response, 500


# ✅ Fetch Chat History
@app.route('/chat_history/<sender>/<receiver>', methods=['GET'])
def get_chat_history(sender, receiver):
    """Retrieve past messages between two users"""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT sender, receiver, message, timestamp 
                    FROM messages 
                    WHERE (sender=:sender AND receiver=:receiver) 
                       OR (sender=:receiver AND receiver=:sender) 
                    ORDER BY timestamp ASC
                """),
                {"sender": sender, "receiver": receiver}
            )
            messages = [{"sender": row[0], "receiver": row[1], "message": row[2], "timestamp": row[3]} for row in result.fetchall()]
        return jsonify(messages)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Fetch Relevant Conversations
@app.route('/get_chats', methods=['GET'])
def get_chats():
    user_id = request.args.get("user_id") or session.get("user_id")  # ✅ Ensure user_id is retrieved
    clicked_user = request.args.get("clicked_user")  # ✅ Get the user that was clicked on

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    try:
        with engine.connect() as conn:
            # ✅ Fetch users the current user has chatted with
            result = conn.execute(
                text("""
                    SELECT DISTINCT 
                        CASE WHEN sender = :user_id THEN receiver ELSE sender END AS chat_partner
                    FROM messages 
                    WHERE sender = :user_id OR receiver = :user_id
                """),
                {"user_id": user_id}
            )
            conversations = {row[0] for row in result.fetchall()}  # Convert to set

            # ✅ If the user has no previous chats, add the clicked user dynamically
            if not conversations and clicked_user:
                conversations.add(clicked_user)

            chat_list = [{"chat_partner": user} for user in sorted(conversations)]

        return jsonify({"conversations": chat_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Join Chat Room
@socketio.on('join_chat')
def handle_join_chat(data):
    sender = data.get('sender')
    receiver = data.get('receiver')

    if not sender or not receiver:
        return

    room = f"{sender}-{receiver}" if sender < receiver else f"{receiver}-{sender}"
    join_room(room)
    print(f"👥 {sender} joined room {room}")


# ✅ Health Check Route
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "Chat service is running!"})


if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5001, debug=True)
