"""对话生成器：生成简单的随机对话。

基于模板 + 随机填充，模拟小说中的对话段落。
"""

from ..word_bank import WordBank


class DialogueGenerator:
    """对话生成器。"""

    # 对话模板池
    EXCHANGE_PATTERNS = [
        {
            "a": '"{name_a}，你这是什么{skill}？好生厉害！"',
            "b": '"{name_b}，{expression}。我这招{skill_name}不过才练了{num}年。你刚才那招{skill2_name}，才真是{adj}至极！"',
        },
        {
            "a": '"看来{name_b}的{weapon}果然名不虚传。"',
            "b": '"{name_a}过奖了。倒是你的{treasure}，让人{verb}不已。"',
        },
        {
            "a": '"这一战的胜负，还难说得很呢！"',
            "b": '"{name_a}，你果然是个值得{verb}的对手。再来！"',
        },
        {
            "a": '"小心了！这招{skill_name}，我还从未对人用过！"',
            "b": '"{name_b}，{expression}。那我也只好全力以赴了！"',
        },
        {
            "a": '"{name_b}兄，你我今日在此相遇，也是缘分。不如{action}？"',
            "b": '"{name_a}说得好！那就让这{terrain}，见证你我这一战吧！"',
        },
        {
            "a": '"哼！你只知道{skill_name}的厉害，却不知道它的弱点！"',
            "b": '"{name_a}，{expression}。那就请赐教吧！"',
        },
        {
            "a": '"好！好！好！能遇到{name_b}这样的对手，不枉此行！"',
            "b": '"{name_a}，你的{weapon}也不差。只是，你还差了一点点……"',
        },
    ]

    def __init__(self, wb: WordBank):
        self._wb = wb

    def generate_exchange(self, name_a: str, name_b: str,
                          skill_a: str, skill_b: str,
                          weapon_a: str, weapon_b: str,
                          treasure_a: str, treasure_b: str,
                          terrain: str) -> str:
        """生成一段两人对话（2-4句）。"""
        rng = self._wb.get_rng()
        pattern = rng.choice(self.EXCHANGE_PATTERNS)

        # 准备替换变量
        vars_ = {
            "name_a": name_a,
            "name_b": name_b,
            "skill_name": skill_a.strip("☆"),
            "skill2_name": skill_b.strip("☆"),
            "skill": rng.choice(["武功", "法术", "绝技", "秘技", "杀招"]),
            "weapon": weapon_a.strip("☆"),
            "treasure": treasure_a.strip("☆"),
            "terrain": terrain,
            "expression": rng.choice(["脸色一变", "微微一笑", "神情严肃", "眼中闪过一丝惊讶",
                                       "不由自主地赞叹道", "深吸一口气", "面色凝重"]),
            "verb": rng.choice(["佩服", "赞叹", "忌惮", "向往", "恐惧", "敬仰"]),
            "action": rng.choice(["切磋一场", "比试一番", "分个高下", "点到为止", "全力一战"]),
            "adj": rng.choice(["精妙", "恐怖", "令人窒息", "不可思议", "前所未见"]),
            "num": str(rng.randint(3, 99)),
        }

        # 填充模板
        a_line = pattern["a"]
        b_line = pattern["b"]
        for key, val in vars_.items():
            a_line = a_line.replace("{" + key + "}", val)
            b_line = b_line.replace("{" + key + "}", val)

        return f"{name_a}道：{a_line}\n{name_b}道：{b_line}"
