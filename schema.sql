-- Hercules Database Schema
CREATE DATABASE IF NOT EXISTS GestureSystem;
USE GestureSystem;

CREATE TABLE IF NOT EXISTS gesture_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    gesture_name VARCHAR(50) NOT NULL,
    confidence_score FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);