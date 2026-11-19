import ReactMarkdown from 'react-markdown';
import { useChatContext } from '../context/ChatContext';

function CitationsBlock({ citations }) {
  if (!citations || citations.length === 0) return null;
  return (
    <div className="citations-block">
      <h4>📌 Sources</h4>
      {citations.map((c, i) => (
        <div key={i} className="citation-item">
          <span className="citation-badge">p.{c.page || '?'}</span>
          <span className="citation-text">
            <strong>{c.section || 'Reference'}</strong>
            {c.excerpt ? ` — "${c.excerpt.slice(0, 90)}${c.excerpt.length > 90 ? '…' : ''}"` : ''}
          </span>
        </div>
      ))}
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="message-row bot">
      <div className="avatar bot">🎓</div>
      <div className="message-content">
        <div className="typing-indicator">
          <div className="typing-dot" />
          <div className="typing-dot" />
          <div className="typing-dot" />
        </div>
      </div>
    </div>
  );
}

export default function MessageList({ messages, isLoading }) {
  const { rateBotMessage } = useChatContext();

  const getBubbleClass = (status) => {
    if (status === 'ERROR') return 'bot error';
    if (status === 'OUT_OF_SCOPE') return 'bot out-of-scope';
    if (status === 'NOT_FOUND') return 'bot not-found';
    return 'bot';
  };

  const formatTime = (iso) => {
    if (!iso) return '';
    const d = new Date(iso);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <>
      {messages.map((msg) => (
        <div key={msg.id} className={`message-row ${msg.role}`}>
          <div className={`avatar ${msg.role}`}>
            {msg.role === 'bot' ? '🎓' : '👤'}
          </div>
          <div className="message-content">
            <div className={`message-bubble ${msg.role === 'user' ? 'user' : getBubbleClass(msg.status)}`}>
              {msg.role === 'user' ? (
                <span>{msg.text}</span>
              ) : (
                <ReactMarkdown>{msg.text}</ReactMarkdown>
              )}
            </div>
            {msg.role === 'bot' && msg.citations?.length > 0 && (
              <CitationsBlock citations={msg.citations} />
            )}
            {msg.role === 'bot' && msg.missingInfo && msg.status === 'PARTIAL' && (
              <div style={{ fontSize: 12, color: '#F57C00', padding: '4px 2px', fontStyle: 'italic' }}>
                ⚠️ {msg.missingInfo}
              </div>
            )}
            {msg.role === 'bot' && (
              <div className="message-actions">
                {msg.createdAt && <span className="msg-time">{formatTime(msg.createdAt)}</span>}
                <button className="action-btn up" onClick={() => rateBotMessage(msg.id, 'up')} title="Helpful">👍</button>
                <button className="action-btn down" onClick={() => rateBotMessage(msg.id, 'down')} title="Not helpful">👎</button>
              </div>
            )}
          </div>
        </div>
      ))}
      {isLoading && <TypingIndicator />}
    </>
  );
}
