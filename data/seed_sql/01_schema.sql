-- Project Atlas: MySQL Schema
CREATE DATABASE IF NOT EXISTS atlas_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE atlas_db;

-- 1. Reports metadata table
DROP TABLE IF EXISTS reports;
CREATE TABLE reports (
    id VARCHAR(20) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    publisher VARCHAR(100) NOT NULL,
    published DATE NOT NULL,
    sector VARCHAR(100) NOT NULL,
    access ENUM('paid', 'public excerpt') NOT NULL
) ENGINE=InnoDB;

-- 2. Market metrics table
DROP TABLE IF EXISTS market_metrics;
CREATE TABLE market_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    report_id VARCHAR(20) NOT NULL,
    metric VARCHAR(100) NOT NULL,
    region VARCHAR(50) NOT NULL,
    year_period VARCHAR(50) NOT NULL,
    value VARCHAR(50) NOT NULL,
    scope_note TEXT,
    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 3. Clients table
DROP TABLE IF EXISTS clients;
CREATE TABLE clients (
    id VARCHAR(64) PRIMARY KEY,
    company VARCHAR(255) NOT NULL,
    contact_email VARCHAR(255) NOT NULL,
    purchased_reports TEXT NOT NULL
) ENGINE=InnoDB;

-- 4. Analyst Escalations table
DROP TABLE IF EXISTS escalations;
CREATE TABLE escalations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id VARCHAR(64) NOT NULL,
    query TEXT NOT NULL,
    reason VARCHAR(255) NOT NULL,
    confidence DECIMAL(4,3) DEFAULT 0.000,
    status ENUM('open', 'in_review', 'resolved') DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 5. Chat conversations and feedback table
DROP TABLE IF EXISTS chat_logs;
CREATE TABLE chat_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id VARCHAR(64) NOT NULL,
    query TEXT NOT NULL,
    answer TEXT NOT NULL,
    confidence DECIMAL(4,3) DEFAULT 0.000,
    escalated TINYINT(1) DEFAULT 0,
    latency_ms INT DEFAULT 0,
    tokens_used INT DEFAULT 0,
    estimated_cost_usd DECIMAL(12,8) NULL,
    feedback ENUM('up', 'down', 'none') DEFAULT 'none',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 6. Security audit logs for prompt injection
DROP TABLE IF EXISTS security_audit;
CREATE TABLE security_audit (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id VARCHAR(64) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    payload TEXT NOT NULL,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;
