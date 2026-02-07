import argparse
import math

from src.config import Config
from src.db.connection import create_connection
from src.db.queries import (
    fetch_pokemon_detail,
    fetch_pokemon_page,
    filter_pokemon,
    get_total_count,
    search_pokemon,
)
from src.cli.display import format_pokemon_detail, format_pokemon_table


def _open_conn():
    return create_connection(Config().db_path)


def _show_detail(conn, id_or_name: str) -> None:
    row, abilities = fetch_pokemon_detail(conn, id_or_name)
    if row is None:
        print(f"  未找到宝可梦: {id_or_name}")
        return
    print(format_pokemon_detail(row, abilities))


def cmd_browse(args: argparse.Namespace) -> None:
    page_size = args.page_size
    conn = _open_conn()
    try:
        total = get_total_count(conn)
        total_pages = math.ceil(total / page_size)
        current_page = 1

        while True:
            offset = (current_page - 1) * page_size
            rows = fetch_pokemon_page(conn, offset=offset, limit=page_size)
            page_info = f"第 {current_page}/{total_pages} 页 (共 {total} 只)"
            print(format_pokemon_table(rows, page_info=page_info))
            print()

            try:
                choice = input(
                    "  [n]下一页 [p]上一页 [q]退出 [数字]查看详情: "
                ).strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if choice == "q":
                break
            elif choice == "n":
                if current_page < total_pages:
                    current_page += 1
            elif choice == "p":
                if current_page > 1:
                    current_page -= 1
            elif choice.isdigit():
                _show_detail(conn, choice)
                print()
            else:
                print("  无效输入，请重试")
    finally:
        conn.close()


def cmd_search(args: argparse.Namespace) -> None:
    conn = _open_conn()
    try:
        rows = search_pokemon(conn, args.name)
        print(format_pokemon_table(rows))
    finally:
        conn.close()


def cmd_info(args: argparse.Namespace) -> None:
    conn = _open_conn()
    try:
        _show_detail(conn, args.id_or_name)
    finally:
        conn.close()


def cmd_filter(args: argparse.Namespace) -> None:
    conn = _open_conn()
    try:
        rows = filter_pokemon(
            conn,
            type_name=args.type_name,
            gen=args.gen,
            min_total=args.min_total,
            sort_by=args.sort,
            limit=args.limit,
        )
        print(format_pokemon_table(rows))
    finally:
        conn.close()
