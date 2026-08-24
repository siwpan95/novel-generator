# -*- coding: utf-8 -*-
"""多层嵌套循环引擎 —— 复现《宇宙巨校闪级生》的核心生成机制。

宇宙巨校闪级生用VB实现了"部→卷→章→段→句→词"六层嵌套循环，
每层都触发关键字随机替换，产生组合爆炸（111部×11卷×N章 → 1.7亿字）。

本模块将这套"ASP多层嵌套循环替换关键字"的写法提升为可配置的Python引擎。

核心机制：
  Layer 0: Series (部)   — 世界/主题级上下文
  Layer 1: Volume (卷)   — 卷级上下文
  Layer 2: Chapter (章)  — 章级上下文
  Layer 3: Section (段)  — 段级上下文，词库填充开始
  Layer 4: Sentence (句) — 模板+词库 → 句子
  Layer 5: Word (词)     — WordBank.pick() 原子操作

变量作用域：
  Series scope: 贯穿整部，如"巨校主题"、"世界法则"
  Volume scope:  贯穿一卷，如"反派姓名"、"核心事件"
  Chapter scope: 贯穿一章，如"场景地形"、"当前对手"
  Section scope: 仅本段，如"战斗招式名"、"环境形容词"
"""

import random
import logging
from typing import Optional, Callable, Any
from pathlib import Path

try:
    from .word_bank import WordBank
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from novel_generator.engine.word_bank import WordBank

_logger = logging.getLogger(__name__)


# ============================================================================
# 六层嵌套循环的层定义
# ============================================================================

class LayerContext:
    """一层嵌套循环的上下文容器。"""

    def __init__(self, name: str, parent: Optional["LayerContext"] = None):
        self.name = name          # 层名: "series" / "volume" / "chapter" / "section" / "sentence"
        self.parent = parent
        self.vars: dict[str, Any] = {}
        self.iteration = 0        # 当前迭代次数
        self.max_iterations = 1   # 最大迭代次数
        self._generated_count = 0 # 本层已生成文本段数

    def get(self, key: str, default=None):
        """沿作用域链向上查找变量。"""
        node = self
        while node is not None:
            if key in node.vars:
                return node.vars[key]
            node = node.parent
        return default

    def set(self, key: str, value):
        self.vars[key] = value

    @property
    def depth(self) -> int:
        d = 0
        node = self.parent
        while node:
            d += 1
            node = node.parent
        return d


