import { useEffect, useMemo, useState } from 'react'
import { categories, products as initialProducts, reviews } from './data/products'
import {
  signIn,
  signUp,
  getProducts,
  getCart,
  addCartItem,
  updateCartItem,
  removeCartItem,
  clearCart,
  getWishlist,
  addWishlistItem,
  removeWishlistItem,
  createCustomization,
  getCustomizationTemplate,
  createGiftRequest,
  createOrder,
  getOrders,
  getOrderTracking,
  clearSession,
} from './services/api'
import './App.css'

const IG_URL = 'https://www.instagram.com/yarntalesbyaniiii/?utm_source=ig_web_button_share_sheet&igsh=ZDNlZDc0MzIxNw=='
const money = (value) => `₹${Number(value).toLocaleString('en-IN')}`
let catalogProducts = initialProducts

function App() {
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('yarntales-user')) || null
    } catch {
      return null
    }
  })
  const [view, setView] = useState(() => (user ? 'home' : 'auth'))
  const [authMode, setAuthMode] = useState('signin')
  const [cart, setCart] = useState([])
  const [wishlist, setWishlist] = useState([])
  const [orders, setOrders] = useState([])
  const [selectedProduct, setSelectedProduct] = useState(initialProducts[0])
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('All')
  const [toast, setToast] = useState('')
  const [mobileMenu, setMobileMenu] = useState(false)
  const [paletteOpen, setPaletteOpen] = useState(false)
  const [catalogVersion, setCatalogVersion] = useState(0)
  const [lastOrderId, setLastOrderId] = useState(() => localStorage.getItem('yarntales-last-order') || '')

  const currentUserId = user?.userId || user?.id || ''

  const hydrateCart = (items) => (items || []).map((item) => {
    const product = catalogProducts.find((candidate) => candidate.id === String(item.productId))
    return {
      ...(product || {
        id: String(item.productId),
        name: item.productName || 'YarnTales Product',
        category: item.category || 'Handmade',
        price: Number(item.unitPrice || 0),
        image: item.images?.[0] || '',
        gallery: item.images || [],
        colors: [],
        rating: 4.9,
        reviews: 0,
      }),
      ...item,
      id: String(item.productId),
      name: product?.name || item.productName || 'YarnTales Product',
      category: product?.category || item.category || 'Handmade',
      image: product?.image || item.images?.[0] || '',
      gallery: product?.gallery || item.images || [],
      price: Number(product?.price ?? item.unitPrice ?? 0),
      quantity: Number(item.quantity || 1),
      customizationId: item.customizationId || null,
    }
  })

  const refreshUserData = async (activeUser = user) => {
    const uid = activeUser?.userId || activeUser?.id
    if (!uid) return

    const [productData, cartData, wishlistData, orderData] = await Promise.all([
      getProducts(),
      getCart(uid),
      getWishlist(uid),
      getOrders(uid),
    ])

    catalogProducts = productData
    setCatalogVersion((value) => value + 1)
    setSelectedProduct((current) =>
      productData.find((item) => item.id === current?.id) || productData[0] || current
    )
    setCart(hydrateCart(cartData))
    const productMap = new Map(productData.map((item) => [item.id, item]))
    setWishlist(
      (wishlistData || [])
        .map((item) => productMap.get(String(item.productId)))
        .filter(Boolean),
    )
    setOrders(orderData || [])
  }

  useEffect(() => {
    if (!user) {
      setCart([])
      setWishlist([])
      setOrders([])
      return
    }

    let active = true
    ;(async () => {
      try {
        await refreshUserData(user)
      } catch (error) {
        if (active) notify(error.message || 'Unable to load YarnTales data')
      }
    })()

    return () => {
      active = false
    }
  }, [user])

  useEffect(() => {
    if (user) localStorage.setItem('yarntales-user', JSON.stringify(user))
    else localStorage.removeItem('yarntales-user')
  }, [user])

  useEffect(() => {
    if (lastOrderId) localStorage.setItem('yarntales-last-order', lastOrderId)
    else localStorage.removeItem('yarntales-last-order')
  }, [lastOrderId])

  const cartCount = cart.reduce((sum, item) => sum + item.quantity, 0)
  const cartTotal = cart.reduce((sum, item) => sum + item.price * item.quantity, 0)

  const navigate = (next) => {
    setView(next)
    setMobileMenu(false)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const notify = (message) => {
    setToast(message)
    window.clearTimeout(window.__ytToast)
    window.__ytToast = window.setTimeout(() => setToast(''), 2200)
  }

  const toggleWishlist = async (product) => {
    if (!currentUserId) return

    const exists = wishlist.some((item) => item.id === product.id)
    try {
      if (exists) {
        await removeWishlistItem(currentUserId, product.id)
        setWishlist((current) => current.filter((item) => item.id !== product.id))
        notify('Removed from saved')
      } else {
        await addWishlistItem(currentUserId, product.id)
        setWishlist((current) => [...current, product])
        notify('Saved for later ♡')
      }
    } catch (error) {
      notify(error.message || 'Unable to update wishlist')
    }
  }

  const addToCart = async (product, quantity = 1, customizationId = null) => {
    if (!currentUserId || !product?.id) return

    try {
      await addCartItem({
        userId: currentUserId,
        productId: product.id,
        quantity,
        customizationId,
      })
      const cartData = await getCart(currentUserId)
      setCart(hydrateCart(cartData))
      notify(`${product.name} added to cart 🧶`)
    } catch (error) {
      notify(error.message || 'Unable to add to cart')
    }
  }

  const updateQuantity = async (id, delta) => {
    if (!currentUserId) return

    const item = cart.find((entry) => entry.id === id)
    if (!item) return

    const nextQuantity = item.quantity + delta

    try {
      if (nextQuantity <= 0) {
        await removeCartItem(currentUserId, id)
      } else {
        await updateCartItem(currentUserId, id, nextQuantity)
      }

      const cartData = await getCart(currentUserId)
      setCart(hydrateCart(cartData))
    } catch (error) {
      notify(error.message || 'Unable to update cart')
    }
  }

  const clearUserCart = async () => {
    if (!currentUserId) return
    await clearCart(currentUserId)
    setCart([])
  }

  const handleCustomAdd = async ({ productId, color, size, detail, personalizedName }) => {
    if (!currentUserId || !productId) return
    try {
      const result = await createCustomization({
        userId: currentUserId,
        productId,
        color,
        size,
        features: [detail],
        accessory: detail,
        personalizedName: personalizedName || null,
      })

      await addToCart(
        catalogProducts.find((item) => item.id === productId) || {
          id: productId,
          name: 'Custom Crochet Piece',
        },
        1,
        result.customization.customizationId,
      )
      notify('Your custom piece is in the cart ✨')
    } catch (error) {
      notify(error.message || 'Unable to save customization')
    }
  }

  const handleGiftRequest = async ({ occasion, budget, giftWrapping = false, messageCard = '', scheduledDelivery = null }) => {
    if (!currentUserId) return
    try {
      const result = await createGiftRequest({
        userId: currentUserId,
        occasion,
        budget,
        giftWrapping,
        messageCard,
        scheduledDelivery,
      })
      notify(`${result.giftRequest.recommendations?.length || 0} gift ideas found ✨`)
    } catch (error) {
      notify(error.message || 'Unable to create gift request')
    }
  }

  const handlePlaceOrder = async (orderDetails) => {
    if (!currentUserId || cart.length === 0) return false

    const {
      paymentMethod = 'UPI',
      paymentStatus = paymentMethod === 'Cash on Delivery' ? 'pending' : 'paid',
      paymentReference = null,
      ...shippingAddress
    } = orderDetails

    try {
      const result = await createOrder({
        userId: currentUserId,
        shippingAddress,
        paymentMethod,
        paymentStatus,
        paymentReference,
        items: cart.map((item) => ({
          productId: item.id,
          quantity: item.quantity,
        })),
      })

      setLastOrderId(result.order.orderId)
      await refreshUserData(user)
      setCart([])
      notify('Order placed ♡')
      navigate('tracking')
      return true
    } catch (error) {
      notify(error.message || 'Unable to place order')
      return false
    }
  }

  const handleAuth = async (payload) => {
    try {
      const result = authMode === 'signin'
        ? await signIn(payload)
        : await signUp(payload)

      setUser(result.user)
      navigate('home')
      notify(authMode === 'signin' ? 'Welcome back ♡' : 'Your cozy corner is ready ✨')
    } catch (error) {
      notify(error.message || 'Please check your details')
    }
  }

  const signOut = () => {
    clearSession()
    setUser(null)
    setCart([])
    setWishlist([])
    setOrders([])
    setLastOrderId('')
    navigate('auth')
  }

  if (!user) {
    return (
      <>
        <AuthScreen mode={authMode} setMode={setAuthMode} onSubmit={handleAuth} />
        {toast && <Toast message={toast} />}
      </>
    )
  }

  // Keep the catalog reference alive for child components without changing
  // their visual structure. catalogVersion ensures React rerenders after API sync.
  void catalogVersion

  return (
    <div className="site">
      <Header
        view={view}
        navigate={navigate}
        cartCount={cartCount}
        wishlistCount={wishlist.length}
        search={search}
        setSearch={setSearch}
        mobileMenu={mobileMenu}
        setMobileMenu={setMobileMenu}
        instagramUrl={IG_URL}
      />

      <div className="shell">
        {view === 'home' && (
          <HomePage
            navigate={navigate}
            wishlist={wishlist}
            addToCart={addToCart}
            toggleWishlist={toggleWishlist}
            openProduct={(product) => {
              setSelectedProduct(product)
              navigate('product')
            }}
          />
        )}

        {view === 'shop' && (
          <ShopPage
            search={search}
            setSearch={setSearch}
            categoryFilter={categoryFilter}
            setCategoryFilter={setCategoryFilter}
            wishlist={wishlist}
            addToCart={addToCart}
            toggleWishlist={toggleWishlist}
            openProduct={(product) => {
              setSelectedProduct(product)
              navigate('product')
            }}
          />
        )}

        {view === 'product' && (
          <ProductPage
            product={selectedProduct}
            wishlist={wishlist}
            addToCart={addToCart}
            toggleWishlist={toggleWishlist}
            navigate={navigate}
            openProduct={(product) => {
              setSelectedProduct(product)
              navigate('product')
            }}
          />
        )}

        {view === 'custom' && (
          <CustomPage
            notify={notify}
            onAddCustom={handleCustomAdd}
          />
        )}

        {view === 'gift' && (
          <GiftPage
            wishlist={wishlist}
            addToCart={addToCart}
            toggleWishlist={toggleWishlist}
            openProduct={(product) => {
              setSelectedProduct(product)
              navigate('product')
            }}
            navigate={navigate}
            onGiftRequest={handleGiftRequest}
          />
        )}

        {view === 'wishlist' && (
          <WishlistPage
            wishlist={wishlist}
            addToCart={addToCart}
            toggleWishlist={toggleWishlist}
            openProduct={(product) => {
              setSelectedProduct(product)
              navigate('product')
            }}
            navigate={navigate}
          />
        )}

        {view === 'cart' && (
          <CartPage
            cart={cart}
            cartTotal={cartTotal}
            updateQuantity={updateQuantity}
            navigate={navigate}
          />
        )}

        {view === 'checkout' && (
          <CheckoutPage
            cart={cart}
            cartTotal={cartTotal}
            navigate={navigate}
            notify={notify}
            onPlaceOrder={handlePlaceOrder}
          />
        )}

        {view === 'tracking' && (
          <TrackingPage
            orderId={lastOrderId}
            navigate={navigate}
          />
        )}

        {view === 'inquiry' && <InquiryPage product={selectedProduct} />}

        {view === 'profile' && (
          <ProfilePage
            user={user}
            wishlist={wishlist}
            cartCount={cartCount}
            orderCount={orders.length}
            navigate={navigate}
            signOut={signOut}
          />
        )}
      </div>

      <Footer
        navigate={navigate}
        instagramUrl={IG_URL}
        onPalette={() => setPaletteOpen(true)}
      />

      <MobileNav view={view} navigate={navigate} />

      {paletteOpen && <PaletteModal onClose={() => setPaletteOpen(false)} />}

      {toast && <Toast message={toast} />}
    </div>
  )
}


