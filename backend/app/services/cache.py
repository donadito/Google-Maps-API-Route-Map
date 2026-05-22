from __future__ import annotations

import sqlite3
import threading
import time

MAX_AGE_SECONDS = 60 * 60 * 24 * 30  # 30 días


class DistanceCache:
  def __init__(self, db_path: str) -> None:
    self._lock = threading.Lock()
    self._memory: dict[tuple[str, str], tuple[float, float, int]] = {}
    self._conn = sqlite3.connect(db_path, check_same_thread=False)
    self._conn.execute(
      """
      CREATE TABLE IF NOT EXISTS distance_cache (
        origin_key TEXT NOT NULL,
        destination_key TEXT NOT NULL,
        distance_meters REAL NOT NULL,
        duration_seconds REAL NOT NULL,
        updated_at INTEGER NOT NULL,
        PRIMARY KEY (origin_key, destination_key)
      )
      """
    )
    self._conn.commit()

  def close(self) -> None:
    self._conn.close()

  def get(self, origin_key: str, destination_key: str) -> tuple[float, float] | None:
    memory_key = (origin_key, destination_key)
    cached = self._memory.get(memory_key)
    if cached is not None:
      distance, duration, updated_at = cached
      if int(time.time()) - updated_at <= MAX_AGE_SECONDS:
        return (distance, duration)
      self._memory.pop(memory_key, None)

    with self._lock:
      cursor = self._conn.execute(
        """
        SELECT distance_meters, duration_seconds, updated_at
        FROM distance_cache
        WHERE origin_key = ? AND destination_key = ?
          AND updated_at > ?
        """,
        (origin_key, destination_key, int(time.time()) - MAX_AGE_SECONDS),
      )
      row = cursor.fetchone()

    if not row:
      return None

    distance, duration, updated_at = float(row[0]), float(row[1]), int(row[2])
    self._memory[memory_key] = (distance, duration, updated_at)
    return (distance, duration)

  def set_many(self, records: list[tuple[str, str, float, float]]) -> None:
    if not records:
      return

    now = int(time.time())
    with self._lock:
      self._conn.executemany(
        """
        INSERT OR REPLACE INTO distance_cache
        (origin_key, destination_key, distance_meters, duration_seconds, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
          (origin, destination, distance, duration, now)
          for origin, destination, distance, duration in records
        ],
      )
      self._conn.commit()
      for origin, destination, distance, duration in records:
        self._memory[(origin, destination)] = (distance, duration, now)
