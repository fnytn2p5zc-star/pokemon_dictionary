from __future__ import annotations

import logging
import threading
import time

from flask import current_app, request
from flask_socketio import SocketIO, emit, join_room, leave_room

from src.battle.models import BattleConfig
from src.battle.rules import parse_rules_from_data, validate_team
from src.battle.state import Room, create_team
from src.battle.engine import TurnBattleEngine
from src.battle.room_manager import RoomManager
from src.db.connection import create_connection
from src.db.queries import fetch_battle_stats, fetch_team_validation_data

logger = logging.getLogger(__name__)

room_manager = RoomManager()
_battle_engines: dict[str, TurnBattleEngine] = {}
_switch_events: dict[str, threading.Event] = {}
_chat_rate: dict[str, float] = {}


def register_events(socketio: SocketIO) -> None:

    @socketio.on("connect")
    def on_connect():
        pass

    @socketio.on("disconnect")
    def on_disconnect():
        sid = request.sid
        room_before = room_manager.get_room_by_sid(sid)
        code_before = room_before.code if room_before else None

        room, empty = room_manager.leave_room(sid)

        if code_before:
            engine = _battle_engines.pop(code_before, None)
            if engine:
                engine.finished = True
            switch_evt = _switch_events.pop(code_before, None)
            if switch_evt:
                switch_evt.set()

        if room and not empty:
            socketio.emit("room_update", room.to_dict(), room=room.code)
        room_manager.remove_sid(sid)
        _chat_rate.pop(sid, None)

    @socketio.on("set_nickname")
    def on_set_nickname(data):
        sid = request.sid
        nickname = str(data.get("nickname", "")).strip()[:20]
        if not nickname:
            emit("error", {"message": "昵称不能为空"})
            return
        room_manager.set_nickname(sid, nickname)
        emit("nickname_set", {"success": True, "nickname": nickname})

    @socketio.on("create_room")
    def on_create_room(data=None):
        sid = request.sid
        rules_data = {}
        if isinstance(data, dict):
            rules_data = data.get("rules", {})
        rules = parse_rules_from_data(rules_data)
        room = room_manager.create_room(sid, rules=rules)
        if room is None:
            emit("error", {"message": "无法创建房间，请先设置昵称"})
            return
        join_room(room.code)
        emit("room_created", {"room_code": room.code})
        emit("room_update", room.to_dict(), room=room.code)

    @socketio.on("join_room")
    def on_join_room(data):
        sid = request.sid
        code = str(data.get("room_code", "")).strip()
        room, error = room_manager.join_room(sid, code)
        if room is None:
            emit("room_joined", {"success": False, "error": error})
            return
        join_room(room.code)
        emit("room_joined", {"success": True})
        socketio.emit("room_update", room.to_dict(), room=room.code)

    @socketio.on("set_team")
    def on_set_team(data):
        sid = request.sid
        room = room_manager.get_room_by_sid(sid)
        if room is None:
            emit("error", {"message": "你不在任何房间中"})
            return

        raw_ids = data.get("pokemon_ids", [])
        if not isinstance(raw_ids, list):
            emit("error", {"message": "无效的队伍数据"})
            return

        config = BattleConfig()
        try:
            pokemon_ids = [int(pid) for pid in raw_ids[:config.team_max]]
        except (ValueError, TypeError):
            emit("error", {"message": "无效的宝可梦 ID"})
            return

        if any(pid <= 0 or pid > 1025 for pid in pokemon_ids):
            emit("error", {"message": "无效的宝可梦 ID"})
            return

        if len(pokemon_ids) < config.team_min:
            emit("error", {"message": f"至少选择 {config.team_min} 只宝可梦"})
            return

        # Validate against room rules
        db_path = current_app.config["DB_PATH"]
        conn = create_connection(db_path)
        try:
            team_data = fetch_team_validation_data(conn, pokemon_ids)
        finally:
            conn.close()

        if len(team_data) != len(pokemon_ids):
            emit("error", {"message": "部分宝可梦 ID 无效"})
            return

        errors = validate_team(room.rules, team_data)
        if errors:
            emit("team_invalid", {"errors": errors})
            return

        player = room.get_player(sid)
        if player is None:
            return
        player.team_ids = pokemon_ids
        player.ready = False
        socketio.emit("room_update", room.to_dict(), room=room.code)

    @socketio.on("toggle_ready")
    def on_toggle_ready(_data=None):
        sid = request.sid
        room = room_manager.get_room_by_sid(sid)
        if room is None:
            return

        player = room.get_player(sid)
        if player is None:
            return
        if not player.team_ids:
            emit("error", {"message": "请先选择宝可梦队伍"})
            return

        player.ready = not player.ready
        socketio.emit("room_update", room.to_dict(), room=room.code)

        if room.all_ready:
            _start_battle(socketio, room)

    @socketio.on("leave_room")
    def on_leave_room(_data=None):
        sid = request.sid
        r = room_manager.get_room_by_sid(sid)
        code_before = r.code if r else None

        room, empty = room_manager.leave_room(sid)
        if code_before:
            leave_room(code_before)
            engine = _battle_engines.pop(code_before, None)
            if engine:
                engine.finished = True
            switch_evt = _switch_events.pop(code_before, None)
            if switch_evt:
                switch_evt.set()
        if room and not empty:
            socketio.emit("room_update", room.to_dict(), room=room.code)
        emit("left_room", {"success": True})

    @socketio.on("send_chat")
    def on_send_chat(data):
        sid = request.sid
        if not isinstance(data, dict):
            return
        room = room_manager.get_room_by_sid(sid)
        if room is None:
            return
        now = time.monotonic()
        if now - _chat_rate.get(sid, 0) < 1.0:
            return
        _chat_rate[sid] = now
        nickname = room_manager.get_nickname(sid) or "???"
        message = str(data.get("message", "")).strip()[:100]
        if not message:
            return
        socketio.emit("chat_message", {
            "nickname": nickname,
            "message": message,
        }, room=room.code)

    @socketio.on("select_pokemon")
    def on_select_pokemon(data):
        sid = request.sid
        room = room_manager.get_room_by_sid(sid)
        if room is None:
            return

        engine = _battle_engines.get(room.code)
        if engine is None or engine.state != "waiting_switch":
            return

        player = room.get_player(sid)
        if player is None:
            return

        team_num = room.players.index(player) + 1
        if engine.waiting_switch_team != team_num:
            return

        index = data.get("pokemon_index")
        if not isinstance(index, int):
            return

        new_active = engine.switch_pokemon(team_num, index)
        if new_active is None:
            emit("error", {"message": "无法选择该宝可梦"})
            return

        socketio.emit("pokemon_switched", {
            "team": team_num,
            "pokemon": new_active.to_dict(),
        }, room=room.code)

        switch_evt = _switch_events.get(room.code)
        if switch_evt:
            switch_evt.set()


