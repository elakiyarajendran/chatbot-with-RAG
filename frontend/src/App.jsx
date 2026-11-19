import { useEffect, useRef, useState } from 'react';
import { Toaster } from 'react-hot-toast';
import { ChatProvider, useChatContext } from './context/ChatContext';
import Sidebar from './components/Sidebar';
import MessageList from './components/MessageList';
import ChatInput from './components/ChatInput';
import InfoPanel from './components/InfoPanel';
import './styles/App.css';

const QUICK_CARDS = [
  { icon: '💬', text: 'Ask anything about policies, fees, attendance, or exams' },
  { icon: '🎤', text: 'Ask about hostel, library, transport & campus facilities' },
  { icon: '🖼️', text: 'Upload a document to get instant Q&A from it' },
  { icon: '📊', text: 'Take a quiz on the College Policy Handbook' },
];

function WelcomeScreen() {
  const { ask } = useChatContext();
  const SAMPLE_PROMPTS = [
    "What is the minimum attendance required?",
    "Explain the grading scale and CGPA classification.",
    "Tell me about the hostel timings and visitor policy.",
    "What are examination malpractice penalties?",
  ];

  return (
    <div className="welcome-screen">
      <div className="welcome-hero">
        <div className="welcome-star">✦</div>
        <h2>Hello! 👋 I'm <span>MC Buddy</span></h2>
        <p>Your Smart Assistant for Mesderian Christ College.<br />
          Ask me anything about academics, events, campus life, or college policies.</p>
      </div>
      <div className="quick-access-grid">
        {QUICK_CARDS.map((card, i) => (
          <div key={i} className="quick-card" onClick={() => ask(SAMPLE_PROMPTS[i])}>
            <span className="quick-card-icon">{card.icon}</span>
            <span className="quick-card-text">{card.text}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function ChatApp() {
  const { messages, isLoading, isInitializing, activeDoc } = useChatContext();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  if (isInitializing) {
    return (
      <div className="global-loader">
        <div className="spinner" />
        <p>Connecting to MC Buddy…</p>
      </div>
    );
  }

  return (
    <div className="app-shell">
      {/* Sidebar Backdrop (mobile) */}
      <div
        className={`sidebar-backdrop ${sidebarOpen ? 'show' : ''}`}
        onClick={() => setSidebarOpen(false)}
      />

      {/* Sidebar */}
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main Content */}
      <div className="main-content">
        {/* Top Bar */}
        <div className="topbar">
          <div className="topbar-left">
            <button className="hamburger-btn" onClick={() => setSidebarOpen(true)}>☰</button>
            <div>
              <div className="topbar-title">✦ MC Buddy</div>
              <div className="topbar-subtitle">
                {activeDoc ? `📄 ${activeDoc.name}` : 'Your College Assistant'}
              </div>
            </div>
          </div>
          <div className="topbar-right">
            <div className="status-pill">
              <div className="status-dot" />
              Online
            </div>
            <button className="icon-btn" title="Your College. Your Assistant.">🌙</button>
          </div>
        </div>

        {/* Chat Layout */}
        <div className="chat-layout">
          <div className="messages-panel">
            <div className="messages-scroll">
              {messages.length === 0 && !isLoading ? (
                <WelcomeScreen />
              ) : (
                <MessageList messages={messages} isLoading={isLoading} />
              )}
              <div ref={messagesEndRef} />
            </div>
            <ChatInput />
          </div>

          {/* Right Info Panel */}
          <InfoPanel />
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <ChatProvider>
      <Toaster
        position="top-right"
        toastOptions={{
          style: { fontSize: '13px', borderRadius: '10px', maxWidth: 360 },
          success: { iconTheme: { primary: '#6B0F1A', secondary: '#fff' } },
        }}
      />
      <ChatApp />
    </ChatProvider>
  );
}
