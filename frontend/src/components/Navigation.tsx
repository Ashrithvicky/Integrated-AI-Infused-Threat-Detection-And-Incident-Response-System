// src/components/Navigation.tsx
import React from 'react';
import { NavLink } from 'react-router-dom';
import './Navigation.css';

const Navigation: React.FC = () => {
  return (
    <nav className="navigation">
      <div className="nav-container">
        {/* Logo */}
        <div className="nav-brand">
          <div className="logo">
            <span className="logo-icon">🛡️</span>
            <span className="logo-text">ThreadSys</span>
          </div>
          <div className="brand-tagline">Cloud Threat Detection</div>
        </div>

        {/* Links */}
        <div className="nav-links">
          <NavLink to="/" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            Home
          </NavLink>
          <NavLink to="/alerts" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            Alerts
          </NavLink>
          <NavLink to="/dashboard" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            Dashboard
          </NavLink>
          <NavLink to="/logs" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            Logs
          </NavLink>
          <NavLink to="/SysHealth" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            System Health
          </NavLink>
        </div>

        {/* Status */}
        <div className="nav-status">
          <span className="status-indicator">
            <span className="status-dot"></span>
            System Online
          </span>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;