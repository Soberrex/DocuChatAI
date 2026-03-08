import React, { useState, useEffect, useCallback, useRef } from 'react';
import type { ChangeEvent } from 'react';
import { MessageSquare, FolderOpen, Send, Paperclip, Sun, Moon, Plus, AlertCircle } from 'lucide-react';
import Sidebar from './components/Sidebar';
import WelcomeView from './components/WelcomeView';
import ChatInterface from './components/ChatInterface';
import KnowledgeBase from './components/KnowledgeBase';
import { useResponsive } from './hooks/useResponsive';
import { v4 as uuidv4 } from 'uuid';
import {
  uploadDocument,
  sendMessage as sendChatMessage,
  getDocuments,
  getConversations,
  createConversation,
  deleteConversation as apiDeleteConversation,
  getConversationHistory,
} from './services/api';

/* ── Session Management ────────────────────────────── */
function getSessionId(): string {
  let sid = localStorage.getItem('session_id');
  if (!sid) {
    sid = uuidv4();
    localStorage.setItem('session_id', sid);
  }
  return sid;
}

/* ── Drag-to-Resize Hook ─────────────────────────── */
function usePanelResize(
  initialWidth: number,
  minWidth: number,
  maxWidth: number,
  storageKey: string,
  direction: 'left' | 'right' = 'left',
) {
  const [width, setWidth] = useState<number>(() => {
    const saved = localStorage.getItem(storageKey);
    return saved ? Math.max(minWidth, Math.min(maxWidth, Number(saved))) : initialWidth;
  });
  const dragging = useRef(false);
  const startX = useRef(0);
  const startW = useRef(0);

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    dragging.current = true;
    startX.current = e.clientX;
    startW.current = width;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';

    const onMove = (ev: MouseEvent) => {
      if (!dragging.current) return;
      const delta = ev.clientX - startX.current;
      const newW = direction === 'left'
        ? Math.max(minWidth, Math.min(maxWidth, startW.current + delta))
        : Math.max(minWidth, Math.min(maxWidth, startW.current - delta));
      setWidth(newW);
    };

    const onUp = () => {
      dragging.current = false;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
      setWidth((w) => { localStorage.setItem(storageKey, String(w)); return w; });
    };

    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
  }, [width, minWidth, maxWidth, storageKey, direction]);

  return { width, onMouseDown };
}

