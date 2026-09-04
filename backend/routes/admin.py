from flask import Blueprint, request, jsonify
from config import db, SECRET_KEY
from bson import ObjectId
from datetime import datetime, timezone
import jwt

admin_bp = Blueprint("admin", __name__)


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
# ADMIN AUTHENTICATION HELPER
# -------------------------------------------------

def get_admin_from_token():

    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return None, "Authorization token is required"

    parts = auth_header.split(" ")

    if len(parts) != 2 or parts[0] != "Bearer":
        return None, "Authorization format must be Bearer <token>"

    token = parts[1]

    try:
        decoded = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256"]
        )

    except jwt.ExpiredSignatureError:
        return None, "Token has expired"

    except jwt.InvalidTokenError:
        return None, "Invalid token"

    if decoded.get("role") != "admin":
        return None, "Admin access required"

    user = db.users.find_one({
        "userId": decoded.get("userId")
    })

    if not user:
        return None, "Admin user not found"

    return user, None


# -------------------------------------------------
# TRACKING STATUSES
# -------------------------------------------------

TRACKING_STAGES = [
    "order_confirmed",
    "materials_sourced",
    "handcrafting_in_progress",
    "quality_check",
    "packed",
    "dispatched",
    "delivered"
]


# -------------------------------------------------
# ADMIN DASHBOARD
# -------------------------------------------------

@admin_bp.route("/api/admin/dashboard", methods=["GET"])
def admin_dashboard():

    admin, error = get_admin_from_token()

    if error:
        return jsonify({
            "message": error
        }), 403

    return jsonify({
        "message": "Admin access granted",
        "admin": {
            "userId": admin["userId"],
            "name": admin["name"],
            "email": admin["email"],
            "role": admin.get("role")
        }
    }), 200


# -------------------------------------------------
# ADMIN - VIEW ALL PRODUCTS
# -------------------------------------------------

@admin_bp.route("/api/admin/products", methods=["GET"])
def admin_get_products():

    admin, error = get_admin_from_token()

    if error:
        return jsonify({
            "message": error
        }), 403

    products = list(
        db.products.find({})
    )

    products = convert_object_ids(products)

    return jsonify({
        "products": products
    }), 200


# -------------------------------------------------
# ADMIN - CREATE PRODUCT
# -------------------------------------------------

@admin_bp.route("/api/admin/products", methods=["POST"])
def admin_create_product():

    admin, error = get_admin_from_token()

    if error:
        return jsonify({
            "message": error
        }), 403

    data = request.get_json()

    if not data:
        return jsonify({
            "message": "Request body is required"
        }), 400

    name = data.get("name")
    description = data.get("description", "")
    category_id = data.get("categoryId")
    base_price = data.get("basePrice")
    available_colors = data.get("availableColors", [])
    available_sizes = data.get("availableSizes", [])
    customizable_features = data.get("customizableFeatures", [])
    images = data.get("images", [])

    if not name:
        return jsonify({
            "message": "name is required"
        }), 400

    if not category_id:
        return jsonify({
            "message": "categoryId is required"
        }), 400

    if base_price is None:
        return jsonify({
            "message": "basePrice is required"
        }), 400

    try:
        base_price = float(base_price)
    except (ValueError, TypeError):
        return jsonify({
            "message": "basePrice must be a number"
        }), 400

    if base_price <= 0:
        return jsonify({
            "message": "basePrice must be greater than 0"
        }), 400

    try:
        category_object_id = ObjectId(category_id)
    except Exception:
        return jsonify({
            "message": "Invalid categoryId"
        }), 400

    category = db.categories.find_one({
        "_id": category_object_id
    })

    if not category:
        return jsonify({
            "message": "Category not found"
        }), 404

    now = datetime.now(timezone.utc)

    product = {
        "name": name.strip(),
        "description": description,
        "categoryId": category_object_id,
        "basePrice": base_price,
        "availableColors": available_colors,
        "availableSizes": available_sizes,
        "customizableFeatures": customizable_features,
        "images": images,
        "isActive": True,
        "createdBy": admin["_id"],
        "createdAt": now,
        "updatedAt": now
    }

    result = db.products.insert_one(product)

    product["_id"] = result.inserted_id

    product = convert_object_ids(product)

    return jsonify({
        "message": "Product created successfully",
        "product": product
    }), 201


# -------------------------------------------------
# ADMIN - UPDATE PRODUCT
# -------------------------------------------------

