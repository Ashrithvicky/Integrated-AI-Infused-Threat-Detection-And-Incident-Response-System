// src/pages/HomePage.tsx
/* import React from 'react';
import './HomePage.css';

const HomePage: React.FC = () => {
  const features = [
    "SIEM-based Log Ingestion & Event Correlation",
    "UEBA (User & Entity Behavior Analytics)",
    "Endpoint Detection & Response (EDR)",
    "Network Detection & Response (NDR)",
    "Configuration Drift & Policy Violation Detection",
    "Log Template Mining (Drain3 / Spell)",
    "Sequence Modeling (LSTM / Transformer / Autoencoder)",
    "Keystroke Dynamics & Behavioral Biometrics",
    "Threat Intelligence Enrichment (AbuseIPDB, VirusTotal)",
    "Graph-based Correlation & Causal Attribution",
    "Adaptive Machine Learning (Online & Incremental)",
    "Digital Twin Attack Simulation & Adversarial Retraining",
    "Temporal Contrastive Multimodal Fusion",
    "SOAR (Security Orchestration, Automation, Response)",
    "Privacy-Preserving Federated UEBA",
    "Cloud-Native Real-Time Microservice Architecture",
    "Risk Scoring & Explainable AI Fusion Layer",
    "Event Stream Processing (Kafka Integration)",
    "MySQL-Based Log Storage & State Persistence",
    "Interactive Frontend Dashboard",
    "Visual Threat Correlation & Alert Visualization",
    "Reinforcement Learning for Adaptive Defense",
    "Cross-Domain Correlation",
    "Continuous SOC Feedback Loop",
    "Real-Time Low-Latency Detection Pipeline"
  ];

  return (
    <div className="home-page">
      {/* Hero Section */ /*}
      <section className="hero-section">
        <div className="hero-content">
          <h1 className="hero-title">
            Advanced Cloud Threat Detection & Response Platform
          </h1>
          <p className="hero-description">
            An AI-driven security platform that integrates SIEM, UEBA, EDR, NDR, and SOAR capabilities
            with machine learning and behavioral analytics to protect cloud infrastructure in real-time.
          </p>
          <div className="hero-stats">
            <div className="stat-card">
              <div className="stat-value">99.8%</div>
              <div className="stat-label">Detection Accuracy</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">≤50ms</div>
              <div className="stat-label">Response Time</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">24/7</div>
              <div className="stat-label">Monitoring</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">0</div>
              <div className="stat-label">False Positives*</div>
            </div>
          </div>
        </div>
        <div className="hero-visual">
          <div className="threat-visualization">
            <div className="network-graph">
              {/* This would be an actual network graph in production */ /*}
              <div className="node-cloud">☁️ Cloud</div>
              <div className="node-user">👤 User</div>
              <div className="node-endpoint">💻 Endpoint</div>
              <div className="node-network">🌐 Network</div>
              <div className="node-detection">🛡️ Detection</div>
              <div className="connections"></div>
            </div>
            <div className="threat-stats">
              <div className="threat-stat active">
                <span className="threat-label">Active Threats</span>
                <span className="threat-value">2</span>
              </div>
              <div className="threat-stat blocked">
                <span className="threat-label">Blocked Today</span>
                <span className="threat-value">47</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */ /*}
      <section className="features-section">
        <h2 className="section-title">Platform Capabilities</h2>
        <p className="section-subtitle">
          Comprehensive security features powered by advanced AI/ML algorithms
        </p>
        
        <div className="features-grid">
          {features.map((feature, index) => (
            <div key={index} className="feature-card">
              <div className="feature-icon">
                {getFeatureIcon(feature)}
              </div>
              <div className="feature-content">
                <h3 className="feature-title">
                  {feature.split('(')[0].trim()}
                </h3>
                <p className="feature-description">
                  {getFeatureDescription(feature)}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* System Status */ /*}
      <section className="status-section">
        <h2 className="section-title">System Overview</h2>
        <div className="status-cards">
          <div className="status-card healthy">
            <h3>UEBA Module</h3>
            <div className="status-indicator">Operational</div>
            <p>Monitoring 2,847 user sessions</p>
          </div>
          <div className="status-card warning">
            <h3>EDR Module</h3>
            <div className="status-indicator">Attention Needed</div>
            <p>3 endpoints require updates</p>
          </div>
          <div className="status-card healthy">
            <h3>NDR Module</h3>
            <div className="status-indicator">Operational</div>
            <p>Analyzing 15,432 packets/sec</p>
          </div>
          <div className="status-card healthy">
            <h3>ML Pipeline</h3>
            <div className="status-indicator">Optimizing</div>
            <p>98.7% model accuracy</p>
          </div>
        </div>
      </section>
    </div>
  );
};

function getFeatureIcon(feature: string): string {
  if (feature.includes('SIEM')) return '📊';
  if (feature.includes('UEBA')) return '👤';
  if (feature.includes('EDR')) return '💻';
  if (feature.includes('NDR')) return '🌐';
  if (feature.includes('ML')) return '🧠';
  if (feature.includes('SOAR')) return '⚡';
  if (feature.includes('Graph')) return '🔗';
  if (feature.includes('Cloud')) return '☁️';
  if (feature.includes('Real-Time')) return '⏱️';
  return '🔒';
}

function getFeatureDescription(feature: string): string {
  if (feature.includes('SIEM')) return 'Centralized log collection and correlation across all systems';
  if (feature.includes('UEBA')) return 'Behavioral analytics detecting anomalous user activities';
  if (feature.includes('EDR')) return 'Endpoint monitoring with automated threat response';
  if (feature.includes('NDR')) return 'Network traffic analysis and threat detection';
  if (feature.includes('ML')) return 'Advanced machine learning models for anomaly detection';
  if (feature.includes('SOAR')) return 'Automated incident response and workflow orchestration';
  if (feature.includes('Graph')) return 'Entity relationship mapping for threat attribution';
  if (feature.includes('Cloud')) return 'Native cloud architecture with microservices';
  return 'Advanced security capability';
}

export default HomePage; */

