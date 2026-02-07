import argparse
import asyncio
import signal
import sys
from pathlib import Path

from src.config import Config
from src.db.connection import create_connection
from src.db.repository import get_scrape_status
from src.export.csv_export import export_csv
from src.export.json_export import export_json
from src.scraper.pokemon_scraper import PokemonScraper
from src.scraper.ability_scraper import run_ability_scraper
from src.cli.viewer import cmd_browse, cmd_search, cmd_info, cmd_filter
from src.chatbot.chat_session import run_chat


def cmd_scrape(args: argparse.Namespace) -> None:
    config = Config(
        requests_per_second=args.rate,
    )
    config.ensure_dirs()
    conn = create_connection(config.db_path)

    scraper = PokemonScraper(config, conn)

    def handle_interrupt(_signum: int, _frame: object) -> None:
        print("\nGracefully stopping... (progress saved)")
        scraper.request_stop()

    signal.signal(signal.SIGINT, handle_interrupt)

    try:
        asyncio.run(scraper.run(
            start=args.start,
            end=args.end,
            skip_images=args.skip_images,
        ))
    finally:
        conn.close()


def cmd_status(_args: argparse.Namespace) -> None:
    config = Config()
    if not config.db_path.exists():
        print("No database found. Run 'scrape' first.")
        return

    conn = create_connection(config.db_path)
    try:
        status = get_scrape_status(conn)
        print(f"Pokemon in DB:      {status['total_pokemon']}")
        print(f"Data scraped:       {status['data_scraped']}")
        print(f"Images downloaded:  {status['images_downloaded']}")

        artwork_count = len(list(config.artwork_dir.glob("*.png"))) if config.artwork_dir.exists() else 0
        sprite_count = len(list(config.sprite_dir.glob("*.png"))) if config.sprite_dir.exists() else 0
        print(f"Artwork files:      {artwork_count}")
        print(f"Sprite files:       {sprite_count}")
    finally:
        conn.close()


def cmd_export_json(args: argparse.Namespace) -> None:
    config = Config()
    if not config.db_path.exists():
        print("No database found. Run 'scrape' first.")
        return

    conn = create_connection(config.db_path)
    try:
        output = Path(args.output)
        export_json(conn, output)
    finally:
        conn.close()


def cmd_export_csv(args: argparse.Namespace) -> None:
    config = Config()
    if not config.db_path.exists():
        print("No database found. Run 'scrape' first.")
        return

    conn = create_connection(config.db_path)
    try:
        output = Path(args.output)
        export_csv(conn, output)
    finally:
        conn.close()


def cmd_scrape_abilities(_args: argparse.Namespace) -> None:
    run_ability_scraper()


def cmd_web(args: argparse.Namespace) -> None:
    from src.web.app import create_app
    app = create_app()
    app.run(host=args.host, port=args.port, debug=args.debug)


def cmd_chat(_args: argparse.Namespace) -> None:
    run_chat()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pokemon Data Scraper - fetch from PokeAPI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    scrape_parser = subparsers.add_parser(
        "scrape", help="Scrape Pokemon data from PokeAPI",
    )
    scrape_parser.add_argument(
        "--start", type=int, default=1,
        help="Starting Pokemon ID (default: 1)",
    )
    scrape_parser.add_argument(
        "--end", type=int, default=None,
        help="Ending Pokemon ID (default: 1025)",
    )
    scrape_parser.add_argument(
        "--skip-images", action="store_true",
        help="Skip image downloads",
    )
    scrape_parser.add_argument(
        "--rate", type=float, default=2.0,
        help="Requests per second (default: 2.0)",
    )
    scrape_parser.set_defaults(func=cmd_scrape)

    status_parser = subparsers.add_parser(
        "status", help="Show scraping progress",
    )
    status_parser.set_defaults(func=cmd_status)

    json_parser = subparsers.add_parser(
        "export-json", help="Export data to JSON",
    )
    json_parser.add_argument(
        "--output", default="data/pokemon.json",
        help="Output file path (default: data/pokemon.json)",
    )
    json_parser.set_defaults(func=cmd_export_json)

    csv_parser = subparsers.add_parser(
        "export-csv", help="Export data to CSV",
    )
    csv_parser.add_argument(
        "--output", default="data/pokemon.csv",
        help="Output file path (default: data/pokemon.csv)",
    )
    csv_parser.set_defaults(func=cmd_export_csv)

    browse_parser = subparsers.add_parser(
        "browse", help="Browse Pokemon interactively",
    )
    browse_parser.add_argument(
        "--page-size", type=int, default=20,
        help="Number of Pokemon per page (default: 20)",
    )
    browse_parser.set_defaults(func=cmd_browse)

    search_parser = subparsers.add_parser(
        "search", help="Search Pokemon by name",
    )
    search_parser.add_argument(
        "name", help="Pokemon name (Chinese/English/Japanese)",
    )
    search_parser.set_defaults(func=cmd_search)

    info_parser = subparsers.add_parser(
        "info", help="Show Pokemon detail info",
    )
    info_parser.add_argument(
        "id_or_name", help="Pokemon ID or name",
    )
    info_parser.set_defaults(func=cmd_info)

    filter_parser = subparsers.add_parser(
        "filter", help="Filter Pokemon by type/gen/stats",
    )
    filter_parser.add_argument("--type", dest="type_name")
    filter_parser.add_argument("--gen", type=int)
    filter_parser.add_argument(
        "--sort", default="id",
        choices=["id", "total", "hp", "attack", "defense",
                 "sp_attack", "sp_defense", "speed"],
    )
    filter_parser.add_argument("--min-total", type=int)
    filter_parser.add_argument("--limit", type=int, default=20)
    filter_parser.set_defaults(func=cmd_filter)

    abilities_parser = subparsers.add_parser(
        "scrape-abilities", help="Scrape ability flavor text from PokeAPI",
    )
    abilities_parser.set_defaults(func=cmd_scrape_abilities)

    web_parser = subparsers.add_parser(
        "web", help="Start web-based Pokedex interface",
    )
    web_parser.add_argument("--host", default="127.0.0.1")
    web_parser.add_argument("--port", type=int, default=5000)
    web_parser.add_argument("--debug", action="store_true")
    web_parser.set_defaults(func=cmd_web)

    chat_parser = subparsers.add_parser(
        "chat", help="Pokemon Q&A chatbot",
    )
    chat_parser.set_defaults(func=cmd_chat)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
