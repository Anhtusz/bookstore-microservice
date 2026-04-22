import { useState, useRef, useEffect, useContext } from 'react';
import axios from 'axios';
import { AppContext } from '../context/AppContext.jsx';

export default function Chatbot() {
    const { API_BASE, user } = useContext(AppContext);
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState([
        { role: 'bot', text: 'Hi! I am your AI assistant. Ask me anything about our books!' }
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        if (isOpen) {
            scrollToBottom();
        }
    }, [messages, isOpen]);

    const handleSend = async () => {
        if (!input.trim()) return;
        
        const userQuery = input.trim();
        setMessages(prev => [...prev, { role: 'user', text: userQuery }]);
        setInput('');
        setIsLoading(true);

        try {
            const res = await axios.post(`${API_BASE}/recommender-ai/recommendations/chat/`, {
                query: userQuery,
                user_id: user?.id ?? null,
            });
            const sourceLine = Array.isArray(res.data.sources) && res.data.sources.length > 0
                ? `\n\nSources: ${res.data.sources.map(source => source.title || `${source.type}#${source.id || ''}`).join(', ')}`
                : '';
            setMessages(prev => [...prev, { role: 'bot', text: `${res.data.answer || "I'm not sure how to respond to that."}${sourceLine}` }]);
        } catch (error) {
            setMessages(prev => [...prev, { role: 'bot', text: 'Sorry, I am having trouble connecting to my central brain right now.' }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <>
            {/* Toggle Button */}
            <button 
                onClick={() => setIsOpen(!isOpen)}
                className="fixed bottom-6 right-6 w-14 h-14 bg-blue-600 rounded-full flex items-center justify-center text-2xl shadow-lg shadow-blue-500/50 hover:scale-110 transition-transform z-50"
            >
                {isOpen ? '✕' : '💬'}
            </button>

            {/* Chat Window */}
            {isOpen && (
                <div className="fixed bottom-24 right-6 w-80 md:w-[400px] max-w-[calc(100vw-3rem)] h-[500px] bg-slate-900 border border-white/10 rounded-2xl shadow-2xl flex flex-col z-50 overflow-hidden animate-[fadeIn_0.2s_ease-out]">
                    <div className="bg-blue-600 p-4 font-bold text-white shadow-md flex justify-between items-center z-10">
                        <div className="flex items-center gap-2">
                            <span className="text-xl">🤖</span>
                            <span>Bookstore AI</span>
                        </div>
                        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                    </div>
                    
                    <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gradient-to-b from-slate-900 to-slate-800">
                        {messages.map((msg, idx) => (
                            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                <div className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed shadow-sm ${
                                    msg.role === 'user' 
                                    ? 'bg-blue-600 text-white rounded-br-sm' 
                                    : 'bg-white/10 text-slate-200 border border-white/5 rounded-bl-sm'
                                }`}>
                                    {msg.text}
                                </div>
                            </div>
                        ))}
                        {isLoading && (
                            <div className="flex justify-start">
                                <div className="bg-white/10 border border-white/5 text-slate-400 rounded-2xl rounded-bl-sm px-4 py-3 text-xs flex gap-1.5 items-center">
                                    <span className="animate-bounce inline-block">●</span>
                                    <span className="animate-bounce delay-100 inline-block">●</span>
                                    <span className="animate-bounce delay-200 inline-block">●</span>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>
                    
                    <div className="p-3 border-t border-white/10 bg-slate-900 flex gap-2">
                        <input 
                            type="text" 
                            className="flex-1 bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
                            placeholder="Ask about our books..."
                            value={input}
                            onChange={e => setInput(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && handleSend()}
                        />
                        <button 
                            onClick={handleSend}
                            disabled={isLoading || !input.trim()}
                            className="bg-blue-600 text-white px-5 py-2.5 rounded-xl text-sm font-bold hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            ↗
                        </button>
                    </div>
                </div>
            )}
        </>
    );
}
