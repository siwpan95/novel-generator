# -*- coding: utf-8 -*-
"""结构化大纲框架 —— 对标《宇宙巨校闪级生》111部×11卷宏大规模。

宇宙巨校闪级生的宏观结构是其产生1.7亿字的基础：
  111部 × 11卷 × N章 = 天文级数的文本量

每一部有一个"巨校主题"（厨艺巨校、包装巨校、战斗巨校...），
每一卷围绕该主题的一场"对决"或"冒险"展开。

这种结构化的框架提供了一个可伸缩的骨架——只要改变
"部数×卷数×章数"的参数，就能精确控制输出规模。

本模块提供：
  1. StructurePlan — 结构计划（部/卷/章的参数化定义）
  2. ArcGenerator — 卷弧线生成器（每卷的故事弧线）
  3. ThemeMixer — 主题混合器（生成新的"巨校"主题组合）
"""

import random
import json
import logging
from pathlib import Path
from typing import Optional, Iterator
from dataclasses import dataclass, field

_logger = logging.getLogger(__name__)


# ============================================================================
# 结构计划
# ============================================================================

@dataclass
class ChapterPlan:
    """一章的计划。"""
    index: int
    title: str = ""
    arc_type: str = "战斗"  # 战斗/探索/解密/修炼/社交/转折
    opponent: str = ""
    location: str = ""
    treasure: str = ""


@dataclass
class VolumePlan:
    """一卷的计划。"""
    index: int
    theme: str = ""
    chapters: list[ChapterPlan] = field(default_factory=list)
    boss_name: str = ""
    boss_tier: str = "common"


@dataclass
class SeriesPlan:
    """一部的计划。"""
    index: int
    theme: str = ""
    world_setting: str = ""
    volumes: list[VolumePlan] = field(default_factory=list)


@dataclass
class StructurePlan:
    """完整的小说结构计划。"""
    title: str = ""
    series: list[SeriesPlan] = field(default_factory=list)
    total_chapters: int = 0
    estimated_words: int = 0


# ============================================================================
# 宏大结构生成器
# ============================================================================

