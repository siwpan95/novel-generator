"""ASP 模板引擎（增强版）。

核心功能：
- {{bank.key}} 占位符替换
- ★ 修饰符系统：加权、分类、去重、回退
  - {{bank.key:w}}          → 权重随机选取
  - {{bank.key:c=category}} → 按分类过滤
  - {{bank.key:u}}          → 避免重复（unique）
  - {{bank.key:f=fb_bank.fb_key=f2_bank.f2_key}} → 回退链
  - {{bank.key:e=exclude}}  → 排除指定项
- ★ 状态变量：$var{default} 持久化追踪
- ★ 条件分支：{{?var=value}}...{{/}}
- ★ 重复避免上下文：ctx=tag 标记不同上下文
- ★ 上下文缓存：模板块复用后保持一致性
"""

import re
import random
from typing import Optional, Callable


# ───────────────── 修饰符解析 ─────────────────

_MODIFIER_RE = re.compile(
    r"\{\{([\w]+)\.([\w]+)((?::[a-zA-Z0-9_=.\-,\u4e00-\u9fff]+)*)\}\}"
)
_CONDITION_RE = re.compile(
    r"\{\{\?(\w+)=([\w\u4e00-\u9fff]+)\}\}(.*?)\{\{/\}\}"
)
_VAR_RE = re.compile(
    r"\$(\w+)\{([^}]*)\}"
)

_MODIFIER_PARSERS = {
    "w": lambda v, p: ("weighted", None),
    "u": lambda v, p: ("unique", v.get("ctx", "default") if isinstance(v, dict) else "default"),
    "c": lambda v, p: ("category", v),
    "f": lambda v, p: ("fallback", [tuple(x.split(".")) for x in v.split("=")]),
    "e": lambda v, p: ("exclude", set(v.split(",")) if isinstance(v, str) else set()),
    "n": lambda v, p: ("pick_n", int(v) if v else 1),
}


def _parse_modifier(mod_str: str) -> tuple[str, list]:
    """解析修饰符字符串为 (主操作, 参数列表)。

    示例：
        "w"       → ("weighted", [])
        "c=fire"  → ("category", ["fire"])
        "u"       → ("unique", ["default"])
        "f=a.b=c.d" → ("fallback", [[("a","b"), ("c","d")]])
    """
    if not mod_str:
        return ("default", [])
    parts = mod_str.lstrip(":").split(":")
    actions = []
    for p in parts:
        if "=" in p:
            k, v = p.split("=", 1)
            parser = _MODIFIER_PARSERS.get(k)
            if parser:
                actions.append(parser(v, {}))
        else:
            parser = _MODIFIER_PARSERS.get(p)
            if parser:
                actions.append(parser("", {}))
    if not actions:
        return ("default", [])
    return actions[0]


# ─────────────────   模板引擎    ─────────────────


