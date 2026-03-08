import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, Paperclip, StopCircle } from 'lucide-react';
import MessageBubble from './MessageBubble';

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    created_at: string;
    sources?: any[];
    confidence?: number;
    chart_data?: any;
}

interface ChatInterfaceProps {
    messages: Message[];
    onSendMessage: (msg: string) => void;
    isProcessing: boolean;
    onFileUpload?: () => void;
}

const ChatInterface = ({ messages, onSendMessage, isProcessing, onFileUpload }: ChatInterfaceProps) => {
    const [input, setInput] = useState('');
    const [isListening, setIsListening] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const recognitionRef = useRef<any>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSend = () => {
        const trimmed = input.trim();
        if (!trimmed || isProcessing) return;
        onSendMessage(trimmed);
        setInput('');
    };

    const toggleVoice = () => {
        if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) return;
        if (isListening) { recognitionRef.current?.stop(); setIsListening(false); return; }
        const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
        const recognition = new SR();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        recognition.onresult = (e: any) => { setInput((p) => p + e.results[0][0].transcript); setIsListening(false); };
        recognition.onerror = () => setIsListening(false);
        recognition.onend = () => setIsListening(false);
        recognitionRef.current = recognition;
        recognition.start();
        setIsListening(true);
    };

    return (
        <div className="flex-1 flex flex-col h-full min-w-0 overflow-hidden">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto">
                <div className="mx-auto w-full" style={{ maxWidth: '760px', paddingLeft: '24px', paddingRight: '24px', paddingTop: '20px', paddingBottom: '20px' }}>
                    {messages.map((msg, i) => (
                        <MessageBubble key={msg.id || i} message={msg} />
                    ))}
                    {isProcessing && (
                        <div className="flex items-center gap-3 py-4 anim-fade">
                            <div className="w-7 h-7 rounded-full grad-copper flex items-center justify-center anim-spin">
                                <div className="w-4 h-4 rounded-full" style={{ backgroundColor: 'var(--color-surface)' }} />
                            </div>
                            <span className="text-sm" style={{ color: 'var(--color-secondary)' }}>Analysing...</span>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>
            </div>

            {/* Input Bar — centered, tall, matching welcome bar style */}
            <div className="shrink-0 w-full">
                <div className="mx-auto w-full" style={{ maxWidth: '760px', padding: '8px 24px 20px 24px' }}>
                    <div
                        className="flex items-center gap-2 rounded-xl"
                        style={{
                            backgroundColor: 'var(--color-card)',
                            border: '1px solid var(--color-edge)',
                            padding: '12px 16px',
                            minHeight: '56px',
                        }}
                    >
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
                            placeholder="Message DocuChat AI..."
                            disabled={isProcessing}
                            className="flex-1 min-w-0 bg-transparent outline-none disabled:opacity-50"
                            style={{ color: 'var(--color-primary)', fontSize: '15px', lineHeight: '1.5' }}
                        />
                        <button
                            onClick={toggleVoice}
                            className="p-2 rounded-lg shrink-0 active:scale-90 transition-transform"
                            style={{ color: isListening ? 'var(--color-accent)' : 'var(--color-muted)' }}
                        >
                            {isListening ? <StopCircle size={20} /> : <Mic size={20} />}
                        </button>
                        <button onClick={onFileUpload} className="p-2 rounded-lg shrink-0 active:scale-90 transition-transform" style={{ color: 'var(--color-muted)' }}>
                            <Paperclip size={20} />
                        </button>
                        <button
                            onClick={handleSend}
                            disabled={!input.trim() || isProcessing}
                            className="w-9 h-9 rounded-full flex items-center justify-center shrink-0 active:scale-90 transition-transform"
                            style={{
                                backgroundColor: input.trim() && !isProcessing ? 'var(--color-accent)' : 'var(--color-elevated)',
                                color: input.trim() && !isProcessing ? 'white' : 'var(--color-muted)',
                                cursor: input.trim() && !isProcessing ? 'pointer' : 'not-allowed',
                            }}
                        >
                            <Send size={16} />
                        </button>
                    </div>
                    <p className="text-[10px] text-center mt-1.5" style={{ color: 'var(--color-muted)' }}>
                        DocuChat AI can make mistakes. Verify important information.
                    </p>
                </div>
            </div>
        </div>
    );
};

export default ChatInterface;
