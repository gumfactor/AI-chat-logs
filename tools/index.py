#!/usr/bin/env python3
"""
tools/index.py — Index all session transcripts into a SQLite FTS5 database.

Usage:
    python tools/index.py

Walks sessions/ recursively. For each session folder containing a metadata.yaml,
reads metadata and indexes all .md files into index/sessions.db.

Run after each new session commit to keep the index current.
"""

import os
import sqlite3
import sys

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSIONS_DIR = os.path.join(REPO_ROOT, "sessions")
DB_PATH = os.path.join(REPO_ROOT, "index", "sessions.db")


def parse_yaml_simple(text):
    """
    Minimal YAML parser for the subset used in metadata.yaml.
    Handles scalar string values only. Falls back to empty dict on any error.
    Only used when the `yaml` package is not available.
    """
    result = {}
    for line in text.splitlines():
        # Skip comments and blank lines
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip()
        # Strip inline comments
        if " #" in value:
            value = value[: value.index(" #")].strip()
        # Strip quotes
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        # Treat null/~/{} as empty string
        if value in ("null", "~", "[]", "{}"):
            value = ""
        result[key] = value
    return result


def load_metadata(yaml_path):
    """Read metadata.yaml and return a dict with the fields we care about."""
    defaults = {
        "session_id": "",
        "date": "",
        "agent": "unknown",
        "model": "unknown",
        "repo": "",
        "status": "",
        "platform_url": "",
    }
    if not os.path.isfile(yaml_path):
        return defaults

    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return defaults

    if _YAML_AVAILABLE:
        try:
            data = yaml.safe_load(text) or {}
        except Exception:
            data = {}
    else:
        data = parse_yaml_simple(text)

    def get(key):
        val = data.get(key)
        if val is None:
            return defaults.get(key, "")
        return str(val).strip()

    # Derive date from timestamp_start if 'date' field absent
    date = get("date")
    if not date:
        ts = get("timestamp_start")
        if ts and ts != "null":
            date = ts[:10]  # "YYYY-MM-DD"

    return {
        "session_id": get("session_id") or defaults["session_id"],
        "date": date,
        "agent": get("agent") or defaults["agent"],
        "model": get("model") or defaults["model"],
        "repo": get("repo") or defaults["repo"],
        "status": get("status") or defaults["status"],
        "platform_url": get("platform_url") or defaults["platform_url"],
    }


def init_db(conn):
    """Create tables if they don't exist."""
    conn.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS transcripts USING fts5(
            session_id,
            date,
            agent,
            repo,
            filename,
            content
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS session_meta (
            session_id TEXT PRIMARY KEY,
            date TEXT,
            agent TEXT,
            model TEXT,
            repo TEXT,
            status TEXT,
            platform_url TEXT,
            folder_path TEXT
        )
        """
    )
    conn.commit()


def upsert_session(conn, meta, folder_path, md_files):
    """Delete and re-insert a session's rows so re-runs are idempotent."""
    session_id = meta["session_id"]

    # Upsert session_meta
    conn.execute(
        """
        INSERT INTO session_meta
            (session_id, date, agent, model, repo, status, platform_url, folder_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(session_id) DO UPDATE SET
            date=excluded.date,
            agent=excluded.agent,
            model=excluded.model,
            repo=excluded.repo,
            status=excluded.status,
            platform_url=excluded.platform_url,
            folder_path=excluded.folder_path
        """,
        (
            session_id,
            meta["date"],
            meta["agent"],
            meta["model"],
            meta["repo"],
            meta["status"],
            meta["platform_url"],
            folder_path,
        ),
    )

    # Delete existing FTS rows for this session before re-inserting
    conn.execute("DELETE FROM transcripts WHERE session_id = ?", (session_id,))

    # Insert one FTS row per .md file
    rows = []
    for filepath in md_files:
        filename = os.path.basename(filepath)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError:
            content = ""
        rows.append(
            (
                session_id,
                meta["date"],
                meta["agent"],
                meta["repo"],
                filename,
                content,
            )
        )

    conn.executemany(
        "INSERT INTO transcripts (session_id, date, agent, repo, filename, content) VALUES (?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    return len(rows)


def find_session_folders(sessions_dir):
    """
    Walk sessions_dir and yield (folder_path) for every leaf directory that
    contains at least one .md file. Sessions can be arbitrarily nested.
    """
    if not os.path.isdir(sessions_dir):
        return

    for dirpath, dirnames, filenames in os.walk(sessions_dir):
        # Skip hidden directories
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        md_files = [
            os.path.join(dirpath, f)
            for f in filenames
            if f.endswith(".md")
        ]
        if md_files:
            yield dirpath, md_files


def main():
    # Ensure index directory exists
    index_dir = os.path.dirname(DB_PATH)
    os.makedirs(index_dir, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    total_sessions = 0
    total_files = 0
    live_session_ids = set()

    for folder_path, md_files in find_session_folders(SESSIONS_DIR):
        yaml_path = os.path.join(folder_path, "metadata.yaml")
        meta = load_metadata(yaml_path)

        # If no session_id in metadata, derive one from folder name
        if not meta["session_id"]:
            meta["session_id"] = os.path.basename(folder_path)

        # If no date in metadata, try to derive from folder path
        if not meta["date"]:
            # Path like .../sessions/2026/2026-06-20/TASK-.../
            parts = folder_path.replace(SESSIONS_DIR, "").strip(os.sep).split(os.sep)
            for part in parts:
                if len(part) == 10 and part.count("-") == 2:
                    meta["date"] = part
                    break

        file_count = upsert_session(conn, meta, folder_path, md_files)
        print(f"[indexed] {meta['session_id']} ({file_count} file{'s' if file_count != 1 else ''})")
        total_sessions += 1
        total_files += file_count
        live_session_ids.add(meta["session_id"])

    # Tombstone sessions that no longer exist on disk (preserve rows, mark deleted)
    if live_session_ids:
        stale_ids = [
            row[0]
            for row in conn.execute("SELECT session_id FROM session_meta").fetchall()
            if row[0] not in live_session_ids
        ]
        if stale_ids:
            for sid in stale_ids:
                conn.execute(
                    "UPDATE session_meta SET status = 'deleted' WHERE session_id = ?",
                    (sid,),
                )
                print(f"[tombstoned] {sid} (folder no longer exists)")
            conn.commit()

    conn.close()

    if total_sessions == 0:
        print("No session folders found. Nothing to index.")
    else:
        print(f"\nDone. {total_sessions} session(s), {total_files} file(s) indexed into {DB_PATH}")


if __name__ == "__main__":
    main()
