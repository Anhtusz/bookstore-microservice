import { Link } from 'react-router-dom';

export default function StaffNavbar() {
    return (
        <nav className="sticky top-0 z-50 bg-slate-900/90 backdrop-blur-md border-b border-purple-500/30">
            <div className="max-w-5xl mx-auto px-6 py-4 flex justify-between items-center">
                <div className="flex items-center gap-3">
                    <span className="text-2xl">⚙️</span>
                    <div>
                        <h1 className="text-lg font-bold text-white leading-none">Staff Panel</h1>
                        <p className="text-xs text-purple-400">MicroBooks Admin</p>
                    </div>
                </div>
                <Link
                    to="/"
                    className="text-sm text-slate-400 hover:text-white transition flex items-center gap-1"
                >
                    ← Go to Storefront
                </Link>
            </div>
        </nav>
    );
}
