"""ASP 小说生成统一引擎（纯净版）。

整合所有 ASP 模板流核心模块：
- 词库加载与随机选取（WordBank）
- 模板引擎（TemplateEngine）
- Tracery 语法适配（TraceryAdapter）
- 多层嵌套循环引擎（MultiLayerEngine）
- 章节节奏控制（SentenceRhythmEngine）
- 上下文状态管理（ContextManager）
- 闪记标记强化（FlashMarker）
- 结构框架（StructureFramework）
- 怪物生成器（MonsterGenerator）
- 批量写作（BatchWriter）
- 生成器集合（generators/）

运行模式：
- full：全量生成全部 20 部小说（NovelGenerator 模式）
- single：单章生成（ChapterGenerator 模式）
- volume：整卷生成（VolumeGenerator 模式）
"""

import argparse
import json
import os
import random
import time
from pathlib import Path
from typing import Optional

from engine.word_bank import WordBank
from engine.template import TemplateEngine
from engine.tracery_grammar import TraceryAdapter
from engine.multi_layer_engine import MultiLayerEngine
from engine.flash_marker import FlashMarker
from engine.structure_framework import StructureFramework
from engine.monster_generator import MonsterGenerator
from engine.batch_writer import BatchWriter, BatchConfig
from engine.sentence_rhythm import SentenceRhythmEngine, ChapterRhythmOrchestrator
from engine.context_manager import ContextManager
from engine.narrative_constraints import NarrativeConstraintEngine
from engine.character_drive import InteractionEngine
from engine.generators import (
    NovelGenerator, ChapterGenerator, VolumeGenerator,
    CharacterGenerator, BattleGenerator, DialogueGenerator
)

OUTPUT_DIR = Path(__file__).parent / "output"


