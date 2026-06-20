#!/usr/bin/env python3
"""
tools/search.py — Search session transcripts indexed in index/sessions.db.

Usage:
    python tools/search.py "query terms"
    python tools/search.py "query terms" --session TASK-20260620-0001
    python tools/search.py "query terms" --include-deleted
    python tools/search.py --help

Options:
    --session SESSION_ID    Restrict search to a specific session.
    --include-deleted       Include sessions that have been tombstoned (deleted from disk).
                            By default, deleted sessions are excluded from search results.
    --help                  Show this help message and exit.

Prerequisites:
    Run `python tools/index.py` first to build the index.
"""

import os
import sqlite3
import sys


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(REPO_ROOT, "index", "sessions.db")

SNIPPET_TOKENS = 20  # roughly how many words appear in each snippet chunk


def parse_args(argv):
    """Parse CLI arguments. Returns (query, session_id_filter, include_deleted)."""
    args = argv[1:]  # drop script name

    if not args or "--help" in args or "-h" in args:
        print(__doc__.strip())
        sys.exit(0)

    session_filter = None
    include_deleted = False
    remaining = []
    i = 0
    while i < len(args):
        if args[i] == "--session":
            if i + 1 >= len(args):
                print("Error: --session requires a value.", file=sys.stderr)
                sys.exit(1)
            session_filter = args[i + 1]
            i += 2
        elif args[i] == "--include-deleted":
            include_deleted = True
            i += 1
        else:
            remaining.append(args[i])
            i += 1

    if not remaining:
        print("Error: No query provided.", file=sys.stderr)
        print("Usage: python tools/search.py \"query terms\"", file=sys.stderr)
        sys.exit(1)

    query = " ".join(remaining)
    if not query.strip():
        print("Error: No query provided.", file=sys.stderr)
        print('Usage: python tools/search.py "query terms"', file=sys.stderr)
        sys.exit(1)
    return query, session_filter, include_deleted


def check_db():
    """Exit with a helpful message if the database doesn't exist."""
    if not os.path.isfile(DB_PATH):
        print(
            f"Error: index not found at {DB_PATH}\n"
            "Run `python tools/index.py` first to build the search index.",
            file=sys.stderr,
        )
        sys.exit(1)


def get_deleted_session_ids(conn):
    """Return a set of session IDs that have been tombstoned (status = 'deleted')."""
    try:
        rows = conn.execute(
            "SELECT session_id FROM session_meta WHERE status = 'deleted'"
        ).fetchall()
        return {row[0] for row in rows}
    except sqlite3.OperationalError:
        # session_meta table may not exist in older DBs
        return set()


def run_search(query, session_filter=None, include_deleted=False):
    """
    Query the FTS5 index and return a list of result dicts.
    Each dict has: session_id, date, agent, repo, filename, snippet.

    By default, sessions with status='deleted' in session_meta are excluded.
    Pass include_deleted=True to include them.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    if session_filter:
        sql = """
            SELECT
                session_id,
                date,
                agent,
                repo,
                filename,
                snippet(transcripts, 5, '>>>', '<<<', '...', ?) AS snippet
            FROM transcripts
            WHERE transcripts MATCH ?
              AND session_id = ?
            ORDER BY rank
        """
        rows = conn.execute(sql, (SNIPPET_TOKENS, query, session_filter)).fetchall()
    else:
        sql = """
            SELECT
                session_id,
                date,
                agent,
                repo,
                filename,
                snippet(transcripts, 5, '>>>', '<<<', '...', ?) AS snippet
            FROM transcripts
            WHERE transcripts MATCH ?
            ORDER BY rank
        """
        rows = conn.execute(sql, (SNIPPET_TOKENS, query)).fetchall()

    results = [dict(r) for r in rows]

    if not include_deleted:
        deleted_ids = get_deleted_session_ids(conn)
        if deleted_ids:
            filtered = [r for r in results if r["session_id"] not in deleted_ids]
            excluded_count = len(results) - len(filtered)
            results = filtered
            if excluded_count > 0:
                results = (filtered, excluded_count)
                conn.close()
                return results

    conn.close()
    return results


def print_results(results, query, session_filter=None):
    """Format and print results to stdout."""
    header = f"Search results for: \"{query}\""
    if session_filter:
        header += f"  [session: {session_filter}]"
    print(header)
    print("=" * len(header))

    for i, r in enumerate(results, start=1):
        snippet = (r["snippet"] or "").strip()
        # Truncate to ~200 chars at a word boundary for readability
        if len(snippet) > 200:
            truncated = snippet[:200]
            last_space = truncated.rfind(" ")
            if last_space > 150:
                truncated = truncated[:last_space]
            snippet = truncated + "..."

        print(f"\n[{i}] {r['session_id']}")
        print(f"    Date     : {r['date'] or '(unknown)'}")
        print(f"    Agent    : {r['agent'] or '(unknown)'}")
        print(f"    Repo     : {r['repo'] or '(unknown)'}")
        print(f"    File     : {r['filename'] or '(unknown)'}")
        print(f"    Context  : {snippet}")

    print()


def main():
    query, session_filter, include_deleted = parse_args(sys.argv)
    check_db()

    excluded_count = 0
    try:
        raw = run_search(query, session_filter, include_deleted)
    except sqlite3.OperationalError as e:
        error_msg = str(e)
        if "no such table" in error_msg:
            print(
                "Error: index tables not found. Run `python tools/index.py` first.",
                file=sys.stderr,
            )
            sys.exit(1)
        elif "fts5: syntax error" in error_msg or "unknown special query" in error_msg:
            print(
                f"Error: invalid query syntax — {error_msg}\n"
                "Tip: wrap the query in quotes, e.g.: python tools/search.py \"your query\"",
                file=sys.stderr,
            )
            sys.exit(1)
        else:
            print(f"Database error: {error_msg}", file=sys.stderr)
            sys.exit(1)

    # run_search may return (results, excluded_count) when some results were filtered
    if isinstance(raw, tuple):
        results, excluded_count = raw
    else:
        results = raw

    if not results:
        if session_filter:
            print(f'No results found for "{query}" in session {session_filter}.')
        else:
            print(f'No results found for "{query}".')
        if excluded_count > 0:
            print(
                f"Note: {excluded_count} result(s) from deleted sessions were excluded. "
                "Use --include-deleted to include them."
            )
        sys.exit(0)

    print_results(results, query, session_filter)

    if excluded_count > 0:
        print(
            f"Note: {excluded_count} result(s) from deleted sessions were excluded. "
            "Use --include-deleted to include them."
        )


if __name__ == "__main__":
    main()
