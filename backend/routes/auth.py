from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from flask import Blueprint, request, jsonify
from pymongo.errors import DuplicateKeyError

from config import db, SECRET_KEY
from models.user import UserModel

auth_bp = Blueprint("auth", __name__)


def create_token(user_id, role):
    payload = {
        "userId": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def safe_user(user):
    return {
        "userId": user["userId"],
        "name": user.get("name", ""),
        "email": user["email"],
        "phone": user.get("phone", ""),
        "role": user.get("role", "buyer"),
    }


@auth_bp.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body is required"}), 400

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    phone = str(data.get("phone", "")).strip()

    if not name or not email or not password:
        return jsonify({"message": "Name, email and password are required"}), 400

    if len(password) < 6:
        return jsonify({"message": "Password must be at least 6 characters"}), 400

    existing_user = db.users.find_one({"email": email})
    if existing_user:
        return jsonify({"message": "An account with this email already exists"}), 409

    user_id = str(uuid4())
    user = {
        "userId": user_id,
        "name": name,
        "email": email,
        "password": UserModel.hash_password(password),
        "role": "buyer",
        "createdAt": datetime.now(timezone.utc),
    }

    if phone:
        user["phone"] = phone

    try:
        db.users.insert_one(user)
    except DuplicateKeyError:
        return jsonify({"message": "An account with this email already exists"}), 409

    token = create_token(user_id, "buyer")

    return jsonify({
        "message": "Registration successful",
        "token": token,
        "user": safe_user(user),
    }), 201


@auth_bp.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body is required"}), 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 400

    user = db.users.find_one({"email": email})
    if not user:
        return jsonify({"message": "Invalid email or password"}), 401

    if "password" not in user:
        return jsonify({"message": "This account cannot be authenticated"}), 401

    password_valid = UserModel(
        name=user.get("name", ""),
        email=user["email"],
        password=user["password"],
        role=user.get("role", "buyer"),
        user_id=user["userId"],
    ).check_password(password)

    if not password_valid:
        return jsonify({"message": "Invalid email or password"}), 401

    role = user.get("role", "buyer")
    return jsonify({
        "message": "Login successful",
        "token": create_token(user["userId"], role),
        "user": safe_user(user),
    }), 200


@auth_bp.route("/api/profile", methods=["GET"])
def profile():
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return jsonify({"message": "Authorization token is required"}), 401

    try:
        parts = auth_header.split(" ")
        if len(parts) != 2 or parts[0] != "Bearer":
            return jsonify({"message": "Authorization format must be Bearer <token>"}), 401

        decoded = jwt.decode(parts[1], SECRET_KEY, algorithms=["HS256"])

        user = db.users.find_one({"userId": decoded["userId"]})
        if not user:
            return jsonify({"message": "User not found"}), 404

        return jsonify({"user": safe_user(user)}), 200

    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token has expired"}), 401

    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid token"}), 401
