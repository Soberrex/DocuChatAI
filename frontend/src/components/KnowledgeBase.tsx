import React from 'react';
import FileUpload from './FileUpload';
import DocumentList from './DocumentList';

interface Document {
    id: string;
    filename: string;
    original_filename: string;
    file_size: number;
    file_type: string;
    status: 'processing' | 'ready' | 'failed';
    created_at: string;
}

interface KnowledgeBaseProps {
    documents: Document[];
    onFileUpload: (file: File) => void;
    uploading: boolean;
    onDocumentDeleted?: (id: string) => void;
}

const KnowledgeBase = ({ documents, onFileUpload, uploading, onDocumentDeleted }: KnowledgeBaseProps) => {
    return (
        <div
            className="h-full flex flex-col overflow-y-auto"
            style={{ padding: '24px 20px' }}
        >
            {/* Header */}
            <div style={{ marginBottom: '20px' }}>
                <h2
                    className="text-lg font-bold leading-snug"
                    style={{ color: 'var(--color-primary)' }}
                >
                    Your File Speaks Accurately
                </h2>
                <p className="text-xs" style={{ color: 'var(--color-secondary)', marginTop: '4px' }}>
                    Upload documents to start analyzing
                </p>
            </div>

            {/* File Upload */}
            <FileUpload onFileUpload={onFileUpload} uploading={uploading} />

            {/* Document List */}
            {documents.length > 0 && (
                <div style={{ marginTop: '24px' }}>
                    <h3
                        className="text-[10px] font-semibold uppercase tracking-wider"
                        style={{ color: 'var(--color-muted)', marginBottom: '12px' }}
                    >
                        Uploaded Files ({documents.length})
                    </h3>
                    <DocumentList documents={documents} onDocumentDeleted={onDocumentDeleted} />
                </div>
            )}
        </div>
    );
};

export default KnowledgeBase;
