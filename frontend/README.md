# YarnTales – Real Visual Frontend

This build uses the actual YarnTales product photos you supplied and replaces the placeholder products with a real catalogue.

## Visual direction
Inspired by:
- image-first ecommerce homepages
- Pinterest-style masonry discovery
- Instagram-like visual galleries
- cute boutique / bakery-style sticker details

The design is still original to YarnTales.

## Main flows
Sign In / Create Account
→ Home
→ Shop
→ Product
→ Cart
→ Checkout
→ Tracking
→ My Page

Also included:
- Gift Mode
- Custom Corner
- Wishlist
- Profile points
- Sign Out
- Colour Palette
- Real Instagram link
- Mobile bottom navigation
- Search and category filters
- LocalStorage cart / wishlist / demo accounts

## Real Instagram
https://www.instagram.com/yarntalesbyaniiii/

## Run
```powershell
npm install
npm run dev
```

## Backend later
The auth API helper supports:
```env
VITE_USE_BACKEND=true
VITE_API_BASE_URL=http://localhost:5000
```

Then change the API paths in `src/services/api.js` if your teammate's backend uses different routes.

## Prices
The prices in this demo are sample frontend prices because final pricing was not supplied yet. Replace them in:
`src/data/products.js`


### Product list (exact names supplied)
1. 🌻 Sunflower Fringe Sling
2. 💜 Lavender Wave Tote
3. 🐼 Panda Keychain
4. 🌸 Lavender Flower Keychain
5. 🍒 Cherry Duo Keychain
6. 🌻 Sunflower Keychain
7. 🐝 Bee Keychain
8. 🥑 Avocado Keychain
9. 🌼 Navy Daisy Fringe Bag
10. 🧸 flower Mini Bag
11. 🤍 Cream Shell Bag
12. 🎀 Black & Butter Bow Bag
13. 📖 Floral Book Bookmark
14. 🎀 Ribbon Bottle Sleeve
15. 💛 Golden Tie Pouch
16. 🖤 Midnight Flower Scarf
17. 🤎 Toffee Bow Scarf
