#!/usr/bin/env python3
"""
tools/dag.py — Generate a Mermaid DAG diagram of multi-agent session relationships.

Reads all metadata.yaml files in sessions/ and builds a graph from:
  - subagent_sessions: list of child session IDs in a parent's metadata (preferred)
  - parent_session: field in a child's metadata (fallback)

Usage:
    # Generate diagram for all sessions
    python tools/dag.py

    # Generate diagram rooted at a specific session (includes all descendants)
    python tools/dag.py --root TASK-20260620-0041

    # Write output to a file instead of stdout
    python tools/dag.py --output /tmp/dag.md

    # Append diagram to a session's summary.md (idempotent: skips if already present)
    python tools/dag.py --root TASK-20260620-0041 \\
        --append-to sessions/2026/2026-06-20/TASK-20260620-0041/summary.md

    # Replace an existing DAG section in the file
    python tools/dag.py --root TASK-20260620-0041 \\
        --append-to sessions/2026/2026-06-20/TASK-20260620-0041/summary.md --force
"""

import os
import sys

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSIONS_DIR = os.path.join(REPO_ROOT, "sessions")


# ---------------------------------------------------------------------------
# YAML loading
# ---------------------------------------------------------------------------

def _parse_yaml_simple(text):
    """
    Minimal YAML parser that handles the subset used in metadata.yaml.
    Returns a dict with string values. Lists are returned as Python lists
    for the fields we care about (subagent_sessions).
    Only used when the `yaml` package is not available.
    """
    result = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        # Skip comments and blank lines
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        if ":" not in stripped:
            i += 1
            continue

        key, _, rest = stripped.partition(":")
        key = key.strip()
        rest = rest.strip()

        # Strip inline comments
        if " #" in rest:
            rest = rest[: rest.index(" #")].strip()

        # Check if value is a YAML list (starts with [] or next lines are - items)
        if rest == "[]":
            result[key] = []
            i += 1
            continue

        if rest == "" or rest == "null" or rest == "~":
            # Could be a block list — peek ahead
            items = []
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                next_stripped = next_line.strip()
                if next_stripped.startswith("- "):
                    item = next_stripped[2:].strip()
                    # Strip quotes
                    if (item.startswith('"') and item.endswith('"')) or \
                       (item.startswith("'") and item.endswith("'")):
                        item = item[1:-1]
                    items.append(item)
                    j += 1
                elif next_stripped.startswith("-") and len(next_stripped) == 1:
                    # bare "-" — empty item
                    j += 1
                elif not next_stripped or next_stripped.startswith("#"):
                    j += 1
                else:
                    break

            if items:
                result[key] = items
                i = j
                continue
            else:
                if rest == "" or rest == "null" or rest == "~":
                    result[key] = None
                    i += 1
                    continue

        # Inline list [item1, item2]
        if rest.startswith("[") and rest.endswith("]"):
            inner = rest[1:-1]
            items = [s.strip().strip('"').strip("'") for s in inner.split(",") if s.strip()]
            result[key] = items
            i += 1
            continue

        # Strip quotes from scalar
        if (rest.startswith('"') and rest.endswith('"')) or \
           (rest.startswith("'") and rest.endswith("'")):
            rest = rest[1:-1]

        result[key] = rest
        i += 1

    return result


