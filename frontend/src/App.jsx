import { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppProvider } from './context/AppContext.jsx';
import CustomerNavbar from './components/CustomerNavbar.jsx';
import StaffNavbar from './components/StaffNavbar.jsx';
import CartDrawer from './components/CartDrawer.jsx';
import StorefrontPage from './pages/StorefrontPage.jsx';
import CartPage from './pages/CartPage.jsx';
import AuthPage from './pages/AuthPage.jsx';
import StaffPage from './pages/StaffPage.jsx';
import CheckoutPage from './pages/CheckoutPage.jsx';
import BookDetailPage from './pages/BookDetailPage.jsx';
import OrdersPage from './pages/OrdersPage.jsx';

export default function App() {
  const [cartOpen, setCartOpen] = useState(false);
  const [booksMap, setBooksMap] = useState({});
  const toggleCart = () => setCartOpen(o => !o);
  const handleBooksFetched = (arr) => {
    const map = {};
    arr.forEach(b => map[b.id] = b);
    setBooksMap(map);
  };

  return (
    <AppProvider>
      <BrowserRouter>
        <Routes>
          {/* ── Staff realm ─────────────────── */}
          <Route path="/staff/*" element={
            <div className="min-h-screen">
              <StaffNavbar />
              <div className="max-w-5xl mx-auto px-6">
                <StaffPage />
              </div>
            </div>
          } />

          {/* ── Customer realm ──────────────── */}
          <Route path="*" element={
            <div className="min-h-screen flex flex-col">
              <CustomerNavbar toggleCart={toggleCart} />
              <main className="flex-1">
                <Routes>
                  <Route path="/" element={<StorefrontPage fetchBooks={handleBooksFetched} />} />
                  <Route path="/cart" element={<CartPage booksMap={booksMap} />} />
                  <Route path="/login" element={<AuthPage />} />
                  <Route path="/checkout" element={<CheckoutPage />} />
                  <Route path="/orders" element={<OrdersPage />} />
                  <Route path="/book/:id" element={<BookDetailPage />} />
                </Routes>
              </main>
              <CartDrawer isOpen={cartOpen} toggleCart={toggleCart} booksMap={booksMap} />
            </div>
          } />
        </Routes>
      </BrowserRouter>
    </AppProvider>
  );
}
