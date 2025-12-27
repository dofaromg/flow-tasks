import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
import uuid
from typing import Dict, Any

from flask import Flask, abort, jsonify, redirect, render_template_string, request, url_for

DATA_ROOT = Path(".flowcore")


# ---------------------------
# Persistence Helpers
# ---------------------------

def _ensure_data_root() -> None:
    DATA_ROOT.mkdir(exist_ok=True)


def _project_dir(name: str) -> Path:
    return DATA_ROOT / name


def _project_file(name: str) -> Path:
    return _project_dir(name) / "project.json"


def _sessions_file(name: str) -> Path:
    return _project_dir(name) / "sessions.json"


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _iso_now() -> str:
    return datetime.now(UTC).isoformat()


# ---------------------------
# Command Implementations
# ---------------------------

def project_init(args: argparse.Namespace) -> None:
    _ensure_data_root()
    proj_dir = _project_dir(args.project)
    proj_dir.mkdir(parents=True, exist_ok=True)

    meta_path = _project_file(args.project)
    metadata: Dict[str, Any] = _read_json(meta_path, {})
    metadata.update({
        "name": args.project,
        "title": args.title,
        "updated_at": _iso_now(),
    })
    metadata.setdefault("created_at", metadata["updated_at"])
    _write_json(meta_path, metadata)

    sessions_path = _sessions_file(args.project)
    if not sessions_path.exists():
        _write_json(sessions_path, {})

    print(f"Project '{args.project}' initialized at {proj_dir.resolve()}")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


def session_new(args: argparse.Namespace) -> None:
    proj_path = _project_file(args.project)
    if not proj_path.exists():
        raise SystemExit(f"Project '{args.project}' not found. Please run project-init first.")

    sessions = _read_json(_sessions_file(args.project), {})
    session_id = uuid.uuid4().hex
    sessions[session_id] = {
        "title": args.title,
        "created_at": _iso_now(),
        "messages": [],
    }
    _write_json(_sessions_file(args.project), sessions)

    print(f"Session created: {session_id}")


def session_send(args: argparse.Namespace) -> None:
    proj_path = _project_file(args.project)
    if not proj_path.exists():
        raise SystemExit(f"Project '{args.project}' not found. Please run project-init first.")

    sessions = _read_json(_sessions_file(args.project), {})
    session = sessions.get(args.session_id)
    if session is None:
        raise SystemExit(f"Session '{args.session_id}' not found for project '{args.project}'.")

    message = {
        "persona": args.persona,
        "intent": args.intent,
        "text": args.text,
        "timestamp": _iso_now(),
    }
    session.setdefault("messages", []).append(message)
    sessions[args.session_id] = session
    _write_json(_sessions_file(args.project), sessions)

    print("Message stored:")
    print(json.dumps(message, ensure_ascii=False, indent=2))


# ---------------------------
# Web UI
# ---------------------------

