# YarnTales Integrated Project — Setup

## Architecture

React + Vite frontend → Flask REST API → MongoDB Atlas.

The frontend UI/design files were kept as provided. Integration changes are primarily in API/state/data handling.

## Backend setup

From the `backend` folder:

```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `backend\.env`:

```env
MONGO_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
MONGO_DB_NAME=yarntales
SECRET_KEY=<long-random-secret>
```

Run the final catalog seed:

```bat
python seed.py
```

`seed.py`:
- checks the MongoDB connection with `ping`
- ensures the required YarnTales collections exist
- upserts the 21 storefront products from the React catalog
- creates/updates categories
- creates a hidden custom-builder base product at ₹1,999
- keeps legacy/test product documents but marks them inactive and not storefront-visible
- creates useful indexes

Start Flask:

```bat
python app.py
```

Health check:

```bat
curl.exe http://127.0.0.1:5000/api/health
```

Expected:

```json
{
  "message": "YarnTales backend and MongoDB are connected",
  "status": "success"
}
```

## Frontend setup

From the `frontend` folder:

```bat
npm install
copy .env.example .env
```

`frontend\.env`:

```env
VITE_USE_BACKEND=true
VITE_API_BASE_URL=http://localhost:5000
```

Start Vite:

```bat
npm run dev
```

## MongoDB Atlas

1. In MongoDB Atlas, ensure a database user exists.
2. Ensure the current development machine IP is allowed in Network Access.
3. Copy the Atlas connection string and place it in `backend\.env` as `MONGO_URI`.
4. Set `MONGO_DB_NAME=yarntales`.
5. Run `python seed.py`.
6. Confirm `python app.py` starts.
7. Confirm `/api/health` returns a successful MongoDB connection.

## Data flow

Authentication:
- React calls `/api/register` and `/api/login`.
- Flask stores users in `users` with hashed passwords.
- Flask returns a JWT.
- The frontend stores the JWT in `localStorage` under `yarntales-token`.

Products:
- React loads `/api/products` from MongoDB rather than using the hard-coded catalog as the runtime source.
- Product `_id` values are used as the frontend `id`.
- Images are resolved against the existing Vite `src/assets` files, so the visual product images/design remain unchanged.

Cart / Wishlist / Orders:
- React loads these from Flask after login.
- Add/update/remove operations are sent to Flask.
- Checkout creates a real order in MongoDB.
- The cart is cleared only after the order is successfully created.

Customization:
- The custom builder loads a hidden `custom-builder-base` product.
- The selected customization is saved to `customizations` and attached to the cart item.

Gift Mode:
- Recommendations come from the MongoDB product catalog.
- The Gift Mode request is persisted when the user continues to the shop from the gift flow.

Tracking:
- The tracking page loads the latest order's tracking data from Flask.
- All seven YarnTales status stages are supported.

## Git safety

Do not commit:
- `backend/.env`
- `frontend/.env`
- `backend/venv/`
- `frontend/node_modules/`
- `frontend/dist/`

The integrated package intentionally includes only `.env.example` files, not real credentials.

## Simulated UPI payment

The checkout keeps the existing UPI / Card / Cash on Delivery choices and visual design. Selecting UPI opens a simulated UPI payment dialog with a demo QR-style panel. Clicking `Simulate Payment` creates the YarnTales order and stores `paymentMethod: "UPI"`, `paymentStatus: "paid"`, and a `SIM-UPI-*` payment reference in MongoDB. No real payment provider or money movement is used.

Card is also treated as a simulated paid method for the project, while Cash on Delivery is stored as `pending`.
