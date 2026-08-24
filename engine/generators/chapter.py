"""章节生成器：多层嵌套循环 + 全叙事模块集成。

整合模块：
- StructureFramework：剧情弧线节拍控制
- ContextManager：叙事阶段/紧张度/世界状态追踪
- NarrativeConstraintEngine：叙事一致性验证
- CharacterDrive：角色动机/人格矩阵/互动引擎
- 词库集成：伏笔/钩子/五感/场景节拍/真理揭示/质量碎片

每章输出结构：
1. 叙事规划 → 2. 世界观开场 → 3. 角色动机卡片（精简版）
4. 情节推进（非战斗节拍）→ 5. 战斗序列（增强版）
6. 叙事验证 → 7. 伏笔+钩子 → 8. 章尾收束

支持两种模式：
- 经典模式（默认）：纯战斗→对话→收束
- 增强模式：接入全部叙事模块
"""

from ..word_bank import WordBank
from .character import CharacterGenerator
from .battle import BattleGenerator, SceneGenerator
from .dialogue import DialogueGenerator


class ChapterGenerator:
    """章节生成器：多层嵌套循环生成完整一章。"""

    def __init__(self, wb: WordBank):
        self._wb = wb
        self._char_gen = CharacterGenerator(wb)
        self._scene_gen = SceneGenerator(wb)
        self._battle_gen = BattleGenerator(wb)
        self._dialog_gen = DialogueGenerator(wb)

    def generate(
        self,
        chapter_num: int,
        volume_title: str,
        hero: dict = None,
        partner: dict = None,
        opponent_count: int = 4,
        battle_rounds_per_pair: int = 3,
        seed: int = None,
        # ★ 增强模式参数
        context_mgr=None,
        structure_fw=None,
        constraint_engine=None,
        drive_engine=None,
    ) -> str:
        """生成完整一章（支持增强模式）。"""
        if seed is not None:
            self._wb.get_rng().seed(seed)

        rng = self._wb.get_rng()
        enhanced = all([
            context_mgr is not None,
            structure_fw is not None,
            constraint_engine is not None,
            drive_engine is not None,
        ])

        # === 章标题 ===
        chapter_title = self._generate_chapter_title(chapter_num, volume_title)
        lines = [
            chapter_title, "",
            "=" * 40, ""
        ]

        # === 主角和搭档 ===
        if hero is None:
            hero = self._char_gen.generate(
                surname=rng.choice(["蘑菇", "蓝光"]), assign_personality=True
            )
        if partner is None:
            partner = self._char_gen.generate(assign_personality=True)

        # === 生成对手 ===
        opponents = [
            self._char_gen.generate(assign_personality=True)
            for _ in range(opponent_count)
        ]

        if enhanced:
            char_agent, interaction_engine = drive_engine
            return self._generate_enhanced(
                lines, chapter_num, volume_title,
                hero, partner, opponents, opponent_count,
                battle_rounds_per_pair,
                context_mgr, structure_fw, constraint_engine,
                char_agent, interaction_engine, rng,
            )

        return self._generate_classic(
            lines, hero, partner, opponents,
            opponent_count, battle_rounds_per_pair,
            volume_title, rng,
        )

    def _generate_chapter_title(self, chapter_num: int, volume_title: str) -> str:
        """生成章标题。"""
        adj = self._wb.pick("adjectives", "appearance")
        noun = self._wb.pick("locations", "terrain_type")
        return f"第{chapter_num}章 {adj}{noun}"

    # ═══════════════════ 经典模式 ═══════════════════

    def _generate_classic(self, lines, hero, partner, opponents,
                          opponent_count, battle_rounds_per_pair,
                          volume_title, rng):
        """经典模式：保留原有行为。"""
        scene_text = self._scene_gen.generate_scene()
        lines.append("【场景】")
        lines.append(scene_text)
        lines.append("")
        lines.append("【本章主角与搭档】")
        lines.append(self._char_gen.format_character_intro(hero))
        lines.append("")
        lines.append(self._char_gen.format_character_intro(partner))
        lines.append("")
        lines.append("【本章登场对手】")
        for i, opp in enumerate(opponents):
            lines.append(f"--- 对手 {i + 1} ---")
            lines.append(self._char_gen.format_character_intro(opp))
            lines.append("")
        return self._generate_battles(
            lines, hero, partner, opponents,
            opponent_count, battle_rounds_per_pair,
            volume_title, rng,
        )

    # ═══════════════════ 增强模式 ═══════════════════

    def _generate_enhanced(self, lines, chapter_num, volume_title,
                           hero, partner, opponents, opponent_count,
                           battle_rounds_per_pair,
                           context_mgr, structure_fw, constraint_engine,
                           char_agent, interaction_engine, rng):
        """增强模式：接入全部叙事模块。"""
        # 1. 叙事规划
        story_beat = self._plan_narrative(
            chapter_num, context_mgr, rng
        )

        # 2. 世界观开场
        lines.append(self._world_opening(story_beat, structure_fw, rng))
        lines.append("")

        # 3. 角色动机卡片（精简版）
        lines.append(self._compact_characters(
            hero, partner, opponents, char_agent, rng
        ))
        lines.append("")

        # 4. 情节节拍（非战斗叙事）
        lines.append(self._plot_beat(
            hero, partner, story_beat, context_mgr, rng
        ))
        lines.append("")

        # 5. 场景 + 五感
        scene_text = self._scene_gen.generate_scene()
        lines.append("【场景】")
        lines.append(scene_text)
        lines.append("")
        lines.append(self._sensory_passage(volume_title, rng))
        lines.append("")

        # 6. 战斗序列
        chapter_text = self._generate_battles(
            lines, hero, partner, opponents,
            opponent_count, battle_rounds_per_pair,
            volume_title, rng,
        )
        body_lines = chapter_text.split("\n")

        # 7. 叙事验证
        event = {
            "summary": f"{hero['name']}与{partner['name']}在第{chapter_num}章的冒险",
            "characters_involved": {
                hero["name"]: True, partner["name"]: True
            },
            "event_tags": [story_beat["beat_name"]],
        }
        for opp in opponents:
            event["characters_involved"][opp["name"]] = True
        result = constraint_engine.check_chapter(chapter_num, event)
        if not result["pass"] or result["total_violations"] > 0:
            body_lines.append("")
            body_lines.append("【叙事约束检查】")
            for v in result["violations"][:2]:
                body_lines.append(f"※ {v['description']}")

        # 8. 伏笔 + 钩子
        body_lines.append("")
        body_lines.append(self._foreshadow(chapter_num, rng))
        body_lines.append(self._hook(story_beat, hero, partner, rng))

        # 9. 章尾收束
        end = self._enhanced_ending(
            hero, partner, volume_title, story_beat, rng
        )
        body_lines.append(end)
        return "\n".join(body_lines)

    def _generate_battles(self, lines, hero, partner, opponents,
                          opponent_count, battle_rounds_per_pair,
                          volume_title, rng):
        """通用战斗生成（经典+增强共用）。"""
        terrain_name = f"闪{self._wb.pick('locations', 'terrain_type')}"
        lines.append(f"【{hero['name']}与{partner['name']}的挑战】")
        lines.append("")

        fighters = [
            (hero if i % 2 == 0 else partner, opponents[i])
            for i in range(opponent_count)
        ]

        for idx, (attacker, defender) in enumerate(fighters):
            lines.append(
                f"———— 第{idx + 1}场：{attacker['name']} VS "
                f"{defender['name']} ————\n"
            )
            battle_text = self._battle_gen.generate_battle(
                char_a=attacker, char_b=defender,
                rounds=battle_rounds_per_pair, terrain=terrain_name,
            )
            lines.append(battle_text)
            lines.append("")
            dialogue = self._dialog_gen.generate_exchange(
                name_a=attacker['name'], name_b=defender['name'],
                skill_a=attacker['skill'], skill_b=defender['skill'],
                weapon_a=attacker['weapon'], weapon_b=defender['weapon'],
                treasure_a=attacker['treasure'], treasure_b=defender['treasure'],
                terrain=terrain_name,
            )
            lines.append(dialogue)
            lines.append("")

        ending_templates = [
            f"就这样，{hero['name']}与{partner['name']}一路过关斩将，"
            f"向着更深的{volume_title}进发。",
            f"{hero['name']}收起{hero['weapon'].strip('☆')}，"
            f"望向远方的下一片战场。",
            f"这一章的挑战虽已结束，但{hero['name']}知道，真正的战斗还在后面。",
            f"{partner['name']}拍了拍{hero['name']}的肩膀："
            f"\"走吧，还有更多对手等着我们。\"",
        ]
        lines.append(rng.choice(ending_templates))
        return "\n".join(lines)

    # ── 叙事规划 ──

    def _plan_narrative(self, chapter_num, context_mgr, rng) -> dict:
        """根据章节位置映射叙事节拍。14章节按 3:1:3:3:4 比例划分。"""
        total = 140
        ratio = chapter_num / total
        if ratio <= 0.2:
            beat, tension = "setup", "calm"
        elif ratio <= 0.27:
            beat, tension = "inciting", "calm"
        elif ratio <= 0.35:
            beat, tension = "debate", "rising"
        elif ratio <= 0.5:
            beat, tension = "fun_games", "calm"
        elif ratio <= 0.6:
            beat, tension = "midpoint", "rising"
        elif ratio <= 0.7:
            beat, tension = "bad_guys", "high"
        elif ratio <= 0.8:
            beat, tension = "all_lost", "high"
        elif ratio <= 0.9:
            beat, tension = "dark_night", "peak"
        else:
            beat, tension = "epilogue", "calm"
        context_mgr.set_world("chapter", chapter_num)
        context_mgr._arc["chapter"] = chapter_num
        context_mgr._arc["phase"] = beat
        context_mgr._arc["tension"] = {
            "calm": 0.2, "rising": 0.5, "high": 0.75, "peak": 0.9
        }.get(tension, 0.3)
        return {"beat_name": beat, "tension": tension, "chapter_num": chapter_num}

    # ── 世界观开场 ──

    def _world_opening(self, story_beat, structure_fw, rng) -> str:
        """生成世界观开场段落。"""
        beat = story_beat["beat_name"]
        tension = story_beat["tension"]
        try:
            data = self._wb.load("chapter_enrichments")
            candidates = data.get(beat, [])
            if candidates:
                if isinstance(candidates[0], dict):
                    texts = [c["text"] for c in candidates]
                    w = [c.get("weight", 1) for c in candidates]
                    return rng.choices(texts, weights=w, k=1)[0]
                return rng.choice(candidates)
        except (KeyError, FileNotFoundError):
            pass

        # 回退：从 StructureFramework 选取对应节拍
        try:
            beat_pool = getattr(structure_fw, "beats", {}).get(beat, [])
            if beat_pool:
                return rng.choice(beat_pool)
        except Exception:
            pass
        return self._fallback_opening(tension, rng)

    def _fallback_opening(self, tension, rng):
        pool = {
            "calm": [
                "归墟的石壁泛着均匀的蓝光，时间在这里没有意义。",
                "世界锚定点稳定运行——至少在表面上是这样。",
            ],
            "rising": [
                "墟核的蓝光闪烁频率加快了——世界线不稳定的前兆。",
                "不安感再次袭来，像是有什么在归墟深处苏醒。",
            ],
            "high": [
                "墟核面板上的数据曲线剧烈波动，多个世界同时出现异常。",
                "归墟的穹顶在震动。不是地震——是某个世界正在从内部撕裂。",
            ],
            "peak": [
                "归墟到了最危险的时刻。墟核的蓝光几乎在尖叫。",
                "混沌海的裂缝张开了——比任何时候都大。",
            ],
        }
        return rng.choice(pool.get(tension, pool["calm"]))

    # ── 精简角色卡片 ──

    def _compact_characters(self, hero, partner, opponents,
                            char_agent, rng) -> str:
        """精简角色卡片（~200字/角色）。"""
        result = ["【本章角色】"]
        for role, char in [("主角", hero), ("搭档", partner)] + [
            (f"对手{i + 1}", opp) for i, opp in enumerate(opponents)
        ]:
            name = char.get("name", "无名")
            skill = char.get("skill", "")
            weapon = char.get("weapon", "")
            # appearance 是 body part 描述列表，取前3项作为外貌剪影
            app_list = char.get("appearance", [])
            if app_list:
                appearance = "，".join(app_list[:3])
            else:
                appearance = "相貌平凡"
            # 性格
            pers = char.get("personality", {})
            if pers:
                tag = pers.get("tag", "")
                tone = pers.get("dialogue_style", {}).get("tone", "")
                quirk = pers.get("quirk", "")
                parts = [tag]
                if tone:
                    parts.append(tone)
                if quirk:
                    parts.append(quirk)
                trait_str = " | ".join(parts[:2])
            else:
                trait_strs = ["坚毅", "敏锐", "果决", "隐忍", "孤傲", "温和", "沉稳", "凌厉"]
                trait_str = "、".join(rng.sample(trait_strs, 2))
            result.append(
                f"【{role}】{name}\n"
                f"  外貌：{appearance}\n"
                f"  武学：{skill}　兵器：{weapon}\n"
                f"  特质：{trait_str}"
            )
        return "\n\n".join(result)

    # ── 情节节拍 ──

    def _plot_beat(self, hero, partner, story_beat,
                   context_mgr, rng) -> str:
        """生成非战斗叙事节拍。"""
        beat = story_beat["beat_name"]
        try:
            data = self._wb.load("chapter_enrichments")
            candidates = data.get(beat, [])
            if candidates:
                if isinstance(candidates[0], dict):
                    texts = [c["text"] for c in candidates]
                    w = [c.get("weight", 1) for c in candidates]
                    return rng.choices(texts, weights=w, k=1)[0]
                return rng.choice(candidates)
        except (KeyError, FileNotFoundError):
            pass
        hn, pn = hero["name"], partner["name"]
        fallback = {
            "setup": f"{hn}站在归墟石阶上，穹顶星图闪烁，每一个光点都是一个世界。",
            "inciting": f"墟核面板跳出一条从未见过的信息。{hn}盯着它看了很久。",
            "midpoint": f"真相像钝刀，慢慢切开{hn}以为坚固的认知。",
            "all_lost": f"{pn}的脸白了——不是恐惧，是看懂了此战没有退路。",
            "fun_games": f"{hn}和{pn}在废墟间搜寻碎片信息，每一步像在拼看不清全貌的拼图。",
        }
        return fallback.get(beat, fallback["fun_games"])

    # ── 五感描写 ──

    def _sensory_passage(self, volume_title, rng) -> str:
        """使用 world_senses 词库生成五感场景描写。"""
        try:
            data = self._wb.load("world_senses")
            worlds = data.get("worlds", {})
            matched = next(
                (k for k in worlds if k in volume_title), "归墟"
            )
            wdata = worlds.get(matched, {"visual": ["幽蓝的冷光"]})
            types = ["visual", "auditory", "olfactory", "tactile"]
            s1 = rng.choice(types)
            s2 = rng.choice([t for t in types if t != s1])
            f1 = rng.choice(wdata.get(s1, ["未知"]))
            f2 = rng.choice(wdata.get(s2, ["未知"]))
            return f"【五感】{f1}。{f2}。"
        except (KeyError, FileNotFoundError):
            return "四周一片寂静，只有微弱的能量波动在空气中震颤。"

    # ── 伏笔 ──

    def _foreshadow(self, chapter_num, rng) -> str:
        """从伏笔词库选取并植入伏笔。"""
        try:
            data = self._wb.load("foreshadowing_pool")
            seeds = data.get("seeds", {})
        except (KeyError, FileNotFoundError):
            return ""
        ratio = chapter_num / 140
        if ratio <= 0.2:
            bt = "theme"
        elif ratio <= 0.35:
            bt = "inciting"
        elif ratio <= 0.6:
            bt = "break_1"
        elif ratio <= 0.8:
            bt = "midpoint"
        else:
            return ""
        candidates = seeds.get(bt, [])
        if not candidates:
            return ""
        return rng.choice(candidates).get("content", "")

    # ── 钩子 ──

    def _hook(self, story_beat, hero, partner, rng) -> str:
        """从钩子模板词库生成章末悬念。"""
        try:
            data = self._wb.load("hook_templates")
            hooks = data.get("hooks", [])
        except (KeyError, FileNotFoundError):
            return ""
        if not hooks:
            return ""
        template = rng.choice(hooks)
        hn, pn = hero["name"], partner["name"]
        beat = story_beat["beat_name"]
        return (
            template.replace("{hero}", hn)
                    .replace("{partner}", pn)
                    .replace("{beat}", beat)
        )

    # ── 增强收束 ──

    def _enhanced_ending(self, hero, partner, volume_title,
                         story_beat, rng) -> str:
        """根据叙事节拍生成对应收束。"""
        beat = story_beat["beat_name"]
        hn, pn = hero["name"], partner["name"]
        pool = {
            "setup": f"世界平稳运转。{hn}和{pn}继续深入{volume_title}。",
            "inciting": f"线索出现了。{hn}意识到——接下来的旅程将不再一样。",
            "debate": f"要不要追这条线索？{hn}和{pn}交换了一个眼神。",
            "fun_games": f"虽然危险重重，但{hn}和{pn}渐入佳境。",
            "midpoint": "一切从这一章开始都将不同了。",
            "bad_guys": f"{pn}低声道：\"后面的路，只会更难。\"",
            "all_lost": f"{hn}咬紧牙关。不能倒下——绝对不能。",
            "dark_night": "最黑暗的时刻。但黑暗中，总会有光的第一丝裂痕。",
            "epilogue": f"{hn}望向天边——那里，是新世界的轮廓。",
        }
        return pool.get(beat, pool["fun_games"])


