// src/pages/AlertsPage.tsx
/*import React from "react";
import AlertsTable from "../components/AlertsTable";

const AlertsPage: React.FC = () => {
  return (
    <div className="page">
      <h2>Alerts</h2>
      <p className="page-subtitle">
        All alerts generated from CloudTrail and other telemetry after fusion of UEBA, TI, sequence, and graph scores.
      </p>
      <AlertsTable />
    </div>
  );
};

export default AlertsPage; */

// src/pages/AlertsPage.tsx
import React from "react";
import AlertsTable from "../components/AlertsTable";

const AlertsPage: React.FC = () => {
  return (
    <div className="page">
      <h2>Alerts</h2>
      <p className="page-subtitle">
        All alerts generated from CloudTrail and other telemetry after fusion of UEBA, TI, sequence, and graph scores.
      </p>
      <AlertsTable />
      
      {/* Alert Type Explanation Box */}
      <div className="alert-types-box">
        <h3>Alert Type Explanations</h3>
        <div className="alert-types-grid">
          <div className="alert-type-card rule">
            <div className="alert-type-header">
              <span className="alert-type-icon">📋</span>
              <span className="alert-type-title"><strong>Rule</strong></span>
            </div>
            <p className="alert-type-description">
              Means a rule-based detector flagged the event. Example: CloudTrail IAM changes (CreateUser/AssumeRole/PutBucketPolicy) triggered a rule that scores high risk.
            </p>
          </div>
          
          <div className="alert-type-card graph">
            <div className="alert-type-header">
              <span className="alert-type-icon">🔗</span>
              <span className="alert-type-title"><strong>Graph</strong></span>
            </div>
            <p className="alert-type-description">
              Means the graph/correlation component found related suspicious activity (e.g., many suspicious events connected to the same entity or neighbor nodes) and contributed the main signal.
            </p>
          </div>
          
          <div className="alert-type-card fused">
            <div className="alert-type-header">
              <span className="alert-type-icon">⚡</span>
              <span className="alert-type-title"><strong>Fused</strong></span>
            </div>
            <p className="alert-type-description">
              Means the fusion layer combined multiple weak signals (rule, ueba, sequence, TI) and their combination produced the alert — no single subsystem dominated.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AlertsPage;