class TemplateEngine:
    """ASP 模板引擎：占位符替换 + 修饰符系统 + 状态变量。"""

    def __init__(self, word_bank, seed: Optional[int] = None,
                 context_tag: str = "default"):
        self.wb = word_bank  # WordBank 实例
        self._rng = random.Random(seed)
        self._context_tag = context_tag
        # 状态变量存储
        self._vars: dict[str, str] = {}
        # 上下文缓存：同一上下文下相同模板解析结果保持一致
        self._context_cache: dict[str, str] = {}
        # 自定义处理器
        self._custom_handlers: dict[str, Callable] = {}

    # ───── 状态变量 ─────

    def set_var(self, name: str, value: str):
        """设置状态变量。"""
        self._vars[name] = value

    def get_var(self, name: str, default: str = "") -> str:
        """获取状态变量。"""
        return self._vars.get(name, default)

    def clear_vars(self):
        """清除所有状态变量。"""
        self._vars.clear()
        self._context_cache.clear()

    # ───── 自定义处理器 ─────

    def register_handler(self, prefix: str, handler: Callable):
        """注册自定义占位符处理器。

        handler 签名为 (bank, key, modifiers, params) -> str
        prefix 为占位符前缀，如 '__' 则处理 {{__expr}}。
        """
        self._custom_handlers[prefix] = handler

    # ───── 占位符解析 ─────

    def _resolve_placeholder(self, bank: str, key: str,
                             modifiers: list) -> str:
        """解析单个 {{bank.key}} 占位符，应用修饰符。"""

        if not modifiers:
            return self.wb.pick(bank, key)

        # 应用修饰符链
        result = None
        for mod in modifiers:
            # 兼容各种元组格式
            if isinstance(mod, tuple) and len(mod) >= 2:
                action, params = mod[0], mod[1] if len(mod) > 1 else None
            else:
                action = "default"
                params = None

            if action == "weighted":
                result = self.wb.pick_weighted(bank, key)

            elif action == "unique":
                ctx = params if params else "default"
                result = self.wb.pick_unique(bank, key, context_tag=ctx)

            elif action == "category":
                result = self.wb.pick_by_category(bank, key, category=params)

            elif action == "fallback":
                result = self.wb.pick_fallback(bank, key,
                                               fallback_chain=params)

            elif action == "exclude":
                exclude_set = params if isinstance(params, set) else set()
                result = self.wb.pick_without(bank, key, exclude=exclude_set)

            elif action == "pick_n":
                n = params if params else 1
                items = self.wb.pick_n(bank, key, n=n, unique=True)
                result = "、".join(items)

            else:  # "default"
                result = self.wb.pick(bank, key)

        return result if result is not None else self.wb.pick(bank, key)

    # ───── 变量替换 ─────

    def _resolve_vars(self, text: str) -> str:
        """替换 $var{default} 状态变量。

        首次访问时返回 default 并记录；后续访问返回之前的值。
        """
        def replacer(m):
            var_name = m.group(1)
            default_val = m.group(2)
            if var_name not in self._vars:
                self._vars[var_name] = default_val
            return self._vars[var_name]
        return _VAR_RE.sub(replacer, text)

    # ───── 条件分支 ─────

    def _resolve_conditions(self, text: str) -> str:
        """解析 {{?var=value}}...{{/}} 条件分支。

        如果 var 当前值为 value，则保留内容；否则删除。
        """
        def replacer(m):
            var_name = m.group(1)
            expected = m.group(2)
            content = m.group(3)
            actual = self._vars.get(var_name, "")
            if actual == expected:
                return content
            return ""
        return _CONDITION_RE.sub(replacer, text)

    # ───── 主解析入口 ─────

    def _resolve_match(self, match: re.Match) -> str:
        """处理单个正则匹配。"""
        bank = match.group(1)
        key = match.group(2)
        mod_str = match.group(3) or ""

        # 检查自定义处理器
        for prefix, handler in self._custom_handlers.items():
            if bank.startswith(prefix):
                return handler(bank, key, mod_str, self)

        # 解析修饰符
        modifiers = []
        if mod_str:
            for part in mod_str.lstrip(":").split(":"):
                if "=" in part:
                    k, v = part.split("=", 1)
                else:
                    k, v = part, ""
                parser = _MODIFIER_PARSERS.get(k)
                if parser:
                    modifiers.append(parser(v, {}))
        if not modifiers:
            modifiers.append(("default", []))

        return self._resolve_placeholder(bank, key, modifiers)

    def _resolve(self, text: str) -> str:
        """解析模板中的所有 {{bank.key}} 占位符。"""
        return _MODIFIER_RE.sub(self._resolve_match, text)

    def resolve(self, text: str) -> str:
        """完整解析模板：变量 → 条件 → 占位符。

        解析顺序：
        1. $var{default} 状态变量
        2. {{?var=value}}...{{/}} 条件分支
        3. {{bank.key:modifiers}} 词库占位符
        """
        # Step 1: 解析状态变量
        text = self._resolve_vars(text)
        # Step 2: 解析条件分支
        text = self._resolve_conditions(text)
        # Step 3: 解析词库占位符
        text = self._resolve(text)
        return text

    def resolve_with_context(self, text: str,
                             context: Optional[dict] = None) -> str:
        """带上下文缓存的解析：同上下文同模板结果一致。"""
        if context:
            cache_key = f"{text}__{'||'.join(f'{k}={v}' for k, v in sorted(context.items()))}"
            if cache_key in self._context_cache:
                return self._context_cache[cache_key]
            # 应用上下文变量
            for k, v in context.items():
                self.set_var(k, v)
            result = self.resolve(text)
            self._context_cache[cache_key] = result
            return result
        return self.resolve(text)

    def batch_resolve(self, templates: list[str],
                      context: Optional[dict] = None) -> list[str]:
        """批量解析模板列表。"""
        return [self.resolve_with_context(t, context) for t in templates]

    def template(self, template_text: str, **kwargs) -> str:
        """便捷方法：设置变量后解析模板。"""
        for k, v in kwargs.items():
            self.set_var(k, str(v))
        return self.resolve(template_text)

    # ───── ★ 向后兼容方法：fill / fill_loop ─────

    # 兼容旧版 {{变量名}} 语法的正则
    _OLD_VAR_RE = re.compile(r"\{\{([^{}]+)\}\}")

    def fill(self, text: str, variables: dict = None) -> str:
        """向后兼容的简单填充方法。

        支持两种占位符：
        1. `{{变量名}}` — 从 variables 字典中查找替换
        2. `{{bank.key}}` — 从词库中随机选取（当不包含修饰符时）

        Args:
            text: 模板文本
            variables: 上下文字典

        Returns:
            填充后的文本。
        """
        variables = variables or {}

        def replacer(match):
            key = match.group(1).strip()

            # 1. 优先从 variables 字典中查找
            if key in variables:
                return str(variables[key])

            # 2. 检查是否是 bank.key 格式
            if "." in key and ":" not in key:
                parts = key.split(".", 1)
                bank, sub_key = parts[0], parts[1]
                try:
                    return self.wb.pick(bank, sub_key)
                except (KeyError, FileNotFoundError):
                    pass

            # 3. 保留原样
            return match.group(0)

        return self._OLD_VAR_RE.sub(replacer, text)

    def fill_loop(self, template: str, variables: dict = None,
                  iterations: int = 1) -> list[str]:
        """向后兼容的循环填充。

        每次迭代中，{{循环索引}} 会被替换为当前迭代序号（从1开始）。

        Args:
            template: 模板文本
            variables: 上下文字典
            iterations: 迭代次数

        Returns:
            填充后的文本列表。
        """
        results = []
        base_vars = dict(variables or {})
        for i in range(1, iterations + 1):
            vars_copy = dict(base_vars)
            vars_copy["循环索引"] = str(i)
            results.append(self.fill(template, vars_copy))
        return results