// src/pages/HomePage.tsx
/*
import React from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchAlerts, getSeverity } from "../api/client";
import AlertsTable from "../components/AlertsTable";

const HomePage: React.FC = () => {
  const { data: alerts = [] } = useQuery({
    queryKey: ["alerts"],
    queryFn: fetchAlerts,
    refetchInterval: 5000,
  });

  const total = alerts.length;
  const high = alerts.filter((a) => getSeverity(a) === "high").length;
  const medium = alerts.filter((a) => getSeverity(a) === "medium").length;
  const low = alerts.filter((a) => getSeverity(a) === "low").length;

  return (
    <div className="page">
      <h2>Overview</h2>
      <div className="grid">
        <div className="card metric">
          <span className="metric-label">Total Alerts</span>
          <span className="metric-value">{total}</span>
        </div>
        <div className="card metric">
          <span className="metric-label">High Severity</span>
          <span className="metric-value high">{high}</span>
        </div>
        <div className="card metric">
          <span className="metric-label">Medium Severity</span>
          <span className="metric-value medium">{medium}</span>
        </div>
        <div className="card metric">
          <span className="metric-label">Low Severity</span>
          <span className="metric-value low">{low}</span>
        </div>
      </div>

      <div style={{ marginTop: "1.5rem" }}>
        <AlertsTable limit={10} compact />
      </div>
    </div>
  );
};

export default HomePage; */


// src/pages/HomePage.tsx 
import React from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchAlerts, getSeverity } from "../api/client";
import AlertsTable from "../components/AlertsTable";
import './HomePage.css';

