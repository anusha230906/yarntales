from flask import Blueprint, request, jsonify
from config import db
from bson import ObjectId
from uuid import uuid4
from datetime import datetime, timezone

order_bp = Blueprint("order", __name__)


# -------------------------------------------------
# CONVERT MONGODB OBJECTID TO STRING
# -------------------------------------------------

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


# -------------------------------------------------
# FIND USER
# -------------------------------------------------

def find_user(user_id):

    return db.users.find_one({
        "userId": user_id
    })


# -------------------------------------------------
# CREATE ORDER
# -------------------------------------------------

@order_bp.route("/api/orders", methods=["POST"])
def create_order():

    data = request.get_json()

    if not data:
        return jsonify({
            "message": "Request body is required"
        }), 400

    user_id = data.get("userId")
    shipping_address = data.get("shippingAddress")
    payment_method = data.get("paymentMethod", "UPI")
    payment_status = data.get("paymentStatus")
    payment_reference = data.get("paymentReference")
    items = data.get("items")

    allowed_payment_methods = ["UPI", "Card", "Cash on Delivery"]
    if payment_method not in allowed_payment_methods:
        return jsonify({
            "message": "Invalid payment method",
            "allowedPaymentMethods": allowed_payment_methods
        }), 400

    # Payment is intentionally simulated for this college project.
    # UPI/Card are treated as paid after the frontend confirmation step;
    # Cash on Delivery remains pending.
    expected_payment_status = "pending" if payment_method == "Cash on Delivery" else "paid"
    payment_status = expected_payment_status

    # Check user ID
    if not user_id:
        return jsonify({
            "message": "userId is required"
        }), 400

    # Check shipping address
    if not shipping_address:
        return jsonify({
            "message": "shippingAddress is required"
        }), 400

    # Check items
    if not isinstance(items, list):
        return jsonify({
            "message": "items must be an array"
        }), 400

    if len(items) == 0:
        return jsonify({
            "message": "Order must contain at least one item"
        }), 400

    # -------------------------------------------------
    # FIND USER
    # -------------------------------------------------

    user = find_user(user_id)

    if not user:
        return jsonify({
            "message": "User not found"
        }), 404

    order_items = []
    total = 0

    # -------------------------------------------------
    # PROCESS ORDER ITEMS
    # -------------------------------------------------

    for item in items:

        if not isinstance(item, dict):
            return jsonify({
                "message": "Each order item must be an object"
            }), 400

        product_id = item.get("productId")
        quantity = item.get("quantity", 1)

        # Product ID required
        if not product_id:
            return jsonify({
                "message": "Each item must contain productId"
            }), 400

        # Convert product ID to ObjectId
        try:
            product_object_id = ObjectId(product_id)

        except Exception:
            return jsonify({
                "message": "Invalid product ID"
            }), 400

        # Find product
        product = db.products.find_one({
            "_id": product_object_id
        })

        if not product:
            return jsonify({
                "message": "Product not found",
                "productId": product_id
            }), 404

        # Validate quantity
        try:
            quantity = int(quantity)

        except (ValueError, TypeError):
            return jsonify({
                "message": "Quantity must be a number"
            }), 400

        if quantity <= 0:
            return jsonify({
                "message": "Quantity must be greater than 0"
            }), 400

        # Get product price
        price = float(product.get("basePrice", 0))

        if price <= 0:
            return jsonify({
                "message": "Product price must be greater than 0"
            }), 400

        # Calculate subtotal
        subtotal = price * quantity

        # -------------------------------------------------
        # IMPORTANT:
        # MongoDB validator requires:
        # productId
        # quantity
        # subtotal
        # -------------------------------------------------

        order_items.append({
            "productId": product_object_id,
            "quantity": quantity,
            "subtotal": subtotal
        })

        total += subtotal

    # -------------------------------------------------
    # CREATE ORDER
    # -------------------------------------------------

    order = {
        "orderId": str(uuid4()),

        # MongoDB expects the actual User ObjectId
        "userId": user["_id"],

        # Required order items
        "items": order_items,

        # Total order amount
        "total": total,

        # Required status value
        "status": "order_confirmed",

        # Shipping information
        "shippingAddress": shipping_address,

        # Simulated payment details
        "paymentMethod": payment_method,
        "paymentStatus": payment_status,
        "paymentReference": payment_reference,

        # Timestamps
        "createdAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc)
    }

    # -------------------------------------------------
    # SAVE ORDER
    # -------------------------------------------------

    db.orders.insert_one(order)

    # Convert ObjectIds before returning JSON
    order = convert_object_ids(order)

    return jsonify({
        "message": "Order created successfully",
        "order": order
    }), 201


# -------------------------------------------------
# GET USER ORDERS
# -------------------------------------------------

@order_bp.route("/api/orders/user/<user_id>", methods=["GET"])
def get_user_orders(user_id):

    user = find_user(user_id)

    if not user:
        return jsonify({
            "message": "User not found"
        }), 404

    orders = list(
        db.orders.find({
            "userId": user["_id"]
        }).sort("createdAt", -1)
    )

    orders = convert_object_ids(orders)

    return jsonify({
        "orders": orders
    }), 200


# -------------------------------------------------
# GET SINGLE ORDER
# -------------------------------------------------

@order_bp.route("/api/orders/<order_id>", methods=["GET"])
def get_order(order_id):

    order = db.orders.find_one({
        "orderId": order_id
    })

    if not order:
        return jsonify({
            "message": "Order not found"
        }), 404

    order = convert_object_ids(order)

    return jsonify({
        "order": order
    }), 200