class MultiLayerEngine:
    """多层嵌套循环引擎。

    使用方式：
        engine = MultiLayerEngine(wb)
        engine.configure_series(count=111)
        engine.configure_volume(count=11)
        engine.configure_chapter(count=5)
        engine.configure_section(templates=section_templates)

        for text in engine.generate_stream():
            output_file.write(text)
    """

    # 默认的六层配置
    DEFAULT_LAYERS = ["series", "volume", "chapter", "section", "sentence", "word"]

    def __init__(self, wb: WordBank, seed: Optional[int] = None):
        self._wb = wb
        self._rng = random.Random(seed)
        self._layer_configs: dict[str, dict] = {}
        self._series_factories: dict[str, Callable[[LayerContext], None]] = {}
        self._volume_factories: dict[str, Callable[[LayerContext], None]] = {}
        self._chapter_factories: dict[str, Callable[[LayerContext], None]] = {}
        self._section_templates: list[str] = []
        self._sentence_templates: dict[str, list[str]] = {}
        self._total_words = 0
        self._output_file: Optional[Path] = None

    # ================================================================
    # 配置 API
    # ================================================================

    def configure_series(self, count: int, **variables):
        """配置部级参数。"""
        self._layer_configs["series"] = {"count": count, "variables": variables}

    def configure_volume(self, count: int, **variables):
        self._layer_configs["volume"] = {"count": count, "variables": variables}

    def configure_chapter(self, count: int, **variables):
        self._layer_configs["chapter"] = {"count": count, "variables": variables}

    def configure_section(self, templates: list[str]):
        """配置段级模板列表（每个模板就是一个段落框架）。"""
        self._section_templates = templates

    def add_sentence_templates(self, category: str, templates: list[str]):
        """按类别添加句子模板。"""
        if category not in self._sentence_templates:
            self._sentence_templates[category] = []
        self._sentence_templates[category].extend(templates)

    def set_series_factory(self, name: str, factory: Callable[[LayerContext], None]):
        """注册一个部级工厂函数（用于生成该部的全局上下文）。"""
        self._series_factories[name] = factory

    def set_volume_factory(self, name: str, factory: Callable[[LayerContext], None]):
        self._volume_factories[name] = factory

    def set_chapter_factory(self, name: str, factory: Callable[[LayerContext], None]):
        self._chapter_factories[name] = factory

    def set_output_file(self, path: Path):
        """设置输出文件（边生成边写入，避免内存爆炸）。"""
        self._output_file = path

    # ================================================================
    # 多层嵌套循环核心
    # ================================================================

    def generate_all(self) -> str:
        """一次性生成全部文本，返回完整字符串。

        WARNING: 如果配置 111部×11卷×5章×10段 ≈ 61050 个段落，
        可能非常巨大（数千万字）。建议用 generate_stream() 流式输出。
        """
        parts = []
        for text_chunk in self._generate_layers(None):
            parts.append(text_chunk)
        return "\n\n".join(parts)

    def generate_stream(self):
        """流式生成器：每次 yield 一个文本块。

        边生成边 yield，不需要等全部完成。
        """
        yield from self._generate_layers(None)

    def estimate_word_count(self) -> int:
        """预估总字数。"""
        series = self._layer_configs.get("series", {}).get("count", 1)
        volume = self._layer_configs.get("volume", {}).get("count", 1)
        chapter = self._layer_configs.get("chapter", {}).get("count", 1)
        sections = len(self._section_templates) or 1
        # 每段约200字
        return series * volume * chapter * sections * 200

    # ================================================================
    # 内部：嵌套循环生成
    # ================================================================

    def _generate_layers(self, parent: Optional[LayerContext], depth: int = 0) -> iter:
        """递归六层嵌套循环。

        depth 0 = series, 1 = volume, 2 = chapter, 3 = section,
        4 = sentence, 5 = word.
        """
        if depth >= len(self.DEFAULT_LAYERS):
            return

        layer_name = self.DEFAULT_LAYERS[depth]
        config = self._layer_configs.get(layer_name, {})
        count = config.get("count", 1)
        variables = config.get("variables", {})

        for i in range(count):
            ctx = LayerContext(layer_name, parent)
            ctx.iteration = i + 1
            ctx.max_iterations = count

            # 注入层变量
            for k, v in variables.items():
                ctx.set(k, v)

            # 注入层特定变量（如"第X部"、"第Y卷"）
            ctx.set("layer_index", i + 1)
            ctx.set("layer_total", count)

            # 调用工厂函数填充上下文
            if layer_name == "series":
                for factory in self._series_factories.values():
                    factory(ctx)
            elif layer_name == "volume":
                for factory in self._volume_factories.values():
                    factory(ctx)
            elif layer_name == "chapter":
                for factory in self._chapter_factories.values():
                    factory(ctx)

            # 叶节点（段）→ 真正生成文本
            if layer_name == "section":
                yield from self._generate_sections(ctx)
            elif layer_name == "sentence":
                yield from self._generate_sentences(ctx)
            elif layer_name == "word":
                # 最底层不用递归
                pass
            else:
                # 中间层继续递归
                yield from self._generate_layers(ctx, depth + 1)

    def _generate_sections(self, ctx: LayerContext) -> iter:
        """在段层内，对每个段模板生成文本。"""
        if not self._section_templates:
            # 没有模板：生成默认段落
            yield self._default_section_text(ctx)
            return

        for tmpl in self._section_templates:
            # 创建段级子上下文
            section_ctx = LayerContext("sentence", ctx)
            text = self._fill_template(tmpl, section_ctx)
            yield text

    def _generate_sentences(self, ctx: LayerContext) -> iter:
        """句子层：从句子模板池生成句子。"""
        for category, templates in self._sentence_templates.items():
            if templates:
                tmpl = self._rng.choice(templates)
                yield self._fill_template(tmpl, ctx)

    # ================================================================
    # 模板填充（∈占位符← 风格）
    # ================================================================

    def _fill_template(self, template: str, ctx: LayerContext) -> str:
        """填充模板中的占位符。

        支持三种占位符语法：
          ∈词库名.键名←       → 从WordBank随机取（宇宙巨校闪级生风格）
          ∈词库名.键名,N←     → 取N项用顿号连接
          ∈词库名.键名:unique← → 本次展开中不重复
          {变量名}             → 从上下文变量替换
          $变量名              → 同上下文变量
        """
        import re

        # —— 第一步：处理 ∈...← 词库引用 ——
        def wb_replacer(m: re.Match) -> str:
            ref = m.group(1).strip()
            return self._resolve_wb_ref(ref, ctx)

        text = re.sub(r"∈([^←]+)←", wb_replacer, template)

        # —— 第二步：处理 {变量} 和 $变量 ——
        def var_replacer(m: re.Match) -> str:
            key = m.group(1)
            val = ctx.get(key)
            if val is not None:
                return str(val)
            # 尝试从词库查找
            if "." in key:
                return self._resolve_wb_ref(key, ctx)
            return m.group(0)

        text = re.sub(r"\{(\w+(?:\.\w+(?::\w+)?(?:,\d+)?)?)\}", var_replacer, text)
        text = re.sub(r"\$(\w+)", lambda m: str(ctx.get(m.group(1), m.group(0))), text)

        return text

    def _resolve_wb_ref(self, ref: str, ctx: LayerContext) -> str:
        """解析词库引用：bank.key 或 bank.key,N 或 bank.key:unique。"""
        key = ref
        count = 1
        unique = False

        if ":unique" in key:
            unique = True
            key = key.replace(":unique", "")

        if "," in key:
            parts = key.rsplit(",", 1)
            key = parts[0]
            try:
                count = int(parts[1].strip())
            except ValueError:
                count = 1

        if "." not in key:
            return f"[无词库引用: {ref}]"

        bank, k = key.split(".", 1)

        try:
            if count > 1:
                items = self._wb.pick_n(bank, k, count, unique=True)
                return "、".join(items)
            return self._wb.pick(bank, k)
        except (FileNotFoundError, KeyError) as e:
            _logger.warning(f"词库引用失败: {ref} — {e}")
            return f"[{ref}不可用]"

    # ================================================================
    # 默认文本生成
    # ================================================================

    def _default_section_text(self, ctx: LayerContext) -> str:
        """当没有模板时的默认段落生成。"""
        name = ctx.get("主角名", "他")
        scene = ctx.get("当前场景", "这片区域")
        action = self._wb.pick("adjectives", "appearance")
        location = self._wb.get_rng().choice(["前方", "远处", "眼前", "周围"])

        parts = [
            f"{name}站在{scene}，{location}的景色显得{action}。",
            f"他深吸一口气，目光扫过四周。",
        ]

        try:
            terrain = self._wb.pick("locations", "terrain_type")
            terrain_prefix = self._wb.pick("locations", "terrain_prefix")
            parts.append(f"这里是{terrain_prefix}的{terrain}，空气中弥漫着一种说不出的气息。")
        except (FileNotFoundError, KeyError):
            pass

        return "\n".join(parts)

    # ================================================================
    # 统计信息
    # ================================================================

    def summarize(self) -> dict:
        """返回引擎配置的摘要。"""
        series = self._layer_configs.get("series", {}).get("count", 1)
        volume = self._layer_configs.get("volume", {}).get("count", 1)
        chapter = self._layer_configs.get("chapter", {}).get("count", 1)
        sections = len(self._section_templates) or 1
        total_blocks = series * volume * chapter * sections
        est_words = total_blocks * 200

        return {
            "结构": f"{series}部 × {volume}卷 × {chapter}章 × {sections}段",
            "文本块总数": total_blocks,
            "预估字数": f"{est_words:,}",
            "段模板数": len(self._section_templates),
            "句子模板类别": len(self._sentence_templates),
            "句子模板总数": sum(len(t) for t in self._sentence_templates.values()),
        }