function AuthScreen({ mode, setMode, onSubmit }) {
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  return (
    <main className="auth-page">
      <section className="auth-visual">
        <div className="auth-collage">
          <img src="/src/assets/flower-bookmark.jpg" alt="" />
          <img src="/src/assets/black-yellow-bow-bag.jpg" alt="" />
          <img src="/src/assets/sunflower-keychain.jpg" alt="" />
          <img src="/src/assets/lavender-wave-tote.jpg" alt="" />
        </div>
        <div className="auth-overlay" />
        <div className="auth-visual-copy">
          <span className="eyebrow inverse">✦ YARNTales · HANDMADE</span>
          <h1>Little things,<br /><em>made with love.</em></h1>
          <p>Shop crochet pieces that feel personal, playful and a little bit you.</p>
        </div>
        <span className="sticker left">♡ made in India</span>
        <span className="sticker right">soft yarn • slow craft</span>
      </section>

      <section className="auth-card">
        <div className="wordmark"><span>♡</span> YarnTales</div>

        <div className="auth-tabs">
          <button className={mode === 'signin' ? 'active' : ''} onClick={() => setMode('signin')}>Sign In</button>
          <button className={mode === 'signup' ? 'active' : ''} onClick={() => setMode('signup')}>Create Account</button>
        </div>

        <div className="auth-title">
          <span>{mode === 'signin' ? 'Welcome back' : 'Welcome in'}</span>
          <h2>{mode === 'signin' ? 'Come back to your cozy corner.' : 'Make your own cozy corner.'}</h2>
          <p>{mode === 'signin' ? 'Your saved pieces are waiting.' : 'Save favourites and make checkout easier.'}</p>
        </div>

        <form className="auth-form" onSubmit={(event) => {
          event.preventDefault()
          onSubmit({ name, phone, email, password })
        }}>
          {mode === 'signup' && (
            <label>
              Name
              <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Your name" required />
            </label>
          )}
          <label>
            Phone Number
            <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="10-digit mobile number" inputMode="numeric" required />
          </label>
          <label>
            Email
            <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" type="email" required />
          </label>
          <label>
            Password
            <input value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" type="password" required />
          </label>
          <button className="primary-cta auth-submit" type="submit">
            {mode === 'signin' ? 'Sign In' : 'Create Account'} <span>→</span>
          </button>
        </form>

        <p className="auth-switch">
          {mode === 'signin' ? 'New here?' : 'Already have an account?'}{' '}
          <button onClick={() => setMode(mode === 'signin' ? 'signup' : 'signin')}>
            {mode === 'signin' ? 'Create an account' : 'Sign in'}
          </button>
        </p>
      </section>
    </main>
  )
}

