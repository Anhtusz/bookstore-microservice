import { useState, useEffect, useContext } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { AppContext } from '../context/AppContext.jsx';

export default function StorefrontPage({ fetchBooks }) {
    const { user, fetchCart, API_BASE, showToast, cart, categories } = useContext(AppContext);
    const navigate = useNavigate();
    const [books, setBooks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedCategory, setSelectedCategory] = useState(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [recommendedBooks, setRecommendedBooks] = useState([]);
    const [catalogMap, setCatalogMap] = useState({}); // book_id -> category_id

    const loadBooks = async () => {
        setLoading(true);
        try {
            const [booksRes, recRes, catalogRes] = await Promise.all([
                axios.get(`${API_BASE}/book/books/`),
                axios.get(`${API_BASE}/recommender-ai/recommendations/suggest/`).catch(() => ({ data: [] })),
                axios.get(`${API_BASE}/catalog/items/`).catch(() => ({ data: [] }))
            ]);
            setBooks(booksRes.data);
            setRecommendedBooks(recRes.data);

            // Build a map: book_id -> category_id for fast filter/display
            const map = {};
            if (Array.isArray(catalogRes.data)) {
                catalogRes.data.forEach(item => {
                    map[item.book_id] = item.category; // category is the FK id
                });
            }
            setCatalogMap(map);

            if (fetchBooks) fetchBooks(booksRes.data);
        } catch {
            showToast("Failed to load catalog", "error");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { loadBooks(); }, []);

    const filteredBooks = books.filter(b => {
        const bookCategoryId = catalogMap[b.id];
        const matchesCategory = !selectedCategory || bookCategoryId === selectedCategory;
        const matchesSearch = b.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
                             b.author.toLowerCase().includes(searchQuery.toLowerCase());
        return matchesCategory && matchesSearch;
    });

    const requireAuth = () => {
        if (!user) {
            showToast("Please sign in to continue", "error");
            navigate('/login');
            return false;
        }
        return true;
    };

    const addToCart = async (bookId) => {
        if (!requireAuth()) return;

        const existing = cart.find(i => i.book_id === bookId);
        try {
            if (existing) {
                await axios.put(`${API_BASE}/cart/cart-items/${existing.id}/`, {
                    quantity: existing.quantity + 1,
                    cart: existing.cart,
                    book_id: existing.book_id,
                });
            } else {
                await axios.post(`${API_BASE}/cart/cart-items/`, {
                    cart: user.id, book_id: bookId, quantity: 1
                });
            }
            fetchCart(user.id);
            showToast("Added to cart 🛒");
        } catch {
            showToast("Failed to add to cart", "error");
        }
    };

    return (
        <div className="max-w-7xl mx-auto py-12 px-6">
            {/* Hero */}
            <div className="text-center mb-16">
                <h1 className="text-6xl font-black mb-6 tracking-tight">
                    Premium <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">Bookstore</span> Experience
                </h1>
                <p className="text-slate-400 text-xl max-w-2xl mx-auto leading-relaxed">
                    Explore curated collections from top authors worldwide. 
                    Manage your library and get personalized recommendations.
                </p>
            </div>

            {/* Search and Category Filter */}
            <div className="flex flex-col md:flex-row gap-6 mb-12 items-center justify-between glass-panel p-6">
                <div className="flex flex-wrap gap-2">
                    <button 
                        onClick={() => setSelectedCategory(null)}
                        className={`px-5 py-2.5 rounded-full text-sm font-bold transition-all ${
                            !selectedCategory 
                            ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30' 
                            : 'bg-white/5 text-slate-400 hover:text-white hover:bg-white/10'
                        }`}
                    >
                        All Books
                    </button>
                    {categories.map(cat => (
                        <button 
                            key={cat.id}
                            onClick={() => setSelectedCategory(cat.id)}
                            className={`px-5 py-2.5 rounded-full text-sm font-bold transition-all ${
                                selectedCategory === cat.id 
                                ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30' 
                                : 'bg-white/5 text-slate-400 hover:text-white hover:bg-white/10'
                            }`}
                        >
                            {cat.name}
                        </button>
                    ))}
                </div>
                
                <div className="relative w-full md:w-80">
                    <input 
                        type="text"
                        placeholder="Search title or author..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full bg-black/40 border border-white/10 rounded-2xl px-5 py-3 text-white focus:outline-none focus:border-blue-500 transition-all pl-12"
                    />
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 opacity-40">🔍</span>
                </div>
            </div>

            {/* Recommendations Ribbon */}
            {!loading && recommendedBooks.length > 0 && !searchQuery && !selectedCategory && (
                <div className="mb-16 animate-[fadeIn_0.5s_ease-out]">
                    <div className="flex items-center gap-3 mb-6">
                        <span className="text-3xl">✨</span>
                        <h2 className="text-2xl font-black bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">
                            Recommended For You
                        </h2>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                        {recommendedBooks.map((rb, idx) => {
                            const inCart = cart.find(c => c.book_id === rb.id);
                            return (
                                <div key={`rec-${rb.id}`} className="glass-panel p-4 flex gap-4 hover:border-blue-500/30 transition-all hover:-translate-y-1 relative overflow-hidden group">
                                    <div className="absolute -right-10 -top-10 w-32 h-32 bg-blue-500/10 blur-2xl rounded-full" />
                                    <div className="w-20 h-28 flex-shrink-0 bg-slate-800 rounded-lg overflow-hidden relative">
                                        {rb.image_url ? (
                                            <img src={rb.image_url} alt={rb.title} className="w-full h-full object-cover" />
                                        ) : (
                                            <div className="absolute inset-0 flex items-center justify-center text-3xl">📖</div>
                                        )}
                                    </div>
                                    <div className="flex flex-col justify-between py-1 relative z-10 w-full">
                                        <div>
                                            <Link to={`/book/${rb.id}`} className="font-bold text-sm leading-tight hover:text-blue-400 line-clamp-2 mb-1">{rb.title}</Link>
                                            <p className="text-[10px] text-slate-400 font-medium">by {rb.author}</p>
                                        </div>
                                        <div className="flex items-center justify-between mt-2">
                                            <span className="font-black text-blue-400 text-sm">${parseFloat(rb.price || 0).toFixed(2)}</span>
                                            <button 
                                                onClick={() => addToCart(rb.id)}
                                                disabled={rb.stock <= 0}
                                                className={`w-8 h-8 rounded-full flex items-center justify-center text-xs transition-colors ${
                                                    inCart ? 'bg-blue-600 text-white' : rb.stock <= 0 ? 'bg-white/5 text-slate-600' : 'bg-white/10 hover:bg-white hover:text-black text-white'
                                                }`}
                                            >
                                                {inCart ? '✓' : rb.stock <= 0 ? '✕' : '+'}
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Book Grid */}
            {loading ? (
                <div className="flex flex-col justify-center items-center h-80 gap-4">
                    <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
                    <p className="text-slate-500 font-medium animate-pulse">Syncing catalog...</p>
                </div>
            ) : filteredBooks.length === 0 ? (
                <div className="glass-panel py-32 text-center flex flex-col items-center gap-4">
                    <span className="text-6xl grayscale opacity-30">📚</span>
                    <div>
                        <h3 className="text-xl font-bold">No results found</h3>
                        <p className="text-slate-500">Try adjusting your filters or search query.</p>
                    </div>
                </div>
            ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
                    {filteredBooks.map((b, i) => {
                        const inCart = cart.find(c => c.book_id === b.id);
                        const isOutOfStock = b.stock <= 0;
                        const bookCategoryId = catalogMap[b.id];
                        const cat = categories.find(c => c.id === bookCategoryId);
                        const categoryName = cat ? cat.name : null;
                        
                        return (
                            <div
                                key={b.id}
                                className="glass-panel group relative flex flex-col p-2 hover:border-blue-500/40 transition-all duration-500 hover:-translate-y-2 overflow-hidden"
                                style={{ animation: `fadeIn 0.5s ease-out ${i * 0.05}s both` }}
                            >
                                {/* Thumbnail-ish Area */}
                                <div className="aspect-[4/5] w-full bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl overflow-hidden relative mb-4">
                                    {b.image_url ? (
                                        <img src={b.image_url} alt={b.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                                    ) : (
                                        <div className="absolute inset-0 flex flex-col items-center justify-center bg-blue-900/40 text-blue-300">
                                            <span className="text-6xl mb-2 group-hover:scale-110 transition-transform duration-500">📖</span>
                                        </div>
                                    )}
                                    <div className="absolute top-3 left-3 flex flex-col gap-2">
                                        {categoryName && (
                                            <span className="bg-blue-600/90 backdrop-blur-md text-[10px] font-black uppercase tracking-widest px-2.5 py-1 rounded-full text-white">
                                                {categoryName}
                                            </span>
                                        )}
                                        <span className={`text-[10px] font-black uppercase tracking-widest px-2.5 py-1 rounded-full backdrop-blur-md ${
                                            isOutOfStock ? 'bg-red-500/80 text-white' : 'bg-emerald-500/80 text-white'
                                        }`}>
                                            {b.stock_status || (isOutOfStock ? "Out of Stock" : "In Stock")}
                                        </span>
                                    </div>
                                    <div className="absolute inset-0 bg-blue-600/0 group-hover:bg-blue-600/10 transition-colors" />
                                </div>

                                <div className="px-4 pb-4 flex flex-col flex-1">
                                    <div className="mb-4">
                                        <Link to={`/book/${b.id}`} className="text-xl font-bold leading-tight hover:text-blue-400 transition-colors mb-1 block">
                                            {b.title}
                                        </Link>
                                        <p className="text-slate-400 text-sm font-medium">by {b.author}</p>
                                    </div>

                                    <div className="mt-auto flex items-center justify-between gap-4">
                                        <div className="flex flex-col">
                                            <span className="text-[10px] uppercase font-black text-slate-500 tracking-wider">Price</span>
                                            <span className="text-2xl font-black">${parseFloat(b.price || 0).toFixed(2)}</span>
                                        </div>
                                        
                                        <button
                                            onClick={() => addToCart(b.id)}
                                            disabled={isOutOfStock}
                                            className={`flex-1 h-12 rounded-2xl font-black transition-all transform active:scale-95 ${
                                                inCart
                                                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/40'
                                                    : isOutOfStock 
                                                        ? 'bg-white/5 text-slate-600 cursor-not-allowed border border-white/5'
                                                        : 'bg-white/5 border border-white/10 hover:bg-white text-slate-200 hover:text-black'
                                            }`}
                                        >
                                            {inCart ? `+ Add More (${inCart.quantity})` : isOutOfStock ? 'Sold Out' : 'Add to Cart'}
                                        </button>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
            
            <style dangerouslySetInnerHTML={{ __html: `
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(20px); }
                    to { opacity: 1; transform: translateY(0); }
                }
            `}} />
        </div>
    );
}