class ASPNovelEngine:
    """ASP 小说生成引擎：整合全部 ASP 核心模块。"""

    def __init__(self, seed: Optional[int] = None):
        self.seed = seed
        # 基础层
        self._rng = random.Random(seed)
        self.wb = WordBank(seed=seed)
        self.template = TemplateEngine(self.wb, seed=seed)

        # 语法层
        self.grammar = TraceryAdapter(self.wb, seed=seed)
        self.grammar.register_preset_grammars()

        # 上下文层
        self.context = ContextManager()

        # 核心引擎层
        self.rhythm = SentenceRhythmEngine(seed=seed)
        self.rhythm_orch = ChapterRhythmOrchestrator(seed=seed)
        self.flash_marker = FlashMarker(self.wb)
        self.structure = StructureFramework(seed=seed)
        self.monster_gen = MonsterGenerator(self.wb)
        self.batch_writer = BatchWriter(self.wb, BatchConfig())

        # 叙事模块（增强）
        self.constraint_engine = NarrativeConstraintEngine()
        self.interaction_engine = InteractionEngine(rng=self._rng)

        # 生成器层（遵循现有接口）
        self.novel_gen = NovelGenerator(
            seed=seed,
            context_mgr=self.context,
            structure_fw=self.structure,
            constraint_engine=self.constraint_engine,
            drive_engine=(None, self.interaction_engine),
        )
        self.multi_layer = MultiLayerEngine(self.wb, seed=seed)
        self.chapter_gen = ChapterGenerator(self.wb)
        self.vol_gen = VolumeGenerator(self.wb)
        self.char_gen = CharacterGenerator(self.wb)
        self.battle_gen = BattleGenerator(self.wb)
        self.dialogue_gen = DialogueGenerator(self.wb)

        # 统计
        self.stats = {
            "total_chapters": 0,
            "total_words": 0,
            "start_time": None,
            "elapsed": 0,
        }

    # ───────────────── 全量生成（NovelGenerator 模式） ─────────────────

    def generate_full_novel(self,
                            volumes: int = 20,
                            chapters_per_volume: int = 7,
                            opponents_per_chapter: int = 4,
                            output_dir: Optional[str] = None) -> str:
        """全量生成小说（使用 NovelGenerator 的经典巨校模式）。

        Args:
            volumes: 部（卷）数
            chapters_per_volume: 每卷章数
            opponents_per_chapter: 每章对手数量
            output_dir: 输出目录

        Returns:
            完整小说文本。
        """
        self.stats["start_time"] = time.time()

        out = output_dir or str(OUTPUT_DIR)
        os.makedirs(out, exist_ok=True)

        print("=" * 60)
        print("  ASP 小说全量生成（巨校模式）")
        print(f"  部数：{volumes}，每部 {chapters_per_volume} 章")
        print(f"  预计总字数：约 {volumes * chapters_per_volume * 7000:,} 字")
        print(f"  输出目录：{out}")
        print("=" * 60)

        result = self.novel_gen.generate(
            volumes=volumes,
            chapters_per_volume=chapters_per_volume,
            opponents_per_chapter=opponents_per_chapter,
            output_dir=out,
            seed=self._rng.randint(1, 999999),
        )

        self.stats["elapsed"] = time.time() - self.stats["start_time"]
        self.stats["total_chapters"] = volumes * chapters_per_volume
        self.stats["total_words"] = len(result)
        self._print_stats()
        return result

    # ───────────────── 单章生成（ChapterGenerator 模式） ─────────────────

    def generate_single_chapter(self,
                                chapter_num: int = 1,
                                volume_title: str = "未知领域",
                                hero: dict = None,
                                partner: dict = None,
                                opponent_count: int = 4,
                                seed: int = None) -> str:
        """生成单章内容。

        Args:
            chapter_num: 章序号
            volume_title: 卷标题
            hero: 主角设定（可复用）
            partner: 搭档设定（可复用）
            opponent_count: 对手数
            seed: 随机种子

        Returns:
            章节文本。
        """
        self.stats["start_time"] = time.time()

        ch = self.chapter_gen.generate(
            chapter_num=chapter_num,
            volume_title=volume_title,
            hero=hero,
            partner=partner,
            opponent_count=opponent_count,
            battle_rounds_per_pair=3,
            seed=seed,
            context_mgr=self.context,
            structure_fw=self.structure,
            constraint_engine=self.constraint_engine,
            drive_engine=(None, self.interaction_engine),
        )

        self.stats["total_chapters"] = 1
        self.stats["total_words"] = len(ch)
        self.stats["elapsed"] = time.time() - self.stats["start_time"]
        return ch

    # ───────────────── 整卷生成（VolumeGenerator 模式） ─────────────────

    def generate_volume(self,
                        volume_num: int = 1,
                        volume_title: str = "神秘领域",
                        chapters: int = 7,
                        opponents_per_chapter: int = 4) -> str:
        """生成完整一卷。

        Args:
            volume_num: 卷序号
            volume_title: 卷标题
            chapters: 卷内章数
            opponents_per_chapter: 每章对手数

        Returns:
            整卷文本。
        """
        self.stats["start_time"] = time.time()

        vol = self.vol_gen.generate(
            volume_num=volume_num,
            volume_title=volume_title,
            chapters=chapters,
            opponents_per_chapter=opponents_per_chapter,
            context_mgr=self.context,
            structure_fw=self.structure,
            constraint_engine=self.constraint_engine,
            drive_engine=(None, self.interaction_engine),
        )

        self.stats["elapsed"] = time.time() - self.stats["start_time"]
        self.stats["total_chapters"] = chapters
        self.stats["total_words"] = len(vol)
        self._print_stats()
        return vol

    # ───────────────── 工具方法 ─────────────────

    def generate_character(self, name: str = None,
                           surname: str = None) -> dict:
        """快捷生成一个角色。"""
        return self.char_gen.generate(name=name, surname=surname)

    def generate_battle(self, char_a: dict, char_b: dict,
                        rounds: int = 3,
                        terrain: str = "闪排骨溪") -> str:
        """快捷生成一场战斗。"""
        return self.battle_gen.generate_battle(
            char_a, char_b, rounds=rounds, terrain=terrain
        )

    def generate_dialogue(self, name_a: str, name_b: str,
                          skill_a: str, skill_b: str,
                          weapon_a: str, weapon_b: str,
                          treasure_a: str, treasure_b: str,
                          terrain: str) -> str:
        """快捷生成一段对话。"""
        return self.dialogue_gen.generate_exchange(
            name_a, name_b, skill_a, skill_b,
            weapon_a, weapon_b, treasure_a, treasure_b,
            terrain
        )

    def load_context(self, filepath: str):
        """加载上下文文件（断点续写）。"""
        self.context = ContextManager.load(filepath)

    def save_context(self, filepath: str):
        """保存上下文。"""
        self.context.save(filepath)

    def get_context_info(self) -> dict:
        """获取当前上下文摘要。"""
        return {
            "arc": self.context.get_arc(),
            "world": {k: self.context.get_world(k)
                      for k in ["time_of_day", "weather", "location"]},
            "characters": self.context.list_characters(),
        }

    def reset(self):
        """重置引擎状态。"""
        self.context = ContextManager()
        self.rhythm.reset()
        self.wb.clear_history()
        self.template.clear_vars()
        self.grammar.registry.clear_saved()

    def _print_stats(self):
        """打印统计信息。"""
        elapsed = self.stats["elapsed"]
        ch = self.stats["total_chapters"]
        words = self.stats["total_words"]
        if ch == 0:
            return
        print(f"\n{'='*60}")
        print(f"  生成完成！")
        print(f"  章节数：{ch}")
        print(f"  总字数：{words:,}")
        print(f"  耗时：{elapsed:.1f} 秒")
        print(f"  速度：{ch / elapsed:.1f} 章/秒, "
              f"{words / elapsed:.0f} 字/秒")
        print(f"{'='*60}")


