import os
import uuid
from datetime import datetime

from flask import Blueprint, request, jsonify
from bson import ObjectId
import razorpay

from config import db, RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET


order_bp = Blueprint("order", __name__)


# ============================================================
# RAZORPAY CLIENT
# ============================================================

razorpay_client = None

if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    razorpay_client = razorpay.Client(
        auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
    )


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def convert_object_ids(data):
    """
    Convert MongoDB ObjectId values into strings so they can
    safely be returned as JSON.
    """

    if isinstance(data, ObjectId):
        return str(data)

    if isinstance(data, dict):
        return {
            key: convert_object_ids(value)
            for key, value in data.items()
        }

    if isinstance(data, list):
        return [
            convert_object_ids(item)
            for item in data
        ]

    return data


def find_user(user_id):
    """
    Find a user by either MongoDB ObjectId or string userId.
    """

    try:
        if ObjectId.is_valid(user_id):
            user = db.users.find_one({
                "_id": ObjectId(user_id)
            })

            if user:
                return user
    except Exception:
        pass

    user = db.users.find_one({
        "userId": user_id
    })

    if user:
        return user

    user = db.users.find_one({
        "id": user_id
    })

    return user


def calculate_order_items(items):
    """
    Validate cart items against products in MongoDB and
    calculate the final order total using database prices.
    """

    calculated_items = []
    total_amount = 0

    for item in items:

        product_id = (
            item.get("productId")
            or item.get("id")
            or item.get("_id")
        )

        quantity = item.get("quantity", 1)

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            quantity = 1

        if quantity < 1:
            quantity = 1

        if not product_id:
            continue

        product = None

        # Try ObjectId
        try:
            if ObjectId.is_valid(str(product_id)):
                product = db.products.find_one({
                    "_id": ObjectId(str(product_id))
                })
        except Exception:
            pass

        # Try productId field
        if not product:
            product = db.products.find_one({
                "productId": str(product_id)
            })

        # Try id field
        if not product:
            product = db.products.find_one({
                "id": str(product_id)
            })

        if not product:
            continue

        price = product.get("price", 0)

        try:
            price = float(price)
        except (TypeError, ValueError):
            price = 0

        subtotal = price * quantity
        total_amount += subtotal

        calculated_items.append({
            "productId": str(
                product.get("productId")
                or product.get("_id")
            ),
            "name": product.get(
                "name",
                product.get("title", "Product")
            ),
            "price": price,
            "quantity": quantity,
            "subtotal": subtotal,
            "image": product.get(
                "image",
                product.get("imageUrl", "")
            ),
        })

    return calculated_items, total_amount


# ============================================================
# CREATE RAZORPAY PAYMENT ORDER
# ============================================================

@order_bp.route("/api/payment/create", methods=["POST"])
def create_payment():

    try:

        if not razorpay_client:
            return jsonify({
                "error": "Razorpay is not configured"
            }), 500

        data = request.get_json()

        if not data:
            return jsonify({
                "error": "Request body is required"
            }), 400

        amount = data.get("amount")

        if amount is None:
            return jsonify({
                "error": "Amount is required"
            }), 400

        try:
            amount = float(amount)
        except (TypeError, ValueError):
            return jsonify({
                "error": "Invalid amount"
            }), 400

        if amount <= 0:
            return jsonify({
                "error": "Amount must be greater than zero"
            }), 400

        # Razorpay expects amount in paise
        amount_in_paise = int(round(amount * 100))

        payment_data = {
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": str(uuid.uuid4())[:40],
        }

        razorpay_order = razorpay_client.order.create(
            data=payment_data
        )

        return jsonify({
            "success": True,
            "order": razorpay_order
        }), 200

    except Exception as e:

        print("Razorpay create order error:", str(e))

        return jsonify({
            "error": "Failed to create payment order",
            "details": str(e)
        }), 500


# ============================================================
# VERIFY RAZORPAY PAYMENT
# ============================================================

@order_bp.route("/api/payment/verify", methods=["POST"])
def verify_payment():

    try:

        if not razorpay_client:
            return jsonify({
                "error": "Razorpay is not configured"
            }), 500

        data = request.get_json()

        if not data:
            return jsonify({
                "error": "Request body is required"
            }), 400

        razorpay_order_id = data.get(
            "razorpay_order_id"
        )

        razorpay_payment_id = data.get(
            "razorpay_payment_id"
        )

        razorpay_signature = data.get(
            "razorpay_signature"
        )

        if not all([
            razorpay_order_id,
            razorpay_payment_id,
            razorpay_signature
        ]):
            return jsonify({
                "error": "Missing Razorpay payment details"
            }), 400

        verification_data = {
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
        }

        razorpay_client.utility.verify_payment_signature(
            verification_data
        )

        return jsonify({
            "success": True,
            "message": "Payment verified successfully"
        }), 200

    except Exception as e:

        print("Razorpay verification error:", str(e))

        return jsonify({
            "success": False,
            "error": "Payment verification failed",
            "details": str(e)
        }), 400


