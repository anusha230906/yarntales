from flask import Blueprint, jsonify
from config import db
from bson import ObjectId

product_bp = Blueprint("product", __name__)


def convert_object_ids(data):
    if isinstance(data, ObjectId):
        return str(data)
    if isinstance(data, list):
        return [convert_object_ids(item) for item in data]
    if isinstance(data, dict):
        return {key: convert_object_ids(value) for key, value in data.items()}
    return data


@product_bp.route("/api/products", methods=["GET"])
def get_products():
    products = list(
        db.products.find({
            "isActive": True,
            "$or": [
                {"catalogVisible": True},
                {"catalogVisible": {"$exists": False}},
            ],
        })
    )
    return jsonify({
        "products": convert_object_ids(products)
    }), 200


@product_bp.route("/api/products/<product_id>", methods=["GET"])
def get_product(product_id):
    try:
        object_id = ObjectId(product_id)
    except Exception:
        return jsonify({"message": "Invalid product ID"}), 400

    product = db.products.find_one({
        "_id": object_id,
        "isActive": True,
        "$or": [
            {"catalogVisible": True},
            {"catalogVisible": {"$exists": False}},
        ],
    })

    if not product:
        return jsonify({"message": "Product not found"}), 404

    return jsonify({
        "product": convert_object_ids(product)
    }), 200
