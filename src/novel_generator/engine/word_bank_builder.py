# -*- coding: utf-8 -*-
"""词库批量扩充工具 —— 对标《宇宙巨校闪级生》万级词库规模。

宇宙巨校闪级生的核心优势之一是巨大的词库：
  1.7万+人物姓名 | 2.7万+怪物 | 海量形容词/动词/招式名

这些词汇来源推测是：
  1. 批量扫描古典名著提取（《西游记》《封神榜》等的神仙/法宝名）
  2. 手工编选的同义词/反义词词典
  3. 固定格式的姓名组合（姓氏×名字字的笛卡尔积）

本模块提供三个工具：
  1. 组合扩展器 —— 将已有词库的元素做笛卡尔积
  2. 文本扫描器 —— 从给定的文本文件中提取候选词汇
  3. 结构生成器 —— 按模板自动生成虚构词汇（功法名、技能名、地名）
"""

import re
import json
import random
import logging
from pathlib import Path
from typing import Optional, Iterator
from collections import Counter

_logger = logging.getLogger(__name__)


# ============================================================================
# 组合扩展器（笛卡尔积）
# ============================================================================

class CombinatorialExpander:
    """通过已有词库的笛卡尔积，指数级扩大词汇量。

    宇宙巨校闪级生的人物命名核心：姓氏×名字字 = 海量组合。
    """

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)

    def expand_cartesian(self, *word_lists: list[str],
                         max_count: int = 10000, sample: bool = False) -> list[str]:
        """对多个词表做笛卡尔积。

        expand_cartesian(["张","李","王"], ["三","四","五"])
        → ["张三","张四","张五","李三","李四","李五","王三","王四","王五"]
        """
        result = []
        import itertools
        for combo in itertools.product(*word_lists):
            result.append("".join(combo))
        if sample and len(result) > max_count:
            result = self._rng.sample(result, max_count)
        elif len(result) > max_count:
            result = result[:max_count]
        return result

    def expand_prefix_suffix(self, prefixes: list[str], suffixes: list[str],
                              max_count: int = 5000) -> list[str]:
        """前缀 × 后缀 = 新词。

        如 prefixes=["天","地","玄","黄"], suffixes=["剑","刀","枪","戟"]
        → ["天剑","天刀","天枪","天戟","地剑",...]
        """
        return self.expand_cartesian(prefixes, suffixes, max_count=max_count)

    def expand_pattern(self, pattern: str, slots: dict[str, list[str]],
                        count: int = 500) -> list[str]:
        """按模式生成词汇。

        pattern: "{prefix}之{suffix}" 或 "{adj}{noun}"
        slots: {"prefix": ["永恒","刹那"], "suffix": ["剑","盾"]}
        → ["永恒之剑","永恒之盾","刹那之剑","刹那之盾"]
        """
        keys = re.findall(r"\{(\w+)\}", pattern)
        if not keys:
            return [pattern]

        result = []
        import itertools
        for combo in itertools.product(*[slots.get(k, []) for k in keys]):
            text = pattern
            for k, v in zip(keys, combo):
                text = text.replace(f"{{{k}}}", v)
            result.append(text)
            if len(result) >= count:
                break
        return result


# ============================================================================
# 文本扫描器
# ============================================================================

class TextScanner:
    """从文本文件中提取词汇。

    可从《西游记》等名著提取人名、法宝名、地名、技能名。
    """

    # 常见的中文小说人物名模式
    NAME_PATTERNS = [
        re.compile(r"([\u4e00-\u9fff]{2,4})(?:道人|大师|长老|老祖|天尊|帝君|魔王)"),
        re.compile(r"(?:[姓名字号自称名叫唤作])([\u4e00-\u9fff]{2,3})"),
    ]

    # 法宝/兵器模式
    ARTIFACT_PATTERNS = [
        re.compile(r"([\u4e00-\u9fff]{2,4}(?:剑|刀|枪|戟|斧|钺|钩|叉|鞭|锏|锤|抓|棒|棍|环|圈|镜|印|瓶|葫芦|袋|塔|钟|鼎|幡|图|珠|帕|绫|索|拂尘))"),
        re.compile(r"([\u4e00-\u9fff]{2,3}(?:塔|镜|钟|鼎|幡|图|珠|印))"),
    ]

    # 技能/功法模式
    SKILL_PATTERNS = [
        re.compile(r"([\u4e00-\u9fff]{2,4}(?:功|法|诀|术|经|典|录|谱|篇|书|章|卷))"),
        re.compile(r"([\u4e00-\u9fff]{2,3}(?:大法|神功|仙术|秘诀|宝典))"),
    ]

    def scan_file(self, filepath: Path, category: str = "names") -> list[str]:
        """扫描单个文件，按类别提取词汇。"""
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
        return self._extract(text, category)

    def scan_directory(self, directory: Path, category: str = "names",
                       min_count: int = 2) -> list[str]:
        """扫描目录下所有文本文件，提取高频词汇。"""
        counter = Counter()
        for txt_file in directory.glob("**/*.txt"):
            try:
                words = self.scan_file(txt_file, category)
                counter.update(words)
            except Exception as e:
                _logger.warning(f"扫描失败 {txt_file}: {e}")

        # 返回出现频次 >= min_count 的词汇
        return [w for w, c in counter.most_common() if c >= min_count]

    def _extract(self, text: str, category: str) -> list[str]:
        patterns = {
            "names": self.NAME_PATTERNS,
            "artifacts": self.ARTIFACT_PATTERNS,
            "skills": self.SKILL_PATTERNS,
        }
        result = []
        for pattern in patterns.get(category, []):
            for m in pattern.finditer(text):
                word = m.group(1)
                # 过滤太短或太长的
                if 2 <= len(word) <= 6:
                    result.append(word)
        return result


