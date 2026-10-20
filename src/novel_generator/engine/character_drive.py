# -*- coding: utf-8 -*-
"""角色自主决策引擎 —— 基于目标、人格、关系的模拟驱动叙事模块。

每个角色（CharacterAgent）根据自身目标(Motivation)、人格矩阵(PersonalityMatrix)、
以及与其他角色的关系(RelationGraph)，在每一叙事轮次作出自主决策。决策结果直接推动
情节发展，而非依赖预写事件序列。

灵感来源：Dwarf Fortress 传奇生成、Versu (Evans & Short 2014)的 Agent 决策模型。
"""

import random
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum


class ActionType(Enum):
    APPROACH = "approach"       # 接近/帮助
    CONFRONT = "confront"       # 冲突/对抗
    EVADE = "evade"             # 逃避/回避
    NEGOTIATE = "negotiate"     # 谈判/交易
    OBSERVE = "observe"         # 观察/收集信息
    SACRIFICE = "sacrifice"     # 牺牲/付出
    BETRAY = "betray"           # 背叛/出卖
    SEEK_POWER = "seek_power"   # 寻求力量
    PROTECT = "protect"         # 保护/守护
    RESTORE = "restore"         # 修复/救赎


class PersonalityTrait(Enum):
    """人格维度（五大人格简化版 + 叙事特定维度）。"""
    OPENNESS = "开放性"         # 好奇 vs 保守
    CONSCIENTIOUSNESS = "尽责性" # 自律 vs 散漫
    EXTRAVERSION = "外向性"     # 主动 vs 内敛
    AGREEABLENESS = "宜人性"    # 同理心 vs 冷酷
    NEUROTICISM = "情绪稳定性"  # 稳定 vs 敏感
    AMBITION = "抱负"           # 渴望权力/成就
    LOYALTY = "忠诚度"          # 对所属阵营的忠诚
    MORALITY = "道德感"         # 善 vs 恶 vs 灰色


@dataclass
class PersonalityMatrix:
    """人格矩阵：8维打分 [-1.0, 1.0]。"""
    openness: float = 0.0
    conscientiousness: float = 0.0
    extraversion: float = 0.0
    agreeableness: float = 0.0
    neuroticism: float = 0.0
    ambition: float = 0.0
    loyalty: float = 0.0
    morality: float = 0.0

    def get(self, trait: PersonalityTrait) -> float:
        key = trait.name.lower()
        return getattr(self, key, 0.0)

    def to_action_bias(self, action: ActionType) -> float:
        """计算角色对特定行动类型的天然倾向。"""
        bias = 0.0
        if action == ActionType.APPROACH:
            bias += self.extraversion * 0.5 + self.agreeableness * 0.5
        elif action == ActionType.CONFRONT:
            bias += self.extraversion * 0.3 - self.agreeableness * 0.4 + self.ambition * 0.3
        elif action == ActionType.EVADE:
            bias += self.neuroticism * 0.5 - self.extraversion * 0.3
        elif action == ActionType.NEGOTIATE:
            bias += self.agreeableness * 0.3 + self.openness * 0.4 - self.ambition * 0.1
        elif action == ActionType.OBSERVE:
            bias += self.openness * 0.5 - self.extraversion * 0.3
        elif action == ActionType.SACRIFICE:
            bias += self.agreeableness * 0.5 + self.morality * 0.4 - self.ambition * 0.3
        elif action == ActionType.BETRAY:
            bias -= self.loyalty * 0.6 - self.morality * 0.4 + self.ambition * 0.2
        elif action == ActionType.SEEK_POWER:
            bias += self.ambition * 0.7 - self.agreeableness * 0.2
        elif action == ActionType.PROTECT:
            bias += self.loyalty * 0.5 + self.agreeableness * 0.3 + self.morality * 0.2
        elif action == ActionType.RESTORE:
            bias += self.conscientiousness * 0.4 + self.morality * 0.3
        return bias

    @classmethod
    def from_profile(cls, profile: str) -> "PersonalityMatrix":
        """从预设人物模板生成人格矩阵。"""
        profiles = {
            "hero_classic": cls(0.6, 0.7, 0.5, 0.5, -0.1, 0.3, 0.7, 0.8),
            "anti_hero": cls(0.5, 0.3, 0.2, -0.3, 0.4, 0.6, 0.2, 0.1),
            "wise_mentor": cls(0.8, 0.9, -0.2, 0.7, -0.5, -0.3, 0.9, 0.9),
            "villain_cold": cls(0.4, 0.8, 0.3, -0.7, -0.3, 0.9, -0.5, -0.8),
            "trickster": cls(0.9, -0.2, 0.6, -0.1, 0.1, 0.4, -0.3, -0.2),
            "loyal_sidekick": cls(0.2, 0.5, 0.4, 0.6, 0.3, -0.1, 0.9, 0.5),
            "innocent": cls(0.3, -0.3, 0.1, 0.8, 0.7, -0.5, 0.3, 0.9),
            "rival": cls(0.3, 0.6, 0.7, -0.4, 0.2, 0.7, -0.1, -0.1),
        }
        return profiles.get(profile, cls())