function Header({ view, navigate, cartCount, wishlistCount, search, setSearch, mobileMenu, setMobileMenu, instagramUrl }) {
  return (
    <header className="topbar">
      <button className="brand" onClick={() => navigate('home')}><span>♡</span> YarnTales</button>

      <nav className={`nav ${mobileMenu ? 'open' : ''}`}>
        <button className={view === 'shop' ? 'active' : ''} onClick={() => navigate('shop')}>Shop</button>
        <button className={view === 'gift' ? 'active' : ''} onClick={() => navigate('gift')}>Gift Mode ✨</button>
        <button className={view === 'custom' ? 'active' : ''} onClick={() => navigate('custom')}>Custom</button>
        <button className={view === 'wishlist' ? 'active' : ''} onClick={() => navigate('wishlist')}>Wishlist <sup>{wishlistCount}</sup></button>
        <button className={view === 'profile' ? 'active' : ''} onClick={() => navigate('profile')}>My Page</button>
        <a href={instagramUrl} target="_blank" rel="noreferrer">Instagram ↗</a>
      </nav>

      <div className="header-right">
        <label className="searchbar">
          <span>⌕</span>
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && navigate('shop')}
            placeholder="Search cozy things..."
          />
        </label>
        <button className="cart-chip" onClick={() => navigate('cart')}>Cart ({cartCount})</button>
        <button className="menu-toggle" onClick={() => setMobileMenu((open) => !open)} aria-label="Menu">☰</button>
      </div>
    </header>
  )
}

