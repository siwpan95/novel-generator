# -*- coding: utf-8 -*-
"""Propp 31种叙事功能编码 + 叙事蓝图模板引擎。
将 Propp《民间故事形态学》改编为因果链引擎的情节规划驱动层。
"""

import random
from typing import Optional
from dataclasses import dataclass


@dataclass
class ProppFunction:
    index: int                    # 1~31
    name: str                     # 中文名称
    symbol: str                   # Propp 原符号
    zone: str                     # preparation/complication/transfer/struggle/return/punishment
    description: str
    preconditions: list[str]
    slot_fillers: dict[str, str]  # slot名 → 说明
    narrative_beat: int           # 映射的节拍 1~15
    outcome_tags: list[str]
    variant_templates: list[str]

# 31功能精简编码（保留核心结构与多模板）
PROPP_31 = [
    ProppFunction(1, "远离/缺席", "β", "preparation",
        "某位家庭成员离开或外出", ["世界平衡态"],
        {"absentee": "缺席者", "reason": "离开原因", "destination": "去向"},
        1, ["initial_departure", "power_vacuum"],
        ["{absentee}因{reason}离开了{destination}，平衡被打破。",
         "{absentee}远赴{destination}，无人知晓变动正在酝酿。"]),
    ProppFunction(2, "禁令", "γ¹", "preparation",
        "英雄被给予一道禁令", ["存在权威角色"],
        {"hero": "英雄", "authority": "禁令者", "forbidden_act": "被禁行为"},
        1, ["interdiction_set"],
        ["{authority}郑重警告{hero}：绝不要{forbidden_act}。",
         "「{forbidden_act}——记住，这是最后的忠告。」"]),
    ProppFunction(3, "违禁", "δ¹", "preparation",
        "禁令被打破", ["禁令已颁布"],
        {"hero": "英雄", "forbidden_act": "违反行为", "trigger": "触发原因"},
        2, ["interdiction_broken", "villain_entry"],
        ["然而{trigger}，{hero}选择了{forbidden_act}。",
         "{hero}明知不可为，却因{trigger}，毅然{forbidden_act}。"]),
    ProppFunction(4, "刺探", "ε¹", "complication",
        "反派尝试获取信息", ["反派已出场"],
        {"villain": "反派", "target_info": "目标信息", "method": "刺探方式"},
        2, ["villain_scouting"],
        ["{villain}派遣密探，用{method}打探{target_info}。",
         "暗处，{villain}正通过{method}收集{target_info}。"]),
    ProppFunction(5, "通报", "ζ¹", "complication",
        "反派获得受害者信息", ["刺探完成"],
        {"villain": "反派", "victim": "受害者", "intel": "情报"},
        3, ["villain_informed"],
        ["密报传回——{villain}得知：{intel}。",
         "「原来如此。」{villain}终于知道了{intel}。"]),
    ProppFunction(6, "诡计", "η¹", "complication",
        "反派试图欺骗受害者", ["反派已收集信息"],
        {"villain": "反派", "victim": "受害者", "deception": "欺骗手段"},
        3, ["villain_deception", "conflict_seed"],
        ["{villain}以{deception}接近{victim}。",
         "一场精心布置的陷阱——{villain}用{deception}诱使{victim}走入圈套。"]),
    ProppFunction(7, "同谋", "θ¹", "complication",
        "受害者上当，无意帮助敌人", ["诡计已实施"],
        {"victim": "受害者", "villain": "反派", "unwitting_help": "无意帮助"},
        4, ["victim_complicit"],
        ["不知真相的{victim}，竟{unwitting_help}，正中{villain}下怀。"]),
    ProppFunction(8, "恶行/缺失", "A/a", "complication",
        "反派造成伤害或某人/某物缺失", ["反派已设陷阱"],
        {"villain": "反派", "victim": "受害者", "villainy": "恶行", "loss": "失去之物"},
        5, ["inciting_incident", "quest_trigger"],
        ["{villain}终于出手——{villainy}。{victim}失去了{loss}。",
         "灾难降临：{villainy}。{loss}从此成为必须追寻之物。"]),
    ProppFunction(9, "调停/中介", "B", "transfer",
        "灾难被知晓，英雄受到召唤", ["恶行已发生"],
        {"hero": "英雄", "caller": "派遣者", "quest": "任务"},
        6, ["call_to_adventure", "quest_accepted"],
        ["{caller}找到{hero}：你必须去{quest}。",
         "{hero}望着疮痍，心中已有答案——{quest}。"]),
    ProppFunction(10, "出发/启程", "C↑", "transfer",
        "英雄离开家踏上征途", ["任务已接受"],
        {"hero": "英雄", "from_place": "出发地", "to_place": "目的地", "companion": "同行者"},
        6, ["departure", "journey_begin"],
        ["{hero}告别{from_place}，与{companion}踏上前往{to_place}的旅途。"]),
    ProppFunction(11, "捐赠者考验", "D¹", "transfer",
        "英雄经受考验以获得宝物", ["英雄已出发"],
        {"hero": "英雄", "donor": "考验者", "test": "考验内容"},
        7, ["mentor_test", "power_acquisition"],
        ["{donor}拦住去路：想过去？先{test}。"]),
    ProppFunction(12, "英雄反应", "E¹", "transfer",
        "英雄对考验作出反应", ["考验已提出"],
        {"hero": "英雄", "reaction": "反应", "result": "结果"},
        7, ["hero_responds", "mentor_result"],
        ["{hero}{reaction}，带来了{result}。"]),
    ProppFunction(13, "领受宝物", "F¹", "transfer",
        "魔法器物被英雄获得", ["英雄通过考验"],
        {"hero": "英雄", "donor": "赠与者", "magical_item": "宝物", "item_power": "功效"},
        7, ["power_up", "item_acquisition"],
        ["{donor}将{magical_item}交给{hero}：它能{item_power}。"]),
    ProppFunction(14, "空间转换", "G", "transfer",
        "英雄被引领到关键地点", ["英雄已获辅助"],
        {"hero": "英雄", "guide": "引导者", "destination": "目的地"},
        8, ["world_entry", "realm_transfer"],
        ["{guide}打开通往{destination}的门——进入了另一个世界。"]),
    ProppFunction(15, "斗争", "H¹", "struggle",
        "英雄与反派正面交锋", ["双方已入战场"],
        {"hero": "英雄", "villain": "反派", "battlefield": "战场", "stakes": "赌注"},
        9, ["climax_battle", "direct_confrontation"],
        ["{battlefield}之上，{hero}与{villain}终于正面相对，赌注是{stakes}。"]),
    ProppFunction(16, "标记/烙印", "J¹", "struggle",
        "英雄被留下标记", ["斗争已发生"],
        {"hero": "英雄", "mark": "标记", "significance": "意义"},
        10, ["hero_marked", "scar_earned"],
        ["{hero}低头看着{mark}——{significance}。"]),
    ProppFunction(17, "胜利", "I¹", "struggle",
        "反派被击败", ["斗争已展开"],
        {"hero": "英雄", "villain": "反派", "method": "方式", "consequence": "后果"},
        10, ["villain_defeated", "quest_complete"],
        ["{villain}终于倒下——{hero}以{method}终结一切。{consequence}。"]),
    ProppFunction(18, "缺失填补", "K¹", "struggle",
        "初始缺失被消除", ["反派已败"],
        {"initial_loss": "最初缺失", "restoration": "恢复方式"},
        11, ["loss_restored", "mission_accomplished"],
        ["{initial_loss}——这遗憾终于通过{restoration}得到弥补。"]),
    ProppFunction(19, "归来", "↓", "return",
        "英雄踏上归途", ["任务完成"],
        {"hero": "英雄", "from_place": "归来地", "home": "家乡"},
        12, ["return_journey"],
        ["{hero}踏上从{from_place}回{home}的路，归途漫漫却不再迷茫。"]),
    ProppFunction(20, "追捕", "Pr¹", "return",
        "英雄被追逐", ["英雄已归途"],
        {"hero": "英雄", "pursuer": "追逐者", "danger": "危险"},
        12, ["pursuit", "return_complication"],
        ["但{pursuer}的影子紧随——{danger}。"]),
    ProppFunction(21, "获救", "Rs¹", "return",
        "英雄从追捕中被救", ["追捕已发生"],
        {"hero": "英雄", "rescuer": "救援者", "escape_method": "逃脱方式"},
        12, ["rescue", "escape"],
        ["千钧一发之际，{rescuer}出现，{escape_method}。"]),
    ProppFunction(22, "不被认出的抵达", "O", "return",
        "英雄以未知身份抵达", ["英雄脱离追捕"],
        {"hero": "英雄", "disguise": "伪装", "destination": "抵达地"},
        13, ["incognito_arrival"],
        ["{hero}以{disguise}来到{destination}，无人识得真容。"]),
    ProppFunction(23, "假英雄宣称", "L", "return",
        "假英雄提出无效宣称", ["英雄未恢复身份"],
        {"false_hero": "假英雄", "claim": "宣称功绩"},
        13, ["false_claim", "impostor"],
        ["{false_hero}站出，声称{claim}——但那是谎言。"]),
    ProppFunction(24, "艰难任务", "M", "return",
        "给英雄提出艰难任务", ["假英雄已宣称"],
        {"hero": "英雄", "task": "任务", "taskmaster": "出题者"},
        13, ["final_test", "identity_proof"],
        ["{taskmaster}提出：唯有能{task}者，才是真正的英雄。"]),
    ProppFunction(25, "任务完成", "N", "return",
        "英雄完成艰难任务", ["任务已提出"],
        {"hero": "英雄", "task": "任务", "completion": "完成方式"},
        14, ["feat_accomplished", "identity_proven"],
        ["{hero}做到了——{completion}。真相大白。"]),
    ProppFunction(26, "认出/确认", "Q", "return",
        "英雄被认出", ["任务已完成"],
        {"hero": "英雄", "marker": "认出依据", "recognizer": "认出者"},
        14, ["recognition", "identity_restored"],
        ["{marker}——{recognizer}惊呼：是他！真的是{hero}！"]),
    ProppFunction(27, "揭露", "Ex", "return",
        "假英雄/反派被揭露", ["真英雄已认出"],
        {"false_one": "被揭露者", "truth": "真相"},
        14, ["exposure", "villain_unmasked"],
        ["真相暴露——{false_one}的谎言被{truth}击碎。"]),
    ProppFunction(28, "变容/新生", "T", "return",
        "英雄获得新形象", ["身份已恢复"],
        {"hero": "英雄", "transformation": "变化", "new_form": "新形态"},
        15, ["transformation", "hero_ascension"],
        ["旧{hero}已死。现在站着的是{new_form}。"]),
    ProppFunction(29, "惩罚", "U", "punishment",
        "反派受到惩罚", ["反派已被揭露"],
        {"villain": "反派", "punishment": "惩罚"},
        15, ["justice", "villain_punished"],
        ["{villain}终于受到应得惩罚——{punishment}。"]),
    ProppFunction(30, "婚礼/登基", "W", "return",
        "英雄获得最终奖赏", ["一切结束"],
        {"hero": "英雄", "reward": "奖赏", "new_status": "新地位"},
        15, ["final_reward", "happy_ending"],
        ["{reward}——{hero}终于得到了。{new_status}。"]),
    ProppFunction(31, "英雄升华", "*", "return",
        "英雄完成叙事弧", ["奖赏已获"],
        {"hero": "英雄", "final_state": "终态", "legacy": "传奇"},
        15, ["ascension", "story_end"],
        ["{hero}回望来路。{legacy}——这是他留给世界的一切。"]),
]

