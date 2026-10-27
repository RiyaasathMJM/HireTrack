// ── components/layout/Sidebar.tsx ─────────────────────────────────────────────

import { NavLink } from 'react-router-dom';
import {
  Users,
  Briefcase,
  BarChart3,
  Upload,
  ChevronRight,
  Zap,
} from 'lucide-react';

interface NavItem {
  to: string;
  icon: React.ReactNode;
  label: string;
  end?: boolean;
}

const navItems: NavItem[] = [
  { to: '/', icon: <BarChart3 size={18} />, label: 'Dashboard', end: true },
  { to: '/candidates', icon: <Users size={18} />, label: 'Candidates' },
  { to: '/jobs', icon: <Briefcase size={18} />, label: 'Job Descriptions' },
  { to: '/upload', icon: <Upload size={18} />, label: 'Upload Resumes' },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-icon">
          <Zap size={20} />
        </div>
        <span className="brand-text">HireTrack</span>
      </div>

      <nav className="sidebar-nav">
        <p className="nav-label">Main</p>
        {navItems.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `nav-item ${isActive ? 'nav-item--active' : ''}`
            }
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-text">{item.label}</span>
            <ChevronRight size={14} className="nav-arrow" />
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-footer-inner">
          <div className="status-dot" />
          <span>Backend connected</span>
        </div>
      </div>
    </aside>
  );
}