function HomePage({ navigate, wishlist, addToCart, toggleWishlist, openProduct }) {
  const featureProducts = [catalogProducts[0], catalogProducts[2], catalogProducts[12], catalogProducts[16]]

  return (
    <main>
      <section className="home-hero">
        <div className="hero-copy">
          <span className="eyebrow">✦ handmade in India</span>
          <h1>Handcrafted with love,<br /><em>stitched just for you.</em></h1>
          <p>Real crochet. Small batches. Cute little things made to be gifted, carried, clipped on and loved.</p>

          <div className="hero-actions">
            <button className="primary-cta" onClick={() => navigate('shop')}>Shop the pieces →</button>
            <button className="soft-cta" onClick={() => navigate('custom')}>Make a custom one</button>
          </div>

          <div className="hero-notes">
            <span>♡ handmade</span>
            <span>✦ gift-ready</span>
            <span>🧶 made slowly</span>
          </div>
        </div>

        <div className="hero-photo-grid">
          <div className="hero-photo tall"><img src="/src/assets/black-yellow-bow-bag.jpg" alt="Crochet black and yellow bow bag" /><span>the bow girl ♡</span></div>
          <div className="hero-photo"><img src="/src/assets/flower-bookmark.jpg" alt="Floral crochet bookmark" /></div>
          <div className="hero-photo"><img src="/src/assets/cherry-keychain.jpg" alt="Crochet cherry keychain" /></div>
          <div className="hero-photo"><img src="/src/assets/navy-daisy-fringe-bag.jpg" alt="Navy crochet fringe bag" /></div>
          <div className="hero-sticker">tiny details<br /><b>big feelings</b></div>
        </div>
      </section>

      <section className="ticker">
        <div>♡ handmade</div><div>✦ cute things</div><div>♡ small batches</div><div>✦ made in India</div><div>♡ gift a little joy</div>
      </section>

      <section className="home-section cream">
        <SectionHeader title="The little favourites" subtitle="Things that look even cuter off-screen." action="Shop all" onAction={() => navigate('shop')} />

        <div className="featured-grid">
          {featureProducts.map((product, index) => (
            <PinterestCard
              key={product.id}
              product={product}
              tall={index === 0 || index === 3}
              wishlist={wishlist}
              addToCart={addToCart}
              toggleWishlist={toggleWishlist}
              openProduct={openProduct}
            />
          ))}
        </div>
      </section>

      <section className="home-section pinkwash">
        <SectionHeader title="Pick your vibe" subtitle="A little corner for every kind of cozy." />

        <div className="category-grid home-category">
          {categories.map((category) => (
            <button key={category.title} className="category-card" onClick={() => category.title === 'Custom' ? navigate('custom') : navigate('shop')}>
              <span className={`category-art ${category.tone}`}>{category.icon}</span>
              <span className="category-copy"><b>{category.title}</b><small>{category.text}</small></span>
              <span className="arrow">↗</span>
            </button>
          ))}
        </div>
      </section>

      <section className="story-strip">
        <div className="story-photo">
          <img src="/src/assets/black-flower-scarf-flat.jpg" alt="Handmade black and cream crochet scarf" />
        </div>
        <div className="story-copy">
          <span className="eyebrow">✦ WHY YARNTales</span>
          <h2>Made by hand.<br />Made to feel like yours.</h2>
          <p>From tiny keychains to everyday bags, every piece is made slowly with real yarn, little details and a lot of care.</p>
          <button className="soft-cta" onClick={() => navigate('custom')}>Make something personal →</button>
        </div>
      </section>

      <section className="home-section cream">
        <SectionHeader
          title="Save a little inspiration"
          subtitle="Our real pieces, arranged like a moodboard."
          action="See more on Instagram"
          onAction={() => window.open(IG_URL, '_blank', 'noopener,noreferrer')}
        />

        <div className="moodboard">
          {catalogProducts.slice(1, 10).map((product, index) => (
            <button className={`mood-card mood-${(index % 6) + 1}`} key={product.id} onClick={() => openProduct(product)}>
              <img src={product.image} alt={product.name} />
              <span><b>{product.name}</b><small>♡ save idea</small></span>
            </button>
          ))}
        </div>
      </section>

      <section className="home-section pinkwash">
        <SectionHeader title="Loved by cozy collectors" subtitle="Sweet little notes from customers in India." />

        <div className="review-grid">
          {reviews.map((review) => (
            <article className="review-card" key={review.name}>
              <div className="review-person"><span>{review.name[0]}</span><div><b>{review.name}</b><small>{review.city}</small></div></div>
              <div className="stars">★★★★★</div>
              <p>“{review.text}”</p>
            </article>
          ))}
        </div>
      </section>

      <section className="instagram-banner">
        <div className="insta-copy">
          <span className="eyebrow">✦ @yarntalesbyaniiii</span>
          <h2>Come hang out<br />on Instagram ♡</h2>
          <p>See new pieces, behind-the-scenes crochet and the real YarnTales mood.</p>
          <a className="primary-cta link-button" href={IG_URL} target="_blank" rel="noreferrer">Visit Instagram ↗</a>
        </div>

        <div className="insta-grid">
          {[
            '/src/assets/flower-bookmark.jpg',
            '/src/assets/cherry-keychain.jpg',
            '/src/assets/black-yellow-bow-bag.jpg',
            '/src/assets/sunflower-keychain.jpg',
          ].map((src, index) => <img key={src} src={src} alt={`YarnTales Instagram preview ${index + 1}`} />)}
        </div>
      </section>

      <section className="club-banner">
        <div><span className="eyebrow">✦ THE COZY CLUB</span><h2>A little love in your inbox.</h2><p>New drops, cute gift ideas and 10% off your first order.</p></div>
        <form className="club-form" onSubmit={(e) => { e.preventDefault(); e.currentTarget.reset() }}>
          <input placeholder="your@email.com" type="email" required />
          <button className="primary-cta" type="submit">Join ♡</button>
        </form>
      </section>
    </main>
  )
}

function ShopPage({ search, setSearch, categoryFilter, setCategoryFilter, wishlist, addToCart, toggleWishlist, openProduct }) {
  const filters = ['All', 'Bags', 'Keychains', 'Bookish', 'Pouches', 'Everyday', 'Wearables']
  const list = catalogProducts.filter((product) => {
    const categoryOk = categoryFilter === 'All' || product.category === categoryFilter
    const searchOk = !search.trim() || `${product.name} ${product.category}`.toLowerCase().includes(search.trim().toLowerCase())
    return categoryOk && searchOk
  })

  return (
    <main className="page-section">
      <div className="page-intro">
        <span className="eyebrow">✦ THE COLLECTION</span>
        <h1>Little things worth keeping.</h1>
        <p>Pick a bag, add a tiny charm, or find something made for your next reading day.</p>
      </div>

      <div className="shop-toolbar">
        <div className="filter-pills">
          {filters.map((filter) => <button key={filter} className={categoryFilter === filter ? 'selected' : ''} onClick={() => setCategoryFilter(filter)}>{filter}</button>)}
        </div>
        <label className="shop-search"><span>⌕</span><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search..." /></label>
      </div>

      <div className="shop-layout">
        <aside className="filter-card">
          <b>Browse by</b>
          <span>Price</span>
          <label><input type="checkbox" /> Under ₹1,000</label>
          <label><input type="checkbox" /> ₹1,000–₹1,500</label>
          <label><input type="checkbox" /> ₹1,500+</label>
          <span>Colours</span>
          <div className="swatches"><i className="s-lavender" /><i className="s-pink" /><i className="s-yellow" /><i className="s-mint" /><i className="s-blue" /></div>
          <span>Need help?</span>
          <button className="mini-link" onClick={() => setCategoryFilter('All')}>Clear filters</button>
        </aside>

        <div className="shop-grid">
          {list.length ? list.map((product) => (
            <PinterestCard key={product.id} product={product} wishlist={wishlist} addToCart={addToCart} toggleWishlist={toggleWishlist} openProduct={openProduct} />
          )) : <EmptyState title="No little finds here." text="Try another word or category." />}
        </div>
      </div>
    </main>
  )
}

