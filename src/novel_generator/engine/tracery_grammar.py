"""Tracery 语法的 ASP 适配器（增强版）。

支持三种语法模式：
1. Classic {{bank.key}} — 已有基本语法
2. ★ Tracery JSON Grammar — 动态注册语法规则
3. ★ 组合语法 — 语法模块可以互相引用和嵌套

新增能力：
- ★ 动态语法注册表（GrammarRegistry）
- ★ 权重语法规则（#rule# 支持加权分支）
- ★ 情感适配（根据情绪状态选择不同的语法分支）
- ★ 世界特定语法包（不同世界/场景使用不同语法集）
- ★ 语法模块组合（多个语法包合并使用）
"""

import random
import re
from typing import Optional, Callable, Union


# ───────────────── Tracery 标记解析 ─────────────────

_TRACERY_RULE_RE = re.compile(r"#(\w+)#")
_TRACERY_MOD_RE = re.compile(r"#(\w+)\.(\w+)#")  # #rule.modifier#
_TRACERY_ACTION_RE = re.compile(r"\[(\w+):#(\w+)#\]")    # [action:#rule#]
_TRACERY_PUSH_RE = re.compile(r"\[(\w+)\s*<-\s*#(\w+)#\]")  # [var <- #rule#]


class GrammarRegistry:
    """动态语法注册表：注册、组合、解析 Tracery 风格的语法规则。

    每条规则是一个字符串列表（随机选一），或带权重的分支列表。
    """

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)
        self._grammars: dict[str, dict] = {}  # namespace → {rule → [branches]}
        self._saved: dict[str, str] = {}  # 保存的变量
        self._active_namespace: str = "default"

    # ───── 注册 ─────

    def register(self, rules: dict, namespace: str = None):
        """注册一组语法规则。

        rules 格式：
        {
            "origin": ["开头句1", "开头句2"],
            "emotion": [
                {"text": "喜悦的句子", "weight": 3, "tag": "joy"},
                {"text": "悲伤的句子", "weight": 1, "tag": "sad"},
            ],
        }
        """
        ns = namespace or self._active_namespace
        if ns not in self._grammars:
            self._grammars[ns] = {}
        self._grammars[ns].update(rules)
        self._active_namespace = ns

    def register_from_json(self, json_data: dict,
                           namespace: str = None):
        """从 JSON 字典注册语法规则。"""
        ns = namespace or self._active_namespace
        if ns not in self._grammars:
            self._grammars[ns] = {}

        for rule_name, branches in json_data.items():
            if isinstance(branches, list):
                self._grammars[ns][rule_name] = branches
            elif isinstance(branches, str):
                self._grammars[ns][rule_name] = [branches]

    def merge_namespace(self, source_ns: str, target_ns: str = None):
        """合并两个命名空间的规则。"""
        target = target_ns or self._active_namespace
        if source_ns not in self._grammars:
            raise KeyError(f"命名空间 '{source_ns}' 不存在")
        if target not in self._grammars:
            self._grammars[target] = {}
        self._grammars[target].update(self._grammars[source_ns])

    def use_namespace(self, namespace: str):
        """设置当前活跃命名空间。"""
        self._active_namespace = namespace

    # ───── 解析 ─────

    def _pick_branch(self, branches: list, emotion: str = None) -> str:
        """从分支列表中按权重（或情绪标签）选取一项。"""
        if not branches:
            return ""

        # 带权重格式
        if isinstance(branches[0], dict):
            if emotion:
                # 按情绪标签过滤
                tagged = [b for b in branches if b.get("tag") == emotion]
                if tagged:
                    branches = tagged
            texts = [b["text"] for b in branches]
            weights = [b.get("weight", 1) for b in branches]
            return self._rng.choices(texts, weights=weights, k=1)[0]

        # 普通字符串列表
        return self._rng.choice(branches)

    def resolve_rule(self, rule_name: str, emotion: str = None,
                     depth: int = 0) -> str:
        """解析一个语法规则，返回展开后的文本。

        递归展开规则中嵌入的其他 #sub_rule#。
        先在活跃命名空间查找，再向其他命名空间搜索作为回退。
        """
        if depth > 20:  # 递归深度限制
            return f"[递归溢出:#{rule_name}#]"

        ns = self._active_namespace
        rules = self._grammars.get(ns, {})

        # 如果活跃命名空间中找不到，搜索所有命名空间作为回退
        if rule_name not in rules:
            for other_ns, other_rules in self._grammars.items():
                if rule_name in other_rules:
                    rules = other_rules
                    break
            else:
                return f"[缺失:#{rule_name}#]"

        branches = rules[rule_name]
        raw = self._pick_branch(branches, emotion=emotion)

        # 递归展开嵌入的规则
        def sub_resolver(match):
            sub_rule = match.group(1)
            return self.resolve_rule(sub_rule, emotion=emotion,
                                     depth=depth + 1)

        result = _TRACERY_RULE_RE.sub(sub_resolver, raw)

        # 展开变量引用
        result = self._expand_saved_vars(result)

        return result

    def _expand_saved_vars(self, text: str) -> str:
        """展开已保存的变量。"""
        def replacer(match):
            var_name = match.group(1)
            return self._saved.get(var_name, f"[var:{var_name}]")
        return _TRACERY_ACTION_RE.sub(replacer, text)

    # ───── 保存 / 动作 ─────

    def save(self, var_name: str, value: str):
        """保存一个变量值。"""
        self._saved[var_name] = value

    def get_saved(self, var_name: str, default: str = "") -> str:
        """获取已保存的变量值。"""
        return self._saved.get(var_name, default)

    def clear_saved(self):
        """清除所有已保存变量。"""
        self._saved.clear()

    # ───── 辅助 ─────

    def list_namespaces(self) -> list[str]:
        """列出所有命名空间。"""
        return list(self._grammars.keys())

    def list_rules(self, namespace: str = None) -> list[str]:
        """列出指定命名空间的所有规则名。"""
        ns = namespace or self._active_namespace
        return list(self._grammars.get(ns, {}).keys())


