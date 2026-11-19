import { useRef, useState } from 'react';
import { useChatContext } from '../context/ChatContext';

const STARTER_QUESTIONS = [
  "What is the minimum attendance required?",
  "Explain the grading scale and CGPA classification.",
  "What are the examination malpractice penalties?",
  "What is the hostel entry/exit timing policy?",
  "Summarise the fee refund policy on withdrawal.",
  "What is the college anti-ragging zero tolerance policy?",
];

function DocCard({ doc, onReplaceClick, isDefaultPolicy, onResetDefault, isLoading }) {
  const fileIcon = { pdf: '📄', docx: '📝', txt: '📃', md: '📋' };
  return (
    <div className="doc-card-container">
      <div className="doc-card">
        <span className="doc-icon">{fileIcon[doc.file_type] || '📁'}</span>
        <div className="doc-info">
          <div className="doc-name" title={doc.name}>{doc.name}</div>
          <div className="doc-meta">{doc.page_count} pages · {doc.token_count?.toLocaleString()} tokens</div>
          <div className="doc-meta" style={{ marginTop: 3, display: 'flex', gap: 6, alignItems: 'center' }}>
            <span className="doc-badge">{doc.mode} mode</span>
            {isDefaultPolicy ? (
              <span className="doc-badge-default">Standard Policy</span>
            ) : (
              <span className="doc-badge-custom">Custom Policy</span>
            )}
          </div>
        </div>
      </div>

      <div className="doc-actions-row">
        <button
          className="btn btn-primary btn-sm"
          style={{ flex: 1, fontSize: '11px', padding: '6px 8px' }}
          onClick={onReplaceClick}
          disabled={isLoading}
          title="Upload or paste a new document to replace this policy"
        >
          🔄 Replace Policy
        </button>
        {!isDefaultPolicy && (
          <button
            className="btn btn-outline btn-sm"
            style={{ fontSize: '11px', padding: '6px 8px' }}
            onClick={onResetDefault}
            disabled={isLoading}
            title="Restore default Meridian College Policy Handbook"
          >
            🏫 Restore Default
          </button>
        )}
      </div>
    </div>
  );
}

export default function InfoPanel() {
  const { activeDoc, ask, uploadDoc, pasteDoc, resetToDefaultPolicy, clearSession, isLoading } = useChatContext();
  const fileRef = useRef(null);
  const replaceFileRef = useRef(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [showReplaceModal, setShowReplaceModal] = useState(false);

  const isDefault = activeDoc?.name?.toLowerCase().includes("meridian college");

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) uploadDoc(file);
  };

  return (
    <div className="info-panel">
      {/* Quick Access */}
      <div className="info-panel-section">
        <h3>⚡ Quick Access</h3>
        <div className="starter-list">
          {STARTER_QUESTIONS.map((q, i) => (
            <button key={i} className="starter-item" onClick={() => ask(q)} disabled={isLoading}>
              <span className="si-icon">💬</span>
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Active Document */}
      <div className="info-panel-section">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
          <h3 style={{ margin: 0 }}>📂 Active Knowledge Source</h3>
        </div>
        {activeDoc ? (
          <DocCard
            doc={activeDoc}
            isDefaultPolicy={isDefault}
            onReplaceClick={() => setShowReplaceModal(true)}
            onResetDefault={resetToDefaultPolicy}
            isLoading={isLoading}
          />
        ) : (
          <div style={{ fontSize: 12, color: '#aaa' }}>No document loaded.</div>
        )}
      </div>

      {/* Upload New Document Dropzone */}
      <div className="info-panel-section">
        <h3>📤 Add / Upload Document</h3>
        <div
          className={`upload-zone ${isDragOver ? 'drag-over' : ''}`}
          onClick={() => fileRef.current?.click()}
          onDrop={handleDrop}
          onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
          onDragLeave={() => setIsDragOver(false)}
        >
          <span className="upload-zone-icon">☁️</span>
          <p><strong>Click or drag & drop</strong><br />PDF, DOCX, TXT, MD · Max 20 MB</p>
        </div>
        <input ref={fileRef} type="file" accept=".pdf,.docx,.txt,.md" style={{ display: 'none' }}
          onChange={(e) => { const f = e.target.files?.[0]; if (f) uploadDoc(f); e.target.value = ''; }} />
      </div>

      {/* Controls */}
      <div className="info-panel-section">
        <h3>⚙️ Controls</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <button className="btn btn-outline btn-sm full-width" onClick={resetToDefaultPolicy} disabled={isLoading}>
            🏫 Reset to Meridian College Handbook
          </button>
          <button className="btn btn-danger btn-sm full-width" onClick={clearSession} disabled={isLoading}>
            🗑️ Clear Chat & Session
          </button>
        </div>
      </div>

      {/* Latest Update Banner */}
      <div className="info-panel-section" style={{ marginTop: 'auto', background: '#6B0F1A', borderRadius: 10, margin: 12, padding: '14px 14px' }}>
        <div style={{ color: '#D4AF37', fontSize: 12, fontWeight: 700, marginBottom: 5 }}>📢 Meridian College Updates</div>
        <div style={{ color: 'rgba(255,255,255,0.85)', fontSize: 12, lineHeight: 1.5 }}>
          Academic Year 2026-2027 Handbook in effect. All policies active.
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginTop: 8 }}>
          <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#4CAF50', display: 'inline-block' }}></span>
          <span style={{ color: '#4CAF50', fontSize: 11, fontWeight: 600 }}>RAG Engine Active</span>
          <span style={{ color: 'rgba(255,255,255,0.4)', fontSize: 11, marginLeft: 'auto' }}>DocuChat v1.0</span>
        </div>
      </div>

      {/* Replace Policy Document Modal */}
      {showReplaceModal && (
        <ReplaceDocModal
          onClose={() => setShowReplaceModal(false)}
          onUploadFile={(file) => { uploadDoc(file); setShowReplaceModal(false); }}
          onPasteText={(text, title) => { pasteDoc(text, title); setShowReplaceModal(false); }}
          currentDocName={activeDoc?.name}
        />
      )}
    </div>
  );
}