function ProductPage({ product, wishlist, addToCart, toggleWishlist, navigate, openProduct }) {
  const [qty, setQty] = useState(1)
  const [colour, setColour] = useState(product.colors[0])
  const saved = wishlist.some((item) => item.id === product.id)

  return (
    <main className="page-section">
      <button className="back-link" onClick={() => navigate('shop')}>← Back to shop</button>

      <section className="product-detail">
        <div className="product-gallery">
          <div className="product-main-photo"><img src={product.image} alt={product.name} /></div>
          <div className="thumbnail-row">
            {product.gallery.map((image) => <img key={image} src={image} alt="" />)}
          </div>
        </div>

        <div className="product-info">
          <span className="product-label">✦ made with love</span>
          <h1>{product.name}</h1>
          <div className="rating-line"><span className="stars">★★★★★</span> {product.rating} · {product.reviews} reviews</div>
          <div className="big-price">{money(product.price)}</div>
          <p>{product.description}</p>

          <div className="detail-option"><b>Pick a colour</b><div className="choice-row">{product.colors.map((item) => <button className={colour === item ? 'selected' : ''} key={item} onClick={() => setColour(item)}>{item}</button>)}</div></div>

          <div className="detail-option"><b>Quantity</b><div className="qty-box"><button onClick={() => setQty((q) => Math.max(1, q - 1))}>−</button><span>{qty}</span><button onClick={() => setQty((q) => q + 1)}>+</button></div></div>

          <div className="purchase-row">
            <button className="primary-cta fill" onClick={() => addToCart(product, qty)}>Add to Cart · {money(product.price * qty)}</button>
            <button className="icon-button" onClick={() => toggleWishlist(product)}>{saved ? '♥' : '♡'}</button>
          </div>

          <div className="accordion">
            <div><b>Details</b><span>Made by hand with soft yarn and careful finishing.</span></div>
            <div><b>Care</b><span>Keep dry and spot-clean gently when needed.</span></div>
            <div><b>Shipping</b><span>Made-to-order pieces may take a few days before dispatch.</span></div>
          </div>

          <button className="inquiry-button" onClick={() => navigate('inquiry')}>Have a question about this piece? →</button>
        </div>
      </section>

      <section className="section-inner">
        <SectionHeader title="You may also like" subtitle="A few more things you might love." />
        <div className="product-row-three">{catalogProducts.filter((item) => item.id !== product.id).slice(0, 3).map((item) => <PinterestCard key={item.id} product={item} wishlist={wishlist} addToCart={addToCart} toggleWishlist={toggleWishlist} openProduct={openProduct} />)}</div>
      </section>
    </main>
  )
}

function CustomPage({ notify, onAddCustom }) {
  const [base, setBase] = useState('Mini Bag')
  const [colour, setColour] = useState('Lavender')
  const [detail, setDetail] = useState('Bow')
  const [note, setNote] = useState('')
  const [template, setTemplate] = useState(null)

  useEffect(() => {
    getCustomizationTemplate().then(setTemplate).catch(() => setTemplate(null))
  }, [])

  const customColours = ['Lavender', 'Blush Pink', 'Butter Yellow', 'Mint', 'Baby Blue', 'Cream']
  const size = 'Standard'
  const previewImage = '/src/assets/lavender-wave-tote.jpg'

  return (
    <main className="page-section">
      <div className="page-intro row-intro"><div><span className="eyebrow">✦ CUSTOM CORNER</span><h1>Make it yours.</h1><p>Pick the shape, colour and little detail. Keep the words simple — keep the piece personal.</p></div><span className="price-pill">from ₹1,999</span></div>

      <div className="builder">
        <div className="builder-preview"><span className="live-tag">● live preview</span><img src={previewImage} alt="Custom crochet preview" /><div className="preview-caption"><b>{colour} {base}</b><span>{detail} · made for you</span></div></div>

        <div className="builder-controls">
          <BuilderStep number="01" title="Choose your base">
            <div className="choice-grid">{['Mini Bag', 'Pouch', 'Keychain'].map((item) => <button key={item} className={base === item ? 'selected' : ''} onClick={() => setBase(item)}>{item}</button>)}</div>
          </BuilderStep>
          <BuilderStep number="02" title="Pick a colour">
            <div className="choice-row wrap">{customColours.map((item) => <button key={item} className={colour === item ? 'selected' : ''} onClick={() => setColour(item)}>{item}</button>)}</div>
          </BuilderStep>
          <BuilderStep number="03" title="Choose the detail">
            <div className="choice-row wrap">{['Bow', 'Flower', 'Heart', 'Name tag'].map((item) => <button key={item} className={detail === item ? 'selected' : ''} onClick={() => setDetail(item)}>{item}</button>)}</div>
          </BuilderStep>
          <BuilderStep number="04" title="Add a gift note">
            <textarea className="wide-input" rows="4" value={note} onChange={(e) => setNote(e.target.value)} placeholder="Write a short note..." />
          </BuilderStep>

          <div className="builder-bottom">
            <div><small>Estimated price</small><b>₹1,999</b></div>
            <button
              className="primary-cta"
              onClick={() => {
                if (!template?.id) {
                  notify('Custom builder is still loading — please try again.')
                  return
                }
                onAddCustom({
                  productId: template.id,
                  color: colour,
                  size,
                  detail,
                  personalizedName: note,
                })
              }}
            >
              Add Custom Piece
            </button>
          </div>
        </div>
      </div>
    </main>
  )
}