# ───────────────── Tracery ASP 适配器 ─────────────────


class TraceryAdapter:
    """Tracery 语法 → ASP 词库 的适配器。

    让 Tracery 语法规则可以直接引用 ASP 词库的条目：
    - #bank_key# 自动路由到 WordBank.pool(bank, key)
    - #emotion_# 读取 ContextManager 中的情绪状态
    """

    def __init__(self, word_bank, context_manager=None,
                 seed: Optional[int] = None):
        self.wb = word_bank  # WordBank 实例
        self.cm = context_manager  # ContextManager 实例（可选）
        self.registry = GrammarRegistry(seed=seed)
        self._rng = random.Random(seed)
        # 注册 ASP 词库映射规则
        self._register_asp_mappings()

    def _register_asp_mappings(self):
        """将 ASP 词库自动映射为 Tracery 语法规则。"""
        # 遍历所有已加载词库，为每个 bank.key 创建 Tracery 规则
        pass  # 延迟注册，在 resolve 时动态查找

    def resolve(self, text: str, emotion: str = None) -> str:
        """解析文本中的 Tracery 标记 #rule#。

        优先级：
        1. GrammarRegistry 中已注册的规则
        2. ASP 词库 (bank_key)
        3. 原样返回（找不到规则）
        """
        def replacer(match):
            rule_name = match.group(1)

            # 处理带修饰符的规则 #rule.modifier#
            if '.' in rule_name:
                parts = rule_name.split('.', 1)
                rule_name = parts[0]

            # 1. 检查 GrammarRegistry
            try:
                return self.registry.resolve_rule(rule_name,
                                                   emotion=emotion)
            except KeyError:
                pass

            # 2. 检查 ASP 词库映射
            if '_' in rule_name:
                bank, key = rule_name.split('_', 1)
                try:
                    pool = self.wb.pool(bank, key)
                    if pool:
                        return self._rng.choice(pool)
                except (FileNotFoundError, KeyError):
                    pass

            # 3. 保底
            return f"#{rule_name}#"

        return _TRACERY_RULE_RE.sub(replacer, text)

    def register_preset_grammars(self):
        """注册预设的中文小说常用语法模块。"""

        # 动作描写
        self.registry.register({
            "action_start": [
                "他#action_verb#地#action_motion#",
                "#body_part#一动，#action_result#",
                "只见他#action_verb#，身形#movement_style#",
            ],
            "action_verb": [
                {"text": "猛然", "weight": 3},
                {"text": "缓缓", "weight": 2},
                {"text": "急速", "weight": 2},
                {"text": "轻轻", "weight": 2},
            ],
            "action_motion": [
                "向前踏出一步",
                "转身回首",
                "跃上半空",
                "挥出手臂",
                "凝神注视",
            ],
        }, namespace="combat")

        # 心理描写
        self.registry.register({
            "inner_thought": [
                "#pronoun#心中暗想：#thought_content#",
                "#pronoun#心头一凛，只觉#feeling_desc#",
                "一种#emotion_desc#的情绪涌上#pronoun#的心头",
            ],
            "emotion_desc": [
                "说不出的",
                "难以言喻的",
                "强烈的",
                "淡淡的",
                "莫名的",
            ],
            "feeling_desc": [
                "一阵寒意",
                "热血沸腾",
                "心乱如麻",
                "如释重负",
                "百感交集",
            ],
        }, namespace="psychology")

        # 环境描写
        self.registry.register({
            "env_open": [
                "#time_prefix#，#weather_desc#。",
                "#location_prefix#，#env_detail#。",
                "放眼望去，#landscape_desc#。",
            ],
            "time_prefix": [
                "天色渐明",
                "夕阳西下",
                "夜幕降临",
                "正午时分",
                "晨光熹微",
            ],
            "weather_desc": [
                "微风轻拂，树叶沙沙作响",
                "细雨蒙蒙，天地间一片朦胧",
                "骄阳似火，热浪滚滚",
                "寒风凛冽，雪花纷飞",
            ],
            "location_prefix": [
                "此处",
                "放眼四周",
                "环顾左右",
                "立于高处",
                "驻足细看",
            ],
            "env_detail": [
                "古木参天，藤萝密布",
                "怪石嶙峋，奇花异草丛生",
                "一片荒芜，寸草不生",
                "宫殿巍峨，金碧辉煌",
            ],
            "landscape_desc": [
                "群山连绵，云雾缭绕",
                "大江奔流，气势磅礴",
                "平原辽阔，一望无际",
                "密林深处，幽暗寂静",
            ],
        }, namespace="environment")

        # 对话框架
        self.registry.register({
            "dialogue_frame": [
                "#speaker_name##speaker_action#道："#dialogue_content#\"",
                "\"#dialogue_content#\"#speaker_name##speaker_action#地说道。",
                "#speaker_name#目光#eye_action#，缓缓道："#dialogue_content#\"",
            ],
            "speaker_action": [
                "微微一笑",
                "眉头紧锁",
                "叹了口气",
                "目光闪烁",
                "神色凝重",
                "冷笑一声",
            ],
            "eye_action": [
                "炯炯有神",
                "黯淡无光",
                "闪烁不定",
                "锐利如刀",
                "温柔似水",
            ],
        }, namespace="dialogue")

        # 战斗描写
        self.registry.register({
            "combat_sequence": [
                "#combat_open# #attack_chain# #combat_result#",
                "#attack_chain#，#reaction_desc#。",
                "#combat_open#。#defense_move#。#counter_attack#。",
            ],
            "combat_open": [
                "二人相对而立，气势对撞",
                "说时迟那时快，",
                "刹那间，",
                "电光石火之间，",
            ],
            "attack_chain": [
                "长刀划过一道金色弧光",
                "一掌拍出，凌厉的掌风扑面而来",
                "他猛然发力，如闪电般而至",
                "剑光一闪，寒气四溢",
            ],
            "combat_result": [
                "激起一阵轰然巨响",
                "对手身形一晃，后退数步",
                "地面被震得四分五裂",
            ],
            "defense_move": [
                "对手侧身闪过",
                "对手右手一抬，格挡在前",
                "对手不闪不避，迎面而上",
            ],
            "counter_attack": [
                "反手一击",
                "顺势反击",
                "借力打力",
            ],
            "reaction_desc": [
                "对方反应极快，瞬间后退",
                "这一招出乎意料，对方瞳孔一缩",
                "对方神色不变，稳如泰山",
            ],
        }, namespace="combat")

    def get_grammar_pack(self, pack_name: str) -> dict:
        """获取指定的语法包（用于组合模板）。"""
        packs = {
            "combat": "combat",
            "psychology": "psychology",
            "environment": "environment",
            "dialogue": "dialogue",
        }
        ns = packs.get(pack_name)
        if ns and ns in self.registry.list_namespaces():
            return self.registry._grammars[ns]
        return {}