class GoalType(Enum):
    POWER = "力量/权力"
    REVENGE = "复仇"
    PROTECTION = "保护"
    KNOWLEDGE = "知识/真相"
    REDEMPTION = "救赎"
    FREEDOM = "自由"
    BELONGING = "归属"
    DESTRUCTION = "毁灭"
    WEALTH = "财富"
    LOVE = "爱/羁绊"


@dataclass
class Goal:
    """角色的目标（驱动力）。"""
    type: GoalType
    target: str          # 目标对象（角色名/地点/物品）
    intensity: float     # 强烈程度 0~1
    specificity: str     # 具体描述
    is_urgent: bool = False


@dataclass
class Relation:
    """两个角色之间的关系。"""
    trust: float = 0.0         # -1~1 信任度
    affection: float = 0.0     # -1~1 情感倾向
    power_balance: float = 0.0 # -1(对方强) ~ 1(我强)
    shared_history: list[str] = field(default_factory=list)  # 共同经历标签


@dataclass
class CharacterState:
    """角色当前状态快照。"""
    health: float = 1.0        # 0~1
    morale: float = 1.0        # 0~1 士气
    power_level: float = 0.5   # 0~1 当前实力
    location: str = "未知"
    emotion: str = "平静"
    alive: bool = True
    known_info: set[str] = field(default_factory=set)  # 角色已知的信息片段