function GiftPage({ wishlist, addToCart, toggleWishlist, openProduct, navigate, onGiftRequest }) {
  const [recipient, setRecipient] = useState('For Her')
  const [occasion, setOccasion] = useState('Birthday')
  const [budget, setBudget] = useState('₹2,000')

  const picks = occasion === 'Anniversary' ? catalogProducts.slice(11, 14) : recipient === 'For Baby' ? catalogProducts.slice(1, 4) : catalogProducts.slice(0, 3)

  return (
    <main className="page-section">
      <div className="page-intro row-intro"><div><span className="eyebrow">✦ GIFT MODE ✨</span><h1>Tell us a little about them.</h1><p>We'll help you find something that feels personal.</p></div><span className="gift-badge">gift helper on</span></div>

      <section className="gift-panel">
        <BuilderStep number="01" title="Who is it for?">
          <div className="recipient-grid">{['For Her', 'For Him', 'For Kids', 'For Baby', 'For a Friend'].map((item) => <button key={item} className={recipient === item ? 'selected' : ''} onClick={() => setRecipient(item)}><span>{item.slice(4, 5)}</span><b>{item}</b><small>cute picks</small></button>)}</div>
        </BuilderStep>

        <BuilderStep number="02" title="What's the occasion?">
          <div className="choice-row wrap">{['Birthday', 'Anniversary', 'Thank You', 'Just Because', 'Housewarming'].map((item) => <button key={item} className={occasion === item ? 'selected' : ''} onClick={() => setOccasion(item)}>{item}</button>)}</div>
        </BuilderStep>

        <BuilderStep number="03" title="Set a budget">
          <div className="budget-grid">{['₹1,000', '₹2,000', '₹3,000', '₹5,000+'].map((item) => <button key={item} className={budget === item ? 'selected' : ''} onClick={() => setBudget(item)}><b>{item}</b><small>gift ideas</small></button>)}</div>
        </BuilderStep>

        <div className="gift-picks"><div className="gift-picks-head"><div><h2>Your picks</h2><p>{recipient} · {occasion} · {budget}</p></div><button className="soft-cta" onClick={() => {
  const numericBudget = Number(budget.replace(/[^0-9]/g, '')) || 2000
  onGiftRequest?.({
    occasion,
    budget: numericBudget,
    giftWrapping: false,
    messageCard: '',
  })
  navigate('shop')
}}>See all</button></div><div className="product-row-three">{picks.map((product) => <PinterestCard key={product.id} product={product} wishlist={wishlist} addToCart={addToCart} toggleWishlist={toggleWishlist} openProduct={openProduct} />)}</div></div>
      </section>
    </main>
  )
}

function WishlistPage({ wishlist, addToCart, toggleWishlist, openProduct, navigate }) {
  return <main className="page-section"><div className="page-intro row-intro"><div><span className="eyebrow">✦ SAVED ♡</span><h1>My Cozy Wishlist</h1><p>Keep the pieces you love close by.</p></div><span className="price-pill">{wishlist.length} saved</span></div>{wishlist.length ? <div className="product-row-three">{wishlist.map((product) => <PinterestCard key={product.id} product={product} wishlist={wishlist} addToCart={addToCart} toggleWishlist={toggleWishlist} openProduct={openProduct} />)}</div> : <EmptyState title="Your wishlist is waiting." text="Save the little things you love." action="Browse shop" onAction={() => navigate('shop')} />}</main>
}

function CartPage({ cart, cartTotal, updateQuantity, navigate }) {
  const shipping = cartTotal >= 2500 ? 0 : cart.length ? 99 : 0
  return <main className="page-section"><div className="page-intro"><span className="eyebrow">✦ YOUR CART 🧶</span><h1>Your Cozy Cart</h1><p>{cart.length ? 'Almost yours.' : 'Nothing here yet — let’s find something cute.'}</p></div>{cart.length ? <div className="cart-layout"><div className="cart-list">{cart.map((item) => <div className="cart-row" key={item.id}><img src={item.image} alt={item.name} /><div className="cart-copy"><b>{item.name}</b><small>{item.category}</small><strong>{money(item.price)}</strong></div><div className="qty-box"><button onClick={() => updateQuantity(item.id, -1)}>−</button><span>{item.quantity}</span><button onClick={() => updateQuantity(item.id, 1)}>+</button></div><b>{money(item.price * item.quantity)}</b></div>)}<div className="shipping-hint">{shipping ? `Add ${money(2500 - cartTotal)} more for free shipping` : 'Free shipping unlocked ✨'}</div></div><aside className="summary-card"><h2>Order summary</h2><div><span>Subtotal</span><b>{money(cartTotal)}</b></div><div><span>Shipping</span><b>{shipping ? money(shipping) : 'FREE'}</b></div><hr /><div className="summary-total"><span>Total</span><b>{money(cartTotal + shipping)}</b></div><button className="primary-cta fill" onClick={() => navigate('checkout')}>Checkout →</button></aside></div> : <EmptyState title="Your cart is waiting." text="Find something soft, cute or useful." action="Start shopping" onAction={() => navigate('shop')} />}</main>
}

