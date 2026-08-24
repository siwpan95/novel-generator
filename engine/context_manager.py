"""上下文状态管理器（ASP 增强）。

为 ASP 生成管线提供全局上下文感知：
- 人物状态追踪（情绪、位置、关系距离）
- 世界状态变量（天气、时间、地点索引）
- 叙事弧线跟踪（当前处于故事弧线的哪一段）
- 上下文传播（前文状态自动影响后文）
- 事件记忆（已发生事件的简史，供后文引用）

设计原则：
- 轻量级：纯字典存储，不引入复杂数据结构
- 可序列化：所有状态可 JSON 序列化，支持断点续写
- 无侵入：独立模块，不影响已有 ASP 管线
"""

import json
from typing import Any, Optional
from pathlib import Path


class ContextManager:
    """全局上下文管理器：追踪叙事状态，为模板提供上下文感知。"""

    def __init__(self):
        # 人物状态 {char_name: {"mood": str, "location": str, "hp": int, ...}}
        self._characters: dict[str, dict] = {}
        # 世界状态
        self._world: dict[str, Any] = {
            "time_of_day": "清晨",
            "weather": "晴",
            "location": "未知",
            "scene_id": 0,
        }
        # 叙事弧线
        self._arc: dict[str, Any] = {
            "part": 0,          # 部编号
            "volume": 0,        # 卷编号
            "chapter": 0,       # 章编号
            "phase": "opening", # 阶段：opening/build/climax/ending
            "tension": 0.3,     # 当前紧张度 0-1
        }
        # 事件简史 [(event_type, summary, chapter), ...]
        self._event_log: list[tuple] = []
        # 章节级记忆 {chapter_id: {"key_events": [...], "characters_present": [...]}}
        self._chapter_memory: dict[int, dict] = {}
        # 关系图 {char_a: {char_b: relation_strength}}
        self._relationships: dict[str, dict[str, float]] = {}

    # ───── 世界状态 ─────

    def set_world(self, key: str, value: Any):
        """设置世界状态变量。"""
        self._world[key] = value

    def get_world(self, key: str, default: Any = None) -> Any:
        """获取世界状态变量。"""
        return self._world.get(key, default)

    def advance_time(self, delta_hours: float = 1.0):
        """推进游戏内时间（简化实现）。"""
        phases = ["清晨", "上午", "正午", "下午", "傍晚", "夜晚", "深夜"]
        current = self._world.get("time_of_day", "清晨")
        idx = phases.index(current) if current in phases else 0
        new_idx = (idx + int(delta_hours / 2)) % len(phases)
        self._world["time_of_day"] = phases[new_idx]

    def advance_scene(self):
        """推进场景编号。"""
        self._world["scene_id"] = self._world.get("scene_id", 0) + 1

    # ───── 人物状态 ─────

    def register_character(self, name: str, **attrs):
        """注册或更新人物。"""
        if name not in self._characters:
            self._characters[name] = {}
        self._characters[name].update(attrs)

    def get_character(self, name: str) -> dict:
        """获取人物状态。"""
        return self._characters.get(name, {})

    def set_character_attr(self, name: str, key: str, value: Any):
        """设置单个人物属性。"""
        if name not in self._characters:
            self._characters[name] = {}
        self._characters[name][key] = value

    def get_character_attr(self, name: str, key: str, default: Any = None) -> Any:
        """获取单个人物属性。"""
        char = self._characters.get(name, {})
        return char.get(key, default)

    def list_characters(self) -> list[str]:
        """列出所有已注册人物。"""
        return list(self._characters.keys())

    def characters_in_location(self, location: str) -> list[str]:
        """列出指定位置的所有人物。"""
        return [name for name, attrs in self._characters.items()
                if attrs.get("location") == location]

    # ───── 关系系统 ─────

    def set_relationship(self, char_a: str, char_b: str, strength: float):
        """设置两个人物之间的关系强度 (0=陌生, 1=极度亲密)。"""
        if char_a not in self._relationships:
            self._relationships[char_a] = {}
        if char_b not in self._relationships:
            self._relationships[char_b] = {}
        self._relationships[char_a][char_b] = strength
        self._relationships[char_b][char_a] = strength

    def get_relationship(self, char_a: str, char_b: str) -> float:
        """获取两个人物之间的关系强度。"""
        if char_a in self._relationships:
            return self._relationships[char_a].get(char_b, 0.0)
        return 0.0

    def relation_label(self, strength: float) -> str:
        """将关系强度转为中文标签。"""
        if strength >= 0.9:
            return "生死之交"
        if strength >= 0.7:
            return "挚友"
        if strength >= 0.5:
            return "朋友"
        if strength >= 0.3:
            return "认识"
        if strength >= 0.1:
            return "点头之交"
        return "陌生人"

    # ───── 叙事弧线 ─────

    def set_chapter(self, part: int, volume: int, chapter: int):
        """设置当前叙事位置。"""
        self._arc["part"] = part
        self._arc["volume"] = volume
        self._arc["chapter"] = chapter
        # 自动推演阶段
        total_chapters = 30  # 假设每卷30章
        ch_in_vol = chapter % total_chapters
        if ch_in_vol < 5:
            self._arc["phase"] = "opening"
        elif ch_in_vol < 15:
            self._arc["phase"] = "build"
        elif ch_in_vol < 22:
            self._arc["phase"] = "climax"
        else:
            self._arc["phase"] = "ending"
        self._arc["tension"] = min(1.0, 0.2 + 0.8 * (ch_in_vol / total_chapters))

    def get_arc(self) -> dict:
        """获取叙事弧线状态。"""
        return dict(self._arc)

    def current_tension(self) -> float:
        """获取当前紧张度。"""
        return self._arc.get("tension", 0.3)

    def current_phase(self) -> str:
        """获取当前叙事阶段。"""
        return self._arc.get("phase", "opening")

    # ───── 事件日志 ─────

    def log_event(self, event_type: str, summary: str,
                  chapter: Optional[int] = None):
        """记录一个事件。"""
        ch = chapter or self._arc.get("chapter", 0)
        self._event_log.append((event_type, summary, ch))

    def recent_events(self, n: int = 10) -> list[tuple]:
        """获取最近n个事件。"""
        return self._event_log[-n:]

    def events_in_chapter(self, chapter: int) -> list[tuple]:
        """获取指定章的事件。"""
        return [e for e in self._event_log if e[2] == chapter]

    def summary_for_template(self) -> str:
        """生成供模板使用的叙事上下文摘要文本。"""
        chars = self.list_characters()
        main_chars = chars[:3] if chars else ["无"]
        recent = self.recent_events(3)
        events_text = "；".join(
            f"[{e[0]}] {e[1]}" for e in recent
        ) if recent else "暂无重大事件"

        lines = [
            f"时间：{self._world.get('time_of_day', '—')}",
            f"天气：{self._world.get('weather', '—')}",
            f"地点：{self._world.get('location', '—')}",
            f"主要人物：{'、'.join(main_chars)}",
            f"叙事阶段：{self._arc.get('phase', '—')}",
            f"紧张度：{self._arc.get('tension', 0):.2f}",
            f"近期事件：{events_text}",
        ]
        return "\n".join(lines)

    # ───── 序列化 ─────

    def to_dict(self) -> dict:
        """导出为可 JSON 序列化的字典。"""
        return {
            "characters": self._characters,
            "world": self._world,
            "arc": self._arc,
            "event_log": [list(e) for e in self._event_log],
            "chapter_memory": self._chapter_memory,
            "relationships": self._relationships,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ContextManager":
        """从字典恢复。"""
        ctx = cls()
        ctx._characters = data.get("characters", {})
        ctx._world = data.get("world", {})
        ctx._arc = data.get("arc", {})
        ctx._event_log = [tuple(e) for e in data.get("event_log", [])]
        ctx._chapter_memory = data.get("chapter_memory", {})
        ctx._relationships = data.get("relationships", {})
        return ctx

    def save(self, filepath: str):
        """保存上下文到文件。"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, filepath: str) -> "ContextManager":
        """从文件加载上下文。"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