def build_app() -> Flask:
    app = Flask(__name__)

    def load_project(name: str):
        proj_path = _project_file(name)
        if not proj_path.exists():
            abort(404, f"Project '{name}' not found")
        metadata = _read_json(proj_path, {})
        sessions = _read_json(_sessions_file(name), {})
        return metadata, sessions

    @app.route("/")
    def index():
        projects = []
        if DATA_ROOT.exists():
            for path in sorted(DATA_ROOT.iterdir()):
                if path.is_dir() and _project_file(path.name).exists():
                    meta = _read_json(_project_file(path.name), {})
                    projects.append(meta)
        return render_template_string(
            """
            <h1>FlowCore Projects</h1>
            {% if projects %}
              <ul>
              {% for project in projects %}
                <li><a href="{{ url_for('project_detail', project=project['name']) }}">{{ project['title'] or project['name'] }}</a></li>
              {% endfor %}
              </ul>
            {% else %}
              <p>No projects found. Initialize one via CLI.</p>
            {% endif %}
            """,
            projects=projects,
        )

    @app.route("/project/<project>")
    def project_detail(project: str):
        metadata, sessions = load_project(project)
        return render_template_string(
            """
            <h1>{{ metadata['title'] or metadata['name'] }}</h1>
            <p>Project ID: {{ metadata['name'] }}</p>
            <p>Updated: {{ metadata.get('updated_at', '-') }}</p>
            <h2>Sessions</h2>
            {% if sessions %}
              <ul>
              {% for sid, session in sessions.items() %}
                <li><a href="{{ url_for('session_detail', project=metadata['name'], session_id=sid) }}">{{ session.get('title', sid) }}</a></li>
              {% endfor %}
              </ul>
            {% else %}
              <p>No sessions yet.</p>
            {% endif %}
            <p><a href="{{ url_for('index') }}">Back</a></p>
            """,
            metadata=metadata,
            sessions=sessions,
        )

    @app.route("/project/<project>/session/<session_id>")
    def session_detail(project: str, session_id: str):
        metadata, sessions = load_project(project)
        session = sessions.get(session_id)
        if not session:
            abort(404, "Session not found")
        return render_template_string(
            """
            <h1>{{ session.get('title', session_id) }}</h1>
            <p>Session ID: {{ session_id }}</p>
            <p>Project: <a href="{{ url_for('project_detail', project=metadata['name']) }}">{{ metadata['title'] or metadata['name'] }}</a></p>
            <h2>Messages</h2>
            {% if session.get('messages') %}
              <ul>
              {% for msg in session['messages'] %}
                <li>
                  <strong>{{ msg['persona'] }}</strong> ({{ msg['intent'] }}) at {{ msg['timestamp'] }}:<br/>
                  {{ msg['text'] }}
                </li>
              {% endfor %}
              </ul>
            {% else %}
              <p>No messages recorded.</p>
            {% endif %}
            <p><a href="{{ url_for('project_detail', project=metadata['name']) }}">Back to project</a></p>
            """,
            metadata=metadata,
            session_id=session_id,
            session=session,
        )

    @app.route("/api/projects")
    def api_projects():
        projects = []
        if DATA_ROOT.exists():
            for path in DATA_ROOT.iterdir():
                if path.is_dir() and _project_file(path.name).exists():
                    meta = _read_json(_project_file(path.name), {})
                    projects.append(meta)
        return jsonify(projects)

    @app.route("/api/project/<project>/sessions")
    def api_sessions(project: str):
        _, sessions = load_project(project)
        return jsonify(sessions)

    @app.route("/api/project/<project>/session/<session_id>/messages")
    def api_messages(project: str, session_id: str):
        _, sessions = load_project(project)
        session = sessions.get(session_id)
        if not session:
            abort(404, "Session not found")
        return jsonify(session.get("messages", []))

    @app.route("/api/project/<project>/session/<session_id>/send", methods=["POST"])
    def api_send(project: str, session_id: str):
        text = request.form.get("text") or request.json.get("text") if request.is_json else None
        persona = request.form.get("persona") or (request.json or {}).get("persona") if request.is_json else None
        intent = request.form.get("intent") or (request.json or {}).get("intent") if request.is_json else None
        if not text:
            abort(400, "text is required")
        send_args = argparse.Namespace(
            project=project,
            session_id=session_id,
            persona=persona or "web",
            intent=intent or "chat",
            text=text,
        )
        session_send(send_args)
        return jsonify({"status": "ok"})

    @app.route("/api/redirect")
    def api_redirect():
        project = request.args.get("project")
        if not project:
            return redirect(url_for("index"))
        session_id = request.args.get("session")
        if session_id:
            return redirect(url_for("session_detail", project=project, session_id=session_id))
        return redirect(url_for("project_detail", project=project))

    return app


def run_web(args: argparse.Namespace) -> None:
    app = build_app()
    host = "127.0.0.1" if args.debug else "0.0.0.0"
    app.run(host=host, port=args.port, debug=args.debug)


# ---------------------------
# CLI Wiring
# ---------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="FlowCore loop CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("project-init", help="Initialize a project")
    init_parser.add_argument("project", help="Project name")
    init_parser.add_argument("--title", default="", help="Project title")
    init_parser.set_defaults(func=project_init)

    session_parser = subparsers.add_parser("session-new", help="Create a new session")
    session_parser.add_argument("project", help="Project name")
    session_parser.add_argument("--title", default="", help="Session title")
    session_parser.set_defaults(func=session_new)

    send_parser = subparsers.add_parser("session-send", help="Send a message to a session")
    send_parser.add_argument("project", help="Project name")
    send_parser.add_argument("session_id", help="Session identifier")
    send_parser.add_argument("--persona", default="user", help="Persona sending the message")
    send_parser.add_argument("--intent", default="chat", help="Intent of the message")
    send_parser.add_argument("--text", required=True, help="Message text")
    send_parser.set_defaults(func=session_send)

    web_parser = subparsers.add_parser("web", help="Launch the minimal web UI")
    web_parser.add_argument("project", help="Project name")
    web_parser.add_argument("--port", type=int, default=8787, help="Port to bind")
    web_parser.add_argument("--debug", action="store_true", help="Enable Flask debug mode")
    web_parser.set_defaults(func=run_web)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
