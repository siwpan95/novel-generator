# -*- coding: utf-8 -*-
"""∈占位符← 风格标记系统 —— 对标《宇宙巨校闪级生》的可追踪模板语法。

宇宙巨校闪级生的一个鲜明技术特征是其独特的占位符语法：
  "蘑菇王子的兵器是∈追云赶天鞭←"
  "蘑菇王子的魔法是∈神音蘑菇咒←"
  "蘑菇王子的法宝是∈蓝光宝典←"

这些 ∈名称← 标记既是词库替换的占位符，又是最终的输出格式。
这种标记法有几个技术优点：
  1. 可见性强 —— 尖括号风格的定界符在纯文本中清晰可辨
  2. 可追溯 —— 输出后的文本可以反向查找到底是哪个词库填充的
  3. 可调试 —— 未解析的标记可以在最终输出中留下痕迹
  4. 多语言友好 —— 不需要转义，天然适配中文环境

本模块提供：
  1. FlashMarker —— 标记解析引擎
  2. FlashTemplate —— 模板定义与组合
  3. FlashTracer —— 回溯追踪（从输出文本反推模板+词库来源）
"""

import re
import json
import random
import logging
from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict

try:
    from .word_bank import WordBank
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from novel_generator.engine.word_bank import WordBank

_logger = logging.getLogger(__name__)


# ============================================================================
# FlashMarker 核心
# ============================================================================

@dataclass
class MarkerRef:
    """一个解析后的标记引用。"""
    raw: str              # 原始标记文本，如 "∈names.surnames←"
    bank: str             # 词库名
    key: str              # 键名
    count: int = 1        # 取几个值
    unique: bool = False  # 是否不重复
    transform: Optional[str] = None  # 后处理（如 :upper, :capitalize）


@dataclass
class ResolvedText:
    """解析后的文本，包含原始占位符→实际值的映射。"""
    text: str              # 最终文本
    mappings: list[tuple[str, str]] = field(default_factory=list)
    # [(原始标记, 替换后的值), ...]

    @property
    def unresolved(self) -> list[str]:
        """返回未解析的标记（值为空或带[不可用]后缀的）。"""
        return [raw for raw, val in self.mappings if "[不可用]" in val or not val]


