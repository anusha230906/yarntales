from flask import Blueprint, request, jsonify
from config import db
from bson import ObjectId
from uuid import uuid4
from datetime import datetime, timezone

feed_bp = Blueprint("feed", __name__)


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
# CREATE FEED POST
# -------------------------------------------------

@feed_bp.route("/api/feed", methods=["POST"])
def create_feed_post():

    data = request.get_json()

    if not data:
        return jsonify({
            "message": "Request body is required"
        }), 400

    image = data.get("image")
    caption = data.get("caption")
    product_id = data.get("productId")
    instagram_url = data.get("instagramUrl")

    if not image:
        return jsonify({
            "message": "image is required"
        }), 400

    if not caption:
        return jsonify({
            "message": "caption is required"
        }), 400

    # Check product if provided
    if product_id:

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

    else:
        product_object_id = None

    feed_post = {
        "feedId": str(uuid4()),
        "image": image,
        "caption": caption,
        "productId": product_object_id,
        "instagramUrl": instagram_url,
        "createdAt": datetime.now(timezone.utc)
    }

    db.feed.insert_one(feed_post)

    feed_post = convert_object_ids(feed_post)

    return jsonify({
        "message": "Feed post created successfully",
        "feedPost": feed_post
    }), 201


# -------------------------------------------------
# GET ALL FEED POSTS
# -------------------------------------------------

@feed_bp.route("/api/feed", methods=["GET"])
def get_feed():

    feed_posts = list(
        db.feed.find({}).sort("createdAt", -1)
    )

    feed_posts = convert_object_ids(feed_posts)

    return jsonify({
        "feed": feed_posts
    }), 200


# -------------------------------------------------
# GET SINGLE FEED POST
# -------------------------------------------------

@feed_bp.route("/api/feed/<feed_id>", methods=["GET"])
def get_feed_post(feed_id):

    feed_post = db.feed.find_one({
        "feedId": feed_id
    })

    if not feed_post:
        return jsonify({
            "message": "Feed post not found"
        }), 404

    feed_post = convert_object_ids(feed_post)

    return jsonify({
        "feedPost": feed_post
    }), 200


# -------------------------------------------------
# DELETE FEED POST
# -------------------------------------------------

@feed_bp.route("/api/feed/<feed_id>", methods=["DELETE"])
def delete_feed_post(feed_id):

    result = db.feed.delete_one({
        "feedId": feed_id
    })

    if result.deleted_count == 0:
        return jsonify({
            "message": "Feed post not found"
        }), 404

    return jsonify({
        "message": "Feed post deleted successfully"
    }), 200