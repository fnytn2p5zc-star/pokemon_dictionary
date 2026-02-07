from pathlib import Path

from flask import Flask, g, send_from_directory

from src.config import Config
from src.db.connection import create_connection
from src.web.filters import register_filters
from src.web.routes import bp


def create_app() -> Flask:
    config = Config()
    template_dir = Path(__file__).parent / "templates"

    app = Flask(__name__, template_folder=str(template_dir))
    app.config["DB_PATH"] = config.db_path
    app.config["DATA_DIR"] = config.data_dir

    register_filters(app)
    app.register_blueprint(bp)

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