function CheckoutPage({ cart, cartTotal, navigate, notify, onPlaceOrder }) {
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [address, setAddress] = useState('')
  const [city, setCity] = useState('')
  const [pincode, setPincode] = useState('')
  const [payment, setPayment] = useState('UPI')
  const [showUpiPayment, setShowUpiPayment] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const deliveryDetails = () => ({
    name: name.trim(),
    phone: phone.trim(),
    address: address.trim(),
    city: city.trim(),
    pincode: pincode.trim(),
    state: 'Maharashtra',
  })

  const submitOrder = async () => {
    if (!name.trim() || !phone.trim() || !address.trim() || !city.trim() || !pincode.trim()) {
      notify('Please complete your delivery details')
      return
    }

    if (payment === 'UPI') {
      setShowUpiPayment(true)
      return
    }

    setSubmitting(true)
    await onPlaceOrder({
      ...deliveryDetails(),
      paymentMethod: payment,
      paymentStatus: payment === 'Cash on Delivery' ? 'pending' : 'paid',
      paymentReference: payment === 'Cash on Delivery' ? null : `SIM-${payment.toUpperCase().replaceAll(' ', '-')}-${Date.now()}`,
    })
    setSubmitting(false)
  }

  const confirmUpiPayment = async () => {
    setSubmitting(true)
    const success = await onPlaceOrder({
      ...deliveryDetails(),
      paymentMethod: 'UPI',
      paymentStatus: 'paid',
      paymentReference: `SIM-UPI-${Date.now()}`,
    })
    setSubmitting(false)
    if (success) setShowUpiPayment(false)
  }

  return (
    <main className="page-section">
      <button className="back-link" onClick={() => navigate('cart')}>← Back to cart</button>
      <div className="checkout-layout">
        <div className="checkout-left">
          <div className="form-card">
            <span className="step-mini">01</span>
            <h2>Delivery details</h2>
            <div className="field-grid">
              <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Full name" />
              <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="Phone number" inputMode="numeric" />
              <input className="full" value={address} onChange={(e) => setAddress(e.target.value)} placeholder="Address" />
              <input value={city} onChange={(e) => setCity(e.target.value)} placeholder="City" />
              <input value={pincode} onChange={(e) => setPincode(e.target.value)} placeholder="Pincode" />
            </div>
          </div>

          <div className="form-card">
            <span className="step-mini">02</span>
            <h2>Payment</h2>
            <div className="payment-list">
              {['UPI', 'Card', 'Cash on Delivery'].map((item) => (
                <button key={item} className={payment === item ? 'selected' : ''} onClick={() => setPayment(item)}>
                  <span>{item}</span><small>{payment === item ? '●' : '○'}</small>
                </button>
              ))}
            </div>
          </div>
        </div>

        <aside className="summary-card">
          <h2>Your order</h2>
          {cart.map((item) => <div className="summary-item" key={item.id}><span>{item.name} × {item.quantity}</span><b>{money(item.price * item.quantity)}</b></div>)}
          <hr />
          <div className="summary-total"><span>Total</span><b>{money(cartTotal)}</b></div>
          <button className="primary-cta fill" onClick={submitOrder} disabled={submitting}>
            {submitting ? 'Processing…' : 'Place Order'}
          </button>
        </aside>
      </div>

      {showUpiPayment && (
        <div className="simulated-payment-overlay" role="dialog" aria-modal="true" aria-labelledby="upi-payment-title">
          <div className="simulated-payment-modal">
            <button
              className="simulated-payment-close"
              onClick={() => !submitting && setShowUpiPayment(false)}
              aria-label="Close payment dialog"
              disabled={submitting}
            >
              ×
            </button>
            <span className="eyebrow">✦ UPI PAYMENT</span>
            <h2 id="upi-payment-title">Pay {money(cartTotal)}</h2>
            <p className="simulated-payment-note">This is a simulated UPI payment for the YarnTales project. No real money will be charged.</p>

            <div className="simulated-qr" aria-label="Simulated UPI QR code">
              <span className="qr-corner qr-corner-a" />
              <span className="qr-corner qr-corner-b" />
              <span className="qr-corner qr-corner-c" />
              <span className="qr-block qr-block-1" />
              <span className="qr-block qr-block-2" />
              <span className="qr-block qr-block-3" />
              <span className="qr-block qr-block-4" />
              <span className="qr-block qr-block-5" />
              <span className="qr-block qr-block-6" />
              <span className="qr-block qr-block-7" />
              <span className="qr-block qr-block-8" />
              <span className="qr-block qr-block-9" />
              <span className="qr-block qr-block-10" />
              <span className="qr-block qr-block-11" />
              <span className="qr-block qr-block-12" />
              <span className="qr-block qr-block-13" />
              <span className="qr-block qr-block-14" />
              <span className="qr-block qr-block-15" />
              <span className="qr-label">DEMO</span>
            </div>

            <div className="simulated-upi-hint">
              <b>UPI</b>
              <span>Scan & pay in a real UPI app is not enabled for this demo.</span>
            </div>

            <button className="primary-cta fill" onClick={confirmUpiPayment} disabled={submitting}>
              {submitting ? 'Confirming payment…' : 'Simulate Payment ✓'}
            </button>
            <button className="text-button simulated-cancel" onClick={() => setShowUpiPayment(false)} disabled={submitting}>Cancel</button>
          </div>
        </div>
      )}
    </main>
  )
}


function TrackingPage({ orderId, navigate }) {
  const [tracking, setTracking] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!orderId) return

    let active = true
    getOrderTracking(orderId)
      .then((data) => active && setTracking(data))
      .catch((err) => active && setError(err.message || 'Unable to load order tracking'))

    return () => { active = false }
  }, [orderId])

  const labels = {
    order_confirmed: ['Order confirmed', 'We received your order.'],
    materials_sourced: ['Materials sourced', 'The yarn and supplies are ready.'],
    handcrafting_in_progress: ['Being made', 'Your piece is being crocheted with care.'],
    quality_check: ['Quality check', 'We are checking every little detail.'],
    packed: ['Packed', 'Wrapped and ready to leave us.'],
    dispatched: ['On the way', 'Your parcel is heading to you.'],
    delivered: ['Delivered', 'Your YarnTales piece has arrived.'],
  }

  if (error) {
    return (
      <main className="page-section">
        <div className="empty-state"><div className="empty-symbol">♡</div><h2>We couldn't load this order.</h2><p>{error}</p><button className="primary-cta" onClick={() => navigate('shop')}>Keep browsing</button></div>
      </main>
    )
  }

  const stages = tracking?.tracking || []
  const current = tracking?.currentStatus || 'order_confirmed'

  return (
    <main className="page-section">
      <div className="tracking-head">
        <div><span className="eyebrow">✦ ORDER TRACKING 📦</span><h1>Your Yarn Trail</h1><p>{orderId ? `Order #${orderId}` : 'Your latest order will appear here.'}</p></div>
        <span className="status-badge">{current.replaceAll('_', ' ')}</span>
      </div>
      <section className="tracking-card">
        <div className="tracking-timeline">
          {stages.map((stage, index) => {
            const [title, description] = labels[stage.status] || [stage.status, '']
            return (
              <div className={`tracking-step ${stage.completed ? 'done' : ''}`} key={stage.status}>
                <span className="tracking-dot">{stage.completed ? '✓' : ''}</span>
                <div><b>{title}</b><p>{description}</p></div>
              </div>
            )
          })}
        </div>
        <div className="maker-note"><div className="maker-avatar">Y</div><div><b>Made by a YarnTales maker</b><span>Your piece is being prepared in India and packed with care.</span></div></div>
        <button className="soft-cta" onClick={() => navigate('home')}>Keep browsing</button>
      </section>
    </main>
  )
}