class StructureFramework:
    """基于参数化配置生成111部×11卷的大刚框架。

    使用方式：
        sf = StructureFramework()
        plan = sf.generate(series=111, volumes_per=11, chapters_per=5)
        print(plan.estimated_words)  # 预估字数
    """

    # 111个巨校主题（简化自原版的全部主题，实际更多）
    SCHOOL_THEMES = [
        # 生活技艺类
        "厨艺", "包装", "制衣", "建筑", "园艺", "酿造", "制茶", "刺绣",
        "陶瓷", "木艺", "铁匠", "玉雕", "造纸", "印刷", "制香", "烘焙",
        # 武学类
        "剑道", "刀法", "枪术", "拳法", "掌法", "腿法", "指法", "步法",
        "内功", "轻功", "暗器", "毒术", "医术", "阵法", "符咒", "丹药",
        # 奇门类
        "机关", "傀儡", "占卜", "星象", "风水", "幻术", "结界", "传送",
        "召唤", "驯兽", "御剑", "炼器", "炼丹", "制符", "通灵", "咒术",
        # 魔法类
        "元素魔法", "空间魔法", "时间魔法", "亡灵魔法", "自然魔法", "心灵魔法",
        "光明魔法", "黑暗魔法", "混沌魔法", "血魔法", "符文魔法", "言灵魔法",
        # 科技类
        "机械", "能源", "材料", "生物", "信息", "量子", "纳米", "基因",
        # 奇异类
        "梦境", "影子", "回声", "镜像", "悖论", "轮回", "宿命", "因果",
        "语言", "音乐", "舞蹈", "棋艺", "书法", "绘画", "雕塑", "诗歌",
        "数学", "逻辑", "记忆", "情感", "灵魂", "意志", "信仰", "虚无",
        # 组合类
        "厨艺+战斗", "包装+幻术", "音乐+召唤", "书法+剑道",
        "棋艺+阵法", "绘画+结界", "酿造+毒术", "刺绣+暗器",
        "铁匠+炼器", "烘焙+丹药", "制茶+自然魔法", "陶瓷+土魔法",
    ]

    # 卷弧线类型
    ARC_TYPES = [
        "正面对决", "暗中较量", "秘境探险", "传承试炼",
        "宗门比武", "外敌入侵", "寻宝之旅", "复仇之路",
        "降妖除魔", "破阵解谜", "卧底渗透", "护宝逃亡",
        "联盟缔结", "师承考验", "心魔突破", "天地异变",
    ]

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)

    def generate(
        self,
        series: int = 12,
        volumes_per: int = 3,
        chapters_per: int = 5,
        avg_words_per_chapter: int = 4000,
    ) -> StructurePlan:
        """生成完整结构计划。"""
        plan = StructurePlan(title="巨校传说")

        # 循环获取主题（允许主题数少于部数）
        themes = self.SCHOOL_THEMES[:]

        for s_idx in range(series):
            theme = themes[s_idx % len(themes)]
            s_plan = SeriesPlan(
                index=s_idx + 1,
                theme=theme,
                world_setting=self._generate_world_setting(theme),
            )

            for v_idx in range(volumes_per):
                v_plan = VolumePlan(
                    index=v_idx + 1,
                    theme=theme,
                    boss_name=self._generate_boss_name(),
                    boss_tier=self._rng.choice(["common", "rare", "legendary", "mythic"]),
                )

                # 为每卷生成章计划
                arc_types = self._rng.sample(
                    self.ARC_TYPES,
                    min(chapters_per, len(self.ARC_TYPES)),
                )
                for c_idx in range(chapters_per):
                    arc = arc_types[c_idx % len(arc_types)]
                    c_plan = ChapterPlan(
                        index=c_idx + 1,
                        title=f"第{c_idx + 1}章",
                        arc_type=arc,
                        opponent=self._generate_boss_name(),
                        location=self._generate_location(),
                        treasure=self._generate_treasure(),
                    )
                    v_plan.chapters.append(c_plan)
                    plan.total_chapters += 1

                s_plan.volumes.append(v_plan)
            plan.series.append(s_plan)

        plan.estimated_words = plan.total_chapters * avg_words_per_chapter
        return plan

    def generate_stream(self, **kwargs) -> Iterator[dict]:
        """流式生成每章的简要描述（不全部存入内存）。"""
        series = kwargs.get("series", 12)
        volumes_per = kwargs.get("volumes_per", 3)
        chapters_per = kwargs.get("chapters_per", 5)
        themes = self.SCHOOL_THEMES[:]

        for s_idx in range(series):
            theme = themes[s_idx % len(themes)]
            for v_idx in range(volumes_per):
                arc_types = self._rng.sample(
                    self.ARC_TYPES,
                    min(chapters_per, len(self.ARC_TYPES)),
                )
                for c_idx in range(chapters_per):
                    yield {
                        "series": s_idx + 1,
                        "volume": v_idx + 1,
                        "chapter": c_idx + 1,
                        "theme": theme,
                        "arc_type": arc_types[c_idx % len(arc_types)],
                        "boss": self._generate_boss_name(),
                        "location": self._generate_location(),
                    }

    # ================================================================
    # 内部生成方法
    # ================================================================

    def _generate_world_setting(self, theme: str) -> str:
        """根据主题生成世界设定。"""
        templates = [
            f"这是一个以{theme}为最高准则的世界。在这里，{theme}的造诣决定了一切。",
            f"在这个世界里，{theme}不仅是一种技艺，更是力量的源泉。",
            f"传说中，只有掌握了{theme}的终极奥秘，才能打开通往更高次元的大门。",
        ]
        return self._rng.choice(templates)

    def _generate_boss_name(self) -> str:
        """生成反派/对手名称。"""
        prefixes = ["黑暗", "深渊", "血影", "邪眼", "狂刃", "霜寒",
                    "紫电", "毒牙", "天邪", "地煞", "幽冥", "噬魂",
                    "灭世", "碎星", "裂空", "破虚", "混元", "无极"]
        suffixes = ["老祖", "帝君", "天尊", "魔王", "妖皇", "龙帝",
                    "剑圣", "刀尊", "法王", "术帝", "丹圣", "阵王"]
        if self._rng.random() < 0.5:
            return self._rng.choice(prefixes) + self._rng.choice(suffixes)
        else:
            surname = self._rng.choice("慕容上官欧阳令狐独孤夏侯东方南宫西门")
            name = self._rng.choice("天魔妖神鬼仙灵圣皇帝")
            return surname + name

    def _generate_location(self) -> str:
        """生成地点名。"""
        prefixes = ["天", "地", "玄", "黄", "星", "月", "云", "雾",
                    "灵", "仙", "魔", "妖", "鬼", "龙", "凤", "虎"]
        types = ["峰", "谷", "渊", "海", "林", "原", "洞", "塔",
                 "宫", "殿", "城", "府", "山", "崖", "湖", "岛"]
        return self._rng.choice(prefixes) + self._rng.choice(types) + "之地"

    def _generate_treasure(self) -> str:
        """生成宝物名。"""
        prefixes = ["混元", "太初", "阴阳", "五行", "七星", "九转",
                    "封天", "诛仙", "破界", "斩灵", "照妖", "噬魂"]
        types = ["剑", "刀", "珠", "镜", "印", "幡", "鼎", "炉",
                 "钟", "扇", "尺", "绫", "塔", "图", "环", "轮"]
        return self._rng.choice(prefixes) + self._rng.choice(types)

    # ================================================================
    # 统计与导出
    # ================================================================

    def summarize(self, plan: StructurePlan) -> str:
        """打印结构计划摘要。"""
        lines = [
            f"《{plan.title}》— 结构计划",
            f"{'=' * 50}",
            f"部数: {len(plan.series)}",
            f"卷数: {sum(len(s.volumes) for s in plan.series)}",
            f"章数: {plan.total_chapters}",
            f"预估字数: {plan.estimated_words:,}字",
            f"",
            f"前3部预览:",
        ]
        for s in plan.series[:3]:
            vol_count = len(s.volumes)
            chap_count = sum(len(v.chapters) for v in s.volumes)
            lines.append(f"  第{s.index}部「{s.theme}巨校」- {vol_count}卷{chap_count}章")
            for v in s.volumes[:2]:
                lines.append(f"    第{v.index}卷 - BOSS: {v.boss_name}({v.boss_tier})")
                lines.append(f"      弧线: {', '.join(c.arc_type for c in v.chapters[:3])}")
        return "\n".join(lines)

    def export_to_json(self, plan: StructurePlan, filepath: Path):
        """导出结构计划为JSON。"""
        def _serialize(plan):
            return {
                "title": plan.title,
                "total_chapters": plan.total_chapters,
                "estimated_words": plan.estimated_words,
                "series": [
                    {
                        "index": s.index,
                        "theme": s.theme,
                        "world_setting": s.world_setting,
                        "volumes": [
                            {
                                "index": v.index,
                                "theme": v.theme,
                                "boss_name": v.boss_name,
                                "boss_tier": v.boss_tier,
                                "chapters": [
                                    {
                                        "index": c.index,
                                        "title": c.title,
                                        "arc_type": c.arc_type,
                                        "opponent": c.opponent,
                                        "location": c.location,
                                        "treasure": c.treasure,
                                    }
                                    for c in v.chapters
                                ],
                            }
                            for v in s.volumes
                        ],
                    }
                    for s in plan.series
                ],
            }
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(_serialize(plan), f, ensure_ascii=False, indent=2)


