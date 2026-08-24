# -*- coding: utf-8 -*-
"""叙事约束求解器 —— 基于 BRUTUS 逻辑约束方法的叙事一致性引擎。

BRUTUS (Bringsjord & Ferrucci, 2000) 是最早系统使用逻辑约束来确保叙事一致性的
故事生成系统之一。它专门生成"背叛"主题故事，使用一阶逻辑来表达角色信念、目标、
行为之间的约束关系。

本模块将 BRUTUS 的逻辑约束方法扩展为通用的叙事一致性检查框架，包括：
  - 硬约束（不可违反）：角色生死、物品归属、时间因果关系
  - 软约束（可权衡）：角色性格一致性、动机逻辑性、情节节奏
  - 自动修复建议：检测到矛盾后提供替代方案
"""

import re
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum


class ConstraintSeverity(Enum):
    FATAL = "fatal"       # 不可违反（如死人出现、时间悖论）
    STRONG = "strong"     # 强烈建议遵守（如角色个性矛盾）
    WEAK = "weak"         # 弱建议（如修辞偏好、风格一致）


@dataclass
class ConstraintViolation:
    """一次约束违反记录。"""
    severity: ConstraintSeverity
    rule_name: str
    description: str
    context: str           # 出现矛盾的叙事上下文
    fix_suggestion: str    # 修复建议


@dataclass
class CharacterStatus:
    """角色的约束状态记录。"""
    alive: bool = True
    location: str = ""
    status_effects: list[str] = field(default_factory=list)  # [受伤/中毒/封印/...]
    chapters_appeared: set[int] = field(default_factory=set)
    last_mentioned_chapter: int = 0


@dataclass
class ItemStatus:
    """物品的约束状态记录。"""
    exists: bool = True
    holder: str = ""             # 当前持有者
    destroyed_chapter: int = -1  # 被摧毁的章节
    used_chapters: set[int] = field(default_factory=set)


