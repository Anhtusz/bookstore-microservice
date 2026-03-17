import { useEffect, useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { AppContext } from '../context/AppContext.jsx';

export default function CartPage({ booksMap }) {
    const { user, cart, fetchCart, API_BASE, showToast } = useContext(AppContext);
    const navigate = useNavigate();

    // Redirect to login if not authenticated
    useEffect(() => {
        if (user === null) {
            showToast("Please sign in to view your cart", "error");
            navigate('/login');
        }
    }, [user]);

    const updateQty = async (itemId, newQty, bookId, cartId) => {
        if (newQty <= 0) {
            await axios.delete(`${API_BASE}/cart/cart-items/${itemId}/`);
        } else {
            await axios.put(`${API_BASE}/cart/cart-items/${itemId}/`, {
                quantity: newQty, cart: cartId, book_id: bookId
            });
        }
        fetchCart(user.id);
    };

    const checkout = () => {
        navigate('/checkout');
    };

    if (!user) return null;

    let total = 0;

    return (
        <div className="max-w-3xl mx-auto py-12 px-6">
            <div className="flex items-center justify-between mb-8">
                <h1 className="text-3xl font-bold">Your Cart</h1>
                <Link to="/" className="text-slate-400 hover:text-white text-sm transition">
                    ← Continue Shopping
                </Link>
            </div>

            {cart.length === 0 ? (
                <div className="glass-panel py-20 text-center text-slate-400 flex flex-col items-center gap-4">
                    <span className="text-6xl">🛒</span>
                    <p>Your cart is empty.</p>
                    <Link to="/" className="mt-2 px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-bold transition">
                        Browse Books
                    </Link>
                </div>
            ) : (
                <div className="flex flex-col gap-4">
                    {cart.map(item => {
                        const book = booksMap[item.book_id] || { title: `Book #${item.book_id}`, price: 10.0 };
                        const price = parseFloat(book.price || 10);
                        total += price * item.quantity;

                        return (
                            <div key={item.id} className="glass-panel p-5 flex items-center gap-4 group hover:border-blue-500/40 transition">
                                <span className="text-4xl">📖</span>
                                <div className="flex-1">
                                    <h4 className="font-semibold">{book.title}</h4>
                                    <p className="text-blue-400 font-bold">${price.toFixed(2)}</p>
                                </div>
                                <div className="flex items-center gap-2">
                                    <button onClick={() => updateQty(item.id, item.quantity - 1, item.book_id, item.cart)}
                                        className="w-8 h-8 bg-white/10 hover:bg-white/20 rounded flex items-center justify-center transition">−</button>
                                    <span className="w-6 text-center font-bold">{item.quantity}</span>
                                    <button onClick={() => updateQty(item.id, item.quantity + 1, item.book_id, item.cart)}
                                        className="w-8 h-8 bg-white/10 hover:bg-white/20 rounded flex items-center justify-center transition">+</button>
                                    <button onClick={() => updateQty(item.id, 0, item.book_id, item.cart)}
                                        className="ml-2 text-red-400 hover:text-red-300 text-sm transition">Remove</button>
                                </div>
                            </div>
                        );
                    })}

                    <div className="glass-panel p-6 mt-4">
                        <div className="flex justify-between text-xl font-bold mb-6">
                            <span>Total</span>
                            <span>${total.toFixed(2)}</span>
                        </div>
                        <button
                            onClick={checkout}
                            className="w-full py-4 rounded-xl font-bold text-lg bg-gradient-to-r from-purple-500 to-blue-500 hover:shadow-[0_0_20px_rgba(59,130,246,0.4)] transition-all"
                        >
                            Checkout & Pay 💳
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