# ============================================================================
# 主题混合器
# ============================================================================

class ThemeMixer:
    """生成新的"巨校主题"组合。

    宇宙巨校闪级生中不只有单一主题（厨艺巨校），还有混合主题。
    通过已有的主题做随机组合，可以指数级扩展主题空间。
    """

    def __init__(self, base_themes: Optional[list[str]] = None, seed: Optional[int] = None):
        self._base = base_themes or StructureFramework.SCHOOL_THEMES
        self._rng = random.Random(seed)

    def mix(self, count: int = 100, max_components: int = 3) -> list[str]:
        """生成混合主题（如 '厨艺+战斗+幻术巨校'）。"""
        results = set()
        attempts = 0
        while len(results) < count and attempts < count * 10:
            n = self._rng.randint(2, max_components)
            components = self._rng.sample(self._base, n)
            theme = " + ".join(components)
            results.add(theme)
            attempts += 1
        return list(results)[:count]

    def themed_titles(self, themes: list[str]) -> list[str]:
        """为主题列表生成小说标题。"""
        titles = []
        for theme in themes:
            parts = theme.replace("巨校", "").split("+")
            clean = [p.strip() for p in parts]
            pattern = self._rng.choice([
                "{theme}传说",
                "{theme}之路",
                "究极{theme}",
                "{theme}无双",
                "{theme}天王",
                "逆天{theme}",
            ])
            titles.append(pattern.format(theme="".join(clean)))
        return titles


