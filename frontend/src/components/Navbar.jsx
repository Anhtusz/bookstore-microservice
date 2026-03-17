import { Link } from 'react-router-dom';
import { useContext } from 'react';
import { AppContext } from '../context/AppContext';

export default function Navbar({ toggleCart }) {
    const { user, cart } = useContext(AppContext);
    
    return (
        <nav className="sticky top-0 z-50 bg-slate-900/80 backdrop-blur-md border-b border-white/10 py-4">
            <div className="max-w-6xl mx-auto px-6 flex justify-between items-center">
                
                <Link to="/" className="text-2xl font-bold flex items-center gap-2 text-blue-500">
                    <span className="text-xl">📚</span> MicroBooks
                </Link>

                <div className="flex items-center gap-6">
                    {user ? (
                        <div className="px-4 py-1.5 bg-slate-800/70 border border-white/10 rounded-full text-sm">
                            👤 {user.name}
                        </div>
                    ) : (
                        <Link to="/login" className="text-sm font-semibold text-slate-300 hover:text-white transition">
                            Sign In
                        </Link>
                    )}

                    <Link to="/admin" className="text-sm font-semibold text-purple-400 hover:text-purple-300 transition">
                        Staff Panel
                    </Link>

                    <button onClick={toggleCart} className="relative p-2 text-slate-300 hover:text-blue-400 transition">
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" /></svg>
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
