from flask import Flask, request, jsonify, render_template
import os
from sqlalchemy import create_engine, text
import pymysql

# 1) Import Elasticsearch
from elasticsearch import Elasticsearch

app = Flask(__name__)

# ✅ Cloud SQL Credentials (Replace with environment variables in production)
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Test%40123")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "userbio_db")

# ✅ SQLAlchemy Database URL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

# ✅ Connect to Elasticsearch (assuming it's running on localhost:9200)
es = Elasticsearch(["http://localhost:9200"])

# ✅ Test DB Connection
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


# ---------------------------------------------
# Existing: Get a user's bio by email (POST)
#           Or if method=GET, get all user bios
# ---------------------------------------------
@app.route("/get_user_bio", methods=["GET", "POST"])
def get_user_bio():
    if request.method == "GET":
        # Get ALL users from MySQL
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT name, profession, bio FROM users"))
                rows = result.fetchall()
            users = []
            for row in rows:
                users.append({
                    "name": row[0],
                    "profession": row[1],
                    "bio": row[2],
                })
            return jsonify(users)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    else:
        # POST - get a single user by email
        data = request.json
        email = data.get("email")
        if not email:
            return jsonify({"error": "Email is required"}), 400

        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT name, profession, bio FROM users WHERE email = :email"),
                    {"email": email}
                )
                user = result.fetchone()

            if user:
                return jsonify({
                    "name": user[0],
                    "profession": user[1],
                    "bio": user[2],
                    "new_user": False
                })
            else:
                return jsonify({"message": "No bio found", "new_user": True}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500


# ------------------------------------------------
# Existing: Submit (insert/update) a user's bio
# Modified to also index user data in Elasticsearch
# ------------------------------------------------
@app.route("/submit_bio", methods=["POST"])
def submit_bio():
    """Insert or update user bio in Cloud SQL AND Elasticsearch."""
    data = request.json
    email = data.get("email")
    name = data.get("name")
    profession = data.get("profession")
    bio = data.get("bio")

    if not email or not name or not profession or not bio:
        return jsonify({"error": "All fields are required"}), 400

    try:
        with engine.connect() as conn:
            # Check if user exists
            result = conn.execute(text("SELECT 1 FROM users WHERE email = :email"), {"email": email})
            existing_user = result.fetchone()

            if existing_user:
                # Update
                conn.execute(
                    text("UPDATE users SET name = :name, profession = :profession, bio = :bio WHERE email = :email"),
                    {"name": name, "profession": profession, "bio": bio, "email": email}
                )
            else:
                # Insert
                conn.execute(
                    text("INSERT INTO users (email, name, profession, bio) VALUES (:email, :name, :profession, :bio)"),
                    {"email": email, "name": name, "profession": profession, "bio": bio}
                )
            conn.commit()

        # ---- Index or Update Elasticsearch ----
        # Use email as the document ID for easy upserts.
        es.index(
            index="askpro-users",            # Name of your index
            id=email,                       # Use the email as the document id
            body={
                "email": email,
                "name": name,
                "profession": profession,
                "bio": bio
            }
        )

        return jsonify({"message": "User data saved successfully!"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------
# New: Search route with ES
# -----------------------------
@app.route("/search_users", methods=["GET"])
def search_users():
    """Search for users in Elasticsearch by name, profession, or bio."""
    query = request.args.get("q", "")

    if not query:
        return jsonify([])  # Return empty if no query

    try:
        # Multi-match query on name, profession, and bio
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

        # Extract _source from each hit
        results = []
        for h in hits:
            source = h["_source"]
            results.append({
                "email": source.get("email"),
                "name": source.get("name"),
                "profession": source.get("profession"),
                "bio": source.get("bio")
            })

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # For production, use a production server like Gunicorn.
    # For local dev, debug=True is fine.
    app.run(host="0.0.0.0", port=8080, debug=True)
