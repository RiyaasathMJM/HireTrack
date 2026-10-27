// ── components/layout/TopBar.tsx ──────────────────────────────────────────────

import { Search, Bell } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface TopBarProps {
  title: string;
  subtitle?: string;
}

export default function TopBar({ title, subtitle }: TopBarProps) {
  const [query, setQuery] = useState('');
  const navigate = useNavigate();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/candidates?keyword=${encodeURIComponent(query.trim())}`);
    }
  };

  return (
    <header className="topbar">
      <div className="topbar-left">
        <h1 className="topbar-title">{title}</h1>
        {subtitle && <p className="topbar-subtitle">{subtitle}</p>}
      </div>
      <div className="topbar-right">
        <form className="search-form" onSubmit={handleSearch}>
          <Search size={16} className="search-icon" />
          <input
            type="text"
            className="search-input"
            placeholder="Search candidates…"
            value={query}
            onChange={e => setQuery(e.target.value)}
          />
        </form>
        <button className="icon-btn" aria-label="Notifications">
          <Bell size={18} />
          <span className="notif-badge">3</span>
        </button>
        <div className="avatar" aria-label="User avatar">HR</div>
      </div>
    </header>
  );
}
