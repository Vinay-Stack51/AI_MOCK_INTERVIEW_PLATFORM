"""
MySQL persistence layer for authentication and interview records.
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
        self.host = st.secrets.get("MYSQL_HOST", "localhost")
        self.port = int(st.secrets.get("MYSQL_PORT", "3306"))
        self.user = st.secrets.get("MYSQL_USER", "root")
        self.password = st.secrets.get("MYSQL_PASSWORD", "")
        self.database = st.secrets.get("MYSQL_DATABASE", "ai_interview_coach")
        self.enabled = st.secrets.get("MYSQL_ENABLED", "true").lower() == "true"

    def _connect(self, with_database: bool = True):
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

    def _migrate_schema(self, cursor) -> None:
        """Best-effort migrations for existing databases."""
        try:
            cursor.execute(
                "ALTER TABLE users MODIFY COLUMN password_hash VARCHAR(255) NOT NULL"
            )
        except Exception:
            pass
        try:
            cursor.execute(
                """
                ALTER TABLE users ADD COLUMN is_admin TINYINT(1) NOT NULL DEFAULT 0
                """
            )
        except Exception:
            pass

    def _bootstrap_admins(self, cursor, conn) -> None:
        raw = os.getenv("ADMIN_EMAILS", "").strip()
        if not raw:
            return
        emails = [e.strip().lower() for e in raw.split(",") if e.strip()]
        for email in emails:
            cursor.execute(
                "UPDATE users SET is_admin = 1 WHERE email = %s",
                (email,),
            )
        conn.commit()

    def initialize(self) -> Tuple[bool, str]:
        if mysql is None:
            return False, "MySQL connector missing. Install with: pip install mysql-connector-python"
        if bcrypt is None:
            return False, "bcrypt missing. Install with: pip install bcrypt"
        if not self.enabled:
            return False, "MySQL disabled via MYSQL_ENABLED=false"
        try:
            conn = self._connect(with_database=False)
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{self.database}`")
            cursor.close()
            conn.close()

            conn = self._connect(with_database=True)
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    full_name VARCHAR(120) NOT NULL,
                    email VARCHAR(160) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    password_salt VARCHAR(64) NOT NULL,
                    is_admin TINYINT(1) NOT NULL DEFAULT 0,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            self._migrate_schema(cursor)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL UNIQUE,
                    target_role VARCHAR(120) NOT NULL,
                    experience_level VARCHAR(80) NOT NULL,
                    skills_json TEXT NOT NULL,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS interview_sessions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    started_at DATETIME NOT NULL,
                    ended_at DATETIME NULL,
                    total_questions INT NOT NULL DEFAULT 0,
                    overall_score DECIMAL(4,2) NULL,
                    performance_level VARCHAR(50) NULL,
                    report_json LONGTEXT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS interview_answers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    session_id INT NOT NULL,
                    question_id INT NOT NULL,
                    question_text TEXT NOT NULL,
                    answer_text LONGTEXT NOT NULL,
                    topic VARCHAR(80) NOT NULL,
                    difficulty VARCHAR(40) NOT NULL,
                    score DECIMAL(4,2) NOT NULL,
                    feedback_json LONGTEXT NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES interview_sessions(id) ON DELETE CASCADE
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS password_reset_tokens (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    token_hash CHAR(64) NOT NULL,
                    expires_at DATETIME NOT NULL,
                    used_at DATETIME NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    INDEX idx_token_hash (token_hash),
                    INDEX idx_expires (expires_at)
                )
                """
            )
            conn.commit()
            self._bootstrap_admins(cursor, conn)
            cursor.close()
            conn.close()
            return True, "MySQL connection ready"
        except Exception as exc:
            return False, f"MySQL initialization failed: {exc}"

    @staticmethod
    def _hash_password_legacy(password: str, salt: str) -> str:
        return hashlib.sha256(f"{salt}{password}".encode("utf-8")).hexdigest()

    def _hash_password_bcrypt(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def _set_password_bcrypt(self, user_id: int, plain_password: str) -> None:
        conn = self._connect()
        cursor = conn.cursor()
        ph = self._hash_password_bcrypt(plain_password)
        cursor.execute(
            """
            UPDATE users SET password_hash=%s, password_salt=%s WHERE id=%s
            """,
            (ph, BCRYPT_SALT_MARKER, user_id),
        )
        conn.commit()
        cursor.close()
        conn.close()

    def create_user(self, full_name: str, email: str, password: str) -> Tuple[bool, str]:
        if bcrypt is None:
            return False, "bcrypt not installed"
        if len(password) < 8:
            return False, "Password must be at least 8 characters."
        ph = self._hash_password_bcrypt(password)
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (full_name, email, password_hash, password_salt)
                VALUES (%s, %s, %s, %s)
                """,
                (full_name.strip(), email.strip().lower(), ph, BCRYPT_SALT_MARKER),
            )
            conn.commit()
            cursor.close()
            conn.close()
            return True, "Account created successfully"
        except mysql.connector.IntegrityError:
            return False, "Email already registered"
        except Exception as exc:
            return False, f"Signup failed: {exc}"

    def _password_matches_row(self, row: Dict, password: str) -> bool:
        salt = row.get("password_salt") or ""
        stored = row["password_hash"]
        if salt == BCRYPT_SALT_MARKER:
            try:
                return bcrypt.checkpw(password.encode("utf-8"), stored.encode("utf-8"))
            except Exception:
                return False
        calc = self._hash_password_legacy(password, salt)
        return calc == stored

    def authenticate_user(self, email: str, password: str) -> Tuple[bool, Optional[Dict], str]:
        if bcrypt is None:
            return False, None, "bcrypt not installed"
        try:
            conn = self._connect()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, full_name, email, password_hash, password_salt, is_admin
                FROM users WHERE email=%s
                """,
                (email.strip().lower(),),
            )
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            if not row:
                return False, None, "No account found for this email"

            if not self._password_matches_row(row, password):
                return False, None, "Invalid password"

            salt = row.get("password_salt") or ""
            if salt != BCRYPT_SALT_MARKER:
                self._set_password_bcrypt(row["id"], password)

            is_admin = bool(row.get("is_admin"))
            return True, {
                "id": row["id"],
                "name": row["full_name"],
                "email": row["email"],
                "is_admin": is_admin,
            }, "Login successful"
        except Exception as exc:
            return False, None, f"Login failed: {exc}"

    def change_password(
        self, user_id: int, current_password: str, new_password: str
    ) -> Tuple[bool, str]:
        if len(new_password) < 8:
            return False, "New password must be at least 8 characters."
        conn = self._connect()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, password_hash, password_salt FROM users WHERE id=%s
            """,
            (user_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if not row or not self._password_matches_row(row, current_password):
            return False, "Current password is incorrect."
        self._set_password_bcrypt(user_id, new_password)
        return True, "Password updated."

    def request_password_reset(self, email: str) -> Tuple[bool, Optional[str], str]:
        """Create a reset token. Returns (ok, plaintext_token, message). Token shown once in UI."""
        email_l = email.strip().lower()
        conn = self._connect()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE email=%s", (email_l,))
        row = cursor.fetchone()
        if not row:
            cursor.close()
            conn.close()
            return (
                True,
                None,
                "If this email is registered, a one-time token will appear after you request a reset.",
            )
        user_id = row["id"]
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        expires = datetime.now() + timedelta(hours=1)
        cursor.execute(
            """
            INSERT INTO password_reset_tokens (user_id, token_hash, expires_at)
            VALUES (%s, %s, %s)
            """,
            (user_id, token_hash, expires.strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True, token, "Use the token below with your email to set a new password (valid 1 hour)."

    def complete_password_reset(
        self, email: str, token: str, new_password: str
    ) -> Tuple[bool, str]:
        if len(new_password) < 8:
            return False, "Password must be at least 8 characters."
        email_l = email.strip().lower()
        token_hash = hashlib.sha256(token.strip().encode("utf-8")).hexdigest()
        conn = self._connect()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE email=%s", (email_l,))
        urow = cursor.fetchone()
        if not urow:
            cursor.close()
            conn.close()
            return False, "Invalid email or token."
        user_id = urow["id"]
        cursor.execute(
            """
            SELECT id FROM password_reset_tokens
            WHERE user_id=%s AND token_hash=%s AND used_at IS NULL AND expires_at > NOW()
            ORDER BY id DESC LIMIT 1
            """,
            (user_id, token_hash),
        )
        trow = cursor.fetchone()
        if not trow:
            cursor.close()
            conn.close()
            return False, "Invalid or expired token."
        tid = trow["id"]
        ph = self._hash_password_bcrypt(new_password)
        cursor.execute(
            """
            UPDATE users SET password_hash=%s, password_salt=%s WHERE id=%s
            """,
            (ph, BCRYPT_SALT_MARKER, user_id),
        )
        cursor.execute(
            "UPDATE password_reset_tokens SET used_at=NOW() WHERE id=%s", (tid,)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True, "Password reset successful. You can log in now."

    def get_profile(self, user_id: int) -> Optional[Dict]:
        try:
            conn = self._connect()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT u.full_name, u.email, p.target_role, p.experience_level, p.skills_json
                FROM users u
                LEFT JOIN user_profiles p ON p.user_id = u.id
                WHERE u.id = %s
                """,
                (user_id,),
            )
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            if not row:
                return None

            skills = []
            if row.get("skills_json"):
                try:
                    skills = json.loads(row["skills_json"])
                except Exception:
                    skills = []

            return {
                "name": row.get("full_name") or "",
                "email": row.get("email") or "",
                "target_role": row.get("target_role") or "Software Engineer",
                "experience_level": row.get("experience_level") or "entry level",
                "skills": skills,
                "profile_complete": bool(row.get("target_role")),
            }
        except Exception:
            return None

    def save_profile(self, user_id: int, profile: Dict) -> Tuple[bool, str]:
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET full_name=%s, email=%s WHERE id=%s",
                (profile.get("name", "").strip(), profile.get("email", "").strip().lower(), user_id),
            )
            cursor.execute(
                """
                INSERT INTO user_profiles (user_id, target_role, experience_level, skills_json)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                  target_role=VALUES(target_role),
                  experience_level=VALUES(experience_level),
                  skills_json=VALUES(skills_json)
                """,
                (
                    user_id,
                    profile.get("target_role", "Software Engineer"),
                    profile.get("experience_level", "entry level"),
                    json.dumps(profile.get("skills", [])),
                ),
            )
            conn.commit()
            cursor.close()
            conn.close()
            return True, "Profile saved"
        except Exception as exc:
            return False, f"Profile save failed: {exc}"

    def create_interview_session(self, user_id: int, started_at: datetime) -> Optional[int]:
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO interview_sessions (user_id, started_at)
                VALUES (%s, %s)
                """,
                (user_id, started_at.strftime("%Y-%m-%d %H:%M:%S")),
            )
            session_id = cursor.lastrowid
            conn.commit()
            cursor.close()
            conn.close()
            return session_id
        except Exception:
            return None

    def save_answer_record(self, session_id: int, record: Dict) -> bool:
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO interview_answers (
                    session_id, question_id, question_text, answer_text,
                    topic, difficulty, score, feedback_json
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    session_id,
                    int(record.get("question_id", 0)),
                    record.get("question", ""),
                    record.get("answer", ""),
                    record.get("topic", "general"),
                    record.get("difficulty", "beginner"),
                    float(record.get("score", 0)),
                    json.dumps(record.get("feedback", {})),
                ),
            )
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception:
            return False

    def complete_interview_session(self, session_id: int, report: Dict) -> bool:
        try:
            summary = report.get("summary", {})
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE interview_sessions
                SET ended_at=%s,
                    total_questions=%s,
                    overall_score=%s,
                    performance_level=%s,
                    report_json=%s
                WHERE id=%s
                """,
                (
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    int(summary.get("total_questions", 0)),
                    float(summary.get("overall_score", 0)),
                    summary.get("performance_level", "unknown"),
                    json.dumps(report, default=str),
                    session_id,
                ),
            )
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception:
            return False

    def get_recent_interviews(self, user_id: int, limit: int = 5) -> List[Dict]:
        try:
            conn = self._connect()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, started_at, ended_at, total_questions, overall_score, performance_level,
                       (report_json IS NOT NULL AND LENGTH(report_json) > 0) AS has_report
                FROM interview_sessions
                WHERE user_id=%s
                ORDER BY started_at DESC
                LIMIT %s
                """,
                (user_id, limit),
            )
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows or []
        except Exception:
            return []

    def list_users_admin(self) -> List[Dict[str, Any]]:
        try:
            conn = self._connect()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, full_name, email, is_admin, created_at
                FROM users
                ORDER BY id ASC
                """
            )
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows or []
        except Exception:
            return []

    def list_interview_sessions_for_user(self, user_id: int) -> List[Dict[str, Any]]:
        try:
            conn = self._connect()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, user_id, started_at, ended_at, total_questions,
                       overall_score, performance_level,
                       (report_json IS NOT NULL AND LENGTH(report_json) > 0) AS has_report
                FROM interview_sessions
                WHERE user_id=%s
                ORDER BY started_at DESC
                """,
                (user_id,),
            )
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows or []
        except Exception:
            return []

    def get_session_report_json(self, session_id: int) -> Optional[Dict[str, Any]]:
        try:
            conn = self._connect()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, user_id, started_at, ended_at, report_json
                FROM interview_sessions
                WHERE id=%s
                """,
                (session_id,),
            )
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            if not row or not row.get("report_json"):
                return None
            return json.loads(row["report_json"])
        except Exception:
            return None

    def get_session_answers(self, session_id: int) -> List[Dict[str, Any]]:
        """Retrieve saved answer records for a session so the feedback page
        can render the question-by-question review."""
        try:
            conn = self._connect()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT question_text, answer_text, topic, difficulty,
                       score, feedback_json
                FROM interview_answers
                WHERE session_id=%s
                ORDER BY id ASC
                """,
                (session_id,),
            )
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            result = []
            for r in rows:
                fb = {}
                if r.get("feedback_json"):
                    try:
                        fb = json.loads(r["feedback_json"])
                    except Exception:
                        pass
                result.append({
                    "question": r.get("question_text", ""),
                    "answer": r.get("answer_text", ""),
                    "topic": r.get("topic", "general"),
                    "difficulty": r.get("difficulty", "beginner"),
                    "score": float(r.get("score", 0)),
                    "feedback": fb,
                })
            return result
        except Exception:
            return []
