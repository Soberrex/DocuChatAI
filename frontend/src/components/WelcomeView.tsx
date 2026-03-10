import React from 'react';
import { Zap, Sparkles } from 'lucide-react';

interface WelcomeViewProps {
    onSendMessage: (msg: string) => void;
    userEmail?: string | null;
}

const suggestions = [
    { icon: <Sparkles size={16} />, text: 'What is My Financial Summary of This Year?' },
    { icon: <Zap size={16} />, text: 'How can I automate my current Savings?' },
];

const WelcomeView = ({ onSendMessage, userEmail }: WelcomeViewProps) => {
    // Extract first name (capitalize first letter)
    const firstName = userEmail ? userEmail.split('@')[0] : '';
    const nameStr = firstName ? firstName.charAt(0).toUpperCase() + firstName.slice(1) : '';

    return (
        <div className="flex-1 flex flex-col items-center justify-center px-6 sm:px-8 lg:px-12 overflow-hidden">
            <div className="anim-fade w-full flex flex-col items-center text-center" style={{ maxWidth: '640px' }}>
                {/* Logo */}
                <div className="w-16 h-16 rounded-2xl grad-copper flex items-center justify-center shadow-lg mb-8">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" className="text-white">
                        <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        <path d="M2 17L12 22L22 17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        <path d="M2 12L12 17L22 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                </div>

                {/* Display logic for Guest vs Logged In */}
                <h1
                    className="text-2xl sm:text-3xl lg:text-4xl font-bold leading-tight tracking-tight mb-4"
                    style={{ color: 'var(--color-primary)' }}
                >
                    {userEmail ? (
                        <>Welcome back, <span style={{ color: 'var(--color-accent)' }}>{nameStr}</span></>
                    ) : (
                        <>Welcome to <span style={{ color: 'var(--color-accent)' }}>DocuChat AI</span></>
                    )}
                </h1>

                <p className="text-sm sm:text-base leading-relaxed max-w-sm sm:max-w-md mx-auto mb-10" style={{ color: 'var(--color-secondary)' }}>
                    Upload your documents and ask questions. Get instant insights powered by AI.
                </p>

                {/* Suggestion Chips — Symmetrical Layout */}
                <div className="flex flex-col sm:flex-row gap-4 w-full max-w-2xl justify-center items-stretch">
                    {suggestions.map((s, i) => (
                        <button
                            key={i}
                            onClick={() => onSendMessage(s.text)}
                            className="flex-1 flex items-center gap-3 rounded-2xl text-left transition-all hover:-translate-y-1 hover:shadow-lg active:translate-y-0 active:scale[0.98] w-full"
                            style={{
                                backgroundColor: 'var(--color-card)',
                                border: '1px solid var(--color-edge)',
                                padding: '16px 20px',
                            }}
                        >
                            <div className="shrink-0 p-2.5 rounded-xl" style={{ backgroundColor: 'rgba(224,90,43,0.1)', color: 'var(--color-accent)' }}>
                                {s.icon}
                            </div>
                            <span className="text-sm font-medium" style={{ color: 'var(--color-primary)', lineHeight: '1.4' }}>{s.text}</span>
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default WelcomeView;
