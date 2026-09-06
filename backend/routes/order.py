import os
import uuid
from datetime import datetime

from flask import Blueprint, request, jsonify
from bson import ObjectId
import razorpay
import resend

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
# RESEND CONFIGURATION
# ============================================================

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
RESEND_FROM_EMAIL = os.getenv(
    "RESEND_FROM_EMAIL",
    "onboarding@resend.dev"
)

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY


# ============================================================
# HELPER: CONVERT OBJECT IDS
# ============================================================

def convert_object_ids(data):

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

    if not user_id:
        return None

    # Application userId
    user = db.users.find_one({
        "userId": str(user_id)
    })

    if user:
        return user

    # MongoDB _id
    try:

        if ObjectId.is_valid(str(user_id)):

            user = db.users.find_one({
                "_id": ObjectId(str(user_id))
            })

            if user:
                return user

    except Exception:
        pass

    # Legacy id
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

    if not product_id:
        return None

    # productId
    product = db.products.find_one({
        "productId": str(product_id)
    })

    if product:
        return product

    # MongoDB _id
    try:

        if ObjectId.is_valid(str(product_id)):

            product = db.products.find_one({
                "_id": ObjectId(str(product_id))
            })

            if product:
                return product

    except Exception:
        pass

    # legacy id
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

    calculated_items = []
    total = 0

    for item in items:

        product_id = (
            item.get("productId")
            or item.get("id")
            or item.get("_id")
        )

        if not product_id:
            continue

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

        # Find product
        product = find_product(product_id)

        if not product:
            print(
                "Product not found:",
                product_id
            )
            continue

        # MongoDB _id
        mongo_product_id = product.get("_id")

        if not mongo_product_id:
            continue

        # Product price
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

        subtotal = price * quantity

        # Schema requires subtotal > 0
        if subtotal <= 0:
            print(
                "Invalid subtotal:",
                product_id,
                subtotal
            )
            continue

        total += subtotal

        product_name = product.get(
            "name",
            product.get(
                "title",
                "Product"
            )
        )

        product_image = product.get(
            "image",
            product.get(
                "imageUrl",
                ""
            )
        )

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
# SEND ORDER EMAIL THROUGH RESEND
# ============================================================