@admin_bp.route("/api/admin/products/<product_id>", methods=["PUT"])
def admin_update_product(product_id):

    admin, error = get_admin_from_token()

    if error:
        return jsonify({
            "message": error
        }), 403

    try:
        product_object_id = ObjectId(product_id)
    except Exception:
        return jsonify({
            "message": "Invalid product ID"
        }), 400

    product = db.products.find_one({
        "_id": product_object_id
    })

    if not product:
        return jsonify({
            "message": "Product not found"
        }), 404

    data = request.get_json()

    if not data:
        return jsonify({
            "message": "Request body is required"
        }), 400

    update_fields = {}

    if "name" in data:

        name = data.get("name")

        if not name or not str(name).strip():
            return jsonify({
                "message": "name cannot be empty"
            }), 400

        update_fields["name"] = str(name).strip()

    if "description" in data:
        update_fields["description"] = data.get("description", "")

    if "categoryId" in data:

        category_id = data.get("categoryId")

        try:
            category_object_id = ObjectId(category_id)
        except Exception:
            return jsonify({
                "message": "Invalid categoryId"
            }), 400

        category = db.categories.find_one({
            "_id": category_object_id
        })

        if not category:
            return jsonify({
                "message": "Category not found"
            }), 404

        update_fields["categoryId"] = category_object_id

    if "basePrice" in data:

        try:
            base_price = float(data.get("basePrice"))
        except (ValueError, TypeError):
            return jsonify({
                "message": "basePrice must be a number"
            }), 400

        if base_price <= 0:
            return jsonify({
                "message": "basePrice must be greater than 0"
            }), 400

        update_fields["basePrice"] = base_price

    if "availableColors" in data:

        if not isinstance(data["availableColors"], list):
            return jsonify({
                "message": "availableColors must be an array"
            }), 400

        update_fields["availableColors"] = data["availableColors"]

    if "availableSizes" in data:

        if not isinstance(data["availableSizes"], list):
            return jsonify({
                "message": "availableSizes must be an array"
            }), 400

        update_fields["availableSizes"] = data["availableSizes"]

    if "customizableFeatures" in data:

        if not isinstance(data["customizableFeatures"], list):
            return jsonify({
                "message": "customizableFeatures must be an array"
            }), 400

        update_fields["customizableFeatures"] = data[
            "customizableFeatures"
        ]

    if "images" in data:

        if not isinstance(data["images"], list):
            return jsonify({
                "message": "images must be an array"
            }), 400

        update_fields["images"] = data["images"]

    if "isActive" in data:

        if not isinstance(data["isActive"], bool):
            return jsonify({
                "message": "isActive must be true or false"
            }), 400

        update_fields["isActive"] = data["isActive"]

    if not update_fields:
        return jsonify({
            "message": "No fields provided for update"
        }), 400

    update_fields["updatedAt"] = datetime.now(timezone.utc)

    db.products.update_one(
        {
            "_id": product_object_id
        },
        {
            "$set": update_fields
        }
    )

    updated_product = db.products.find_one({
        "_id": product_object_id
    })

    updated_product = convert_object_ids(updated_product)

    return jsonify({
        "message": "Product updated successfully",
        "product": updated_product
    }), 200


# -------------------------------------------------
# ADMIN - DEACTIVATE PRODUCT
# -------------------------------------------------

@admin_bp.route("/api/admin/products/<product_id>", methods=["DELETE"])
def admin_delete_product(product_id):

    admin, error = get_admin_from_token()

    if error:
        return jsonify({
            "message": error
        }), 403

    try:
        product_object_id = ObjectId(product_id)
    except Exception:
        return jsonify({
            "message": "Invalid product ID"
        }), 400

    product = db.products.find_one({
        "_id": product_object_id
    })

    if not product:
        return jsonify({
            "message": "Product not found"
        }), 404

    if product.get("isActive") is False:
        return jsonify({
            "message": "Product is already inactive"
        }), 409

    db.products.update_one(
        {
            "_id": product_object_id
        },
        {
            "$set": {
                "isActive": False,
                "updatedAt": datetime.now(timezone.utc)
            }
        }
    )

    return jsonify({
        "message": "Product deactivated successfully",
        "productId": product_id,
        "isActive": False
    }), 200


# -------------------------------------------------
# ADMIN - VIEW ALL ORDERS
# -------------------------------------------------

@admin_bp.route("/api/admin/orders", methods=["GET"])
def admin_get_orders():

    admin, error = get_admin_from_token()

    if error:
        return jsonify({
            "message": error
        }), 403

    orders = list(
        db.orders.find({}).sort("createdAt", -1)
    )

    orders = convert_object_ids(orders)

    return jsonify({
        "orders": orders
    }), 200


# -------------------------------------------------
# ADMIN - UPDATE ORDER STATUS
# -------------------------------------------------

@admin_bp.route(
    "/api/admin/orders/<order_id>/status",
    methods=["PUT"]
)
def admin_update_order_status(order_id):

    admin, error = get_admin_from_token()

    if error:
        return jsonify({
            "message": error
        }), 403

    data = request.get_json()

    if not data:
        return jsonify({
            "message": "Request body is required"
        }), 400

    new_status = data.get("status")

    if not new_status:
        return jsonify({
            "message": "status is required"
        }), 400

    if new_status not in TRACKING_STAGES:
        return jsonify({
            "message": "Invalid tracking status",
            "allowedStatuses": TRACKING_STAGES
        }), 400

    order = db.orders.find_one({
        "orderId": order_id
    })

    if not order:
        return jsonify({
            "message": "Order not found"
        }), 404

    db.orders.update_one(
        {
            "orderId": order_id
        },
        {
            "$set": {
                "status": new_status,
                "updatedAt": datetime.now(timezone.utc)
            }
        }
    )

    return jsonify({
        "message": "Order status updated successfully",
        "orderId": order_id,
        "status": new_status
    }), 200

# -------------------------------------------------
# ADMIN - VIEW ALL USERS
# -------------------------------------------------

@admin_bp.route("/api/admin/users", methods=["GET"])
def admin_get_users():

    admin, error = get_admin_from_token()

    if error:
        return jsonify({
            "message": error
        }), 403

    users = list(
        db.users.find(
            {},
            {
                "password": 0
            }
        ).sort("createdAt", -1)
    )

    users = convert_object_ids(users)

    return jsonify({
        "users": users
    }), 200