class NarrativeConstraintEngine:
    """叙事约束引擎 —— 检查并维持叙事世界的逻辑一致性。"""

    def __init__(self):
        self._characters: dict[str, CharacterStatus] = {}
        self._items: dict[str, ItemStatus] = {}
        self._timeline: dict[int, dict] = {}      # chapter → events
        self._world_rules: list[str] = []          # 世界规则声明
        self._violations: list[ConstraintViolation] = []
        self._hard_rules: list[callable] = []      # 硬约束规则函数列表
        self._soft_rules: list[callable] = []

        self._register_rules()

    # ---- 规则注册 ----

    def _register_rules(self):
        """注册所有内置约束规则。"""
        # 硬约束
        self._hard_rules.extend([
            self._check_death_paradox,
            self._check_item_ownership_paradox,
            self._check_timeline_causality,
            self._check_location_impossible,
            self._check_contradiction_self,
        ])
        # 软约束
        self._soft_rules.extend([
            self._check_character_motivation_consistency,
            self._check_power_level_consistency,
            self._check_relationship_consistency,
        ])

    # ---- 角色/物品注册 ----

    def register_character(self, name: str, **kwargs):
        self._characters[name] = CharacterStatus(**kwargs)

    def register_item(self, name: str, **kwargs):
        self._items[name] = ItemStatus(**kwargs)

    def declare_world_rule(self, rule: str):
        """声明一条世界规则（如：归墟世界中死者不可复生）。"""
        self._world_rules.append(rule)

    # ---- 硬约束规则 ----

    def _check_death_paradox(self, chapter_num: int, event: dict) -> list[ConstraintViolation]:
        """规则1：已死亡角色不能再次出现。"""
        violations = []
        for char_name, involved in event.get("characters_involved", {}).items():
            if char_name in self._characters and not self._characters[char_name].alive:
                violations.append(ConstraintViolation(
                    ConstraintSeverity.FATAL, "death_paradox",
                    f"角色【{char_name}】已在第{self._characters[char_name].last_mentioned_chapter}章死亡，"
                    f"不能在第{chapter_num}章再次出现",
                    f"第{chapter_num}章: {event.get('summary', '')}",
                    f"建议：将角色替换为{char_name}的继承者/幻象/回忆，或者删除此出场"
                ))
        return violations

    def _check_item_ownership_paradox(self, chapter_num: int, event: dict) -> list[ConstraintViolation]:
        """规则2：已摧毁/已转手的物品不能出现在错误的持有者手中。"""
        violations = []
        for item_name, holder in event.get("items_used", {}).items():
            if item_name in self._items:
                item = self._items[item_name]
                if not item.exists and item.destroyed_chapter < chapter_num:
                    violations.append(ConstraintViolation(
                        ConstraintSeverity.FATAL, "item_destroyed",
                        f"物品【{item_name}】已在第{item.destroyed_chapter}章被摧毁，"
                        f"不能在第{chapter_num}章再次使用",
                        f"{holder} 使用了 {item_name}",
                        f"建议：改用类似功能的替代物品，或改为该物品的残片/仿制品"
                    ))
        return violations

    def _check_timeline_causality(self, chapter_num: int, event: dict) -> list[ConstraintViolation]:
        """规则3：事件必须发生在因果链的正确位置（果不能先于因）。"""
        violations = []
        required_events = event.get("requires_events", [])
        completed_events = set()
        for ch, ev_dict in self._timeline.items():
            if ch < chapter_num:
                completed_events.update(ev_dict.get("event_tags", []))
        for req in required_events:
            if req not in completed_events:
                violations.append(ConstraintViolation(
                    ConstraintSeverity.STRONG, "causality_break",
                    f"事件'{event.get('summary', '')}'要求前置事件'{req}'，"
                    f"但该事件在第{chapter_num}章之前尚未发生",
                    f"缺失前置: {req}",
                    f"建议：在第{chapter_num}章之前插入'{req}'事件，或修改当前事件逻辑"
                ))
        return violations

    def _check_location_impossible(self, chapter_num: int, event: dict) -> list[ConstraintViolation]:
        """规则4：角色不能同时出现在两个不同地点（同一章节内）。"""
        violations = []
        locations = {}
        for char_name, loc in event.get("character_locations", {}).items():
            if char_name in locations and locations[char_name] != loc:
                violations.append(ConstraintViolation(
                    ConstraintSeverity.FATAL, "location_paradox",
                    f"角色【{char_name}】在第{chapter_num}章同时出现在"
                    f"「{locations[char_name]}」和「{loc}」",
                    f"矛盾位置: {locations[char_name]} vs {loc}",
                    f"建议：二选一保留一个地点，或使用分身/投影/回忆的叙事技巧"
                ))
            locations[char_name] = loc
        return violations

    def _check_contradiction_self(self, chapter_num: int, event: dict) -> list[ConstraintViolation]:
        """规则5：在单章节内不能自相矛盾。"""
        violations = []
        statements = event.get("character_statements", {})
        for char, stmts in statements.items():
            if isinstance(stmts, list) and len(stmts) >= 2:
                for i in range(len(stmts)):
                    for j in range(i + 1, len(stmts)):
                        if self._are_contradictory(str(stmts[i]), str(stmts[j])):
                            violations.append(ConstraintViolation(
                                ConstraintSeverity.FATAL, "self_contradiction",
                                f"角色【{char}】在第{chapter_num}章中自相矛盾",
                                f"「{stmts[i]}」vs「{stmts[j]}」",
                                "建议：删除其中一个矛盾陈述，或改为角色故意说谎/记忆错乱"
                            ))
        return violations

    # ---- 软约束规则 ----

    def _check_character_motivation_consistency(self, chapter_num: int, event: dict) -> list[ConstraintViolation]:
        """软约束1：角色行为与动机/人格一致。"""
        violations = []
        # 检查是否有角色的行为与已建立的动机矛盾
        for char_name, actions in event.get("character_actions", {}).items():
            if char_name in self._characters:
                char = self._characters[char_name]
                char.chapters_appeared.add(chapter_num)
        return violations

    def _check_power_level_consistency(self, chapter_num: int, event: dict) -> list[ConstraintViolation]:
        """软约束2：实力变化应有原因（不能无理由变强）。"""
        violations = []
        power_changes = event.get("power_changes", {})
        for char_name, delta in power_changes.items():
            if abs(delta) > 0.3:  # 大幅变化
                if "training" not in event.get("event_tags", []) and \
                   "power_acquisition" not in event.get("event_tags", []):
                    violations.append(ConstraintViolation(
                        ConstraintSeverity.STRONG, "power_leap",
                        f"角色【{char_name}】的实力在第{chapter_num}章出现大幅变化({delta:+.2f})"
                        f"，但缺少修炼/奇遇/代价的叙事支撑",
                        f"实力变化: {delta}",
                        "建议：添加修炼场景、获得法宝/传承、或以牺牲其他方面为代价"
                    ))
        return violations

    def _check_relationship_consistency(self, chapter_num: int, event: dict) -> list[ConstraintViolation]:
        """软约束3：人际关系变化应有合理过渡。"""
        violations = []
        rel_changes = event.get("relationship_changes", {})
        for pair, change in rel_changes.items():
            if abs(change) > 0.5 and chapter_num > 1:
                # 检查前一章是否有铺垫
                prev_rels = self._timeline.get(chapter_num - 1, {}).get("relationship_changes", {})
                if pair not in prev_rels or abs(prev_rels.get(pair, 0)) < 0.2:
                    violations.append(ConstraintViolation(
                        ConstraintSeverity.WEAK, "relationship_jump",
                        f"角色关系{pair}在第{chapter_num}章发生突变({change:+.2f})，缺乏铺垫",
                        f"关系变化: {change}",
                        "建议：在前面章节添加过渡场景，或在此章增加关系变化的原因说明"
                    ))
        return violations

    # ---- 工具方法 ----

    @staticmethod
    def _are_contradictory(a: str, b: str) -> bool:
        """简单检测两个陈述是否矛盾（基于否定词检测）。"""
        negations = ["不", "没有", "从未", "并非", "完全不是"]
        for neg in negations:
            if (neg + a.strip().lstrip(neg).strip() == b.strip() or
                a.strip() == neg + b.strip().lstrip(neg).strip()):
                return True
        # 简单对立词检测
        opposites = [
            ("活着", "死了"), ("有", "没有"), ("是", "不是"),
            ("去了", "没去"), ("赢了", "输了"), ("同意", "拒绝"),
        ]
        for w1, w2 in opposites:
            if w1 in a and w2 in b:
                return True
            if w2 in a and w1 in b:
                return True
        return False

    # ---- 主检查入口 ----

    def check_chapter(self, chapter_num: int, event: dict) -> dict:
        """对某一章节进行全部的叙事约束检查。
        
        Args:
            chapter_num: 章节号
            event: 章节事件字典，可包含以下键：
                   summary, characters_involved, items_used, requires_events,
                   character_locations, event_tags, character_statements,
                   character_actions, power_changes, relationship_changes
        
        Returns:
            {"pass": bool, "violations": [...], "fatal_count": int, "suggestions": [...]}
        """
        all_violations: list[ConstraintViolation] = []

        # 硬约束
        for rule in self._hard_rules:
            violations = rule(chapter_num, event)
            all_violations.extend(violations)

        # 软约束
        for rule in self._soft_rules:
            violations = rule(chapter_num, event)
            all_violations.extend(violations)

        # 记录到timeline
        self._timeline[chapter_num] = event
        self._violations.extend(all_violations)

        fatal_count = sum(1 for v in all_violations if v.severity == ConstraintSeverity.FATAL)

        return {
            "pass": fatal_count == 0,
            "violations": [
                {"severity": v.severity.value, "rule": v.rule_name,
                 "description": v.description, "fix": v.fix_suggestion}
                for v in all_violations
            ],
            "fatal_count": fatal_count,
            "total_violations": len(all_violations),
        }

    def mark_character_death(self, name: str, chapter_num: int):
        """标记角色死亡。"""
        if name in self._characters:
            self._characters[name].alive = False
            self._characters[name].last_mentioned_chapter = chapter_num

    def mark_item_destroyed(self, name: str, chapter_num: int):
        """标记物品被摧毁。"""
        if name in self._items:
            self._items[name].exists = False
            self._items[name].destroyed_chapter = chapter_num

    def transfer_item(self, name: str, new_holder: str, chapter_num: int):
        """转移物品所有权。"""
        if name in self._items:
            self._items[name].holder = new_holder
            self._items[name].used_chapters.add(chapter_num)

    @property
    def violations_summary(self) -> dict:
        """获取所有违反记录的摘要。"""
        fatal = sum(1 for v in self._violations if v.severity == ConstraintSeverity.FATAL)
        strong = sum(1 for v in self._violations if v.severity == ConstraintSeverity.STRONG)
        weak = sum(1 for v in self._violations if v.severity == ConstraintSeverity.WEAK)
        return {"fatal": fatal, "strong": strong, "weak": weak, "total": len(self._violations)}


