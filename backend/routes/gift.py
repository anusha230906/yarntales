from flask import Blueprint, request, jsonify
from config import db
from bson import ObjectId
from uuid import uuid4
from datetime import datetime, timezone

gift_bp = Blueprint("gift", __name__)


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


@gift_bp.route("/api/gift-mode", methods=["POST"])
def create_gift_request():

    data = request.get_json()

    if not data:
        return jsonify({
            "message": "Request body is required"
        }), 400

    user_id = data.get("userId")
    occasion = data.get("occasion")
    budget = data.get("budget")
    gift_wrapping = data.get("giftWrapping", False)
    message_card = data.get("messageCard")
    scheduled_delivery = data.get("scheduledDelivery")

    if not user_id:
        return jsonify({
            "message": "userId is required"
        }), 400

    if not occasion:
        return jsonify({
            "message": "occasion is required"
        }), 400

    if budget is None:
        return jsonify({
            "message": "budget is required"
        }), 400

    try:
        budget = float(budget)
    except (ValueError, TypeError):
        return jsonify({
            "message": "Budget must be a number"
        }), 400

    if budget <= 0:
        return jsonify({
            "message": "Budget must be greater than 0"
        }), 400

    user = db.users.find_one({
        "userId": user_id
    })

    if not user:
        return jsonify({
            "message": "User not found"
        }), 404

    # ---------------------------------------------
    # RULE-BASED PRODUCT RECOMMENDATIONS
    # ---------------------------------------------

    products = list(
        db.products.find({
            "isActive": True,
            "basePrice": {
                "$lte": budget
            }
        }).limit(10)
    )

    recommendations = convert_object_ids(products)

    gift_request = {
        "giftId": str(uuid4()),
        "userId": user["_id"],
        "occasion": occasion,
        "budget": budget,
        "giftWrapping": bool(gift_wrapping),
        "messageCard": message_card,
        "scheduledDelivery": scheduled_delivery,
        "recommendations": recommendations,
        "createdAt": datetime.now(timezone.utc)
    }

    db.gift_mode.insert_one(gift_request)

    gift_request = convert_object_ids(gift_request)

    return jsonify({
        "message": "Gift request created successfully",
        "giftRequest": gift_request
    }), 201


@gift_bp.route("/api/gift-mode/user/<user_id>", methods=["GET"])
def get_user_gift_requests(user_id):

    user = db.users.find_one({
        "userId": user_id
    })

    if not user:
        return jsonify({
            "message": "User not found"
        }), 404

    gift_requests = list(
        db.gift_mode.find({
            "userId": user["_id"]
        }).sort("createdAt", -1)
    )

    gift_requests = convert_object_ids(gift_requests)

    return jsonify({
        "giftRequests": gift_requests
    }), 200


@gift_bp.route("/api/gift-mode/<gift_id>", methods=["GET"])
def get_gift_request(gift_id):

    gift_request = db.gift_mode.find_one({
        "giftId": gift_id
    })

    if not gift_request:
        return jsonify({
            "message": "Gift request not found"
        }), 404

    gift_request = convert_object_ids(gift_request)

    return jsonify({
        "giftRequest": gift_request
    }), 200