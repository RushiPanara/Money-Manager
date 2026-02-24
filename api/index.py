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

if not firebase_admin._apps:
    firebase_key_json = os.environ.get("FIREBASE_KEY")
    if not firebase_key_json:
        raise Exception("FIREBASE_KEY environment variable is missing!")
    cred = credentials.Certificate(json.loads(firebase_key_json))
    firebase_admin.initialize_app(cred)

db = firestore.client()

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/add", methods=["POST"])
def add_transaction():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    id_token = data.get("token")
    if not id_token:
        return jsonify({"error": "No token provided"}), 401

    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token["uid"]
    except Exception as e:
        return jsonify({"error": str(e)}), 401

    transaction = {
        "type": data.get("type"),  
        "amount": data.get("amount"),
        "category": data.get("category")
    }

    if not transaction["type"] or not transaction["amount"] or not transaction["category"]:
        return jsonify({"error": "Missing transaction fields"}), 400

    db.collection("users").document(uid).collection("transactions").add(transaction)

    return jsonify({"message": "Transaction added successfully"})


@app.route("/transactions", methods=["GET"])
def get_transactions():
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        id_token = auth_header.split("Bearer ")[-1]
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token["uid"]
    except Exception as e:
        return jsonify({"error": str(e)}), 401

    transactions_ref = db.collection("users").document(uid).collection("transactions")
    transactions_docs = transactions_ref.stream()

    transactions = []
    total_income = 0
    total_expense = 0

    for doc in transactions_docs:
        t = doc.to_dict()
        t["id"] = doc.id  
        transactions.append(t)
        if t["type"] == "income":
            total_income += t["amount"]
        else:
            total_expense += t["amount"]

    balance = total_income - total_expense

    return jsonify({
        "transactions": transactions,
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": balance
    })




