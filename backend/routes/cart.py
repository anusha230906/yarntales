from datetime import datetime, timezone
from uuid import uuid4

from bson import ObjectId
from flask import Blueprint, jsonify, request

from config import db

cart_bp = Blueprint("cart", __name__)


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


@cart_bp.route("/api/cart", methods=["POST"])
def add_to_cart():
    data = request.get_json()

    if not data:
        return jsonify({"message": "Request body is required"}), 400

    user_id = data.get("userId")
    product_id = data.get("productId")
    quantity = data.get("quantity", 1)
    customization_id = data.get("customizationId")

    if not user_id or not product_id:
        return jsonify({
            "message": "userId and productId are required"
        }), 400

    try:
        quantity = int(quantity)
    except (ValueError, TypeError):
        return jsonify({
            "message": "Quantity must be a number"
        }), 400

    if quantity < 1:
        return jsonify({
            "message": "Quantity must be at least 1"
        }), 400

    # Check if product exists
    product = db.products.find_one({"productId": product_id})
    if not product:
        try:
            product = db.products.find_one({"_id": ObjectId(product_id)})
        except Exception:
            product = None

    if not product:
        return jsonify({
            "message": "Product not found"
        }), 404

    # Check if same product/customization is already in cart
    existing = db.carts.find_one({
        "userId": user_id,
        "productId": product_id,
        "customizationId": customization_id
    })

    if existing:
        new_quantity = existing.get("quantity", 1) + quantity

        db.carts.update_one(
            {"_id": existing["_id"]},
            {
                "$set": {
                    "quantity": new_quantity,
                    "updatedAt": datetime.now(timezone.utc)
                }
            }
        )

        updated_cart = db.carts.find_one({
            "_id": existing["_id"]
        })

        return jsonify({
            "message": "Cart quantity updated",
            "cartItem": convert_object_ids(updated_cart)
        }), 200

    cart_item = {
        "cartId": str(uuid4()),
        "userId": user_id,
        "productId": product_id,
        "quantity": quantity,
        "customizationId": customization_id,
        "createdAt": datetime.now(timezone.utc)
    }

    db.carts.insert_one(cart_item)

    cart_item = convert_object_ids(cart_item)

    return jsonify({
        "message": "Product added to cart",
        "cartItem": cart_item
    }), 201


@cart_bp.route("/api/cart/<user_id>", methods=["GET"])
def get_cart(user_id):
    cart_items = list(db.carts.find({"userId": user_id}))

    enriched = []
    for item in cart_items:
        item = dict(item)
        product_id = str(item.get("productId", ""))
        product = None

        try:
            product = db.products.find_one({"_id": ObjectId(product_id)})
        except Exception:
            product = db.products.find_one({"productId": product_id})

        if product:
            item["productName"] = product.get("name")
            item["category"] = product.get("category", "Handmade")
            item["unitPrice"] = float(product.get("basePrice", 0))
            item["images"] = product.get("images", [])

        # For a customized piece, prefer the preview image captured at
        # customization time (it reflects the shape/base the shopper
        # actually picked, e.g. Mini Bag vs Pouch vs Keychain).
        customization_id = item.get("customizationId")
        if customization_id:
            customization = db.customizations.find_one({
                "customizationId": customization_id
            })

            if customization:
                if customization.get("previewImage"):
                    item["images"] = [customization["previewImage"]]
                if customization.get("base"):
                    item["variantLabel"] = customization["base"]

        enriched.append(item)

    return jsonify({
        "cart": convert_object_ids(enriched)
    }), 200


@cart_bp.route("/api/cart/<user_id>/<product_id>", methods=["PUT"])
def update_cart_quantity(user_id, product_id):
    data = request.get_json()

    if not data:
        return jsonify({
            "message": "Request body is required"
        }), 400

    quantity = data.get("quantity")

    try:
        quantity = int(quantity)
    except (ValueError, TypeError):
        return jsonify({
            "message": "Quantity must be a number"
        }), 400

    if quantity < 1:
        return jsonify({
            "message": "Quantity must be at least 1"
        }), 400

    result = db.carts.update_one(
        {
            "userId": user_id,
            "productId": product_id
        },
        {
            "$set": {
                "quantity": quantity,
                "updatedAt": datetime.now(timezone.utc)
            }
        }
    )

    if result.matched_count == 0:
        return jsonify({
            "message": "Cart item not found"
        }), 404

    return jsonify({
        "message": "Cart quantity updated"
    }), 200


@cart_bp.route("/api/cart/<user_id>/<product_id>", methods=["DELETE"])
def remove_from_cart(user_id, product_id):
    result = db.carts.delete_one({
        "userId": user_id,
        "productId": product_id
    })

    if result.deleted_count == 0:
        return jsonify({
            "message": "Cart item not found"
        }), 404

    return jsonify({
        "message": "Product removed from cart"
    }), 200


@cart_bp.route("/api/cart/<user_id>", methods=["DELETE"])
def clear_cart(user_id):
    result = db.carts.delete_many({
        "userId": user_id
    })

    return jsonify({
        "message": "Cart cleared",
        "removedItems": result.deleted_count
    }), 200