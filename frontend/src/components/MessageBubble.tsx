import React, { useState } from 'react';
import { Copy, ThumbsUp, ThumbsDown, RotateCcw, ChevronDown, ChevronUp, FileText, Volume2 } from 'lucide-react';
import ChartVisualizer from './ChartVisualizer';

interface Source {
    document_id: string;
    filename: string;
    chunk_index: number;
    content: string;
    relevance_score: number;
}

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    created_at: string;
    sources?: Source[];
    confidence?: number;
    chart_data?: any;
}

const MessageBubble = ({ message }: { message: Message }) => {
    const [sourcesOpen, setSourcesOpen] = useState(false);
    const [copied, setCopied] = useState(false);
    const isUser = message.role === 'user';

    const handleCopy = () => {
        navigator.clipboard.writeText(message.content);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const handleSpeak = () => {
        const u = new SpeechSynthesisUtterance(message.content);
        window.speechSynthesis.speak(u);
    };

    const formatInline = (text: string) => {
        const parts = text.split(/(\*\*[^*]+\*\*)/g);
        return parts.map((p, i) =>
            p.startsWith('**') && p.endsWith('**')
                ? <strong key={i} className="font-semibold" style={{ color: 'var(--color-primary)' }}>{p.slice(2, -2)}</strong>
                : p
        );
    };

    const renderTable = (lines: string[], key: number) => {
        const rows = lines
            .filter((l) => !l.match(/^\|[\s-:|]+\|$/))
            .map((l) => l.split('|').filter((c) => c.trim() !== '').map((c) => c.trim()));
        if (rows.length === 0) return null;
        const header = rows[0];
        const body = rows.slice(1);
        return (
            <div key={key} className="overflow-x-auto" style={{ margin: '12px 0', borderRadius: '10px', border: '1px solid var(--color-edge)' }}>
                <table className="w-full text-sm" style={{ minWidth: '280px' }}>
                    <thead>
                        <tr style={{ backgroundColor: 'var(--color-elevated)' }}>
                            {header.map((h, i) => (
                                <th key={i} className="text-left text-[11px] font-semibold uppercase tracking-wider whitespace-nowrap" style={{ color: 'var(--color-primary)', padding: '10px 14px' }}>{h}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {body.map((row, ri) => (
                            <tr key={ri} style={{ borderTop: '1px solid var(--color-edge)' }}>
                                {row.map((cell, ci) => (
                                    <td key={ci} className="whitespace-nowrap" style={{ color: 'var(--color-secondary)', padding: '10px 14px' }}>{cell}</td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        );
    };

    const renderContent = (text: string) => {
        const lines = text.split('\n');
        const els: React.ReactNode[] = [];
        let tableLines: string[] = [];
        let inTable = false;

        lines.forEach((line, idx) => {
            const t = line.trim();
            if (t.startsWith('|') && t.endsWith('|')) { inTable = true; tableLines.push(t); return; }
            if (inTable && !t.startsWith('|')) { els.push(renderTable(tableLines, idx)); tableLines = []; inTable = false; }
            if (t.startsWith('## ')) { els.push(<h3 key={idx} className="font-bold text-base" style={{ color: 'var(--color-primary)', marginTop: '16px', marginBottom: '6px' }}>{t.substring(3)}</h3>); return; }
            if (t.startsWith('### ')) { els.push(<h4 key={idx} className="font-semibold text-sm" style={{ color: 'var(--color-primary)', marginTop: '14px', marginBottom: '4px' }}>{t.substring(4)}</h4>); return; }
            if (t.startsWith('• ') || t.startsWith('- ') || t.startsWith('* ')) {
                els.push(<li key={idx} className="text-sm leading-relaxed list-disc" style={{ color: 'var(--color-secondary)', marginLeft: '20px', marginBottom: '2px' }}>{formatInline(t.substring(2))}</li>); return;
            }
            if (t) { els.push(<p key={idx} className="text-sm leading-relaxed" style={{ color: 'var(--color-secondary)', marginBottom: '2px' }}>{formatInline(t)}</p>); }
        });
        if (tableLines.length > 0) els.push(renderTable(tableLines, -1));
        return els;
    };

    /* ── User Message ──────────────────────────────── */
    if (isUser) {
        return (
            <div className="flex justify-end anim-fade" style={{ marginBottom: '16px' }}>
                <div
                    style={{
                        backgroundColor: 'var(--color-card)',
                        border: '1px solid var(--color-edge)',
                        maxWidth: '75%',
                        borderRadius: '16px 16px 4px 16px',
                        padding: '14px 18px',
                    }}
                >
                    <p className="text-sm leading-relaxed break-words" style={{ color: 'var(--color-primary)' }}>{message.content}</p>
                </div>
            </div>
        );
    }

    /* ── AI Message ────────────────────────────────── */
    return (
        <div className="anim-fade" style={{ marginBottom: '20px' }}>
            <div
                className="overflow-hidden"
                style={{
                    backgroundColor: 'var(--color-card)',
                    border: '1px solid var(--color-edge)',
                    borderRadius: '16px 16px 16px 4px',
                    padding: '20px 24px',
                }}
            >
                <div className="min-w-0 overflow-hidden">{renderContent(message.content)}</div>

                {message.chart_data && <ChartVisualizer data={message.chart_data} />}

                {message.sources && message.sources.length > 0 && (
                    <div style={{ marginTop: '16px', paddingTop: '14px', borderTop: '1px solid var(--color-edge)' }}>
                        <button onClick={() => setSourcesOpen(!sourcesOpen)} className="flex items-center gap-1.5 text-xs active:opacity-70" style={{ color: 'var(--color-accent)', padding: '4px 0' }}>
                            <FileText size={12} />
                            <span>{message.sources.length} source{message.sources.length > 1 ? 's' : ''}</span>
                            {sourcesOpen ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                        </button>
                        {sourcesOpen && (
                            <div className="anim-fade" style={{ marginTop: '8px' }}>
                                {message.sources.map((src, i) => (
                                    <div key={i} className="text-xs" style={{ backgroundColor: 'var(--color-elevated)', border: '1px solid var(--color-edge)', borderRadius: '10px', padding: '12px 14px', marginBottom: '6px' }}>
                                        <span className="font-medium" style={{ color: 'var(--color-accent)' }}>{src.filename}</span>
                                        <p className="line-clamp-2" style={{ color: 'var(--color-muted)', marginTop: '4px' }}>{src.content}</p>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {message.confidence !== undefined && (
                    <p className="text-[10px]" style={{ color: 'var(--color-muted)', marginTop: '12px' }}>✨ {Math.round(message.confidence * 100)}% confidence</p>
                )}
            </div>

            {/* Action buttons */}
            <div className="flex items-center gap-0.5" style={{ marginTop: '6px', marginLeft: '4px' }}>
                {[
                    { icon: <Copy size={14} />, fn: handleCopy, title: copied ? 'Copied!' : 'Copy' },
                    { icon: <Volume2 size={14} />, fn: handleSpeak, title: 'Read aloud' },
                    { icon: <ThumbsUp size={14} />, fn: () => { }, title: 'Helpful' },
                    { icon: <ThumbsDown size={14} />, fn: () => { }, title: 'Not helpful' },
                    { icon: <RotateCcw size={14} />, fn: () => { }, title: 'Regenerate' },
                ].map((btn, i) => (
                    <button
                        key={i}
                        onClick={btn.fn}
                        title={btn.title}
                        className="rounded transition-all active:scale-90"
                        style={{ color: 'var(--color-muted)', padding: '6px' }}
                    >
                        {btn.icon}
                    </button>
                ))}
            </div>
        </div>
    );
};

export default MessageBubble;
