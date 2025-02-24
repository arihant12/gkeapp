from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room
from flask_cors import CORS
from sqlalchemy import create_engine, text
import os
import pymysql

# ✅ Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
CORS(app)  # ✅ Allow React frontend to access chat service
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

# ✅ Test Cloud SQL Connection
try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT DATABASE();"))
        print("✅ Connected to DB:", result.fetchone()[0])
except Exception as e:
    print("❌ Database connection failed:", str(e))


# ✅ Store Messages in Cloud SQL
@socketio.on('send_message')
def handle_send_message(data):
    sender = data.get('sender')
    receiver = data.get('receiver')
    message = data.get('message')

    if not sender or not receiver or not message:
        return

    print(f"📩 {sender} → {receiver}: {message}")

    # Insert message into MySQL
    try:
        with engine.connect() as conn:
            conn.execute(
                text("INSERT INTO messages (sender, receiver, message) VALUES (:sender, :receiver, :message)"),
                {"sender": sender, "receiver": receiver, "message": message}
            )
            conn.commit()
    except Exception as e:
        print("❌ Error saving message:", str(e))

    # Emit message to both sender and receiver rooms
    room = f"{sender}-{receiver}" if sender < receiver else f"{receiver}-{sender}"
    emit("receive_message", data, room=room)


# ✅ Fetch Chat History
@app.route('/chat_history/<sender>/<receiver>', methods=['GET'])
def get_chat_history(sender, receiver):
    """Retrieve past messages between two users"""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT sender, message 
                    FROM messages 
                    WHERE (sender=:sender AND receiver=:receiver) 
                       OR (sender=:receiver AND receiver=:sender) 
                    ORDER BY id
                """),
                {"sender": sender, "receiver": receiver}
            )
            messages = [{"sender": row[0], "message": row[1]} for row in result.fetchall()]
        return jsonify(messages)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Join Chat Room
@socketio.on('join_chat')
def handle_join_chat(data):
    sender = data.get('sender')
    receiver = data.get('receiver')

    if not sender or not receiver:
        return

    # Ensure unique room for one-on-one chat
    room = f"{sender}-{receiver}" if sender < receiver else f"{receiver}-{sender}"
    join_room(room)
    print(f"👥 {sender} joined room {room}")


# ✅ Health Check Route
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "Chat service is running!"})


if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5001, debug=True)
