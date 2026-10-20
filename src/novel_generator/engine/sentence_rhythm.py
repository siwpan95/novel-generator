"""句子节奏与章法控制引擎。

基于 ASP 多层嵌套结构，为每层配置不同的节奏模式：
- 部级别：宏观节奏曲线（铺陈→展开→高潮→收束）
- 卷级别：卷内情绪图谱（紧张/舒缓交替）
- 章级别：段落长短分布控制
- 句级别：句式长短变化规则

核心概念：
- 节奏曲线（Rhythm Curve）：一条随时间变化的强度/情绪曲线
- 句式模板（Sentence Pattern）：不同节奏点的句式选择
- 段落结构（Paragraph Structure）：段内句子的组织模式
"""

import random
import math
from typing import Optional, Callable


class RhythmProfile:
    """节奏配置档案：定义一种节奏模式的所有参数。"""

    def __init__(self,
                 name: str,
                 sentence_lengths: list[int] = None,
                 paragraph_sizes: list[int] = None,
                 transition_prob: float = 0.3,
                 intensity_curve: callable = None):
        self.name = name
        # 句长分布池（字数）
        self.sentence_lengths = sentence_lengths or [8, 12, 16, 20, 24, 30]
        # 段落大小分布池（句子数）
        self.paragraph_sizes = paragraph_sizes or [2, 3, 4, 5, 6]
        # 句式转换概率
        self.transition_prob = transition_prob
        # 强度曲线函数 phase(0.0~1.0) → intensity(0.0~1.0)
        self.intensity_curve = intensity_curve or (lambda p: 0.5 + 0.5 * math.sin(p * math.pi))

    def intensity_at(self, progress: float) -> float:
        """获取指定进度位置的强度值。"""
        return self.intensity_curve(progress)


# ───────────────── 预设节奏配置 ─────────────────

PRESET_PROFILES = {
    "build_up": RhythmProfile(
        name="build_up",
        sentence_lengths=[10, 14, 18, 22, 26, 32],
        paragraph_sizes=[3, 4, 5, 6, 7],
        intensity_curve=lambda p: 0.3 + 0.7 * p,  # 线性递增
    ),
    "climax": RhythmProfile(
        name="climax",
        sentence_lengths=[6, 8, 10, 12, 14, 18],
        paragraph_sizes=[1, 2, 3, 4],
        intensity_curve=lambda p: 0.7 + 0.3 * math.sin(p * math.pi),  # 高位震荡
    ),
    "resolution": RhythmProfile(
        name="resolution",
        sentence_lengths=[12, 16, 20, 24, 28],
        paragraph_sizes=[2, 3, 4, 5],
        intensity_curve=lambda p: 0.6 - 0.4 * p,  # 渐降
    ),
    "breather": RhythmProfile(
        name="breather",
        sentence_lengths=[4, 6, 8, 10, 14],
        paragraph_sizes=[1, 2, 3],
        intensity_curve=lambda p: 0.2 + 0.2 * math.sin(p * math.pi * 1.5),  # 低位轻震
    ),
    "exposition": RhythmProfile(
        name="exposition",
        sentence_lengths=[14, 18, 22, 26, 30, 36],
        paragraph_sizes=[3, 4, 5, 6],
        intensity_curve=lambda p: 0.4 + 0.3 * math.sin(p * math.pi * 0.5),  # 中位缓动
    ),
}


