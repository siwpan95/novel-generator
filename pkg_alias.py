"""把本仓根注册成 ``novel_generator`` 包 —— 兼容「仓目录名 ≠ 包名」。

背景
----
本仓目录名是 ``novel-generator``（= gitee 仓名，带连字符），而代码、文档与 ``pyproject.toml``
里的包名是 ``novel_generator``（下划线）。Python 不能从 ``novel-generator`` 这个目录名里
import 出 ``novel_generator``，于是凡是 ``from novel_generator.xxx import ...`` 的地方
（``main.py``、``__main__.py``、``tests/conftest.py`` 以及 ``engine/*`` 内部）都会
``ModuleNotFoundError``——与路径是否写死无关，属于仓库布局问题（2026-09-23 实测）。

做法
----
用 :mod:`importlib` 把**本仓根**注册成名为 ``novel_generator`` 的包（同一份代码，不拷贝、
不改各文件的 import 语句、不动 sys.path 上的其它条目）。入口脚本只要在第一条
``from novel_generator...`` 之前调用 :func:`install` 即可：

    import pkg_alias
    pkg_alias.install()

这样无论仓目录叫什么名字（``novel-generator`` / ``novel_generator`` / 别的工作区路径），
``python main.py`` 与 ``python -m pytest tests`` 都能跑；若日后把目录改名成 ``novel_generator``，
本模块会成为无害的幂等操作。
"""

from __future__ import annotations

import importlib.util
import os
import sys

PKG_NAME = "novel_generator"


def install() -> str:
    """注册包别名；返回被注册的 ``__init__.py`` 路径。重复调用是安全的。"""
    root = os.path.dirname(os.path.abspath(__file__))
    if PKG_NAME in sys.modules:
        return getattr(sys.modules[PKG_NAME], "__file__", "")
    if root not in sys.path:
        sys.path.insert(0, root)
    init_py = os.path.join(root, "__init__.py")
    if not os.path.isfile(init_py):
        raise RuntimeError(f"本仓根缺少 __init__.py：{init_py}")
    spec = importlib.util.spec_from_file_location(
        PKG_NAME, init_py, submodule_search_locations=[root]
    )
    if spec is None or spec.loader is None:  # pragma: no cover - 理论不可达
        raise RuntimeError(f"无法为本仓根构造包规范：{init_py}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[PKG_NAME] = module
    spec.loader.exec_module(module)
    return init_py


if __name__ == "__main__":  # 便于自检：python pkg_alias.py
    print(install())