# ============================================================================
# 结构生成器
# ============================================================================

class StructureGenerator:
    """按模板自动生成虚构词汇。

    宇宙巨校闪级生中有大量规则化的虚构名称：
    功法名、巨校名、怪物名、宝物名等。
    """

    GENERATORS = {
        "skill_name": {
            "description": "功法/技能名",
            "template": "{num}{element}{style}{type}",
            "slots": {
                "num": ["一", "二", "三", "四", "五", "六", "七", "八", "九",
                        "十", "百", "千", "万", "大", "小", "太", "元", "玄"],
                "element": ["金", "木", "水", "火", "土", "风", "雷", "光", "暗",
                            "冰", "炎", "毒", "魂", "血", "星", "月", "日", "空"],
                "style": ["灵", "圣", "仙", "神", "魔", "妖", "鬼", "龙", "凤",
                          "天", "地", "真", "混", "太", "上", "玉", "紫", "青"],
                "type": ["功", "法", "诀", "术", "经", "录", "篇", "谱", "卷"],
            },
        },
        "school_name": {
            "description": "巨校/宗门名",
            "template": "{domain}{school}",
            "slots": {
                "domain": ["厨艺", "包装", "战斗", "音乐", "魔法", "科技",
                          "制药", "驯兽", "机关", "幻术", "符文", "星象",
                          "制符", "炼丹", "炼器", "阵法", "剑道", "刀法",
                          "医术", "毒术", "傀儡", "占卜", "鬼道", "佛门"],
                "school": ["巨校", "学院", "宗", "门", "派", "道场", "山", "谷",
                          "洞", "堂", "阁", "楼", "院", "观", "寺", "庵"],
            },
        },
        "artifact_name": {
            "description": "法宝/神器名",
            "template": "{adj}{artifact}",
            "slots": {
                "adj": ["混元", "太初", "混沌", "太极", "两仪", "三才", "四象",
                       "五行", "六合", "七星", "八卦", "九宫", "十方", "灭世",
                       "创世", "永恒", "刹那", "无尽", "虚空", "破灭", "重生"],
                "artifact": ["剑", "刀", "枪", "戟", "锤", "鞭", "珠", "印",
                            "镜", "钟", "鼎", "幡", "图", "塔", "炉", "瓶",
                            "扇", "笔", "尺", "绫", "索", "拂尘", "如意"],
            },
        },
    }

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)

    def generate(self, category: str, count: int = 100,
                 unique: bool = True) -> list[str]:
        """按类别生成虚构词汇。"""
        config = self.GENERATORS.get(category)
        if not config:
            _logger.warning(f"未知类别: {category}")
            return []

        template = config["template"]
        slots = config["slots"]

        if unique:
            seen = set()
            result = []
            attempts = 0
            while len(result) < count and attempts < count * 10:
                word = self._fill(template, slots)
                if word not in seen:
                    seen.add(word)
                    result.append(word)
                attempts += 1
            return result
        else:
            return [self._fill(template, slots) for _ in range(count)]

    def generate_all_categories(self, count_per: int = 50) -> dict[str, list[str]]:
        """生成所有类别的词汇。"""
        return {
            cat: self.generate(cat, count=count_per)
            for cat in self.GENERATORS
        }

    def _fill(self, template: str, slots: dict[str, list[str]]) -> str:
        result = template
        for key, values in slots.items():
            result = result.replace(f"{{{key}}}", self._rng.choice(values))
        return result


# ============================================================================
# 词库导出工具
# ============================================================================

