from __future__ import annotations

from src.battle.state import Room, Player


class RoomManager:
    def __init__(self) -> None:
        self._rooms: dict[str, Room] = {}
        self._sid_to_room: dict[str, str] = {}
        self._sid_to_nickname: dict[str, str] = {}

    def set_nickname(self, sid: str, nickname: str) -> None:
        self._sid_to_nickname[sid] = nickname

    def get_nickname(self, sid: str) -> str | None:
        return self._sid_to_nickname.get(sid)

    def create_room(self, sid: str) -> Room | None:
        nickname = self._sid_to_nickname.get(sid)
        if nickname is None:
            return None
        if sid in self._sid_to_room:
            return None

        code = self._generate_unique_code()
        player = Player(sid=sid, nickname=nickname)
        room = Room(code=code, host=player)
        self._rooms[code] = room
        self._sid_to_room[sid] = code
        return room

    def join_room(self, sid: str, code: str) -> tuple[Room | None, str]:
        nickname = self._sid_to_nickname.get(sid)
        if nickname is None:
            return None, "请先设置昵称"
        if sid in self._sid_to_room:
            return None, "你已经在一个房间中"

        room = self._rooms.get(code)
        if room is None:
            return None, "房间不存在"
        if room.is_full:
            return None, "房间已满"
        if room.status != "waiting":
            return None, "对战已开始"

        player = Player(sid=sid, nickname=nickname)
        room.players.append(player)
        self._sid_to_room[sid] = code
        return room, ""

    def leave_room(self, sid: str) -> tuple[Room | None, bool]:
        code = self._sid_to_room.pop(sid, None)
        if code is None:
            return None, False

        room = self._rooms.get(code)
        if room is None:
            return None, False

        room.players = [p for p in room.players if p.sid != sid]
        empty = len(room.players) == 0
        if empty:
            self._rooms.pop(code, None)
        else:
            for p in room.players:
                p.ready = False
            room.status = "waiting"

        return room, empty

    def get_room_by_sid(self, sid: str) -> Room | None:
        code = self._sid_to_room.get(sid)
        if code is None:
            return None
        return self._rooms.get(code)

    def get_room(self, code: str) -> Room | None:
        return self._rooms.get(code)

    def remove_sid(self, sid: str) -> None:
        self._sid_to_nickname.pop(sid, None)
        self._sid_to_room.pop(sid, None)

    def _generate_unique_code(self) -> str:
        for _ in range(100):
            code = Room.generate_code()
            if code not in self._rooms:
                return code
        raise RuntimeError("无法生成唯一房间号")
