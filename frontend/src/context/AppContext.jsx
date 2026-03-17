import { createContext, useState, useEffect } from 'react';
import axios from 'axios';

export const AppContext = createContext();

export const AppProvider = ({ children }) => {
    // Restore user from localStorage to survive page refresh
    const [user, setUserState] = useState(() => {
        try {
            const saved = localStorage.getItem('mb_user');
            return saved ? JSON.parse(saved) : null;
        } catch { return null; }
    });
    const [cart, setCart] = useState([]);
    const [categories, setCategories] = useState([]);
    const [toast, setToast] = useState({ message: '', type: '', visible: false });

    const API_BASE = 'http://localhost:8000/api';

    // Wrap setUser to also persist to localStorage
    const setUser = (userData) => {
        if (userData) {
            localStorage.setItem('mb_user', JSON.stringify(userData));
        } else {
            localStorage.removeItem('mb_user');
        }
        setUserState(userData);
    };

    const logout = () => {
        setUser(null);
        setCart([]);
    };

    const showToast = (message, type = 'success') => {
        setToast({ message, type, visible: true });
        setTimeout(() => setToast({ message: '', type: '', visible: false }), 4000);
    };

    const fetchCart = async (userId) => {
        try {
            const res = await axios.get(`${API_BASE}/cart/carts/${userId}/`);
            setCart(res.data);
        } catch (error) {
            console.error(error);
        }
    };

    const fetchCategories = async () => {
        try {
            const res = await axios.get(`${API_BASE}/catalog/categories/`);
            setCategories(res.data);
        } catch (error) {
            console.error("Failed to fetch categories");
        }
    };

    useEffect(() => {
        fetchCategories();
    }, []);

    useEffect(() => {
        if (user) {
            fetchCart(user.id);
        } else {
            setCart([]);
        }
    }, [user]);

    return (
        <AppContext.Provider value={{
            user, setUser, logout,
            cart, setCart, fetchCart,
            categories, fetchCategories,
            toast, showToast,
            API_BASE
        }}>
            {children}
            
            {/* Global Toast */}
            <div className={`fixed bottom-5 left-1/2 -translate-x-1/2 px-6 py-3 rounded-full border shadow-2xl z-50 transition-all duration-300 flex items-center gap-2
                ${toast.visible ? 'translate-y-0 opacity-100' : 'translate-y-20 opacity-0'}
                ${toast.type === 'success' ? 'border-emerald-500 bg-slate-800 text-white' : 'border-red-500 bg-slate-800 text-white'}
            `}>
                {toast.message}
            </div>
        </AppContext.Provider>
    );
};
