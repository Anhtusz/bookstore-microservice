import { useContext } from 'react';
import { AppContext } from '../context/AppContext';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

export default function CartDrawer({ isOpen, toggleCart, booksMap }) {
    const { user, cart, fetchCart, API_BASE, showToast } = useContext(AppContext);
    const navigate = useNavigate();

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
        toggleCart();
        navigate('/checkout');
    };

    let total = 0;

    return (
        <>
            {/* Backdrop */}
            <div onClick={toggleCart} className={`fixed inset-0 bg-black/50 backdrop-blur-sm z-50 transition-opacity duration-300 ${isOpen ? 'opacity-100 visible' : 'opacity-0 invisible'}`} />
            
            {/* Drawer */}
            <div className={`fixed top-0 right-0 h-full w-[400px] max-w-full bg-slate-900 border-l border-white/10 z-[60] flex flex-col transition-transform duration-400 ease-[cubic-bezier(0.16,1,0.3,1)] ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}>
                
                <div className="p-6 border-b border-white/10 flex justify-between items-center">
                    <h3 className="text-xl font-bold">Your Cart</h3>
                    <button onClick={toggleCart} className="text-slate-400 hover:text-white pb-1 text-2xl">&times;</button>
                </div>

                <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-4">
                    {!user ? (
                        <div className="flex flex-col items-center justify-center h-full text-slate-500 gap-4">
                            <span className="text-5xl">🛒</span>
                            <p>Register to unlock the cart</p>
                        </div>
                    ) : cart.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-full text-slate-500 gap-4">
                            <span className="text-5xl">🛍️</span>
                            <p>Your cart is empty</p>
                        </div>
                    ) : (
                        cart.map(item => {
                            const book = booksMap[item.book_id] || { title: `Book #${item.book_id}`, price: 10.0 };
                            const price = parseFloat(book.price || 10.0);
                            total += price * item.quantity;

                            return (
                                <div key={item.id} className="bg-white/5 border border-white/10 p-4 rounded-xl flex justify-between items-center group hover:border-blue-500/50 transition">
                                    <div>
                                        <h4 className="font-semibold text-sm mb-1">{book.title}</h4>
                                        <p className="text-blue-400 font-bold text-sm">${price.toFixed(2)}</p>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <button onClick={() => updateQty(item.id, item.quantity - 1, item.book_id, item.cart)} className="w-8 h-8 rounded bg-white/10 hover:bg-white/20 flex items-center justify-center">-</button>
                                        <span className="w-4 text-center text-sm">{item.quantity}</span>
                                        <button onClick={() => updateQty(item.id, item.quantity + 1, item.book_id, item.cart)} className="w-8 h-8 rounded bg-white/10 hover:bg-white/20 flex items-center justify-center">+</button>
                                    </div>
                                </div>
                            );
                        })
                    )}
                </div>

                <div className="p-6 border-t border-white/10 bg-black/20">
                    <div className="flex justify-between items-center mb-6 text-xl font-bold">
                        <span>Total</span>
                        <span>${total.toFixed(2)}</span>
                    </div>
                    <button 
                        onClick={checkout}
                        disabled={!user || cart.length === 0}
                        className="w-full py-4 rounded-xl font-bold bg-gradient-to-r from-purple-500 to-blue-500 hover:shadow-[0_0_20px_rgba(59,130,246,0.5)] disabled:opacity-50 disabled:grayscale transition-all"
                    >
                        Checkout & Pay
                    </button>
                </div>
            </div>
        </>
    );
}