def load_yaml(path):
    """Load a YAML file and return a dict. Returns empty dict on any error."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return {}

    if _YAML_AVAILABLE:
        try:
            data = yaml.safe_load(text) or {}
        except Exception:
            data = {}
    else:
        data = _parse_yaml_simple(text)

    return data if isinstance(data, dict) else {}


# ---------------------------------------------------------------------------
# Session discovery
# ---------------------------------------------------------------------------

def find_all_sessions(sessions_dir):
    """
    Walk sessions_dir recursively. For every directory that contains a
    metadata.yaml, load it and yield (session_id, metadata_dict, folder_path).
    Silently skips folders without metadata.yaml.
    """
    if not os.path.isdir(sessions_dir):
        return

    for dirpath, dirnames, filenames in os.walk(sessions_dir):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        if "metadata.yaml" in filenames:
            meta_path = os.path.join(dirpath, "metadata.yaml")
            data = load_yaml(meta_path)
            session_id = data.get("session_id")
            if not session_id:
                # Derive from folder name
                session_id = os.path.basename(dirpath)
            yield session_id, data, dirpath


# ---------------------------------------------------------------------------
# Graph building
# ---------------------------------------------------------------------------

def build_graph(sessions_dir):
    """
    Build the parent→children relationship graph.

    Returns:
        sessions: dict of session_id → metadata dict
        children: dict of session_id → set of child session_ids
        parents: dict of session_id → parent session_id or None
    """
    sessions = {}
    children = {}   # parent_id → set of child_ids
    parents = {}    # child_id → parent_id

    # First pass: load all sessions
    for session_id, data, folder in find_all_sessions(sessions_dir):
        sessions[session_id] = data
        if session_id not in children:
            children[session_id] = set()
        if session_id not in parents:
            parents[session_id] = None

    # Second pass: build edges
    for session_id, data in sessions.items():
        # Primary source: subagent_sessions in parent
        subagent_list = data.get("subagent_sessions")
        if isinstance(subagent_list, list):
            for child_id in subagent_list:
                if not child_id or not isinstance(child_id, str):
                    continue
                child_id = child_id.strip()
                if child_id not in sessions:
                    # Child referenced but not found — skip silently
                    continue
                children.setdefault(session_id, set()).add(child_id)
                parents[child_id] = session_id

        # Fallback: parent_session in child (only if not already set via subagent_sessions)
        parent_id = data.get("parent_session")
        if parent_id and isinstance(parent_id, str) and parent_id.strip():
            parent_id = parent_id.strip()
            if parent_id in sessions and parents.get(session_id) is None:
                parents[session_id] = parent_id
                children.setdefault(parent_id, set()).add(session_id)

    return sessions, children, parents


def detect_cycles(children, start_id):
    """
    DFS from start_id. Returns a set of (parent, child) edges that would
    introduce a cycle. Warns to stderr for each one found.
    """
    visited = set()
    in_stack = set()
    cycle_edges = set()

    def dfs(node):
        visited.add(node)
        in_stack.add(node)
        for child in list(children.get(node, set())):
            if child not in visited:
                dfs(child)
            elif child in in_stack:
                print(
                    f"Warning: circular reference detected: {node} → {child}. "
                    "Skipping that edge.",
                    file=sys.stderr,
                )
                cycle_edges.add((node, child))
        in_stack.discard(node)

    dfs(start_id)
    return cycle_edges


def descendants(children, root):
    """Return the set of all session IDs reachable from root (including root)."""
    seen = set()
    stack = [root]
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        for child in children.get(node, set()):
            stack.append(child)
    return seen


# ---------------------------------------------------------------------------
# Mermaid rendering
# ---------------------------------------------------------------------------

def mermaid_id(session_id):
    """Convert a session ID to a valid Mermaid node identifier (no hyphens)."""
    return session_id.replace("-", "_")


def node_label(session_id, data):
    """Build the display label for a node."""
    agent = data.get("agent") or "unknown"
    label = f"{session_id} ({agent})"
    if str(data.get("orchestrator", "")).lower() in ("true", "1", "yes"):
        label += " [orchestrator]"
    return label


def render_mermaid(sessions, children, parents, scope_ids=None, cycle_edges=None):
    """
    Generate a Mermaid graph TD string.

    Args:
        sessions:     dict of session_id → metadata
        children:     dict of session_id → set of child session_ids
        parents:      dict of session_id → parent_id or None
        scope_ids:    if not None, only render these session IDs
        cycle_edges:  set of (parent, child) edges to skip

    Returns a list of lines (without the fenced code block wrapper).
    """
    if cycle_edges is None:
        cycle_edges = set()

    if scope_ids is not None:
        render_sessions = {k: v for k, v in sessions.items() if k in scope_ids}
    else:
        render_sessions = sessions

    lines = ["graph TD"]

    # Node definitions (sorted for deterministic output)
    for sid in sorted(render_sessions.keys()):
        data = render_sessions[sid]
        mid = mermaid_id(sid)
        label = node_label(sid, data)
        lines.append(f'    {mid}["{label}"]')

    # Edge definitions
    edges_added = set()
    for sid in sorted(render_sessions.keys()):
        for child_id in sorted(children.get(sid, set())):
            if scope_ids is not None and child_id not in scope_ids:
                continue
            edge = (sid, child_id)
            if edge in cycle_edges:
                continue
            if edge not in edges_added:
                lines.append(f"    {mermaid_id(sid)} --> {mermaid_id(child_id)}")
                edges_added.add(edge)

    # Style abandoned sessions differently
    for sid in sorted(render_sessions.keys()):
        data = render_sessions[sid]
        if str(data.get("status", "")).strip().lower() == "abandoned":
            mid = mermaid_id(sid)
            lines.append(f"    style {mid} fill:#eee,color:#999")

    return lines


def format_mermaid_block(lines):
    """Wrap Mermaid lines in a fenced code block."""
    return "```mermaid\n" + "\n".join(lines) + "\n```"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

DAG_SECTION_MARKER = "<!-- dag:generated -->"


def parse_args(argv):
    """Parse CLI arguments manually (no argparse dependency)."""
    args = argv[1:]

    root = None
    output = None
    append_to = None
    force = False

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("--help", "-h"):
            print(__doc__.strip())
            sys.exit(0)
        elif arg == "--root":
            if i + 1 >= len(args):
                print("Error: --root requires a session ID value.", file=sys.stderr)
                sys.exit(1)
            root = args[i + 1]
            i += 2
        elif arg == "--output":
            if i + 1 >= len(args):
                print("Error: --output requires a file path.", file=sys.stderr)
                sys.exit(1)
            output = args[i + 1]
            i += 2
        elif arg == "--append-to":
            if i + 1 >= len(args):
                print("Error: --append-to requires a file path.", file=sys.stderr)
                sys.exit(1)
            append_to = args[i + 1]
            i += 2
        elif arg == "--force":
            force = True
            i += 1
        else:
            print(f"Error: unknown argument: {arg}", file=sys.stderr)
            sys.exit(1)

    return root, output, append_to, force


def main():
    root_id, output_path, append_to_path, force = parse_args(sys.argv)

    # Load all sessions and build the graph
    sessions, children, parents = build_graph(SESSIONS_DIR)

    # Validate --root if provided
    if root_id is not None and root_id not in sessions:
        print(
            f"Error: session '{root_id}' not found in sessions/. "
            "Check the session ID and try again.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Determine which sessions to render
    if root_id is not None:
        scope_ids = descendants(children, root_id)
    else:
        scope_ids = None  # render all

    # Check if there are any parent/child relationships at all (in scope)
    has_relationships = False
    check_sessions = scope_ids if scope_ids is not None else set(sessions.keys())
    for sid in check_sessions:
        if children.get(sid):
            # At least one of the children must also be in scope
            scoped_children = (
                children[sid] & scope_ids if scope_ids is not None else children[sid]
            )
            if scoped_children:
                has_relationships = True
                break

    if not has_relationships and (scope_ids is None or len(scope_ids) <= 1):
        # All sessions are independent
        if scope_ids is None or len(sessions) > 0:
            msg = "No parent/child relationships found. All sessions are independent."
            if output_path:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(msg + "\n")
                print(f"Written to {output_path}")
            elif append_to_path:
                _append_dag_to_file(append_to_path, msg)
            else:
                print(msg)
            return

    # Detect and remove cycle edges.
    # Strategy: attempt from explicit roots first. If no roots exist (every node
    # is part of a cycle with no entry point), fall back to running detection
    # from every node so fully-circular graphs are still caught.
    cycle_edges = set()
    if root_id is not None:
        cycle_edges = detect_cycles(children, root_id)
    else:
        roots = [sid for sid in sessions if parents.get(sid) is None]
        if roots:
            for r in roots:
                cycle_edges |= detect_cycles(children, r)
        else:
            # Fully-circular graph: every node has a parent. Run detection from
            # every node; the DFS visited-set prevents redundant work.
            all_visited = set()
            for sid in sessions:
                if sid not in all_visited:
                    edges = detect_cycles(children, sid)
                    cycle_edges |= edges
                    # Mark anything reachable from sid as visited
                    all_visited.update(descendants(children, sid))

    # Render the diagram
    lines = render_mermaid(sessions, children, parents, scope_ids, cycle_edges)
    diagram = format_mermaid_block(lines)

    # Output
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(diagram + "\n")
        print(f"Written to {output_path}")
    elif append_to_path:
        _append_dag_to_file(append_to_path, diagram, force=force)
    else:
        print(diagram)


def _append_dag_to_file(file_path, content, force=False):
    """
    Append content to a file, creating it if it doesn't exist.

    Idempotent: if the file already contains the DAG_SECTION_MARKER, skip
    appending unless force=True, in which case the existing DAG section
    (from the marker to the end of the file) is replaced.
    """
    abs_path = file_path if os.path.isabs(file_path) else os.path.join(REPO_ROOT, file_path)

    if not os.path.exists(abs_path):
        # Create parent directories if needed
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(DAG_SECTION_MARKER + "\n" + content + "\n")
        print(f"Created and wrote DAG to {abs_path}")
        return

    with open(abs_path, "r", encoding="utf-8") as f:
        existing = f.read()

    if DAG_SECTION_MARKER in existing:
        if not force:
            print(
                f"DAG section already present in {abs_path}. "
                "Use --force to replace."
            )
            return
        # --force: replace existing DAG section (from marker to end of file)
        marker_pos = existing.index(DAG_SECTION_MARKER)
        # Keep everything before the marker (strip trailing whitespace)
        before = existing[:marker_pos].rstrip()
        new_content = before + "\n\n" + DAG_SECTION_MARKER + "\n" + content + "\n"
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Replaced DAG section in {abs_path}")
    else:
        with open(abs_path, "a", encoding="utf-8") as f:
            f.write("\n" + DAG_SECTION_MARKER + "\n" + content + "\n")
        print(f"Appended DAG to {abs_path}")


if __name__ == "__main__":
    main()