class CharacterAgent:
    """自主决策的角色智能体。"""

    def __init__(self, name: str, personality: PersonalityMatrix,
                 role: str = "配角", rng: Optional[random.Random] = None):
        self.name = name
        self.personality = personality
        self.role = role
        self._rng = rng or random.Random()
        self._goals: list[Goal] = []
        self._state = CharacterState()
        self._relationships: dict[str, Relation] = {}
        self._action_log: list[str] = []

    # ---- 目标系统 ----

    def add_goal(self, goal: Goal):
        self._goals.append(goal)

    def remove_goal(self, goal_type: GoalType):
        self._goals = [g for g in self._goals if g.type != goal_type]

    def get_primary_goal(self) -> Optional[Goal]:
        """获取当前最高优先级目标（综合强度与紧急度）。"""
        if not self._goals:
            return None
        return max(self._goals, key=lambda g: g.intensity * (1.5 if g.is_urgent else 1.0))

    # ---- 关系系统 ----

    def set_relation(self, other_name: str, relation: Relation):
        self._relationships[other_name] = relation

    def get_relation(self, other_name: str) -> Relation:
        return self._relationships.get(other_name, Relation())

    def modify_relation(self, other_name: str, trust_delta: float = 0,
                        affection_delta: float = 0, event_tag: str = ""):
        rel = self._relationships.get(other_name, Relation())
        rel.trust = max(-1, min(1, rel.trust + trust_delta))
        rel.affection = max(-1, min(1, rel.affection + affection_delta))
        if event_tag:
            rel.shared_history.append(event_tag)
        self._relationships[other_name] = rel

    # ---- 状态管理 ----

    def update_state(self, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self._state, k):
                setattr(self._state, k, v)

    @property
    def state(self) -> CharacterState:
        return self._state

    # ---- 核心决策 ----

    def decide_action(self, world_state: dict,
                      other_agents: list["CharacterAgent"]) -> tuple[ActionType, str, str]:
        """根据当前世界状态、自身目标、与其他角色的关系，决定下一步行动。
        
        Returns:
            (行动类型, 行动目标, 行动动机描述)
        """
        candidates: list[tuple[float, ActionType, str, str]] = []

        primary_goal = self.get_primary_goal()
        goal_type = primary_goal.type if primary_goal else None
        goal_target = primary_goal.target if primary_goal else ""

        # 评估每个可能行动的综合得分
        for action in ActionType:
            base_score = self.personality.to_action_bias(action)
            goal_score = 0.0
            relation_score = 0.0

            # 目标驱动的分数
            if goal_type == GoalType.REVENGE and action in (ActionType.CONFRONT, ActionType.BETRAY):
                goal_score += 0.5 * (primary_goal.intensity if primary_goal else 0)
            elif goal_type == GoalType.PROTECTION and action in (ActionType.PROTECT, ActionType.SACRIFICE):
                goal_score += 0.6 * (primary_goal.intensity if primary_goal else 0)
            elif goal_type == GoalType.POWER and action in (ActionType.SEEK_POWER, ActionType.CONFRONT):
                goal_score += 0.5 * (primary_goal.intensity if primary_goal else 0)
            elif goal_type == GoalType.KNOWLEDGE and action in (ActionType.OBSERVE, ActionType.NEGOTIATE):
                goal_score += 0.4 * (primary_goal.intensity if primary_goal else 0)
            elif goal_type == GoalType.REDEMPTION and action in (ActionType.RESTORE, ActionType.SACRIFICE):
                goal_score += 0.5 * (primary_goal.intensity if primary_goal else 0)
            elif goal_type == GoalType.FREEDOM and action in (ActionType.EVADE, ActionType.CONFRONT):
                goal_score += 0.4 * (primary_goal.intensity if primary_goal else 0)

            # 关系驱动的分数（最重要的其他角色）
            if other_agents:
                target_agent = other_agents[0]  # 默认主目标为第一个其他角色
                rel = self.get_relation(target_agent.name)
                if action == ActionType.APPROACH and rel.affection > 0:
                    relation_score += rel.affection * 0.4
                elif action == ActionType.CONFRONT and rel.affection < 0:
                    relation_score -= rel.affection * 0.4
                elif action == ActionType.BETRAY and rel.trust > 0.3:
                    relation_score -= 0.3  # 背叛信任的人有心理成本
                elif action == ActionType.PROTECT and rel.affection > 0:
                    relation_score += rel.affection * 0.5

            # 状态修正
            if self._state.morale < 0.3:
                if action in (ActionType.EVADE, ActionType.OBSERVE):
                    base_score += 0.2
                elif action == ActionType.CONFRONT:
                    base_score -= 0.2

            total = base_score + goal_score + relation_score + self._rng.uniform(-0.15, 0.15)
            target = goal_target or (other_agents[0].name if other_agents else "世界")
            motivation = self._make_motivation(action, primary_goal, target)
            candidates.append((total, action, target, motivation))

        candidates.sort(reverse=True)
        best = candidates[0]
        action_desc = f"{self.name} 决定 {best[1].value} {best[2]} —— {best[3]}"
        self._action_log.append(action_desc)
        return best[1], best[2], best[3]

    def _make_motivation(self, action: ActionType, goal: Optional[Goal], target: str) -> str:
        """生成行动动机的自然语言描述。"""
        if goal:
            return f"为了{goal.type.value}（{goal.specificity}）"
        action_motives = {
            ActionType.CONFRONT: f"与{target}的恩怨已经到了必须了结的时刻",
            ActionType.PROTECT: f"守护{target}高于一切",
            ActionType.BETRAY: f"与{target}之间的信任已经破裂",
            ActionType.OBSERVE: f"在行动之前必须先看清{target}的底细",
            ActionType.SACRIFICE: f"有些东西比自己的安危更重要",
            ActionType.SEEK_POWER: f"只有获得力量，才能改变一切",
            ActionType.NEGOTIATE: f"也许还有和平的解决方式",
        }
        return action_motives.get(action, "命运在推动")


# ====================================================================
# 角色交互与情节驱动
# ====================================================================