# ───────────────── 高级句式模板 ─────────────────

class SentencePatterns:
    """高级句式模板库：按情绪和场景分类的句式模式。"""

    @staticmethod
    def all_patterns() -> dict:
        return {
            # 战斗场景句式
            "combat_impact": [
                "{attacker}的{weapon}如{metaphor}般{verb}，直取{target}的{body_part}。",
                "只听{attacker}一声{shout}，{weapon}已{verb}至{target}面门。",
                "{attacker}身形{style}，{weapon}化作{num}道{color}光芒。",
            ],
            # 情感场景句式
            "emotion_surge": [
                "{character}心中{emotion}，{body_reaction}。",
                "一股{emotion}之意涌上{character}心头，{bodily_sensation}。",
                "{character}只觉{feeling}，不由得{action}。",
            ],
            # 过渡句式
            "transition": [
                "时光流转，转眼已是{time_gap}。",
                "在这{place}之中，{duration}转瞬即逝。",
                "{time_prefix}，{scene_summary}。",
            ],
            # 悬念句式
            "suspense": [
                "就在这时，{unexpected_event}。",
                "然而，{character}并未注意到，{hidden_threat}。",
                "突然，{perception}——{shocking_discovery}！",
            ],
            # 总结句式
            "summary": [
                "就这样，{outcome_summary}。",
                "经此一役，{change_description}。",
                "从此，{new_status_quo}。",
            ],
        }

    @classmethod
    def pick_pattern(cls, category: str) -> str:
        """从指定分类中随机挑选一个句式模板。"""
        patterns = cls.all_patterns().get(category, [])
        if not patterns:
            return ""
        return random.choice(patterns)
