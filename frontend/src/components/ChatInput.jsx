import { useState, useRef, useEffect } from 'react';
import { useChatContext } from '../context/ChatContext';

export default function ChatInput() {
  const { ask, isLoading, uploadDoc } = useChatContext();
  const [text, setText] = useState('');
  const [showPaste, setShowPaste] = useState(false);
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  const autoResize = () => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = 'auto';
      el.style.height = Math.min(el.scrollHeight, 120) + 'px';
    }
  };

  useEffect(() => { autoResize(); }, [text]);

  const handleSend = () => {
    if (!text.trim() || isLoading) return;
    ask(text.trim());
    setText('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) uploadDoc(file);
    e.target.value = '';
  };

  return (
    <div className="input-area">
      <div className="input-row">
        <textarea
          ref={textareaRef}
          className="chat-textarea"
          placeholder="Ask anything about the college policy…"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          disabled={isLoading}
        />
        <button
          className="send-btn"
          onClick={handleSend}
          disabled={!text.trim() || isLoading}
          title="Send (Enter)"
        >
          ➤
        </button>
      </div>

      <div className="input-tools">
        <button
          className="tool-pill"
          onClick={() => fileInputRef.current?.click()}
          disabled={isLoading}
          title="Upload PDF, DOCX or TXT"
        >
          📎 Upload Doc
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt,.md"
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />
        <button
          className="tool-pill"
          onClick={() => setShowPaste(true)}
          disabled={isLoading}
          title="Paste plain text as document"
        >
          📋 Paste Text
        </button>
        <span style={{ fontSize: 11, color: '#aaa', marginLeft: 'auto' }}>
          Shift+Enter for new line
        </span>
      </div>

      {showPaste && <PasteModal onClose={() => setShowPaste(false)} />}
    </div>
  );
}

function PasteModal({ onClose }) {
  const { pasteDoc } = useChatContext();
  const [text, setText] = useState('');
  const [name, setName] = useState('');

  const handleSubmit = () => {
    if (!text.trim()) return;
    pasteDoc(text, name || 'Pasted Document');
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <h2>📋 Paste Document Text</h2>
        <p>Paste text from any document and DocuChat will use it as the knowledge source.</p>
        <input
          className="modal-input"
          placeholder="Document name (optional)"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <textarea
          className="modal-textarea"
          placeholder="Paste document text here…"
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={8}
        />
        <div className="modal-actions">
          <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={handleSubmit} disabled={!text.trim()}>
            Load Document
          </button>
        </div>
      </div>
    </div>
  );
}
