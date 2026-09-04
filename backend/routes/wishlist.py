from flask import Blueprint, request, jsonify
from config import db
from bson import ObjectId
from uuid import uuid4
from datetime import datetime, timezone

wishlist_bp = Blueprint("wishlist", __name__)


def convert_object_ids(data):

    if isinstance(data, ObjectId):
        return str(data)

    if isinstance(data, list):
        return [convert_object_ids(item) for item in data]

    if isinstance(data, dict):
        return {
            key: convert_object_ids(value)
            for key, value in data.items()
        }

    return data


# --------------------------------------------------
# FIND USER
# --------------------------------------------------

def find_user(user_id):

    # Our Flask authentication system uses UUID userId.
    # The MongoDB users collection has its own _id ObjectId.

    user = db.users.find_one({
        "userId": user_id
    })

    return user


# --------------------------------------------------
# ADD PRODUCT TO WISHLIST
# --------------------------------------------------

@wishlist_bp.route("/api/wishlist", methods=["POST"])
def add_to_wishlist():

    data = request.get_json()

    if not data:
        return jsonify({
            "message": "Request body is required"
        }), 400

    user_id = data.get("userId")
    product_id = data.get("productId")

    if not user_id or not product_id:
        return jsonify({
            "message": "userId and productId are required"
        }), 400

    # ----------------------------------------------
    # Find user
    # ----------------------------------------------

    user = find_user(user_id)

    if not user:
        return jsonify({
            "message": "User not found"
        }), 404

    # ----------------------------------------------
    # Convert product ID to ObjectId
    # ----------------------------------------------

    try:
        product_object_id = ObjectId(product_id)
    except Exception:
        return jsonify({
            "message": "Invalid product ID"
        }), 400

    # ----------------------------------------------
    # Check product
    # ----------------------------------------------

    product = db.products.find_one({
        "_id": product_object_id
    })

    if not product:
        return jsonify({
            "message": "Product not found"
        }), 404

    # ----------------------------------------------
    # Check if already in wishlist
    # ----------------------------------------------

    existing = db.wishlists.find_one({
        "userId": user["_id"],
        "productId": product_object_id
    })

    if existing:
        return jsonify({
            "message": "Product is already in wishlist"
        }), 409

    # ----------------------------------------------
    # Create wishlist item
    # ----------------------------------------------

    wishlist_item = {
        "wishlistId": str(uuid4()),
        "userId": user["_id"],
        "productId": product_object_id,
        "createdAt": datetime.now(timezone.utc)
    }

    db.wishlists.insert_one(wishlist_item)

    wishlist_item = convert_object_ids(wishlist_item)

    return jsonify({
        "message": "Product added to wishlist",
        "wishlist": wishlist_item
    }), 201


# --------------------------------------------------
# GET USER WISHLIST
# --------------------------------------------------

@wishlist_bp.route(
    "/api/wishlist/<user_id>",
    methods=["GET"]
)
def get_wishlist(user_id):

    # Find user using our UUID
    user = find_user(user_id)

    if not user:
        return jsonify({
            "message": "User not found"
        }), 404

    wishlist = list(
        db.wishlists.find({
            "userId": user["_id"]
        })
    )

    wishlist = convert_object_ids(wishlist)

    return jsonify({
        "wishlist": wishlist
    }), 200


# --------------------------------------------------
# REMOVE PRODUCT FROM WISHLIST
# --------------------------------------------------

@wishlist_bp.route(
    "/api/wishlist/<user_id>/<product_id>",
    methods=["DELETE"]
)
def remove_from_wishlist(user_id, product_id):

    # Find user
    user = find_user(user_id)

    if not user:
        return jsonify({
            "message": "User not found"
        }), 404

    # Convert product ID
    try:
        product_object_id = ObjectId(product_id)
    except Exception:
        return jsonify({
            "message": "Invalid product ID"
        }), 400

    result = db.wishlists.delete_one({
        "userId": user["_id"],
        "productId": product_object_id
    })

    if result.deleted_count == 0:
        return jsonify({
            "message": "Product not found in wishlist"
        }), 404

    return jsonify({
        "message": "Product removed from wishlist"
    }), 200