# 节拍→Propp功能映射
BEAT_TO_PROPP: dict[int, list[int]] = {
    1: [1, 2], 2: [3, 4], 3: [5, 6], 4: [7], 5: [8],
    6: [9, 10], 7: [11, 12, 13], 8: [14], 9: [15],
    10: [16, 17], 11: [18], 12: [19, 20, 21],
    13: [22, 23, 24], 14: [25, 26, 27], 15: [28, 29, 30, 31],
}

ZONE_RHYTHM = {
    "preparation": {"tempo": "slow", "length": (3, 5)},
    "complication": {"tempo": "rising", "length": (4, 7)},
    "transfer": {"tempo": "medium", "length": (3, 6)},
    "struggle": {"tempo": "fast", "length": (5, 10)},
    "return": {"tempo": "falling", "length": (3, 6)},
    "punishment": {"tempo": "final", "length": (2, 4)},
}

WORLD_PROPP_PROFILES = {
    "归墟": ["preparation", "complication", "transfer", "struggle", "return", "punishment"],
    "东方修仙": ["preparation", "transfer", "transfer", "struggle", "return"],
    "武侠·苍云之殇": ["preparation", "complication", "struggle", "return", "punishment"],
    "赛博都市": ["complication", "struggle", "struggle", "return"],
    "克苏鲁深渊": ["preparation", "complication", "complication", "struggle"],
    "星际殖民": ["transfer", "transfer", "struggle", "return"],
    "末日废土": ["complication", "struggle", "struggle", "return", "punishment"],
}


