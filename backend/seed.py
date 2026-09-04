"""
YarnTales MongoDB seed script.

Seeds the final storefront catalog from the React/Vite product data,
creates/updates categories, and hides legacy products from the storefront
without deleting them (so historical order references remain valid).

Run from backend:
    python seed.py
"""

from datetime import datetime, timezone
from pathlib import Path
from pymongo import MongoClient
from dotenv import load_dotenv
from bson import ObjectId
import os

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "yarntales")

if not MONGO_URI:
    raise RuntimeError("MONGO_URI is missing. Create backend/.env from backend/.env.example.")

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
client.admin.command("ping")
db = client[MONGO_DB_NAME]

PRODUCTS = [
  {
    "id": 1,
    "name": "Macramé Bag",
    "category": "Bags",
    "price": 1200,
    "rating": 4.9,
    "reviews": 12,
    "image": "/src/assets/fringe-sunflower-sling.jpg",
    "gallery": [
      "/src/assets/fringe-sunflower-sling.jpg"
    ],
    "tone": "bags",
    "colors": [
      "Cream",
      "Blue",
      "Black",
      "Brown",
      "Yellow"
    ],
    "description": "A handmade crochet sling with a sunflower detail and long fringe."
  },
  {
    "id": 2,
    "name": "Sunflower Keychain",
    "category": "Keychains",
    "price": 100,
    "rating": 4.9,
    "reviews": 12,
    "image": "/src/assets/sunflower-keychain.jpg",
    "gallery": [
      "/src/assets/sunflower-keychain.jpg"
    ],
    "tone": "keychains",
    "colors": [
      "Yellow",
      "Lavender",
      "Black & White",
      "Cherry Red",
      "Green"
    ],
    "description": "A tiny sunflower charm for your keys, bag or pouch."
  },
  {
    "id": 3,
    "name": "Panda Keychain",
    "category": "Keychains",
    "price": 170,
    "rating": 4.9,
    "reviews": 12,
    "image": "/src/assets/panda-keychain.jpg",
    "gallery": [
      "/src/assets/panda-keychain.jpg"
    ],
    "tone": "keychains",
    "colors": [
      "Yellow",
      "Lavender",
      "Black & White",
      "Cherry Red",
      "Green"
    ],
    "description": "A tiny panda charm made for your everyday bag or keys."
  },
  {
    "id": 4,
    "name": "Tulip Keychain",
    "category": "Keychains",
    "price": 150,
    "rating": 4.9,
    "reviews": 12,
    "image": "/src/assets/lavender-flower-keychain.jpg",
    "gallery": [
      "/src/assets/lavender-flower-keychain.jpg"
    ],
    "tone": "keychains",
    "colors": [
      "Yellow",
      "Lavender",
      "Black & White",
      "Cherry Red",
      "Green"
    ],
    "description": "A little tulip charm in soft lavender yarn."
  },
  {
    "id": 5,
    "name": "Bee Keychain",
    "category": "Keychains",
    "price": 170,
    "rating": 4.9,
    "reviews": 12,
    "image": "/src/assets/bee-keychain.jpg",
    "gallery": [
      "/src/assets/bee-keychain.jpg"
    ],
    "tone": "keychains",
    "colors": [
      "Yellow",
      "Lavender",
      "Black & White",
      "Cherry Red",
      "Green"
    ],
    "description": "A tiny handmade bee with a sweet, round shape."
  },
  {
    "id": 6,
    "name": "Cherry Keychain",
    "category": "Keychains",
    "price": 150,
    "rating": 4.9,
    "reviews": 12,
    "image": "/src/assets/cherry-keychain.jpg",
    "gallery": [
      "/src/assets/cherry-keychain.jpg"
    ],
    "tone": "keychains",
    "colors": [
      "Yellow",
      "Lavender",
      "Black & White",
      "Cherry Red",
      "Green"
    ],
    "description": "A pair of crochet cherries with leafy green details."
  },
  {
    "id": 7,
    "name": "Blue Macramé Bag",
    "category": "Bags",
    "price": 1500,
    "rating": 4.9,
    "reviews": 12,
    "image": "/src/assets/navy-daisy-fringe-bag.jpg",
    "gallery": [
      "/src/assets/navy-daisy-fringe-bag.jpg"
    ],
    "tone": "bags",
    "colors": [
      "Cream",
      "Blue",
      "Black",
      "Brown",
      "Yellow"
    ],
    "description": "A deep blue crochet bag with a white flower and fringe."
  },
  {
    "id": 8,
    "name": "Daisy Keychain",
    "category": "Keychains",
    "price": 120,
    "rating": 4.9,
    "reviews": 12,
    "image": "/src/assets/navy-daisy-fringe-bag.jpg",
    "gallery": [
      "/src/assets/navy-daisy-fringe-bag.jpg"
    ],
    "tone": "keychains",
    "colors": [
      "Yellow",
      "Lavender",
      "Black & White",
      "Cherry Red",
      "Green"
    ],
    "description": "A small handmade daisy charm inspired by the YarnTales flower bags."
  },
  {
    "id": 9,
    "name": "Avocado Keychain",
    "category": "Keychains",
    "price": 170,
    "rating": 4.9,
    "reviews": 12,
    "image": "/src/assets/avocado-keychain.jpg",
    "gallery": [
      "/src/assets/avocado-keychain.jpg"
    ],
    "tone": "keychains",
    "colors": [
      "Yellow",
      "Lavender",
      "Black & White",
      "Cherry Red",
      "Green"
    ],
    "description": "A tiny avocado buddy to clip onto your bag or keys."
  },
  {
    "id": 10,
    "name": "Small Flower Bag",
    "category": "Bags",
    "price": 1000,
    "rating": 4.9,
    "reviews": 12,
    "image": "/src/assets/teddy-mini-bag.jpg",
    "gallery": [
      "/src/assets/teddy-mini-bag.jpg"
    ],
    "tone": "bags",
    "colors": [
      "Cream",
      "Blue",
      "Black",
      "Brown",
      "Yellow"
    ],
    "description": "A small everyday crochet bag with a cute flower-inspired shape."
  },
  {
    "id": 11,
    "name": "Bubble Bag",
    "category": "Bags",
    "price": 1000,
    "rating": 4.9,
    "reviews": 12,
    "image": "/src/assets/lavender-wave-tote.jpg",
    "gallery": [
      "/src/assets/lavender-wave-tote.jpg"
    ],
    "tone": "bags",
    "colors": [
      "Cream",
      "Blue",
      "Black",
      "Brown",
      "Yellow"
    ],
    "description": "A soft textured crochet bag made for easy everyday use."
  },
  {
    "id": 12,
    "name": "Shell Bag",
    "category": "Bags",
    "price": 1200,
    "rating": 4.9,
    "reviews": 12,
    "image": "/src/assets/cream-shell-bag.jpg",
    "gallery": [
      "/src/assets/cream-shell-bag.jpg"
    ],
    "tone": "bags",
    "colors": [
      "Cream",
      "Blue",
      "Black",
      "Brown",
      "Yellow"
    ],
    "description": "A simple cream shell-shaped crochet bag."
  },
  {
    "id": 13,
    "name": "Cute Bow Bag",
    "category": "Bags",
    "price": 1500,
    "rating": 4.9,
    "reviews": 12,
    "image": "/src/assets/black-yellow-bow-bag.jpg",
    "gallery": [
      "/src/assets/black-yellow-bow-bag.jpg"
    ],
    "tone": "bags",
    "colors": [
      "Cream",
      "Blue",
      "Black",
      "Brown",
      "Yellow"
    ],
    "description": "A black crochet bag finished with an oversized yellow bow."
  },
  {
    "id": 14,
    "name": "Pencil / Money Pouch",
    "category": "Pouches",
    "price": 400,
    "rating": 4.9,
    "reviews": 12,
    "image": "/src/assets/blue-brown-pouches.jpg",
    "gallery": [
      "/src/assets/blue-brown-pouches.jpg"
    ],
    "tone": "pouches",
    "colors": [
      "Blue",
      "Brown",
      "Yellow",
      "Cream"
    ],
    "description": "A small crochet pouch for pencils, coins or little everyday things."
  },
  {
    "id": 15,
    "name": "Bandana",
    "category": "Accessories",
    "price": 200,
    "rating": 4.9,
    "reviews": 12,
    "image": "/src/assets/tan-red-pouch.jpg",
    "gallery": [
      "/src/assets/tan-red-pouch.jpg"
    ],
    "tone": "accessories",
    "colors": [
      "Red",
      "Pink",
      "Lavender",
      "Green"
    ],
    "description": "A handmade crochet bandana with a playful contrast edge."
  },
  {
    "id": 16,
    "name": "Cute Bow Bag (Small)",
    "category": "Bags",
    "price": 1200,
    "rating": 4.9,
    "reviews": 12,
    "image": "/src/assets/yellow-bow-bag.jpg",
    "gallery": [
      "/src/assets/yellow-bow-bag.jpg"
    ],
    "tone": "bags",
    "colors": [
      "Cream",
      "Blue",
      "Black",
      "Brown",
      "Yellow"
    ],
    "description": "A smaller bow bag for when you want the same cute look in a tiny size."
  },
  {
    "id": 17,
    "name": "Tulip Headband",
    "category": "Accessories",
    "price": 300,
    "rating": 4.9,
    "reviews": 12,
    "image": "/src/assets/flower-bookmark.jpg",
    "gallery": [
      "/src/assets/flower-bookmark.jpg"
    ],
    "tone": "accessories",
    "colors": [
      "Red",
      "Pink",
      "Lavender",
      "Green"
    ],
    "description": "A handmade headband finished with little tulip flowers."
  },
  {
    "id": 18,
    "name": "Bottle Cover",
    "category": "Everyday",
    "price": 200,
    "rating": 4.9,
    "reviews": 12,
    "image": "/src/assets/bottle-sleeve.jpg",
    "gallery": [
      "/src/assets/bottle-sleeve.jpg"
    ],
    "tone": "everyday",
    "colors": [
      "Cream",
      "Pink"
    ],
    "description": "A crochet bottle cover with a bright ribbon tie."
  },
  {
    "id": 19,
    "name": "Card Pouch",
    "category": "Pouches",
    "price": 200,
    "rating": 4.9,
    "reviews": 12,
    "image": "/src/assets/golden-tie-pouch.jpg",
    "gallery": [
      "/src/assets/golden-tie-pouch.jpg"
    ],
    "tone": "pouches",
    "colors": [
      "Blue",
      "Brown",
      "Yellow",
      "Cream"
    ],
    "description": "A small crochet pouch for cards, notes or tiny keepsakes."
  },
  {
    "id": 20,
    "name": "Cute Muffler",
    "category": "Wearables",
    "price": 1500,
    "rating": 4.9,
    "reviews": 12,
    "image": "/src/assets/black-flower-scarf.jpg",
    "gallery": [
      "/src/assets/black-flower-scarf.jpg"
    ],
    "tone": "wearables",
    "colors": [
      "Black",
      "Cream",
      "Brown"
    ],
    "description": "A cozy black-and-cream crochet muffler with flowers and tassels."
  },
  {
    "id": 21,
    "name": "BTS Bag",
    "category": "Bags",
    "price": 1200,
    "rating": 4.9,
    "reviews": 12,
    "image": "/src/assets/brown-yellow-bow-bag-clean.jpg",
    "gallery": [
      "/src/assets/brown-yellow-bow-bag-clean.jpg"
    ],
    "tone": "bags",
    "colors": [
      "Cream",
      "Blue",
      "Black",
      "Brown",
      "Yellow"
    ],
    "description": "A playful black crochet bag made for BTS fans."
  }
]
CATEGORIES = [
  {
    "title": "Bags",
    "text": "Macramé, bow & everyday bags",
    "tone": "lavender",
    "icon": "⌁"
  },
  {
    "title": "Keychains",
    "text": "Tiny handmade charms",
    "tone": "pink",
    "icon": "♡"
  },
  {
    "title": "Pouches",
    "text": "Small things, nicely kept",
    "tone": "yellow",
    "icon": "□"
  },
  {
    "title": "Accessories",
    "text": "Little wearable details",
    "tone": "mint",
    "icon": "✦"
  },
  {
    "title": "Everyday",
    "text": "Useful, cute & handmade",
    "tone": "blue",
    "icon": "✧"
  },
  {
    "title": "Wearables",
    "text": "Cozy pieces to wear",
    "tone": "peach",
    "icon": "♡"
  },
  {
    "title": "Custom",
    "text": "Make one your way",
    "tone": "pink",
    "icon": "✦"
  }
]