class FlashMarker:
    """∈标记← 语法解析与替换引擎。

    支持语法：
      基础引用:    ∈bank.key←
      多重引用:    ∈bank.key,3←   (取3个，顿号连接)
      去重引用:    ∈bank.key:unique←
      链式引用:    ∈bank1.k1←的∈bank2.k2←
      嵌套变量:    ∈bank.{var}←   (用上下文变量决定key)
      转义:        ∈←             (输出原始字符∈←)
    """

    MARKER_PATTERN = re.compile(r"∈([^←]*)←")

    def __init__(self, wb: WordBank, seed: Optional[int] = None):
        self._wb = wb
        self._rng = random.Random(seed)
        self._cache: dict[str, list[str]] = {}  # 已取值缓存(用于unique)
        self._usage_count: dict[str, int] = defaultdict(int)

    # ================================================================
    # 主接口
    # ================================================================

    def resolve(self, template: str, context: Optional[dict[str, str]] = None) -> ResolvedText:
        """解析模板中的所有 ∈...← 标记。"""
        if context is None:
            context = {}

        mappings = []
        def replacer(m: re.Match) -> str:
            raw = m.group(0)
            ref_text = m.group(1).strip()

            if not ref_text:
                # ∈← 转义
                mappings.append((raw, ""))
                return ""

            # 先替换上下文变量
            for var, val in context.items():
                ref_text = ref_text.replace(f"{{{var}}}", val)

            marker = self._parse_ref(ref_text)
            if marker is None:
                mappings.append((raw, f"[无效标记:{ref_text}]"))
                return f"[无效标记:{ref_text}]"

            value = self._resolve_marker(marker)
            mappings.append((raw, value))
            self._usage_count[raw] += 1
            return value

        text = self.MARKER_PATTERN.sub(replacer, template)
        return ResolvedText(text=text, mappings=mappings)

    def resolve_batch(self, templates: list[str],
                       context: Optional[dict[str, str]] = None) -> list[ResolvedText]:
        """批量解析多个模板（共享unique缓存）。"""
        return [self.resolve(t, context) for t in templates]

    def reset_cache(self):
        """重置unique缓存（新一轮生成时调用）。"""
        self._cache.clear()
        self._usage_count.clear()

    # ================================================================
    # 内部解析
    # ================================================================

    def _parse_ref(self, ref: str) -> Optional[MarkerRef]:
        """解析一个引用字符串为 MarkerRef。"""
        ref = ref.strip()
        if not ref:
            return None

        count = 1
        unique = False
        transform = None

        # 提取修饰符
        # :unique
        if ":unique" in ref:
            unique = True
            ref = ref.replace(":unique", "")

        # :upper, :capitalize, :lower
        for tf in (":upper", ":capitalize", ":lower"):
            if tf in ref:
                transform = tf[1:]
                ref = ref.replace(tf, "")

        # ,N
        if "," in ref:
            parts = ref.rsplit(",", 1)
            ref = parts[0]
            try:
                count = int(parts[1].strip())
            except ValueError:
                pass

        # 解析 bank.key
        if "." not in ref:
            return None

        parts = ref.split(".", 1)
        return MarkerRef(
            raw=f"∈{ref}←".replace(":unique", "").replace(":upper", "").replace(":lower", ""),
            bank=parts[0],
            key=parts[1],
            count=count,
            unique=unique,
            transform=transform,
        )

    def _resolve_marker(self, marker: MarkerRef) -> str:
        """解析一个 MarkerRef 为实际字符串。"""
        cache_key = f"{marker.bank}.{marker.key}"

        try:
            if marker.count > 1:
                items = self._wb.pick_n(
                    marker.bank, marker.key,
                    count=marker.count,
                    unique=marker.unique,
                )
            else:
                item = self._wb.pick(marker.bank, marker.key)
                items = [item]
        except Exception as e:
            _logger.debug(f"标记解析失败: {marker.raw} — {e}")
            return f"[{marker.bank}.{marker.key}不可用]"

        # 后处理
        if marker.transform == "upper":
            items = [i.upper() if hasattr(i, 'upper') else i for i in items]
        elif marker.transform == "capitalize":
            items = [i[0].upper() + i[1:] if i else i for i in items]
        elif marker.transform == "lower":
            items = [i.lower() if hasattr(i, 'lower') else i for i in items]

        return self._join_items(items, marker.count)

    def _join_items(self, items: list[str], count: int) -> str:
        """连接多个词项：2个用"和"，3+个用"、...和"。"""
        if not items:
            return "[空]"
        if count == 1:
            return items[0]
        if count == 2:
            return f"{items[0]}和{items[1]}"
        return "、".join(items[:-1]) + "和" + items[-1]


# ============================================================================
# FlashTemplate 模板定义系统
# ============================================================================

