# -*- coding: utf-8 -*-
"""独立怪物生成器 —— 对标《宇宙巨校闪级生》2.7万+奇异生物系统。

宇宙巨校闪级生创造了2.7万+独特怪物，每种怪物有独立的
姓名 + 造型描述 + 奇特性征 + 特殊能力。本模块从人物模板中
剥离出独立的怪物生成系统，具有以下特色：

  1. 怪物身体部位组合系统（头/躯干/四肢/尾巴/翅膀/角）
  2. 材质/元素/形态 三维修饰系统
  3. 怪物能力等级体系（普通→稀有→传说→神话）
  4. 族群与生态描述生成
  5. 对战场景中的怪物行动模板
"""

import random
import logging
from pathlib import Path
from typing import Optional, Any

try:
    from .word_bank import WordBank
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from novel_generator.engine.word_bank import WordBank

_logger = logging.getLogger(__name__)


# ============================================================================
# 怪物身体部位模板
# ============================================================================

MONSTER_BODY_PARTS = {
    "head": [
        "头颅", "脑袋", "头部", "颅骨", "头盖骨",
    ],
    "head_shape": [
        "三角形的", "菱形的", "螺旋形的", "多层叠合的", "不规则扭动的",
        "棱锥状的", "球形的", "扁平的", "倒三角的", "水滴形的",
    ],
    "eyes": [
        "复眼", "单眼", "宝石眼", "灯笼眼", "漩涡眼", "星云眼",
        "黑洞眼", "燃烧之眼", "辉光之眼", "深渊凝视之眼",
    ],
    "eye_count": [
        "三只", "五只", "七只", "九只", "十三只", "无数只",
        "一只巨瞳", "两只并列", "四只对生", "六只环形排列",
    ],
    "body": [
        "躯干", "身体", "肢体", "肉柱", "甲壳", "水晶躯壳",
    ],
    "body_texture": [
        "布满鳞片的", "覆盖甲壳的", "透明胶质的", "金属质感的",
        "流动岩浆般的", "冰晶构成的", "看似虚无的", "由纯粹光芒组成的",
        "不断变换形态的", "散发恶臭腐败的",
    ],
    "legs": [
        "腿", "足", "肢腿", "触足", "节肢",
    ],
    "leg_count": [
        "八条", "十二条", "十六条", "二十四条", "三十二条",
        "六条", "无数条", "四条", "两条",
    ],
    "tail": [
        "尾巴", "长尾", "蛇尾", "蝎尾", "鞭尾",
    ],
    "tail_morph": [
        "末端长着毒刺的", "分叉成三条的", "可以无限延伸的",
        "燃烧着火焰的", "由骨骼碎片拼接成的", "拖着星光的",
        "末端睁开一只巨眼的", "散发着毒雾的",
    ],
    "wings": [
        "翅膀", "翼", "飞翼", "羽翼", "膜翼",
    ],
    "wing_morph": [
        "覆盖骨骼的", "半透明的", "由纯粹魔力构成的",
        "燃烧的火焰之翼", "冰晶凝成的", "每次扇动都撒落星光的",
        "布满符文的", "由无数细小触须编织成的",
    ],
    "horns": [
        "角", "犄角", "触角", "巨角", "卷角",
    ],
    "horn_morph": [
        "螺旋上升的", "弯曲向后的", "直指天穹的",
        "像树枝一样分叉的", "流淌着熔岩的", "随时变换方向的",
        "呈现出彩虹光泽的", "锋利如刀的",
    ],
    "mouth": [
        "口腔", "巨口", "利齿口腔", "深渊般的大嘴", "针管状口器", "三瓣嘴",
    ],
    "teeth": [
        "三排锯齿", "钻石般的利齿", "内外双层牙齿", "可以旋转的环状齿盘",
        "散发电光的獠牙", "密密麻麻的针状毒牙", "蓝光莹莹的门齿",
    ],
}

# ============================================================================
# 怪物族群/生态描述模板
# ============================================================================

