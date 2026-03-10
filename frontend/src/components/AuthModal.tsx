import React, { useState } from 'react';
import { X, Mail, Lock, Loader2 } from 'lucide-react';
import { login, register } from '../services/api';

interface AuthModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: (user: { id: string; email: string }) => void;
}

export default function AuthModal({ isOpen, onClose, onSuccess }: AuthModalProps) {
    const [isLogin, setIsLogin] = useState(true);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    if (!isOpen) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            let response;
            if (isLogin) {
                response = await login(email, password);
            } else {
                response = await register(email, password);
            }
            onSuccess(response.user);
            onClose();
        } catch (err: any) {
            setError(err.response?.data?.detail || 'An error occurred. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 anim-fade-in">
            <div className="w-full max-w-md bg-white dark:bg-gray-900 rounded-2xl shadow-xl overflow-hidden border border-gray-200 dark:border-gray-800 anim-slide-up">
                {/* Header */}
                <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--color-edge)' }} className="flex justify-between items-center">
                    <h2 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-[var(--color-accent)] to-[var(--color-primary)]">
                        {isLogin ? 'Sign In' : 'Create Account'}
                    </h2>
                    <button onClick={onClose} className="p-2 -mr-2 text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full transition-colors">
                        <X size={20} />
                    </button>
                </div>

                {/* Body */}
                <form onSubmit={handleSubmit} style={{ padding: '24px' }}>
                    {error && (
                        <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm rounded-lg border border-red-200 dark:border-red-900/50">
                            {error}
                        </div>
                    )}

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                        <div>
                            <label style={{ display: 'block', fontSize: '14px', fontWeight: 500, marginBottom: '8px', color: 'var(--color-primary)' }}>Email Address</label>
                            <div className="relative">
                                <Mail size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                                <input
                                    type="email"
                                    required
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full bg-gray-50 dark:bg-gray-800 border-none rounded-xl focus:ring-2 focus:ring-[var(--color-accent)] outline-none text-gray-900 dark:text-gray-100 transition-shadow"
                                    style={{ padding: '10px 16px 10px 40px', width: '100%', boxSizing: 'border-box' }}
                                    placeholder="your@email.com"
                                />
                            </div>
                        </div>

                        <div>
                            <label style={{ display: 'block', fontSize: '14px', fontWeight: 500, marginBottom: '8px', color: 'var(--color-primary)' }}>Password</label>
                            <div className="relative">
                                <Lock size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                                <input
                                    type="password"
                                    required
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full bg-gray-50 dark:bg-gray-800 border-none rounded-xl focus:ring-2 focus:ring-[var(--color-accent)] outline-none text-gray-900 dark:text-gray-100 transition-shadow"
                                    style={{ padding: '10px 16px 10px 40px', width: '100%', boxSizing: 'border-box' }}
                                    placeholder="••••••••"
                                    minLength={6}
                                />
                            </div>
                        </div>
                    </div>

                    <div style={{ marginTop: '32px' }}>
                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full flex justify-center items-center bg-gradient-to-r from-[var(--color-accent)] to-[var(--color-primary)] hover:opacity-90 text-white rounded-xl font-medium shadow-md shadow-orange-500/20 transition-all active:scale-[0.98] disabled:opacity-70 disabled:scale-100"
                            style={{ padding: '12px 16px' }}
                        >
                            {loading ? <Loader2 size={20} className="animate-spin" /> : isLogin ? 'Sign In' : 'Sign Up'}
                        </button>
                    </div>
                </form>

                {/* Footer */}
                <div style={{ padding: '16px 24px', borderTop: '1px solid var(--color-edge)', textAlign: 'center', backgroundColor: 'rgba(0,0,0,0.02)' }}>
                    <button
                        type="button"
                        onClick={() => { setIsLogin(!isLogin); setError(''); }}
                        className="text-sm hover:text-[var(--color-accent)] transition-colors"
                        style={{ color: 'var(--color-muted)' }}
                    >
                        {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
                    </button>
                </div>
            </div>
        </div>
    );
}