def send_new_order_email(order, user):

    try:

        # ----------------------------------------------------
        # Check configuration
        # ----------------------------------------------------

        if not RESEND_API_KEY:

            print(
                "Order email skipped: "
                "RESEND_API_KEY is not configured."
            )

            return False

        if not ADMIN_EMAIL:

            print(
                "Order email skipped: "
                "ADMIN_EMAIL is not configured."
            )

            return False

        # ----------------------------------------------------
        # Customer details
        # ----------------------------------------------------

        customer_name = user.get(
            "name",
            user.get(
                "fullName",
                "Customer"
            )
        )

        customer_email = user.get(
            "email",
            "Not provided"
        )

        # ----------------------------------------------------
        # Order details
        # ----------------------------------------------------

        order_id = order.get(
            "orderId",
            "N/A"
        )

        total = order.get(
            "total",
            0
        )

        payment_method = order.get(
            "paymentMethod",
            "N/A"
        )

        payment_status = order.get(
            "paymentStatus",
            "pending"
        )

        payment_reference = order.get(
            "paymentReference"
        ) or "N/A"

        created_at = order.get(
            "createdAt"
        )

        # ----------------------------------------------------
        # Shipping address
        # ----------------------------------------------------

        shipping = order.get(
            "shippingAddress",
            {}
        )

        if isinstance(shipping, dict):

            address_parts = [
                str(shipping.get("name", "")),
                str(shipping.get("address", "")),
                str(shipping.get("line1", "")),
                str(shipping.get("line2", "")),
                str(shipping.get("city", "")),
                str(shipping.get("state", "")),
                str(shipping.get("pincode", "")),
                str(shipping.get("postalCode", ""))
            ]

            address_parts = [
                part.strip()
                for part in address_parts
                if part and part.strip()
            ]

            shipping_address = "<br>".join(
                address_parts
            )

        else:

            shipping_address = str(
                shipping
            )

        if not shipping_address:

            shipping_address = "Not provided"

        # ----------------------------------------------------
        # Items HTML
        # ----------------------------------------------------

        items_html = ""

        for item in order.get(
            "items",
            []
        ):

            name = item.get(
                "name",
                "Product"
            )

            quantity = item.get(
                "quantity",
                1
            )

            price = item.get(
                "price",
                0
            )

            subtotal = item.get(
                "subtotal",
                0
            )

            items_html += f"""
            <tr>
                <td style="padding:10px;border-bottom:1px solid #eee;">
                    {name}
                </td>

                <td style="padding:10px;border-bottom:1px solid #eee;text-align:center;">
                    {quantity}
                </td>

                <td style="padding:10px;border-bottom:1px solid #eee;text-align:right;">
                    ₹{price:.2f}
                </td>

                <td style="padding:10px;border-bottom:1px solid #eee;text-align:right;">
                    ₹{subtotal:.2f}
                </td>
            </tr>
            """

        # ----------------------------------------------------
        # Email HTML
        # ----------------------------------------------------

        html = f"""
        <!DOCTYPE html>

        <html>

        <body style="
            margin:0;
            padding:0;
            background:#f7f3fb;
            font-family:Arial,sans-serif;
            color:#333;
        ">

            <div style="
                max-width:700px;
                margin:30px auto;
                background:white;
                border-radius:12px;
                overflow:hidden;
                box-shadow:0 2px 10px rgba(0,0,0,0.08);
            ">

                <div style="
                    background:#b79ad8;
                    padding:25px;
                    text-align:center;
                    color:white;
                ">

                    <h1 style="margin:0;">
                        🧶 New YarnTales Order
                    </h1>

                    <p style="margin:8px 0 0;">
                        A new order has been placed.
                    </p>

                </div>


                <div style="padding:25px;">

                    <h2>
                        Order Details
                    </h2>

                    <p>
                        <strong>Order ID:</strong>
                        {order_id}
                    </p>

                    <p>
                        <strong>Date:</strong>
                        {created_at}
                    </p>

                    <hr>


                    <h2>
                        Customer
                    </h2>

                    <p>
                        <strong>Name:</strong>
                        {customer_name}
                    </p>

                    <p>
                        <strong>Email:</strong>
                        {customer_email}
                    </p>

                    <hr>


                    <h2>
                        Items
                    </h2>

                    <table style="
                        width:100%;
                        border-collapse:collapse;
                    ">

                        <thead>

                            <tr style="
                                background:#f3edf9;
                            ">

                                <th style="
                                    padding:10px;
                                    text-align:left;
                                ">
                                    Product
                                </th>

                                <th style="
                                    padding:10px;
                                ">
                                    Qty
                                </th>

                                <th style="
                                    padding:10px;
                                    text-align:right;
                                ">
                                    Price
                                </th>

                                <th style="
                                    padding:10px;
                                    text-align:right;
                                ">
                                    Subtotal
                                </th>

                            </tr>

                        </thead>

                        <tbody>

                            {items_html}

                        </tbody>

                    </table>


                    <h2 style="
                        text-align:right;
                        margin-top:20px;
                    ">

                        Total:
                        ₹{total:.2f}

                    </h2>


                    <hr>


                    <h2>
                        Payment
                    </h2>

                    <p>
                        <strong>Method:</strong>
                        {payment_method}
                    </p>

                    <p>
                        <strong>Status:</strong>
                        {payment_status}
                    </p>

                    <p>
                        <strong>Payment Reference:</strong>
                        {payment_reference}
                    </p>


                    <hr>


                    <h2>
                        Shipping Address
                    </h2>

                    <p>
                        {shipping_address}
                    </p>

                </div>


                <div style="
                    padding:20px;
                    text-align:center;
                    background:#f3edf9;
                    color:#777;
                ">

                    <p style="margin:0;">
                        YarnTales 🧶
                    </p>

                    <p style="
                        margin:5px 0 0;
                        font-size:13px;
                    ">
                        Handmade with love.
                    </p>

                </div>

            </div>

        </body>

        </html>
        """

        # ----------------------------------------------------
        # Send using Resend API
        # ----------------------------------------------------

        params = {
            "from": RESEND_FROM_EMAIL,
            "to": [ADMIN_EMAIL],
            "subject": (
                f"🧶 New YarnTales Order - {order_id}"
            ),
            "html": html
        }

        email = resend.Emails.send(
            params
        )

        print(
            "Order email sent successfully:",
            email
        )

        return True

    except Exception as e:

        # IMPORTANT:
        # Email failure must NEVER make the order fail.

        print(
            "Order email failed:",
            str(e)
        )

        return False


# ============================================================
# RAZORPAY: CREATE PAYMENT ORDER
# ============================================================

