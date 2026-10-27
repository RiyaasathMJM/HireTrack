// ── pages/Upload.tsx ──────────────────────────────────────────────────────────

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useNavigate } from 'react-router-dom';
import {
  Upload as UploadIcon,
  FileText,
  CheckCircle2,
  X,
  Loader2,
  ArrowRight,
} from 'lucide-react';
import toast from 'react-hot-toast';
import TopBar from '../components/layout/TopBar';
import StageTag from '../components/ui/StageTag';
import candidatesApi from '../api/candidates';
import type { Candidate } from '../types';

interface FileItem {
  file: File;
  status: 'pending' | 'uploading' | 'done' | 'error';
  candidate?: Candidate;
  error?: string;
}

const ACCEPTED_TYPES = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'text/plain': ['.txt'],
};

export default function Upload() {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [uploading, setUploading] = useState(false);
  const navigate = useNavigate();

  const onDrop = useCallback((accepted: File[]) => {
    setFiles(prev => [
      ...prev,
      ...accepted.map(f => ({ file: f, status: 'pending' as const })),
    ]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    multiple: true,
  });

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    const pendingFiles = files.filter(f => f.status === 'pending').map(f => f.file);
    if (pendingFiles.length === 0) return;

    setUploading(true);
    setFiles(prev =>
      prev.map(f => f.status === 'pending' ? { ...f, status: 'uploading' } : f)
    );

    try {
      const res = await candidatesApi.upload(pendingFiles);
      const created = res.data;

      setFiles(prev => {
        let createdIdx = 0;
        return prev.map(f => {
          if (f.status === 'uploading') {
            const candidate = created[createdIdx++];
            return { ...f, status: 'done', candidate };
          }
          return f;
        });
      });

      toast.success(`${created.length} resume${created.length > 1 ? 's' : ''} uploaded!`);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { error?: string } } })?.response?.data?.error ?? 'Upload failed';
      setFiles(prev =>
        prev.map(f => f.status === 'uploading' ? { ...f, status: 'error', error: msg } : f)
      );
      toast.error(msg);
    } finally {
      setUploading(false);
    }
  };

  const pendingCount = files.filter(f => f.status === 'pending').length;
  const doneCount    = files.filter(f => f.status === 'done').length;

  return (
    <div className="page">
      <TopBar title="Upload Resumes" subtitle="Upload PDF, DOCX, or TXT files" />
      <div className="page-content">

        {/* Dropzone */}
        <div
          {...getRootProps()}
          className={`dropzone ${isDragActive ? 'dropzone--active' : ''}`}
          id="resume-dropzone"
        >
          <input {...getInputProps()} id="resume-file-input" />
          <div className="dropzone-content">
            <div className={`dropzone-icon ${isDragActive ? 'dropzone-icon--active' : ''}`}>
              <UploadIcon size={36} />
            </div>
            <h2 className="dropzone-title">
              {isDragActive ? 'Drop files here…' : 'Drag & drop resumes here'}
            </h2>
            <p className="text-muted">or click to browse files (PDF, DOCX, TXT)</p>
          </div>
        </div>

        {/* File list */}
        {files.length > 0 && (
          <div className="upload-file-list">
            {files.map((item, idx) => (
              <div key={idx} className={`upload-file-row upload-file-row--${item.status}`}>
                <div className="upload-file-icon">
                  <FileText size={18} />
                </div>
                <div className="upload-file-info">
                  <p className="upload-file-name">{item.file.name}</p>
                  <p className="upload-file-size text-muted text-sm">
                    {(item.file.size / 1024).toFixed(0)} KB
                    {item.status === 'uploading' && ' · Uploading…'}
                    {item.status === 'error' && ` · Error: ${item.error}`}
                  </p>
                  {item.candidate && (
                    <div className="upload-file-result">
                      <span className="upload-file-parsed">
                        Parsed: <strong>{item.candidate.name || '(no name)'}</strong>
                        {item.candidate.email ? ` · ${item.candidate.email}` : ''}
                      </span>
                      <StageTag stage={item.candidate.stage} />
                    </div>
                  )}
                </div>
                <div className="upload-file-status">
                  {item.status === 'done' && <CheckCircle2 size={18} className="icon-green" />}
                  {item.status === 'uploading' && <Loader2 size={18} className="spin text-muted" />}
                  {item.status === 'error' && <X size={18} className="icon-red" />}
                  {item.status === 'pending' && (
                    <button
                      className="icon-btn"
                      onClick={() => removeFile(idx)}
                      aria-label="Remove file"
                    >
                      <X size={15} />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Actions */}
        {files.length > 0 && (
          <div className="upload-actions">
            {pendingCount > 0 && (
              <button
                className="btn btn-primary"
                onClick={handleUpload}
                disabled={uploading}
              >
                {uploading
                  ? <><Loader2 size={15} className="spin" /> Uploading…</>
                  : <><UploadIcon size={15} /> Upload {pendingCount} File{pendingCount > 1 ? 's' : ''}</>
                }
              </button>
            )}
            {doneCount > 0 && (
              <button
                className="btn btn-ghost"
                onClick={() => navigate('/candidates')}
              >
                View Candidates <ArrowRight size={15} />
              </button>
            )}
            <button
              className="btn btn-ghost"
              onClick={() => setFiles([])}
              disabled={uploading}
            >
              Clear All
            </button>
          </div>
        )}

        {/* Tips */}
        <div className="upload-tips card">
          <h3 className="card-title">Tips</h3>
          <ul className="upload-tips-list">
            <li>Supports <strong>PDF</strong>, <strong>DOCX</strong>, and <strong>TXT</strong> formats</li>
            <li>Upload multiple resumes at once — each becomes a separate candidate</li>
            <li>Skills, name, email and phone are automatically extracted</li>
            <li>After upload, use <strong>Match All</strong> on a Job Description to score candidates</li>
          </ul>
        </div>

      </div>
    </div>
  );
}