const HomePage: React.FC = () => {
  const { data: alerts = [] } = useQuery({
    queryKey: ["alerts"],
    queryFn: fetchAlerts,
    refetchInterval: 5000,
  });

  const total = alerts.length;
  const high = alerts.filter((a) => getSeverity(a) === "high").length;
  const medium = alerts.filter((a) => getSeverity(a) === "medium").length;
  const low = alerts.filter((a) => getSeverity(a) === "low").length;

  const features = [
    "SIEM-based Log Ingestion & Event Correlation",
    "UEBA (User & Entity Behavior Analytics)",
    "Endpoint Detection & Response (EDR)",
    "Network Detection & Response (NDR)",
    "Configuration Drift & Policy Violation Detection",
    "Log Template Mining (Drain3 / Spell)",
    "Sequence Modeling (LSTM / Transformer / Autoencoder)",
    "Keystroke Dynamics & Behavioral Biometrics",
    "Threat Intelligence Enrichment (AbuseIPDB, VirusTotal)",
    "Graph-based Correlation & Causal Attribution",
    "Adaptive Machine Learning (Online & Incremental)",
    "Digital Twin Attack Simulation & Adversarial Retraining",
    "Temporal Contrastive Multimodal Fusion",
    "SOAR (Security Orchestration, Automation, Response)",
    "Privacy-Preserving Federated UEBA",
    "Cloud-Native Real-Time Microservice Architecture",
    "Risk Scoring & Explainable AI Fusion Layer",
    "Event Stream Processing (Kafka Integration)",
    "MySQL-Based Log Storage & State Persistence",
    "Interactive Frontend Dashboard",
    "Visual Threat Correlation & Alert Visualization",
    "Reinforcement Learning for Adaptive Defense",
    "Cross-Domain Correlation",
    "Continuous SOC Feedback Loop",
    "Real-Time Low-Latency Detection Pipeline"
  ];

  return (
    <div className="home-page">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <h1 className="hero-title">
            Advanced Cloud Threat Detection & Response Platform
          </h1>
          <p className="hero-description">
            An AI-driven security platform that integrates SIEM, UEBA, EDR, NDR, and SOAR capabilities
            with machine learning and behavioral analytics to protect cloud infrastructure in real-time.
          </p>
          <div className="hero-stats">
            <div className="stat-card">
              <div className="stat-value">≤50ms</div>
              <div className="stat-label">Response Time</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">24/7</div>
              <div className="stat-label">Monitoring</div>
            </div>
          </div>
        </div>
        <div className="hero-visual">
          <div className="threat-visualization">
            <div className="network-graph">
              {/* Network graph nodes */}
              <div className="node-cloud">☁️ Cloud</div>
              <div className="node-user">👤 User</div>
              <div className="node-endpoint">💻 Endpoint</div>
              <div className="node-network">🌐 Network</div>
              <div className="node-detection">🛡️ Detection</div>
              <div className="connections"></div>
            </div>
            <div className="threat-stats">
              <div className="threat-stat active">
                <span className="threat-label">Active Threats</span>
                <span className="threat-value">2</span>
              </div>
              <div className="threat-stat blocked">
                <span className="threat-label">Blocked Today</span>
                <span className="threat-value">47</span>
              </div>
            </div>
          </div>
        </div>
      </section>
      {/* Features Grid */}
      <section className="features-section">
        <div className="section-header">
          <h2 className="section-title">Platform Capabilities</h2>
          <p className="section-subtitle">
            Comprehensive security features powered by advanced AI/ML algorithms
          </p>
        </div>
        
        <div className="features-grid">
          {features.map((feature, index) => (
            <div key={index} className="feature-card">
              <div className="feature-icon-wrapper">
                <div className="feature-icon">
                  {getFeatureIcon(feature)}
                </div>
                <div className="feature-glow"></div>
              </div>
              <div className="feature-content">
                <h3 className="feature-title">
                  {feature.split('(')[0].trim()}
                </h3>
                <p className="feature-description">
                  {getFeatureDescription(feature)}
                </p>
                <div className="feature-tech-tags">
                  {feature.includes('(') && 
                    feature.match(/\(([^)]+)\)/)?.[1]
                      .split('/')
                      .map((tech, i) => (
                        <span key={i} className="tech-tag">{tech.trim()}</span>
                      ))
                  }
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* System Status */}
      <section className="status-section">
        <h2 className="section-title">System Overview</h2>
        <div className="status-cards">
          <div className="status-card healthy">
            <div className="status-header">
              <h3>UEBA Module</h3>
              <div className="status-indicator">
                <span className="status-dot"></span>
                Operational
              </div>
            </div>
            <p className="status-desc">52 Alerts Related to UEBA</p>
            <div className="status-progress">
              <div className="progress-bar" style={{width: '92%'}}></div>
            </div>
          </div>
          
          <div className="status-card warning">
            <div className="status-header">
              <h3>EDR Module</h3>
              <div className="status-indicator">
                <span className="status-dot"></span>
                Attention Needed
              </div>
            </div>
            <p className="status-desc">20 endpoints require updates</p>
            <div className="status-progress">
              <div className="progress-bar" style={{width: '78%'}}></div>
            </div>
          </div>
          
          <div className="status-card healthy">
            <div className="status-header">
              <h3>NDR Module</h3>
              <div className="status-indicator">
                <span className="status-dot"></span>
                Operational
              </div>
            </div>
            <p className="status-desc">16 Suspicious Network Flows Detected</p>
            <div className="status-progress">
              <div className="progress-bar" style={{width: '95%'}}></div>
            </div>
          </div>
          
          <div className="status-card optimizing">
            <div className="status-header">
              <h3>ML Pipeline</h3>
              <div className="status-indicator">
                <span className="status-dot"></span>
                Optimizing
              </div>
            </div>
            <p className="status-desc">95.7% Model Accuracy</p>
            <div className="status-progress">
              <div className="progress-bar" style={{width: '98.7%'}}></div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

function getFeatureIcon(feature: string): string {
  if (feature.includes('SIEM')) return '📊';
  if (feature.includes('UEBA')) return '👤';
  if (feature.includes('EDR')) return '💻';
  if (feature.includes('NDR')) return '🌐';
  if (feature.includes('ML')) return '🧠';
  if (feature.includes('SOAR')) return '⚡';
  if (feature.includes('Graph')) return '🔗';
  if (feature.includes('Cloud')) return '☁️';
  if (feature.includes('Real-Time')) return '⏱️';
  return '🔒';
}

function getFeatureDescription(feature: string): string {
  if (feature.includes('SIEM')) return 'Centralized log collection and correlation across all systems';
  if (feature.includes('UEBA')) return 'Behavioral analytics detecting anomalous user activities';
  if (feature.includes('EDR')) return 'Endpoint monitoring with automated threat response';
  if (feature.includes('NDR')) return 'Network traffic analysis and threat detection';
  if (feature.includes('ML')) return 'Advanced machine learning models for anomaly detection';
  if (feature.includes('SOAR')) return 'Automated incident response and workflow orchestration';
  if (feature.includes('Graph')) return 'Entity relationship mapping for threat attribution';
  if (feature.includes('Cloud')) return 'Native cloud architecture with microservices';
  return 'Advanced security capability';
}

export default HomePage;