@order_bp.route(
    "/api/payment/create",
    methods=["POST"]
)
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

        amount = data.get(
            "amount"
        )

        if amount is None:

            return jsonify({
                "error": "Amount is required"
            }), 400

        try:

            amount = float(
                amount
            )

        except (TypeError, ValueError):

            return jsonify({
                "error": "Invalid amount"
            }), 400

        if amount <= 0:

            return jsonify({
                "error": "Amount must be greater than zero"
            }), 400

        amount_in_paise = int(
            round(
                amount * 100
            )
        )

        payment_data = {

            "amount": amount_in_paise,

            "currency": "INR",

            "receipt": str(
                uuid.uuid4()
            )[:40]
        }

        razorpay_order = (
            razorpay_client.order.create(
                data=payment_data
            )
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

            "error":
                "Failed to create payment order",

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
                "error":
                    "Missing Razorpay payment details"
            }), 400

        verification_data = {

            "razorpay_order_id":
                razorpay_order_id,

            "razorpay_payment_id":
                razorpay_payment_id,

            "razorpay_signature":
                razorpay_signature
        }

        razorpay_client.utility.verify_payment_signature(
            verification_data
        )

        return jsonify({

            "success": True,

            "message":
                "Payment verified successfully"

        }), 200

    except Exception as e:

        print(
            "Razorpay verification error:",
            str(e)
        )

        return jsonify({

            "success": False,

            "error":
                "Payment verification failed",

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

        mongo_user_id = user.get(
            "_id"
        )

        if not mongo_user_id:

            return jsonify({
                "error":
                    "User MongoDB ID not found"
            }), 400

        # ----------------------------------------------------
        # SHIPPING
        # ----------------------------------------------------

        shipping_address = data.get(
            "shippingAddress"
        )

        if not shipping_address:

            return jsonify({
                "error":
                    "Shipping address is required"
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
                "error":
                    "Order must contain at least one item"
            }), 400

        calculated_items, total = (
            calculate_order_items(
                items
            )
        )

        if not calculated_items:

            return jsonify({
                "error":
                    "No valid products found in order"
            }), 400

        if total <= 0:

            return jsonify({
                "error":
                    "Order total must be greater than zero"
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

        if payment_status != "paid":

            payment_status = "pending"

        # ----------------------------------------------------
        # ORDER
        # ----------------------------------------------------

        order_id = str(
            uuid.uuid4()
        )

        order = {

            "orderId":
                order_id,

            "userId":
                mongo_user_id,

            "items":
                calculated_items,

            "total":
                total,

            "status":
                "order_confirmed",

            "createdAt":
                datetime.utcnow(),

            "paymentMethod":
                payment_method,

            "paymentStatus":
                payment_status,

            "paymentReference":
                payment_reference,

            "shippingAddress":
                shipping_address,

            "customerName":
                user.get(
                    "name",
                    user.get(
                        "fullName",
                        ""
                    )
                ),

            "customerEmail":
                user.get(
                    "email",
                    ""
                )
        }

        # ----------------------------------------------------
        # SAVE ORDER FIRST
        # ----------------------------------------------------

        db.orders.insert_one(
            order
        )

        # ----------------------------------------------------
        # SEND OWNER EMAIL
        #
        # Email failure is caught internally and will NOT
        # cause checkout to fail.
        # ----------------------------------------------------

        send_new_order_email(
            order,
            user
        )

        # ----------------------------------------------------
        # RETURN ORDER
        # ----------------------------------------------------

        order = convert_object_ids(
            order
        )

        return jsonify({

            "message":
                "Order created successfully",

            "order":
                order

        }), 201

    except Exception as e:

        print(
            "Create order error:",
            str(e)
        )

        return jsonify({

            "error":
                "Failed to create order",

            "details":
                str(e)

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

        user = find_user(
            user_id
        )

        if not user:

            return jsonify({
                "error":
                    "User not found"
            }), 404

        mongo_user_id = user.get(
            "_id"
        )

        if not mongo_user_id:

            return jsonify({
                "error":
                    "User MongoDB ID not found"
            }), 400

        orders = list(
            db.orders.find({
                "userId":
                    mongo_user_id
            }).sort(
                "createdAt",
                -1
            )
        )

        orders = convert_object_ids(
            orders
        )

        return jsonify({
            "orders":
                orders
        }), 200

    except Exception as e:

        print(
            "Get user orders error:",
            str(e)
        )

        return jsonify({

            "error":
                "Failed to fetch orders",

            "details":
                str(e)

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
            "orderId":
                str(order_id)
        })

        if not order:

            try:

                if ObjectId.is_valid(
                    str(order_id)
                ):

                    order = db.orders.find_one({
                        "_id":
                            ObjectId(
                                str(order_id)
                            )
                    })

            except Exception:
                pass

        if not order:

            return jsonify({
                "error":
                    "Order not found"
            }), 404

        order = convert_object_ids(
            order
        )

        return jsonify({
            "order":
                order
        }), 200

    except Exception as e:

        print(
            "Get order error:",
            str(e)
        )

        return jsonify({

            "error":
                "Failed to fetch order",

            "details":
                str(e)

        }), 500