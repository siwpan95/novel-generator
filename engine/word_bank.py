"""词库加载与随机选取引擎（增强版）。

支持：
- JSON词库文件的加载和缓存
- 基于权重的随机选取
- 半随机名字生成（姓氏固定挑选 + 名字字符随机组合）
- 种子控制（可复现生成）
- ★ 权重修饰符（weighted pick by tag）
- ★ 分类过滤选取（category-filtered selection）
- ★ 回退链（fallback chains）
- ★ 词池暴露（pool 方法，供 Tracery 语法使用）
- ★ 重复避免（recent history tracking）
"""

import json
import random
import os
from pathlib import Path
from typing import Any, Optional

WORD_BANK_DIR = Path(__file__).parent.parent / "word_banks"


class WordBank:
    """词库管理器：加载、缓存、随机选取（增强版）。"""

    def __init__(self, seed: Optional[int] = None,
                 repetition_window: int = 8):
        self._cache: dict[str, dict] = {}
        self._rng = random.Random(seed)
        self._recent: dict[str, list[str]] = {}  # 最近使用记录
        self._repetition_window = repetition_window  # 避免重复的窗口大小

    # ───────────────── 基础加载 / 选取 ─────────────────

    def load(self, bank_name: str) -> dict:
        """加载指定词库JSON文件（带缓存）。"""
        if bank_name in self._cache:
            return self._cache[bank_name]

        filepath = WORD_BANK_DIR / f"{bank_name}.json"
        if not filepath.exists():
            raise FileNotFoundError(f"词库文件不存在: {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._cache[bank_name] = data
        return data

    def pick(self, bank_name: str, key: str) -> str:
        """从词库的指定key中随机挑选一项。"""
        data = self.load(bank_name)
        if key not in data:
            raise KeyError(f"词库'{bank_name}'中无键'{key}'")
        pool = data[key]
        return self._rng.choice(pool)

    def pick_n(self, bank_name: str, key: str, n: int,
               unique: bool = False) -> list[str]:
        """从词库中随机挑选n项。"""
        data = self.load(bank_name)
        pool = data[key]
        if unique and n > len(pool):
            n = len(pool)
        if unique:
            return self._rng.sample(pool, n)
        return [self._rng.choice(pool) for _ in range(n)]

    def pick_without(self, bank_name: str, key: str,
                     exclude: set[str]) -> str:
        """从词库中随机挑选，排除某些项。"""
        data = self.load(bank_name)
        pool = [item for item in data[key] if item not in exclude]
        if not pool:
            return self._rng.choice(data[key])  # fallback
        return self._rng.choice(pool)

    # ───────────────── ★ 增强：权重选取 ─────────────────

    def pick_weighted(self, bank_name: str, key: str,
                      weight_key: str = "weight") -> str:
        """按权重随机选取一项。
        
        如果词库条目是字典格式 {"text": "...", "weight": 3}，
        则按权重随机；如果条目是普通字符串，则回退到等权重随机。
        """
        data = self.load(bank_name)
        pool = data[key]

        # 检测是否带权重
        if pool and isinstance(pool[0], dict):
            texts = [item["text"] for item in pool]
            weights = [item.get(weight_key, 1) for item in pool]
            return self._rng.choices(texts, weights=weights, k=1)[0]
        # 回退到普通随机
        if isinstance(pool[0], str):
            return self._rng.choice(pool)
        return str(self._rng.choice(pool))

    def pick_weighted_without(self, bank_name: str, key: str,
                              exclude: set[str],
                              weight_key: str = "weight") -> str:
        """按权重随机选取，排除指定项。"""
        data = self.load(bank_name)
        pool = data[key]

        if pool and isinstance(pool[0], dict):
            # 过滤排除项
            filtered = [(item, item.get(weight_key, 1))
                        for item in pool
                        if item["text"] not in exclude]
            if not filtered:
                filtered = [(item, item.get(weight_key, 1))
                            for item in pool]
            texts = [f[0]["text"] for f in filtered]
            weights = [f[1] for f in filtered]
            return self._rng.choices(texts, weights=weights, k=1)[0]

        # 回退：普通列表
        pool_strs = [str(x) for x in pool if str(x) not in exclude]
        if not pool_strs:
            pool_strs = [str(x) for x in pool]
        return self._rng.choice(pool_strs)

    # ───────────────── ★ 增强：分类过滤 ─────────────────

    def pick_by_category(self, bank_name: str, key: str,
                         category: str,
                         cat_key: str = "category") -> str:
        """按分类标签过滤后随机选取。
        
        词库条目格式示例：
        {"text": "火焰刀", "category": "fire", "weight": 2}
        """
        data = self.load(bank_name)
        pool = data[key]

        filtered = [item for item in pool
                    if isinstance(item, dict) and
                    item.get(cat_key) == category]
        if not filtered:
            # 回退到全池随机
            return self.pick(bank_name, key)

        texts = [item["text"] for item in filtered]
        weights = [item.get("weight", 1) for item in filtered]
        return self._rng.choices(texts, weights=weights, k=1)[0]

    # ───────────────── ★ 增强：回退链 ─────────────────

    def pick_fallback(self, bank_name: str, key: str,
                      fallback_chain: list[tuple[str, str]] = None) -> str:
        """从词库选取，失败时沿回退链依次尝试。
        
        fallback_chain 格式: [(bank, key), (bank, key), ...]
        例如: [("moves_fire", "basic"), ("moves_common", "attack")]
        """
        try:
            return self.pick(bank_name, key)
        except (KeyError, FileNotFoundError):
            if fallback_chain:
                for fb_bank, fb_key in fallback_chain:
                    try:
                        return self.pick(fb_bank, fb_key)
                    except (KeyError, FileNotFoundError):
                        continue
            return f"【缺失:{bank_name}.{key}】"

    # ───────────────── ★ 增强：重复避免 ─────────────────

    def pick_unique(self, bank_name: str, key: str,
                    context_tag: str = "default") -> str:
        """随机选取，但避免与最近已选用词重复。

        context_tag 用于区分不同的上下文（如不同角色、不同场景）。
        """
        data = self.load(bank_name)
        pool = data[key]

        tag = f"{bank_name}.{key}.{context_tag}"
        recent = self._recent.get(tag, [])

        if pool and isinstance(pool[0], dict):
            candidates = [item["text"] for item in pool
                          if item["text"] not in recent]
            if not candidates:
                candidates = [item["text"] for item in pool]
        else:
            candidates = [str(x) for x in pool if str(x) not in recent]
            if not candidates:
                candidates = [str(x) for x in pool]

        chosen = self._rng.choice(candidates)
        recent.append(chosen)
        if len(recent) > self._repetition_window:
            recent.pop(0)
        self._recent[tag] = recent
        return chosen

    def clear_history(self):
        """清除所有重复避免的最近记录。"""
        self._recent.clear()

    # ───────────────── ★ 增强：词池暴露 ─────────────────

    def pool(self, bank_name: str, key: str) -> list:
        """获取某个键下的完整词池列表。
        
        供 Tracery 语法适配器使用。
        自动解包加权字典为纯文本列表。
        """
        data = self.load(bank_name)
        if key not in data:
            return []
        pool_data = data[key]
        if pool_data and isinstance(pool_data[0], dict):
            return [item["text"] for item in pool_data]
        return pool_data

    # ───────────────── 名字生成 ─────────────────

    def generate_name(self, length: int = 2,
                      surname: Optional[str] = None) -> str:
        """半随机生成中文名字。"""
        data = self.load("names")
        if surname is None:
            surname = self._rng.choice(data["surnames"])

        given_chars = self._rng.sample(data["given_name_chars"], length)
        given_name = "".join(given_chars)
        return f"{surname}{given_name}"

    def generate_name_pair(self, gender_hint: str = "neutral") -> tuple[str, str]:
        """生成一对名字。"""
        return self.generate_name(), self.generate_name()

    def get_rng(self) -> random.Random:
        """获取内部随机数生成器。"""
        return self._rng

    def all_keys(self, bank_name: str) -> list[str]:
        """获取词库中所有键名。"""
        data = self.load(bank_name)
        return list(data.keys())
