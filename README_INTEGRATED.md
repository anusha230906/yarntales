# YarnTales 🧶 — Personalized Crochet E-commerce Platform

YarnTales is a dedicated e-commerce platform for handmade crochet products. It replaces free-text "customize in a DM" buying with a guided, visual **Custom Crochet Builder**, adds an occasion-and-budget-aware **Gift Mode**, and gives buyers real **production-stage order tracking** — problems that generic marketplaces like Etsy and gifting sites like FlowerAura don't solve together.

## ✨ Features

- **User Registration & Login** — secure authentication with buyer/admin role-based access
- **Product Listing & Details** — crochet items catalogued by category (amigurumi, home decor, accessories, etc.)
- **Custom Crochet Builder** — interactive configurator for yarn color, size, character features, accessories, and name text personalization, with real-time preview
- **Gift Mode** — buyers enter an occasion and budget and get curated product recommendations, plus gift wrapping and message card options
- **Shop the Feed** — a scrollable, social-media-style visual product discovery feed
- **Wishlist** — save, view, and remove favorite products
- **Order Tracking** — 7-stage production tracking: `Order Confirmed → Materials Sourced → Handcrafting in Progress → Quality Check → Packed → Dispatched → Delivered`
- **Inquiry Option** — structured pre-order inquiry form on each product page (message submission to the artisan is planned for a future release)
- **Admin Panel** — manage products, orders, and users from a dedicated backend interface
- **Payment Gateway** — live Razorpay integration (order creation, signature verification, webhook-based payment confirmation)

## 🛠️ Tech Stack

| Layer      | Technology        |
|------------|--------------------|
| Frontend   | React 19.1         |
| Styling    | HTML5 / CSS3       |
| Backend    | Python 3.10+, Flask 3.1.3 |
| Database   | MongoDB v6.0+ (Atlas) |
| Payments   | Razorpay           |
| Design     | Figma              |

## 🏗️ Architecture

The system is organized into seven modules: User Management, Product Management, Custom Crochet Builder, Gift Recommendation, Wishlist, Order Management, and Admin. Core data entities are `User`, `Product`, `Order`, `Order_Item`, `Customization`, `Wishlist`, and `Category`; Gift Mode requests (occasion, budget, wrapping, message card, scheduled delivery) are stored separately in a `gift_mode` collection rather than as fields on `Order`.

Full ER diagrams, data flow diagrams (Level 0–2), a use case diagram, and an activity diagram are documented in the project report.

## 🚀 Getting Started

### Prerequisites

- Node.js and npm
- Python 3.10+
- MongoDB (local instance or Atlas connection string)
- Razorpay API keys (test mode is fine for development)


> Adjust the folder names/commands above if your repo layout differs — update this section to match your actual `backend/` and `frontend/` directories once the structure is finalized.

## 📦 Project Scope

**Included in current prototype:** registration/login, product catalog, Custom Crochet Builder, Gift Mode, Shop the Feed, wishlist, order tracking, inquiry form, admin panel, Razorpay payments.

**Explicitly out of scope (future work):** native mobile app, AI-based recommendation engine, international shipping, live chat, and advanced analytics dashboards.

## 👥 Contributors

- Sharvi Kamerkar
- Anusha Manjrekar
- Shubham Nirmal
- Janvi Pandey

### Academic Context

Field Project — TY.B.Sc.IT, Department of Information Technology, Sathaye College (Autonomous), University of Mumbai — Academic Year 2026–2027

## 📄 License