# ───────────────── CLI 入口 ─────────────────

def main():
    parser = argparse.ArgumentParser(
        description="ASP 小说生成引擎 —— 多层嵌套循环 + 词库随机替换"
    )
    parser.add_argument(
        "--mode", choices=["full", "single", "volume"],
        default="single",
        help="生成模式：full=全量(巨校), single=单章, volume=整卷"
    )
    parser.add_argument("--volumes", type=int, default=20,
                        help="[full模式] 部数")
    parser.add_argument("--chapters", type=int, default=7,
                        help="[full/volume模式] 每卷章数")
    parser.add_argument("--chapter-num", type=int, default=1,
                        help="[single模式] 章序号")
    parser.add_argument("--volume-num", type=int, default=1,
                        help="[volume模式] 卷序号")
    parser.add_argument("--volume-title", type=str, default="未知领域",
                        help="卷标题")
    parser.add_argument("--seed", type=int, default=None,
                        help="随机种子（可复现）")
    parser.add_argument("--output", type=str, default=None,
                        help="输出文件/目录路径")
    parser.add_argument("--opponents", type=int, default=4,
                        help="每章对手数量")

    args = parser.parse_args()
    engine = ASPNovelEngine(seed=args.seed)

    if args.mode == "full":
        engine.generate_full_novel(
            volumes=args.volumes,
            chapters_per_volume=args.chapters,
            opponents_per_chapter=args.opponents,
            output_dir=args.output,
        )

    elif args.mode == "single":
        result = engine.generate_single_chapter(
            chapter_num=args.chapter_num,
            volume_title=args.volume_title,
            opponent_count=args.opponents,
            seed=args.seed,
        )
        # 输出
        output_path = args.output or str(
            OUTPUT_DIR / f"ch_{args.chapter_num}.txt"
        )
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"\n已输出至：{output_path}")
        print(f"字数：{len(result)}")
        print(f"\n--- 预览（前500字） ---")
        print(result[:500])

    elif args.mode == "volume":
        result = engine.generate_volume(
            volume_num=args.volume_num,
            volume_title=args.volume_title,
            chapters=args.chapters,
            opponents_per_chapter=args.opponents,
        )
        output_path = args.output or str(
            OUTPUT_DIR / f"vol_{args.volume_num}.txt"
        )
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"\n已输出至：{output_path}")


if __name__ == "__main__":
    main()
