from flask import Flask, jsonify, request, render_template
from datetime import datetime

app = Flask(__name__)

POSTS_STORE = [
    {
        "id": 1,
        "title": "Architecting Resilient Distributed Systems",
        "author": "Engineering Lead",
        "content": "Designing high-availability systems with graceful degradation and circuit breakers.",
        "created_at": "2026-11-19T10:00:00Z"
    }
]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/posts", methods=["GET"])
def get_posts():
    return jsonify(POSTS_STORE)

@app.route("/api/posts", methods=["POST"])
def create_post():
    data = request.get_json() or {}
    title = str(data.get("title", "")).strip()
    author = str(data.get("author", "")).strip()
    content = str(data.get("content", "")).strip()

    if not title or not content:
        return jsonify({"error": "Title and content are required fields"}), 400

    new_post = {
        "id": len(POSTS_STORE) + 1,
        "title": title,
        "author": author or "Anonymous",
        "content": content,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    POSTS_STORE.append(new_post)
    return jsonify(new_post), 201

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
