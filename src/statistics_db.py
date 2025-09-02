"""SQLite database manager for Pomodoro statistics."""

import sqlite3
from pathlib import Path
from datetime import datetime, date
from typing import Optional, Dict, List, Tuple


class StatisticsDB:
    """Manages session statistics in SQLite database."""
    
    def __init__(self, db_path: Path):
        """Initialize database connection and create tables if needed.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._create_tables()
        self.current_session_id: Optional[int] = None
    
    def _create_tables(self):
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_type TEXT NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    planned_duration INTEGER NOT NULL,
                    actual_duration INTEGER,
                    completed BOOLEAN DEFAULT 0,
                    extend_count INTEGER DEFAULT 0,
                    profile_name TEXT
                )
            """)
            
            # Add profile_name column to existing tables (migration)
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(sessions)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'profile_name' not in columns:
                conn.execute("ALTER TABLE sessions ADD COLUMN profile_name TEXT")
            
            # Create index for faster queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_start_time 
                ON sessions(start_time)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_type 
                ON sessions(session_type)
            """)
            conn.commit()
    
    def start_session(self, session_type: str, planned_duration: int, profile_name: str = None) -> int:
        """Start a new session.
        
        Args:
            session_type: 'work', 'short_break', or 'long_break'
            planned_duration: Planned duration in minutes
            
        Returns:
            Session ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO sessions (session_type, start_time, planned_duration, extend_count, profile_name)
                VALUES (?, ?, ?, 0, ?)
            """, (session_type, datetime.now(), planned_duration, profile_name))
            session_id = cursor.lastrowid
            conn.commit()
            self.current_session_id = session_id
            return session_id
    
    def end_session(self, session_id: Optional[int] = None, completed: bool = False, 
                    actual_seconds: int = 0, pause_count: int = 0, pause_seconds: int = 0) -> None:
        """End a session.
        
        Args:
            session_id: Session ID to end (uses current if None)
            completed: Whether session completed naturally
            actual_seconds: Actual seconds worked (excluding pauses)
            pause_count: Number of times paused
            pause_seconds: Total seconds spent paused
        """
        if session_id is None:
            session_id = self.current_session_id
        
        if session_id is None:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            # Get start time to calculate duration
            cursor = conn.execute(
                "SELECT start_time FROM sessions WHERE id = ?", 
                (session_id,)
            )
            row = cursor.fetchone()
            
            if row:
                end_time = datetime.now()
                
                # Use the actual worked seconds (excluding pauses) if provided
                # Otherwise fall back to wall clock time for backwards compatibility
                if actual_seconds > 0:
                    actual_duration = actual_seconds
                else:
                    start_time = datetime.fromisoformat(row[0])
                    actual_duration = int((end_time - start_time).total_seconds())
                
                conn.execute("""
                    UPDATE sessions 
                    SET end_time = ?, actual_duration = ?, completed = ?
                    WHERE id = ?
                """, (end_time, actual_duration, completed, session_id))
                conn.commit()
        
        if session_id == self.current_session_id:
            self.current_session_id = None
    
    def add_extend(self, session_id: Optional[int] = None) -> None:
        """Increment extend count for a session.
        
        Args:
            session_id: Session ID (uses current if None)
        """
        if session_id is None:
            session_id = self.current_session_id
        
        if session_id is None:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE sessions 
                SET extend_count = extend_count + 1
                WHERE id = ?
            """, (session_id,))
            conn.commit()
    
    def reopen_session(self, session_id: int) -> None:
        """Reopen a completed session (for extending after completion).
        
        Args:
            session_id: Session ID to reopen
        """
        with sqlite3.connect(self.db_path) as conn:
            # Clear the end time and completed flag, increment extend count
            conn.execute("""
                UPDATE sessions 
                SET end_time = NULL, 
                    actual_duration = NULL, 
                    completed = 0,
                    extend_count = extend_count + 1
                WHERE id = ?
            """, (session_id,))
            conn.commit()
        
        # Set as current session
        self.current_session_id = session_id
    
    def get_last_session_id(self) -> Optional[int]:
        """Get the ID of the most recent session.
        
        Returns:
            Session ID or None if no sessions exist
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id FROM sessions
                ORDER BY start_time DESC
                LIMIT 1
            """)
            row = cursor.fetchone()
            return row[0] if row else None
    
    def get_today_stats(self) -> Dict:
        """Get today's statistics.
        
        Returns:
            Dictionary with today's stats
        """
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(CASE WHEN session_type = 'work' AND completed = 1 THEN 1 END) as completed_pomodoros,
                    COUNT(CASE WHEN session_type = 'work' THEN 1 END) as total_work_sessions,
                    SUM(CASE WHEN session_type = 'work' AND completed = 1 THEN actual_duration END) as work_seconds,
                    COUNT(CASE WHEN session_type IN ('short_break', 'long_break') AND completed = 1 THEN 1 END) as completed_breaks,
                    SUM(extend_count) as total_extends
                FROM sessions
                WHERE start_time >= ?
            """, (today_start,))
            
            row = cursor.fetchone()
            
            return {
                'completed_pomodoros': row[0] or 0,
                'total_work_sessions': row[1] or 0,
                'work_minutes': (row[2] or 0) // 60,
                'completed_breaks': row[3] or 0,
                'total_extends': row[4] or 0
            }
    
    def get_all_time_stats(self) -> Dict:
        """Get all-time statistics.
        
        Returns:
            Dictionary with all-time stats
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(CASE WHEN session_type = 'work' AND completed = 1 THEN 1 END) as total_pomodoros,
                    SUM(CASE WHEN session_type = 'work' AND completed = 1 THEN actual_duration END) as total_work_seconds,
                    COUNT(CASE WHEN session_type IN ('short_break', 'long_break') AND completed = 1 THEN 1 END) as total_breaks,
                    AVG(CASE WHEN session_type = 'work' AND completed = 1 THEN actual_duration END) as avg_work_duration,
                    SUM(extend_count) as total_extends
                FROM sessions
            """)
            
            row = cursor.fetchone()
            
            return {
                'total_pomodoros': row[0] or 0,
                'total_work_minutes': (row[1] or 0) // 60,
                'total_breaks': row[2] or 0,
                'avg_work_minutes': (row[3] or 0) // 60 if row[3] else 0,
                'total_extends': row[4] or 0
            }
    
    def get_orphaned_sessions(self) -> List[Dict]:
        """Get sessions that were not properly closed (orphaned).
        
        Returns:
            List of orphaned session dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM sessions
                WHERE end_time IS NULL OR end_time = ''
                ORDER BY start_time DESC
            """)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def mark_session_as_crashed(self, session_id: int) -> None:
        """Mark a session as crashed/interrupted.
        
        Args:
            session_id: Session ID to mark as crashed
        """
        with sqlite3.connect(self.db_path) as conn:
            # Estimate the duration based on start time and current time
            cursor = conn.execute(
                "SELECT start_time, planned_duration FROM sessions WHERE id = ?",
                (session_id,)
            )
            row = cursor.fetchone()
            
            if row:
                start_time = datetime.fromisoformat(row[0])
                planned_duration_seconds = row[1] * 60
                
                # Use current time as estimated end time
                end_time = datetime.now()
                elapsed = int((end_time - start_time).total_seconds())
                
                # Cap actual duration at planned duration (can't work more than planned without extends)
                actual_duration = min(elapsed, planned_duration_seconds)
                
                conn.execute("""
                    UPDATE sessions 
                    SET end_time = ?, actual_duration = ?, completed = 0
                    WHERE id = ?
                """, (end_time, actual_duration, session_id))
                conn.commit()
    
    def get_recent_sessions(self, limit: int = 10) -> List[Dict]:
        """Get recent sessions.
        
        Args:
            limit: Number of sessions to return
            
        Returns:
            List of session dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM sessions
                ORDER BY start_time DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_profile_stats(self, profile_name: str = None) -> Dict:
        """Get statistics for a specific profile or all profiles.
        
        Args:
            profile_name: Profile name to filter by (None for all profiles)
            
        Returns:
            Dictionary with profile-specific stats
        """
        with sqlite3.connect(self.db_path) as conn:
            if profile_name:
                cursor = conn.execute("""
                    SELECT 
                        COUNT(CASE WHEN session_type = 'work' AND completed = 1 THEN 1 END) as completed_pomodoros,
                        SUM(CASE WHEN session_type = 'work' AND completed = 1 THEN actual_duration END) as work_seconds,
                        COUNT(CASE WHEN session_type IN ('short_break', 'long_break') AND completed = 1 THEN 1 END) as completed_breaks,
                        AVG(CASE WHEN session_type = 'work' AND completed = 1 THEN actual_duration END) as avg_work_duration
                    FROM sessions
                    WHERE profile_name = ?
                """, (profile_name,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'completed_pomodoros': row[0] or 0,
                        'work_seconds': row[1] or 0,
                        'completed_breaks': row[2] or 0,
                        'avg_work_duration': row[3] or 0
                    }
                return {'completed_pomodoros': 0, 'work_seconds': 0, 'completed_breaks': 0, 'avg_work_duration': 0}
            else:
                cursor = conn.execute("""
                    SELECT 
                        profile_name,
                        COUNT(CASE WHEN session_type = 'work' AND completed = 1 THEN 1 END) as completed_pomodoros,
                        SUM(CASE WHEN session_type = 'work' AND completed = 1 THEN actual_duration END) as work_seconds
                    FROM sessions
                    WHERE profile_name IS NOT NULL
                    GROUP BY profile_name
                """)
                
                return [
                    {'profile': row[0], 'completed_pomodoros': row[1], 'work_seconds': row[2]}
                    for row in cursor.fetchall()
                ]