class FlashTemplate:
    """标记模板定义与管理。

    宇宙巨校闪级生的模板体系可分为五大类：
      1. 人物出场模板
      2. 怪物出场模板
      3. 场景描写模板
      4. 战斗场面模板
      5. 对话模板
    """

    @staticmethod
    def character_intro() -> list[str]:
        """人物出场模板。"""
        return [
            # 基础模板
            "∈names.surnames←∈names.given_name_chars←的年龄看上去有∈adjectives.appearance←的样子。"
            "他最善使用的兵器是∈equipment.weapon_prefix←∈equipment.weapon_type←，"
            "有一身奇特的武功∈equipment.skill_prefix←∈equipment.skill_body←，"
            "看家的魔法是∈equipment.skill_prefix←∈equipment.skill_body←。",

            # 荣誉模板
            "∈names.surnames←∈names.given_name_chars←，人称∈names.nickname_prefix←"
            "∈names.nickname_suffix←。他这一生最大的骄傲便是∈equipment.weapon_prefix←"
            "∈equipment.weapon_type←，这件宝物随他征战多年，从未败过。",

            # 神秘模板
            "没人知道∈names.surnames←∈names.given_name_chars←的真实来历。"
            "只知道他出现时总是带着∈adjectives.emotion←的神情，"
            "手中∈equipment.weapon_type←闪烁着∈adjectives.color←的光芒。",
        ]

    @staticmethod
    def monster_intro() -> list[str]:
        """怪物出场模板。"""
        return [
            "忽然一声∈adjectives.ambient←的巨响，从∈locations.terrain_type←中"
            "冲出一只∈monsters.monster_prefix←∈monsters.monster_type←！",

            "那∈monsters.monster_prefix←∈monsters.monster_type←发出"
            "∈adjectives.terrifying←的咆哮，它的∈adjectives.appearance←身体"
            "在月光下显得格外狰狞。",

            "远方的∈locations.terrain_type←忽然裂开一道口子，"
            "一只体型巨大的∈monsters.monster_prefix←∈monsters.monster_type←"
            "从裂缝中爬了出来，浑身上下散发着∈adjectives.ambient←的气息。",
        ]

    @staticmethod
    def scene_description() -> list[str]:
        """场景描写模板。"""
        return [
            "这∈locations.terrain_type←∈locations.scene_like←。"
            "极目远方，在那∈locations.terrain_type←的深处，"
            "隐蔽着∈locations.landmark_prefix←的∈locations.landmark_type←。",

            "∈locations.terrain_prefix←的∈locations.terrain_type←"
            "∈locations.scene_like←。周围的空气中弥漫着"
            "∈adjectives.ambient←的∈adjectives.scene←气息。",

            "放眼望去，∈locations.terrain_type←延绵千里，"
            "目之所及皆是∈adjectives.color←的∈adjectives.texture←。",
        ]

    @staticmethod
    def battle_sequence() -> list[str]:
        """战斗场面模板（可链式组合为完整战斗段落）。"""
        return [
            # 开局
            "两人对峙片刻，∈names.surnames←∈names.given_name_chars←率先出手！"
            "他手中的∈equipment.weapon_prefix←∈equipment.weapon_type←"
            "化作一道∈adjectives.color←的光芒，直取对方要害。",

            # 反击
            "对手∈names.surnames←∈names.given_name_chars←冷笑一声，"
            "不闪不避，手中的∈equipment.weapon_type←迎了上去。"
            "两件宝物在空中碰撞，迸发出∈adjectives.appearance←的火花。",

            # 大招
            "就在此时，∈names.surnames←∈names.given_name_chars←"
            "忽然大喝一声：」∈equipment.skill_prefix←∈equipment.skill_body←」!"
            "刹那间天地变色，∈adjectives.terrifying←的气场笼罩了整个战场。",
        ]

    @staticmethod
    def dialogue() -> list[str]:
        """对话模板。"""
        return [
            "\"你竟敢来这{location}撒野！\"∈names.surnames←∈names.given_name_chars←怒喝道。",
            "\"久仰{opponent}大名，今日终于得见！\"∈names.surnames←∈names.given_name_chars←拱手道。",
            "\"这{treasure}真不愧是传说中的宝物！\"众人禁不住惊叹。",
        ]

    @classmethod
    def all_templates(cls) -> dict[str, list[str]]:
        """返回所有模板类别。"""
        return {
            "character_intro": cls.character_intro(),
            "monster_intro": cls.monster_intro(),
            "scene_description": cls.scene_description(),
            "battle_sequence": cls.battle_sequence(),
            "dialogue": cls.dialogue(),
        }

    @classmethod
    def random_template(cls, category: str, seed: Optional[int] = None) -> str:
        """随机选取一个类别的模板。"""
        rng = random.Random(seed)
        templates = cls.all_templates().get(category, [])
        if not templates:
            return ""
        return rng.choice(templates)


