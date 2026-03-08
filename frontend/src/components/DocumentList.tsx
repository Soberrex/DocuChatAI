import React, { useState } from 'react';
import { FileText, CheckCircle, Clock, AlertCircle, Trash2, X } from 'lucide-react';

interface Document {
    id: string;
    filename: string;
    original_filename: string;
    file_size: number;
    file_type: string;
    status: 'processing' | 'ready' | 'failed';
    created_at: string;
}

interface DocumentListProps {
    documents: Document[];
    onDocumentDeleted?: (id: string) => void;
}

const DocumentList = ({ documents, onDocumentDeleted }: DocumentListProps) => {
    const [deleteId, setDeleteId] = useState<string | null>(null);

    const formatFileSize = (bytes: number) => {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    };

    const statusConfig = (s: string) => {
        if (s === 'ready') return { icon: <CheckCircle size={12} />, color: '#22c55e', bg: 'rgba(34,197,94,0.12)', border: 'rgba(34,197,94,0.2)' };
        if (s === 'processing') return { icon: <Clock size={12} />, color: '#f59e0b', bg: 'rgba(245,158,11,0.12)', border: 'rgba(245,158,11,0.2)' };
        return { icon: <AlertCircle size={12} />, color: '#ef4444', bg: 'rgba(239,68,68,0.12)', border: 'rgba(239,68,68,0.2)' };
    };

    return (
        <div className="space-y-1.5">
            {documents.length === 0 ? (
                <div className="text-center" style={{ padding: '24px 12px' }}>
                    <FileText size={28} className="mx-auto" style={{ color: 'var(--color-muted)', opacity: 0.2, marginBottom: '8px' }} />
                    <p className="text-xs" style={{ color: 'var(--color-muted)' }}>No documents uploaded</p>
                </div>
            ) : (
                documents.map((doc) => {
                    const status = statusConfig(doc.status);
                    return (
                        <div
                            key={doc.id}
                            className="group flex items-center gap-3 rounded-lg transition-all"
                            style={{ padding: '10px 12px', minHeight: '52px' }}
                        >
                            {/* File Icon */}
                            <div
                                className="shrink-0 flex items-center justify-center"
                                style={{
                                    width: '36px',
                                    height: '36px',
                                    borderRadius: '10px',
                                    backgroundColor: 'rgba(224,90,43,0.12)',
                                }}
                            >
                                <FileText size={16} style={{ color: 'var(--color-accent)' }} />
                            </div>

                            {/* File Info */}
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium truncate" style={{ color: 'var(--color-primary)' }}>{doc.original_filename}</p>
                                <div className="flex items-center gap-2" style={{ marginTop: '4px' }}>
                                    <span
                                        className="inline-flex items-center gap-1 text-[10px] rounded-full"
                                        style={{
                                            color: status.color,
                                            backgroundColor: status.bg,
                                            border: `1px solid ${status.border}`,
                                            padding: '2px 8px',
                                        }}
                                    >
                                        <span style={{ color: status.color }}>{status.icon}</span>
                                        {doc.status}
                                    </span>
                                    <span className="text-[10px]" style={{ color: 'var(--color-muted)' }}>{formatFileSize(doc.file_size)}</span>
                                </div>
                            </div>

                            {/* Delete */}
                            <button
                                onClick={() => setDeleteId(doc.id)}
                                className="opacity-0 group-hover:opacity-100 p-1.5 rounded transition-all shrink-0 active:scale-90"
                                style={{ color: 'var(--color-muted)' }}
                            >
                                <Trash2 size={14} />
                            </button>
                        </div>
                    );
                })
            )}

            {/* Delete Confirmation */}
            {deleteId && (
                <div className="fixed inset-0 flex items-center justify-center z-[100] anim-fade" style={{ backgroundColor: 'rgba(0,0,0,0.6)' }}>
                    <div className="max-w-sm w-full mx-4 shadow-2xl" style={{ backgroundColor: 'var(--color-card)', border: '1px solid var(--color-edge)', borderRadius: '12px', padding: '20px' }}>
                        <div className="flex items-center justify-between" style={{ marginBottom: '12px' }}>
                            <h3 className="text-sm font-semibold" style={{ color: 'var(--color-primary)' }}>Delete Document</h3>
                            <button onClick={() => setDeleteId(null)} className="active:scale-90" style={{ color: 'var(--color-muted)' }}><X size={16} /></button>
                        </div>
                        <p className="text-sm" style={{ color: 'var(--color-secondary)', marginBottom: '16px' }}>Are you sure? This will remove the document and its embeddings.</p>
                        <div className="flex gap-2 justify-end">
                            <button onClick={() => setDeleteId(null)} className="rounded-lg text-sm transition-colors" style={{ padding: '8px 14px', color: 'var(--color-secondary)' }}>Cancel</button>
                            <button onClick={() => { onDocumentDeleted?.(deleteId); setDeleteId(null); }} className="rounded-lg text-sm transition-colors" style={{ padding: '8px 14px', color: 'white', backgroundColor: '#ef4444' }}>Delete</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default DocumentList;
