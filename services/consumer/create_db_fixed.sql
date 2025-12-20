-- create_db_fixed.sql
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
  correlation_score DOUBLE,
  identifier_type VARCHAR(64),
  severity ENUM('low','medium','high') DEFAULT 'low',
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

CREATE TABLE IF NOT EXISTS event_feedback (
  feedback_id INT AUTO_INCREMENT PRIMARY KEY,
  event_id VARCHAR(128),
  analyst VARCHAR(128),
  feedback_label ENUM('normal','problem') NOT NULL,
  comment TEXT,
  feedback_ts DATETIME DEFAULT CURRENT_TIMESTAMP
);
