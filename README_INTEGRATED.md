# YarnTales — Frontend + Backend Integrated

This version connects the React/Vite frontend to the Flask + MongoDB backend.

## 1. Backend

Open a terminal in `backend`:

```powershell
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt
```

Create `backend/.env` from `.env.example` and put your own MongoDB URI and secret in it.

Seed the products once:

```powershell
python seed.py
```

Start Flask:

```powershell
python app.py
```

Backend runs at `http://localhost:5000`.

## 2. Frontend

Open another terminal in `field project/yarntales`:

```powershell
npm install
npm run dev
```

The included `.env` points the frontend to `http://localhost:5000` and enables backend mode.

## What is connected

- Register / login using Flask + JWT
- Products loaded from MongoDB
- Wishlist stored in MongoDB
- Cart stored in MongoDB
- Checkout creates a real order in MongoDB
- Cart is cleared after a successful order
- Order tracking reads the backend tracking endpoint
- Profile shows the number of orders from MongoDB
- CORS is enabled in Flask

The UI styling and local product photos are preserved. Product records are normalized so the frontend can display the existing YarnTales design while using MongoDB product IDs for cart, wishlist and orders.

## Important

Do not commit or share `backend/.env`. Use your own MongoDB credentials.
