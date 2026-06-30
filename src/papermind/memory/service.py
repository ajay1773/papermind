import json
import logging
from datetime import datetime

from papermind.memory.models import get_connection

logger = logging.getLogger(__name__)


class MemoryService:
    def get_indexed_paper_ids(self) -> set[str]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT paper_id FROM indexed_papers")
        result = {row["paper_id"] for row in cursor.fetchall()}
        conn.close()
        return result

    def add_indexed_paper(self, paper_id: str, title: str, source: str) -> None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO indexed_papers (paper_id, title, source, indexed_at)
            VALUES (?, ?, ?, ?)
            """,
            (paper_id, title, source, datetime.utcnow().isoformat()),
        )
        conn.commit()
        conn.close()

    def get_similar_briefings(self, topic: str, limit: int = 3) -> list[dict]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT topic, briefing_json, created_at
            FROM briefing_history
            WHERE topic LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (f"%{topic}%", limit),
        )
        results = []
        for row in cursor.fetchall():
            try:
                results.append({
                    "topic": row["topic"],
                    "briefing": json.loads(row["briefing_json"]),
                    "created_at": row["created_at"],
                })
            except json.JSONDecodeError:
                logger.warning("Failed to parse briefing JSON for topic: %s", row["topic"])
        conn.close()
        return results

    def save_briefing(self, topic: str, briefing: dict) -> None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO briefing_history (topic, briefing_json, created_at)
            VALUES (?, ?, ?)
            """,
            (topic, json.dumps(briefing), datetime.utcnow().isoformat()),
        )
        conn.commit()
        conn.close()

    def get_user_preferences(self) -> dict[str, str]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM user_preferences")
        result = {row["key"]: row["value"] for row in cursor.fetchall()}
        conn.close()
        return result

    def set_user_preference(self, key: str, value: str) -> None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO user_preferences (key, value)
            VALUES (?, ?)
            """,
            (key, value),
        )
        conn.commit()
        conn.close()

    def get_paper_extraction(self, paper_id: str) -> dict | None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT extraction_json FROM paper_extractions WHERE paper_id = ?",
            (paper_id,),
        )
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        try:
            return json.loads(row["extraction_json"])
        except json.JSONDecodeError:
            logger.warning("Failed to parse extraction JSON for paper: %s", paper_id)
            return None

    def save_paper_extraction(self, paper_id: str, extraction: dict) -> None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO paper_extractions (paper_id, extraction_json, extracted_at)
            VALUES (?, ?, ?)
            """,
            (paper_id, json.dumps(extraction), datetime.utcnow().isoformat()),
        )
        conn.commit()
        conn.close()

    def get_papers_with_cached_extractions(self) -> set[str]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT paper_id FROM paper_extractions")
        result = {row["paper_id"] for row in cursor.fetchall()}
        conn.close()
        return result

    def get_latest_briefing_for_topic(self, topic: str) -> dict | None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT topic, briefing_json, created_at
            FROM briefing_history
            WHERE LOWER(TRIM(topic)) = LOWER(TRIM(?))
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (topic,),
        )
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        try:
            return {
                "topic": row["topic"],
                "briefing": json.loads(row["briefing_json"]),
                "created_at": row["created_at"],
            }
        except json.JSONDecodeError:
            logger.warning("Failed to parse briefing JSON for topic: %s", row["topic"])
            return None

    def get_memory_context(self, topic: str) -> dict:
        context: dict = {
            "past_briefings": self.get_similar_briefings(topic),
            "user_preferences": self.get_user_preferences(),
        }
        prior = self.get_latest_briefing_for_topic(topic)
        if prior:
            context["prior_briefing"] = prior
        return context