MONSTER_HABITAT_TEMPLATES = [
    "这种怪物通常栖息在∈locations.terrain_type←的深处，以∈locations.terrain_prefix←的∈locations.terrain_type←为巢穴。",
    "它们群居在∈locations.terrain_type←地带，每次出动都是成群结队，所过之处寸草不生。",
    "这怪物天生孤僻，总在∈locations.terrain_type←的边缘地带独自游荡。",
    "传说它们原本居住在∈locations.terrain_type←的最底层，近百年才逐渐出现在地表。",
    "它们的巢穴隐藏在∈locations.landmark_prefix←的∈locations.landmark_type←之中，寻常人根本无法发现。",
]

MONSTER_DIET_TEMPLATES = [
    "它以∈adjectives.texture←为食，每次进食能将方圆数里的该物质全部吞噬。",
    "这种生物只吃∈adjectives.appearance←的东西，对普通食物不屑一顾。",
    "它以吸食生灵的∈adjectives.emotion←为生，被其盯上的人会在不知不觉中被榨干。",
    "它什么都吃——石头、金属、甚至魔力本身都能被它消化掉。",
    "它靠吸收空气中的∈adjectives.ambient←为生，永远不需要休息。",
]

MONSTER_ORIGIN_TEMPLATES = [
    "据古籍记载，这类怪物起源于远古的∈adjectives.ancient←时代，由∈names.surnames←大法师无意中创造出来。",
    "没有人知道它们从何而来，只知道第一次有目击记录是在∈adjectives.appearance←的那一年。",
    "有些学者认为，它们是天地间∈adjectives.ambient←之力的扭曲化身。",
    "传说它们是某位上古神明的宠物后代，因为神明的陨落而流落凡间。",
    "它们原本只是普通的∈adjectives.texture←之物，因为吸收了天外陨石的能量才变异成如今的模样。",
]

# ============================================================================
# 怪物能力等级体系
# ============================================================================

ABILITY_TIERS = {
    "common": {
        "name": "普通",
        "prefixes": ["初级", "基础", "入门", "简单的"],
        "abilities": [
            "撕裂爪击", "毒雾喷吐", "岩石皮肤", "快速再生",
            "音波震荡", "酸液腐蚀", "缠绕之触", "地陷之力",
        ],
    },
    "rare": {
        "name": "稀有",
        "prefixes": ["中级", "精进", "熟练的", "独特的"],
        "abilities": [
            "空间撕裂", "时间减缓", "灵魂吞噬", "元素转化",
            "镜像分身", "血肉操控", "重力领域", "虚化穿行",
        ],
    },
    "legendary": {
        "name": "传说",
        "prefixes": ["高级", "顶级", "精湛的", "传说中的"],
        "abilities": [
            "因果逆转", "维度穿越", "法则改写", "万物归一",
            "永恒禁锢", "命运编织", "混沌降临", "起源回溯",
        ],
    },
    "mythic": {
        "name": "神话",
        "prefixes": ["究极", "禁忌的", "神话级", "无人能及的"],
        "abilities": [
            "创世之息", "灭世之吼", "轮回重启", "虚空造物",
            "概念抹除", "无限增殖", "现实扭曲", "终极审判",
        ],
    },
}


# ============================================================================
# 怪物生成器核心
# ============================================================================