def _start_battle(socketio: SocketIO, room: Room) -> None:
    config = BattleConfig()
    room.status = "battling"

    db_path = current_app.config["DB_PATH"]
    conn = create_connection(db_path)

    try:
        p1 = room.players[0]
        p2 = room.players[1]

        stats1 = fetch_battle_stats(conn, p1.team_ids)
        stats2 = fetch_battle_stats(conn, p2.team_ids)
    finally:
        conn.close()

    if not stats1 or not stats2:
        room.status = "waiting"
        for p in room.players:
            p.ready = False
        socketio.emit(
            "error", {"message": "队伍数据无效，请重新选择"}, room=room.code,
        )
        socketio.emit("room_update", room.to_dict(), room=room.code)
        return

    team1 = create_team(stats1, 1)
    team2 = create_team(stats2, 2)

    engine = TurnBattleEngine(team1, team2, config)
    _battle_engines[room.code] = engine

    socketio.emit("battle_start", {
        "your_team_num": 1,
        "your_team": engine.get_team_summary(1),
        "enemy_active": engine.get_active(2).to_dict(),
        "enemy_team_count": len(team2),
        "player1": p1.nickname,
        "player2": p2.nickname,
    }, room=p1.sid)

    socketio.emit("battle_start", {
        "your_team_num": 2,
        "your_team": engine.get_team_summary(2),
        "enemy_active": engine.get_active(1).to_dict(),
        "enemy_team_count": len(team1),
        "player1": p1.nickname,
        "player2": p2.nickname,
    }, room=p2.sid)

    socketio.start_background_task(_run_turn_loop, socketio, room, engine, config)


def _run_turn_loop(
    socketio: SocketIO,
    room: Room,
    engine: TurnBattleEngine,
    config: BattleConfig,
) -> None:
    try:
        socketio.sleep(1.5)

        while not engine.finished:
            events = engine.execute_turn()
            room.turn = engine.turn

            event_dicts = [e.to_dict() for e in events]
            socketio.emit("turn_result", {
                "turn": engine.turn,
                "events": event_dicts,
            }, room=room.code)

            if engine.state == "waiting_switch":
                fainted_team = engine.waiting_switch_team
                fainted_player = room.players[fainted_team - 1]
                remaining = [
                    p.to_dict() for p in engine.get_alive(fainted_team)
                ]

                if len(remaining) == 1:
                    socketio.sleep(2)  # wait for faint animation to finish
                    new_active = engine.switch_pokemon(
                        fainted_team, remaining[0]["index"]
                    )
                    if new_active:
                        socketio.emit("pokemon_switched", {
                            "team": fainted_team,
                            "pokemon": new_active.to_dict(),
                        }, room=room.code)
                else:
                    socketio.emit("request_switch", {
                        "reason": "fainted",
                        "remaining": remaining,
                    }, room=fainted_player.sid)

                    switch_evt = threading.Event()
                    _switch_events[room.code] = switch_evt

                    switch_evt.wait(timeout=config.switch_timeout)
                    _switch_events.pop(room.code, None)

                    if engine.state == "waiting_switch":
                        new_active = engine.auto_switch(fainted_team)
                        if new_active:
                            socketio.emit("pokemon_switched", {
                                "team": fainted_team,
                                "pokemon": new_active.to_dict(),
                            }, room=room.code)

                if engine.finished:
                    break

                socketio.sleep(1.5)
            else:
                socketio.sleep(config.turn_delay)

        winner_team = engine.winner_team
        winner_name = ""
        if winner_team == 1 and len(room.players) > 0:
            winner_name = room.players[0].nickname
        elif winner_team == 2 and len(room.players) > 1:
            winner_name = room.players[1].nickname

        socketio.emit("battle_end", {
            "winner_name": winner_name,
            "winner_team": winner_team,
            "total_turns": engine.turn,
        }, room=room.code)
    except Exception:
        logger.exception("Battle loop crashed for room %s", room.code)
        socketio.emit("error", {"message": "对战发生错误"}, room=room.code)
    finally:
        room.status = "finished"
        _battle_engines.pop(room.code, None)
        _switch_events.pop(room.code, None)