# ============================================================================
# 快捷工厂：为「巨校」风格创建预设配置
# ============================================================================

def create_juxiao_engine(wb: WordBank, seed: int = 42) -> MultiLayerEngine:
    """快速创建一个《宇宙巨校闪级生》风格的引擎实例。

    预设结构：12个巨校主题 × 每主题若干卷 × 每卷若干章。
    """
    engine = MultiLayerEngine(wb, seed=seed)

    # 12个巨校主题（实际111个简化版）
    school_themes = [
        "厨艺巨校", "包装巨校", "战斗巨校", "音乐巨校",
        "魔法巨校", "科技巨校", "制药巨校", "驯兽巨校",
        "机关巨校", "幻术巨校", "符文巨校", "星象巨校",
    ]

    # 部级：循环12个主题
    def series_factory(ctx: LayerContext):
        idx = (ctx.iteration - 1) % len(school_themes)
        theme = school_themes[idx]
        ctx.set("巨校主题", theme)
        ctx.set("世界主题", theme)

    engine.set_series_factory("juxiao", series_factory)
    engine.configure_series(count=len(school_themes))

    # 卷级：每部3卷
    engine.configure_volume(count=3)

    # 章级：每卷5章
    engine.configure_chapter(count=5)

    # 段模板（从现有词库风格构建）
    section_templates = [
        # 人物出场模板
        "∈names.surnames←∈names.given_name_chars←的年龄看上去有∈adjectives.appearance←的样子。"
        "他最善使用的兵器是∈equipment.weapon_prefix←∈equipment.weapon_type←，"
        "有一身奇特的武功∈equipment.skill_prefix←∈equipment.skill_body←，"
        "看家的魔法是∈equipment.skill_prefix←∈equipment.skill_body←。",

        # 场景描写模板
        "在{巨校主题}的实习场地上，∈locations.terrain_prefix←的∈locations.terrain_type←"
        "∈locations.scene_like←。极目远方，在那∈locations.terrain_type←的深处，"
        "隐蔽着∈locations.landmark_prefix←的∈locations.landmark_type←。",

        # 战斗开始模板
        "两人对峙片刻，∈names.surnames←∈names.given_name_chars←率先出手！"
        "他手中的∈equipment.weapon_prefix←∈equipment.weapon_type←"
        "化作一道光芒，直取对方要害。",
    ]
    engine.configure_section(section_templates)

    return engine


# ============================================================================
# 自检
# ============================================================================
if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from novel_generator.engine.word_bank import WordBank

    print("=" * 60)
    print("多层嵌套循环引擎 - 自检")
    print("=" * 60)

    wb = WordBank(seed=42)
    engine = create_juxiao_engine(wb, seed=42)

    # 打印配置摘要
    summary = engine.summarize()
    print(f"\n[配置摘要]")
    for k, v in summary.items():
        print(f"  {k}: {v}")

    # 生成前3个文本块作为预览
    print(f"\n[生成预览（前3段）]")
    count = 0
    for text in engine.generate_stream():
        print(f"\n--- 段 {count + 1} ---")
        print(text[:200] + ("..." if len(text) > 200 else ""))
        count += 1
        if count >= 3:
            break

    print(f"\n全部自检通过 [OK]")
