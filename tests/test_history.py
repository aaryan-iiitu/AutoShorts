import os
import sqlite3
import pytest
from services.history import SQLiteHistory

def test_history_backend_records_success(tmp_path):
    db_path = os.path.join(tmp_path, "test_history.db")
    history = SQLiteHistory(db_path=db_path)
    
    # Test getting empty topics
    assert len(history.get_recent_topics()) == 0
    
    # Record a success
    history.record_success("AI Agents", "https://youtube.com/shorts/123")
    
    # Verify it was recorded
    recent = history.get_recent_topics()
    assert len(recent) == 1
    assert recent[0] == "AI Agents"

    # Verify DB directly
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status, youtube_url FROM history WHERE topic = 'AI Agents'")
        row = cursor.fetchone()
        assert row[0] == "success"
        assert row[1] == "https://youtube.com/shorts/123"

def test_history_backend_records_failure(tmp_path):
    db_path = os.path.join(tmp_path, "test_history.db")
    history = SQLiteHistory(db_path=db_path)
    
    # Record a failure
    history.record_failure("Quantum Computing", "API Timeout")
    
    # Failure should NOT be returned in recent topics to allow trying again later
    # Wait, the prompt says "prevent duplicate topics". Does a failed topic count as duplicate?
    # Our implementation checks WHERE status IN ('success', 'pending')
    # So a failed one is NOT returned, meaning we CAN try it again.
    recent = history.get_recent_topics()
    assert len(recent) == 0

    # Verify DB directly
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status, error_message FROM history WHERE topic = 'Quantum Computing'")
        row = cursor.fetchone()
        assert row[0] == "failure"
        assert row[1] == "API Timeout"
