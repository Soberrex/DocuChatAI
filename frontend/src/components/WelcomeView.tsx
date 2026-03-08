import React from 'react';
import { Zap, Sparkles } from 'lucide-react';

interface WelcomeViewProps {
    onSendMessage: (msg: string) => void;
}

const suggestions = [
    { icon: <Sparkles size={14} />, text: 'What is My Financial Summary of This Year?' },
    { icon: <Zap size={14} />, text: 'How can I automate my current Savings?' },
];

const WelcomeView = ({ onSendMessage }: WelcomeViewProps) => {
    return (
        <div className="flex-1 flex flex-col items-center justify-center px-6 sm:px-8 lg:px-12 overflow-hidden">
            <div className="text-center anim-fade w-full" style={{ maxWidth: '520px' }}>
                {/* Logo */}
                <div className="w-14 h-14 rounded-2xl grad-copper mx-auto mb-5 flex items-center justify-center shadow-lg">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="text-white">
                        <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        <path d="M2 17L12 22L22 17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        <path d="M2 12L12 17L22 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                </div>

                <h1
                    className="text-xl sm:text-2xl lg:text-3xl font-bold leading-tight tracking-tight"
                    style={{ color: 'var(--color-primary)' }}
                >
                    Welcome to Your
                    <br />
                    <span style={{ color: 'var(--color-accent)' }}>DocuChat AI</span>
                </h1>
                <p className="mt-2 text-xs sm:text-sm leading-relaxed mx-auto max-w-xs" style={{ color: 'var(--color-secondary)' }}>
                    Upload your documents and ask questions. Get instant insights powered by AI.
                </p>

                {/* Suggestion Chips — with minimum height */}
                <div className="mt-6 flex flex-col gap-2.5 w-full">
                    {suggestions.map((s, i) => (
                        <button
                            key={i}
                            onClick={() => onSendMessage(s.text)}
                            className="flex items-center gap-3 rounded-xl text-left transition-all active:scale-[0.98] w-full"
                            style={{
                                backgroundColor: 'var(--color-card)',
                                border: '1px solid var(--color-edge)',
                                color: 'var(--color-secondary)',
                                minHeight: '56px',
                                padding: '16px 20px',
                            }}
                        >
                            <span className="shrink-0" style={{ color: 'var(--color-accent)', opacity: 0.7 }}>{s.icon}</span>
                            <span className="text-sm leading-snug">{s.text}</span>
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default WelcomeView;
