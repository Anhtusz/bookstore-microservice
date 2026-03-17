import { useState, useContext } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { AppContext } from '../context/AppContext.jsx';

export default function AuthPage() {
    const [tab, setTab] = useState('register'); // 'login' | 'register'
    const { setUser, API_BASE, showToast, fetchCart } = useContext(AppContext);
    const navigate = useNavigate();

    // Register state
    const [regName, setRegName] = useState('');
    const [regEmail, setRegEmail] = useState('');
    const [regPassword, setRegPassword] = useState('');
    const [regConfirm, setRegConfirm] = useState('');

    // Login state
    const [loginEmail, setLoginEmail] = useState('');
    const [loginPassword, setLoginPassword] = useState('');
    const [loading, setLoading] = useState(false);

    const handleRegister = async (e) => {
        e.preventDefault();
        if (regPassword !== regConfirm) {
            showToast("Passwords do not match", "error");
            return;
        }
        if (regPassword.length < 6) {
            showToast("Password must be at least 6 characters", "error");
            return;
        }

        setLoading(true);
        try {
            const res = await axios.post(`${API_BASE}/customer/customers/`, {
                user_id: Math.floor(Math.random() * 99999),
                name: regName,
                email: regEmail,
                address: '',
                password: regPassword,
            });
            setUser({ id: res.data.id, name: res.data.name });
            showToast(`Welcome ${res.data.name}! Cart provisioned ✅`);
            fetchCart(res.data.id);
            navigate('/');
        } catch (err) {
            const msg = err.response?.data?.email?.[0] || err.response?.data?.detail || "Registration failed.";
            showToast(msg, "error");
        } finally {
            setLoading(false);
        }
    };

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const res = await axios.post(`${API_BASE}/customer/customers/login/`, {
                email: loginEmail,
                password: loginPassword,
            });
            setUser({ id: res.data.id, name: res.data.name });
            showToast(`Welcome back, ${res.data.name}! 👋`);
            fetchCart(res.data.id);
            navigate('/');
        } catch (err) {
            const msg = err.response?.data?.detail || "Login failed. Check your credentials.";
            showToast(msg, "error");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-[85vh] flex items-center justify-center px-4">
            <div className="w-full max-w-md">
                {/* Logo */}
                <div className="text-center mb-8">
                    <Link to="/" className="text-4xl font-extrabold text-blue-400">📚 MicroBooks</Link>
                    <p className="text-slate-400 text-sm mt-2">Your distributed bookstore</p>
                </div>

                {/* Card */}
                <div className="glass-panel p-8">
                    {/* Tabs */}
                    <div className="flex rounded-xl overflow-hidden border border-white/10 mb-8">
                        {[
                            { id: 'login', label: 'Sign In' },
                            { id: 'register', label: 'Register' },
                        ].map(t => (
                            <button
                                key={t.id}
                                onClick={() => setTab(t.id)}
                                className={`flex-1 py-3 text-sm font-bold transition-all ${
                                    tab === t.id
                                        ? 'bg-blue-600 text-white'
                                        : 'text-slate-400 hover:text-white hover:bg-white/5'
                                }`}
                            >
                                {t.label}
                            </button>
                        ))}
                    </div>

                    {/* LOGIN FORM */}
                    {tab === 'login' && (
                        <form onSubmit={handleLogin} className="flex flex-col gap-4">
                            <div>
                                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Email</label>
                                <input
                                    type="email" required value={loginEmail}
                                    onChange={e => setLoginEmail(e.target.value)}
                                    placeholder="you@example.com"
                                    className="input-field w-full"
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Password</label>
                                <input
                                    type="password" required value={loginPassword}
                                    onChange={e => setLoginPassword(e.target.value)}
                                    placeholder="••••••••"
                                    className="input-field w-full"
                                />
                            </div>
                            <button
                                type="submit" disabled={loading}
                                className="w-full py-3 bg-blue-600 hover:bg-blue-500 disabled:opacity-60 text-white font-bold rounded-xl transition mt-2 shadow-lg shadow-blue-500/20"
                            >
                                {loading ? 'Signing in...' : 'Sign In →'}
                            </button>
                            <p className="text-center text-slate-500 text-sm">
                                No account?{' '}
                                <button type="button" onClick={() => setTab('register')} className="text-blue-400 hover:underline">Register here</button>
                            </p>
                        </form>
                    )}

                    {/* REGISTER FORM */}
                    {tab === 'register' && (
                        <form onSubmit={handleRegister} className="flex flex-col gap-4">
                            <div>
                                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Full Name</label>
                                <input
                                    type="text" required value={regName}
                                    onChange={e => setRegName(e.target.value)}
                                    placeholder="John Doe"
                                    className="input-field w-full"
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Email</label>
                                <input
                                    type="email" required value={regEmail}
                                    onChange={e => setRegEmail(e.target.value)}
                                    placeholder="you@example.com"
                                    className="input-field w-full"
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Password</label>
                                <input
                                    type="password" required value={regPassword}
                                    onChange={e => setRegPassword(e.target.value)}
                                    placeholder="Min. 6 characters"
                                    className="input-field w-full"
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Confirm Password</label>
                                <input
                                    type="password" required value={regConfirm}
                                    onChange={e => setRegConfirm(e.target.value)}
                                    placeholder="Repeat password"
                                    className="input-field w-full"
                                />
                            </div>
                            <button
                                type="submit" disabled={loading}
                                className="w-full py-3 bg-blue-600 hover:bg-blue-500 disabled:opacity-60 text-white font-bold rounded-xl transition mt-2 shadow-lg shadow-blue-500/20"
                            >
                                {loading ? 'Creating account...' : 'Create Account →'}
                            </button>
                            <p className="text-center text-slate-500 text-sm">
                                Already have an account?{' '}
                                <button type="button" onClick={() => setTab('login')} className="text-blue-400 hover:underline">Sign in here</button>
                            </p>
                        </form>
                    )}
                </div>

                {/* Back link */}
                <p className="text-center mt-4 text-slate-500 text-sm">
                    <Link to="/" className="hover:text-slate-300 transition">← Back to Storefront</Link>
                </p>
            </div>
        </div>
    );
}
