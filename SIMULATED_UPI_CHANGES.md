# YarnTales — Simulated UPI Changes

This update keeps the existing React/Vite checkout UI and styling intact while adding a simulated UPI confirmation step.

## Files changed

### `frontend/src/App.jsx`
- Updated `handlePlaceOrder` to keep payment fields separate from `shippingAddress`.
- Sends `paymentMethod`, `paymentStatus`, and `paymentReference` to Flask.
- `CheckoutPage` now opens a simulated UPI payment dialog when UPI is selected.
- Added a demo QR-style panel, explicit "No real money will be charged" notice, and `Simulate Payment` action.
- Added submit/processing state so duplicate clicks are prevented.
- Existing Card and Cash on Delivery choices remain available.

### `frontend/src/App.css`
- Added only the styles required for the simulated UPI dialog.
- Existing checkout styles and overall site design were not replaced.

### `backend/routes/order.py`
- Accepts and validates `paymentMethod`.
- Stores `paymentMethod`, `paymentStatus`, and `paymentReference` at the order level.
- UPI/Card are stored as simulated `paid`; Cash on Delivery is stored as `pending`.
- No external payment provider or real transaction is introduced.

### `SETUP.md`
- Documented the simulated UPI flow and payment storage behavior.

## Verification

- Python backend files compile successfully.
- `frontend/src/App.jsx` parses successfully with the JSX parser.
- The project was not visually redesigned.

## Important

This is a simulation only. The displayed QR-style panel is not a real payable UPI QR code and does not move money.