function ReplaceDocModal({ onClose, onUploadFile, onPasteText, currentDocName }) {
  const [tab, setTab] = useState('upload'); // 'upload' or 'paste'
  const [pastedText, setPastedText] = useState('');
  const [docName, setDocName] = useState('');
  const fileInputRef = useRef(null);

  const handleFile = (e) => {
    const f = e.target.files?.[0];
    if (f) onUploadFile(f);
  };

  const handlePasteSubmit = (e) => {
    e.preventDefault();
    if (!pastedText.trim()) return;
    onPasteText(pastedText.trim(), docName || 'Replacement Policy');
  };

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" style={{ maxWidth: 520 }}>
        <h2>🔄 Replace Policy Document</h2>
        <p style={{ marginBottom: 12 }}>
          Replacing the policy document will index the new file and reset the chat context according to <strong>SRS FR-08</strong>.
        </p>

        <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
          <button
            className={`tool-pill ${tab === 'upload' ? 'active' : ''}`}
            onClick={() => setTab('upload')}
          >
            📁 Upload File (PDF / DOCX / TXT / MD)
          </button>
          <button
            className={`tool-pill ${tab === 'paste' ? 'active' : ''}`}
            onClick={() => setTab('paste')}
          >
            📋 Paste Plain Text
          </button>
        </div>

        {tab === 'upload' ? (
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <div
              className="upload-zone"
              onClick={() => fileInputRef.current?.click()}
              style={{ padding: 30 }}
            >
              <span className="upload-zone-icon" style={{ fontSize: 36 }}>📑</span>
              <p style={{ marginTop: 8 }}>
                <strong>Select a new Policy Document</strong><br />
                PDF, DOCX, TXT or Markdown (max 20 MB, 300 pages)
              </p>
              <button
                type="button"
                className="btn btn-primary btn-sm"
                style={{ marginTop: 12 }}
                onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click(); }}
              >
                Choose File from Computer
              </button>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.txt,.md"
              style={{ display: 'none' }}
              onChange={handleFile}
            />
          </div>
        ) : (
          <form onSubmit={handlePasteSubmit}>
            <input
              className="modal-input"
              placeholder="Document Title (e.g., Code of Conduct 2027)"
              value={docName}
              onChange={(e) => setDocName(e.target.value)}
            />
            <textarea
              className="modal-textarea"
              placeholder="Paste the full policy text here (up to 100,000 characters)..."
              value={pastedText}
              onChange={(e) => setPastedText(e.target.value)}
              rows={8}
            />
            <div style={{ fontSize: 11, color: '#888', marginBottom: 10, textAlign: 'right' }}>
              {pastedText.length.toLocaleString()} / 100,000 characters
            </div>
            <div className="modal-actions">
              <button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={!pastedText.trim()}
              >
                Apply Replacement
              </button>
            </div>
          </form>
        )}

        {tab === 'upload' && (
          <div className="modal-actions" style={{ marginTop: 10 }}>
            <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
          </div>
        )}
      </div>
    </div>
  );
}
