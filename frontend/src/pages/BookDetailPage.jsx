import { useState, useEffect, useContext } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { AppContext } from '../context/AppContext.jsx';

export default function BookDetailPage() {
    const { id } = useParams();
    const { user, API_BASE, showToast, cart, fetchCart } = useContext(AppContext);
    const navigate = useNavigate();
    
    const [book, setBook] = useState(null);
    const [reviews, setReviews] = useState([]);
    const [loading, setLoading] = useState(true);
    const [newComment, setNewComment] = useState('');
    const [newRating, setNewRating] = useState(5);
    const [recommendedBooks, setRecommendedBooks] = useState([]);

    const loadData = async () => {
        setLoading(true);
        try {
            const [bookRes, reviewsRes, recRes] = await Promise.all([
                axios.get(`${API_BASE}/book/books/${id}/`),
                axios.get(`${API_BASE}/comment-rate/reviews/?book_id=${id}`),
                axios.get(`${API_BASE}/recommender-ai/recommendations/suggest/`).catch(() => ({ data: [] }))
            ]);
            setBook(bookRes.data);
            setReviews(reviewsRes.data);
            setRecommendedBooks(recRes.data.filter(r => r.id !== parseInt(id)));
        } catch {
            showToast("Failed to load book details", "error");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { loadData(); }, [id]);

    const addToCart = async () => {
        if (!user) {
            showToast("Please sign in to add to cart", "error");
            navigate('/login');
            return;
        }

        const existing = cart.find(i => i.book_id === book.id);
        try {
            if (existing) {
                await axios.put(`${API_BASE}/cart/cart-items/${existing.id}/`, {
                    quantity: existing.quantity + 1,
                    cart: existing.cart,
                    book_id: existing.book_id,
                });
            } else {
                await axios.post(`${API_BASE}/cart/cart-items/`, {
                    cart: user.id, book_id: book.id, quantity: 1
                });
            }
            fetchCart(user.id);
            showToast("Added to cart 🛒");
        } catch {
            showToast("Failed to add to cart", "error");
        }
    };

    const submitReview = async (e) => {
        e.preventDefault();
        if (!user) {
            showToast("Please sign in to review", "error");
            navigate('/login');
            return;
        }

        try {
            await axios.post(`${API_BASE}/comment-rate/reviews/`, {
                book_id: book.id,
                customer_id: user.id,
                rating: newRating,
                comment: newComment
            });
            showToast("Review submitted ⭐");
            setNewComment('');
            loadData();
        } catch {
            showToast("Failed to submit review", "error");
        }
    };

    if (loading) return (
        <div className="flex justify-center items-center h-screen">
            <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
    );

    if (!book) return <div className="text-center py-20 text-2xl font-bold">Book not found</div>;

    const avgRating = reviews.length > 0 
        ? (reviews.reduce((acc, r) => acc + r.rating, 0) / reviews.length).toFixed(1)
        : null;

    return (
        <div className="max-w-6xl mx-auto py-12 px-6">
            <Link to="/" className="text-slate-500 hover:text-white transition-colors mb-8 inline-block">← Back to Catalog</Link>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-12 mb-16">
                {/* Book Cover / Hero Section */}
                <div className="glass-panel aspect-square flex items-center justify-center text-[10rem] relative overflow-hidden group">
                    <div className="absolute inset-0 bg-gradient-to-br from-blue-600/10 to-purple-600/10" />
                    {book.image_url ? (
                        <img src={book.image_url} alt={book.title} className="w-full h-full object-cover relative z-10" />
                    ) : (
                        <span className="group-hover:scale-110 transition-transform duration-700 select-none relative z-10 text-[10rem]">📖</span>
                    )}
                    {book.category_id && categories.find(c => c.id === book.category_id) && (
                        <div className="absolute top-6 left-6 bg-blue-600 px-4 py-1.5 rounded-full text-xs font-black uppercase tracking-widest leading-none">
                            {categories.find(c => c.id === book.category_id).name}
                        </div>
                    )}
                </div>

                {/* Details */}
                <div className="flex flex-col">
                    <div className="mb-8">
                        <h1 className="text-5xl font-black mb-2 tracking-tight">{book.title}</h1>
                        <p className="text-slate-400 text-xl font-medium">by {book.author}</p>
                    </div>

                    <div className="flex items-center gap-6 mb-8">
                        <div className="flex flex-col">
                            <span className="text-[10px] uppercase font-black text-slate-500 tracking-widest mb-1">Rating</span>
                            <div className="flex items-center gap-2">
                                <span className="text-3xl font-black text-yellow-400">{avgRating || 'N/A'}</span>
                                <div className="flex flex-col text-[10px] font-bold text-slate-500 leading-tight">
                                    <span>{reviews.length}</span>
                                    <span>REVIEWS</span>
                                </div>
                            </div>
                        </div>
                        <div className="h-10 w-px bg-white/10" />
                        <div className="flex flex-col">
                            <span className="text-[10px] uppercase font-black text-slate-500 tracking-widest mb-1">Availability</span>
                            <span className={`text-xl font-black ${book.stock > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                {book.stock > 0 ? `In Stock (${book.stock})` : 'Out of Stock'}
                            </span>
                        </div>
                    </div>

                    <p className="text-slate-300 text-lg leading-relaxed mb-10 pb-10 border-b border-white/10">
                        {book.description || "No description available for this book yet. Check back soon for more details."}
                    </p>

                    <div className="flex items-center gap-6">
                        <div className="flex flex-col">
                            <span className="text-[10px] uppercase font-black text-slate-500 tracking-widest mb-1">Price</span>
                            <span className="text-4xl font-black text-blue-400">${parseFloat(book.price || 0).toFixed(2)}</span>
                        </div>
                        <button 
                            onClick={addToCart}
                            disabled={book.stock <= 0}
                            className="flex-1 h-16 rounded-2xl bg-gradient-to-r from-blue-600 to-purple-600 text-white font-black text-xl hover:shadow-[0_0_40px_rgba(59,130,246,0.4)] transition-all transform active:scale-95 disabled:opacity-50"
                        >
                            Add to Cart 🛒
                        </button>
                    </div>
                </div>
            </div>

            {/* Reviews Section */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
                <div className="lg:col-span-2 space-y-8">
                    <h2 className="text-3xl font-black mb-6">User Reviews</h2>
                    {reviews.length === 0 ? (
                        <div className="glass-panel py-16 text-center text-slate-500 italic">
                            No reviews yet. Be the first to share your thoughts!
                        </div>
                    ) : (
                        reviews.map(r => (
                            <div key={r.id} className="glass-panel p-6 border-white/5 bg-white/2 hover:border-white/20 transition-all">
                                <div className="flex justify-between items-start mb-4">
                                    <div className="flex items-center gap-2">
                                        <div className="w-10 h-10 rounded-full bg-blue-600/20 flex items-center justify-center text-blue-400 font-bold">
                                            {r.customer_id % 10}
                                        </div>
                                        <div>
                                            <p className="font-bold text-sm">Customer #{r.customer_id}</p>
                                            <p className="text-[10px] text-slate-500 font-black uppercase tracking-widest">Verified Purchase</p>
                                        </div>
                                    </div>
                                    <div className="flex text-yellow-500 text-xs">
                                        {[...Array(5)].map((_, i) => (
                                            <span key={i}>{i < r.rating ? '★' : '☆'}</span>
                                        ))}
                                    </div>
                                </div>
                                <p className="text-slate-300 italic">"{r.comment}"</p>
                            </div>
                        ))
                    )}
                </div>

                {/* Add Review */}
                <div className="h-fit">
                    <div className="glass-panel p-6 border-blue-500/20 sticky top-24">
                        <h3 className="text-xl font-bold mb-6">Write a Review</h3>
                        <form onSubmit={submitReview} className="space-y-5">
                            <div className="flex flex-col gap-2">
                                <label className="text-[10px] font-black uppercase text-slate-500 tracking-widest">Star Rating</label>
                                <div className="flex gap-2">
                                    {[1, 2, 3, 4, 5].map(s => (
                                        <button 
                                            key={s} type="button" onClick={() => setNewRating(s)}
                                            className={`text-2xl transition-all hover:scale-125 ${newRating >= s ? 'text-yellow-400' : 'text-slate-700'}`}
                                        >
                                            ★
                                        </button>
                                    ))}
                                </div>
                            </div>
                            <div className="flex flex-col gap-2">
                                <label className="text-[10px] font-black uppercase text-slate-500 tracking-widest">Your Comment</label>
                                <textarea 
                                    required value={newComment} onChange={e => setNewComment(e.target.value)}
                                    placeholder="Tell us what you loved about this book..."
                                    className="input-field min-h-[120px] py-3 text-sm"
                                />
                            </div>
                            <button className="w-full py-4 rounded-xl bg-white/10 hover:bg-white text-slate-200 hover:text-black font-black transition-all">
                                Post Review
                            </button>
                        </form>
                    </div>
                </div>
            </div>

            {/* Recommendations */}
            {recommendedBooks.length > 0 && (
                <div className="mt-16 pt-12 border-t border-white/10">
                    <div className="flex items-center gap-3 mb-8">
                        <span className="text-3xl">✨</span>
                        <h2 className="text-2xl font-black bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">
                            You May Also Like
                        </h2>
                    </div>
                    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-6">
                        {recommendedBooks.slice(0, 4).map(rb => (
                            <Link
                                key={rb.id}
                                to={`/book/${rb.id}`}
                                className="glass-panel p-4 flex flex-col gap-3 hover:border-blue-500/30 transition-all hover:-translate-y-1 group"
                            >
                                <div className="aspect-[3/4] rounded-xl bg-slate-800 overflow-hidden relative">
                                    {rb.image_url ? (
                                        <img src={rb.image_url} alt={rb.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                                    ) : (
                                        <div className="absolute inset-0 flex items-center justify-center text-5xl">📖</div>
                                    )}
                                </div>
                                <div>
                                    <p className="font-bold text-sm leading-tight group-hover:text-blue-400 transition-colors line-clamp-2">{rb.title}</p>
                                    <p className="text-xs text-slate-400 mt-1">by {rb.author}</p>
                                    <p className="font-black text-blue-400 text-sm mt-2">${parseFloat(rb.price || 0).toFixed(2)}</p>
                                </div>
                            </Link>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