/* ── App ──────────────────────────────────────────── */
function App() {
  const { isMobile, isTablet, isDesktop } = useResponsive();
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark');
  const [mobilePanel, setMobilePanel] = useState<'chat' | 'files'>('chat');
  const [messages, setMessages] = useState<any[]>([]);
  const [documents, setDocuments] = useState<any[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [conversations, setConversations] = useState<any[]>([]);
  const [tabletFilesOpen, setTabletFilesOpen] = useState(false);
  const [sidebarExpanded, setSidebarExpanded] = useState(() => localStorage.getItem('sidebar_expanded') !== 'false');
  const [sidebarWidth, setSidebarWidth] = useState(() => {
    const saved = localStorage.getItem('sidebar_expanded');
    return saved === 'false' ? 60 : 220;
  });
  const [error, setError] = useState<string | null>(null);
  const [sessionId] = useState(getSessionId);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Resizable panels
  const kbPanel = usePanelResize(380, 280, 550, 'kb_w', 'right');

  const toggleSidebar = () => {
    setSidebarExpanded((prev) => {
      const next = !prev;
      localStorage.setItem('sidebar_expanded', String(next));
      const newWidth = next ? 220 : 60;
      setSidebarWidth(newWidth);
      return next;
    });
  };

  useEffect(() => {
    document.documentElement.className = theme;
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => setTheme((t) => (t === 'dark' ? 'light' : 'dark'));

  // ── Load data from backend on mount ──
  useEffect(() => {
    loadConversations();
    loadDocuments();
  }, [sessionId]);

  const loadConversations = async () => {
    try {
      const convs = await getConversations(sessionId);
      setConversations(convs.map((c: any) => ({ id: c.id, title: c.title })));
    } catch (e) {
      console.warn('Could not load conversations (backend may be offline):', e);
      // Keep empty — this is fine for first use
    }
  };

  const loadDocuments = async () => {
    try {
      const docs = await getDocuments(sessionId);
      setDocuments(docs);
    } catch (e) {
      console.warn('Could not load documents (backend may be offline):', e);
    }
  };

  const showWelcome = messages.length === 0;

  // ── Send message to real backend ──
  const handleSendMessage = async (msg: string) => {
    setError(null);

    // Optimistic UI: show user message immediately
    const userMsg = {
      id: uuidv4(),
      role: 'user',
      content: msg,
      created_at: new Date().toISOString(),
    };
    setMessages((p) => [...p, userMsg]);
    setIsProcessing(true);

    try {
      // Create conversation if needed
      let cid = conversationId;
      if (!cid) {
        const conv = await createConversation(sessionId);
        cid = conv.id;
        setConversationId(cid);
        setConversations((prev) => [{ id: cid, title: msg.slice(0, 50) }, ...prev]);
      }

      // Send to backend
      const response = await sendChatMessage(msg, cid, sessionId);

      // Add assistant response
      setMessages((p) => [...p, {
        ...response.message,
        sources: response.sources,
        chart_data: response.chart_data,
      }]);
    } catch (e: any) {
      console.error('Chat error:', e);
      const errorMsg = e?.response?.data?.detail || e?.message || 'Failed to get response';
      setError(errorMsg);

      // Add fallback error message
      setMessages((p) => [...p, {
        id: uuidv4(),
        role: 'assistant',
        content: `⚠️ ${errorMsg}\n\nPlease check that the backend server is running.`,
        created_at: new Date().toISOString(),
        confidence: 0,
      }]);
    } finally {
      setIsProcessing(false);
    }
  };

  // ── Select conversation & load messages ──
  const handleSelectConversation = async (id: string) => {
    setConversationId(id);
    try {
      const msgs = await getConversationHistory(id);
      setMessages(msgs);
    } catch (e) {
      console.error('Failed to load conversation:', e);
      setMessages([]);
    }
  };

  const handleNewChat = () => {
    setConversationId(null);
    setMessages([]);
    setError(null);
  };

  // ── File upload to real backend ──
  const handleFileUpload = async (file: File) => {
    setUploading(true);
    setError(null);
    try {
      const result: any = await uploadDocument(file, sessionId);
      const docId = result.document_id || result.id;
      // Add to local documents list
      setDocuments((p) => [{
        id: docId,
        filename: result.filename,
        original_filename: result.filename,
        file_size: file.size,
        file_type: file.name.split('.').pop() || '?',
        status: result.status || 'processing',
        created_at: new Date().toISOString(),
      }, ...p]);

      // Poll for status update
      pollDocumentStatus(docId);
    } catch (e: any) {
      console.error('Upload error:', e);
      setError(e?.response?.data?.detail || 'Upload failed. Is the backend running?');
    } finally {
      setUploading(false);
    }
  };

  // ── Poll document processing status ──
  const pollDocumentStatus = (docId: string) => {
    let attempts = 0;
    const maxAttempts = 30; // 30 * 2s = 60s max

    const interval = setInterval(async () => {
      attempts++;
      if (attempts >= maxAttempts) {
        clearInterval(interval);
        return;
      }

      try {
        const docs = await getDocuments(sessionId);
        const doc = docs.find((d: any) => d.id === docId);
        if (doc && doc.status !== 'processing') {
          setDocuments((prev) =>
            prev.map((d) => d.id === docId ? { ...d, status: doc.status, metadata: doc.metadata } : d)
          );
          clearInterval(interval);
        }
      } catch {
        // Silently retry
      }
    }, 2000);
  };

  // ── Delete conversation ──
  const handleDeleteConversation = async (id: string) => {
    try {
      await apiDeleteConversation(id);
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (conversationId === id) {
        handleNewChat();
      }
    } catch (e) {
      console.error('Failed to delete conversation:', e);
    }
  };

  const showFilesPanel = () => {
    if (isMobile) setMobilePanel('files');
    else if (isTablet) setTabletFilesOpen(true);
    else {
      // Desktop: trigger file input directly
      fileInputRef.current?.click();
    }
  };

  const handleFileInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileUpload(file);
      e.target.value = ''; // Reset so same file can be re-uploaded
    }
  };

  const renderChatPanel = () => {
    if (showWelcome) {
      return (
        <div className="flex flex-col h-full">
          <WelcomeView onSendMessage={handleSendMessage} />
          <div className="shrink-0 w-full flex justify-center" style={{ padding: '8px 24px 24px 24px' }}>
            <div className="w-full" style={{ maxWidth: '520px' }}>
              <ChatInput onSend={handleSendMessage} isProcessing={isProcessing} onFileUpload={showFilesPanel} />
            </div>
          </div>
        </div>
      );
    }
    return (
      <ChatInterface messages={messages} onSendMessage={handleSendMessage} isProcessing={isProcessing} onFileUpload={showFilesPanel} />
    );
  };

  /* ── Error Banner ──────────────────────────────────── */
  const errorBanner = error ? (
    <div className="flex items-center gap-2 px-4 py-2 text-sm" style={{ backgroundColor: 'rgba(239,68,68,0.1)', color: 'var(--color-danger)', borderBottom: '1px solid var(--color-edge)' }}>
      <AlertCircle size={14} />
      <span>{error}</span>
      <button onClick={() => setError(null)} className="ml-auto text-xs opacity-60 hover:opacity-100">✕</button>
    </div>
  ) : null;

  /* ── MOBILE ──────────────────────────────────────── */
  if (isMobile) {
    return (
      <div className="h-screen w-screen flex flex-col overflow-hidden" style={{ backgroundColor: 'var(--color-surface)' }}>
        {errorBanner}
        <div className="flex-1 overflow-hidden" style={{ paddingBottom: '56px' }}>
          {mobilePanel === 'chat' ? renderChatPanel() : (
            <KnowledgeBase documents={documents} onFileUpload={handleFileUpload} uploading={uploading} onDocumentDeleted={(id) => setDocuments((p) => p.filter((d) => d.id !== id))} />
          )}
        </div>
        <div className="fixed bottom-0 left-0 right-0 flex items-stretch z-40" style={{ backgroundColor: 'var(--color-sidebar)', borderTop: '1px solid var(--color-edge)', height: '56px' }}>
          <NavBtn icon={<Plus size={18} />} label="New" onClick={handleNewChat} active={false} isLogo />
          <NavBtn icon={<MessageSquare size={18} />} label="Chat" onClick={() => setMobilePanel('chat')} active={mobilePanel === 'chat'} />
          <NavBtn icon={<FolderOpen size={18} />} label="Files" onClick={() => setMobilePanel('files')} active={mobilePanel === 'files'} />
          <NavBtn icon={theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />} label={theme === 'dark' ? 'Light' : 'Dark'} onClick={toggleTheme} active={false} />
        </div>
      </div>
    );
  }

  /* ── TABLET ──────────────────────────────────────── */
  if (isTablet) {
    return (
      <div className="h-screen w-screen flex overflow-hidden" style={{ backgroundColor: 'var(--color-surface)' }}>
        <Sidebar activeTab={showWelcome ? 'home' : 'chat'} setActiveTab={() => { }} theme={theme} toggleTheme={toggleTheme} conversations={conversations} onNewChat={handleNewChat} onSelectConversation={handleSelectConversation} currentConversationId={conversationId} expanded={sidebarExpanded} onToggleExpand={toggleSidebar} />
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
          {errorBanner}
          {renderChatPanel()}
        </div>
        {tabletFilesOpen && (
          <>
            <div className="fixed inset-0 z-30" style={{ backgroundColor: 'rgba(0,0,0,0.4)' }} onClick={() => setTabletFilesOpen(false)} />
            <div className="fixed top-0 right-0 h-full z-40 flex flex-col anim-fade" style={{ width: '360px', backgroundColor: 'var(--color-surface)', borderLeft: '1px solid var(--color-edge)' }}>
              <div className="flex items-center justify-between px-5 py-3" style={{ borderBottom: '1px solid var(--color-edge)' }}>
                <span className="text-sm font-semibold" style={{ color: 'var(--color-primary)' }}>Knowledge Base</span>
                <button onClick={() => setTabletFilesOpen(false)} className="p-1.5 rounded-lg" style={{ color: 'var(--color-muted)' }}>✕</button>
              </div>
              <KnowledgeBase documents={documents} onFileUpload={handleFileUpload} uploading={uploading} onDocumentDeleted={(id) => setDocuments((p) => p.filter((d) => d.id !== id))} />
            </div>
          </>
        )}
      </div>
    );
  }

  /* ── DESKTOP — with drag-to-resize handles ──────── */
  return (
    <div className="h-screen w-screen flex overflow-hidden" style={{ backgroundColor: 'var(--color-surface)' }}>
      {/* Hidden file input for upload */}
      <input ref={fileInputRef} type="file" className="hidden" onChange={handleFileInputChange} accept=".pdf,.docx,.xlsx,.csv,.txt,.md" />
      {/* Left Sidebar */}
      <div className="shrink-0 h-full relative transition-all duration-200" style={{ width: `${sidebarWidth}px`, borderRight: '1px solid var(--color-edge)' }}>
        <Sidebar
          activeTab={showWelcome ? 'home' : 'chat'}
          setActiveTab={() => { }}
          theme={theme}
          toggleTheme={toggleTheme}
          conversations={conversations}
          onNewChat={handleNewChat}
          onSelectConversation={handleSelectConversation}
          currentConversationId={conversationId}
          expanded={sidebarExpanded}
          onToggleExpand={toggleSidebar}
        />

      </div>

      {/* Chat Panel — fills remaining space */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {errorBanner}
        {renderChatPanel()}
      </div>

      {/* Knowledge Base — resizable */}
      <div className="shrink-0 h-full relative" style={{ width: `${kbPanel.width}px`, borderLeft: '1px solid var(--color-edge)' }}>
        <DragHandle side="left" onMouseDown={kbPanel.onMouseDown} />
        <KnowledgeBase documents={documents} onFileUpload={handleFileUpload} uploading={uploading} onDocumentDeleted={(id) => setDocuments((p) => p.filter((d) => d.id !== id))} />
      </div>
    </div>
  );
}

/* ── Drag Handle ─────────────────────────────────── */
function DragHandle({ side, onMouseDown }: { side: 'left' | 'right'; onMouseDown: (e: React.MouseEvent) => void }) {
  return (
    <div
      onMouseDown={onMouseDown}
      className="drag-handle-zone"
      style={{
        position: 'absolute',
        top: 0,
        bottom: 0,
        width: '8px',
        [side === 'right' ? 'right' : 'left']: '-4px',
        cursor: 'col-resize',
        zIndex: 20,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <div
        className="drag-handle-line"
        style={{
          width: '2px',
          height: '100%',
          borderRadius: '1px',
          backgroundColor: 'var(--color-edge)',
          transition: 'background-color 0.2s ease, width 0.2s ease',
        }}
        onMouseEnter={(e) => {
          const el = e.currentTarget as HTMLElement;
          el.style.backgroundColor = 'var(--color-accent)';
          el.style.width = '3px';
        }}
        onMouseLeave={(e) => {
          const el = e.currentTarget as HTMLElement;
          el.style.backgroundColor = 'var(--color-edge)';
          el.style.width = '2px';
        }}
      />
    </div>
  );
}

/* ── Sub-Components ───────────────────────────────── */
function NavBtn({ icon, label, onClick, active, isLogo }: { icon: React.ReactNode; label: string; onClick: () => void; active: boolean; isLogo?: boolean }) {
  return (
    <button onClick={onClick} className="flex-1 flex flex-col items-center justify-center gap-0.5" style={{ color: active ? 'var(--color-accent)' : 'var(--color-muted)' }}>
      {isLogo ? <div className="w-7 h-7 grad-copper rounded-lg flex items-center justify-center"><span className="text-white">{icon}</span></div> : icon}
      <span className="text-[10px] leading-none">{label}</span>
    </button>
  );
}

function ChatInput({ onSend, isProcessing, onFileUpload }: { onSend: (m: string) => void; isProcessing: boolean; onFileUpload?: () => void }) {
  const [input, setInput] = useState('');
  const handleSend = () => { const t = input.trim(); if (!t || isProcessing) return; onSend(t); setInput(''); };

  return (
    <>
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
      <p className="text-[10px] text-center mt-2" style={{ color: 'var(--color-muted)' }}>
        DocuChat AI can make mistakes. Verify important information.
      </p>
    </>
  );
}

export default App;
