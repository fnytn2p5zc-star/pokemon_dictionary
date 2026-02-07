import sqlite3

from flask import Blueprint, render_template, request, abort

from src.db.queries import (
    get_total_count,
    fetch_pokemon_page,
    search_pokemon,
    fetch_pokemon_detail,
    filter_pokemon,
    fetch_all_types,
)
from src.web.helpers import Pagination

bp = Blueprint("main", __name__)


def _get_db() -> sqlite3.Connection:
    from flask import g
    return g.db


@bp.route("/")
def index():
    conn = _get_db()
    page = request.args.get("page", 1, type=int)
    page = max(1, page)
    per_page = 24
    total = get_total_count(conn)
    pagination = Pagination(page=page, per_page=per_page, total=total)
    pokemon_list = fetch_pokemon_page(conn, offset=pagination.offset, limit=per_page)
    return render_template(
        "index.html",
        pokemon_list=pokemon_list,
        pagination=pagination,
        title="Pokemon 图鉴",
    )


@bp.route("/pokemon/<id_or_name>")
def detail(id_or_name: str):
    conn = _get_db()
    pokemon, abilities = fetch_pokemon_detail(conn, id_or_name)
    if pokemon is None:
        abort(404)
    return render_template(
        "detail.html",
        p=pokemon,
        abilities=abilities,
        title=f"{pokemon['name_zh_hans']} - Pokemon 图鉴",
    )


@bp.route("/search")
def search():
    conn = _get_db()
    q = request.args.get("q", "").strip()
    if not q:
        return render_template(
            "index.html",
            pokemon_list=[],
            pagination=None,
            title="搜索结果",
            search_query=q,
        )
    results = search_pokemon(conn, q)
    return render_template(
        "index.html",
        pokemon_list=results,
        pagination=None,
        title=f"搜索: {q}",
        search_query=q,
    )


@bp.route("/filter")
def filter_view():
    conn = _get_db()
    type_name = request.args.get("type", None)
    gen = request.args.get("gen", None, type=int)
    sort_by = request.args.get("sort", "id")
    min_total = request.args.get("min_total", None, type=int)

    all_types = fetch_all_types(conn)
    results = filter_pokemon(
        conn,
        type_name=type_name if type_name else None,
        gen=gen,
        min_total=min_total,
        sort_by=sort_by,
        limit=200,
    )
    return render_template(
        "index.html",
        pokemon_list=results,
        pagination=None,
        title="筛选结果",
        all_types=all_types,
        filter_type=type_name or "",
        filter_gen=gen or "",
        filter_sort=sort_by,
        filter_min_total=min_total or "",
    )
