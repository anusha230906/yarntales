from flask import Blueprint, jsonify, request
from config import db
from datetime import datetime, timezone

tracking_bp = Blueprint("tracking", __name__)


# -------------------------------------------------
# ORDER TRACKING STATUS FLOW
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
# GET ORDER TRACKING
# -------------------------------------------------

@tracking_bp.route("/api/orders/<order_id>/tracking", methods=["GET"])
def get_order_tracking(order_id):

    order = db.orders.find_one({
        "orderId": order_id
    })

    if not order:
        return jsonify({
            "message": "Order not found"
        }), 404

    current_status = order.get(
        "status",
        "order_confirmed"
    )

    tracking = []

    current_index = (
        TRACKING_STAGES.index(current_status)
        if current_status in TRACKING_STAGES
        else 0
    )

    for index, stage in enumerate(TRACKING_STAGES):

        tracking.append({
            "status": stage,
            "completed": index <= current_index,
            "current": index == current_index
        })

    return jsonify({
        "orderId": order_id,
        "currentStatus": current_status,
        "tracking": tracking
    }), 200


# -------------------------------------------------
# UPDATE ORDER TRACKING STATUS
# -------------------------------------------------

@tracking_bp.route(
    "/api/orders/<order_id>/tracking",
    methods=["PUT"]
)
def update_order_tracking(order_id):

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
        "message": "Order tracking status updated",
        "orderId": order_id,
        "status": new_status
    }), 200