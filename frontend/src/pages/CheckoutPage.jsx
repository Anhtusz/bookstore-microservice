import { useState, useContext, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { AppContext } from '../context/AppContext.jsx';

export default function CheckoutPage() {
    const { user, cart, API_BASE, showToast, fetchCart } = useContext(AppContext);
    const navigate = useNavigate();
    
    const [name, setName] = useState(user?.name || '');
    const [phone, setPhone] = useState('');
    const [address, setAddress] = useState('');
    const [paymentMethod, setPaymentMethod] = useState('COD');
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (!user || cart.length === 0) {
            navigate('/');
        }
    }, [user, cart, navigate]);

    const handleCheckout = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const res = await axios.post(`${API_BASE}/order/orders/`, {
                customer_id: user.id,
                customer_name: name,
                customer_phone: phone,
                shipping_address: address,
                payment_method: paymentMethod
            });
            if (res.data.status === 'PAID') {
                showToast("Payment successful! Order confirmed. 💳", "success");
            } else {
                showToast("Order placed successfully! Waiting for confirmation.", "success");
            }
            fetchCart(user.id);
            navigate('/');
        } catch (err) {
            showToast("Checkout failed. Please try again.", "error");
        } finally {
            setLoading(false);
        }
    };

    const subtotal = cart.reduce((acc, item) => acc + (item.price || 10) * item.quantity, 0);

    if (!user || cart.length === 0) return null;

    return (
        <div className="max-w-4xl mx-auto py-16 px-6">
            <h1 className="text-4xl font-black mb-10 text-center">Complete Your Purchase</h1>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
                {/* Form */}
                <div className="glass-panel p-8">
                    <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
                        <span className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-sm">1</span>
                        Shipping Information
                    </h3>
                    <form onSubmit={handleCheckout} className="flex flex-col gap-5">
                        <div className="space-y-1">
                            <label className="text-xs font-black uppercase text-slate-500 tracking-widest pl-1">Full Name</label>
                            <input 
                                required value={name} onChange={e => setName(e.target.value)}
                                className="input-field w-full" placeholder="John Doe"
                            />
                        </div>
                        <div className="space-y-1">
                            <label className="text-xs font-black uppercase text-slate-500 tracking-widest pl-1">Phone Number</label>
                            <input 
                                required value={phone} onChange={e => setPhone(e.target.value)}
                                className="input-field w-full" placeholder="+84 123 456 789"
                            />
                        </div>
                        <div className="space-y-1">
                            <label className="text-xs font-black uppercase text-slate-500 tracking-widest pl-1">Shipping Address</label>
                            <textarea 
                                required value={address} onChange={e => setAddress(e.target.value)}
                                className="input-field w-full min-h-[100px] py-3" placeholder="Street name, City, Country"
                            />
                        </div>

                        <h3 className="text-xl font-bold mt-4 mb-2 flex items-center gap-2">
                            <span className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-sm">2</span>
                            Payment Method
                        </h3>
                        <div className="grid grid-cols-2 gap-4">
                            {[
                                { id: 'BANK', label: 'Credit Card / Bank', icon: '💳' },
                                { id: 'COD', label: 'Cash on Delivery', icon: '💵' },
                            ].map(m => (
                                <button 
                                    key={m.id} type="button"
                                    onClick={() => setPaymentMethod(m.id)}
                                    className={`p-4 rounded-2xl border-2 flex flex-col items-center gap-2 transition-all ${
                                        paymentMethod === m.id 
                                        ? 'border-blue-500 bg-blue-500/10 shadow-[0_0_20px_rgba(59,130,246,0.2)]' 
                                        : 'border-white/5 bg-white/5 hover:border-white/10'
                                    }`}
                                >
                                    <span className="text-2xl">{m.icon}</span>
                                    <span className="text-sm font-bold">{m.label}</span>
                                </button>
                            ))}
                        </div>

                        {paymentMethod === 'BANK' && (
                            <div className="p-6 mt-2 border border-blue-500/30 bg-blue-500/5 rounded-2xl flex flex-col gap-4 animate-[fadeIn_0.3s_ease-out]">
                                <div className="flex justify-between items-center mb-2">
                                    <h4 className="font-bold text-sm uppercase text-slate-300 tracking-wider">Secure Payment</h4>
                                    <span className="text-xs font-black text-blue-400 bg-blue-500/10 px-2 py-1 rounded">TEST MODE</span>
                                </div>
                                <div className="space-y-1">
                                    <label className="text-xs font-black uppercase text-slate-500 tracking-widest pl-1">Card Number</label>
                                    <input type="text" placeholder="0000 0000 0000 0000" maxLength="19" className="input-field w-full font-mono text-lg tracking-widest" required />
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-1">
                                        <label className="text-xs font-black uppercase text-slate-500 tracking-widest pl-1">Expiry</label>
                                        <input type="text" placeholder="MM/YY" maxLength="5" className="input-field w-full font-mono" required />
                                    </div>
                                    <div className="space-y-1">
                                        <label className="text-xs font-black uppercase text-slate-500 tracking-widest pl-1">CVV</label>
                                        <input type="password" placeholder="***" maxLength="3" className="input-field w-full font-mono" required />
                                    </div>
                                </div>
                                <p className="text-[10px] text-slate-500 uppercase font-black text-center mt-2 flex items-center justify-center gap-1">
                                    🔒 End-to-end encrypted
                                </p>
                            </div>
                        )}

                        <button 
                            disabled={loading}
                            className="w-full mt-6 py-4 rounded-2xl bg-gradient-to-r from-blue-600 to-purple-600 text-white font-black text-lg hover:shadow-[0_0_30px_rgba(59,130,246,0.5)] transition-all disabled:opacity-50 flex items-center justify-center gap-3"
                        >
                            {loading ? (
                                <>
                                    <span className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                                    {paymentMethod === 'BANK' ? 'Processing Payment...' : 'Confirming...'}
                                </>
                            ) : (
                                paymentMethod === 'BANK' ? 'Pay Now →' : 'Confirm Order →'
                            )}
                        </button>
                    </form>
                </div>

                {/* Summary */}
                <div className="h-fit lg:sticky top-24">
                    <div className="glass-panel p-8 border-blue-500/20">
                        <h3 className="text-xl font-bold mb-6">Order Summary</h3>
                        <div className="space-y-4 mb-6">
                            {cart.map(item => (
                                <div key={item.id} className="flex justify-between items-center text-sm">
                                    <div className="flex flex-col">
                                        <span className="font-bold">{item.title || `Book #${item.book_id}`}</span>
                                        <span className="text-slate-500">Qty: {item.quantity}</span>
                                    </div>
                                    <span className="font-mono">${((item.price || 10) * item.quantity).toFixed(2)}</span>
                                </div>
                            ))}
                        </div>
                        <div className="border-t border-white/10 pt-6 space-y-3">
                            <div className="flex justify-between text-slate-400">
                                <span>Subtotal</span>
                                <span>${subtotal.toFixed(2)}</span>
                            </div>
                            <div className="flex justify-between text-slate-400">
                                <span>Shipping</span>
                                <span>Free</span>
                            </div>
                            <div className="flex justify-between text-2xl font-black pt-2">
                                <span>Total</span>
                                <span className="text-blue-400">${subtotal.toFixed(2)}</span>
                            </div>
                        </div>
                    </div>
                    <p className="text-center text-xs text-slate-500 mt-6 px-4">
                        By placing your order, you agree to our terms of service and privacy policy. 
                        Orders are typically processed within 24 hours.
                    </p>
                </div>
            </div>
        </div>
    );
}