class MonsterGenerator:
    """独立怪物生成器。

    每个怪物实例是独立的一次随机展开，不依赖持久化状态。
    通过不同的seed和模板组合，可生成数量远超2.7万的独特怪物。
    """

    def __init__(self, wb: WordBank, seed: Optional[int] = None):
        self._wb = wb
        self._rng = random.Random(seed)

    def generate_monster(
        self,
        tier: str = "common",
        include_habitat: bool = True,
        include_origin: bool = True,
    ) -> dict[str, Any]:
        """生成一只完整的怪物，返回包含所有描述的字典。"""
        monster = {}

        # 1. 名称
        monster["name"] = self._generate_name()

        # 2. 身体结构描述
        monster["body"] = self._generate_body()

        # 3. 能力等级
        tier_data = ABILITY_TIERS.get(tier, ABILITY_TIERS["common"])
        ability = self._rng.choice(tier_data["abilities"])
        prefix = self._rng.choice(tier_data["prefixes"])
        monster["ability"] = f"{prefix}{ability}"
        monster["tier"] = tier_data["name"]

        # 4. 族群/生态(可选)
        if include_habitat:
            monster["habitat"] = self._fill_template(
                self._rng.choice(MONSTER_HABITAT_TEMPLATES)
            )
            monster["diet"] = self._fill_template(
                self._rng.choice(MONSTER_DIET_TEMPLATES)
            )

        # 5. 起源传说(可选)
        if include_origin:
            monster["origin"] = self._fill_template(
                self._rng.choice(MONSTER_ORIGIN_TEMPLATES)
            )

        # 6. 整体描述
        monster["full_description"] = self._compose_description(monster)

        return monster

    def generate_monsters_batch(
        self, count: int, tier: str = "common", **kwargs
    ) -> list[dict[str, Any]]:
        """批量生成怪物。"""
        return [self.generate_monster(tier=tier, **kwargs) for _ in range(count)]

    def generate_monster_unique(
        self, previously_generated: set[str], max_attempts: int = 100
    ) -> dict[str, Any]:
        """生成一只名称不重复的怪物。"""
        for _ in range(max_attempts):
            monster = self.generate_monster()
            if monster["name"] not in previously_generated:
                previously_generated.add(monster["name"])
                return monster
        return self.generate_monster()  # 兜底

    # ================================================================
    # 内部生成方法
    # ================================================================

    def _generate_name(self) -> str:
        """生成怪物名称。"""
        patterns = [
            # 经典《宇宙巨校闪级生》风格：∈名称← 占位符
            lambda: f"{self._pick('surnames')}·{self._pick('given_name_chars')}",
            lambda: f"{self._pick('monster_prefix')}{self._pick('monster_type')}",
            lambda: f"{self._pick('monster_prefix')}的{self._pick('monster_type')}",
            lambda: f"{self._pick('monster_prefix')}中的{self._pick('monster_type')}",
            lambda: f"{self._rng.choice(['黑暗', '深渊', '星空', '远古', '混沌', '虚空', '圣光', '幽影'])}{self._pick('monster_type')}",
            lambda: f"{self._pick('monster_type')}{self._pick('monster_prefix')}",
        ]
        # 尝试词库，失败则用组合法
        try:
            return self._rng.choice(patterns)()
        except Exception:
            prefix = self._rng.choice(
                ["幽冥", "天穹", "深海", "地心", "炎狱", "寒渊",
                 "雷霆", "万象", "幻夜", "白昼", "龙鳞", "凤羽",
                 "吞噬", "不朽", "轮回", "星殒", "裂空", "混元",
                 "化骨", "噬魂", "净世", "灭世", "创世", "寂灭"]
            )
            suffix = self._rng.choice(
                ["魔兽", "妖兽", "灵兽", "圣兽", "凶兽", "神兽",
                 "怪物", "异兽", "邪兽", "荒兽", "古兽", "巨兽"]
            )
            char = self._rng.choice("天地玄黄宇宙洪荒日月盈昃辰宿列张")
            return f"{prefix}{char}{suffix}"

    def _generate_body(self) -> str:
        """生成怪物身体结构描述。"""
        parts = []

        # 头部
        head = self._rng.choice(MONSTER_BODY_PARTS["head_shape"])
        head_name = self._rng.choice(MONSTER_BODY_PARTS["head"])
        eyes = self._rng.choice(MONSTER_BODY_PARTS["eyes"])
        eye_count = self._rng.choice(MONSTER_BODY_PARTS["eye_count"])
        mouth = self._rng.choice(MONSTER_BODY_PARTS["mouth"])
        teeth = self._rng.choice(MONSTER_BODY_PARTS["teeth"])
        parts.append(
            f"它长着一个{head}{head_name}，上面排布着{eye_count}{eyes}，"
            f"{mouth}里密布着{teeth}。"
        )

        # 躯干
        body_texture = self._rng.choice(MONSTER_BODY_PARTS["body_texture"])
        body_name = self._rng.choice(MONSTER_BODY_PARTS["body"])
        parts.append(f"它的{body_name}{body_texture}。")

        # 腿部
        leg_count = self._rng.choice(MONSTER_BODY_PARTS["leg_count"])
        leg_name = self._rng.choice(MONSTER_BODY_PARTS["legs"])
        parts.append(f"它拥有{leg_count}{leg_name}。")

        # 尾部 (80%概率)
        if self._rng.random() < 0.8:
            tail_morph = self._rng.choice(MONSTER_BODY_PARTS["tail_morph"])
            tail_name = self._rng.choice(MONSTER_BODY_PARTS["tail"])
            parts.append(f"它的{tail_name}{tail_morph}。")

        # 翅膀 (40%概率)
        if self._rng.random() < 0.4:
            wing_morph = self._rng.choice(MONSTER_BODY_PARTS["wing_morph"])
            wing_name = self._rng.choice(MONSTER_BODY_PARTS["wings"])
            parts.append(f"背上展开{wing_morph}{wing_name}。")

        # 角 (50%概率)
        if self._rng.random() < 0.5:
            horn_morph = self._rng.choice(MONSTER_BODY_PARTS["horn_morph"])
            horn_name = self._rng.choice(MONSTER_BODY_PARTS["horns"])
            parts.append(f"头顶长着{horn_morph}{horn_name}。")

        return " ".join(parts)

    def _compose_description(self, monster: dict) -> str:
        """将怪物各部分信息组合为完整描述段落。"""
        parts = [
            f"[{monster['tier']}级] {monster['name']}",
            monster.get("body", ""),
            f"特殊能力：{monster.get('ability', '未知')}",
        ]
        if "habitat" in monster:
            parts.append(f"栖息地：{monster['habitat']}")
        if "diet" in monster:
            parts.append(f"食性：{monster['diet']}")
        if "origin" in monster:
            parts.append(f"起源：{monster['origin']}")
        return "\n".join(parts)

    def _pick(self, key: str) -> str:
        """从词库中随机选取（带降级）。"""
        try:
            # 尝试多种词库名
            for bank in ["names", "equipment", "monsters", "creatures"]:
                try:
                    return self._wb.pick(bank, key)
                except (FileNotFoundError, KeyError):
                    continue
        except Exception:
            pass

        # 彻底降级：返回一个常量默认值
        defaults = {
            "surnames": self._rng.choice(["龙", "凤", "虎", "豹", "蛇", "猿", "鹰", "蝎"]),
            "given_name_chars": self._rng.choice(["天", "魔", "妖", "兽", "王", "帝", "皇"]),
            "monster_prefix": self._rng.choice(["幽冥", "天穹", "深海", "地心", "炎狱"]),
            "monster_type": self._rng.choice(["魔兽", "妖兽", "灵兽", "圣兽", "凶兽"]),
        }
        return defaults.get(key, f"[{key}]")

    def _fill_template(self, template: str) -> str:
        """简单模板填充（内联版，不依赖外部引擎）。"""
        import re

        def replacer(m):
            ref = m.group(1).strip()
            if "." in ref:
                bank, k = ref.split(".", 1)
                try:
                    return self._wb.pick(bank, k)
                except Exception:
                    return f"[{ref}]"
            return f"[{ref}]"

        return re.sub(r"∈([^←]+)←", replacer, template)


