import { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { AppContext } from '../context/AppContext';

export default function AdminPage() {
    const { API_BASE, showToast } = useContext(AppContext);
    
    // Form state
    const [title, setTitle] = useState('');
    const [author, setAuthor] = useState('');
    const [price, setPrice] = useState('19.99');
    
    // Books State
    const [books, setBooks] = useState([]);

    const fetchBooks = async () => {
        try {
            // Use Staff service as the "authorized" proxy to manage inventory.
            const res = await axios.get(`${API_BASE}/staff/manage-books/`);
            setBooks(res.data);
        } catch(e) { console.error(e) }
    }

    useEffect(() => {
        fetchBooks();
    }, []);

    const handleAddBook = async (e) => {
        e.preventDefault();
        try {
            // Create via Staff service proxy
            const res = await axios.post(`${API_BASE}/staff/manage-books/`, {
                title, 
                author,
                description: `By ${author}`,
                price: parseFloat(price), 
                stock: 10, 
                category_id: 1
            });
            
            showToast(`"${res.data.title}" added to inventory via Staff Service Proxy!`);
            setTitle(''); setAuthor(''); setPrice('19.99');
            fetchBooks();
        } catch (error) {
            showToast("Failed to add book. Ensure Book-Service and Staff-Service are running.", "error");
        }
    };

    const handleDelete = async (id) => {
        try {
            await axios.delete(`${API_BASE}/staff/manage-books/${id}/`);
            showToast("Book removed from inventory.");
            fetchBooks();
        } catch(e) {
            showToast("Error deleting book", "error");
        }
    }

    return (
        <div className="max-w-4xl mx-auto py-12">
            
            <div className="mb-8 flex items-end justify-between">
                <div>
                    <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-600">Admin Dashboard</h1>
                    <p className="text-slate-400 mt-2">Manage the BookStore microservices architecture.</p>
                </div>
                <div className="px-4 py-1.5 bg-purple-500/20 text-purple-400 border border-purple-500/30 rounded-full text-sm font-semibold flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-purple-500 animate-pulse"></span>
                    Staff Authorized
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {/* Book Form */}
                <div className="md:col-span-1 glass-panel p-6 h-fit sticky top-24">
                    <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
                        <span className="text-xl">➕</span> Add to Inventory
                    </h3>
                    <form onSubmit={handleAddBook} className="flex flex-col gap-4">
                        <div>
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1 block">Title</label>
                            <input required value={title} onChange={e=>setTitle(e.target.value)} type="text" className="w-full bg-black/20 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-purple-500 transition" />
                        </div>
                        <div>
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1 block">Author</label>
                            <input required value={author} onChange={e=>setAuthor(e.target.value)} type="text" className="w-full bg-black/20 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-purple-500 transition" />
                        </div>
                        <div>
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1 block">Price ($)</label>
                            <input required value={price} onChange={e=>setPrice(e.target.value)} type="number" step="0.01" className="w-full bg-black/20 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-purple-500 transition" />
                        </div>
                        <button type="submit" className="w-full bg-purple-600 hover:bg-purple-500 text-white font-bold py-2 mt-2 rounded-lg transition shadow-lg shadow-purple-500/20">
                            Save Book -&gt;
                        </button>
                    </form>
                </div>

                {/* Inventory List */}
                <div className="md:col-span-2 glass-panel p-6">
                    <h3 className="font-bold text-lg mb-4 flex items-center gap-2 border-b border-white/10 pb-4">
                        <span className="text-xl">📚</span> Current Inventory
                        <span className="ml-auto bg-slate-800 text-xs px-2 py-0.5 rounded border border-white/10">{books.length} items</span>
                    </h3>
                    
                    <div className="flex flex-col gap-3">
                        {books.length === 0 ? (
                            <div className="py-12 text-center text-slate-500 border border-dashed border-white/10 rounded-xl">
                                Inventory is empty. Add a book.
                            </div>
                        ) : (
                            books.map(b => (
                                <div key={b.id} className="flex justify-between items-center bg-white/5 border border-white/10 p-4 rounded-xl hover:bg-white/10 hover:border-purple-500/50 transition">
                                    <div>
                                        <h4 className="font-semibold text-slate-100">{b.title}</h4>
                                        <p className="text-sm text-slate-400">{b.description}</p>
                                    </div>
                                    <div className="flex items-center gap-6">
                                        <span className="font-mono text-purple-400 font-bold">${parseFloat(b.price || 10).toFixed(2)}</span>
                                        <button onClick={() => handleDelete(b.id)} className="text-red-400 hover:text-red-300 p-2 hover:bg-red-500/10 rounded transition">
                                            Delete
                                        </button>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>
            
        </div>
    );
}
