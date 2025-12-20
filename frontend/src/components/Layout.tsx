// src/components/Layout.tsx
import React from 'react';
import { NavLink } from 'react-router-dom';
import './Layout.css';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const navItems = [
    { path: '/', label: 'Home', icon: '🏠' },
    { path: '/dashboard', label: 'Dashboard', icon: '📊' },
    { path: '/alerts', label: 'Alerts', icon: '🚨' },
    { path: '/logs', label: 'Logs', icon: '📋' },
  ];

  return (
    <div className="layout">
      {/* Top Navigation Bar */}
      <nav className="navbar">
        <div className="navbar-brand">
          <div className="brand-logo"></div>
          <div className="brand-text">
            <h1>CloudAegis</h1>
            <p className="brand-subtitle">Protection And Authority On Cloud Infrastructure</p>
          </div>
        </div>
        
        <div className="navbar-links">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => 
                `nav-link ${isActive ? 'active' : ''}`
              }
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </NavLink>
          ))}
        </div>

        <div className="navbar-status">
        </div>
      </nav>

      {/* Main Content */}
      <main className="main-content">
        {children}
      </main>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-content">
          <div className="footer-section">
            <h4>AI-Infused Threat Detection and Incident Response </h4>
            <p>Final Year Capstone Project</p>
          </div>
          <div className="footer-section">
            <p>Real-time Threat Detection • ML-Powered Analytics • Automated Response</p>
          </div>
          <div className="footer-section">
            <div className="backend-status">
              <span className="status-label">Backend:</span>
              <code>http://localhost:8000</code>
              <span className="status-dot active"></span>
            </div>
            <div className="backend-status">
              <span className="status-label">Graph API:</span>
              <code>http://localhost:8002</code>
              <span className="status-dot active"></span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Layout;