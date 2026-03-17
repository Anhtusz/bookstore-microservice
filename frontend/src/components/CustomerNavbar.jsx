import { Link, useNavigate } from 'react-router-dom';
import { useContext } from 'react';
import { AppContext } from '../context/AppContext.jsx';

export default function CustomerNavbar({ toggleCart }) {
    const { user, cart, logout } = useContext(AppContext);
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/');
    };

    return (
        <nav className="sticky top-0 z-50 bg-slate-900/80 backdrop-blur-md border-b border-white/10">
            <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">

                <Link to="/" className="text-2xl font-bold flex items-center gap-2 text-blue-400">
                    <span>📚</span> MicroBooks
                </Link>

                <div className="flex items-center gap-4">
                    {user ? (
                        <div className="flex items-center gap-4">
                            <span className="text-sm font-bold text-slate-400 hidden sm:block">👤 {user.name}</span>
                            <Link to="/orders" className="text-sm font-semibold text-slate-300 hover:text-blue-400 transition">
                                My Orders
                            </Link>
                            <Link to="/cart" className="text-sm font-semibold text-slate-300 hover:text-blue-400 transition">
                                My Cart {cart.length > 0 && <span className="ml-1 bg-red-500 text-white text-xs px-1.5 py-0.5 rounded-full">{cart.length}</span>}
                            </Link>
                            <button
                                onClick={handleLogout}
                                className="text-sm font-semibold text-slate-400 hover:text-red-400 border border-white/10 hover:border-red-400/40 px-4 py-1.5 rounded-full hover:bg-red-400/10 transition"
                            >
                                Logout
                            </button>
                        </div>
                    ) : (
                        <button
                            onClick={() => navigate('/login')}
                            className="text-sm font-semibold text-blue-400 hover:text-blue-300 border border-blue-400/40 px-4 py-1.5 rounded-full hover:bg-blue-400/10 transition"
                        >
                            Sign In / Register
                        </button>
                    )}

                    {/* Cart icon button */}
                    <button onClick={toggleCart} className="relative p-2 text-slate-300 hover:text-blue-400 transition">
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
                        </svg>
                        {cart.length > 0 && (
                            <span className="absolute top-0 right-0 bg-red-500 text-white text-[10px] w-4 h-4 rounded-full flex items-center justify-center">
                                {cart.length}
                            </span>
                        )}
                    </button>
                </div>
            </div>
        </nav>
    );
}