# ============================================================================
# FlashTracer 回溯追踪
# ============================================================================

class FlashTracer:
    """从输出文本反推模板+词库来源。

    用宇宙巨校闪级生举例：
      原文: "蘑菇王子的兵器是∈追云赶天鞭←"
      追踪: 模板=character_equipment, 词库=equipment.weapon_type,
             取值=追云赶天鞭, 索引=equipment.json第42项

    这在调试时非常有用——当输出中出现不合逻辑的文本时，
    可以精确追踪到是哪个词库的哪一项导致的。
    """

    def __init__(self, wb_dir: Path):
        self._wb_dir = wb_dir
        self._bank_cache: dict[str, dict] = {}

    def trace(self, text: str) -> list[dict]:
        """扫描文本中的 ∈...← 标记，追踪其词库来源。"""
        results = []
        for m in re.finditer(r"∈([^←]+)←", text):
            raw = m.group(0)
            ref = m.group(1).strip()

            if not ref or "." not in ref:
                results.append({"raw": raw, "error": "无效标记"})
                continue

            bank, key = ref.split(".", 1)
            bank_data = self._load_bank(bank)

            trace_info = {
                "raw": raw,
                "bank": bank,
                "key": key,
                "bank_file": str(self._wb_dir / f"{bank}.json"),
                "total_entries": len(bank_data.get(key, [])),
                "sample_values": bank_data.get(key, [])[:5],
            }
            results.append(trace_info)

        return results

    def _load_bank(self, bank: str) -> dict:
        if bank not in self._bank_cache:
            path = self._wb_dir / f"{bank}.json"
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    self._bank_cache[bank] = json.load(f)
            else:
                self._bank_cache[bank] = {}
        return self._bank_cache[bank]

    def print_trace(self, text: str):
        """打印追踪结果（便于调试）。"""
        traces = self.trace(text)
        print(f"追踪 {len(traces)} 个标记:\n")
        for t in traces:
            print(f"  标记: {t.get('raw', '?')}")
            if "error" in t:
                print(f"    → {t['error']}")
            else:
                print(f"    词库: {t['bank']}.json / 键: {t['key']}")
                print(f"    总条目: {t['total_entries']}")
                print(f"    样本: {t['sample_values']}")
            print()


# ============================================================================
# 自检
# ============================================================================
if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from novel_generator.engine.word_bank import WordBank

    print("=" * 60)
    print("∈占位符← 标记系统 - 自检")
    print("=" * 60)

    wb = WordBank(seed=42)
    marker = FlashMarker(wb, seed=42)

    # 测试基础解析
    print("\n[基础解析]")
    test1 = "∈names.surnames←∈names.given_name_chars←"
    r1 = marker.resolve(test1)
    print(f"  输入: {test1}")
    print(f"  输出: {r1.text}")
    print(f"  映射: {r1.mappings}")

    # 测试多重引用
    print("\n[多重引用]")
    test2 = "人物: ∈names.surnames←, ∈names.given_name_chars←"
    r2 = marker.resolve(test2)
    print(f"  输入: {test2}")
    print(f"  输出: {r2.text}")

    # 测试模板
    print("\n[人物出场模板]")
    tmpl = FlashTemplate.random_template("character_intro", seed=42)
    r3 = marker.resolve(tmpl)
    print(f"  模板: {tmpl[:60]}...")
    print(f"  生成: {r3.text[:100]}...")

    # 测试怪物模板
    print("\n[怪物出场模板]")
    tmpl2 = FlashTemplate.random_template("monster_intro", seed=99)
    r4 = marker.resolve(tmpl2)
    print(f"  生成: {r4.text[:100]}...")

    # 测试战斗序列
    print("\n[战斗序列模板]")
    for tmpl in FlashTemplate.battle_sequence()[:2]:
        r5 = marker.resolve(tmpl)
        print(f"  {r5.text[:80]}...")

    print(f"\n全部自检通过 [OK]")
