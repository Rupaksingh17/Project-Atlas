-- Project Atlas: Seed Data
USE atlas_db;

-- Populate reports
INSERT INTO reports (id, title, publisher, published, sector, access) VALUES
('R-101', 'Global Smart Water Meter Market 2025', 'CMR', '2025-03-10', 'Utilities', 'paid'),
('R-102', 'Smart Water Metering: Industry Outlook 2024', 'Aquila Insights (third party)', '2024-06-18', 'Utilities', 'public excerpt'),
('R-103', 'Residential Water Purifier Market 2025', 'CMR', '2025-01-22', 'Consumer Durables', 'paid'),
('R-104', 'Industrial IoT Sensors Market 2025', 'CMR', '2025-02-15', 'Manufacturing', 'paid'),
('R-105', 'Commercial Water Treatment Systems 2024', 'Aquila Insights (third party)', '2024-11-05', 'Utilities', 'paid'),
('R-106', 'Smart Gas Metering Infrastructure 2025', 'CMR', '2025-04-12', 'Energy', 'paid')
ON DUPLICATE KEY UPDATE title=VALUES(title);

-- Populate market metrics
INSERT INTO market_metrics (report_id, metric, region, year_period, value, scope_note) VALUES
('R-101', 'Market size', 'Global', '2024', 'USD 4.21 B', 'Includes hardware, software and services'),
('R-101', 'CAGR', 'Global', '2025-2030', '11.2 %', 'Forecast period stated as 2025-2030'),
('R-101', 'Regional share', 'APAC', '2024', '38 %', 'Share of global market size'),
('R-102', 'Market size', 'Global', '2024', 'USD 3.87 B', 'AMR / AMI hardware only'),
('R-102', 'CAGR', 'Global', '2024-2029', '9.8 %', 'Different forecast window from R-101'),
('R-102', 'Regional share', 'APAC', '2024', '41 %', 'Share of hardware market'),
('R-103', 'Market size', 'Global', '2024', 'USD 9.15 B', 'Residential point-of-use systems'),
('R-103', 'CAGR', 'Global', '2025-2030', '8.4 %', 'Forecast period 2025-2030'),
('R-104', 'Market size', 'Global', '2024', 'USD 14.60 B', 'Factory automation and predictive maintenance'),
('R-105', 'Market size', 'Global', '2024', 'USD 5.30 B', 'Industrial membrane and filtration systems'),
('R-106', 'Market size', 'Global', '2024', 'USD 2.95 B', 'Residential and commercial gas telemetry');

-- Populate clients
INSERT INTO clients (id, company, contact_email, purchased_reports) VALUES
('C-01', 'Northwind Utilities', 'ops@example.com', 'R-101, R-103'),
('C-02', 'Blue Delta Infra', 'procurement@example.com', 'R-103')
ON DUPLICATE KEY UPDATE company=VALUES(company);

-- Database users and least-privilege grants are created by 03_create_users.sh,
-- which reads deployment secrets from the MySQL container environment.