def main():
    now = datetime.now(timezone.utc)

    # Ensure the collections required by the YarnTales plan exist.
    required_collections = [
        "users",
        "products",
        "categories",
        "customizations",
        "orders",
        "order_items",
        "wishlists",
        "carts",
        "gift_mode",
        "feed",
    ]
    existing = set(db.list_collection_names())
    for name in required_collections:
        if name not in existing:
            db.create_collection(name)

    # Seed categories using stable human-readable names.
    category_ids = {}
    for category in CATEGORIES:
        doc = db.categories.find_one({"name": category["title"]})
        if doc:
            category_ids[category["title"]] = doc["_id"]
        else:
            category_id = ObjectId()
            db.categories.insert_one({
                "_id": category_id,
                "name": category["title"],
                "description": category["text"],
                "tone": category["tone"],
                "icon": category["icon"],
                "createdAt": now,
                "updatedAt": now,
            })
            category_ids[category["title"]] = category_id

    # Ensure the hidden custom-builder base exists. It is used by the
    # Custom Corner without appearing in the normal storefront catalog.
    if "Custom" not in category_ids:
        category_id = ObjectId()
        db.categories.insert_one({
            "_id": category_id,
            "name": "Custom",
            "description": "Make one your way",
            "tone": "pink",
            "icon": "✦",
            "createdAt": now,
            "updatedAt": now,
        })
        category_ids["Custom"] = category_id

    custom_base = {
        "seedKey": "custom-builder-base",
        "name": "Custom Crochet Piece",
        "category": "Custom",
        "categoryId": category_ids["Custom"],
        "description": "A custom YarnTales piece built from your selected shape, colour and detail.",
        "basePrice": 1999.0,
        "availableColors": ["Lavender", "Blush Pink", "Butter Yellow", "Mint", "Baby Blue", "Cream"],
        "availableSizes": ["Standard"],
        "customizableFeatures": [
            {"name": "Detail", "options": ["Bow", "Flower", "Heart", "Name tag"]},
        ],
        "images": ["/src/assets/lavender-wave-tote.jpg"],
        "rating": 5.0,
        "reviews": 0,
        "tone": "custom",
        "catalogVisible": False,
        "isActive": True,
        "updatedAt": now,
    }
    existing_custom = db.products.find_one({"seedKey": custom_base["seedKey"]})
    if existing_custom:
        db.products.update_one({"_id": existing_custom["_id"]}, {"$set": custom_base})
    else:
        custom_base["createdAt"] = now
        db.products.insert_one(custom_base)

    # Upsert the final 21 storefront products.
    final_names = set()
    seeded_ids = []
    for source in PRODUCTS:
        final_names.add(source["name"])
        category_id = category_ids[source["category"]]

        customizable_features = []
        if source["category"] in {"Bags", "Pouches"}:
            customizable_features = [
                {"name": "Color", "options": source["colors"]},
            ]

        product = {
            "seedKey": f"frontend-product-{source['id']}",
            "name": source["name"],
            "category": source["category"],
            "categoryId": category_id,
            "description": source["description"],
            "basePrice": float(source["price"]),
            "availableColors": source["colors"],
            "availableSizes": ["Standard"],
            "customizableFeatures": customizable_features,
            "images": source["gallery"],
            "rating": float(source["rating"]),
            "reviews": int(source["reviews"]),
            "tone": source["tone"],
            "catalogVisible": True,
            "isActive": True,
            "updatedAt": now,
        }

        existing = db.products.find_one({"seedKey": product["seedKey"]})
        if existing:
            db.products.update_one(
                {"_id": existing["_id"]},
                {"$set": product, "$setOnInsert": {"createdAt": now}},
            )
            seeded_ids.append(existing["_id"])
        else:
            product["createdAt"] = now
            result = db.products.insert_one(product)
            seeded_ids.append(result.inserted_id)

    # Keep legacy/test products in MongoDB for referential integrity, but
    # remove them from the customer storefront.
    db.products.update_many(
        {
            "seedKey": {"$nin": [f"frontend-product-{p['id']}" for p in PRODUCTS] + ["custom-builder-base"]},
        },
        {"$set": {"catalogVisible": False, "isActive": False, "updatedAt": now}},
    )

    # Useful indexes.
    db.users.create_index("email", unique=True)
    db.products.create_index([("isActive", 1), ("catalogVisible", 1)])
    db.products.create_index("seedKey", unique=True, sparse=True)
    db.categories.create_index("name", unique=True)
    db.orders.create_index([("userId", 1), ("createdAt", -1)])
    db.carts.create_index([("userId", 1)])
    db.wishlists.create_index([("userId", 1)])

    print("MongoDB ping: OK")
    print(f"Database: {db.name}")
    print(f"Final storefront products seeded: {len(seeded_ids)}")
    print("Legacy products were retained but hidden/deactivated from the storefront.")
    print("Collections:", ", ".join(sorted(db.list_collection_names())))

if __name__ == "__main__":
    main()
