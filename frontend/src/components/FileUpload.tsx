import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { FileText } from 'lucide-react';

interface FileUploadProps {
    onFileUpload: (file: File) => void;
    uploading: boolean;
}

const FileUpload = ({ onFileUpload, uploading }: FileUploadProps) => {
    const onDrop = useCallback((files: File[]) => { if (files.length > 0) onFileUpload(files[0]); }, [onFileUpload]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'application/pdf': ['.pdf'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
            'application/vnd.ms-excel': ['.xls'],
            'text/plain': ['.txt'],
            'text/csv': ['.csv'],
        },
        multiple: false,
        disabled: uploading,
    });

    return (
        <div
            {...getRootProps()}
            className={`w-full cursor-pointer transition-all ${uploading ? 'cursor-not-allowed opacity-70' : ''}`}
            style={{ borderRadius: '16px' }}
        >
            <input {...getInputProps()} />
            <div
                className={`w-full flex flex-col items-center justify-center transition-all ${isDragActive ? 'grad-copper' : 'grad-copper-soft'}`}
                style={{
                    borderRadius: '16px',
                    padding: '40px 20px',
                    border: isDragActive ? '2px solid var(--color-accent)' : '1px solid rgba(224,90,43,0.2)',
                }}
            >
                <div
                    className="w-12 h-12 rounded-xl flex items-center justify-center"
                    style={{ background: 'rgba(10,10,10,0.3)', marginBottom: '12px' }}
                >
                    {uploading ? (
                        <div className="w-5 h-5 rounded-full animate-spin" style={{ border: '2px solid var(--color-accent)', borderTopColor: 'transparent' }} />
                    ) : (
                        <FileText size={22} style={{ color: 'var(--color-secondary)' }} />
                    )}
                </div>
                <p className="text-sm font-medium" style={{ color: 'var(--color-primary)', marginBottom: '4px' }}>
                    {isDragActive ? 'Drop your file here' : uploading ? 'Processing...' : 'Choose File or Drag & Drop it here'}
                </p>
                <p className="text-xs" style={{ color: 'var(--color-muted)' }}>xls, xlsx, csv, pdf, docx, txt Formats</p>
                {uploading && (
                    <div className="w-40 h-1 rounded-full overflow-hidden" style={{ background: 'rgba(10,10,10,0.3)', marginTop: '12px' }}>
                        <div className="h-full rounded-full animate-pulse" style={{ width: '60%', backgroundColor: 'var(--color-accent)' }} />
                    </div>
                )}
            </div>
        </div>
    );
};

export default FileUpload;
