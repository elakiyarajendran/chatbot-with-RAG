import { useState } from 'react';
import { useChatContext } from '../context/ChatContext';

const NAV_ITEMS = [
  { id: 'chat', icon: '💬', label: 'Chat' },
  { id: 'explore', icon: '🏛️', label: 'Explore College' },
  { id: 'academics', icon: '📚', label: 'Academic Support' },
  { id: 'events', icon: '📅', label: 'Events & Notices' },
  { id: 'facilities', icon: '⭐', label: 'Facilities' },
  { id: 'help', icon: '🎧', label: 'Help & Support' },
];

const EXPLORE_QUESTIONS = {
  explore: "Tell me about Meridian College's vision, mission, and admission process.",
  academics: "Explain the CBCS credit system, grading scale, and academic policies.",
  events: "What are the co-curricular, clubs, and events policies?",
  facilities: "Describe the hostel, library, transport, and campus facilities.",
  help: "Who should I contact for student grievances and what is the redressal process?",
};

export default function Sidebar({ isOpen, onClose }) {
  const [activeNav, setActiveNav] = useState('chat');
  const { ask } = useChatContext();

  const handleNavClick = (item) => {
    setActiveNav(item.id);
    if (item.id !== 'chat' && EXPLORE_QUESTIONS[item.id]) {
      ask(EXPLORE_QUESTIONS[item.id]);
    }
    if (window.innerWidth <= 768) onClose?.();
  };

  return (
    <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">🏫</div>
        <h1>Mesderian<br />Christ College</h1>
        <p>Learn • Excel • Serve</p>
      </div>

      {/* Nav */}
      <nav className="sidebar-nav">
        <div className="nav-label">Main</div>
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            className={`nav-item ${activeNav === item.id ? 'active' : ''}`}
            onClick={() => handleNavClick(item)}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
          </button>
        ))}

        <div className="nav-label" style={{ marginTop: 16 }}>Policy Sections</div>
        {[
          ['Admission Policy', '🎓'],
          ['Academic Integrity', '✅'],
          ['Examination Policy', '📝'],
          ['Anti-Ragging', '🛡️'],
          ['Grievance Redressal', '⚖️'],
        ].map(([label, icon]) => (
          <button
            key={label}
            className="nav-item"
            onClick={() => { ask(`Summarise the ${label} from the handbook.`); if (window.innerWidth <= 768) onClose?.(); }}
          >
            <span className="nav-icon">{icon}</span>
            {label}
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        "Dream Bigger,<br />Achieve More"
      </div>
    </aside>
  );
}