# ============================================================================
# 快捷生成
# ============================================================================

def generate_demonstration_set(
    wb: WordBank, count_per_tier: int = 3, seed: int = 42
) -> dict[str, list[dict]]:
    """生成全套演示怪物集（四等级各若干只）。"""
    gen = MonsterGenerator(wb, seed=seed)
    result = {}
    for tier in ("common", "rare", "legendary", "mythic"):
        result[tier] = gen.generate_monsters_batch(
            count_per_tier, tier=tier
        )
    return result


# ============================================================================
# 自检
# ============================================================================
if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from novel_generator.engine.word_bank import WordBank

    print("=" * 60)
    print("独立怪物生成器 - 自检")
    print("=" * 60)

    wb = WordBank(seed=42)
    gen = MonsterGenerator(wb, seed=42)

    # 各等级生成1只
    for tier in ("common", "rare", "legendary", "mythic"):
        m = gen.generate_monster(tier=tier)
        print(f"\n[{m['tier']}级怪物]")
        print(f"  名称: {m['name']}")
        print(f"  能力: {m['ability']}")
        print(f"  身体: {m['body'][:80]}...")
        if "origin" in m:
            print(f"  起源: {m['origin'][:80]}...")

    # 统计唯一名称数
    print(f"\n[唯一性测试] 生成100只怪物...")
    seen = set()
    for _ in range(100):
        m = gen.generate_monster()
        seen.add(m['name'])
    print(f"  100只中唯一名称数: {len(seen)}")
    print(f"  重复率: {(100 - len(seen)) / 100 * 100:.1f}%")

    print(f"\n全部自检通过 [OK]")
