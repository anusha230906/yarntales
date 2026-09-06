import os
import uuid
from datetime import datetime

from flask import Blueprint, request, jsonify
from bson import ObjectId
import razorpay

from config import db, RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET


# ============================================================
# BLUEPRINT
# ============================================================

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
# HELPER: CONVERT OBJECT IDS
# ============================================================

def convert_object_ids(data):
    """
    Convert MongoDB ObjectId values into strings
    so they can safely be returned as JSON.
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


# ============================================================
# HELPER: FIND USER
# ============================================================

def find_user(user_id):
    """
    Find user using:
    1. Application userId
    2. MongoDB _id
    """

    if not user_id:
        return None

    # --------------------------------------------------------
    # Try application userId
    # --------------------------------------------------------

    user = db.users.find_one({
        "userId": str(user_id)
    })

    if user:
        return user

    # --------------------------------------------------------
    # Try MongoDB _id
    # --------------------------------------------------------

    try:

        if ObjectId.is_valid(str(user_id)):

            user = db.users.find_one({
                "_id": ObjectId(str(user_id))
            })

            if user:
                return user

    except Exception:
        pass

    # --------------------------------------------------------
    # Try legacy id field
    # --------------------------------------------------------

    user = db.users.find_one({
        "id": str(user_id)
    })

    if user:
        return user

    return None


# ============================================================
# HELPER: FIND PRODUCT
# ============================================================

def find_product(product_id):
    """
    Find a product using productId, MongoDB _id,
    or legacy id field.
    """

    if not product_id:
        return None

    # --------------------------------------------------------
    # Try productId
    # --------------------------------------------------------

    product = db.products.find_one({
        "productId": str(product_id)
    })

    if product:
        return product

    # --------------------------------------------------------
    # Try MongoDB _id
    # --------------------------------------------------------

    try:

        if ObjectId.is_valid(str(product_id)):

            product = db.products.find_one({
                "_id": ObjectId(str(product_id))
            })

            if product:
                return product

    except Exception:
        pass

    # --------------------------------------------------------
    # Try legacy id
    # --------------------------------------------------------

    product = db.products.find_one({
        "id": str(product_id)
    })

    if product:
        return product

    return None


# ============================================================
# HELPER: CALCULATE ORDER ITEMS
# ============================================================

def calculate_order_items(items):
    """
    Validate cart products against MongoDB and calculate
    the final order total.

    MongoDB schema requires:
        items.productId -> ObjectId
        items.subtotal  -> greater than 0
    """

    calculated_items = []
    total = 0

    for item in items:

        # ----------------------------------------------------
        # Product ID
        # ----------------------------------------------------

        product_id = (
            item.get("productId")
            or item.get("id")
            or item.get("_id")
        )

        if not product_id:
            continue

        # ----------------------------------------------------
        # Quantity
        # ----------------------------------------------------

        quantity = item.get(
            "quantity",
            1
        )

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            quantity = 1

        if quantity < 1:
            quantity = 1

        # ----------------------------------------------------
        # Find product
        # ----------------------------------------------------

        product = find_product(product_id)

        if not product:
            print(
                "Product not found:",
                product_id
            )
            continue

        # ----------------------------------------------------
        # MongoDB product ID
        # ----------------------------------------------------

        mongo_product_id = product.get("_id")

        if not mongo_product_id:
            print(
                "Product has no MongoDB _id:",
                product_id
            )
            continue

        # ----------------------------------------------------
        # Price
        #
        # Database documentation/schema uses basePrice.
        # Fall back to price for compatibility.
        # ----------------------------------------------------

        price = product.get(
            "basePrice",
            product.get(
                "price",
                0
            )
        )

        try:
            price = float(price)
        except (TypeError, ValueError):
            price = 0

        # ----------------------------------------------------
        # Subtotal
        # ----------------------------------------------------

        subtotal = price * quantity

        # MongoDB schema requires subtotal > 0
        if subtotal <= 0:
            print(
                "Invalid product subtotal:",
                product_id,
                subtotal
            )
            continue

        total += subtotal

        # ----------------------------------------------------
        # Product name
        # ----------------------------------------------------

        product_name = product.get(
            "name",
            product.get(
                "title",
                "Product"
            )
        )

        # ----------------------------------------------------
        # Product image
        # ----------------------------------------------------

        product_image = product.get(
            "image",
            product.get(
                "imageUrl",
                ""
            )
        )

        # ----------------------------------------------------
        # Store order item
        # ----------------------------------------------------

        calculated_items.append({
            "productId": mongo_product_id,
            "name": product_name,
            "quantity": quantity,
            "price": price,
            "subtotal": subtotal,
            "image": product_image
        })

    return calculated_items, total


# ============================================================
# RAZORPAY: CREATE PAYMENT ORDER
# ============================================================

@order_bp.route(
    "/api/payment/create",
    methods=["POST"]
)
def create_payment():

    try:

        # ----------------------------------------------------
        # Check Razorpay configuration
        # ----------------------------------------------------

        if not razorpay_client:

            return jsonify({
                "error": "Razorpay is not configured"
            }), 500

        data = request.get_json()

        if not data:

            return jsonify({
                "error": "Request body is required"
            }), 400

        # ----------------------------------------------------
        # Amount
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Razorpay uses paise
        # ----------------------------------------------------

        amount_in_paise = int(
            round(amount * 100)
        )

        payment_data = {
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": str(uuid.uuid4())[:40]
        }

        # ----------------------------------------------------
        # Create Razorpay order
        # ----------------------------------------------------

        razorpay_order = razorpay_client.order.create(
            data=payment_data
        )

        return jsonify({
            "success": True,
            "order": razorpay_order
        }), 200

    except Exception as e:

        print(
            "Razorpay create order error:",
            str(e)
        )

        return jsonify({
            "error": "Failed to create payment order",
            "details": str(e)
        }), 500


# ============================================================
# RAZORPAY: VERIFY PAYMENT
# ============================================================

@order_bp.route(
    "/api/payment/verify",
    methods=["POST"]
)
def verify_payment():

    try:

        # ----------------------------------------------------
        # Check Razorpay configuration
        # ----------------------------------------------------

        if not razorpay_client:

            return jsonify({
                "error": "Razorpay is not configured"
            }), 500

        data = request.get_json()

        if not data:

            return jsonify({
                "error": "Request body is required"
            }), 400

        # ----------------------------------------------------
        # Razorpay details
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Verify signature
        # ----------------------------------------------------

        verification_data = {
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature
        }

        razorpay_client.utility.verify_payment_signature(
            verification_data
        )

        return jsonify({
            "success": True,
            "message": "Payment verified successfully"
        }), 200

    except Exception as e:

        print(
            "Razorpay verification error:",
            str(e)
        )

        return jsonify({
            "success": False,
            "error": "Payment verification failed",
            "details": str(e)
        }), 400


# ============================================================
# CREATE ORDER
# ============================================================

@order_bp.route(
    "/api/orders",
    methods=["POST"]
)
def create_order():

    try:

        # ----------------------------------------------------
        # Request data
        # ----------------------------------------------------

        data = request.get_json()

        if not data:

            return jsonify({
                "error": "Request body is required"
            }), 400

        # ----------------------------------------------------
        # USER
        # ----------------------------------------------------

        user_id = data.get(
            "userId"
        )

        if not user_id:

            return jsonify({
                "error": "User ID is required"
            }), 400

        user = find_user(
            user_id
        )

        if not user:

            return jsonify({
                "error": "User not found"
            }), 404

        # ----------------------------------------------------
        # IMPORTANT:
        # MongoDB schema requires userId to be ObjectId.
        # ----------------------------------------------------

        mongo_user_id = user.get(
            "_id"
        )

        if not mongo_user_id:

            return jsonify({
                "error": "User MongoDB ID not found"
            }), 400

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

        items = data.get(
            "items",
            []
        )

        if not items:

            return jsonify({
                "error": "Order must contain at least one item"
            }), 400

        # ----------------------------------------------------
        # CALCULATE ITEMS + TOTAL
        # ----------------------------------------------------

        calculated_items, total = calculate_order_items(
            items
        )

        if not calculated_items:

            return jsonify({
                "error": "No valid products found in order"
            }), 400

        if total <= 0:

            return jsonify({
                "error": "Order total must be greater than zero"
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

        # Only mark payment as paid when explicitly
        # provided as paid by the frontend.
        if payment_status != "paid":

            payment_status = "pending"

        # ----------------------------------------------------
        # ORDER ID
        # ----------------------------------------------------

        order_id = str(
            uuid.uuid4()
        )

        # ----------------------------------------------------
        # CREATE ORDER DOCUMENT
        #
        # IMPORTANT:
        # This structure matches the MongoDB validator:
        #
        # userId     -> ObjectId
        # items      -> array
        # productId  -> ObjectId
        # subtotal   -> > 0
        # total      -> required
        # status     -> required
        # createdAt  -> required
        # ----------------------------------------------------

        order = {

            "orderId": order_id,

            "userId": mongo_user_id,

            "items": calculated_items,

            "total": total,

            "status": "order_confirmed",

            "createdAt": datetime.utcnow(),

            "paymentMethod": payment_method,

            "paymentStatus": payment_status,

            "paymentReference": payment_reference,

            "shippingAddress": shipping_address,

            "customerName": user.get(
                "name",
                user.get(
                    "fullName",
                    ""
                )
            ),

            "customerEmail": user.get(
                "email",
                ""
            )
        }

        # ----------------------------------------------------
        # SAVE ORDER
        # ----------------------------------------------------

        db.orders.insert_one(
            order
        )

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # DO NOT SEND GMAIL SMTP HERE.
        #
        # Railway can block/delay SMTP connections.
        # Sending email here previously caused:
        #
        # WORKER TIMEOUT
        #
        # The order is now saved first and returned
        # immediately.
        # ----------------------------------------------------

        order = convert_object_ids(
            order
        )

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        return jsonify({

            "message": "Order created successfully",

            "order": order

        }), 201

    except Exception as e:

        print(
            "Create order error:",
            str(e)
        )

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

        # ----------------------------------------------------
        # Find user
        # ----------------------------------------------------

        user = find_user(
            user_id
        )

        if not user:

            return jsonify({
                "error": "User not found"
            }), 404

        mongo_user_id = user.get(
            "_id"
        )

        if not mongo_user_id:

            return jsonify({
                "error": "User MongoDB ID not found"
            }), 400

        # ----------------------------------------------------
        # Find orders
        # ----------------------------------------------------

        orders = list(
            db.orders.find({
                "userId": mongo_user_id
            }).sort(
                "createdAt",
                -1
            )
        )

        # ----------------------------------------------------
        # Convert ObjectIds
        # ----------------------------------------------------

        orders = convert_object_ids(
            orders
        )

        return jsonify({
            "orders": orders
        }), 200

    except Exception as e:

        print(
            "Get user orders error:",
            str(e)
        )

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

        order = None

        # ----------------------------------------------------
        # Find using custom orderId
        # ----------------------------------------------------

        order = db.orders.find_one({
            "orderId": str(order_id)
        })

        # ----------------------------------------------------
        # Fallback to MongoDB _id
        # ----------------------------------------------------

        if not order:

            try:

                if ObjectId.is_valid(
                    str(order_id)
                ):

                    order = db.orders.find_one({
                        "_id": ObjectId(
                            str(order_id)
                        )
                    })

            except Exception:
                pass

        # ----------------------------------------------------
        # Not found
        # ----------------------------------------------------

        if not order:

            return jsonify({
                "error": "Order not found"
            }), 404

        # ----------------------------------------------------
        # Convert ObjectIds
        # ----------------------------------------------------

        order = convert_object_ids(
            order
        )

        return jsonify({
            "order": order
        }), 200

    except Exception as e:

        print(
            "Get order error:",
            str(e)
        )

        return jsonify({
            "error": "Failed to fetch order",
            "details": str(e)
        }), 500