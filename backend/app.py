from flask import Flask, jsonify
from flask_cors import CORS

from config import SECRET_KEY
from routes.auth import auth_bp
from routes.product import product_bp
from routes.customization import customization_bp
from routes.wishlist import wishlist_bp
from routes.cart import cart_bp
from routes.order import order_bp
from routes.tracking import tracking_bp
from routes.gift import gift_bp
from routes.feed import feed_bp
from routes.admin import admin_bp


app = Flask(__name__)

app.config["SECRET_KEY"] = SECRET_KEY

CORS(app)

# Register authentication routes
app.register_blueprint(auth_bp)

# Register product routes
app.register_blueprint(product_bp)

# Register customization routes
app.register_blueprint(customization_bp)

# Register wishlist routes
app.register_blueprint(wishlist_bp)

# Register cart routes
app.register_blueprint(cart_bp)

# Register order routes
app.register_blueprint(order_bp)

# Register tracking routes
app.register_blueprint(tracking_bp)

# Register gift routes
app.register_blueprint(gift_bp)

# Register feed routes
app.register_blueprint(feed_bp)

# Register admin routes
app.register_blueprint(admin_bp)


@app.route("/")
def home():
    return jsonify({
        "message": "Welcome to YarnTales API",
        "status": "Backend is running"
    })


@app.route("/api/health")
def health():
    from config import client

    try:
        client.admin.command("ping")

        return jsonify({
            "status": "success",
            "message": "YarnTales backend and MongoDB are connected"
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "MongoDB connection failed",
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)