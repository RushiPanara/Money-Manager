from flask import Flask, render_template, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
import json

app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static"
)

# Initialize Firebase (for hosting use env variable)
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(os.environ["FIREBASE_KEY"]))
    firebase_admin.initialize_app(cred)

db = firestore.client()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/add", methods=["POST"])
def add_transaction():
    data = request.json

    id_token = data.get("token")
    decoded_token = auth.verify_id_token(id_token)
    uid = decoded_token["uid"]

    transaction = {
        "type": data["type"],   # income or expense
        "amount": data["amount"],
        "category": data["category"]
    }

    db.collection("users").document(uid).collection("transactions").add(transaction)

    return jsonify({"message": "Transaction added successfully"})
