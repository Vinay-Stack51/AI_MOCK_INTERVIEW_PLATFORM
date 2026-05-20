"""
MySQL persistence layer for authentication and interview records (STREAMLIT SAFE VERSION).
"""

import hashlib
import json
import streamlit as st
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

try:
    import mysql.connector
except ImportError:
    mysql = None

try:
    import bcrypt
except ImportError:
    bcrypt = None

from dotenv import load_dotenv
load_dotenv()

BCRYPT_SALT_MARKER = "bcrypt"


class MySQLStore:
    def __init__(self):
        # SAFE MODE SWITCH
        self.enabled = str(st.secrets.get("MYSQL_ENABLED", "false")).lower() == "true"

        # If disabled → prevent any DB usage
        if not self.enabled:
            self.host = None
            self.port = None
            self.user = None
            self.password = None
            self.database = None
            return

        # Only used when enabled
        self.host = st.secrets.get("MYSQL_HOST", "localhost")
        self.port = int(st.secrets.get("MYSQL_PORT", "3306"))
        self.user = st.secrets.get("MYSQL_USER", "root")
        self.password = st.secrets.get("MYSQL_PASSWORD", "")
        self.database = st.secrets.get("MYSQL_DATABASE", "ai_interview_coach")

    # ----------------------------
    # CONNECTION
    # ----------------------------
    def _connect(self, with_database: bool = True):
        if not self.enabled:
            raise RuntimeError("MySQL is disabled (demo mode)")

        if mysql is None:
            raise RuntimeError("mysql-connector-python is not installed")

        config = {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
        }

        if with_database:
            config["database"] = self.database

        return mysql.connector.connect(**config)

    # ----------------------------
    # INIT
    # ----------------------------
    def initialize(self) -> Tuple[bool, str]:
        if not self.enabled:
            return False, "MySQL disabled (running in demo mode)"

        if mysql is None:
            return False, "mysql-connector-python missing"

        if bcrypt is None:
            return False, "bcrypt missing"

        try:
            conn = self._connect(with_database=False)
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{self.database}`")
            cursor.close()
            conn.close()

            conn = self._connect(with_database=True)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    full_name VARCHAR(120),
                    email VARCHAR(160) UNIQUE,
                    password_hash VARCHAR(255),
                    password_salt VARCHAR(64),
                    is_admin TINYINT(1) DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS interview_sessions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    started_at DATETIME,
                    ended_at DATETIME,
                    total_questions INT DEFAULT 0,
                    overall_score FLOAT,
                    performance_level VARCHAR(50),
                    report_json LONGTEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS interview_answers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    session_id INT,
                    question_text TEXT,
                    answer_text LONGTEXT,
                    topic VARCHAR(80),
                    difficulty VARCHAR(40),
                    score FLOAT,
                    feedback_json LONGTEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()
            cursor.close()
            conn.close()

            return True, "MySQL ready"
        except Exception as e:
            return False, f"MySQL init failed: {e}"

    # ----------------------------
    # AUTH (SAFE FALLBACK)
    # ----------------------------
    def create_user(self, full_name, email, password):
        if not self.enabled:
            return False, "DB disabled (demo mode)"

        if bcrypt is None:
            return False, "bcrypt missing"

        try:
            conn = self._connect()
            cursor = conn.cursor()

            ph = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

            cursor.execute("""
                INSERT INTO users (full_name, email, password_hash, password_salt)
                VALUES (%s, %s, %s, %s)
            """, (full_name, email.lower(), ph, BCRYPT_SALT_MARKER))

            conn.commit()
            cursor.close()
            conn.close()

            return True, "User created"
        except Exception as e:
            return False, str(e)

    def authenticate_user(self, email, password):
        if not self.enabled:
            return False, None, "DB disabled"

        try:
            conn = self._connect()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT * FROM users WHERE email=%s", (email.lower(),))
            user = cursor.fetchone()

            cursor.close()
            conn.close()

            if not user:
                return False, None, "User not found"

            if bcrypt and bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
                return True, {
                    "id": user["id"],
                    "name": user["full_name"],
                    "email": user["email"]
                }, "Success"

            return False, None, "Invalid password"

        except Exception as e:
            return False, None, str(e)

    # ----------------------------
    # SAFE STUBS (avoid crashes)
    # ----------------------------
    def save_answer_record(self, session_id, record):
        return True

    def complete_interview_session(self, session_id, report):
        return True

    def get_recent_interviews(self, user_id, limit=5):
        return []