class SentenceRhythmEngine:
    """句子节奏引擎：控制句子长度、段落结构和叙事节奏。"""

    def __init__(self, profile: str = "exposition",
                 seed: Optional[int] = None):
        self._rng = random.Random(seed)
        self.profile = PRESET_PROFILES.get(
            profile, PRESET_PROFILES["exposition"]
        )
        self._progress: float = 0.0  # 当前在节奏曲线上的位置
        self._sentence_count: int = 0  # 已生成的句子数

    def set_profile(self, profile_name: str):
        """设置节奏配置。"""
        self.profile = PRESET_PROFILES.get(
            profile_name, PRESET_PROFILES["exposition"]
        )

    def set_progress(self, progress: float):
        """设置当前节奏曲线进度 (0.0 ~ 1.0)。"""
        self._progress = max(0.0, min(1.0, progress))

    def advance_progress(self, delta: float = 0.05):
        """推进节奏曲线进度。"""
        self._progress = max(0.0, min(1.0, self._progress + delta))

    def current_intensity(self) -> float:
        """获取当前强度值。"""
        return self.profile.intensity_at(self._progress)

    def target_sentence_length(self) -> int:
        """获取当前节奏位置建议的句长。"""
        intensity = self.current_intensity()
        lengths = self.profile.sentence_lengths
        # 高强度 → 短句（冲击力），中等强度 → 长句（铺陈）
        # 使用两个池子的混合
        short_pool = lengths[:len(lengths)//2]
        long_pool = lengths[len(lengths)//2:]

        if random.random() < intensity:
            return self._rng.choice(short_pool)
        else:
            return self._rng.choice(long_pool)

    def target_paragraph_size(self) -> int:
        """获取当前节奏位置建议的段落句子数。"""
        return self._rng.choice(self.profile.paragraph_sizes)

    def sentence_pattern(self) -> str:
        """根据当前强度选择句式模式。

        返回句式类型标签：
        - "short_punch"  短促有力
        - "medium_flow"  中速流畅
        - "long_describe" 长句铺陈
        - "fragment"     片段/独词
        - "parallel"     排比句
        """
        intensity = self.current_intensity()
        if intensity > 0.7:
            patterns = ["short_punch", "fragment", "parallel"]
            weights = [0.5, 0.3, 0.2]
        elif intensity > 0.4:
            patterns = ["medium_flow", "long_describe", "parallel"]
            weights = [0.5, 0.3, 0.2]
        else:
            patterns = ["long_describe", "medium_flow", "short_punch"]
            weights = [0.4, 0.4, 0.2]

        return self._rng.choices(patterns, weights=weights, k=1)[0]

    def transition_should_change(self) -> bool:
        """判断当前是否应该切换句式。"""
        return self._rng.random() < self.profile.transition_prob

    def get_paragraph_template(self,
                               sentence_count: Optional[int] = None) -> list[str]:
        """获取一个段落的句式序列模板。

        返回句式类型列表，如 ["long_describe", "medium_flow", "short_punch"]。
        """
        if sentence_count is None:
            sentence_count = self.target_paragraph_size()

        patterns = []
        for i in range(sentence_count):
            self.advance_progress(1.0 / max(sentence_count, 1))
            if patterns and not self.transition_should_change():
                patterns.append(patterns[-1])  # 保持相同模式
            else:
                patterns.append(self.sentence_pattern())
        return patterns

    def reset(self):
        """重置节奏引擎状态。"""
        self._progress = 0.0
        self._sentence_count = 0


# ───────────────── 章节节奏编排 ─────────────────

class ChapterRhythmOrchestrator:
    """章节级节奏编排器：将整章拆分为节奏阶段，各阶段应用不同配置。"""

    STAGE_PRESETS = {
        "opening":    ("exposition", 0.00, 0.15),
        "build_1":    ("build_up",   0.15, 0.35),
        "midpoint":   ("climax",     0.35, 0.55),
        "build_2":    ("build_up",   0.55, 0.75),
        "climax_peak":("climax",     0.75, 0.90),
        "ending":     ("resolution",  0.90, 1.00),
    }

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)
        self._engine = SentenceRhythmEngine(seed=seed)

    def plan_chapter_rhythm(self, total_sentences: int = 60) -> list[dict]:
        """规划一章的节奏分段。

        返回列表，每项包含：
        - stage_name: 阶段名称
        - start_progress: 起始进度
        - end_progress: 结束进度
        - sentence_count: 该阶段句子数
        - profile: 节奏配置名
        """
        plan = []
        for stage_name, (profile, start_p, end_p) in self.STAGE_PRESETS.items():
            portion = end_p - start_p
            s_count = max(1, int(total_sentences * portion))
            plan.append({
                "stage_name": stage_name,
                "profile": profile,
                "start_progress": start_p,
                "end_progress": end_p,
                "sentence_count": s_count,
            })
        return plan

    def generate_paragraph_sequence(self,
                                    total_sentences: int = 60) -> list[list[str]]:
        """根据章节节奏规划，生成全文段落句式序列。"""
        plan = self.plan_chapter_rhythm(total_sentences)
        all_paragraphs = []

        for stage in plan:
            self._engine = SentenceRhythmEngine(
                profile=stage["profile"],
                seed=self._rng.randint(0, 2**31)
            )
            n = stage["sentence_count"]
            stage_start = stage["start_progress"]
            stage_end = stage["end_progress"]

            remaining = n
            while remaining > 0:
                para_size = min(remaining,
                                self._engine.target_paragraph_size())
                self._engine.set_progress(stage_start +
                    (1 - remaining / max(n, 1)) * (stage_end - stage_start))
                patterns = self._engine.get_paragraph_template(para_size)
                all_paragraphs.append(patterns)
                remaining -= para_size

        return all_paragraphs
