import { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { AppContext } from '../context/AppContext';

export default function HomePage({ booksMap, fetchBooks }) {
    const { user, fetchCart, API_BASE, showToast, cart } = useContext(AppContext);
    const [books, setBooks] = useState([]);
    
    // Rating State
    const [ratingModal, setRatingModal] = useState({ visible: false, bookId: null, title: '' });
    const [rating, setRating] = useState(5);
    const [comment, setComment] = useState('');

    useEffect(() => {
        loadBooks();
    }, []);

    const loadBooks = async () => {
        try {
            const res = await axios.get(`${API_BASE}/book/books/`);
            setBooks(res.data);
            if(fetchBooks) fetchBooks(res.data); // Update top level map
        } catch(e) { showToast("Failed to load catalog", "error"); }
    };

    const addToCart = async (bookId) => {
        if (!user) {
            showToast("Please Sign In to use the cart", "error");
            return;
        }

        const existing = cart.find(i => i.book_id === bookId);
        try {
            if (existing) {
                await axios.put(`${API_BASE}/cart/cart-items/${existing.id}/`, {
                    quantity: existing.quantity + 1, cart: existing.cart, book_id: existing.book_id
                });
            } else {
                await axios.post(`${API_BASE}/cart/cart-items/`, {
                    cart: user.id, book_id: bookId, quantity: 1
                });
            }
            fetchCart(user.id);
            showToast("Book added to cart");
        } catch(e) {
            showToast("Failed to update cart", "error");
        }
    };

    const submitRating = async () => {
        if (!user) {
            showToast("Please sign in to rate", "error");
            return;
        }
        try {
            await axios.post(`${API_BASE}/comment/reviews/`, {
                book_id: ratingModal.bookId,
                customer_id: user.id,
                rating,
                comment
            });
            showToast("Review submitted successfully!");
            setRatingModal({ visible: false });
        } catch(e) {
            showToast("Failed to submit review", "error");
        }
    }

    return (
        <div className="max-w-6xl mx-auto py-12 px-6">
            
            <div className="mb-12 text-center">
                <h1 className="text-5xl font-extrabold mb-4">Discover Your Next <span className="text-blue-500">Great Read</span></h1>
                <p className="text-xl text-slate-400 max-w-2xl mx-auto">Explore our catalog powered by 12 independent microservices.</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {books.length === 0 ? (
                    <div className="col-span-full py-20 text-center text-slate-500 glass-panel">
                        No books available. Add some via the Admin Panel.
                    </div>
                ) : (
                    books.map((b, i) => {
                        const style = { animationDelay: `${i * 0.1}s` };
                        return (
                            <div key={b.id} style={style} className="glass-panel p-6 flex flex-col group hover:border-blue-500/50 hover:shadow-[0_0_30px_rgba(59,130,246,0.3)] animate-[slideUp_0.4s_ease_forwards] opacity-0 translate-y-4">
                                
                                <div className="text-5xl mb-4 group-hover:scale-110 transition-transform origin-bottom text-blue-400">📖</div>
                                
                                <h3 className="text-xl font-bold mb-1 leading-tight">{b.title}</h3>
                                <p className="text-slate-400 text-sm mb-4">{b.description}</p>
                                
                                <div className="mt-auto pt-4 flex items-center justify-between">
                                    <span className="text-2xl font-black text-white">${parseFloat(b.price || 10).toFixed(2)}</span>
                                    <button 
                                        onClick={() => setRatingModal({ visible: true, bookId: b.id, title: b.title })}
                                        className="text-yellow-500 hover:text-yellow-400 text-sm flex items-center gap-1 font-semibold"
                                    >
                                        ⭐ Rate
                                    </button>
                                </div>
                                
                                <button 
                                    onClick={() => addToCart(b.id)}
                                    className="w-full mt-4 py-3 rounded-xl font-bold bg-white/5 border border-white/10 hover:bg-blue-600 hover:border-transparent transition-all"
                                >
                                    Add to Cart
                                </button>
                            </div>
                        )
                    })
                )}
            </div>

            {/* Rating Modal */}
            {ratingModal.visible && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <div className="glass-panel w-full max-w-md p-6 animate-[slideUp_0.3s_ease]">
                        <h3 className="text-xl font-bold mb-2">Rate "{ratingModal.title}"</h3>
                        <p className="text-sm text-slate-400 mb-6">Communicates with comment-rate-service</p>
                        
                        <div className="flex gap-2 justify-center mb-6">
                            {[1,2,3,4,5].map(star => (
                                <button 
                                    key={star}
                                    onClick={() => setRating(star)}
                                    className={`text-3xl transition-transform hover:scale-110 ${rating >= star ? 'text-yellow-400 drop-shadow-[0_0_10px_rgba(250,204,21,0.5)]' : 'text-slate-600'}`}
                                >
                                    ⭐
                                </button>
                            ))}
                        </div>
                        
                        <textarea 
                            value={comment}
                            onChange={e=>setComment(e.target.value)}
                            placeholder="Drop a comment..."
                            className="w-full bg-black/20 border border-white/10 rounded-xl p-3 text-white focus:outline-none focus:border-blue-500 mb-4 min-h-[100px]"
                        ></textarea>
                        
                        <div className="flex gap-3">
                            <button onClick={()=>setRatingModal({visible: false})} className="flex-1 py-3 rounded-xl bg-white/5 hover:bg-white/10 transition">Cancel</button>
                            <button onClick={submitRating} className="flex-1 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 transition font-bold">Submit</button>
                        </div>
                    </div>
                </div>
            )}

        </div>
    );
}
