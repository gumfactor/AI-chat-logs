#!/usr/bin/env python3
"""
tools/generate_summary.py — Create or update a session's summary.md with a Mermaid DAG section.

Usage:
    python tools/generate_summary.py TASK-20260620-0041
    python tools/generate_summary.py TASK-20260620-0041 --force

If summary.md does not exist, creates it from the standard blank template and
appends a Mermaid DAG section at the bottom.

If summary.md already exists, appends the DAG section only if it isn't already
present (idempotent — safe to run multiple times).

If summary.md already exists and already has a DAG section, the second run
prints "DAG section already present" and exits 0. Pass --force to replace the
existing DAG section instead (useful when new subagents are added mid-task).

The DAG section shows the full session tree rooted at the given session ID,
using the same logic as `tools/dag.py --root TASK-ID`.
"""

import os
import sys

# We import from dag.py in the same tools/ directory
_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_TOOLS_DIR)

# Add tools/ to sys.path so we can import dag
sys.path.insert(0, _TOOLS_DIR)

try:
    from dag import build_graph, descendants, detect_cycles, render_mermaid, format_mermaid_block, SESSIONS_DIR
except ImportError as e:
    print(f"Error: could not import dag.py — {e}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DAG_SECTION_HEADER = "## Session DAG"
DAG_SECTION_MARKER = "<!-- dag:generated -->"


# ---------------------------------------------------------------------------
# Summary template
# ---------------------------------------------------------------------------

def blank_summary(task_id):
    """Return the standard blank summary.md content for a given task ID."""
    return f"""# Summary: {task_id}

## What this session produced

<!-- Written after the session closes. What was accomplished, what remains open. -->

## What remains open

<!-- Open questions, deferred decisions, follow-up tasks. -->

## Status

<!-- open | returned | repair | merged | abandoned -->

---

## Self-Audit

**What did I change?**

**What did I not touch?**

**What could be wrong?**

**How did I test it?**

**What is unresolved?**
"""


# ---------------------------------------------------------------------------
# DAG section generation
# ---------------------------------------------------------------------------

def generate_dag_section(task_id, sessions, children, parents):
    """
    Generate the DAG Mermaid block section for a given session.

    Returns a string containing the section header, marker comment, and
    the Mermaid fenced code block.
    """
    scope_ids = descendants(children, task_id)

    # Detect cycles
    cycle_edges = detect_cycles(children, task_id)

    # Check if there are any relationships in scope
    has_relationships = False
    for sid in scope_ids:
        scoped_children = children.get(sid, set()) & scope_ids
        if scoped_children:
            has_relationships = True
            break

    if not has_relationships:
        diagram_content = (
            "No parent/child relationships found for this session. "
            "It is an independent session with no subagents."
        )
    else:
        lines = render_mermaid(sessions, children, parents, scope_ids, cycle_edges)
        diagram_content = format_mermaid_block(lines)

    return f"""{DAG_SECTION_HEADER}

{DAG_SECTION_MARKER}

{diagram_content}
"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def find_session_folder(task_id):
    """
    Walk sessions/ to find the folder for the given task_id.
    Returns the absolute folder path, or None if not found.
    """
    for dirpath, dirnames, filenames in os.walk(SESSIONS_DIR):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        if os.path.basename(dirpath) == task_id:
            return dirpath
    return None


def main():
    argv = sys.argv[1:]

    if not argv or argv[0] in ("--help", "-h"):
        print(__doc__.strip())
        sys.exit(0)

    # Parse --force flag
    force = False
    remaining = []
    for arg in argv:
        if arg == "--force":
            force = True
        else:
            remaining.append(arg)
    argv = remaining

    if not argv:
        print("Error: task ID is required.", file=sys.stderr)
        print("Usage: python tools/generate_summary.py TASK-YYYYMMDD-NNNN", file=sys.stderr)
        sys.exit(1)

    task_id = argv[0].strip()
    if not task_id:
        print("Error: task ID is required.", file=sys.stderr)
        print("Usage: python tools/generate_summary.py TASK-YYYYMMDD-NNNN", file=sys.stderr)
        sys.exit(1)

    # Locate session folder
    session_folder = find_session_folder(task_id)
    if session_folder is None:
        print(
            f"Error: session '{task_id}' not found in sessions/.",
            file=sys.stderr,
        )
        sys.exit(1)

    summary_path = os.path.join(session_folder, "summary.md")

    # Build graph
    sessions, children, parents = build_graph(SESSIONS_DIR)

    if task_id not in sessions:
        print(
            f"Error: session '{task_id}' found on disk but could not load its metadata.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Generate the DAG section
    dag_section = generate_dag_section(task_id, sessions, children, parents)

    # Check if summary.md exists
    if not os.path.exists(summary_path):
        # Create from blank template + DAG section
        content = blank_summary(task_id) + "\n---\n\n" + dag_section
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Created summary.md with DAG section: {summary_path}")
        return

    # summary.md exists — check if DAG section is already present (idempotency)
    with open(summary_path, "r", encoding="utf-8") as f:
        existing = f.read()

    if DAG_SECTION_MARKER in existing:
        if not force:
            print(f"DAG section already present in {summary_path}. Nothing to do.")
            print("Use --force to replace the existing DAG section.")
            return
        # --force: replace the existing DAG section
        # Find the marker position and remove everything from it to the end of the
        # DAG block. The block ends at the next '---' separator or end of file.
        marker_pos = existing.index(DAG_SECTION_MARKER)
        # Walk back to include the section header if it immediately precedes the marker
        # (i.e. "## Session DAG\n\n<!-- dag:generated -->")
        before_marker = existing[:marker_pos]
        # Strip trailing whitespace to get a clean cut point
        before = before_marker.rstrip()
        # Remove the trailing section header line if present
        if before.endswith(DAG_SECTION_HEADER):
            before = before[: -len(DAG_SECTION_HEADER)].rstrip()
        # Also strip the separator that preceded the section header, so we
        # don't accumulate extra '---' lines on repeated --force runs.
        while before.endswith("---"):
            before = before[:-3].rstrip()

        # Everything from marker_pos to end is replaced by the new dag_section
        new_content = before + "\n\n---\n\n" + dag_section
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Replaced DAG section in: {summary_path}")
        return

    # Append the DAG section
    # Ensure there's a separator before the new section
    separator = "\n---\n\n" if not existing.rstrip().endswith("---") else "\n\n"
    with open(summary_path, "a", encoding="utf-8") as f:
        f.write(separator + dag_section)
    print(f"Appended DAG section to: {summary_path}")


if __name__ == "__main__":
    main()