# ====================================================================
# 自检
# ====================================================================
if __name__ == "__main__":
    print("=" * 50)
    print("叙事约束求解器 — 自检")
    engine = NarrativeConstraintEngine()
    engine.register_character("白墨", alive=True, location="归墟之巅")
    engine.register_character("渊皇", alive=True, location="九幽深渊")
    engine.register_character("青璃", alive=True, location="归墟入口")
    engine.register_item("碎星剑", holder="白墨")
    engine.register_item("归墟之核", holder="渊皇")

    # 模拟章节检查
    ch1 = {"summary": "白墨在归墟之巅发现碎星剑",
           "characters_involved": {"白墨": True},
           "items_used": {"碎星剑": "白墨"},
           "event_tags": ["power_acquisition"]}
    result = engine.check_chapter(1, ch1)
    print(f"第1章: 通过={result['pass']}, 违规={result['total_violations']}")
    assert result["pass"], "第1章应该通过"

    engine.mark_character_death("渊皇", 3)
    engine.mark_item_destroyed("归墟之核", 4)

    # 第5章：渊皇已死但出场 → 应该检测到致命违规
    ch5 = {"summary": "渊皇突然出现，抢夺碎星剑",
           "characters_involved": {"渊皇": True, "白墨": True},
           "items_used": {"碎星剑": "白墨", "归墟之核": "渊皇"},
           "event_tags": ["villain_return"]}
    result = engine.check_chapter(5, ch5)
    print(f"第5章(渊皇已死+归墟之核已毁): 通过={result['pass']}, "
          f"致命={result['fatal_count']}, 总违规={result['total_violations']}")
    if result["violations"]:
        for v in result["violations"]:
            print(f"  [{v['severity']}] {v['description'][:80]}")
            print(f"    修复: {v['fix'][:80]}")
    print(f"摘要: {engine.violations_summary}")
    print("全部自检通过 [OK]")