class WordBankExporter:
    """将生成的词汇批量导出为 WordBank 兼容的 JSON 文件。"""

    @staticmethod
    def export_to_file(words: list[str], filepath: Path, key: str):
        """将词汇列表导出为词库JSON文件。

        格式: {"key": ["词1", "词2", ...]}
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        data[key] = list(dict.fromkeys(words))  # 去重保序
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def create_bank_from_categories(
        output_dir: Path,
        categories: dict[str, list[str]],
    ):
        """将多个类别的词汇分别导出为词库文件。"""
        output_dir.mkdir(parents=True, exist_ok=True)
        for category, words in categories.items():
            filepath = output_dir / f"{category}.json"
            WordBankExporter.export_to_file(words, filepath, category)
            print(f"  → {filepath.name}: {len(words)} 个词")

    @staticmethod
    def merge_banks(source_dirs: list[Path], output_dir: Path):
        """合并多个词库目录到一个输出目录。"""
        output_dir.mkdir(parents=True, exist_ok=True)
        for src_dir in source_dirs:
            for json_file in src_dir.glob("*.json"):
                dest = output_dir / json_file.name
                if dest.exists():
                    with open(json_file, "r", encoding="utf-8") as f:
                        src_data = json.load(f)
                    with open(dest, "r", encoding="utf-8") as f:
                        dest_data = json.load(f)
                    # 合并
                    for key, vals in src_data.items():
                        if key in dest_data:
                            dest_data[key] = list(dict.fromkeys(
                                dest_data[key] + vals
                            ))
                        else:
                            dest_data[key] = vals
                    with open(dest, "w", encoding="utf-8") as f:
                        json.dump(dest_data, f, ensure_ascii=False, indent=2)
                else:
                    import shutil
                    shutil.copy2(json_file, dest)


# ============================================================================
# 一键扩展
# ============================================================================

def expand_word_bank(
    wb_dir: Path,
    target_total: int = 50000,
    seed: int = 42,
) -> dict[str, int]:
    """一键扩展词库到指定总数。

    返回每个词库文件新增的词汇数。
    """
    rng = random.Random(seed)
    expander = CombinatorialExpander(seed=seed)
    generator = StructureGenerator(seed=seed + 1)
    exporter = WordBankExporter()
    added = {}

    # 1. 生成虚构名称
    for category, words in generator.generate_all_categories(count_per=500).items():
        filepath = wb_dir / f"{category}.json"
        exporter.export_to_file(words, filepath, category)
        added[category] = len(words)

    # 2. 对现有词库做笛卡尔积扩展
    existing = {}
    for f in wb_dir.glob("*.json"):
        if f.stem in added:
            continue  # 刚才已经新建的不重复
        try:
            with open(f, "r", encoding="utf-8") as fp:
                existing.update(json.load(fp))
        except Exception:
            pass

    # 如果existing中有surnames和given_name_chars，做笛卡尔积
    if "surnames" in existing and "given_name_chars" in existing:
        names = expander.expand_cartesian(
            existing["surnames"],
            existing["given_name_chars"],
            max_count=50000, sample=True,
        )
        exporter.export_to_file(names, wb_dir / "generated_names.json", "full_names")
        added["generated_names"] = len(names)

    return added


# ============================================================================
# 自检
# ============================================================================
if __name__ == "__main__":
    import tempfile

    print("=" * 60)
    print("词库批量扩充工具 - 自检")
    print("=" * 60)

    # 1. 组合扩展器
    print("\n[组合扩展器]")
    ce = CombinatorialExpander(seed=42)
    results = ce.expand_cartesian(
        ["张", "李", "王"],
        ["天", "地", "玄"],
        max_count=10,
    )
    print(f"  3×3 → {len(results)} 组合: {results[:5]}...")

    # 2. 结构生成器
    print("\n[结构生成器]")
    sg = StructureGenerator(seed=42)
    skills = sg.generate("skill_name", count=5)
    schools = sg.generate("school_name", count=5)
    print(f"  技能名: {skills}")
    print(f"  宗门名: {schools}")

    # 3. 导出测试
    print("\n[词库导出]")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        exporter = WordBankExporter()
        exporter.export_to_file(skills, tmp / "test_skills.json", "skills")
        with open(tmp / "test_skills.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"  导出成功: {tmp}/test_skills.json, 键: {list(data.keys())}")

    # 4. 模式生成
    print("\n[模式生成]")
    patterned = ce.expand_pattern(
        "{adj}之{obj}",
        {"adj": ["永恒", "刹那", "无尽"], "obj": ["剑", "盾", "矛"]},
    )
    print(f"  3×3 → {patterned}")

    print(f"\n全部自检通过 [OK]")