class ProppBlueprint:
    """叙事蓝图引擎——从Propp功能生成因果链可用的情节骨架。"""

    def __init__(self, rng: Optional[random.Random] = None):
        self._rng = rng or random.Random()
        self._functions: list[ProppFunction] = []

    def from_beat_sequence(self, beats: list[int]) -> "ProppBlueprint":
        self._functions = []
        used: set[int] = set()
        for beat in beats:
            candidates = [i for i in BEAT_TO_PROPP.get(beat, [9]) if i not in used]
            if not candidates:
                candidates = BEAT_TO_PROPP.get(beat, [9])
            chosen = self._rng.choice(candidates)
            used.add(chosen)
            self._functions.append(PROPP_31[chosen - 1])
        return self

    def from_zone_sequence(self, zones: list[str]) -> "ProppBlueprint":
        self._functions = []
        for zone in zones:
            pool = [f for f in PROPP_31 if f.zone == zone]
            if pool:
                self._functions.append(self._rng.choice(pool))
        return self

    def custom(self, indices: list[int]) -> "ProppBlueprint":
        self._functions = [PROPP_31[i - 1] for i in indices if 1 <= i <= 31]
        return self

    @classmethod
    def full_hero_journey(cls, rng: Optional[random.Random] = None) -> "ProppBlueprint":
        bp = cls(rng)
        bp.from_beat_sequence(list(range(1, 16)))
        return bp

    def render_beat_plan(self, slot_bindings: dict[str, str]) -> dict:
        beat_plans = []
        for func in self._functions:
            template = self._rng.choice(func.variant_templates)
            rendered = template
            for slot in func.slot_fillers:
                value = slot_bindings.get(slot, f"[{slot}]")
                rendered = rendered.replace(f"{{{slot}}}", value)
            zone_meta = ZONE_RHYTHM.get(func.zone, {"tempo": "medium", "length": (3, 5)})
            beat_plans.append({
                "beat": func.narrative_beat,
                "propp_index": func.index, "propp_name": func.name,
                "propp_symbol": func.symbol, "zone": func.zone,
                "rendered": rendered.strip(),
                "outcome_tags": func.outcome_tags,
                "tempo": zone_meta["tempo"],
                "suggested_length": list(zone_meta["length"]),
                "slots_required": list(func.slot_fillers.keys()),
                "preconditions": func.preconditions,
            })
        return {"beat_plans": beat_plans}

    def get_outcome_tag_chain(self) -> list[str]:
        tags = []
        for f in self._functions:
            tags.extend(f.outcome_tags)
        return tags

    @property
    def function_count(self) -> int:
        return len(self._functions)

    @property
    def functions(self) -> list[ProppFunction]:
        return list(self._functions)


