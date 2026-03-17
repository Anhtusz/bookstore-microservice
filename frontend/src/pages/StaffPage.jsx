import { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { AppContext } from '../context/AppContext.jsx';

export default function StaffPage() {
    const { API_BASE, showToast, categories, fetchCategories } = useContext(AppContext);
    const [tab, setTab] = useState('books');

    // Book Form
    const [title, setTitle] = useState('');
    const [author, setAuthor] = useState('');
    const [price, setPrice] = useState('19.99');
    const [stock, setStock] = useState('10');
    const [categoryId, setCategoryId] = useState('');
    const [imageUrl, setImageUrl] = useState('');
    const [books, setBooks] = useState([]);
    const [editingBookId, setEditingBookId] = useState(null);

    // Category Form
    const [catName, setCatName] = useState('');
    const [catDesc, setCatDesc] = useState('');

    // Orders
    const [orders, setOrders] = useState([]);

    const loadBooks = async () => {
        try {
            const res = await axios.get(`${API_BASE}/staff/manage-books/`);
            setBooks(res.data);
        } catch { showToast("Failed to load inventory", "error"); }
    };

    const loadOrders = async () => {
        try {
            const res = await axios.get(`${API_BASE}/staff/manage-orders/`);
            setOrders(res.data);
        } catch { showToast("Failed to load orders", "error"); }
    };

    useEffect(() => {
        loadBooks();
        loadOrders();
    }, []);

    const totalBooksCount = books.length;
    const inventoryValue = books.reduce((acc, b) => acc + (b.stock * parseFloat(b.price || 0)), 0);
    const totalOrdersCount = orders.length;
    const validOrders = orders.filter(o => o.status === 'PAID' || o.status === 'SHIPPING');
    const totalRevenue = validOrders.reduce((acc, o) => acc + parseFloat(o.total_price || 0), 0);
    const handleAddBook = async (e) => {
        e.preventDefault();
        try {
            const payload = {
                title, author, price: parseFloat(price),
                stock: parseInt(stock),
                description: `A masterpiece by ${author}.`,
                image_url: imageUrl || ''
            };

            let bookId;
            if (editingBookId) {
                await axios.put(`${API_BASE}/staff/manage-books/${editingBookId}/`, payload);
                bookId = editingBookId;
                showToast("Book updated!");
            } else {
                const res = await axios.post(`${API_BASE}/staff/manage-books/`, payload);
                bookId = res.data.id;
                showToast("Book added!");
            }

            await axios.put(`${API_BASE}/catalog/items/${bookId}/`, {
                book_id: bookId,
                category: categoryId ? parseInt(categoryId) : null
            });
            resetBookForm();
            loadBooks();
        } catch { showToast("Failed to save book", "error"); }
    };

    const resetBookForm = () => {
        setEditingBookId(null);
        setTitle(''); setAuthor(''); setPrice('19.99'); setStock('10');
        setCategoryId(''); setImageUrl('');
    };

    const startEditing = async (book) => {
        setEditingBookId(book.id);
        setTitle(book.title);
        setAuthor(book.author);
        setPrice(book.price.toString());
        setStock(book.stock.toString());
        setImageUrl(book.image_url || '');

        // Fetch category from catalog-service
        try {
            const catRes = await axios.get(`${API_BASE}/catalog/items/${book.id}/`);
            setCategoryId(catRes.data.category ? catRes.data.category.toString() : '');
        } catch {
            setCategoryId(''); // No catalog entry yet
        }

        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    const handleAddCategory = async (e) => {
        e.preventDefault();
        try {
            await axios.post(`${API_BASE}/staff/manage-categories/`, { name: catName, description: catDesc });
            showToast("Category created!");
            setCatName(''); setCatDesc('');
            fetchCategories();
        } catch { showToast("Failed to create category", "error"); }
    };

    const confirmShipment = async (orderId) => {
        try {
            await axios.post(`${API_BASE}/staff/manage-orders/${orderId}/confirm_shipment/`);
            showToast("Shipment confirmed! 🚚");
            loadOrders();
        } catch { showToast("Action failed", "error"); }
    };

    return (
        <div className="py-12">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-12">
                <div>
                    <h1 className="text-4xl font-black bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-600">
                        Staff Dashboard
                    </h1>
                    <p className="text-slate-400 mt-2">Inventory control & order fulfillment systems.</p>
                </div>

                <div className="flex flex-wrap gap-2 bg-white/5 p-1.5 rounded-2xl border border-white/5">
                    {['dashboard', 'books', 'categories', 'orders'].map(t => (
                        <button
                            key={t} onClick={() => setTab(t)}
                            className={`px-5 py-2.5 rounded-xl text-xs sm:text-sm font-black uppercase tracking-widest transition-all ${tab === t ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30' : 'text-slate-500 hover:text-white'
                                }`}
                        >
                            {t}
                        </button>
                    ))}
                </div>
            </div>

            {tab === 'dashboard' && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-12 animate-[fadeIn_0.3s_ease-out]">
                    <div className="glass-panel p-6 flex items-center gap-6">
                        <div className="w-14 h-14 rounded-2xl bg-blue-500/20 text-blue-400 flex items-center justify-center text-3xl">📚</div>
                        <div>
                            <p className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-1">Total Books</p>
                            <p className="text-3xl font-black">{totalBooksCount}</p>
                        </div>
                    </div>
                    <div className="glass-panel p-6 flex items-center gap-6">
                        <div className="w-14 h-14 rounded-2xl bg-purple-500/20 text-purple-400 flex items-center justify-center text-3xl">💎</div>
                        <div>
                            <p className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-1">Inventory Value</p>
                            <p className="text-3xl font-black">${inventoryValue.toFixed(2)}</p>
                        </div>
                    </div>
                    <div className="glass-panel p-6 flex items-center gap-6">
                        <div className="w-14 h-14 rounded-2xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-3xl">📦</div>
                        <div>
                            <p className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-1">Total Orders</p>
                            <p className="text-3xl font-black">{totalOrdersCount}</p>
                        </div>
                    </div>
                    <div className="glass-panel p-6 flex items-center gap-6">
                        <div className="w-14 h-14 rounded-2xl bg-yellow-500/20 text-yellow-400 flex items-center justify-center text-3xl">💰</div>
                        <div>
                            <p className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-1">Valid Revenue</p>
                            <p className="text-3xl font-black">${totalRevenue.toFixed(2)}</p>
                        </div>
                    </div>
                </div>
            )}

            {tab === 'books' && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
                    <div className="glass-panel p-8 h-fit">
                        <div className="flex justify-between items-center mb-8">
                            <h3 className="text-xl font-bold flex items-center gap-3">
                                <span className="text-2xl">{editingBookId ? '✏️' : '➕'}</span>
                                {editingBookId ? 'Edit Book' : 'Add New Book'}
                            </h3>
                            {editingBookId && (
                                <button onClick={resetBookForm} className="text-xs font-bold text-slate-500 hover:text-white uppercase tracking-widest bg-white/5 px-3 py-1.5 rounded-full">
                                    Cancel
                                </button>
                            )}
                        </div>
                        <form onSubmit={handleAddBook} className="space-y-6">
                            <div className="space-y-1">
                                <label className="text-[10px] font-black uppercase text-slate-500 tracking-widest pl-1">Title</label>
                                <input required value={title} onChange={e => setTitle(e.target.value)} className="input-field w-full" />
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-black uppercase text-slate-500 tracking-widest pl-1">Author</label>
                                <input required value={author} onChange={e => setAuthor(e.target.value)} className="input-field w-full" />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-1">
                                    <label className="text-[10px] font-black uppercase text-slate-500 tracking-widest pl-1">Price ($)</label>
                                    <input required type="number" step="0.01" value={price} onChange={e => setPrice(e.target.value)} className="input-field w-full" />
                                </div>
                                <div className="space-y-1">
                                    <label className="text-[10px] font-black uppercase text-slate-500 tracking-widest pl-1">Stock</label>
                                    <input required type="number" value={stock} onChange={e => setStock(e.target.value)} className="input-field w-full" />
                                </div>
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-black uppercase text-slate-500 tracking-widest pl-1">Category</label>
                                <select value={categoryId} onChange={e => setCategoryId(e.target.value)} className="input-field w-full appearance-none">
                                    <option value="">No Category</option>
                                    {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                                </select>
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-black uppercase text-slate-500 tracking-widest pl-1">Cover Image URL (Optional)</label>
                                <input type="url" value={imageUrl} onChange={e => setImageUrl(e.target.value)} className="input-field w-full" placeholder="https://example.com/cover.jpg" />
                            </div>
                            <button className="w-full py-4 rounded-2xl bg-blue-600 text-white font-black uppercase tracking-widest hover:bg-blue-500 transition-all shadow-xl shadow-blue-500/20">
                                {editingBookId ? 'Update Catalog' : 'Add to Catalog'}
                            </button>
                        </form>
                    </div>

                    <div className="lg:col-span-2 glass-panel p-8">
                        <div className="flex items-center justify-between mb-8 pb-4 border-b border-white/5">
                            <h3 className="text-xl font-bold">Inventory Catalog</h3>
                            <span className="text-xs font-black text-slate-500 uppercase tracking-widest">{books.length} Books total</span>
                        </div>
                        <div className="space-y-4">
                            {books.map(b => {
                                const cat = categories.find(c => c.id === b.category_id);
                                const categoryName = cat ? cat.name : null;
                                return (
                                    <div key={b.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-5 bg-white/2 border border-white/5 rounded-2xl hover:border-blue-500/30 transition-all group">
                                        <div className="mb-4 sm:mb-0">
                                            <h4 className="font-bold text-lg group-hover:text-blue-400 transition-colors">{b.title}</h4>
                                            <div className="flex items-center gap-3 mt-1">
                                                <span className="text-xs text-slate-500 font-medium">by {b.author}</span>
                                                {categoryName && <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 text-slate-400 font-black uppercase tracking-tighter">{categoryName}</span>}
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-6">
                                            <div className="text-right">
                                                <p className="text-[10px] font-black text-slate-600 uppercase tracking-widest">Stock</p>
                                                <p className={`font-black ${b.stock > 0 ? 'text-emerald-500' : 'text-red-500'}`}>{b.stock}</p>
                                            </div>
                                            <div className="text-right">
                                                <p className="text-[10px] font-black text-slate-600 uppercase tracking-widest">Price</p>
                                                <p className="font-black text-blue-400">${parseFloat(b.price || 0).toFixed(2)}</p>
                                            </div>
                                            <button
                                                onClick={() => startEditing(b)}
                                                className="w-10 h-10 rounded-full bg-white/5 hover:bg-blue-600 hover:text-white flex items-center justify-center transition-colors border border-white/5 border-transparent pointer-events-auto shadow-sm"
                                                title="Edit Book"
                                            >
                                                ✏️
                                            </button>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </div>
            )}

            {tab === 'categories' && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
                    <div className="glass-panel p-8 h-fit">
                        <h3 className="text-xl font-bold mb-8 flex items-center gap-3">🏷️ New Category</h3>
                        <form onSubmit={handleAddCategory} className="space-y-6">
                            <div className="space-y-1">
                                <label className="text-[10px] font-black uppercase text-slate-500 tracking-widest pl-1">Category Name</label>
                                <input required value={catName} onChange={e => setCatName(e.target.value)} className="input-field w-full" placeholder="e.g. Science Fiction" />
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-black uppercase text-slate-500 tracking-widest pl-1">Description</label>
                                <textarea value={catDesc} onChange={e => setCatDesc(e.target.value)} className="input-field w-full min-h-[100px] py-3" />
                            </div>
                            <button className="w-full py-4 rounded-2xl bg-purple-600 text-white font-black uppercase tracking-widest hover:bg-purple-500 transition-all shadow-xl shadow-purple-500/20">
                                Create Category
                            </button>
                        </form>
                    </div>
                    <div className="lg:col-span-2 glass-panel p-8">
                        <h3 className="text-xl font-bold mb-8 pb-4 border-b border-white/5">Manage Classifications</h3>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            {categories.map(c => (
                                <div key={c.id} className="p-6 bg-white/2 border border-white/5 rounded-2xl hover:border-purple-500/30 transition-all">
                                    <h4 className="font-black text-lg text-purple-400 mb-1">{c.name}</h4>
                                    <p className="text-sm text-slate-500 leading-relaxed">{c.description || "No description provided."}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {tab === 'orders' && (
                <div className="glass-panel p-8">
                    <h3 className="text-xl font-bold mb-8 pb-4 border-b border-white/5 flex items-center gap-4">
                        📦 Order Fulfillment Pipeline
                        <span className="text-xs bg-emerald-500/10 text-emerald-500 px-3 py-1 rounded-full border border-emerald-500/20 font-black uppercase tracking-widest animate-pulse">Live</span>
                    </h3>
                    <div className="space-y-6">
                        {orders.length === 0 ? (
                            <div className="py-20 text-center text-slate-500 italic">No orders in the system yet.</div>
                        ) : orders.map(o => (
                            <div key={o.id} className="p-8 bg-white/2 border border-white/10 rounded-3xl flex flex-col lg:flex-row justify-between gap-10 hover:border-white/20 transition-all">
                                <div className="flex-1">
                                    <div className="flex items-center gap-4 mb-4">
                                        <span className="text-xs font-black bg-blue-600 px-3 py-1 rounded-full uppercase tracking-widest">Order #{o.id}</span>
                                        <span className={`text-xs font-black px-3 py-1 rounded-full uppercase tracking-widest ${o.status === 'WAITING_CONFIRMATION' ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                                            }`}>
                                            {o.status.replace('_', ' ')}
                                        </span>
                                    </div>
                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-8">
                                        <div>
                                            <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">Customer Info</p>
                                            <p className="font-bold">{o.customer_name || 'Anonymous'}</p>
                                            <p className="text-sm text-slate-400">{o.customer_phone}</p>
                                        </div>
                                        <div>
                                            <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">Shipping Address</p>
                                            <p className="text-sm text-slate-400 leading-tight">{o.shipping_address}</p>
                                        </div>
                                    </div>
                                    <div className="mt-6 pt-6 border-t border-white/5 flex gap-4 overflow-x-auto pb-2">
                                        {o.items?.map((item, idx) => (
                                            <div key={idx} className="flex-shrink-0 bg-black/40 px-4 py-2 rounded-xl border border-white/5">
                                                <span className="text-xs font-black text-blue-500 mr-2">x{item.quantity}</span>
                                                <span className="text-sm font-medium">Book #{item.book_id}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                                <div className="lg:w-64 flex flex-col justify-between items-end border-l border-white/5 pl-10">
                                    <div className="text-right">
                                        <p className="text-xs font-black text-slate-500 uppercase tracking-widest mb-1">Method: {o.payment_method}</p>
                                        <p className="text-4xl font-black">${parseFloat(o.total_price).toFixed(2)}</p>
                                    </div>
                                    {o.status === 'WAITING_CONFIRMATION' && (
                                        <button
                                            onClick={() => confirmShipment(o.id)}
                                            className="w-full mt-6 py-4 rounded-2xl bg-white text-black font-black uppercase tracking-widest hover:bg-emerald-500 hover:text-white transition-all shadow-2xl"
                                        >
                                            Ship Items 🚀
                                        </button>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
