"""ASP 模板流引擎核心模块。

导出所有公共接口：
- WordBank / TemplateEngine：词库+模板基础层
- MultiLayerEngine / FlashMarker：嵌套循环+标记层
- NovelGenerator / ChapterGenerator / ... ：生成器层
- SentenceRhythmEngine / ContextManager：v2.0 增强层
- TraceryAdapter / GrammarRegistry：语法层
"""

from .word_bank import WordBank
from .template import TemplateEngine
from .tracery_grammar import TraceryAdapter, GrammarRegistry, SentencePatterns
from .multi_layer_engine import MultiLayerEngine
from .flash_marker import FlashMarker
from .structure_framework import StructureFramework
from .monster_generator import MonsterGenerator
from .batch_writer import BatchWriter
from .sentence_rhythm import (
    SentenceRhythmEngine,
    ChapterRhythmOrchestrator,
    RhythmProfile,
    PRESET_PROFILES,
)
from .context_manager import ContextManager

__all__ = [
    # 基础
    "WordBank",
    "TemplateEngine",
    # 语法
    "TraceryAdapter",
    "GrammarRegistry",
    "SentencePatterns",
    # 引擎
    "MultiLayerEngine",
    "FlashMarker",
    "StructureFramework",
    "MonsterGenerator",
    "BatchWriter",
    # v2.0 增强
    "SentenceRhythmEngine",
    "ChapterRhythmOrchestrator",
    "RhythmProfile",
    "PRESET_PROFILES",
    "ContextManager",
]