class VolumeGenerator:
    """卷生成器：一卷包含N章，每章复用主角和搭档设定。"""

    def __init__(self, wb: WordBank):
        self._wb = wb
        self._chapter_gen = ChapterGenerator(wb)

    def generate(self, volume_num, volume_title, chapters=7,
                 opponents_per_chapter=4,
                 context_mgr=None, structure_fw=None,
                 constraint_engine=None, drive_engine=None):
        """生成完整一卷（支持增强模式）。"""
        rng = self._wb.get_rng()
        lines = [
            f"第{volume_num}卷 {volume_title}",
            "=" * 60, "",
        ]
        hero = CharacterGenerator(self._wb).generate(
            surname="蘑菇", assign_personality=True
        )
        partner = CharacterGenerator(self._wb).generate(
            surname="月光", assign_personality=True
        )

        for ch in range(1, chapters + 1):
            chapter_num = (volume_num - 1) * chapters + ch
            chapter_text = self._chapter_gen.generate(
                chapter_num=chapter_num,
                volume_title=volume_title,
                hero=hero, partner=partner,
                opponent_count=opponents_per_chapter,
                battle_rounds_per_pair=3,
                seed=rng.randint(1, 999999),
                context_mgr=context_mgr,
                structure_fw=structure_fw,
                constraint_engine=constraint_engine,
                drive_engine=drive_engine,
            )
            lines.append(chapter_text)
            lines.extend(["", "-" * 50, ""])
        return "\n".join(lines)
