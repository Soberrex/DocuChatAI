import React, { useState } from 'react';
import {
    Plus,
    History,
    Sun,
    Moon,
    Star,
    X,
    FileText,
    MessageSquare,
    PanelLeftOpen,
    PanelLeftClose,
} from 'lucide-react';

interface SidebarProps {
    activeTab: string;
    setActiveTab: (tab: string) => void;
    theme: string;
    toggleTheme: () => void;
    conversations?: { id: string; title: string }[];
    onNewChat?: () => void;
    onSelectConversation?: (id: string) => void;
    currentConversationId?: string | null;
    expanded: boolean;
    onToggleExpand: () => void;
}

const COLLAPSED_W = 60;
const EXPANDED_W = 220;

const Sidebar = ({
    activeTab,
    setActiveTab,
    theme,
    toggleTheme,
    conversations = [],
    onNewChat,
    onSelectConversation,
    currentConversationId,
    expanded,
    onToggleExpand,
}: SidebarProps) => {
    const [historyOpen, setHistoryOpen] = useState(false);

    return (
        <>
            {/* Sidebar — collapses/expands */}
            <div
                className="h-full w-full flex flex-col z-50 relative overflow-hidden"
                style={{
                    backgroundColor: 'var(--color-sidebar)',
                    paddingTop: '16px',
                    paddingBottom: '20px',
                }}
            >
                {/* Logo + Toggle Row */}
                <div className="flex items-center shrink-0" style={{ padding: expanded ? '0 14px 0 14px' : '0', justifyContent: expanded ? 'space-between' : 'center', marginBottom: '12px' }}>
                    <button
                        onClick={() => setActiveTab('home')}
                        className="flex items-center gap-2.5 hover:scale-105 transition-transform"
                    >
                        <div className="w-9 h-9 grad-copper rounded-lg flex items-center justify-center shadow-lg shrink-0">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" className="text-white">
                                <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                                <path d="M2 17L12 22L22 17" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                                <path d="M2 12L12 17L22 12" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                        </div>
                        {expanded && <span className="text-sm font-bold" style={{ color: 'var(--color-primary)', whiteSpace: 'nowrap' }}>DocuChat</span>}
                    </button>
                    {expanded && (
                        <button onClick={onToggleExpand} className="p-1.5 rounded-lg transition-all active:scale-90" style={{ color: 'var(--color-muted)' }}>
                            <PanelLeftClose size={18} />
                        </button>
                    )}
                </div>

                {/* Nav Buttons */}
                <div className="flex flex-col gap-1" style={{ padding: expanded ? '0 10px' : '0 8px' }}>
                    <SidebarBtn icon={<Plus size={18} />} label="New Chat" expanded={expanded} onClick={onNewChat} />
                    <SidebarBtn icon={<History size={18} />} label="History" expanded={expanded} onClick={() => setHistoryOpen(!historyOpen)} active={historyOpen} />
                </div>

                {/* Spacer */}
                <div className="flex-1" />

                {/* Bottom Actions */}
                <div className="flex flex-col gap-1" style={{ padding: expanded ? '0 10px' : '0 8px' }}>
                    {!expanded && (
                        <SidebarBtn icon={<PanelLeftOpen size={18} />} label="Expand" expanded={false} onClick={onToggleExpand} />
                    )}
                    <SidebarBtn icon={theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />} label={theme === 'dark' ? 'Light' : 'Dark'} expanded={expanded} onClick={toggleTheme} />
                    <SidebarBtn icon={<Star size={16} />} label="Favorites" expanded={expanded} />
                </div>

                {/* Avatar */}
                <div style={{ padding: expanded ? '12px 14px 0 14px' : '12px 0 0 0', display: 'flex', justifyContent: expanded ? 'flex-start' : 'center' }}>
                    <div
                        className="overflow-hidden cursor-pointer flex items-center justify-center text-white text-xs font-semibold"
                        style={{ width: '32px', height: '32px', borderRadius: '50%', background: 'linear-gradient(135deg, rgba(224,90,43,0.6), rgba(224,90,43,0.3))' }}
                    >
                        U
                    </div>
                </div>
            </div>

            {/* History Panel Overlay */}
            {historyOpen && (
                <>
                    <div
                        className="fixed inset-0 z-40"
                        style={{ backgroundColor: 'rgba(0,0,0,0.4)' }}
                        onClick={() => setHistoryOpen(false)}
                    />
                    <div
                        className="fixed top-0 h-full z-50 flex flex-col anim-slide shadow-2xl"
                        style={{
                            left: expanded ? '220px' : '60px',
                            width: '280px',
                            backgroundColor: 'var(--color-sidebar)',
                            borderRight: '1px solid var(--color-edge)',
                        }}
                    >
                        {/* Header */}
                        <div
                            className="flex items-center justify-between"
                            style={{ padding: '16px 20px', borderBottom: '1px solid var(--color-edge)' }}
                        >
                            <h3 className="text-sm font-semibold" style={{ color: 'var(--color-primary)' }}>Your Chats</h3>
                            <button onClick={() => setHistoryOpen(false)} className="p-1.5 rounded-lg transition-colors active:scale-90" style={{ color: 'var(--color-muted)' }}>
                                <X size={16} />
                            </button>
                        </div>

                        {/* New Chat */}
                        <div style={{ padding: '12px 16px' }}>
                            <button
                                onClick={() => { onNewChat?.(); setHistoryOpen(false); }}
                                className="w-full flex items-center justify-center gap-2 rounded-lg text-sm font-medium transition-all active:scale-95"
                                style={{ padding: '12px 16px', backgroundColor: 'var(--color-accent)', color: 'white', minHeight: '44px' }}
                            >
                                <Plus size={16} />
                                New Chat
                            </button>
                        </div>

                        {/* Conversation List */}
                        <div className="flex-1 overflow-y-auto" style={{ padding: '4px 12px 16px 12px' }}>
                            <p className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--color-muted)', padding: '8px 8px 10px 8px' }}>Recent</p>
                            {conversations.length === 0 ? (
                                <div className="text-center" style={{ padding: '24px 12px' }}>
                                    <MessageSquare size={24} className="mx-auto mb-2" style={{ color: 'var(--color-muted)', opacity: 0.4 }} />
                                    <p className="text-xs" style={{ color: 'var(--color-muted)' }}>No conversations yet</p>
                                </div>
                            ) : (
                                <div className="space-y-1">
                                    {conversations.map((conv) => (
                                        <button
                                            key={conv.id}
                                            onClick={() => { onSelectConversation?.(conv.id); setHistoryOpen(false); }}
                                            className="w-full flex items-center gap-3 rounded-lg text-left text-sm transition-all active:scale-[0.98]"
                                            style={{
                                                padding: '10px 12px',
                                                minHeight: '44px',
                                                color: conv.id === currentConversationId ? 'var(--color-accent)' : 'var(--color-secondary)',
                                                backgroundColor: conv.id === currentConversationId ? 'rgba(224,90,43,0.12)' : 'transparent',
                                            }}
                                        >
                                            <FileText size={14} className="shrink-0" style={{ opacity: 0.6 }} />
                                            <span className="truncate">{conv.title}</span>
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </>
            )}
        </>
    );
};

/* ── Sidebar Button ─────────────────────────────── */
function SidebarBtn({
    icon,
    label,
    expanded,
    onClick,
    active,
}: {
    icon: React.ReactNode;
    label: string;
    expanded: boolean;
    onClick?: () => void;
    active?: boolean;
}) {
    return (
        <button
            onClick={onClick}
            className="flex items-center gap-3 rounded-lg transition-all active:scale-95"
            style={{
                padding: expanded ? '10px 12px' : '10px 0',
                justifyContent: expanded ? 'flex-start' : 'center',
                minHeight: '40px',
                color: active ? 'var(--color-accent)' : 'var(--color-secondary)',
                backgroundColor: active ? 'rgba(224,90,43,0.12)' : 'transparent',
                width: '100%',
            }}
            title={label}
        >
            <span className="shrink-0">{icon}</span>
            {expanded && <span className="text-sm whitespace-nowrap" style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>{label}</span>}
        </button>
    );
}

export default Sidebar;
