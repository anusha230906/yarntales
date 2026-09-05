from flask import Blueprint, request, jsonify
from config import db
from bson import ObjectId
from uuid import uuid4
from datetime import datetime, timezone

import razorpay
from config import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET


order_bp = Blueprint("order", __name__)


# -------------------------------------------------
# RAZORPAY CLIENT
# -------------------------------------------------

razorpay_client = razorpay.Client(
    auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
)


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
# CALCULATE ORDER TOTAL
# -------------------------------------------------

def calculate_order_items(items):

    if not isinstance(items, list):
        return None, None, {
            "message": "items must be an array"
        }

    if len(items) == 0:
        return None, None, {
            "message": "Order must contain at least one item"
        }

    order_items = []
    total = 0

    for item in items:

        if not isinstance(item, dict):
            return None, None, {
                "message": "Each order item must be an object"
            }

        product_id = item.get("productId")
        quantity = item.get("quantity", 1)

        if not product_id:
            return None, None, {
                "message": "Each item must contain productId"
            }

        try:
            product_object_id = ObjectId(product_id)

        except Exception:
            return None, None, {
                "message": "Invalid product ID"
            }

        product = db.products.find_one({
            "_id": product_object_id
        })

        if not product:
            return None, None, {
                "message": "Product not found",
                "productId": product_id
            }

        try:
            quantity = int(quantity)

        except (ValueError, TypeError):
            return None, None, {
                "message": "Quantity must be a number"
            }

        if quantity <= 0:
            return None, None, {
                "message": "Quantity must be greater than 0"
            }

        price = float(product.get("basePrice", 0))

        if price <= 0:
            return None, None, {
                "message": "Product price must be greater than 0"
            }

        subtotal = price * quantity

        order_items.append({
            "productId": product_object_id,
            "quantity": quantity,
            "subtotal": subtotal
        })

        total += subtotal

    return order_items, total, None


# -------------------------------------------------
# CREATE RAZORPAY PAYMENT ORDER
# -------------------------------------------------

@order_bp.route("/api/payment/create", methods=["POST"])
def create_razorpay_payment():

    data = request.get_json()

    if not data:
        return jsonify({
            "message": "Request body is required"
        }), 400

    user_id = data.get("userId")
    items = data.get("items")

    if not user_id:
        return jsonify({
            "message": "userId is required"
        }), 400

    user = find_user(user_id)

    if not user:
        return jsonify({
            "message": "User not found"
        }), 404

    order_items, total, error = calculate_order_items(items)

    if error:
        return jsonify(error), 400

    # Razorpay amount is always in the smallest currency unit.
    # For INR, this means paise.
    amount_in_paise = int(round(total * 100))

    try:

        razorpay_order = razorpay_client.order.create({
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": str(uuid4()),
            "notes": {
                "userId": user_id
            }
        })

    except Exception as e:

        return jsonify({
            "message": "Unable to create Razorpay payment order",
            "error": str(e)
        }), 500

    return jsonify({
        "message": "Razorpay payment order created",
        "keyId": RAZORPAY_KEY_ID,
        "razorpayOrderId": razorpay_order["id"],
        "amount": amount_in_paise,
        "currency": "INR",
        "total": total
    }), 201


# -------------------------------------------------
# VERIFY RAZORPAY PAYMENT
# -------------------------------------------------

@order_bp.route("/api/payment/verify", methods=["POST"])
def verify_razorpay_payment():

    data = request.get_json()

    if not data:
        return jsonify({
            "message": "Request body is required"
        }), 400

    razorpay_order_id = data.get("razorpay_order_id")
    razorpay_payment_id = data.get("razorpay_payment_id")
    razorpay_signature = data.get("razorpay_signature")

    if not razorpay_order_id:
        return jsonify({
            "message": "razorpay_order_id is required"
        }), 400

    if not razorpay_payment_id:
        return jsonify({
            "message": "razorpay_payment_id is required"
        }), 400

    if not razorpay_signature:
        return jsonify({
            "message": "razorpay_signature is required"
        }), 400

    try:

        razorpay_client.utility.verify_payment_signature({
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature
        })

        return jsonify({
            "message": "Payment signature verified successfully",
            "verified": True,
            "paymentId": razorpay_payment_id,
            "razorpayOrderId": razorpay_order_id
        }), 200

    except Exception:

        return jsonify({
            "message": "Payment signature verification failed",
            "verified": False
        }), 400


# -------------------------------------------------
# CREATE YARNTales ORDER
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

    allowed_payment_methods = [
        "UPI",
        "Card",
        "Cash on Delivery"
    ]

    if payment_method not in allowed_payment_methods:

        return jsonify({
            "message": "Invalid payment method",
            "allowedPaymentMethods": allowed_payment_methods
        }), 400

    # -------------------------------------------------
    # USER
    # -------------------------------------------------

    if not user_id:

        return jsonify({
            "message": "userId is required"
        }), 400

    user = find_user(user_id)

    if not user:

        return jsonify({
            "message": "User not found"
        }), 404

    # -------------------------------------------------
    # SHIPPING ADDRESS
    # -------------------------------------------------

    if not shipping_address:

        return jsonify({
            "message": "shippingAddress is required"
        }), 400

    # -------------------------------------------------
    # ORDER ITEMS
    # -------------------------------------------------

    order_items, total, error = calculate_order_items(items)

    if error:

        return jsonify(error), 400

    # -------------------------------------------------
    # PAYMENT STATUS
    # -------------------------------------------------

    if payment_method == "Cash on Delivery":

        payment_status = "pending"

    else:

        # For Razorpay payments, the frontend must only
        # send "paid" after successful server verification.
        if payment_status != "paid":

            payment_status = "pending"

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

        # Required tracking status
        "status": "order_confirmed",

        # Shipping information
        "shippingAddress": shipping_address,

        # Payment information
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