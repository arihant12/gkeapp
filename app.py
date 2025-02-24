from flask import Flask, request, jsonify, render_template, redirect
import os
import requests  # ✅ Used to communicate with chat service
from sqlalchemy import create_engine, text
import pymysql
from flask_cors import CORS  # ✅ Allow frontend requests from React
from elasticsearch import Elasticsearch  # ✅ Elasticsearch for search functionality

app = Flask(__name__)
CORS(app)  # ✅ Enable CORS for all routes

# ✅ Cloud SQL Credentials (Use environment variables in production)
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Test%40123")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "userbio_db")

# ✅ SQLAlchemy Database Connection
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

# ✅ Connect to Elasticsearch (assuming it's running on localhost:9200)
es = Elasticsearch(
    ["https://localhost:9200"],  # Use HTTPS instead of HTTP
    basic_auth=("elastic", "Test123"),  # Authenticate with username & password
    verify_certs=False  # Ignore SSL certificate verification (ONLY for local testing)
)
try:
    if es.ping():
        print("✅ Connected to Elasticsearch successfully!")
    else:
        print("❌ Elasticsearch connection failed!")
except Exception as e:
    print("❌ Error connecting to Elasticsearch:", str(e))

# ✅ Chat Microservice URL (Modify if running in production)
CHAT_SERVICE_URL = os.getenv("CHAT_SERVICE_URL", "http://localhost:5001")

# ✅ Test Database Connection
try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT DATABASE();"))
        print("✅ Connected to DB:", result.fetchone()[0])
except Exception as e:
    print("❌ Database connection failed:", str(e))


@app.route("/")
def home():
    """Serve the frontend UI."""
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# -------------------------------
# ✅ Fetch Chat History from Chat Service
# -------------------------------
@app.route("/chat_history/<sender>/<receiver>", methods=["GET"])
def chat_history(sender, receiver):
    """Fetch chat history from chat service."""
    try:
        response = requests.get(f"{CHAT_SERVICE_URL}/chat_history/{sender}/{receiver}")
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------
# ✅ Serve React Chat Frontend
# -------------------------------
@app.route("/chat")
def chat():
    """Redirect users to the React-based chat frontend"""
    receiver_email = request.args.get("receiver", "")

    if not receiver_email:
        return jsonify({"error": "Receiver email is required"}), 400

    # ✅ Redirect to React frontend running at http://localhost:3000/chat
    return redirect(f"http://localhost:3000/chat?receiver={receiver_email}")


# -----------------------------
# ✅ Get a User's Bio (MySQL)
# -----------------------------
@app.route("/get_user_bio", methods=["GET", "POST"])
def get_user_bio():
    if request.method == "GET":
        try:
            with engine.connect() as conn:
                result = conn.execute(text(
                    "SELECT name, profession, bio, priority_dm_charge, one_on_one_call_charge FROM users"
                ))
                rows = result.fetchall()
            users = [{
                "name": row[0], "profession": row[1], "bio": row[2],
                "priority_dm_charge": row[3], "one_on_one_call_charge": row[4]
            } for row in rows]
            return jsonify(users)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    else:
        data = request.json
        email = data.get("email")
        if not email:
            return jsonify({"error": "Email is required"}), 400

        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT name, profession, bio, priority_dm_charge, one_on_one_call_charge FROM users WHERE email = :email"),
                    {"email": email}
                )
                user = result.fetchone()

            if user:
                return jsonify({
                    "name": user[0], "profession": user[1], "bio": user[2],
                    "priority_dm_charge": user[3], "one_on_one_call_charge": user[4],
                    "new_user": False
                })
            else:
                return jsonify({"message": "No bio found", "new_user": True}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500



# ------------------------------------------------
# ✅ Insert/Update User Bio (MySQL + Elasticsearch)
# ------------------------------------------------
@app.route("/submit_bio", methods=["POST"])
def submit_bio():
    """Insert or update user bio in Cloud SQL AND Elasticsearch."""
    data = request.json
    email = data.get("email")
    name = data.get("name")
    profession = data.get("profession")
    bio = data.get("bio")
    priority_dm_charge = data.get("priority_dm_charge", 0.0)
    one_on_one_call_charge = data.get("one_on_one_call_charge", 0.0)

    if not email or not name or not profession or not bio:
        return jsonify({"error": "All fields are required"}), 400

    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 FROM users WHERE email = :email"), {"email": email})
            existing_user = result.fetchone()

            if existing_user:
                conn.execute(
                    text("""
                        UPDATE users 
                        SET name = :name, profession = :profession, bio = :bio, 
                            priority_dm_charge = :priority_dm_charge, one_on_one_call_charge = :one_on_one_call_charge 
                        WHERE email = :email
                    """),
                    {
                        "name": name, "profession": profession, "bio": bio,
                        "priority_dm_charge": priority_dm_charge, "one_on_one_call_charge": one_on_one_call_charge,
                        "email": email
                    }
                )
            else:
                conn.execute(
                    text("""
                        INSERT INTO users (email, name, profession, bio, priority_dm_charge, one_on_one_call_charge) 
                        VALUES (:email, :name, :profession, :bio, :priority_dm_charge, :one_on_one_call_charge)
                    """),
                    {
                        "email": email, "name": name, "profession": profession, "bio": bio,
                        "priority_dm_charge": priority_dm_charge, "one_on_one_call_charge": one_on_one_call_charge
                    }
                )
            conn.commit()

        es.index(
            index="askpro-users",
            id=email,
            body={
                "email": email, "name": name, "profession": profession, "bio": bio,
                "priority_dm_charge": priority_dm_charge, "one_on_one_call_charge": one_on_one_call_charge
            }
        )

        return jsonify({"message": "User data saved successfully!"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500



# -----------------------------
# ✅ Search Users (Elasticsearch)
# -----------------------------
@app.route("/search_users", methods=["GET"])
def search_users():
    """Search for users in Elasticsearch by name, profession, or bio."""
    query = request.args.get("q", "")
    if not query:
        return jsonify([])

    try:
        es_query = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["name", "profession", "bio"]
                }
            }
        }
        response = es.search(index="askpro-users", body=es_query)
        hits = response["hits"]["hits"]
        results = [{
            "email": h["_source"]["email"], "name": h["_source"]["name"],
            "profession": h["_source"]["profession"], "bio": h["_source"]["bio"],
            "priority_dm_charge": h["_source"].get("priority_dm_charge", 0.0),
            "one_on_one_call_charge": h["_source"].get("one_on_one_call_charge", 0.0)
        } for h in hits]
        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)