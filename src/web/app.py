import os
from pathlib import Path

from flask import Flask, g, send_from_directory
from flask_socketio import SocketIO

from src.config import Config
from src.db.connection import create_connection, ensure_evolution_data
from src.web.filters import register_filters
from src.web.routes import bp
from src.web.battle_routes import battle_bp

socketio = SocketIO()


def create_app() -> Flask:
    config = Config()
    template_dir = Path(__file__).parent / "templates"
    static_dir = Path(__file__).parent / "static"

    app = Flask(
        __name__,
        template_folder=str(template_dir),
        static_folder=str(static_dir),
    )
    app.config["DB_PATH"] = config.db_path
    app.config["DATA_DIR"] = config.data_dir
    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY", os.urandom(32).hex()
    )

    if config.db_path.exists():
        startup_conn = create_connection(config.db_path)
        try:
            ensure_evolution_data(startup_conn)
        finally:
            startup_conn.close()

    register_filters(app)
    app.register_blueprint(bp)
    app.register_blueprint(battle_bp)

    origins = os.environ.get("CORS_ORIGINS", "*")
    if origins == "*":
        allowed_origins = "*"
    else:
        allowed_origins = [o.strip() for o in origins.split(",") if o.strip()]
    socketio.init_app(app, cors_allowed_origins=allowed_origins)

    from src.web.socket_events import register_events
    register_events(socketio)

    @app.teardown_appcontext
    def close_db(_exc: BaseException | None) -> None:
        conn = g.pop("db", None)
        if conn is not None:
            conn.close()

    @app.route("/img/<path:filename>")
    def serve_image(filename: str):
        images_dir = config.data_dir.resolve() / "images"
        return send_from_directory(str(images_dir), filename)

    return app


@bp.before_request
def _inject_db() -> None:
    if "db" not in g:
        from flask import current_app
        g.db = create_connection(current_app.config["DB_PATH"])


@battle_bp.before_request
def _inject_db_battle() -> None:
    if "db" not in g:
        from flask import current_app
        g.db = create_connection(current_app.config["DB_PATH"])
