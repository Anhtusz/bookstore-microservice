import { useState, useEffect, useContext } from 'react';
import { AppContext } from '../context/AppContext.jsx';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

export default function OrdersPage() {
    const { user, API_BASE, showToast, booksMap = {} } = useContext(AppContext);
    const navigate = useNavigate();
    
    const [orders, setOrders] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!user) {
            navigate('/login');
            return;
        }

        const fetchOrders = async () => {
            try {
                const res = await axios.get(`${API_BASE}/order/orders/?customer_id=${user.id}`);
                setOrders(res.data);
            } catch (err) {
                showToast("Failed to fetch order history", "error");
            } finally {
                setLoading(false);
            }
        };

        fetchOrders();
    }, [user, navigate, API_BASE]);

    const getStatusStyle = (status) => {
        switch (status) {
            case 'PAID':
            case 'SHIPPING': return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
            case 'WAITING_CONFIRMATION': return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20';
            case 'PAYMENT_FAILED': return 'bg-red-500/10 text-red-400 border-red-500/20';
            default: return 'bg-slate-500/10 text-slate-400 border-slate-500/20';
        }
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center h-screen">
                <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto py-12 px-6">
            <h1 className="text-4xl font-black mb-10">My Orders</h1>

            {orders.length === 0 ? (
                <div className="glass-panel py-24 text-center text-slate-500 flex flex-col items-center gap-4">
                    <span className="text-6xl">📦</span>
                    <p className="text-lg">You haven't placed any orders yet.</p>
                </div>
            ) : (
                <div className="space-y-8">
                    {orders.map(order => (
                        <div key={order.id} className="glass-panel p-6 sm:p-8 animate-[fadeIn_0.4s_ease-out]">
                            {/* Order Header */}
                            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6 pb-6 border-b border-white/10">
                                <div>
                                    <h3 className="font-black text-xl mb-1">Order #{order.id}</h3>
                                    <p className="text-slate-500 text-sm font-mono">{new Date(order.created_at).toLocaleString()}</p>
                                </div>
                                <div className={`px-4 py-1.5 rounded-full border text-xs font-black uppercase tracking-widest ${getStatusStyle(order.status)}`}>
                                    {order.status.replace('_', ' ')}
                                </div>
                            </div>

                            {/* Order Details */}
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-8 mb-6">
                                <div>
                                    <h4 className="text-[10px] font-black uppercase text-slate-500 tracking-widest mb-2">Shipping Information</h4>
                                    <div className="text-sm bg-white/5 p-4 rounded-xl space-y-1 text-slate-300">
                                        <p className="font-bold text-white">{order.customer_name}</p>
                                        <p>{order.customer_phone}</p>
                                        <p className="pt-2">{order.shipping_address}</p>
                                    </div>
                                </div>
                                <div>
                                    <h4 className="text-[10px] font-black uppercase text-slate-500 tracking-widest mb-2">Payment</h4>
                                    <div className="text-sm bg-white/5 p-4 rounded-xl flex items-center gap-3 text-slate-300">
                                        <span className="text-2xl">{order.payment_method === 'BANK' ? '💳' : '💵'}</span>
                                        <span className="font-bold tracking-wide">{order.payment_method === 'BANK' ? 'Credit Card / Bank' : 'Cash on Delivery'}</span>
                                    </div>
                                </div>
                            </div>

                            {/* Order Items */}
                            <h4 className="text-[10px] font-black uppercase text-slate-500 tracking-widest mb-4">Items Summary</h4>
                            <div className="space-y-3">
                                {order.items.map(item => (
                                    <div key={item.id} className="flex justify-between items-center text-sm py-2 px-4 rounded-lg bg-black/20">
                                        <div className="flex items-center gap-4">
                                            <span className="w-8 h-8 rounded bg-white/10 flex items-center justify-center font-bold text-xs">{item.quantity}x</span>
                                            <span className="font-bold text-slate-200">Book #{item.book_id}</span>
                                        </div>
                                        <span className="font-mono text-slate-400">${item.price}</span>
                                    </div>
                                ))}
                            </div>

                            {/* Order Total */}
                            <div className="mt-6 pt-6 border-t border-white/10 flex justify-between items-center">
                                <span className="text-sm font-black uppercase text-slate-500 tracking-widest">Total Amount</span>
                                <span className="text-2xl font-black text-blue-400">${order.total_price}</span>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
