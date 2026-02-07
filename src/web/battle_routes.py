import sqlite3

from flask import Blueprint, render_template, jsonify, request

from src.db.queries import (
    fetch_pokemon_page,
    search_pokemon,
    get_total_count,
    filter_pokemon,
    fetch_all_types,
)

battle_bp = Blueprint(
    "battle",
    __name__,
    url_prefix="/battle",
)


def _get_db() -> sqlite3.Connection:
    from flask import g
    return g.db


@battle_bp.route("/")
def lobby():
    return render_template("battle/lobby.html", title="Pokemon 对战")


@battle_bp.route("/room")
def room_page():
    return render_template("battle/room.html", title="Pokemon 对战 - 房间")


@battle_bp.route("/arena")
def arena():
    return render_template("battle/arena.html", title="Pokemon 对战 - 竞技场")


@battle_bp.route("/api/pokemon")
def api_pokemon():
    conn = _get_db()
    q = request.args.get("q", "").strip()
    type_name = request.args.get("type", "").strip() or None
    gen = request.args.get("gen", type=int)
    sort_by = request.args.get("sort", "id").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 24

    if q:
        results = search_pokemon(conn, q)
        pokemon_list = [dict(row) for row in results]
        return jsonify({"pokemon": pokemon_list, "total": len(pokemon_list)})

    has_filters = type_name is not None or gen is not None or sort_by != "id"
    if has_filters:
        results = filter_pokemon(
            conn,
            type_name=type_name,
            gen=gen,
            sort_by=sort_by,
            limit=200,
        )
        pokemon_list = [dict(row) for row in results]
        return jsonify({"pokemon": pokemon_list, "total": len(pokemon_list)})

    total = get_total_count(conn)
    offset = (max(1, page) - 1) * per_page
    results = fetch_pokemon_page(conn, offset=offset, limit=per_page)
    pokemon_list = [dict(row) for row in results]
    return jsonify({
        "pokemon": pokemon_list,
        "total": total,
        "page": page,
        "per_page": per_page,
    })


@battle_bp.route("/api/types")
def api_types():
    conn = _get_db()
    rows = fetch_all_types(conn)
    return jsonify({"types": [dict(row) for row in rows]})
