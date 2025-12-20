-- create_db.sql
CREATE DATABASE IF NOT EXISTS threatsys CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE threatsys;

CREATE TABLE IF NOT EXISTS events (
  id VARCHAR(128) PRIMARY KEY,
  ingest_ts DATETIME DEFAULT CURRENT_TIMESTAMP,
  event_id VARCHAR(128),
  source VARCHAR(128),
  entity_type VARCHAR(64),
  entity_id VARCHAR(256),
  event_type VARCHAR(128),
  raw_json LONGTEXT,
  normalized_json LONGTEXT,
  enriched_json LONGTEXT,
  template_id VARCHAR(128),
  ti_score DOUBLE,
  detection_score DOUBLE,
  label ENUM('normal','problem') DEFAULT 'normal',
  detected BOOLEAN DEFAULT FALSE,
  model_version VARCHAR(64),
  alert_ts DATETIME NULL,
  feedback VARCHAR(512),
  updated_ts DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_entity (entity_id),
  INDEX idx_event_type (event_type),
  INDEX idx_label (label)
);

-- Optional table to store audit of feedback actions
CREATE TABLE IF NOT EXISTS event_feedback (
  feedback_id INT AUTO_INCREMENT PRIMARY KEY,
  event_id VARCHAR(128),
  analyst VARCHAR(128),
  feedback_label ENUM('normal','problem') NOT NULL,
  comment TEXT,
  feedback_ts DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Alerts (what /alerts returns to the frontend)
CREATE TABLE IF NOT EXISTS alerts (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  event_id VARCHAR(128),
  entity_id VARCHAR(256),
  entity_type VARCHAR(64),
  event_type VARCHAR(128),
  source VARCHAR(128),
  detection_score DOUBLE,
  ti_score DOUBLE,
  correlation_score DOUBLE,
  label ENUM('normal','problem') DEFAULT 'problem',
  alert_ts DATETIME DEFAULT CURRENT_TIMESTAMP,
  `explain` LONGTEXT,
  explain_shap LONGTEXT,
  raw LONGTEXT,
  normalized LONGTEXT,
  INDEX idx_event_id (event_id),
  INDEX idx_entity_id (entity_id),
  INDEX idx_label_alerts (label)
);