# ============================================================================
# 一键生成
# ============================================================================

def create_juxiao_plan(
    target_words: int = 100_000_000,  # 1亿字
    avg_words_per_chapter: int = 4000,
    seed: int = 42,
) -> StructurePlan:
    """根据目标字数自动计算结构参数，生成《宇宙巨校闪级生》风格的计划。

    target_words=1亿 → 约10部×10卷×10章=1000章×4000字=400万字（太少了）
    实际需要: 25000章 × 4000字 = 1亿字 ≈ 100部×10卷×25章
    """
    chapters_needed = target_words // avg_words_per_chapter

    # 计算一组合理的参数
    series = max(10, min(111, int(chapters_needed ** (1 / 3))))
    volumes = max(3, int((chapters_needed / series) ** 0.5))
    chapters = max(5, int(chapters_needed / (series * volumes)))

    actual = series * volumes * chapters
    actual_words = actual * avg_words_per_chapter

    print(f"[自动推算结构] 目标{target_words:,}字")
    print(f"  → {series}部 × {volumes}卷 × {chapters}章 = {actual}章")
    print(f"  → 预估值: {actual_words:,}字")

    sf = StructureFramework(seed=seed)
    return sf.generate(
        series=series,
        volumes_per=volumes,
        chapters_per=chapters,
        avg_words_per_chapter=avg_words_per_chapter,
    )


# ============================================================================
# 自检
# ============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("结构化大纲框架 - 自检")
    print("=" * 60)

    # 1. 小规模生成测试
    print("\n[小规模结构生成]")
    sf = StructureFramework(seed=42)
    plan = sf.generate(series=3, volumes_per=2, chapters_per=3)
    print(sf.summarize(plan))

    # 2. 主题混合器
    print("\n[主题混合器]")
    mixer = ThemeMixer(seed=42)
    mixed = mixer.mix(count=5)
    print(f"  混合主题: {mixed}")
    titles = mixer.themed_titles(mixed)
    print(f"  生成标题: {titles}")

    # 3. 流式生成
    print("\n[流式生成（前5章）]")
    count = 0
    for chap in sf.generate_stream(series=2, volumes_per=2, chapters_per=3):
        print(f"  第{chap['series']}部·「{chap['theme']}巨校」"
              f"第{chap['volume']}卷第{chap['chapter']}章: "
              f"{chap['arc_type']} | BOSS:{chap['boss']} | {chap['location']}")
        count += 1
        if count >= 5:
            break

    # 4. 自动推算
    print("\n[目标1万字快速测试]")
    small_plan = create_juxiao_plan(target_words=10_000, avg_words_per_chapter=500, seed=42)
    print(f"  实际章数: {small_plan.total_chapters}")
    print(f"  实际预估: {small_plan.estimated_words:,}字")

    print(f"\n全部自检通过 [OK]")