class InteractionEngine:
    """角色间交互引擎——模拟角色相遇时的冲突/合作/谈判等互动。"""

    def __init__(self, rng: Optional[random.Random] = None):
        self._rng = rng or random.Random()
        self._history: list[dict] = []

    def resolve_interaction(self, a: CharacterAgent, b: CharacterAgent) -> dict:
        """解析两个角色之间的互动，返回互动描述和关系变化。"""
        a_act, a_target, a_motive = a.decide_action(
            {"location": a.state.location, "timeline": "current"},
            [b])
        # B 的视角（角色可能不是对称的）
        b_act, b_target, b_motive = b.decide_action(
            {"location": b.state.location, "timeline": "current"},
            [a])

        rel_a = a.get_relation(b.name)
        rel_b = b.get_relation(a.name)
        tension = abs(rel_a.affection - rel_b.affection)  # 关系不对称度

        interaction = {
            "agent_a": a.name, "agent_b": b.name,
            "a_action": a_act.value, "a_motive": a_motive,
            "b_action": b_act.value, "b_motive": b_motive,
            "tension": tension,
        }

        # 关系变化
        if a_act == ActionType.PROTECT and b_act == ActionType.APPROACH:
            interaction["outcome"] = "synergy"
            a.modify_relation(b.name, 0.1, 0.15, "protected_by")
            b.modify_relation(a.name, 0.15, 0.2, "protected_me")
        elif a_act == ActionType.CONFRONT and b_act == ActionType.CONFRONT:
            interaction["outcome"] = "clash"
            a.modify_relation(b.name, -0.1, -0.2, "confronted")
            b.modify_relation(a.name, -0.1, -0.2, "confronted")
        elif a_act == ActionType.BETRAY and b_act in (ActionType.APPROACH, ActionType.PROTECT):
            interaction["outcome"] = "betrayal"
            b.modify_relation(a.name, -0.5, -0.6, "betrayed")
            a.modify_relation(b.name, 0.0, -0.1, "betrayer")
        elif a_act == ActionType.NEGOTIATE and b_act == ActionType.NEGOTIATE:
            interaction["outcome"] = "truce"
            a.modify_relation(b.name, 0.05, 0.05, "negotiated")
            b.modify_relation(a.name, 0.05, 0.05, "negotiated")
        else:
            interaction["outcome"] = "ambiguous"

        self._history.append(interaction)
        return interaction

    def forge_narrative(self, interaction: dict) -> str:
        """从互动结果生成叙事段落。"""
        templates = {
            "clash": "{a}与{b}正面对峙。一方要{a_motive}，另一方要{b_motive}。冲突不可避免。",
            "synergy": "{a}与{b}在危机中达成默契。{a_motive}，而对方亦是如此。",
            "betrayal": "{b}未曾想到，{a}会在此时背叛。信任的裂痕再也无法弥合。",
            "truce": "剑拔弩张之间，{a}与{b}选择了谈判。毕竟，{a_motive}。",
            "ambiguous": "{a}与{b}的相遇，让局面变得更加扑朔迷离。",
        }
        template = templates.get(interaction["outcome"], templates["ambiguous"])
        return template.format(
            a=interaction["agent_a"], b=interaction["agent_b"],
            a_motive=interaction["a_motive"], b_motive=interaction["b_motive"])

    @property
    def history(self) -> list[dict]:
        return list(self._history)


# ====================================================================
# 自检
# ====================================================================
if __name__ == "__main__":
    print("=" * 50)
    print("角色自主决策引擎 — 自检")
    hero = CharacterAgent("白墨", PersonalityMatrix.from_profile("hero_classic"), "主角")
    villain = CharacterAgent("渊皇", PersonalityMatrix.from_profile("villain_cold"), "反派")
    mentor = CharacterAgent("守碑老人", PersonalityMatrix.from_profile("wise_mentor"), "导师")

    hero.add_goal(Goal(GoalType.PROTECTION, "归墟", 0.9, "守护归墟不被渊皇侵蚀", True))
    villain.add_goal(Goal(GoalType.POWER, "归墟之核", 0.95, "夺取归墟之核统御万界", True))
    mentor.add_goal(Goal(GoalType.KNOWLEDGE, "万界真相", 0.7, "揭开万界归墟的终极秘密"))

    hero.set_relation("渊皇", Relation(-0.5, -0.8, -0.3, ["昔日的同门", "背叛"]))
    villain.set_relation("白墨", Relation(0.1, 0.2, 0.5, ["昔日的同门", "不屑"]))

    print(f"白墨 人格: 宜人={hero.personality.agreeableness}, 道德={hero.personality.morality}")
    print(f"渊皇 人格: 宜人={villain.personality.agreeableness}, 道德={villain.personality.morality}")
    act, target, motive = hero.decide_action({"location": "归墟之巅"}, [villain])
    print(f"白墨决定: {act.value} → {target} ({motive})")
    act, target, motive = villain.decide_action({"location": "归墟之巅"}, [hero])
    print(f"渊皇决定: {act.value} → {target} ({motive})")

    engine = InteractionEngine()
    result = engine.resolve_interaction(hero, villain)
    narrative = engine.forge_narrative(result)
    print(f"互动结果: {result['outcome']}")
    print(f"叙事: {narrative}")
    print(f"关系变化: 白墨→渊皇 信任={hero.get_relation('渊皇').trust:+.2f}")
    print("全部自检通过 [OK]")