def make_world_blueprint(world_name: str, total_beats: int = 8,
                         rng: Optional[random.Random] = None) -> ProppBlueprint:
    """为指定世界生成精简Propp叙事蓝图。"""
    rng = rng or random.Random()
    profile = WORLD_PROPP_PROFILES.get(world_name, WORLD_PROPP_PROFILES["归墟"])
    bp = ProppBlueprint(rng)
    if total_beats <= len(profile):
        bp.from_zone_sequence(profile[:total_beats])
    else:
        zones = list(profile)
        while len(zones) < total_beats:
            zones.insert(-2, "struggle")
        bp.from_zone_sequence(zones[:total_beats])
    return bp


if __name__ == "__main__":
    print("=" * 50)
    print("Propp 31 叙事功能编码 — 自检")
    print(f"功能数: {len(PROPP_31)} | 节拍映射: {len(BEAT_TO_PROPP)}/15")
    bp = ProppBlueprint.full_hero_journey()
    slots = {"hero": "白墨", "villain": "渊皇", "authority": "天道",
             "absentee": "师父", "reason": "天道召唤", "destination": "归墟",
             "forbidden_act": "打开万界封印", "trigger": "至亲被俘",
             "target_info": "归墟入口", "method": "傀儡渗透", "victim": "青璃",
             "intel": "归墟守护者已衰老", "deception": "化身为故人",
             "unwitting_help": "引狼入室", "villainy": "摧毁归墟灵脉", "loss": "归墟之核",
             "quest": "找回归墟之核", "caller": "天道化身", "from_place": "归墟遗迹",
             "to_place": "九幽深渊", "companion": "青璃", "donor": "守碑老人",
             "test": "走过九步炼心桥", "reaction": "闭目前行，不被幻象所惑",
             "result": "守碑老人颔首微笑", "magical_item": "碎星剑", "item_power": "斩断因果",
             "guide": "星图", "battlefield": "九幽之巅", "stakes": "万界存亡",
             "mark": "胸口的剑痕", "significance": "这是英雄的烙印",
             "method": "碎星一剑", "consequence": "渊皇化作星光散去",
             "initial_loss": "归墟之核", "restoration": "星光重聚",
             "pursuer": "渊皇余党", "danger": "灭魂阵已成",
             "rescuer": "青璃", "escape_method": "以身破阵",
             "disguise": "流浪道人", "false_hero": "渊皇残魂",
             "claim": "是他击败了真正的渊皇",
             "task": "在万界之石上刻下真名", "taskmaster": "天道",
             "completion": "以血为墨,写下白墨二字",
             "marker": "胸口的剑痕", "recognizer": "青璃",
             "truth": "渊皇残魂的破绽", "false_one": "渊皇残魂",
             "transformation": "归墟之力入体", "new_form": "新的万界守护者",
             "punishment": "永囚归墟之底",
             "reward": "万界安宁", "new_status": "从凡人到守护者的蜕变",
             "final_state": "屹立归墟之巅", "legacy": "万界归墟的传说"}
    plan = bp.render_beat_plan(slots)
    for p in plan["beat_plans"]:
        print(f"  Beat {p['beat']:2d} | {p['propp_name']:10s} [{p['zone']}] → {p['rendered'][:70]}")
    print("=" * 50)
    for world in WORLD_PROPP_PROFILES:
        wbp = make_world_blueprint(world, 6)
        print(f"  {world}: {wbp.function_count}功能 | 标签: {wbp.get_outcome_tag_chain()[:6]}")
    print("全部自检通过 [OK]")