function ProfilePage({ user, wishlist, cartCount, orderCount, navigate, signOut }) {
  return <main className="page-section"><div className="profile-hero"><div className="profile-avatar">{user.name?.[0] || 'Y'}</div><div><span className="eyebrow">✦ MY COZY CORNER</span><h1>Hi, {user.name || 'there'}.</h1><p>{user.email} · {user.phone}</p></div></div><div className="profile-stats"><div><b>{wishlist.length}</b><span>Saved pieces</span></div><div><b>{cartCount}</b><span>In your cart</span></div><div><b>{orderCount}</b><span>Past orders</span></div><div><b>{user.points || 120}</b><span>Cozy points ✦</span></div></div><div className="profile-menu"><button onClick={() => navigate('wishlist')}>My Wishlist <span>→</span></button><button onClick={() => navigate('tracking')}>My Orders <span>→</span></button><button onClick={() => navigate('custom')}>My Custom Pieces <span>→</span></button><button>Saved Addresses <span>→</span></button><button>Account Settings <span>→</span></button><button className="signout" onClick={signOut}>Sign Out <span>→</span></button></div></main>
}

function PinterestCard({ product, tall = false, wishlist, addToCart, toggleWishlist, openProduct }) {
  const saved = wishlist.some((item) => item.id === product.id)
  return <article className={`pin-card ${tall ? 'tall' : ''}`}><button className="pin-photo" onClick={() => openProduct(product)}><img src={product.image} alt={product.name} /><span className="heart-button" onClick={(e) => { e.stopPropagation(); toggleWishlist(product) }}>{saved ? '♥' : '♡'}</span></button><div className="pin-meta"><small>{product.category}</small><button className="product-name" onClick={() => openProduct(product)}>{product.name}</button><div className="product-line"><span className="stars">★ {product.rating}</span><b>{money(product.price)}</b></div><button className="product-add" onClick={() => addToCart(product)}>Add to Cart</button></div></article>
}

function SectionHeader({ title, subtitle, action, onAction }) {
  return <div className="section-header"><div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div>{action && <button className="text-button" onClick={onAction}>{action} ↗</button>}</div>
}

function BuilderStep({ number, title, children }) {
  return <section className="builder-step"><div className="builder-step-title"><span>{number}</span><h3>{title}</h3></div>{children}</section>
}

function EmptyState({ title, text, action, onAction }) {
  return <div className="empty-state"><div className="empty-symbol">♡</div><h2>{title}</h2><p>{text}</p>{action && <button className="primary-cta" onClick={onAction}>{action}</button>}</div>
}

function InquiryPage({ product }) {
  const [message, setMessage] = useState('')
  return (
    <main className="page-section narrow">
      <button className="back-link" onClick={() => window.history.back()}>← Back</button>
      <div className="page-intro">
        <span className="eyebrow">✦ ASK US</span>
        <h1>Have a question?</h1>
        <p>Ask us anything about {product.name}.</p>
      </div>
      <div className="form-card inquiry-card">
        <label>
          Your message
          <textarea value={message} onChange={(e) => setMessage(e.target.value)} rows="7" placeholder="Ask about colour, size, making time or anything else..." />
        </label>
        <button className="primary-cta" onClick={() => setMessage('')}>Send message ♡</button>
      </div>
    </main>
  )
}

function Footer({ navigate, instagramUrl, onPalette }) {
  return <footer className="footer"><div><div className="brand footer-brand">♡ YarnTales</div><p>Little handmade things for big happy moments.</p><small>Made with care in India</small></div><div><h4>Shop</h4><button onClick={() => navigate('shop')}>All pieces</button><button onClick={() => navigate('gift')}>Gift Mode</button><button onClick={() => navigate('custom')}>Custom Corner</button><button onClick={() => navigate('wishlist')}>Wishlist</button></div><div><h4>Account</h4><button onClick={() => navigate('profile')}>My Cozy Corner</button><button onClick={() => navigate('tracking')}>My Orders</button><button onClick={() => navigate('cart')}>My Cart</button><a href={instagramUrl} target="_blank" rel="noreferrer">Instagram ↗</a></div><div><h4>Resources</h4><button onClick={onPalette}>Colour Palette</button><button>Care Guide</button><button>Shipping & Returns</button><button>Care Guide</button><a href={instagramUrl} target="_blank" rel="noreferrer">@yarntalesbyaniiii</a></div></footer>
}

function PaletteModal({ onClose }) {
  const colours = [['Lavender','#c9adff'],['Blush Pink','#ffb6ca'],['Butter Yellow','#ffe7a1'],['Mint','#c3ead8'],['Baby Blue','#c6dcff'],['Warm Cream','#fff8ef']]
  return <div className="modal-backdrop" onClick={onClose}><div className="palette-modal" onClick={(e) => e.stopPropagation()}><button className="modal-close" onClick={onClose}>×</button><span className="eyebrow">✦ YARNTALES PALETTE</span><h2>Soft colours, tiny details.</h2><p>These are the shades used throughout the site.</p><div className="palette-grid">{colours.map(([name, hex]) => <div key={name}><span style={{ background: hex }} /><b>{name}</b><small>{hex}</small></div>)}</div></div></div>
}

function MobileNav({ view, navigate }) {
  return <nav className="mobile-nav"><button className={view === 'home' ? 'active' : ''} onClick={() => navigate('home')}><span>⌂</span>Home</button><button className={view === 'shop' ? 'active' : ''} onClick={() => navigate('shop')}><span>⌕</span>Shop</button><button className={view === 'custom' ? 'active' : ''} onClick={() => navigate('custom')}><span>✦</span>Custom</button><button className={view === 'wishlist' ? 'active' : ''} onClick={() => navigate('wishlist')}><span>♡</span>Saved</button><button className={view === 'cart' ? 'active' : ''} onClick={() => navigate('cart')}><span>▢</span>Cart</button></nav>
}

function Toast({ message }) {
  return <div className="toast">{message}</div>
}

function readStorage(key, fallback) {
  try {
    const parsed = JSON.parse(localStorage.getItem(key))
    return parsed ?? fallback
  } catch {
    return fallback
  }
}

export default App
