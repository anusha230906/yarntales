from flask import Blueprint, request, jsonify
from config import db
from bson import ObjectId
from uuid import uuid4
from datetime import datetime, timezone

customization_bp = Blueprint("customization", __name__)


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
# CREATE CUSTOMIZATION
# --------------------------------------------------

@customization_bp.route("/api/customizations", methods=["POST"])
def create_customization():

    data = request.get_json()

    if not data:
        return jsonify({
            "message": "Request body is required"
        }), 400

    user_id = data.get("userId")
    product_id = data.get("productId")
    color = data.get("color")
    size = data.get("size")
    features = data.get("features", [])
    accessory = data.get("accessory")
    personalized_name = data.get("personalizedName")

    if not user_id or not product_id or not color or not size:
        return jsonify({
            "message": "userId, productId, color and size are required"
        }), 400

    # Check whether product exists
    try:
        product = db.products.find_one({
            "_id": ObjectId(product_id)
        })
    except Exception:
        product = None

    if not product:
        return jsonify({
            "message": "Product not found"
        }), 404

    # Validate color
    available_colors = product.get("availableColors", [])

    if color not in available_colors:
        return jsonify({
            "message": "Selected color is not available",
            "availableColors": available_colors
        }), 400

    # Validate size
    available_sizes = product.get("availableSizes", [])

    if size not in available_sizes:
        return jsonify({
            "message": "Selected size is not available",
            "availableSizes": available_sizes
        }), 400

    customization_id = str(uuid4())

    customization = {
        "customizationId": customization_id,
        "userId": user_id,
        "productId": product_id,
        "color": color,
        "size": size,
        "features": features,
        "accessory": accessory,
        "personalizedName": personalized_name,
        "createdAt": datetime.now(timezone.utc)
    }

    db.customizations.insert_one(customization)

    customization = convert_object_ids(customization)

    return jsonify({
        "message": "Customization saved successfully",
        "customization": customization
    }), 201


# --------------------------------------------------
# GET USER CUSTOMIZATIONS
# --------------------------------------------------

@customization_bp.route(
    "/api/customizations/user/<user_id>",
    methods=["GET"]
)
def get_user_customizations(user_id):

    customizations = list(
        db.customizations.find({
            "userId": user_id
        })
    )

    customizations = convert_object_ids(customizations)

    return jsonify({
        "customizations": customizations
    }), 200


# --------------------------------------------------
# GET SINGLE CUSTOMIZATION
# --------------------------------------------------

@customization_bp.route(
    "/api/customizations/<customization_id>",
    methods=["GET"]
)
def get_customization(customization_id):

    customization = db.customizations.find_one({
        "customizationId": customization_id
    })

    if not customization:
        return jsonify({
            "message": "Customization not found"
        }), 404

    customization = convert_object_ids(customization)

    return jsonify({
        "customization": customization
    }), 200

# --------------------------------------------------
# GET CUSTOM BUILDER BASE PRODUCT
# --------------------------------------------------

@customization_bp.route("/api/customizations/template", methods=["GET"])
def get_customization_template():
    product = db.products.find_one({
        "seedKey": "custom-builder-base",
        "isActive": True,
    })

    if not product:
        return jsonify({
            "message": "Custom builder product is not seeded"
        }), 404

    return jsonify({
        "product": convert_object_ids(product)
    }), 200
