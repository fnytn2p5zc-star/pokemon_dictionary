from src.config import Config
from src.db.connection import create_connection
from src.chatbot.query_parser import parse_query
from src.chatbot.query_handler import handle_query
from src.chatbot.response_formatter import format_response


def run_chat() -> None:
    conn = create_connection(Config().db_path)
    print("宝可梦问答机器人 — 输入问题，输入「退出」结束")
    try:
        while True:
            try:
                user_input = input("\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n再见！")
                break

            if not user_input:
                continue

            parsed = parse_query(user_input, conn)
            if parsed is None:
                print("再见！")
                break

            result = handle_query(parsed, conn)
            print(format_response(result))
    finally:
        conn.close()