# ============================================================
# CREATE ORDER
# ============================================================

@order_bp.route("/api/orders", methods=["POST"])
def create_order():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "error": "Request body is required"
            }), 400

        # ----------------------------------------------------
        # USER
        # ----------------------------------------------------

        user_id = data.get("userId")

        if not user_id:
            return jsonify({
                "error": "User ID is required"
            }), 400

        user = find_user(user_id)

        if not user:
            return jsonify({
                "error": "User not found"
            }), 404

        # ----------------------------------------------------
        # SHIPPING ADDRESS
        # ----------------------------------------------------

        shipping_address = data.get(
            "shippingAddress"
        )

        if not shipping_address:
            return jsonify({
                "error": "Shipping address is required"
            }), 400

        # ----------------------------------------------------
        # ITEMS
        # ----------------------------------------------------

        items = data.get("items", [])

        if not items:
            return jsonify({
                "error": "Order must contain at least one item"
            }), 400

        # ----------------------------------------------------
        # CALCULATE TOTAL
        # ----------------------------------------------------

        calculated_items, total_amount = calculate_order_items(
            items
        )

        if not calculated_items:
            return jsonify({
                "error": "No valid products found in order"
            }), 400

        # ----------------------------------------------------
        # PAYMENT
        # ----------------------------------------------------

        payment_method = data.get(
            "paymentMethod",
            "COD"
        )

        payment_status = data.get(
            "paymentStatus",
            "pending"
        )

        payment_reference = data.get(
            "paymentReference"
        )

        # Only mark as paid when frontend explicitly sends
        # a successful payment status.
        if payment_status != "paid":
            payment_status = "pending"

        # ----------------------------------------------------
        # ORDER
        # ----------------------------------------------------

        order = {
            "orderId": str(uuid.uuid4()),

            "userId": str(user_id),

            "customerName": user.get(
                "name",
                user.get("fullName", "")
            ),

            "customerEmail": user.get(
                "email",
                ""
            ),

            "items": calculated_items,

            "shippingAddress": shipping_address,

            "totalAmount": total_amount,

            "paymentMethod": payment_method,

            "paymentStatus": payment_status,

            "paymentReference": payment_reference,

            "status": "order_confirmed",

            "createdAt": datetime.utcnow(),
        }

        # ----------------------------------------------------
        # SAVE ORDER FIRST
        # ----------------------------------------------------

        db.orders.insert_one(order)

        # ----------------------------------------------------
        # IMPORTANT
        # ----------------------------------------------------
        #
        # DO NOT send Gmail SMTP email here.
        #
        # Railway can block / delay SMTP connections to
        # smtp.gmail.com:587.
        #
        # If email is sent here, the customer's order request
        # waits for Gmail and Gunicorn can kill the worker.
        #
        # The order must always be saved and returned first.
        #
        # ----------------------------------------------------

        order = convert_object_ids(order)

        return jsonify({
            "message": "Order created successfully",
            "order": order
        }), 201

    except Exception as e:

        print("Create order error:", str(e))

        return jsonify({
            "error": "Failed to create order",
            "details": str(e)
        }), 500


# ============================================================
# GET USER ORDERS
# ============================================================

@order_bp.route(
    "/api/orders/user/<user_id>",
    methods=["GET"]
)
def get_user_orders(user_id):

    try:

        orders = list(
            db.orders.find({
                "userId": str(user_id)
            }).sort(
                "createdAt",
                -1
            )
        )

        orders = convert_object_ids(orders)

        return jsonify({
            "orders": orders
        }), 200

    except Exception as e:

        print("Get user orders error:", str(e))

        return jsonify({
            "error": "Failed to fetch orders",
            "details": str(e)
        }), 500


# ============================================================
# GET SINGLE ORDER
# ============================================================

@order_bp.route(
    "/api/orders/<order_id>",
    methods=["GET"]
)
def get_order(order_id):

    try:

        order = db.orders.find_one({
            "orderId": str(order_id)
        })

        # Fallback to MongoDB _id
        if not order and ObjectId.is_valid(order_id):

            order = db.orders.find_one({
                "_id": ObjectId(order_id)
            })

        if not order:

            return jsonify({
                "error": "Order not found"
            }), 404

        order = convert_object_ids(order)

        return jsonify({
            "order": order
        }), 200

    except Exception as e:

        print("Get order error:", str(e))

        return jsonify({
            "error": "Failed to fetch order",
            "details": str(e)
        }), 500